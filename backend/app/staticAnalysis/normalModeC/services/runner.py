from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.staticAnalysis.normalModeC.database import FunctionRepository, ProblemRepository, TaskRepository
from .rules import load_selected_c_rules
from .scanner import scan_c_source_files
from .prompt import build_c_rule_prompt
from .executor import NormalModeCExecutor
from . import progress as progress_service


def _rule_bucket(rule: Dict[str, Any]) -> str:
    rule_type = str(rule.get("rule_type") or "").lower()
    if rule_type == "cwe":
        return "cwe"
    code = str(rule.get("rule_code") or "").upper()
    if code.startswith("CWE") or code.startswith("S_"):
        return "cwe"
    return "gjb"


class NormalModeCRunner:
    """普通模式 C/C++：仅审查勾选规则，每次 1 条规则 × 1 个文件。"""

    def __init__(self, db: Session):
        self.db = db
        self.function_repo = FunctionRepository(db)
        self.problem_repo = ProblemRepository(db)
        self.task_repo = TaskRepository(db)

    def run(self, task_id: int, file_id: int, extract_path: str, selected_rules: List[str]) -> Dict[str, Any]:
        rules = load_selected_c_rules(selected_rules)
        files = scan_c_source_files(extract_path)

        if not rules:
            self.task_repo.update_task_status(task_id, "failed", message="未找到勾选的有效规则")
            progress_service.mark_progress_failed(task_id, "未找到勾选的有效规则")
            self.db.commit()
            return {"total_rules": 0, "total_files": len(files), "total_problems": 0}

        if not files:
            self.task_repo.update_task_status(task_id, "failed", message="未找到可审查的 C/C++ 源文件")
            progress_service.mark_progress_failed(task_id, "未找到可审查的 C/C++ 源文件")
            self.db.commit()
            return {"total_rules": len(rules), "total_files": 0, "total_problems": 0}

        executor = NormalModeCExecutor(extract_path=extract_path, task_id=task_id)
        total_units = max(len(rules) * len(files), 1)
        processed_units = 0
        processed_files = 0
        total_problems = 0
        tool_calls_total = 0
        gjb_rules = sum(1 for r in rules if _rule_bucket(r) == "gjb")
        cwe_rules = sum(1 for r in rules if _rule_bucket(r) == "cwe")
        accurate_rules = sum(1 for r in rules if str(r.get("accuracy_type") or "").lower() == "accurate")
        uncertain_rules = len(rules) - accurate_rules
        gjb_processed_units = 0
        cwe_processed_units = 0

        progress_service.init_progress(
            task_id,
            total_files=len(files),
            total_rules=len(rules),
            accurate_rules=accurate_rules,
            uncertain_rules=uncertain_rules,
            gjb_rules=gjb_rules,
            cwe_rules=cwe_rules,
            total_units=total_units,
            domain="normalModeC",
        )

        self.task_repo.update_task_status(task_id, "processing", total_files=len(files), processed_files=0)

        for file_item in files:
            pseudo_function = self.function_repo.create_function({
                "file_id": file_id,
                "function_name": f"FILE::{file_item['file_path']}",
                "source_code": file_item["source_code"],
                "file_path": file_item["file_path"],
                "start_line": 1,
                "end_line": max(len(file_item["source_code"].splitlines()), 1),
            })
            for rule in rules:
                bucket = _rule_bucket(rule)
                progress_service.update_progress(
                    task_id,
                    "normalModeC",
                    current_rule_code=rule.get("rule_code", ""),
                    current_file_path=file_item["file_path"],
                    current_analyzing_issue=f"{rule.get('rule_code', '')} @ {file_item['file_path']}",
                )
                prompt = build_c_rule_prompt(rule, file_item)
                problems, tool_calls = executor.execute(rule, file_item, prompt)
                tool_calls_total += tool_calls

                for problem in problems:
                    self.problem_repo.create_problem({
                        "task_id": task_id,
                        "file_id": file_id,
                        "function_id": pseudo_function.id,
                        "file_name": file_item["file_path"],
                        "source_code": file_item["source_code"],
                        "violation_rules": problem.get("violation_rules", rule.get("rule_code", "")),
                        "issue_level": problem.get("issue_level", "一般问题"),
                        "issue_name": problem.get("issue_name", rule.get("rule_name", "")),
                        "issue_location": problem.get("issue_location", file_item["file_path"]),
                        "description_requirement": problem.get("description_requirement", rule.get("rule_description", "")),
                        "description_issue": problem.get("description_issue", ""),
                        "description_location": problem.get(
                            "description_location",
                            problem.get("issue_location", file_item["file_path"]),
                        ),
                        "description_impact": problem.get("description_impact", ""),
                    })
                    total_problems += 1

                processed_units += 1
                if bucket == "cwe":
                    cwe_processed_units += 1
                else:
                    gjb_processed_units += 1

                progress_pct = int((processed_units / total_units) * 100)
                self.task_repo.update_task_progress(task_id, progress_pct)
                progress_service.update_progress(
                    task_id,
                    "normalModeC",
                    processed_units=processed_units,
                    processed_files=processed_files,
                    total_problems=total_problems,
                    gjb_processed_units=gjb_processed_units,
                    cwe_processed_units=cwe_processed_units,
                    tool_calls_count=tool_calls_total,
                )
                self.db.commit()

            processed_files += 1
            self.task_repo.update_task_status(
                task_id,
                "processing",
                processed_files=processed_files,
                total_files=len(files),
            )
            progress_service.update_progress(task_id, "normalModeC", processed_files=processed_files)

        self.task_repo.update_task_status(
            task_id,
            "completed",
            progress=100,
            total_problems=total_problems,
            total_files=len(files),
            processed_files=len(files),
        )
        progress_service.mark_progress_completed(task_id, total_problems, domain="normalModeC")
        self.db.commit()
        return {"total_rules": len(rules), "total_files": len(files), "total_problems": total_problems}
