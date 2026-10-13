def clean_text(value, fallback="") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def build_default_requirement(rule_code: str, rule_name: str) -> str:
    code = rule_code or "该规则"
    name = clean_text(rule_name)
    if name:
        return f"遵循{code}（{name}）的规范要求，确保实现满足标准约束。"
    return f"遵循{code}的规范要求，确保实现满足标准约束。"


def build_default_impact(rule_code: str, category: str) -> str:
    code = rule_code or "该规则"
    category_text = clean_text(category)
    if category_text:
        return f"违反{code}可能导致{category_text}相关缺陷，降低系统可靠性与可维护性。"
    return f"违反{code}可能导致功能实现错误或潜在风险，降低系统可靠性。"


def build_default_improvement(rule_code: str, rule_name: str) -> str:
    code = rule_code or "该规则"
    name = clean_text(rule_name)
    if name:
        return f"按照{code}（{name}）的要求梳理设计与实现流程，补充必要的检测与审查步骤。"
    return f"按照{code}的要求梳理设计与实现流程，补充必要的检测与审查步骤。"
