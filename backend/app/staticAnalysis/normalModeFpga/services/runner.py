from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.staticAnalysis.normalModeFpga.database import FunctionRepository, ProblemRepository, TaskRepository
from .rules import load_selected_fpga_rules
from .scanner import scan_fpga_source_files
from .prompt import build_fpga_rule_prompt
from .executor import NormalModeFpgaExecutor


class NormalModeFpgaRunner:
    """普通模式 FPGA：仅审查勾选规则，每次 1 条规则 × 1 个文件。"""

    def __init__(self, db: Session):
        self.db = db
        self.function_repo = FunctionRepository(db)
        self.problem_repo = ProblemRepository(db)
        self.task_repo = TaskRepository(db)

    def run(self, task_id: int, file_id: int, extract_path: str, selected_rules: List[str]) -> Dict[str, Any]:
        rules = load_selected_fpga_rules(selected_rules)
        files = scan_fpga_source_files(extract_path)

        if not rules:
            self.task_repo.update_task_status(task_id, "failed", message="未找到勾选的有效规则")
            self.db.commit()
            return {"total_rules": 0, "total_files": len(files), "total_problems": 0}

        if not files:
            self.task_repo.update_task_status(task_id, "failed", message="未找到可审查的 FPGA 源文件")
            self.db.commit()
            return {"total_rules": len(rules), "total_files": 0, "total_problems": 0}

        executor = NormalModeFpgaExecutor(extract_path=extract_path, task_id=task_id)
        total_units = max(len(rules) * len(files), 1)
        processed_units = 0
        processed_files = 0
        total_problems = 0

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
            file_lang = (file_item.get("language") or "").lower()  # "verilog" or "vhdl"
            for rule in rules:
                rule_lang = (rule.get("language") or "").lower()
                # 跳过语言不匹配的规则（Verilog文件只跑Verilog规则，VHDL文件只跑VHDL规则）
                if rule_lang and file_lang and rule_lang != file_lang:
                    processed_units += 1
                    continue
                prompt = build_fpga_rule_prompt(rule, file_item)
                problems = executor.execute(rule, file_item, prompt)
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
                self.db.commit()
                processed_units += 1
                progress = int((processed_units / total_units) * 100)
                self.task_repo.update_task_progress(task_id, progress)

            processed_files += 1
            self.task_repo.update_task_status(
                task_id,
                "processing",
                processed_files=processed_files,
                total_files=len(files),
            )

        self.task_repo.update_task_status(
            task_id,
            "completed",
            progress=100,
            total_problems=total_problems,
            total_files=len(files),
            processed_files=len(files),
        )
        self.db.commit()
        return {"total_rules": len(rules), "total_files": len(files), "total_problems": total_problems}
