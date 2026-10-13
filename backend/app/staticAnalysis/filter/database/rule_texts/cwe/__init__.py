import json
from pathlib import Path

# 仅使用 JSON 作为规则文本来源；当缺失时在本模块内提供兜底生成逻辑，避免循环导入/不存在的模块导入

_BASE_DIR = Path(__file__).resolve().parent

_PROBLEM_NAME_MAP = json.loads((_BASE_DIR / "problem_name.json").read_text(encoding="utf-8"))
_REQUIREMENT_MAP = json.loads((_BASE_DIR / "requirement_description.json").read_text(encoding="utf-8"))
_IMPACT_MAP = json.loads((_BASE_DIR / "impact_analysis.json").read_text(encoding="utf-8"))
_SUGGEST_MAP = json.loads((_BASE_DIR / "improvement_suggestion.json").read_text(encoding="utf-8"))


def _fallback_problem_name(rule: dict) -> str:
    code = str(rule.get("rule_code", "")).strip()
    title = rule.get("rule_name") or rule.get("title") or "CWE 规则"
    return f"{title} ({code})"


def _fallback_requirement(rule: dict) -> str:
    code = str(rule.get("rule_code", "")).strip()
    return f"需要遵循 {code} 的静态分析规则，确保相关缺陷被检测与修复。"


def _fallback_impact(rule: dict) -> str:
    return "若不遵循该规则，可能导致潜在缺陷未被发现，影响系统可靠性与可维护性。"


def _fallback_suggestion(rule: dict) -> str:
    return "请根据规则要求修正代码，必要时参考对应 CWE 文档与最佳实践。"


def build_rule_texts(rule: dict) -> dict:
    code = str(rule.get("rule_code", "")).strip()
    return {
        "problem_name": _PROBLEM_NAME_MAP.get(code) or _fallback_problem_name(rule),
        "requirement_description": _REQUIREMENT_MAP.get(code) or _fallback_requirement(rule),
        "impact_analysis": _IMPACT_MAP.get(code) or _fallback_impact(rule),
        "improvement_suggestion": _SUGGEST_MAP.get(code) or _fallback_suggestion(rule),
    }
