from typing import Any, Dict, List, Tuple

from app.staticAnalysis.normalModeC.services.ai_client import AIClient
from .agent import NormalModeCAgent


class NormalModeCExecutor:
    """确定类：直调 AI；不确定类：走 Agent 工具调用。"""

    def __init__(self, extract_path: str = None, task_id: int = None) -> None:
        self.ai_client = AIClient()
        self.extract_path = extract_path
        self.task_id = task_id
        self._agent: NormalModeCAgent = None
        self._tool_calls_total = 0

    def execute(
        self,
        rule: Dict[str, Any],
        file_item: Dict[str, Any],
        prompt: str,
    ) -> Tuple[List[Dict[str, Any]], int]:
        accuracy = str(rule.get("accuracy_type") or "uncertain").strip().lower()
        if accuracy == "accurate":
            return self._execute_direct(rule, prompt), 0
        return self._execute_with_agent(rule, file_item)

    def _execute_direct(self, rule: Dict[str, Any], prompt: str) -> List[Dict[str, Any]]:
        result, _ = self.ai_client.call_ai_stream(prompt)
        problems = result.get("problems", []) if isinstance(result, dict) else []
        return self._filter_rule_matched_problems(problems, rule)

    def _execute_with_agent(
        self,
        rule: Dict[str, Any],
        file_item: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], int]:
        agent = self._get_agent()
        if agent is None:
            from .prompt import build_c_rule_prompt
            return self._execute_direct(rule, build_c_rule_prompt(rule, file_item)), 0
        problems = agent.discover_violations_in_file(rule, file_item)
        tool_calls = int(getattr(agent, "tool_call_count", 0) or 0)
        self._tool_calls_total += tool_calls
        return self._filter_rule_matched_problems(problems, rule), tool_calls

    def _get_agent(self) -> NormalModeCAgent:
        if not self.extract_path:
            return None
        if self._agent is None:
            session_id = f"normalModeC_{self.task_id or 'unknown'}"
            self._agent = NormalModeCAgent(session_id=session_id, codebase_path=self.extract_path)
        return self._agent

    def _filter_rule_matched_problems(
        self,
        problems: List[Dict[str, Any]],
        rule: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        expected_rule = str(rule.get("rule_code", "")).strip()
        filtered: List[Dict[str, Any]] = []
        for item in problems or []:
            rule_value = item.get("violation_rules", "")
            if isinstance(rule_value, list):
                matched = expected_rule in [str(v).strip() for v in rule_value]
                rule_text = "; ".join(str(v) for v in rule_value)
            else:
                rule_text = str(rule_value or "").strip()
                matched = rule_text == expected_rule or expected_rule in rule_text
            if not matched:
                continue
            payload = dict(item)
            payload["violation_rules"] = expected_rule or rule_text
            filtered.append(payload)
        return filtered
