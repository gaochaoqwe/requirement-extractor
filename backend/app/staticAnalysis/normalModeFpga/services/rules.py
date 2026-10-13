from typing import Any, Dict, List, Sequence

from app.staticAnalysis.filterFpga.database.postgresql_database import get_db_session as get_fpga_db_session
from app.staticAnalysis.filterFpga.database.postgresql_models import FPGARule
from app.staticAnalysis.filterFpga.database.postgresql_rules_database import get_fpga_rules_database


def _normalize_fpga_rule(rule: Any) -> Dict[str, Any]:
    return {
        "rule_code": getattr(rule, "rule_code", "") or (rule.get("rule_code") if isinstance(rule, dict) else ""),
        "rule_name": (
            getattr(rule, "rule_content", None)
            or getattr(rule, "rule_name", None)
            or (rule.get("rule_name") if isinstance(rule, dict) else None)
            or getattr(rule, "rule_code", "")
            or (rule.get("rule_code") if isinstance(rule, dict) else "")
        ),
        "rule_description": (
            getattr(rule, "rule_content", None)
            or (rule.get("rule_description") if isinstance(rule, dict) else None)
            or (rule.get("rule_content") if isinstance(rule, dict) else None)
            or ""
        ),
        "rule_type": "fpga",
        "accuracy_type": getattr(rule, "accuracy_type", None)
        or (rule.get("accuracy_type") if isinstance(rule, dict) else None)
        or "uncertain",
        "problem_count": 0,
        "language": getattr(rule, "language", None) or (rule.get("language") if isinstance(rule, dict) else None),
        "is_selected": getattr(rule, "is_selected", None) or (rule.get("is_selected") if isinstance(rule, dict) else None) or True,
    }


def load_all_fpga_rules() -> List[Dict[str, Any]]:
    session = get_fpga_db_session()
    try:
        rows = session.query(FPGARule).order_by(FPGARule.language, FPGARule.rule_type, FPGARule.sequence).all()
        return [_normalize_fpga_rule(rule) for rule in rows]
    finally:
        session.close()


def load_selected_fpga_rules(selected_rules: Sequence[str]) -> List[Dict[str, Any]]:
    selected = {str(code).strip() for code in (selected_rules or []) if str(code).strip()}
    if not selected:
        return []

    db = get_fpga_rules_database()
    results: List[Dict[str, Any]] = []
    for rule_code in selected:
        rule = db.get_rule_by_code(rule_code)
        if not rule:
            continue
        results.append(_normalize_fpga_rule(rule))
    return results
