"""普通模式 FPGA 进度服务（独立实现）。"""
from __future__ import annotations

from typing import Any, Dict

from sqlalchemy.orm import Session

from app.staticAnalysis.normalModeFpga.database import (
    ProblemRepository,
    TaskRepository,
)
from app.staticAnalysis.normalModeFpga.utils.context import (
    get_normal_mode_fpga_context,
    set_normal_mode_fpga_context,
)


def init_progress(
    task_id: int,
    *,
    total_files: int,
    total_rules: int,
    accurate_rules: int,
    uncertain_rules: int,
    total_units: int,
) -> None:
    ctx = get_normal_mode_fpga_context(task_id)
    set_normal_mode_fpga_context(task_id, {
        **ctx,
        "domain": "normalModeFpga",
        "progress_status": "processing",
        "total_files": total_files,
        "processed_files": 0,
        "total_rules": total_rules,
        "accurate_rules": accurate_rules,
        "uncertain_rules": uncertain_rules,
        "total_units": total_units,
        "processed_units": 0,
        "total_problems": 0,
        "current_rule_code": "",
        "current_file_path": "",
        "current_analyzing_issue": "",
        "tool_calls_count": 0,
    })


def update_progress(task_id: int, **fields: Any) -> None:
    ctx = get_normal_mode_fpga_context(task_id)
    set_normal_mode_fpga_context(task_id, {**ctx, **fields})


def mark_progress_completed(task_id: int, total_problems: int) -> None:
    update_progress(
        task_id,
        progress_status="completed",
        total_problems=total_problems,
        current_analyzing_issue="",
        current_rule_code="",
        current_file_path="",
    )


def mark_progress_failed(task_id: int, message: str = "") -> None:
    update_progress(task_id, progress_status="failed", error_message=message)


def _count_problems_by_type(db: Session, task_id: int) -> Dict[str, int]:
    problems = ProblemRepository(db).get_problems_by_task(task_id)
    fpga_count = 0
    for item in problems or []:
        rule_code = str(item.get("violation_rules") or "").strip().upper()
        if rule_code.startswith("FPGA") or "VHDL" in rule_code or "VERILOG" in rule_code or rule_code.startswith("R-") or rule_code.startswith("A-") or rule_code.startswith("5."):
            fpga_count += 1
    return {
        "total": len(problems or []),
        "fpga": fpga_count or len(problems or []),
    }


def build_progress_payload(db: Session, task_id: int, *, mode: str = "fpga") -> Dict[str, Any]:
    task = TaskRepository(db).get_task(task_id)
    if not task:
        raise ValueError("Task not found")

    ctx = get_normal_mode_fpga_context(task_id)
    counts = _count_problems_by_type(db, task_id)

    total_units = int(ctx.get("total_units") or 0)
    processed_units = int(ctx.get("processed_units") or 0)
    progress_pct = int(task.progress or 0)
    if total_units > 0:
        progress_pct = max(progress_pct, int(processed_units * 100 / total_units))

    status = task.status or ctx.get("progress_status") or "pending"
    
    return {
        "success": True,
        "progress": {
            "task_id": task_id,
            "status": status,
            "progress": min(progress_pct, 100),
            "total_files": int(task.total_files or ctx.get("total_files") or 0),
            "processed_files": int(task.processed_files or ctx.get("processed_files") or 0),
            "total_rules": int(ctx.get("total_rules") or 0),
            "accurate_rules": int(ctx.get("accurate_rules") or 0),
            "uncertain_rules": int(ctx.get("uncertain_rules") or 0),
            "total_units": total_units,
            "processed_units": processed_units,
            "total_problems": int(task.total_problems or counts["total"]),
            "fpga_problems": counts["fpga"],
            "current_rule_code": ctx.get("current_rule_code") or "",
            "current_file_path": ctx.get("current_file_path") or "",
            "current_analyzing_issue": ctx.get("current_analyzing_issue") or "",
            "tool_calls_count": int(ctx.get("tool_calls_count") or 0),
            "message": ctx.get("error_message") or "",
            "domain": "normalModeFpga",
        },
        "domain": "normalModeFpga",
    }


__all__ = [
    "init_progress",
    "update_progress",
    "mark_progress_completed",
    "mark_progress_failed",
    "build_progress_payload",
]
