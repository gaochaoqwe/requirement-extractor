from typing import Dict, Any, List
from pathlib import Path


def build_business_prompt(
    software_type: str,
    kb: Dict[str, Any],  # 保留参数以兼容，但不使用
    project_root: str,
    file_rel_path: str,
    function_name: str,
    function_code: str,
    dir_context: List[str],
) -> str:
    """构建业务层审查提示词（简化版，不使用知识库）。"""
    # 截断以控制 token
    dir_preview = "\n".join(dir_context[:300])

    prompt = f"""
你是一名资深软件架构与代码审查专家，请从项目整体和功能角度审查代码。

【审查重点】
1. 业务逻辑正确性：函数实现是否符合其命名和预期功能
2. 功能边界清晰性：函数职责是否单一、边界是否清晰
3. 异常处理与鲁棒性：是否有充分的错误处理和边界条件检查
4. 代码流程一致性：控制流程是否合理、是否有遗漏的路径
5. 接口契合度：函数接口设计是否合理、参数使用是否正确
6. 潜在的业务bug：逻辑错误、边界条件处理不当等

【项目上下文】
仓库目录结构（节选）：
{dir_preview}

当前文件：{file_rel_path}
当前函数：{function_name}

【输出要求】
请基于业务和功能语义进行审查，避免纯代码风格类问题。若发现问题，请输出以下结构：
- problem_reason：问题原因（可前缀 [Business] 或 [Logic]）
- issue_level：严重程度（建议改进/一般问题/重要问题）
- issue_name：问题名称
- issue_location：问题位置（函数名/代码行）
- description_requirement：功能预期或正确做法
- description_issue：发现的具体问题
- description_location：问题代码片段或证据
- description_impact：对业务/功能的影响

【函数源码】
```code
{function_code}
```

请仔细分析代码，输出JSON格式的problems列表。
"""
    return prompt 