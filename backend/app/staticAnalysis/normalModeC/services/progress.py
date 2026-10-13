"""普通模式任务进度（写入各 domain 的 context + 读取 DB 任务字段）。"""
from __future__ import annotations

from typing import Any, Dict

from sqlalchemy.orm import Session

from app.staticAnalysis.normalModeC.database import ProblemRepository, TaskRepository
from app.staticAnalysis.normalModeC.utils.context import (
    get_normal_mode_c_context,
    set_normal_mode_c_context,
)
from app.staticAnalysis.normalModeFpga.utils.context import (
    get_normal_mode_fpga_context,
    set_normal_mode_fpga_context,
)


def _get_context(task_id: int, domain: str = "normalModeC") -> Dict[str, Any]:
    if domain == "normalModeFpga":
        return get_normal_mode_fpga_context(task_id)
    return get_normal_mode_c_context(task_id)


def _set_context(task_id: int, payload: Dict[str, Any], domain: str = "normalModeC") -> None:
    if domain == "normalModeFpga":
        set_normal_mode_fpga_context(task_id, payload)
    else:
        set_normal_mode_c_context(task_id, payload)


def init_progress(
    task_id: int,
    *,
    total_files: int,
    total_rules: int,
    accurate_rules: int,
    uncertain_rules: int,
    gjb_rules: int = 0,
    cwe_rules: int = 0,
    total_units: int,
    domain: str = "normalModeC",
) -> None:
    ctx = _get_context(task_id, domain)
    _set_context(task_id, {
        **ctx,
        "domain": domain,
        "progress_status": "processing",
        "total_files": total_files,
        "processed_files": 0,
        "total_rules": total_rules,
        "accurate_rules": accurate_rules,
        "uncertain_rules": uncertain_rules,
        "gjb_rules": gjb_rules,
        "cwe_rules": cwe_rules,
        "total_units": total_units,
        "processed_units": 0,
        "total_problems": 0,
        "gjb_problems": 0,
        "cwe_problems": 0,
        "gjb_processed_units": 0,
        "cwe_processed_units": 0,
        "gjb_total_units": gjb_rules * total_files if gjb_rules else 0,
        "cwe_total_units": cwe_rules * total_files if cwe_rules else 0,
        "current_rule_code": "",
        "current_file_path": "",
        "current_analyzing_issue": "",
        "tool_calls_count": 0,
    }, domain)


def update_progress(task_id: int, domain: str = "normalModeC", **fields: Any) -> None:
    ctx = _get_context(task_id, domain)
    _set_context(task_id, {**ctx, **fields}, domain)


def mark_progress_completed(task_id: int, total_problems: int, domain: str = "normalModeC") -> None:
    update_progress(
        task_id,
        domain,
        progress_status="completed",
        total_problems=total_problems,
        current_analyzing_issue="",
        current_rule_code="",
        current_file_path="",
    )


def mark_progress_failed(task_id: int, message: str = "", domain: str = "normalModeC") -> None:
    update_progress(task_id, domain, progress_status="failed", error_message=message)


def _count_problems_by_type(db: Session, task_id: int) -> Dict[str, int]:
    problems = ProblemRepository(db).get_problems_by_task(task_id)
    gjb_count = 0
    cwe_count = 0
    fpga_count = 0
    for item in problems or []:
        rule_code = str(item.get("violation_rules") or "").strip().upper()
        if rule_code.startswith("CWE") or rule_code.startswith("S_"):
            cwe_count += 1
        elif rule_code.startswith("FPGA") or "VHDL" in rule_code or "VERILOG" in rule_code:
            fpga_count += 1
        else:
            gjb_count += 1
    return {
        "total": len(problems or []),
        "gjb": gjb_count,
        "cwe": cwe_count,
        "fpga": fpga_count,
    }


def build_progress_payload(db: Session, task_id: int, *, mode: str = "c") -> Dict[str, Any]:
    task = TaskRepository(db).get_task(task_id)
    if not task:
        raise ValueError("Task not found")

    domain = "normalModeFpga" if mode == "fpga" else "normalModeC"
    ctx = _get_context(task_id, domain)
    counts = _count_problems_by_type(db, task_id)

    total_units = int(ctx.get("total_units") or 0)
    processed_units = int(ctx.get("processed_units") or 0)
    progress_pct = int(task.progress or 0)
    if total_units > 0:
        progress_pct = max(progress_pct, int(processed_units * 100 / total_units))

    status = task.status or ctx.get("progress_status") or "pending"
    base = {
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
        "current_rule_code": ctx.get("current_rule_code") or "",
        "current_file_path": ctx.get("current_file_path") or "",
        "current_analyzing_issue": ctx.get("current_analyzing_issue") or "",
        "tool_calls_count": int(ctx.get("tool_calls_count") or 0),
        "message": ctx.get("error_message") or "",
    }

    if mode == "fpga":
        return {
            "success": True,
            "progress": {
                **base,
                "fpga_problems": counts["fpga"] or counts["total"],
                "domain": domain,
            },
            "domain": domain,
        }

    gjb_total_units = int(ctx.get("gjb_total_units") or 0)
    cwe_total_units = int(ctx.get("cwe_total_units") or 0)
    gjb_processed = int(ctx.get("gjb_processed_units") or 0)
    cwe_processed = int(ctx.get("cwe_processed_units") or 0)

    def _section(total_u: int, processed_u: int, problems: int) -> Dict[str, Any]:
        pct = int(processed_u * 100 / total_u) if total_u > 0 else (100 if status == "completed" else 0)
        return {
            "status": status,
            "progress": min(pct, 100),
            "total_issues": problems,
            "total_problems": problems,
            "processed_units": processed_u,
            "total_units": total_u,
            "ai_processing_total": total_u,
            "ai_processed_issues": processed_u,
            "current_analyzing_issue": ctx.get("current_analyzing_issue") or "",
            "tool_calls_count": int(ctx.get("tool_calls_count") or 0),
            "accurate_ready": status in ("completed", "processing"),
        }

    return {
        "success": True,
        "progress": base,
        "gjb": _section(gjb_total_units, gjb_processed, counts["gjb"]),
        "cwe": _section(cwe_total_units, cwe_processed, counts["cwe"]),
        "domain": domain,
    }
