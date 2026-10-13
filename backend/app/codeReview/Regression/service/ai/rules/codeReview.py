"""\n通用 C/C++ 代码审查规则加载工具\n"""
from pathlib import Path

def get_rules() -> str:
    """读取 Markdown 规则文件内容"""
    path = Path(__file__).parent / "codeReview.md"
    if not path.exists():
        return ""
    with open(path, encoding="utf-8") as f:
        return f.read()
