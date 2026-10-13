from typing import Any, Dict, List, Sequence

from app.staticAnalysis.filter.database.rules_database_factory import get_rules_database, get_cwe_rules_database


def _normalize_gjb_rule(rule: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "rule_code": rule.get("rule_code", ""),
        "rule_name": rule.get("rule_name") or rule.get("rule_description") or rule.get("rule_code", ""),
        "rule_description": rule.get("rule_description") or "",
        "rule_type": "gjb",
        "accuracy_type": rule.get("accuracy_type", "uncertain"),
        "problem_count": 0,
    }


def _normalize_cwe_rule(rule: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "rule_code": rule.get("rule_code", ""),
        "rule_name": rule.get("rule_name") or rule.get("description") or rule.get("rule_code", ""),
        "rule_description": rule.get("description") or "",
        "rule_type": "cwe",
        "accuracy_type": rule.get("accuracy_type", "uncertain"),
        "problem_count": 0,
    }


def load_all_c_rules() -> List[Dict[str, Any]]:
    gjb_rules = [_normalize_gjb_rule(rule) for rule in get_rules_database().get_all_rules()]
    cwe_rules = [_normalize_cwe_rule(rule) for rule in get_cwe_rules_database().get_all_rules()]
    return gjb_rules + cwe_rules


def load_selected_c_rules(selected_rules: Sequence[str]) -> List[Dict[str, Any]]:
    selected = {str(code).strip() for code in (selected_rules or []) if str(code).strip()}
    if not selected:
        return []

    results: List[Dict[str, Any]] = []
    for rule in load_all_c_rules():
        if rule.get("rule_code") in selected:
            results.append(rule)
    return results
