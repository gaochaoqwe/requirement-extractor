import json
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent

_PROBLEM_NAME_MAP = json.loads((_BASE_DIR / "problem_name.json").read_text(encoding="utf-8"))
_REQUIREMENT_MAP = json.loads((_BASE_DIR / "requirement_description.json").read_text(encoding="utf-8"))
_IMPACT_MAP = json.loads((_BASE_DIR / "impact_analysis.json").read_text(encoding="utf-8"))
_SUGGEST_MAP = json.loads((_BASE_DIR / "improvement_suggestion.json").read_text(encoding="utf-8"))


def build_rule_texts(rule: dict) -> dict:
    """构建规则文本,从JSON映射中获取"""
    code = str(rule.get("rule_code", "")).strip()
    return {
        "problem_name": _PROBLEM_NAME_MAP.get(code, f"规则 {code}"),
        "requirement_description": _REQUIREMENT_MAP.get(code, ""),
        "impact_analysis": _IMPACT_MAP.get(code, ""),
        "improvement_suggestion": _SUGGEST_MAP.get(code, ""),
    }
