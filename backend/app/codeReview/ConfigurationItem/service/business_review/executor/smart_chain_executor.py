"""
智能链路审查执行器 - 基于AI发现的功能模块进行深度审查

使用ReAct模式：
1. AI根据功能描述，自主使用工具探索代码
2. 理解代码后，识别业务逻辑问题
3. 生成问题单

核心特点：
- 上下文控制：每个功能模块单独审查，避免超token
- 工具驱动：AI调用7个代码分析工具
- 业务导向：关注业务逻辑问题，非编码规范
"""
import json
import re
from typing import Dict, Any, List, Optional, cast, Tuple, Pattern
from pathlib import Path

from ...ai.openai.client import AIClient
from ...ai.parser.fpga.fpga_parser import extract_fpga_files_from_code, read_file_with_encoding
from ....utils.concurrent_logger import log_concurrent_info, log_concurrent_warning, log_concurrent_debug, log_concurrent_error
from ..tools.call_graph_query import CallGraphQuery
from ...ai.analysis_runner import normalize_problem


class SmartChainExecutor:
    """智能链路审查执行器"""
    
    def __init__(self, project_root: str, session_id: str = None, language: str = 'c'):
        log_concurrent_info("[SmartChainExecutor] 开始初始化...", "smart_chain_executor")
        self.project_root = Path(project_root)
        self.session_id = session_id or "smart_chain"
        self.language = language
        
        # 使用链路审查专用配置文件
        # 路径: executor -> business_review -> service -> ConfigurationItem -> codeReview -> app -> utils
        chain_review_config_path = (
            Path(__file__).parent  # executor
            .parent  # business_review
            .parent  # service
            .parent  # ConfigurationItem
            .parent  # codeReview
            .parent  # app
            / "utils" / "chain_review_config.json"
        )
        log_concurrent_info(f"[SmartChainExecutor] 配置文件路径: {chain_review_config_path}", "smart_chain_executor")
        log_concurrent_info("[SmartChainExecutor] 正在创建 AIClient...", "smart_chain_executor")
        self.ai_client = AIClient(config_path=str(chain_review_config_path))
        log_concurrent_info("[SmartChainExecutor] AIClient 创建完成", "smart_chain_executor")
        
        # Agent配置
        self.max_iterations = 30  # 增加到30轮，给AI更多探索时间
        # 不限制每轮工具调用次数，让AI自由探索
        
        # 工具映射
        self.tools = CodeAnalysisTools(project_root, language=language)
        self.tool_map = {
            "list_directory": self.tools.list_directory,
            "search_function_by_name": self.tools.search_function_by_name,
            "search_function_in_file": self.tools.search_function_in_file,
            "get_file_outline": self.tools.get_file_outline,
            "read_file_range": self.tools.read_file_range,
            "get_function_context": self.tools.get_function_context,
            "get_variable_usage": self.tools.get_variable_usage,
            "get_call_graph": self.tools.get_call_graph,
            "search_code": self.tools.search_code,
            "get_dependency_function": self.tools.get_dependency_function,
            "get_global_variable": self.tools.get_global_variable,
            "search_function_calls": self.tools.search_function_calls,
            "list_all_globals": self.tools.list_all_globals,
        }
    
    def review_feature(
        self,
        feature: Dict[str, Any],
        kb: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], str]:
        """
        审查单个功能模块
        
        Args:
            feature: 功能信息
            kb: 知识库
            
        Returns:
            问题列表
        """
        feature_name = feature.get('name', '未命名功能')
        log_concurrent_info(f"[review_feature] ========== 进入审查方法: {feature_name} ==========", "smart_chain_executor")
        log_concurrent_info(f"[智能审查] 开始审查功能: {feature_name}", "smart_chain_executor")
        
        # 初始化对话历史
        conversation = []
        
        # 系统提示词
        system_prompt = self._build_system_prompt(kb, feature)
        conversation.append({"role": "system", "content": system_prompt})
        
        # 初始任务
        initial_task = self._build_initial_task(feature)
        conversation.append({"role": "user", "content": initial_task})
        
        # ReAct循环
        problems = []
        feature_description = ''
        early_stop_reason = None
        reached_max_iterations = True
        for iteration in range(self.max_iterations):
            log_concurrent_debug(f"[智能审查] 第 {iteration + 1} 轮推理", "smart_chain_executor")
            
            # 调用AI（支持function calling）
            response = self._call_ai_with_tools(conversation)
            log_concurrent_debug(
                f"[智能审查] 第 {iteration + 1} 轮AI返回: finished={response.get('finished')}, "
                f"content长度={len(response.get('content', '') or '')}, tool_calls={len(response.get('tool_calls') or [])}",
                "smart_chain_executor"
            )
            if response.get('content'):
                log_concurrent_debug(
                    f"[智能审查] AI内容:\n{response.get('content')}", 
                    "smart_chain_executor"
                )
            
            # 检查是否完成
            if response.get('finished'):
                problems = response.get('problems', [])
                feature_description = response.get('feature_description', '')
                reached_max_iterations = False
                early_stop_reason = response.get('stop_reason') or "ai_finished"
                log_concurrent_info(f"[智能审查] 审查完成，发现 {len(problems)} 个问题", "smart_chain_executor")
                break
            
            # 执行工具调用
            if response.get('tool_calls'):
                tool_results = self._execute_tools(response['tool_calls'])
                for tool_result in tool_results:
                    log_concurrent_debug(
                        f"[智能审查] 工具返回[{tool_result['tool_call_id']}]: {tool_result['content']}",
                        "smart_chain_executor"
                    )
                
                # 将tool_calls转换为OpenAI格式
                openai_tool_calls = []
                for tc in response['tool_calls']:
                    openai_tool_calls.append({
                        "id": tc['id'],
                        "type": "function",
                        "function": {
                            "name": tc['name'],
                            "arguments": json.dumps(tc['arguments'], ensure_ascii=False)
                        }
                    })
                
                # 添加AI响应到历史
                conversation.append({
                    "role": "assistant",
                    "content": response.get('content', ''),
                    "tool_calls": openai_tool_calls
                })
                
                # 添加工具结果到历史
                for tool_result in tool_results:
                    conversation.append({
                        "role": "tool",
                        "tool_call_id": tool_result['tool_call_id'],
                        "content": tool_result['content']
                    })
            else:
                # 没有工具调用，可能是直接回答
                conversation.append({
                    "role": "assistant",
                    "content": response.get('content', '')
                })
                
                # 检查是否包含最终答案
                if '【最终问题单】' in response.get('content', ''):
                    result = self._extract_result_from_response(response.get('content', ''))
                    problems = result['problems']
                    feature_description = result.get('feature_description', '')
                    reached_max_iterations = False
                    early_stop_reason = "final_marker_in_content"
                    break
        
        # 如果没有返回问题单，强制让AI总结
        if not problems:
            if reached_max_iterations:
                log_concurrent_warning(
                    f"[智能审查] 已达到最大迭代次数({self.max_iterations})且AI未返回问题单，强制请求总结",
                    "smart_chain_executor"
                )
            else:
                log_concurrent_warning(
                    f"[智能审查] AI提前结束（原因: {early_stop_reason or 'unknown'}）但未返回问题单，强制请求总结",
                    "smart_chain_executor"
                )
            conversation.append({
                "role": "user",
                "content": """
请立即完成审查并输出【最终问题单】。

**重要说明**：
1. 如果你已经审查了关键代码，请基于审查结果输出问题单
2. 如果你发现代码中确实存在问题，请详细列出
3. 如果你尝试查找某些函数但找不到，可能是因为：
   - 该功能在实际代码中不存在
   - 该功能的命名与预期不同
   - 该功能分散在其他文件中
4. **如果确实没有发现问题，请返回空的问题列表**

无论如何，请现在就输出【最终问题单】，格式如下：
【最终问题单】
```json
{
  "problems": []
}
```
"""
            })
            
            final_response = self._call_ai_with_tools(conversation)
            if final_response.get('content'):
                result = self._extract_result_from_response(final_response.get('content'))
                problems = result['problems']
                feature_description = result.get('feature_description', '')
                log_concurrent_info(
                    f"[智能审查] 强制总结后提取到 {len(problems)} 个问题",
                    "smart_chain_executor"
                )
        
        log_concurrent_info(f"[智能审查] 功能 {feature_name} 审查结束，发现 {len(problems)} 个问题", "smart_chain_executor")
        return problems, feature_description
    
    def _build_system_prompt(self, kb: Dict[str, Any], feature: Dict[str, Any]) -> str:
        """构建系统提示词"""
        kb_text = kb.get('kb_text', '')[:2000]
        defect_text = kb.get('defect_text', '')[:1500]
        
        # 提取关键链路信息
        key_functions = feature.get('key_functions', [])
        code_unit_name = '模块/实体' if self.language == 'fpga' else '函数'
        domain_name = 'FPGA设计审查' if self.language == 'fpga' else '软件审查'
        call_chain = feature.get('call_chain', '')
        related_files = feature.get('related_files', [])
        
        # 构建链路信息文本
        chain_info = ""
        if call_chain:
            chain_info += f"\n**调用链路**: {call_chain}"
        if key_functions:
            chain_info += f"\n**关键函数**: {', '.join(key_functions[:10])}"
        if related_files:
            chain_info += f"\n**相关文件**: {', '.join(related_files[:10])}"
        
        return f"""你是一位资深的{domain_name}专家，擅长发现业务逻辑问题。

【审查目标】
审查功能模块：{feature.get('name')}
功能描述：{feature.get('description')}
{chain_info}

【审查重点】
**你的任务是沿着调用链路深入审查，找出业务逻辑问题**，包括但不限于：
1. **资源泄漏**：内存、文件句柄、网络连接未释放
2. **错误处理缺失**：关键操作没有检查返回值或捕获异常
3. **边界条件**：空指针、数组越界、除零等未检查
4. **并发问题**：资源竞争、死锁风险
5. **业务逻辑错误**：状态机错误、业务流程不完整
6. **安全问题**：输入验证缺失、权限检查缺失

**审查策略**：
1. **从入口开始**：如果有key_functions，从第一个关键代码单元开始
2. **沿着调用链深入**：使用get_call_graph追踪关键代码单元之间的关系
3. **重点关注**：
   - 资源申请与释放是否配对
   - 错误分支是否正确处理
   - 边界条件是否检查
   - 并发访问是否安全

【可用工具】
1. get_file_outline - 获取文件结构（函数列表、宏定义等）- **首选工具**
2. read_file_range - 读取文件指定行范围
3. get_function_context - 获取指定行所在函数的完整代码
4. search_function_by_name - 搜索函数定义
5. get_call_graph - **获取函数调用关系图，用于追踪链路**
6. get_variable_usage - 查找变量的使用位置
7. search_code - 搜索代码片段

【领域知识】
{kb_text}

【典型缺陷】
{defect_text}

【问题单格式】
当你完成代码审查后，**必须严格按照如下JSON结构输出分析结果**：

## 问题分析字段含义：
- `file_name`：链路名称（功能模块名称，如"信号采集与处理"）
- `source_code`：出问题的代码片段（导致问题的具体代码段，去掉多余空格，保持原始语法）
- `problem_reason`：问题原因（简洁描述为什么会有这个问题，如"未检查返回值"、"资源未释放"、"缓冲区溢出风险"等）
- `issue_level`：问题等级（**必须**是以下三个值之一：**建议改进**、**一般问题**、**重要问题**）
- `issue_name`：问题名称（简洁明确的问题标题，如"日志文件句柄泄漏"）
- `issue_location`：问题来源（文件名+函数名，格式：`example.c:foo`）
- `description_requirement`：需求描述（说明应该遵循的需求或规范）
- `description_issue`：问题描述（详细描述发现的问题，包含代码片段和上下文）
- `description_location`：问题定位，**必须严格按照以下格式**：`xx文件的xx函数的xx行：问题代码语句源代码为：\\n保留关键上下文的源代码`
  - 示例：`example.c文件的foo函数的3行：gets(buf);源代码为：\\nvoid foo() {{\\n    char buf[10];\\n    gets(buf);\\n}}`
  - 示例：`radar_system.c文件的cleanup_system函数的284行：fclose(log_file);源代码为：\\nvoid cleanup_system() {{\\n    ......\\n    free_signal_buffer();\\n    fclose(log_file);\\n    ......\\n}}`
  - **重要**：问题代码语句是最关键的定位信息，必须先写在`源代码为：`之前，前端将使用该代码语句进行精确匹配
  - `源代码为：`后必须原样保留问题所在函数的关键上下文源代码；无关代码可以使用`......`省略，但问题代码语句及其必要上下文必须保持源代码原样
  - 问题代码语句应该是导致问题的**具体代码片段**，去掉多余空格，保持原始语法
  - 在JSON字符串中，`description_location`里的源码换行必须使用`\\n`表示，不能直接换行
- `description_impact`：影响分析（说明问题可能导致的后果）

**输出示例：**

【最终问题单】
```json
{{
  "problems": [
    {{
      "file_name": "信号采集与处理链路",
      "source_code": "void cleanup_system() {{\\n    // 释放缓冲区\\n    free_signal_buffer();\\n    // 日志文件未关闭\\n}}",
      "problem_reason": "日志文件句柄未释放，导致资源泄漏",
      "issue_level": "重要问题",
      "issue_name": "日志文件句柄泄漏",
      "issue_location": "radar_system.c:cleanup_system",
      "description_requirement": "系统在关闭时应释放所有资源，包括文件句柄",
      "description_issue": "在cleanup_system函数中，只释放了信号缓冲区，但没有关闭之前打开的日志文件（log_file），导致文件句柄泄漏。",
      "description_location": "radar_system.c文件的cleanup_system函数的284行：free_signal_buffer();源代码为：\\nvoid cleanup_system() {{\\n    // 释放缓冲区\\n    free_signal_buffer();\\n    // 日志文件未关闭\\n}}",
      "description_impact": "长期运行可能导致系统文件句柄耗尽，影响系统稳定性"
    }}
  ],
  "chain_info": {{
    "chain_name": "系统初始化",
    "chain_description": "系统启动时按顺序调用 radar_init、signal_processor_init、tracker_init 完成各模块初始化，若任一步骤失败则逆序清理已初始化模块并返回错误码。"
  }}
}}
```

## 严格的JSON格式要求：
1. 必须返回标准的、可解析的JSON格式
2. 所有字符串值必须使用双引号(")，不能使用单引号(')
3. 字符串中如有双引号，必须使用反斜杠转义(\\")
4. 不要在JSON中包含任何控制字符、换行符或特殊格式字符（代码中的换行用\\n表示）
5. 字段值中不要包含未转义的特殊字符，如反斜杠、制表符等
6. 确保所有字段名和值严格遵循上述模板格式
7. 所有数组元素和对象属性必须使用逗号分隔，最后一项后不能有逗号
8. **issue_level字段必须严格使用"建议改进"、"一般问题"、"重要问题"三个值之一，不得使用其他值**
9. **chain_info字段必须包含 chain_name（功能模块名称）和 chain_description（1-3句话描述该功能模块的核心实现逻辑，基于你阅读的代码）**
10. 如果代码完全符合要求，返回 {{"problems": [], "chain_info": {{"chain_name": "功能名称", "chain_description": "功能描述"}}}}
11. 你的整个回复必须是【最终问题单】标记后紧跟一个单一的、完整的JSON对象。在JSON对象之前只能有【最终问题单】和```json标记，在JSON对象之后只能有```标记。
11. **description_location 字段必须严格按照 `xx文件的xx函数的xx行：问题代码语句源代码为：\\n保留关键上下文的源代码` 的格式**
12. **问题代码语句是最重要的定位信息**，必须写在`源代码为：`之前，前端将使用代码语句进行全字匹配定位
13. **源代码为：后必须保留问题所在函数的关键上下文源代码，无关代码可以用......省略**

【重要提示】
- **不要浅尝辄止**：必须深入阅读关键函数的完整代码
- **寻找真实问题**：资源泄漏、错误处理缺失、边界条件未检查等
- **如果确实没问题，才返回空列表**
- **每个功能至少要审查3-5个关键代码单元的完整实现**
"""
    
    def _build_initial_task(self, feature: Dict[str, Any]) -> str:
        """构建初始任务"""
        key_functions = feature.get('key_functions', [])
        related_files = feature.get('related_files', [])
        call_chain = feature.get('call_chain', '')
        code_unit_name = '模块/实体' if self.language == 'fpga' else '函数'
        
        # 构建审查起点提示
        start_hint = ""
        if key_functions:
            start_hint = f"\n**建议起点**：从 `{key_functions[0]}` 这个关键{code_unit_name}开始审查"
        elif related_files:
            start_hint = f"\n**建议起点**：从 `{related_files[0]}` 文件开始"
        
        # 构建审查任务
        task_text = f"""请开始审查功能模块：{feature.get('name')}

【功能信息】
- **描述**：{feature.get('description')}
- **优先级**：{feature.get('priority', 'medium')}"""
        
        if call_chain:
            task_text += f"\n- **调用链**：{call_chain}"
        if key_functions:
            task_text += f"\n- **关键函数**：{', '.join(key_functions[:8])}"
        if related_files:
            task_text += f"\n- **相关文件**：{', '.join(related_files[:8])}"
        
        task_text += f"""{start_hint}

【审查步骤】
1. **定位入口**：找到功能的入口代码单元（优先使用关键列表中的第一个）
2. **追踪调用链**：使用 get_call_graph 工具追踪关键代码单元关系
3. **深入审查每个关键代码单元**：
   - 使用 get_function_context 获取完整代码片段
   - 检查关键状态、时序、资源或接口行为是否一致
   - 检查返回值/错误码是否检查
   - 检查指针使用前是否判空
   - 检查数组访问是否越界
4. **输出问题单**：找到问题后，按照JSON格式输出

**重要**：
- 不要只看函数签名，要深入阅读完整实现
- 每个关键函数至少要完整阅读一遍
- 真实项目很少没有问题，请仔细寻找
- 如果前5轮没找到问题，说明审查不够深入

现在开始审查！"""
        
        return task_text
    
    def _call_ai_with_tools(self, conversation: List[Dict[str, Any]]) -> Dict[str, Any]:
        """调用AI（支持function calling）"""
        log_concurrent_info(
            f"[_call_ai_with_tools] ========== 进入AI调用方法 ==========",
            "smart_chain_executor"
        )
        
        # 记录完整的AI请求
        log_concurrent_info(
            f"[AI请求] ========== 开始 AI 请求 ==========",
            "smart_chain_executor"
        )
        log_concurrent_debug(
            f"[AI请求] 对话历史消息数: {len(conversation)}",
            "smart_chain_executor"
        )
        for idx, msg in enumerate(conversation):
            role = msg.get('role', 'unknown')
            content_preview = str(msg.get('content', ''))[:200] if msg.get('content') else '<无内容>'
            log_concurrent_debug(
                f"[AI请求] 消息{idx+1} - 角色:{role} - 内容预览: {content_preview}",
                "smart_chain_executor"
            )
        
        # 检测重复内容：仅在assistant文本非空时才判定循环，避免"空content+工具调用"被误判
        assistant_messages = [msg for msg in conversation if msg.get('role') == 'assistant']
        if len(assistant_messages) >= 5:
            last_five = assistant_messages[-5:]
            contents = [str(msg.get('content', '') or '').strip() for msg in last_five]
            # 忽略空content，空文本通常是模型仅返回tool_calls的正常阶段
            if all(contents) and len(set(contents)) == 1:
                repeated_content = contents[0]
                log_concurrent_warning(
                    "[AI调用] 检测到重复内容循环（连续5条相同且非空的assistant消息），强制结束审查",
                    "smart_chain_executor"
                )
                # 尝试从重复内容中提取问题
                problems = self._extract_problems_from_response(repeated_content)
                return {
                    "finished": True,
                    "content": repeated_content,
                    "problems": problems,
                    "feature_description": self._extract_result_from_response(repeated_content).get('feature_description', ''),
                    "stop_reason": "repeated_non_empty_assistant_content"
                }
        
        # 准备工具定义
        tools_definition = [
            {
                "type": "function",
                "function": {
                    "name": "list_directory",
                    "description": "列出项目目录的文件和子目录，用于了解项目结构",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "relative_path": {"type": "string", "description": "相对路径，默认为根目录"}
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_file_outline",
                    "description": "获取文件的结构大纲：函数列表、全局变量、宏定义等。**首选工具**，适合快速了解大型文件",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "relative_path": {"type": "string", "description": "文件相对路径"}
                        },
                        "required": ["relative_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file_range",
                    "description": "按行范围读取文件内容，用于查看特定代码区域",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "relative_path": {"type": "string", "description": "文件路径"},
                            "start_line": {"type": "integer", "description": "起始行号（从1开始）"},
                            "end_line": {"type": "integer", "description": "结束行号"}
                        },
                        "required": ["relative_path", "start_line", "end_line"]
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
                            "relative_path": {"type": "string", "description": "文件路径"},
                            "line_number": {"type": "integer", "description": "行号"}
                        },
                        "required": ["relative_path", "line_number"]
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
                            "function_name": {"type": "string", "description": "函数名（支持部分匹配）"}
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
                            "relative_path": {"type": "string", "description": "文件路径"},
                            "function_name": {"type": "string", "description": "要搜索的函数名"}
                        },
                        "required": ["relative_path", "function_name"]
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
                            "relative_path": {"type": "string", "description": "文件路径"},
                            "variable_name": {"type": "string", "description": "变量名"},
                            "line_number": {"type": "integer", "description": "可选：从哪一行开始查找"}
                        },
                        "required": ["relative_path", "variable_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_call_graph",
                    "description": "获取函数的调用关系图，支持指定深度和方向。**强大的拓扑关系工具**，可快速了解函数的上下游关系",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "function_name": {
                                "type": "string", 
                                "description": "要查询的函数名"
                            },
                            "file_path": {
                                "type": "string", 
                                "description": "可选：函数所在文件路径，用于消歧义"
                            },
                            "depth": {
                                "type": "integer",
                                "description": "调用深度（1-5），默认2。深度越大，查询范围越广",
                                "minimum": 1,
                                "maximum": 5
                            },
                            "direction": {
                                "type": "string",
                                "enum": ["callers", "callees", "both"],
                                "description": "查询方向：callers=谁调用了它，callees=它调用了谁，both=双向查询。默认callees"
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
                    "description": "在代码库中搜索包含指定关键字的代码行",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "keyword": {"type": "string", "description": "搜索关键字"},
                            "file_pattern": {"type": "string", "description": "文件模式，如 '*.c'，默认搜索所有代码文件"}
                        },
                        "required": ["keyword"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_dependency_function",
                    "description": "获取依赖函数的完整代码实现，用于理解函数的调用上下文",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "function_name": {"type": "string", "description": "要查询的函数名"}
                        },
                        "required": ["function_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_global_variable",
                    "description": "获取全局变量或宏定义的声明位置和代码",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "variable_name": {"type": "string", "description": "变量或宏的名称"}
                        },
                        "required": ["variable_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_function_calls",
                    "description": "搜索指定函数在项目中被调用的位置，用于理解函数的使用上下文",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "function_name": {"type": "string", "description": "函数名"}
                        },
                        "required": ["function_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_all_globals",
                    "description": "列出代码中可能使用的所有全局变量和宏定义",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]
        
        try:
            # 使用AIClient调用（支持function calling）
            import time
            start_time = time.time()
            log_concurrent_info(f"[AI请求] 准备发送请求到AI模型...", "smart_chain_executor")
            log_concurrent_info(f"[AI请求] 当前对话消息数: {len(conversation)}", "smart_chain_executor")
            
            response = self.ai_client.call_ai_with_tools(
                messages=conversation,
                tools=tools_definition,
                tool_choice="auto"
            )
            
            elapsed_time = time.time() - start_time
            log_concurrent_info(f"[AI响应] AI调用耗时: {elapsed_time:.2f}秒", "smart_chain_executor")
            
            # 记录完整的AI响应
            log_concurrent_info(
                f"[AI响应] ========== 收到 AI 响应 ==========",
                "smart_chain_executor"
            )
            log_concurrent_debug(
                f"[AI响应] 完整响应: {json.dumps(response, ensure_ascii=False, indent=2)}",
                "smart_chain_executor"
            )
            
            # 检查是否有错误（如429限流错误）
            if "error" in response:
                error_msg = response.get("error", "未知错误")
                log_concurrent_error(
                    f"[AI调用] AI服务返回错误: {error_msg}",
                    "smart_chain_executor"
                )
                
                # 判断是否是限流错误
                if "429" in error_msg or "Request limit exceeded" in error_msg or "Rate limit" in error_msg:
                    log_concurrent_warning(
                        "[AI调用] 触发限流错误，审查暂时结束，请稍后重试",
                        "smart_chain_executor"
                    )
                    # 尝试从最后一条成功的assistant消息中提取问题
                    last_assistant_content = ""
                    for msg in reversed(conversation):
                        if msg.get('role') == 'assistant' and msg.get('content'):
                            last_assistant_content = msg.get('content')
                            break
                    
                    result = self._extract_result_from_response(last_assistant_content) if last_assistant_content else {'problems': [], 'feature_description': ''}
                    return {
                        "finished": True,
                        "content": f"审查因API限流而终止，已提取 {len(result['problems'])} 个问题",
                        "problems": result['problems'],
                        "feature_description": result.get('feature_description', ''),
                        "stop_reason": "rate_limit"
                    }
                else:
                    # 其他错误，直接返回finished=True终止
                    return {
                        "finished": True,
                        "content": f"AI调用失败: {error_msg}",
                        "problems": [],
                        "stop_reason": "ai_error"
                    }
            
            # 解析AIClient返回的格式
            message = response.get("message", {})
            
            # 检查是否有工具调用
            tool_calls = message.get("tool_calls", [])
            if tool_calls:
                log_concurrent_info(
                    f"[AI响应] AI请求调用 {len(tool_calls)} 个工具",
                    "smart_chain_executor"
                )
                for idx, tc in enumerate(tool_calls):
                    log_concurrent_debug(
                        f"[AI响应] 工具{idx+1}: {tc['function']['name']} - 参数: {tc['function']['arguments']}",
                        "smart_chain_executor"
                    )
                
                return {
                    "finished": False,
                    "content": message.get("content") or "",
                    "tool_calls": [
                        {
                            "id": tc["id"],
                            "name": tc["function"]["name"],
                            "arguments": json.loads(tc["function"]["arguments"])
                        }
                        for tc in tool_calls
                    ]
                }
            
            # 检查是否完成
            content = message.get("content") or ""
            log_concurrent_info(
                f"[AI响应] AI返回内容（前500字符）: {content[:500]}",
                "smart_chain_executor"
            )
            
            # 尝试提取问题（不管是否有【最终问题单】标记）
            _result = self._extract_result_from_response(content)
            problems = _result['problems']
            _feature_description = _result.get('feature_description', '')
            
            # 判断是否应该结束审查
            should_finish = False
            finish_reason = ""
            
            # 1. 明确标记了【最终问题单】
            if '【最终问题单】' in content:
                should_finish = True
                finish_reason = "AI标记审查完成"
            # 2. 返回了有效的problems JSON结构（即使没有标记）
            elif problems is not None and isinstance(problems, list):
                should_finish = True
                finish_reason = "检测到有效的问题JSON结构"
            # 3. 内容包含JSON代码块且可以提取出problems
            elif '```json' in content and problems:
                should_finish = True
                finish_reason = "提取到问题列表"
            
            if should_finish:
                log_concurrent_info(
                    f"[AI响应] {finish_reason}，提取到 {len(problems) if problems else 0} 个问题",
                    "smart_chain_executor"
                )
                if problems:
                    log_concurrent_debug(
                        f"[AI响应] 问题详情: {json.dumps(problems, ensure_ascii=False, indent=2)}",
                        "smart_chain_executor"
                    )
                return {
                    "finished": True,
                    "content": content,
                    "problems": problems or [],
                    "feature_description": _feature_description,
                    "stop_reason": "ai_returned_final_content"
                }
            
            log_concurrent_info(
                f"[AI响应] AI未标记完成，继续对话",
                "smart_chain_executor"
            )
            return {
                "finished": False,
                "content": content,
                "tool_calls": []
            }
            
        except Exception as e:
            log_concurrent_error(f"[智能审查] AI调用失败", "smart_chain_executor", e)
            return {
                "finished": True,
                "content": f"AI调用失败: {str(e)}",
                "problems": [],
                "stop_reason": "exception"
            }
    
    def _execute_tools(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """执行工具调用"""
        results = []
        
        for tool_call in tool_calls:
            tool_name = tool_call['name']
            tool_args = tool_call['arguments']
            tool_id = tool_call['id']
            
            log_concurrent_debug(f"[工具调用] {tool_name}({tool_args})", "smart_chain_executor")
            
            try:
                if tool_name in self.tool_map:
                    result = self.tool_map[tool_name](**tool_args)
                    results.append({
                        "tool_call_id": tool_id,
                        "content": json.dumps(result, ensure_ascii=False)
                    })
                else:
                    results.append({
                        "tool_call_id": tool_id,
                        "content": json.dumps({"error": f"工具 {tool_name} 不存在"}, ensure_ascii=False)
                    })
            except Exception as e:
                log_concurrent_error(f"[工具调用] {tool_name} 执行失败", "smart_chain_executor", e)
                results.append({
                    "tool_call_id": tool_id,
                    "content": json.dumps({"error": str(e)}, ensure_ascii=False)
                })
        
        return results
    
    def _extract_result_from_response(self, content: str) -> Dict[str, Any]:
        """从响应中提取完整结果（problems + chain_info）"""
        try:
            # 查找JSON块
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                data = json.loads(json_str)
                chain_info = data.get('chain_info', {})
                return {
                    'problems': data.get('problems', []),
                    'feature_description': chain_info.get('chain_description', '') if chain_info else ''
                }
            
            # 尝试直接解析
            if '{' in content and '}' in content:
                start = content.find('{')
                end = content.rfind('}') + 1
                json_str = content[start:end]
                data = json.loads(json_str)
                chain_info = data.get('chain_info', {})
                return {
                    'problems': data.get('problems', []),
                    'feature_description': chain_info.get('chain_description', '') if chain_info else ''
                }
            
        except Exception as e:
            log_concurrent_warning(f"[问题提取] 解析失败: {e}", "smart_chain_executor")
        
        return {'problems': [], 'feature_description': ''}

    def _extract_problems_from_response(self, content: str) -> List[Dict[str, Any]]:
        """从响应中提取问题列表（兼容旧接口）"""
        return self._extract_result_from_response(content)['problems']


class CodeAnalysisTools:
    """代码分析工具集（复制自code_analysis_agent_v2.py）"""
    
    FPGA_EXTENSIONS = ['.v', '.sv', '.vhd', '.vhdl']
    C_EXTENSIONS = ['.c', '.cpp', '.h', '.hpp', '.cc', '.cxx']
    
    def __init__(self, project_root: str, language: str = 'c'):
        self.project_root = Path(project_root)
        self.language = language
        
        # 尝试加载预构建的调用图
        call_graph_file = self.project_root / "call_graph" / "call_graph.json"
        self.call_graph_query = None
        if call_graph_file.exists():
            try:
                self.call_graph_query = CallGraphQuery(call_graph_file)
                log_concurrent_debug(f"[工具初始化] 成功加载调用图: {call_graph_file}", "smart_chain_executor")
            except Exception as e:
                log_concurrent_error(f"[工具初始化] 加载调用图失败", "smart_chain_executor", e)
        else:
            log_concurrent_debug(f"[工具初始化] 调用图不存在，跳过加载: {call_graph_file}", "smart_chain_executor")
    
    def get_file_outline(self, relative_path: str) -> Dict[str, Any]:
        """获取文件大纲"""
        file_path = self.project_root / relative_path
        
        if not file_path.exists():
            return {"error": f"文件不存在: {relative_path}"}
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            if self.language == 'fpga' or file_path.suffix.lower() in self.FPGA_EXTENSIONS:
                infos = extract_fpga_files_from_code(content, str(file_path))
                modules = [info.get('function_name') for info in infos if info.get('function_name')]
                return {
                    "file": relative_path,
                    "functions": modules[:50],
                    "macros": [],
                    "includes": [],
                    "total_lines": content.count('\n') + 1,
                    "language": infos[0].get('language') if infos else 'verilog'
                }
            
            # 简单提取函数和宏
            functions = re.findall(r'^\s*(?:static\s+)?(?:void|int|char|float|double|long|short|unsigned)\s+(\w+)\s*\(', content, re.MULTILINE)
            macros = re.findall(r'^\s*#define\s+(\w+)', content, re.MULTILINE)
            includes = re.findall(r'^\s*#include\s+[<"](.+?)[>"]', content, re.MULTILINE)
            
            return {
                "file": relative_path,
                "functions": functions[:50],  # 限制数量
                "macros": macros[:30],
                "includes": includes,
                "total_lines": content.count('\n') + 1
            }
        except Exception as e:
            return {"error": str(e)}
    
    def read_file_range(self, relative_path: str, start_line: int, end_line: int) -> Dict[str, Any]:
        """读取文件指定行范围"""
        file_path = self.project_root / relative_path
        
        if not file_path.exists():
            return {"error": f"文件不存在: {relative_path}"}
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # 行号从1开始
            selected_lines = lines[start_line - 1:end_line]
            content = ''.join(selected_lines)
            
            return {
                "file": relative_path,
                "start_line": start_line,
                "end_line": end_line,
                "content": content
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_function_context(self, relative_path: str, line_number: int) -> Dict[str, Any]:
        """获取指定行所在函数的完整代码"""
        file_path = self.project_root / relative_path
        
        if not file_path.exists():
            return {"error": f"文件不存在: {relative_path}"}
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # 简单策略：往上找函数开始，往下找函数结束
            start = line_number - 1
            end = line_number
            
            # 往上找函数开始（简化）
            for i in range(line_number - 1, max(0, line_number - 100), -1):
                if '{' in lines[i] or re.match(r'^\s*(?:void|int|char|float)', lines[i]):
                    start = i
                    if '{' in lines[i]:
                        break
            
            # 往下找函数结束
            brace_count = 0
            for i in range(start, min(len(lines), start + 200)):
                brace_count += lines[i].count('{') - lines[i].count('}')
                if brace_count == 0 and i > start:
                    end = i + 1
                    break
            
            function_code = ''.join(lines[start:end])
            
            return {
                "file": relative_path,
                "line_number": line_number,
                "function_start": start + 1,
                "function_end": end,
                "code": function_code
            }
        except Exception as e:
            return {"error": str(e)}
    
    def search_function_by_name(self, function_name: str) -> Dict[str, Any]:
        """搜索函数定义"""
        results: List[Dict[str, Any]] = []
        
        extensions = self.FPGA_EXTENSIONS if self.language == 'fpga' else self.C_EXTENSIONS
        pattern_str = rf'\b(?:void|int|char|float|double|long|short|unsigned|module|entity)\s+{re.escape(function_name)}\b'
        pattern: Pattern[str] = re.compile(pattern_str)
        
        for ext in extensions:
            for file_path in self.project_root.rglob(f"*{ext}"):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # 搜索函数定义
                    if pattern.search(content):
                        rel_path = str(file_path.relative_to(self.project_root))
                        # 找到行号
                        lines = content.split('\n')
                        for i, line in enumerate(lines, 1):
                            if pattern.search(line):
                                results.append({
                                    "file": rel_path,
                                    "line": i,
                                    "snippet": line.strip()
                                })
                                break
                except Exception:
                    continue
                
                if len(results) >= 10:  # 限制结果数量
                    break
        
        return {
            "function_name": function_name,
            "found": len(results) > 0,
            "locations": results
        }
    
    def search_function_in_file(self, relative_path: str, function_name: str) -> Dict[str, Any]:
        """在文件中搜索函数"""
        file_path = self.project_root / relative_path
        
        if not file_path.exists():
            return {"error": f"文件不存在: {relative_path}"}
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            results: List[Dict[str, Any]] = []
            for i, line in enumerate(lines, 1):
                if function_name in line:
                    results.append({
                        "line": i,
                        "content": line.strip()
                    })
            
            return {
                "file": relative_path,
                "function_name": function_name,
                "found": len(results) > 0,
                "occurrences": results
            }
        except Exception as e:
            return {"error": str(e)}
    
    def list_directory(self, relative_path: str = ".") -> Dict[str, Any]:
        """列出目录内容"""
        dir_path = self.project_root / relative_path
        
        if not dir_path.exists() or not dir_path.is_dir():
            return {"error": f"目录不存在: {relative_path}"}
        
        try:
            items: List[Dict[str, Any]] = []
            for item in dir_path.iterdir():
                items.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "path": str(item.relative_to(self.project_root))
                })
            
            return {
                "directory": relative_path,
                "items": items[:50]  # 限制数量
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_variable_usage(self, relative_path: str, variable_name: str, line_number: Optional[int] = None) -> Dict[str, Any]:
        """追踪变量在文件中的所有使用位置"""
        file_path = self.project_root / relative_path
        
        if not file_path.exists():
            return {"error": f"文件不存在: {relative_path}"}
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            usages: List[Dict[str, Any]] = []
            var_pattern: Pattern[str] = re.compile(r'\b' + re.escape(variable_name) + r'\b')
            declaration_pattern: Pattern[str] = re.compile(
                r'\b(int|char|float|double|void|struct|long|short)\s+.*' + re.escape(variable_name)
            )
            
            for i, line in enumerate(lines, 1):
                if var_pattern.search(line):
                    # 判断使用类型
                    usage_type = "读取"
                    left_side = line.split('=', 1)[0] if '=' in line else ''
                    if left_side and variable_name in left_side:
                        usage_type = "赋值"
                    elif declaration_pattern.search(line):
                        usage_type = "声明"
                    
                    usages.append({
                        "line": i,
                        "type": usage_type,
                        "code": line.strip()
                    })
            
            return {
                "path": relative_path,
                "variable_name": variable_name,
                "usage_count": len(usages),
                "usages": usages[:50]  # 最多返回50个使用位置
            }
        except Exception as e:
            return {"error": f"追踪变量使用失败: {str(e)}"}
    
    def get_call_graph(
        self, 
        function_name: str, 
        file_path: Optional[str] = None,
        depth: int = 2,
        direction: str = "callees"
    ) -> Dict[str, Any]:
        """
        获取函数的调用关系图（支持深度查询）
        
        Args:
            function_name: 函数名
            file_path: 函数所在文件（可选，用于消歧义）
            depth: 查询深度（1-5），默认2
            direction: 查询方向（callers/callees/both），默认callees
        
        Returns:
            调用图数据
        """
        # 如果有预构建的调用图，使用快速查询
        if self.call_graph_query:
            try:
                result = self.call_graph_query.query(
                    function_name=function_name,
                    file_path=file_path,
                    depth=min(depth, 5),  # 限制最大深度
                    direction=direction
                )
                return result
            except Exception as e:
                log_concurrent_error(f"[调用图查询] 失败，回退到实时搜索", "smart_chain_executor", e)
        
        # Fallback: 实时搜索（只支持callers方向）
        try:
            callers = []
            
            if file_path:
                search_path = self.project_root / file_path
                if not search_path.exists():
                    return {"error": f"文件不存在: {file_path}"}
                files_to_search = [search_path]
            else:
                allowed_extensions = self.FPGA_EXTENSIONS if self.language == 'fpga' else self.C_EXTENSIONS
                files_to_search = []
                for ext in allowed_extensions:
                    files_to_search.extend(self.project_root.rglob(f"*{ext}"))
            
            func_pattern = re.compile(r'\b' + re.escape(function_name) + r'\s*\(')
            
            for file in files_to_search[:100]:
                try:
                    with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    
                    for i, line in enumerate(lines, 1):
                        if func_pattern.search(line):
                            callers.append({
                                "file": str(file.relative_to(self.project_root)),
                                "line": i,
                                "code": line.strip()
                            })
                except:
                    continue
            
            return {
                "function_name": function_name,
                "callers": callers[:20],
                "caller_count": len(callers),
                "warning": "使用实时搜索（未找到预构建调用图），仅支持callers方向"
            }
        except Exception as e:
            return {"error": f"获取调用关系失败: {str(e)}"}
    
    def search_code(self, keyword: str, file_pattern: Optional[str] = None) -> Dict[str, Any]:
        """在代码库中搜索关键字"""
        try:
            results = []
            
            # 确定搜索文件
            if file_pattern:
                files_to_search = list(self.project_root.rglob(file_pattern))
            else:
                allowed_extensions = self.FPGA_EXTENSIONS if self.language == 'fpga' else self.C_EXTENSIONS
                files_to_search = []
                for ext in allowed_extensions:
                    files_to_search.extend(self.project_root.rglob(f"*{ext}"))
            
            keyword_pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            
            for file in files_to_search[:100]:  # 限制搜索文件数
                try:
                    with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    
                    for i, line in enumerate(lines, 1):
                        if keyword_pattern.search(line):
                            results.append({
                                "file": str(file.relative_to(self.project_root)),
                                "line": i,
                                "code": line.strip()
                            })
                            
                            if len(results) >= 100:  # 限制结果数量
                                break
                except:
                    continue
                
                if len(results) >= 100:
                    break
            
            return {
                "keyword": keyword,
                "result_count": len(results),
                "results": results
            }
        except Exception as e:
            return {"error": f"搜索代码失败: {str(e)}"}
    
    def get_dependency_function(self, function_name: str) -> Dict[str, Any]:
        """获取依赖函数的代码"""
        try:
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
            if self.language != 'fpga' and function_name.lower() in standard_functions:
                return {
                    "function_name": function_name,
                    "found": False,
                    "is_standard_library": True,
                    "message": f"{function_name} 是C标准库函数，无需查看实现。请基于你对标准库的理解进行审查。"
                }
            
            # 在项目中搜索函数定义
            pattern = re.compile(r'^\s*(?:static\s+)?(?:void|int|char|float|double|long|short|unsigned|uint\w*|int\w*)\s+' + re.escape(function_name) + r'\s*\(', re.MULTILINE)
            
            allowed_extensions = self.FPGA_EXTENSIONS if self.language == 'fpga' else self.C_EXTENSIONS
            for ext in allowed_extensions:
                for file_path in self.project_root.rglob(f"*{ext}"):
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        if pattern.search(content):
                            # 提取函数代码
                            lines = content.split('\n')
                            function_start = -1
                            function_end = -1
                            brace_count = 0
                            
                            for i, line in enumerate(lines):
                                if function_name in line and '(' in line:
                                    function_start = i
                                    break
                            
                            if function_start >= 0:
                                for i in range(function_start, len(lines)):
                                    brace_count += lines[i].count('{') - lines[i].count('}')
                                    if brace_count == 0 and '{' in ''.join(lines[function_start:i+1]):
                                        function_end = i
                                        break
                                
                                if function_end == -1:
                                    function_end = min(function_start + 50, len(lines) - 1)
                                
                                source_code = '\n'.join(lines[function_start:function_end + 1])
                                
                                return {
                                    "function_name": function_name,
                                    "source_code": source_code,
                                    "file_path": str(file_path.relative_to(self.project_root)),
                                    "found": True
                                }
                    except:
                        continue
            
            return {
                "function_name": function_name,
                "found": False,
                "is_standard_library": False,
                "message": f"未找到函数 {function_name}，可能是外部库函数、系统调用或函数名不准确"
            }
            
        except Exception as e:
            return {
                "function_name": function_name,
                "found": False,
                "error": f"查找函数时出错: {str(e)}"
            }
    
    def get_global_variable(self, variable_name: str) -> Dict[str, Any]:
        """获取全局变量/宏定义"""
        try:
            allowed_extensions = self.FPGA_EXTENSIONS if self.language == 'fpga' else self.C_EXTENSIONS
            
            for ext in allowed_extensions:
                for file_path in self.project_root.rglob(f"*{ext}"):
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                        
                        for i, line in enumerate(lines, 1):
                            # 搜索全局变量声明
                            if re.search(r'\b(?:int|char|float|double|void|struct|long|short|unsigned)\s+' + re.escape(variable_name) + r'\b', line):
                                if not line.strip().startswith('//'):
                                    return {
                                        "variable_name": variable_name,
                                        "type": "variable",
                                        "file": str(file_path.relative_to(self.project_root)),
                                        "line": i,
                                        "code": line.strip(),
                                        "found": True
                                    }
                            
                            # 搜索宏定义
                            if re.search(r'^\s*#define\s+' + re.escape(variable_name) + r'\b', line):
                                return {
                                    "variable_name": variable_name,
                                    "type": "macro",
                                    "file": str(file_path.relative_to(self.project_root)),
                                    "line": i,
                                    "code": line.strip(),
                                    "found": True
                                }
                    except:
                        continue
            
            return {
                "variable_name": variable_name,
                "found": False,
                "message": f"未找到全局变量或宏 {variable_name}"
            }
        
        except Exception as e:
            return {
                "variable_name": variable_name,
                "found": False,
                "error": str(e)
            }
    
    def search_function_calls(self, function_name: str) -> Dict[str, Any]:
        """搜索函数调用位置"""
        try:
            call_pattern = re.compile(r'\b' + re.escape(function_name) + r'\s*\(')
            callers = []
            
            allowed_extensions = self.FPGA_EXTENSIONS if self.language == 'fpga' else self.C_EXTENSIONS
            for ext in allowed_extensions:
                for file_path in self.project_root.rglob(f"*{ext}"):
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
    
    def list_all_globals(self) -> Dict[str, Any]:
        """列出所有可用的全局变量和宏"""
        try:
            globals_list = []
            allowed_extensions = self.FPGA_EXTENSIONS if self.language == 'fpga' else self.C_EXTENSIONS
            
            for ext in allowed_extensions:
                for file_path in self.project_root.rglob(f"*{ext}"):
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        # 提取宏定义
                        macros = re.findall(r'^\s*#define\s+(\w+)', content, re.MULTILINE)
                        for macro in macros:
                            globals_list.append({
                                "name": macro,
                                "type": "macro",
                                "file": str(file_path.relative_to(self.project_root))
                            })
                        
                        # 提取全局变量（简化版）
                        global_vars = re.findall(r'^\s*(?:extern\s+)?(?:static\s+)?(?:const\s+)?(?:int|char|float|double|void|struct|long|short|unsigned)\s+(\w+)\s*[;=]', content, re.MULTILINE)
                        for var in global_vars:
                            globals_list.append({
                                "name": var,
                                "type": "variable",
                                "file": str(file_path.relative_to(self.project_root))
                            })
                        
                        if len(globals_list) >= 50:  # 限制数量
                            break
                    except:
                        continue
                
                if len(globals_list) >= 50:
                    break
            
            return {
                "globals": globals_list[:50],
                "count": len(globals_list),
                "total": len(globals_list)
            }
        except Exception as e:
            return {"error": str(e)}

