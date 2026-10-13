"""
代码审查规则提示词模板
"""
from pathlib import Path

def get_prompt_template():
    """获取代码审查规则提示词模板"""
    path = Path(__file__).parent / "codeReviewPrompt.md"
    with open(path, encoding="utf-8") as f:
        return f.read()

def get_fpga_prompt_template():
    """获取FPGA代码审查规则提示词模板"""
    path = Path(__file__).parent / "fpgaCodeReviewPrompt.md"
    with open(path, encoding="utf-8") as f:
        return f.read()
