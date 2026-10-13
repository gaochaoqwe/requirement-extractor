"""
函数审查Agent - 使用ReAct模式进行智能代码审查

与传统方式的区别：
- 传统：一次性给AI所有信息（函数代码 + 所有依赖函数 + 全局变量）
- Agent：只给AI原始函数，让AI自己决定需要查看什么信息
"""
import json
import re
import uuid
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from .openai.client import AIClient
from .parser.global_var_parser import detect_actual_global_usage, extract_globals_from_code, extract_macros_from_code
from .parser import collect_function_with_dependencies
from ...utils.concurrent_logger import log_concurrent_info, log_concurrent_warning, log_concurrent_debug, log_concurrent_error


class FunctionReviewAgent:
    """函数审查Agent - 基于ReAct模式的智能审查"""
    
    def __init__(self, project_root: str, language: str = 'c'):
        """
        初始化Agent
        
        Args:
            project_root: 项目根目录
            language: 代码语言（c/cpp）
        """
        self.project_root = Path(project_root)
        self.language = language
        self.ai_client = AIClient()
        
        # Agent配置
        self.max_iterations = 50  # 最多50轮推理（给AI充分的探索空间，但通过提示词建议在20轮内完成）
        self.max_tool_calls_per_iteration = 5  # 每轮最多5个工具调用（提高效率）
        
        # 缓存，避免重复读取
        self.global_var_cache = None
        self.function_cache = {}
        
        # 允许的文件扩展名
        self.allowed_extensions = ['.c', '.cpp', '.h', '.hpp', '.cc', '.cxx', '.v', '.vhd', '.vhdl']
    
    def review_function(
        self,
        function_code: str,
        function_name: str,
        file_path: str,
        global_var_map: Dict[str, Dict[str, Any]],
        forbidden_rules: str
    ) -> Dict[str, Any]:
        """
        审查单个函数
        
        Args:
            function_code: 函数代码
            function_name: 函数名
            file_path: 文件路径
            global_var_map: 全局变量映射
            forbidden_rules: 禁止报告的规则
            
        Returns:
            审查结果 {problems: [], function_info: {}}
        """
        log_concurrent_info(f"[Agent审查] 开始审查函数: {function_name}", "function_review_agent")
        
        # 缓存全局变量映射
        self.global_var_cache = global_var_map
        
        # 初始化对话历史
        conversation = []
        
        # 系统提示词 - 告诉AI它是一个代码审查Agent
        system_prompt = self._build_system_prompt(forbidden_rules)
        conversation.append({"role": "system", "content": system_prompt})
        
        # 记录初始化信息（优化版：只记录摘要，不记录完整内容）
        log_concurrent_info("="*80, "agent_prompt_init")
        log_concurrent_info(f"[Agent审查初始化] 函数: {function_name}", "agent_prompt_init")
        log_concurrent_info("="*80, "agent_prompt_init")
        log_concurrent_info("[1] 系统提示词:", "agent_prompt_init")
        log_concurrent_info(f"   长度: {len(system_prompt)} 字符", "agent_prompt_init")
        log_concurrent_info("   内容: 包含审查规则、工具定义（13个工具）、禁止报告的问题类型、输出格式要求等", "agent_prompt_init")
        log_concurrent_info("   核心原则: 疑罪从无，只提100%确定的问题", "agent_prompt_init")
        
        # 初始任务 - 只给函数代码，不给依赖
        initial_task = self._build_initial_task(function_code, function_name, file_path)
        conversation.append({"role": "user", "content": initial_task})
        
        # 记录初始任务摘要
        log_concurrent_info("[2] 初始任务:", "agent_prompt_init")
        log_concurrent_info(f"   长度: {len(initial_task)} 字符", "agent_prompt_init")
        log_concurrent_info(f"   文件: {file_path}", "agent_prompt_init")
        log_concurrent_info(f"   函数: {function_name}", "agent_prompt_init")
        log_concurrent_info("="*80, "agent_prompt_init")
        
        # ReAct循环
        final_result = None
        for iteration in range(self.max_iterations):
            current_iteration = iteration + 1
            log_concurrent_info(f"🔄 [开始第 {current_iteration} 轮推理]", "function_review_agent")
            
            # 如果超过15轮，添加提醒
            if current_iteration == 15:
                conversation.append({
                    "role": "user",
                    "content": "⚠️ 提醒：已经进行了15轮推理，请尽快完成审查并给出结论。如果代码逻辑清晰且无明显问题，可以直接输出最终结果。\n\n**请严格按照系统提示词中的JSON格式输出**，包含所有必需字段。\n\n**特别注意**：`commented_code` 必须包含完整函数代码，可以直接使用真实换行符（无需\\\\n转义）。"
                })
            elif current_iteration == 20:
                conversation.append({
                    "role": "user", 
                    "content": "⚠️ 重要提醒：已经进行了20轮推理，请立即总结并输出最终审查结果。\n\n**必须使用标准JSON格式**，包含所有必需字段：file_name, source_code, problem_reason, issue_level, issue_name, issue_location, description_requirement, description_issue, description_location（格式：xx文件的xx函数的xx行：问题代码语句源程序为：\\n保留关键上下文的源程序代码）, description_impact, function_info。\n\n**关键**：\n1. function_info字段必须提供（function_name, function_description, commented_code）\n2. description_location字段必须在问题代码语句后追加`源程序为：`和关键上下文源代码，无关代码可用......省略\n3. **commented_code必须包含完整函数代码**，可以直接使用真实换行（无需\\\\n转义）\n4. 确保JSON可以被解析，不要有未转义的双引号等特殊字符"
                })
            
            # 调用AI（支持function calling）
            response = self._call_ai_with_tools(conversation, current_iteration)
            
            # 检查是否遇到上下文超出错误
            if response.get('_context_overflow'):
                log_concurrent_warning(
                    f"[Agent审查] 在第 {current_iteration} 轮遇到上下文超出，需要降级到简化模式",
                    "function_review_agent"
                )
                # 返回特殊标记，让外层调用方降级处理
                return {
                    "problems": [],
                    "function_info": {},
                    "_context_overflow": True,
                    "_error": response.get('_error', '')
                }
            
            # 检查是否完成
            if response.get('finished'):
                final_result = response.get('result', {})
                
                # 检查是否解析成功（更精确的判断）
                # 解析失败的特征：
                # 1. function_info 的 function_name 为空（默认值）
                # 2. function_info 的 description 包含"解析失败"或"解析错误"
                # 3. problems 为空且 function_info.commented_code 为空
                is_parse_failed = False
                if final_result:
                    func_info = final_result.get('function_info', {})
                    func_name = func_info.get('function_name', '')
                    func_desc = func_info.get('function_description', '')
                    commented_code = func_info.get('commented_code', '')
                    problems = final_result.get('problems', [])
                    
                    # 判断是否为解析失败的默认返回值
                    if (not func_name or 
                        '解析失败' in func_desc or 
                        '解析错误' in func_desc or
                        (len(problems) == 0 and not commented_code)):
                        is_parse_failed = True
                        log_concurrent_warning(
                            f"[Agent审查] 检测到解析失败的默认返回值: "
                            f"func_name='{func_name}', func_desc='{func_desc[:50]}', "
                            f"problems={len(problems)}, has_commented_code={bool(commented_code)}",
                            "function_review_agent"
                        )
                
                if is_parse_failed:
                    # JSON解析失败，尝试重试（最多2次）
                    max_json_retries = 2
                    for retry in range(max_json_retries):
                        log_concurrent_warning(
                            f"[Agent审查] JSON解析失败，第 {retry + 1}/{max_json_retries} 次重试",
                            "function_review_agent"
                        )
                        
                        # 添加AI的原始响应（但格式不正确）
                        conversation.append({
                            "role": "assistant",
                            "content": response.get('_raw_content', '')  # 使用原始内容
                        })
                        
                        # 要求AI重新生成符合格式的JSON
                        # 根据错误类型给出更具体的提示
                        raw_content = response.get('_raw_content', '')
                        error_hint = ""
                        
                        # 检测具体错误类型
                        if 'Unterminated string' in str(response.get('_parse_error', '')):
                            error_hint = "\n⚠️ **检测到JSON被截断（字符串未闭合）**\n这通常是因为 `commented_code` 字段内容过长导致JSON超出长度限制。\n**解决方案**：将 `commented_code` 字段值设为空字符串 \"\"，确保JSON完整可解析。problems数据才是最重要的，不要丢失。"
                        elif len(raw_content) > 10000:
                            error_hint = "\n⚠️ **你的回复过长（超过10000字符）**\n**解决方案**：将 `commented_code` 字段值设为空字符串 \"\"，只保留problems和function_name、function_description字段。"
                        
                        retry_prompt = f"""你的上一次回复的JSON格式有误，无法解析。请重新生成符合格式的JSON结果。
{error_hint}

**常见错误：**
1. JSON被截断（未完成）- 通常是 `commented_code` 太长
2. 字符串中包含未转义的换行符（必须使用\\n）
3. 缺少必需字段（problems和function_info）
4. JSON语法错误（缺少逗号、括号不匹配等）

**关键要求：**
- 必须返回完整的、可解析的JSON
- `commented_code` 字段可以直接使用真实换行符，无需\\n转义
- function_info字段必须包含：function_name, function_description, commented_code
- **如果JSON之前被截断，请将 `commented_code` 设为空字符串 \"\"，优先保证problems数据完整**
- 确保JSON完整，不要被截断

请现在重新生成**完整**的JSON结果。"""
                        
                        conversation.append({
                            "role": "user",
                            "content": retry_prompt
                        })
                        
                        # 重新调用AI
                        retry_response = self._call_ai_with_tools(conversation)
                        
                        if retry_response.get('finished'):
                            retry_result = retry_response.get('result', {})
                            if retry_result and (retry_result.get('problems') is not None or retry_result.get('function_info')):
                                # 解析成功
                                final_result = retry_result
                                log_concurrent_info(
                                    f"[Agent审查] JSON解析重试成功！发现 {len(final_result.get('problems', []))} 个问题",
                                    "function_review_agent"
                                )
                                break
                        
                        # 更新对话历史
                        if retry_response.get('_raw_content'):
                            conversation[-2]['content'] = retry_response.get('_raw_content', '')
                    else:
                        # 所有重试都失败
                        log_concurrent_error(
                            f"[Agent审查] JSON解析重试 {max_json_retries} 次后仍然失败",
                            "function_review_agent"
                        )
                        # 使用默认值
                        final_result = {
                            "problems": [],
                            "function_info": {
                                "function_name": function_name,
                                "function_description": "JSON解析失败，审查结果无法获取",
                                "commented_code": function_code
                            }
                        }
                
                log_concurrent_info(
                    f"🎯 [第 {current_iteration} 轮完成] 审查结束，发现 {len(final_result.get('problems', []))} 个问题",
                    "function_review_agent"
                )
                break
            
            # 执行工具调用
            if response.get('tool_calls'):
                tool_results = self._execute_tools(response['tool_calls'])
                
                # 准备干净的tool_calls格式（移除内部字段）
                clean_tool_calls = [
                    {
                        "id": tc.get('id'),
                        "type": tc.get('type'),
                        "function": tc.get('function')
                    }
                    for tc in response['tool_calls']
                ]
                
                # 添加AI响应到历史
                conversation.append({
                    "role": "assistant",
                    "content": response.get('content', ''),
                    "tool_calls": clean_tool_calls
                })
                
                # 添加工具结果到历史
                for tool_call, tool_result in zip(response['tool_calls'], tool_results):
                    conversation.append({
                        "role": "tool",
                        "tool_call_id": tool_call.get('id'),
                        "name": tool_call.get('function', {}).get('name'),
                        "content": json.dumps(tool_result, ensure_ascii=False)
                    })
                
                # 总结本轮工具调用
                tool_names = [tc.get('function', {}).get('name') for tc in response['tool_calls']]
                log_concurrent_info(
                    f"✅ [第 {current_iteration} 轮完成] 本轮共调用 {len(tool_names)} 个工具: {tool_names}",
                    "function_review_agent"
                )
            else:
                # AI没有调用工具，但也没有给出最终答案
                log_concurrent_warning(f"[Agent审查] AI未调用工具也未给出答案", "function_review_agent")
                break
        
        # 如果没有得到结果，返回默认值
        if final_result is None:
            log_concurrent_warning(
                f"[Agent审查] AI在{self.max_iterations}轮推理后仍未完成审查，可能代码过于复杂。返回空结果。", 
                "function_review_agent"
            )
            final_result = {
                "problems": [],
                "function_info": {
                    "function_name": function_name,
                    "function_description": "审查超时未完成（建议简化代码或使用传统模式）",
                    "commented_code": function_code
                }
            }
        
        return final_result
    
    def _build_system_prompt(self, forbidden_rules: str) -> str:
        """构建系统提示词"""
        return f"""你是一名专业的C/C++代码审查专家Agent。你的任务是审查函数代码，找出潜在问题。
**你是一个Agent**，这意味着：
1. 你可以主动调用工具来获取需要的信息
2. 你不需要一次性得到所有信息，可以根据需要逐步探索
3. 你应该根据代码的复杂性决定是否需要查看依赖函数或全局变量

**⚠️ 重要提示**：
- 请尽量在 **20轮推理内** 完成审查
- 不要过度探索，聚焦于影响功能的关键问题
- 如果代码逻辑清晰且无明显问题，可以直接给出结论

{forbidden_rules}

**输出格式要求（非常重要）**：
最终必须输出标准JSON格式的审查结果。

## 问题分析字段含义：
- `file_name`：当前报错的代码函数所在的代码文件名称
- `source_code`：当前报错的代码函数的全部代码
- `problem_reason`：问题的根本原因（例如：未检查返回值、缓冲区溢出风险、资源泄漏等，用简洁的语言描述问题的本质原因）
- `issue_level`：问题等级（必须是以下三个值之一：建议改进、一般问题、重要问题）
- `issue_name`：问题名称
- `issue_location`：问题来源（代码文件名称+函数名称）
- `description_requirement`：需求描述
- `description_issue`：问题描述
- `description_location`：问题定位，**必须严格按照以下格式**：`xx文件的xx函数的xx行：问题代码语句源程序为：\\n保留关键上下文的源程序代码`
  - 示例：`example.c文件的foo函数的3行：gets(buf);源程序为：\\nvoid foo() {{\\n    char buf[10];\\n    gets(buf);\\n}}`
  - 示例：`c_test_project\\src\\event_handler.c文件的register_event_callback函数的45行：g_callbacks[status] = callback;源程序为：\\nSystemStatus register_event_callback(SystemStatus status, EventCallback callback) {{\\n   ......\\n\\n    if (status < SYSTEM_OK || status > SYSTEM_CRITICAL || callback == NULL) {{\\n        return SYSTEM_ERROR;\\n    }}\\n\\n    g_callbacks[status] = callback;\\n    ......\\n}}`
  - **重要**：问题代码语句是最关键的定位信息，必须先写在`源程序为：`之前，前端将使用该代码语句进行精确匹配
  - `源程序为：`后必须原封不动保留关键有问题部分的上下文代码；无关代码可以使用`......`省略，但问题代码语句及其必要上下文必须保持源代码原样
  - 问题代码语句应该是导致问题的**具体代码片段**，去掉多余空格，保持原始语法
  - 在JSON字符串中，`description_location`里的源程序换行必须使用`\\n`表示，不能直接换行
- `description_impact`：影响分析

## 函数信息字段含义：
- `function_name`：函数名称
- `function_description`：函数功能描述
- `commented_code`：注释后的代码（**必须添加详细注释**）
  - **要求**：为每一行重要代码添加行内注释或行上注释
  - **包括**：变量声明、函数调用、条件判断、循环、返回语句等
  - **注释内容**：解释代码的作用、参数含义、返回值、业务逻辑等
  - **示例**：不仅要有"// 声明变量"，还要有"// 声明10字节缓冲区用于存储用户输入"

## 输出示例：
```json
{{
  "problems": [
    {{
      "file_name": "example.c",
      "source_code": "void foo() {{ char buf[10]; gets(buf); }}",
      "problem_reason": "使用不安全的输入函数，存在缓冲区溢出风险",
      "issue_level": "重要问题",
      "issue_name": "使用不安全的函数gets",
      "issue_location": "example.c:foo",
      "description_requirement": "应该使用安全的输入函数，避免缓冲区溢出",
      "description_issue": "使用了不安全的gets函数，可能导致缓冲区溢出",
      "description_location": "example.c文件的foo函数的3行：gets(buf);源程序为：\\nvoid foo() {{\\n    char buf[10];\\n    gets(buf);\\n}}",
      "description_impact": "可能导致程序崩溃或安全漏洞"
    }}
  ],
  "function_info": {{
    "function_name": "foo",
    "function_description": "这是一个示例函数，用于演示输入处理功能。",
    "commented_code": "// 输入处理函数，从标准输入读取字符串\\nvoid foo() {{\\n    // 声明10字节字符数组作为输入缓冲区\\n    char buf[10];\\n    \\n    // 【安全风险】使用gets()函数读取用户输入\\n    // gets()不检查缓冲区边界，可能导致缓冲区溢出\\n    // 建议使用fgets(buf, sizeof(buf), stdin)替代\\n    gets(buf);\\n    \\n    // 函数结束，无返回值\\n}}"
  }}
}}
```

## 严格的JSON格式要求（非常重要！）：
1. 必须返回标准的、可解析的JSON格式
2. 所有字符串值必须使用双引号(" )，不能使用单引号(')
3. **字符串中的换行符必须使用\\n转义**，不能直接换行！例如：
   - ❌ 错误："code": "void foo() {{
              return 0;
          }}"
   - ✅ 正确："code": "void foo() {{\\n    return 0;\\n}}"
4. 字符串中如有双引号，必须使用反斜杠转义(\\")
5. 字符串中如有反斜杠，必须双重转义(\\\\)
6. 不要在JSON中包含任何控制字符或特殊格式字符
7. 所有数组元素和对象属性必须使用逗号分隔，最后一项后不能有逗号
8. **你的整个回复必须是一个单一的、完整的JSON对象**。在JSON对象之前或之后，绝对不要包含任何文本、解释、代码块标记（如 ```json 或 ```）或任何其他非JSON内容。
9. **issue_level字段必须严格使用"建议改进"、"一般问题"、"重要问题"三个值之一，不得使用其他值。**
10. **description_location字段格式固定为：xx文件的xx函数的xx行：问题代码语句源程序为：\\n保留关键上下文的源程序代码**

**关键要求：**
- **function_info字段必须始终提供**，包含function_name, function_description, commented_code三个字段
- **即使未发现问题，也必须返回完整的function_info**
- **commented_code中的换行符必须用\\n转义**，例如："commented_code": "int main() {{\\n    // 注释\\n    return 0;\\n}}"
"""
    
    def _build_initial_task(self, function_code: str, function_name: str, file_path: str) -> str:
        """构建初始任务"""
        return f"""请审查以下函数：

**文件**：{file_path}
**函数名**：{function_name}
**代码**：
```{self.language}
{function_code}
```

请开始审查。如果需要了解被调用函数的实现或全局变量的定义，可以使用工具获取。

**审查完成后，请严格按照系统提示词中的JSON格式输出结果，包含所有必需字段：**
- problems数组（每个问题包含：file_name, source_code, problem_reason, issue_level, issue_name, issue_location, description_requirement, description_issue, description_location, description_impact）
- function_info对象（必须包含：function_name, function_description, commented_code）

**⚠️ 特别重要 - description_location格式要求：**
1. 每个问题的`description_location`必须包含`源程序为：`
2. 固定格式：`xx文件的xx函数的xx行：问题代码语句源程序为：\\n保留关键上下文的源程序代码`
3. `源程序为：`后要写问题所在函数的关键上下文源代码，无关代码可用`......`省略
4. 问题代码语句和上下文中的关键问题代码必须保持源代码原样

**⚠️ 特别重要 - commented_code详细注释要求：**
1. **必须为每一行重要代码添加详细注释**
2. **注释要解释代码的具体作用和业务含义**，不要只写"声明变量"这样的泛泛注释
3. **包括但不限于**：
   - 变量声明：说明用途、大小、数据类型选择原因
   - 函数调用：说明调用目的、参数含义、预期结果
   - 条件判断：说明判断条件的业务含义
   - 循环：说明循环目的、边界条件
   - 返回语句：说明返回值含义
4. **对于潜在问题的代码，要在注释中标注风险**

**⚠️ JSON格式关键要求：**
1. **function_info字段必须始终返回**，即使没有发现问题
2. **commented_code中的换行符必须用\\\\n转义**，例如："commented_code": "int main() {{\\\\n    // 主函数入口\\\\n    return 0;  // 正常退出\\\\n}}"
3. 不要在字符串中直接换行，所有换行必须用\\\\n表示
4. 确保返回的JSON可以被正确解析
"""
    
    def _call_ai_with_tools(self, conversation: List[Dict[str, Any]], current_iteration: int = 0) -> Dict[str, Any]:
        """调用AI（支持function calling）"""
        
        # 记录对话历史到日志（优化版：跳过重复的system和user消息）
        log_concurrent_info("="*80, "ai_prompt_debug")
        if current_iteration > 0:
            log_concurrent_info(f"🔄 [第 {current_iteration} 轮推理] 即将发送给AI的对话历史：", "ai_prompt_debug")
        else:
            log_concurrent_info("[对话记录] 即将发送给AI的对话历史：", "ai_prompt_debug")
        log_concurrent_info("="*80, "ai_prompt_debug")
        
        # 跟踪是否已记录system和user消息
        system_logged = False
        user_logged = False
        
        for idx, msg in enumerate(conversation):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            
            # 优化：system和user消息只记录一次摘要
            if role == 'system':
                if not system_logged:
                    log_concurrent_info(f"\n[消息 {idx+1}] 角色: system", "ai_prompt_debug")
                    log_concurrent_info(f"{'='*60}", "ai_prompt_debug")
                    log_concurrent_info("[系统提示词] (长度: {} 字符，已省略详细内容)".format(len(content)), "ai_prompt_debug")
                    log_concurrent_info("摘要: 包含审查规则、工具定义、输出格式要求等", "ai_prompt_debug")
                    log_concurrent_info(f"{'='*60}\n", "ai_prompt_debug")
                    system_logged = True
                continue  # 跳过后续的system消息
            
            elif role == 'user':
                if not user_logged:
                    log_concurrent_info(f"\n[消息 {idx+1}] 角色: user", "ai_prompt_debug")
                    log_concurrent_info(f"{'='*60}", "ai_prompt_debug")
                    # 提取函数名（如果有）
                    function_name = "未知"
                    if "函数名**：" in content:
                        try:
                            function_name = content.split("函数名**：")[1].split("\n")[0].strip()
                        except:
                            pass
                    log_concurrent_info(f"[初始任务] 审查函数: {function_name} (长度: {len(content)} 字符，已省略代码内容)", "ai_prompt_debug")
                    log_concurrent_info(f"{'='*60}\n", "ai_prompt_debug")
                    user_logged = True
                continue  # 跳过后续的user消息
            
            # 重点记录：assistant和tool消息（这是关键的推理过程）
            log_concurrent_info(f"\n[消息 {idx+1}] 角色: {role}", "ai_prompt_debug")
            log_concurrent_info(f"{'='*60}", "ai_prompt_debug")
            
            if role == 'assistant':
                log_concurrent_info("[AI回复]:", "ai_prompt_debug")
                if content:
                    # 限制AI回复内容的长度，避免日志过长
                    if len(content) > 500:
                        log_concurrent_info(content[:500] + "... (已截断)", "ai_prompt_debug")
                    else:
                        log_concurrent_info(content, "ai_prompt_debug")
                else:
                    log_concurrent_info("[无文本内容]", "ai_prompt_debug")
                
                # 记录工具调用（这是最关键的信息）
                if 'tool_calls' in msg:
                    log_concurrent_info(f"\n🔧 [工具调用] 数量: {len(msg['tool_calls'])}", "ai_prompt_debug")
                    for tc_idx, tc in enumerate(msg['tool_calls']):
                        tool_name = tc.get('function', {}).get('name', 'unknown')
                        tool_args = tc.get('function', {}).get('arguments', '{}')
                        log_concurrent_info(f"   [{tc_idx+1}] {tool_name}", "ai_prompt_debug")
                        log_concurrent_info(f"       参数: {tool_args}", "ai_prompt_debug")
            
            elif role == 'tool':
                tool_name = msg.get('name', 'unknown')
                log_concurrent_info(f"📦 [工具结果] {tool_name}", "ai_prompt_debug")
                log_concurrent_info(f"   结果长度: {len(content)} 字符", "ai_prompt_debug")
                # 工具结果限制长度，避免日志过大
                if len(content) > 1000:
                    log_concurrent_info(f"   内容（前1000字符）: {content[:1000]}... (已截断)", "ai_prompt_debug")
                else:
                    log_concurrent_info(f"   内容: {content}", "ai_prompt_debug")
            
            log_concurrent_info(f"{'='*60}\n", "ai_prompt_debug")
        
        log_concurrent_info("="*80, "ai_prompt_debug")
        if current_iteration > 0:
            log_concurrent_info(f"📊 [对话统计] 第 {current_iteration} 轮 | 累积消息数: {len(conversation)} (包含历史)", "ai_prompt_debug")
        else:
            log_concurrent_info(f"📊 [对话统计] 累积消息数: {len(conversation)}", "ai_prompt_debug")
        log_concurrent_info("="*80, "ai_prompt_debug")
        
        # 准备工具定义
        tools_definition = [
            {
                "type": "function",
                "function": {
                    "name": "get_dependency_function",
                    "description": "获取被当前函数调用的其他函数的完整代码。用于理解函数调用的具体实现。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "function_name": {
                                "type": "string",
                                "description": "要查看的函数名，如 'malloc', 'processData'"
                            }
                        },
                        "required": ["function_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_global_variable",
                    "description": "获取全局变量、宏定义或数组的定义信息。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "variable_name": {
                                "type": "string",
                                "description": "变量、宏或数组的名称"
                            }
                        },
                        "required": ["variable_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_function_calls",
                    "description": "搜索某个函数在项目中被哪些地方调用。用于理解函数的使用上下文。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "function_name": {
                                "type": "string",
                                "description": "要搜索的函数名"
                            }
                        },
                        "required": ["function_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_all_globals",
                    "description": "列出代码中可能使用的所有全局变量、宏定义和数组的名称。",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_file_outline",
                    "description": "获取指定文件的结构大纲：函数列表、全局变量、宏定义等。适合快速了解文件整体结构。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "文件路径（相对于项目根目录）"
                            }
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file_range",
                    "description": "按行范围读取文件内容，用于查看特定代码区域。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "文件路径"
                            },
                            "start_line": {
                                "type": "integer",
                                "description": "起始行号（从1开始）"
                            },
                            "end_line": {
                                "type": "integer",
                                "description": "结束行号"
                            }
                        },
                        "required": ["file_path", "start_line", "end_line"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_call_graph",
                    "description": "获取函数的调用关系图。可以查看函数调用了谁（callees）或被谁调用（callers）。**强大的工具**，可快速了解函数的上下游关系。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "function_name": {
                                "type": "string",
                                "description": "要查询的函数名"
                            },
                            "direction": {
                                "type": "string",
                                "enum": ["callers", "callees", "both"],
                                "description": "查询方向：callers=谁调用了它，callees=它调用了谁，both=双向。默认callees"
                            },
                            "depth": {
                                "type": "integer",
                                "description": "调用深度（1-3），默认1"
                            }
                        },
                        "required": ["function_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_code",
                    "description": "在项目代码中搜索包含指定关键字的代码行，用于查找特定模式或变量使用。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "keyword": {
                                "type": "string",
                                "description": "搜索关键字"
                            },
                            "file_pattern": {
                                "type": "string",
                                "description": "文件模式，如 '*.c'，默认所有代码文件"
                            }
                        },
                        "required": ["keyword"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_directory",
                    "description": "列出项目目录的文件和子目录，用于了解项目结构",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "relative_path": {
                                "type": "string",
                                "description": "相对于项目根目录的路径，空字符串表示项目根目录"
                            },
                            "max_depth": {
                                "type": "integer",
                                "description": "递归深度，默认为2"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_function_by_name",
                    "description": "在项目中按函数名搜索函数，用于快速定位功能实现",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "function_name": {
                                "type": "string",
                                "description": "要搜索的函数名（支持部分匹配）"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "返回结果数量限制，默认10个"
                            }
                        },
                        "required": ["function_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_function_in_file",
                    "description": "在指定文件中搜索特定函数的代码",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "relative_path": {
                                "type": "string",
                                "description": "相对于项目根目录的文件路径"
                            },
                            "function_name": {
                                "type": "string",
                                "description": "函数名"
                            }
                        },
                        "required": ["relative_path", "function_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_function_context",
                    "description": "获取指定行所在函数的完整代码，用于理解函数上下文",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "relative_path": {
                                "type": "string",
                                "description": "文件路径"
                            },
                            "line_number": {
                                "type": "integer",
                                "description": "行号"
                            }
                        },
                        "required": ["relative_path", "line_number"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_variable_usage",
                    "description": "追踪变量在文件中的所有使用位置（声明、赋值、读取）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "relative_path": {
                                "type": "string",
                                "description": "文件路径"
                            },
                            "variable_name": {
                                "type": "string",
                                "description": "变量名"
                            },
                            "line_number": {
                                "type": "integer",
                                "description": "可选：从哪一行开始查找"
                            }
                        },
                        "required": ["relative_path", "variable_name"]
                    }
                }
            }
        ]
        
        try:
            # 使用已有的 AIClient 的 OpenAI 客户端实例
            # 调用时支持 function calling
            log_concurrent_debug(f"[Agent审查] 准备调用AI，对话轮数: {len(conversation)}", "function_review_agent")
            
            # 从配置文件读取 max_tokens
            # 如果配置为 None 或 -1 或不存在，则不限制输出（使用模型默认）
            max_tokens = self.ai_client.model_params.get("max_tokens", None)
            
            # 构建API调用参数
            api_params = {
                "model": self.ai_client.default_model,
                "messages": conversation,
                "tools": tools_definition,
                "tool_choice": "auto",
                "temperature": 0.2
            }
            
            # 只有当 max_tokens 是正数时才添加限制
            if max_tokens is not None and max_tokens > 0:
                api_params["max_tokens"] = max_tokens
                log_concurrent_debug(
                    f"[Agent审查] AI调用参数: model={self.ai_client.default_model}, max_tokens={max_tokens}（受限）",
                    "function_review_agent"
                )
            else:
                log_concurrent_debug(
                    f"[Agent审查] AI调用参数: model={self.ai_client.default_model}, max_tokens=无限制（使用模型默认）",
                    "function_review_agent"
                )
            
            response = self.ai_client.client.chat.completions.create(**api_params)
            
        except Exception as api_error:
            # 检查是否是上下文超出错误
            from .context_overflow_handler import is_context_overflow_error
            
            if is_context_overflow_error(api_error):
                log_concurrent_warning(
                    f"[Agent审查] 检测到上下文超出，对话轮数: {len(conversation)}",
                    "function_review_agent"
                )
                # 返回特殊标记，让调用方知道需要降级
                return {
                    "finished": True,
                    "result": None,
                    "_context_overflow": True,
                    "_error": str(api_error)
                }
            else:
                # 其他错误，重新抛出
                raise
        
        try:
            
            message = response.choices[0].message
            
            log_concurrent_debug(f"[Agent审查] AI响应完成", "function_review_agent")
            
            # 检查是否有工具调用
            if hasattr(message, 'tool_calls') and message.tool_calls:
                tool_calls_list = []
                for tc in message.tool_calls:
                    # 检查参数是否为空
                    arguments_str = tc.function.arguments or "{}"
                    
                    try:
                        parsed_args = json.loads(arguments_str)
                    except json.JSONDecodeError as e:
                        log_concurrent_warning(
                            f"[Agent审查] 工具调用参数JSON解析失败: {tc.function.name}, 参数: '{arguments_str}', 错误: {str(e)}",
                            "function_review_agent"
                        )
                        # 使用空字典作为默认参数
                        parsed_args = {}
                        arguments_str = "{}"
                    
                    tool_calls_list.append({
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": arguments_str
                        },
                        # 同时保留解析后的参数，供工具执行使用
                        "_parsed_arguments": parsed_args
                    })
                
                
                # 记录AI的工具调用请求
                if current_iteration > 0:
                    log_concurrent_info(
                        f"🔧 [第 {current_iteration} 轮] AI请求调用 {len(tool_calls_list)} 个工具：{[tc['function']['name'] for tc in tool_calls_list]}",
                        "function_review_agent"
                    )
                else:
                    log_concurrent_debug(
                        f"[Agent审查] AI请求调用 {len(tool_calls_list)} 个工具：{[tc['function']['name'] for tc in tool_calls_list]}",
                        "function_review_agent"
                    )
                
                return {
                    "finished": False,
                    "content": message.content or "",
                    "tool_calls": tool_calls_list
                }
            else:
                # AI给出了最终答案
                content = message.content or ""
                
                # 记录AI的原始响应到日志
                log_concurrent_info(
                    f"[Agent审查] AI返回最终结果，原始响应内容：\n{'='*60}\n{content}\n{'='*60}",
                    "function_review_agent"
                )
                
                # 尝试解析JSON结果
                result, parse_error = self._parse_final_result(content)
                
                # 如果解析成功，记录详细的函数信息
                if result and isinstance(result, dict):
                    function_info = result.get('function_info', {})
                    if function_info:
                        log_concurrent_info(
                            f"[Agent审查] 函数信息解析成功：\n"
                            f"{'='*60}\n"
                            f"函数名称: {function_info.get('function_name', 'N/A')}\n"
                            f"功能描述: {function_info.get('function_description', 'N/A')}\n"
                            f"注释后代码长度: {len(function_info.get('commented_code', ''))} 字符\n"
                            f"发现问题数量: {len(result.get('problems', []))}\n"
                            f"{'='*60}",
                            "function_review_agent"
                        )
                        
                        # 单独记录注释后的代码（如果存在）
                        commented_code = function_info.get('commented_code', '')
                        if commented_code:
                            log_concurrent_info(
                                f"[Agent审查] AI返回的注释后代码：\n"
                                f"{'='*60}\n"
                                f"{commented_code}\n"
                                f"{'='*60}",
                                "function_review_agent"
                            )
                    
                    # 记录发现的问题详情
                    problems = result.get('problems', [])
                    if problems:
                        log_concurrent_info(
                            f"[Agent审查] 发现的问题详情：\n{'='*60}",
                            "function_review_agent"
                        )
                        for i, problem in enumerate(problems, 1):
                            log_concurrent_info(
                                f"问题 {i}:\n"
                                f"  等级: {problem.get('issue_level', 'N/A')}\n"
                                f"  名称: {problem.get('issue_name', 'N/A')}\n"
                                f"  位置: {problem.get('description_location', 'N/A')}\n"
                                f"  描述: {problem.get('description_issue', 'N/A')[:200]}{'...' if len(problem.get('description_issue', '')) > 200 else ''}",
                                "function_review_agent"
                            )
                        log_concurrent_info(f"{'='*60}", "function_review_agent")
                
                return {
                    "finished": True,
                    "result": result,
                    "_raw_content": content,  # 保留原始内容，供重试使用
                    "_parse_error": parse_error  # 保留解析错误信息
                }
        
        except Exception as e:
            log_concurrent_error(f"[Agent审查] AI调用失败", "function_review_agent", e)
            return {
                "finished": True,
                "result": {
                    "problems": [],
                    "function_info": {
                        "function_name": "",
                        "function_description": "AI调用失败",
                        "commented_code": ""
                    }
                }
            }
    
    def _execute_tools(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """执行工具调用"""
        results = []
        
        for tool_call in tool_calls:
            # 从正确的位置获取工具名称和参数
            tool_name = tool_call.get('function', {}).get('name')
            tool_args = tool_call.get('_parsed_arguments', {})
            
            log_concurrent_info(f"   🔧 执行工具: {tool_name}，参数: {tool_args}", "function_review_agent")
            
            try:
                if tool_name == "get_dependency_function":
                    result = self._tool_get_dependency_function(tool_args['function_name'])
                elif tool_name == "get_global_variable":
                    result = self._tool_get_global_variable(tool_args['variable_name'])
                elif tool_name == "search_function_calls":
                    result = self._tool_search_function_calls(tool_args['function_name'])
                elif tool_name == "list_all_globals":
                    result = self._tool_list_all_globals()
                elif tool_name == "get_file_outline":
                    result = self._tool_get_file_outline(tool_args['file_path'])
                elif tool_name == "read_file_range":
                    result = self._tool_read_file_range(
                        tool_args['file_path'],
                        tool_args['start_line'],
                        tool_args['end_line']
                    )
                elif tool_name == "get_call_graph":
                    result = self._tool_get_call_graph(
                        tool_args['function_name'],
                        tool_args.get('direction', 'callees'),
                        tool_args.get('depth', 1)
                    )
                elif tool_name == "search_code":
                    result = self._tool_search_code(
                        tool_args['keyword'],
                        tool_args.get('file_pattern', '*.c')
                    )
                elif tool_name == "list_directory":
                    result = self._tool_list_directory(
                        tool_args.get('relative_path', ''),
                        tool_args.get('max_depth', 2)
                    )
                elif tool_name == "search_function_by_name":
                    result = self._tool_search_function_by_name(
                        tool_args['function_name'],
                        tool_args.get('limit', 10)
                    )
                elif tool_name == "search_function_in_file":
                    result = self._tool_search_function_in_file(
                        tool_args['relative_path'],
                        tool_args['function_name']
                    )
                elif tool_name == "get_function_context":
                    result = self._tool_get_function_context(
                        tool_args['relative_path'],
                        tool_args['line_number']
                    )
                elif tool_name == "get_variable_usage":
                    result = self._tool_get_variable_usage(
                        tool_args['relative_path'],
                        tool_args['variable_name'],
                        tool_args.get('line_number')
                    )
                else:
                    result = {"error": f"未知工具: {tool_name}"}
                
                # 记录工具执行结果的摘要
                result_summary = str(result)[:200] if isinstance(result, dict) else str(result)[:200]
                log_concurrent_info(
                    f"   📦 工具执行成功，返回结果摘要（前200字符）: {result_summary}",
                    "function_review_agent"
                )
                
                results.append(result)
                
            except Exception as e:
                log_concurrent_error(f"[Agent审查] 工具执行失败: {tool_name}", "function_review_agent", e)
                results.append({"error": str(e)})
        
        return results
    
    # ========== 工具实现 ==========
    
    def _tool_get_dependency_function(self, function_name: str) -> Dict[str, Any]:
        """工具：获取依赖函数的代码"""
        try:
            # 检查缓存
            if function_name in self.function_cache:
                return self.function_cache[function_name]
            
            # 常见标准库函数列表
            standard_functions = {
                'malloc', 'free', 'calloc', 'realloc',
                'memcpy', 'memset', 'memmove', 'memcmp',
                'strcpy', 'strncpy', 'strcat', 'strncat', 'strcmp', 'strncmp', 'strlen', 'strstr',
                'printf', 'fprintf', 'sprintf', 'snprintf', 'scanf', 'fscanf', 'sscanf',
                'fopen', 'fclose', 'fread', 'fwrite', 'fseek', 'ftell', 'feof', 'ferror',
                'exit', 'abort', 'atexit', 'system',
                'sin', 'cos', 'tan', 'sqrt', 'pow', 'exp', 'log',
                'time', 'clock', 'sleep', 'usleep'
            }
            
            # 如果是标准库函数，直接返回友好提示
            if function_name.lower() in standard_functions:
                result = {
                    "function_name": function_name,
                    "found": False,
                    "is_standard_library": True,
                    "message": f"{function_name} 是C标准库函数，无需查看实现。请基于你对标准库的理解进行审查。"
                }
                self.function_cache[function_name] = result
                return result
            
            # 收集函数依赖
            deps = collect_function_with_dependencies(
                entry_function=function_name,
                project_root=str(self.project_root),
                language=self.language,
                max_depth=0  # 只获取这个函数本身
            )
            
            if function_name in deps:
                func_info = deps[function_name]
                result = {
                    "function_name": function_name,
                    "source_code": func_info['source_code'],
                    "file_path": func_info['file_path'],
                    "found": True
                }
            else:
                result = {
                    "function_name": function_name,
                    "found": False,
                    "is_standard_library": False,
                    "message": f"未找到函数 {function_name}，可能是外部库函数、系统调用或函数名不准确"
                }
            
            # 缓存结果
            self.function_cache[function_name] = result
            return result
            
        except Exception as e:
            return {
                "function_name": function_name,
                "found": False,
                "error": f"查找函数时出错: {str(e)}"
            }
    
    def _tool_get_global_variable(self, variable_name: str) -> Dict[str, Any]:
        """工具：获取全局变量/宏定义"""
        try:
            if not self.global_var_cache:
                return {
                    "variable_name": variable_name,
                    "found": False,
                    "message": "全局变量缓存为空"
                }
            
            if variable_name in self.global_var_cache:
                var_info = self.global_var_cache[variable_name]
                return {
                    "variable_name": variable_name,
                    "type": var_info.get('type', 'variable'),
                    "file": var_info.get('file', ''),
                    "line": var_info.get('line', 0),
                    "code": var_info.get('code', ''),
                    "found": True
                }
            else:
                return {
                    "variable_name": variable_name,
                    "found": False,
                    "message": f"未找到全局变量 {variable_name}"
                }
        
        except Exception as e:
            return {
                "variable_name": variable_name,
                "found": False,
                "error": str(e)
            }
    
    def _tool_search_function_calls(self, function_name: str) -> Dict[str, Any]:
        """工具：搜索函数调用"""
        try:
            # 简单实现：在项目中搜索函数调用
            call_pattern = re.compile(r'\b' + re.escape(function_name) + r'\s*\(')
            callers = []
            
            # 搜索.c和.h文件
            for ext in ['.c', '.cpp', '.h', '.hpp']:
                for file_path in self.project_root.rglob(f'*{ext}'):
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                        
                        for i, line in enumerate(lines, 1):
                            if call_pattern.search(line):
                                callers.append({
                                    "file": str(file_path.relative_to(self.project_root)),
                                    "line": i,
                                    "code": line.strip()
                                })
                                
                                if len(callers) >= 10:  # 最多返回10个
                                    break
                    except:
                        continue
                    
                    if len(callers) >= 10:
                        break
            
            return {
                "function_name": function_name,
                "caller_count": len(callers),
                "callers": callers[:10]
            }
        
        except Exception as e:
            return {
                "function_name": function_name,
                "error": str(e)
            }
    
    def _tool_list_all_globals(self) -> Dict[str, Any]:
        """工具：列出所有可用的全局变量"""
        try:
            if not self.global_var_cache:
                return {"globals": [], "count": 0}
            
            globals_list = []
            for name, info in list(self.global_var_cache.items())[:50]:  # 最多50个
                globals_list.append({
                    "name": name,
                    "type": info.get('type', 'variable'),
                    "file": info.get('file', '')
                })
            
            return {
                "count": len(self.global_var_cache),
                "globals": globals_list,
                "message": f"共有 {len(self.global_var_cache)} 个全局项，显示前50个"
            }
        
        except Exception as e:
            return {"error": str(e)}
    
    def _tool_get_file_outline(self, file_path: str) -> Dict[str, Any]:
        """工具：获取文件大纲"""
        try:
            full_path = Path(self.project_root) / file_path
            
            if not full_path.exists():
                return {"error": f"文件不存在: {file_path}"}
            
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 提取函数、宏、include
            functions = re.findall(
                r'^\s*(?:static\s+)?(?:void|int|char|float|double|long|short|unsigned|uint\w*|int\w*)\s+(\w+)\s*\(',
                content,
                re.MULTILINE
            )
            macros = re.findall(r'^\s*#define\s+(\w+)', content, re.MULTILINE)
            includes = re.findall(r'^\s*#include\s+[<"](.+?)[>"]', content, re.MULTILINE)
            
            return {
                "file": file_path,
                "functions": functions[:50],  # 限制50个
                "macros": macros[:30],
                "includes": includes,
                "total_lines": content.count('\n') + 1
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _tool_read_file_range(self, file_path: str, start_line: int, end_line: int) -> Dict[str, Any]:
        """工具：按行范围读取文件"""
        try:
            full_path = Path(self.project_root) / file_path
            
            if not full_path.exists():
                return {"error": f"文件不存在: {file_path}"}
            
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # 行号从1开始
            if start_line < 1 or end_line > len(lines):
                return {"error": f"行号范围无效: {start_line}-{end_line}，文件共 {len(lines)} 行"}
            
            selected_lines = lines[start_line - 1:end_line]
            content = ''.join(selected_lines)
            
            return {
                "file": file_path,
                "start_line": start_line,
                "end_line": end_line,
                "content": content,
                "line_count": len(selected_lines)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _tool_get_call_graph(self, function_name: str, direction: str = "callees", depth: int = 1) -> Dict[str, Any]:
        """工具：获取函数调用关系图（使用统一的CallGraphQuery）"""
        try:
            # 检查调用图是否存在
            # 将调用图文件放在当前项目根目录（extract_path）下，避免跨项目覆盖
            call_graph_file = Path(self.project_root) / "call_graph.json"
            
            log_concurrent_debug(
                f"[Agent审查] 查找调用图文件: {call_graph_file}, 存在: {call_graph_file.exists()}",
                "function_review_agent"
            )
            
            if not call_graph_file.exists():
                return {
                    "function_name": function_name,
                    "direction": direction,
                    "error": "调用图文件不存在，请确保已在审查开始时生成调用图",
                    "callees": [],
                    "callers": [],
                    "note": "需要在阶段0生成调用图文件"
                }
            
            # 使用统一的 CallGraphQuery
            from ..business_review.tools.call_graph_query import CallGraphQuery
            query_tool = CallGraphQuery(call_graph_file)
            
            # 记录调用图统计信息
            stats = query_tool.get_statistics()
            log_concurrent_debug(
                f"[Agent审查] 调用图统计: 项目={stats.get('project', {})}, 函数数={stats.get('total_functions', 0)}",
                "function_review_agent"
            )
            
            # 使用query方法获取调用关系（统一接口）
            result = query_tool.query(
                function_name=function_name,
                depth=min(depth, 3),  # 限制最大深度为3
                direction=direction
            )
            
            # 检查是否有错误
            if "error" in result:
                log_concurrent_warning(
                    f"[Agent审查] 调用图查询失败 '{function_name}': {result['error']}",
                    "function_review_agent"
                )
                
                # 提供调试信息
                all_functions = list(query_tool.functions.keys())[:10]
                function_names = [query_tool.functions[fid].get('name', fid) for fid in all_functions]
                
                log_concurrent_debug(
                    f"[Agent审查] 调用图中的函数示例（前10个）: {function_names}",
                    "function_review_agent"
                )
            
            # 直接返回 CallGraphQuery 的查询结果（统一格式）
            log_concurrent_debug(
                f"[Agent审查] 工具执行成功: get_call_graph，返回结果摘要（前200字符）: {str(result)[:200]}",
                "function_review_agent"
            )
            
            return result
        except Exception as e:
            return {"error": str(e)}
    
    def _tool_search_code(self, keyword: str, file_pattern: str = "*.c") -> Dict[str, Any]:
        """工具：搜索代码关键字"""
        try:
            import glob as glob_module
            
            # 构建搜索模式
            if not file_pattern:
                file_pattern = "*.c"
            
            search_pattern = str(Path(self.project_root) / "**" / file_pattern)
            files = glob_module.glob(search_pattern, recursive=True)
            
            results = []
            max_results = 30  # 限制结果数量
            
            for file_path in files[:100]:  # 最多搜索100个文件
                if len(results) >= max_results:
                    break
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    
                    for line_num, line in enumerate(lines, 1):
                        if keyword in line:
                            rel_path = Path(file_path).relative_to(self.project_root)
                            results.append({
                                "file": str(rel_path),
                                "line": line_num,
                                "content": line.strip()
                            })
                            
                            if len(results) >= max_results:
                                break
                except:
                    continue
            
            return {
                "keyword": keyword,
                "file_pattern": file_pattern,
                "results": results,
                "count": len(results),
                "note": f"最多显示{max_results}个结果" if len(results) == max_results else ""
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _tool_list_directory(self, relative_path: str = "", max_depth: int = 2) -> Dict[str, Any]:
        """工具：列出目录内容"""
        try:
            target_path = self.project_root / relative_path if relative_path else self.project_root
            
            if not target_path.exists():
                return {"error": f"路径不存在: {relative_path}"}
            
            if not target_path.is_dir():
                return {"error": f"不是目录: {relative_path}"}
            
            def scan_directory(path, current_depth):
                if current_depth >= max_depth:
                    return []
                
                items = []
                try:
                    for item in sorted(path.iterdir()):
                        if item.name.startswith('.') or item.name in ['__pycache__', 'node_modules']:
                            continue
                        
                        rel_path = item.relative_to(self.project_root)
                        
                        if item.is_dir():
                            items.append({
                                "type": "directory",
                                "name": item.name,
                                "path": str(rel_path)
                            })
                        elif item.is_file() and item.suffix.lower() in self.allowed_extensions:
                            items.append({
                                "type": "file",
                                "name": item.name,
                                "path": str(rel_path),
                                "extension": item.suffix,
                                "size": item.stat().st_size
                            })
                except Exception as e:
                    items.append({"error": f"扫描失败: {str(e)}"})
                
                return items
            
            result = scan_directory(target_path, 0)
            return {
                "path": relative_path or ".",
                "content": result
            }
        except Exception as e:
            return {"error": f"列出目录失败: {str(e)}"}
    
    def _tool_search_function_by_name(self, function_name: str, limit: int = 10) -> Dict[str, Any]:
        """工具：按函数名搜索函数"""
        try:
            # 在代码中搜索函数定义
            pattern = re.compile(r'^\s*(?:static\s+)?(?:void|int|char|float|double|long|short|unsigned|uint\w*|int\w*)\s+' + re.escape(function_name) + r'\s*\(', re.MULTILINE)
            results = []
            
            for file_path in self.project_root.rglob('*'):
                if file_path.suffix.lower() in self.allowed_extensions:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        if pattern.search(content):
                            # 找到函数，提取行号
                            lines = content.split('\n')
                            for i, line in enumerate(lines, 1):
                                if function_name in line and '(' in line:
                                    results.append({
                                        "function_name": function_name,
                                        "file_path": str(file_path.relative_to(self.project_root)),
                                        "line": i,
                                        "has_source": True
                                    })
                                    break
                        
                        if len(results) >= limit:
                            break
                    except:
                        continue
            
            return {
                "function_name": function_name,
                "result_count": len(results),
                "results": results[:limit]
            }
        except Exception as e:
            return {"error": f"搜索函数失败: {str(e)}"}
    
    def _tool_search_function_in_file(self, relative_path: str, function_name: str) -> Dict[str, Any]:
        """工具：在文件中搜索特定函数"""
        try:
            file_path = self.project_root / relative_path
            
            if not file_path.exists():
                return {"error": f"文件不存在: {relative_path}"}
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 简单的函数搜索
            lines = content.split('\n')
            function_start = -1
            function_end = -1
            brace_count = 0
            found = False
            
            for i, line in enumerate(lines):
                if function_name in line and ('(' in line or '{' in line):
                    stripped = line.strip()
                    if not stripped.startswith('//') and not stripped.startswith('/*'):
                        function_start = i
                        found = True
                
                if found:
                    brace_count += line.count('{') - line.count('}')
                    if brace_count == 0 and '{' in ''.join(lines[function_start:i+1]):
                        function_end = i
                        break
            
            if function_start == -1:
                return {
                    "error": f"在文件 {relative_path} 中未找到函数 {function_name}",
                    "suggestion": "请检查函数名是否正确"
                }
            
            if function_end == -1:
                function_end = min(function_start + 50, len(lines) - 1)
            
            function_code = '\n'.join(lines[function_start:function_end + 1])
            
            return {
                "path": relative_path,
                "function_name": function_name,
                "start_line": function_start + 1,
                "end_line": function_end + 1,
                "code": function_code
            }
        except Exception as e:
            return {"error": f"搜索函数失败: {str(e)}"}
    
    def _tool_get_function_context(self, relative_path: str, line_number: int) -> Dict[str, Any]:
        """工具：获取指定行所在函数的完整代码"""
        try:
            file_path = self.project_root / relative_path
            
            if not file_path.exists():
                return {"error": f"文件不存在: {relative_path}"}
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            if line_number < 1 or line_number > len(lines):
                return {"error": f"行号超出范围: {line_number}"}
            
            # 向上搜索函数开始
            function_start = line_number - 1
            for i in range(line_number - 1, -1, -1):
                line = lines[i].strip()
                if line and not line.startswith('//') and '(' in line:
                    if any(keyword in line for keyword in ['void', 'int', 'char', 'float', 'double', 'static']):
                        function_start = i
                        break
            
            # 向下搜索函数结束
            brace_count = 0
            function_end = len(lines) - 1
            started_counting = False
            
            for i in range(function_start, len(lines)):
                line = lines[i]
                if '{' in line:
                    started_counting = True
                if started_counting:
                    brace_count += line.count('{') - line.count('}')
                    if brace_count == 0:
                        function_end = i
                        break
            
            function_code = ''.join(lines[function_start:function_end + 1])
            
            return {
                "file": relative_path,
                "target_line": line_number,
                "function_start_line": function_start + 1,
                "function_end_line": function_end + 1,
                "code": function_code
            }
        except Exception as e:
            return {"error": f"获取函数上下文失败: {str(e)}"}
    
    def _tool_get_variable_usage(self, relative_path: str, variable_name: str, line_number: int = None) -> Dict[str, Any]:
        """工具：追踪变量在文件中的所有使用位置"""
        try:
            file_path = self.project_root / relative_path
            
            if not file_path.exists():
                return {"error": f"文件不存在: {relative_path}"}
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # 搜索变量使用
            pattern = re.compile(r'\b' + re.escape(variable_name) + r'\b')
            usages = []
            
            start_line = line_number if line_number else 1
            for i in range(start_line - 1, len(lines)):
                line = lines[i]
                if pattern.search(line):
                    # 判断使用类型
                    usage_type = "read"
                    if '=' in line and variable_name in line.split('=')[0]:
                        usage_type = "write"
                    elif any(keyword in line for keyword in ['int ', 'char ', 'float ', 'double ']):
                        usage_type = "declaration"
                    
                    usages.append({
                        "line": i + 1,
                        "code": line.strip(),
                        "type": usage_type
                    })
                    
                    if len(usages) >= 20:  # 限制结果数量
                        break
            
            return {
                "file": relative_path,
                "variable_name": variable_name,
                "usage_count": len(usages),
                "usages": usages
            }
        except Exception as e:
            return {"error": f"追踪变量使用失败: {str(e)}"}
    
    def _fix_truncated_json(self, json_str: str) -> str:
        """
        修复被截断的JSON：当commented_code过长导致JSON截断时，
        截断commented_code字段并补全JSON结构。
        """
        import re
        # 找到 commented_code 字段的起始位置
        match = re.search(r'"commented_code"\s*:\s*"', json_str)
        if not match:
            return json_str
        
        # 截断到 commented_code 之前，把 commented_code 设为空字符串
        truncate_pos = match.start()
        prefix = json_str[:truncate_pos]
        
        # 移除 prefix 末尾的逗号和空白，补全 JSON
        prefix = prefix.rstrip().rstrip(',')
        
        # 检查 function_info 结构是否已开始
        # 需要补全 function_info 对象和根对象
        open_braces = prefix.count('{') - prefix.count('}')
        
        suffix = ',\n    "commented_code": ""'
        suffix += '\n  }' * max(0, open_braces - 1)
        suffix += '\n}'
        
        fixed = prefix + suffix
        try:
            import json as _json
            _json.loads(fixed)
            return fixed
        except Exception:
            return json_str

    def _fix_unescaped_newlines_in_json(self, json_str: str) -> str:
        """
        智能修复JSON字符串中未转义的换行符和其他控制字符
        
        处理逻辑：
        1. 遍历JSON字符串，跟踪是否在字符串值内部
        2. 在字符串值内部时，转义所有控制字符（\n, \r, \t等）
        3. 保持JSON结构的换行和缩进不变
        """
        result = []
        in_string = False  # 是否在字符串内部
        escape_next = False  # 下一个字符是否被转义
        
        i = 0
        while i < len(json_str):
            char = json_str[i]
            
            if escape_next:
                # 当前字符被转义，直接添加
                result.append(char)
                escape_next = False
                i += 1
                continue
            
            if char == '\\':
                # 反斜杠，可能是转义字符的开始
                result.append(char)
                escape_next = True
                i += 1
                continue
            
            if char == '"':
                # 双引号：切换字符串状态
                result.append(char)
                in_string = not in_string
                i += 1
                continue
            
            if in_string:
                # 在字符串内部，需要转义控制字符
                if char == '\n':
                    result.append('\\n')  # 转义换行符
                elif char == '\r':
                    result.append('\\r')  # 转义回车符
                elif char == '\t':
                    result.append('\\t')  # 转义制表符
                elif char == '\b':
                    result.append('\\b')  # 转义退格符
                elif char == '\f':
                    result.append('\\f')  # 转义换页符
                elif ord(char) < 32:
                    # 其他控制字符，使用unicode转义
                    result.append(f'\\u{ord(char):04x}')
                else:
                    result.append(char)
            else:
                # 不在字符串内部，保持原样（包括JSON结构的换行和缩进）
                result.append(char)
            
            i += 1
        
        return ''.join(result)
    
    def _parse_final_result(self, content: str) -> Tuple[Dict[str, Any], str]:
        """解析AI的最终结果，返回(结果字典, 错误信息)"""
        parse_error = ""
        try:
            # 移除markdown代码块标记
            content = content.replace('```json', '').replace('```', '').strip()
            
            # 尝试找到JSON对象
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                json_str = json_match.group()
                
                # 记录完整的原始JSON字符串
                log_concurrent_debug(
                    f"[Agent审查] 提取的完整JSON字符串（长度: {len(json_str)}）：\n{'='*60}\n{json_str}\n{'='*60}",
                    "function_review_agent"
                )
                
                # 第一次尝试：直接解析
                try:
                    result = json.loads(json_str)
                    
                    # 验证必需字段
                    if 'problems' in result and 'function_info' in result:
                        log_concurrent_info(f"[Agent审查] JSON解析成功", "function_review_agent")
                        return result, ""  # 成功，无错误
                    else:
                        log_concurrent_warning(f"[Agent审查] JSON缺少必需字段", "function_review_agent")
                        parse_error = "JSON缺少必需字段(problems或function_info)"
                
                except json.JSONDecodeError as json_err:
                    # JSON解析失败，尝试修复常见问题
                    parse_error = str(json_err)
                    log_concurrent_warning(
                        f"[Agent审查] JSON解析失败: {parse_error}", 
                        "function_review_agent"
                    )
                    
                    # 记录失败时的完整JSON
                    log_concurrent_error(
                        f"[Agent审查] JSON解析失败，完整原始JSON：\n{'='*60}\n{json_str}\n{'='*60}",
                        "function_review_agent"
                    )
                    
                    # 尝试修复：智能转义JSON字符串中的未转义换行符
                    log_concurrent_info(
                        f"[Agent审查] 尝试修复JSON中的未转义换行符...",
                        "function_review_agent"
                    )
                    fixed_json = self._fix_unescaped_newlines_in_json(json_str)
                    
                    # 第二次尝试：使用修复后的JSON
                    try:
                        result = json.loads(fixed_json)
                        if 'problems' in result and 'function_info' in result:
                            log_concurrent_info(
                                f"[Agent审查] JSON修复成功！已转义未转义的换行符", 
                                "function_review_agent"
                            )
                            return result, ""  # 修复成功，无错误
                    except Exception as fix_err:
                        parse_error = f"JSON修复失败: {str(fix_err)}"
                        log_concurrent_error(
                            f"[Agent审查] {parse_error}",
                            "function_review_agent"
                        )
                        # 第三次尝试：修复截断的JSON（commented_code太长被截断）
                        log_concurrent_info(
                            f"[Agent审查] 尝试修复截断的JSON（commented_code过长）...",
                            "function_review_agent"
                        )
                        truncated_fixed = self._fix_truncated_json(json_str)
                        try:
                            result = json.loads(truncated_fixed)
                            if 'problems' in result and 'function_info' in result:
                                log_concurrent_info(
                                    f"[Agent审查] JSON截断修复成功！commented_code已置空",
                                    "function_review_agent"
                                )
                                return result, ""
                        except Exception as trunc_err:
                            parse_error = f"JSON截断修复也失败: {str(trunc_err)}"
                            log_concurrent_error(
                                f"[Agent审查] {parse_error}",
                                "function_review_agent"
                            )
            else:
                # 没有找到JSON对象
                parse_error = "未找到JSON对象"
                log_concurrent_error(
                    f"[Agent审查] {parse_error}，完整响应内容：\n{'='*60}\n{content}\n{'='*60}",
                    "function_review_agent"
                )
            
            # 如果所有尝试都失败，返回默认值
            log_concurrent_warning(
                f"[Agent审查] 无法解析AI结果，返回默认值。内容前200字符: {content[:200]}", 
                "function_review_agent"
            )
            return {
                "problems": [],
                "function_info": {
                    "function_name": "",
                    "function_description": "解析失败：AI返回的JSON格式错误",
                    "commented_code": ""
                }
            }, parse_error
        
        except Exception as e:
            parse_error = f"异常: {str(e)}"
            log_concurrent_error(f"[Agent审查] 解析结果失败", "function_review_agent", e)
            return {
                "problems": [],
                "function_info": {
                    "function_name": "",
                    "function_description": "解析错误",
                    "commented_code": ""
                }
            }, parse_error

