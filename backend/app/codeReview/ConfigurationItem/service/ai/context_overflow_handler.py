"""
上下文超出处理模块

当AI调用超出上下文长度限制时，自动降级到简化模式进行审查。
"""

from typing import Dict, Any, Optional
from ...utils.concurrent_logger import log_concurrent_info, log_concurrent_warning, log_concurrent_error


def is_context_overflow_error(error: Exception) -> bool:
    """
    判断是否是上下文超出错误
    
    Args:
        error: 异常对象
        
    Returns:
        bool: 是否是上下文超出错误
    """
    error_str = str(error).lower()
    error_type = type(error).__name__.lower()
    
    # OpenAI 相关的上下文超出错误特征
    context_overflow_keywords = [
        'context_length_exceeded',
        'maximum context length',
        'context window',
        'too many tokens',
        'exceed',
        'token limit',
        'context size',
        'input is too long'
    ]
    
    # 检查错误消息和类型
    return (
        'badrequesterror' in error_type or
        'invalidrequesterror' in error_type or
        any(keyword in error_str for keyword in context_overflow_keywords)
    )


def build_simplified_prompt(
    function_code: str,
    function_name: str,
    file_path: str,
    forbidden_rules: str
) -> str:
    """
    构建简化版的提示词（不包含任何依赖信息和工具调用）
    
    用于在上下文超出时的降级处理
    
    注意：除了不能调用工具外，审查规则和输出格式要求与Agent模式完全一致
    
    Args:
        function_code: 函数代码
        function_name: 函数名
        file_path: 文件路径
        forbidden_rules: 禁止报告的规则
        
    Returns:
        str: 简化的提示词
    """
    prompt = f"""你是一名专业的C/C++代码审查专家。你的任务是审查函数代码，找出潜在问题。

由于上下文限制，本次审查采用简化模式：
- 你只能看到函数本身的代码
- 不能查看依赖函数或全局变量的定义
- 请基于函数代码本身进行审查

{forbidden_rules}

**待审查函数**：
文件路径：{file_path}
函数名：{function_name}

```c
{function_code}
```

**输出格式要求（非常重要）**：
必须输出标准JSON格式的审查结果。

## 问题分析字段含义：
- `file_name`：当前报错的代码函数所在的代码文件名称
- `source_code`：当前报错的代码函数的全部代码
- `problem_reason`：问题的根本原因（例如：未检查返回值、缓冲区溢出风险、资源泄漏等，用简洁的语言描述问题的本质原因）
- `issue_level`：问题等级（必须是以下三个值之一：建议改进、一般问题、重要问题）
- `issue_name`：问题名称
- `issue_location`：问题来源（代码文件名称+函数名称）
- `description_requirement`：需求描述
- `description_issue`：问题描述
- `description_location`：问题定位，**必须严格按照以下格式**：`xx文件的xx函数的xx行：问题代码语句`
  - 示例：`example.c文件的foo函数的3行：gets(buf)`
  - **重要**：问题代码语句是最关键的定位信息，前端将使用代码语句进行精确匹配
  - 问题代码语句应该是导致问题的**具体代码片段**，去掉多余空格，保持原始语法
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
      "description_location": "example.c文件的foo函数的3行：gets(buf)",
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
10. **description_location字段格式固定为：xx文件的xx函数的xx行：问题代码语句**

**关键要求：**
- **function_info字段必须始终提供**，包含function_name, function_description, commented_code三个字段
- **即使未发现问题，也必须返回完整的function_info**
- **commented_code中的换行符必须用\\n转义**，例如："commented_code": "int main() {{\\n    // 注释\\n    return 0;\\n}}"
- **commented_code必须包含详细注释**：为每一行重要代码添加注释，说明其具体作用和业务含义

请严格按照以上格式输出审查结果。
"""
    return prompt


def review_with_simplified_mode(
    function_code: str,
    function_name: str,
    file_path: str,
    forbidden_rules: str,
    ai_client
) -> Dict[str, Any]:
    """
    使用简化模式审查函数（不调用工具，不包含依赖）
    
    Args:
        function_code: 函数代码
        function_name: 函数名
        file_path: 文件路径
        forbidden_rules: 禁止报告的规则
        ai_client: AI客户端
        
    Returns:
        Dict[str, Any]: 审查结果
    """
    log_concurrent_warning(
        f"[降级模式] 使用简化模式审查函数 {function_name}（无工具调用，无依赖信息）",
        "context_overflow_handler"
    )
    
    try:
        # 构建简化的提示词
        simplified_prompt = build_simplified_prompt(
            function_code=function_code,
            function_name=function_name,
            file_path=file_path,
            forbidden_rules=forbidden_rules
        )
        
        log_concurrent_info(
            f"[降级模式] 简化提示词长度: {len(simplified_prompt)} 字符",
            "context_overflow_handler"
        )
        
        # 调用AI（使用传统的非工具模式）
        result, raw_content = ai_client.call_ai_stream(simplified_prompt)
        
        log_concurrent_info(
            f"[降级模式] 审查完成，发现 {len(result.get('problems', []))} 个问题",
            "context_overflow_handler"
        )
        
        return result
        
    except Exception as e:
        log_concurrent_error(
            f"[降级模式] 简化模式审查也失败了",
            "context_overflow_handler",
            e
        )
        # 返回空结果，避免完全失败
        return {
            "problems": [],
            "function_info": {
                "function_description": f"函数 {function_name}（审查失败：{str(e)[:100]}）"
            },
            "error": f"简化模式审查失败: {str(e)}"
        }


def estimate_context_tokens(
    function_code: str,
    conversation_history: list = None,
    tools_count: int = 0
) -> Dict[str, int]:
    """
    估算当前上下文的token数量
    
    Args:
        function_code: 函数代码
        conversation_history: 对话历史
        tools_count: 工具数量
        
    Returns:
        Dict[str, int]: token估算信息
    """
    # 粗略估算：1个token约等于4个字符（英文），2个字符（中文）
    # 保守估计用3个字符
    CHARS_PER_TOKEN = 3
    
    # 估算函数代码token
    function_tokens = len(function_code) // CHARS_PER_TOKEN
    
    # 估算对话历史token
    conversation_tokens = 0
    if conversation_history:
        for msg in conversation_history:
            content = msg.get('content', '')
            if isinstance(content, str):
                conversation_tokens += len(content) // CHARS_PER_TOKEN
    
    # 估算工具定义token（每个工具约200-300 tokens）
    tools_tokens = tools_count * 250
    
    total_tokens = function_tokens + conversation_tokens + tools_tokens
    
    return {
        "function_tokens": function_tokens,
        "conversation_tokens": conversation_tokens,
        "tools_tokens": tools_tokens,
        "total_tokens": total_tokens,
        "estimated_chars": total_tokens * CHARS_PER_TOKEN
    }


def get_context_limit(model_name: str) -> int:
    """
    获取模型的上下文限制
    
    Args:
        model_name: 模型名称
        
    Returns:
        int: 上下文token限制
    """
    # 常见模型的上下文限制
    context_limits = {
        # OpenAI models
        'gpt-4': 8192,
        'gpt-4-32k': 32768,
        'gpt-4-turbo': 128000,
        'gpt-3.5-turbo': 4096,
        'gpt-3.5-turbo-16k': 16384,
        
        # Qwen models
        'qwen2.5-coder:7b': 32768,
        'qwen2.5-coder:14b': 32768,
        'qwen2.5-coder:32b': 32768,
        'qwen-coder-plus': 131072,
        
        # DeepSeek models
        'deepseek-coder': 16384,
        'deepseek-chat': 32768,
        
        # Claude models
        'claude-3': 200000,
        'claude-2': 100000,
    }
    
    # 匹配模型名称（支持部分匹配）
    model_lower = model_name.lower()
    for key, limit in context_limits.items():
        if key in model_lower:
            return limit
    
    # 默认保守估计
    return 4096


def should_use_simplified_mode(
    estimated_tokens: int,
    model_name: str,
    safety_margin: float = 0.8
) -> bool:
    """
    判断是否应该预先使用简化模式
    
    Args:
        estimated_tokens: 估算的token数
        model_name: 模型名称
        safety_margin: 安全边际（0-1），默认0.8表示使用80%上限
        
    Returns:
        bool: 是否应该使用简化模式
    """
    context_limit = get_context_limit(model_name)
    threshold = int(context_limit * safety_margin)
    
    return estimated_tokens > threshold
