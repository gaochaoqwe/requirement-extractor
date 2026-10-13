import os
from typing import Dict, Any, Optional, List

from sqlalchemy.orm import Session

from ...config_database import get_db
from ...db.models.file import AnalysisFile
from ...db.models.function import AnalysisFunction
from ...db.models.function_pair import RegressionFunctionPair
from ...db.repository.function_repo import FunctionRepository
from ...db.repository.problem_repo import ProblemRepository
from ...db.repository.task_repo import TaskRepository
from ...service.ai.function_review_agent import FunctionReviewAgent
from ...service.ai.rules.codeReview import get_rules
from ...service.ai.task_resume_runner import scan_global_variables
from ...utils.concurrent_logger import log_concurrent_info


def _get_new_extract_path(db: Session, task_id: int) -> str:
    files = db.query(AnalysisFile).filter(AnalysisFile.task_id == task_id).all()
    new_file = next((f for f in files if (f.version or "").lower() == "new"), None)
    if not new_file or not new_file.extract_path:
        raise ValueError("task_id下未找到version=new的文件记录或extract_path为空")
    if not os.path.exists(new_file.extract_path):
        raise ValueError(f"新版本解压目录不存在: {new_file.extract_path}")
    return new_file.extract_path


def _get_pairs_to_review(db: Session, task_id: int) -> List[RegressionFunctionPair]:
    pairs = (
        db.query(RegressionFunctionPair)
        .filter(
            RegressionFunctionPair.task_id == task_id,
            RegressionFunctionPair.should_review == True,
            RegressionFunctionPair.change_type.in_(["new", "modified", "deleted"]),
        )
        .order_by(RegressionFunctionPair.id)
        .all()
    )
    return pairs


def run_regression_review(task_id: int) -> Dict[str, Any]:
    db_gen = get_db()
    db = next(db_gen)

    try:
        task_repo = TaskRepository(db)
        func_repo = FunctionRepository(db)
        prob_repo = ProblemRepository(db)

        task = task_repo.get_task(task_id)
        if not task:
            raise ValueError("任务不存在")

        new_extract_path = _get_new_extract_path(db, task_id)
        global_var_map = scan_global_variables(new_extract_path)
        forbidden_rules = get_rules()

        agent = FunctionReviewAgent(project_root=new_extract_path, language="c")

        pairs = _get_pairs_to_review(db, task_id)
        # 有明确的审查目标后，把进度从0推进一点，避免前端一直显示“扫描/0%”
        # 这里不引入额外字段，只更新progress；状态仍由外层start_analysis控制为processing
        try:
            if len(pairs) > 0:
                task_repo.update_task_progress(task_id, 1)
        except Exception:
            pass
        change_type_counts: Dict[str, int] = {}
        for p in pairs:
            ct = (p.change_type or "").lower() or "unknown"
            change_type_counts[ct] = change_type_counts.get(ct, 0) + 1

        log_concurrent_info(
            f"[RegressionReview] task_id={task_id} 需审查函数对数量={len(pairs)}（预计AI调用次数≈{len(pairs)}） change_type统计={change_type_counts}",
            "regression_review",
        )

        processed = 0
        created_problems = 0

        for pair in pairs:
            new_func: Optional[AnalysisFunction] = None
            old_func: Optional[AnalysisFunction] = None

            if pair.new_function_id:
                new_func = db.query(AnalysisFunction).filter(AnalysisFunction.id == pair.new_function_id).first()
            if pair.old_function_id:
                old_func = db.query(AnalysisFunction).filter(AnalysisFunction.id == pair.old_function_id).first()

            # deleted场景下可能没有new_func；此时仍需要审查（基于old_func + 明确告知已删除）
            target_func: Optional[AnalysisFunction] = new_func or old_func
            if not target_func:
                continue

            log_concurrent_info(
                f"[RegressionReview] 开始审查 pair_id={pair.id} change_type={pair.change_type} old_func_id={pair.old_function_id} new_func_id={pair.new_function_id} target={(target_func.file_path or '')}:{target_func.function_name}",
                "regression_review",
            )

            extra_context = ""
            change_type = (pair.change_type or "").lower()
            # 回归审查：尽量同时给AI旧版与新版；缺失则明确说明
            if change_type in ("new", "modified"):
                if old_func and old_func.source_code:
                    extra_context = (
                        "这是回归测试的函数审查：请结合旧版与新版对比，推断变更意图；但主要针对**当前版本（新版）**函数提出问题并输出注释代码。\n\n"
                        "以下是旧版本函数代码（用于对比）：\n\n"
                        f"旧版本文件: {old_func.file_path}\n"
                        f"旧版本函数名: {old_func.function_name}\n"
                        "旧版本代码:\n"
                        f"```c\n{old_func.source_code}\n```\n"
                    )
                else:
                    extra_context = (
                        "这是回归测试的函数审查：当前函数为**新增函数**（旧版本未找到对应实现）。\n"
                        "请推断该新增函数的意图/功能，并对当前版本实现进行审查。\n"
                    )
            elif change_type == "deleted":
                # 删除：没有新版本实现时，也要审查删除是否合理/是否破坏业务逻辑
                deleted_note = (
                    "这是回归测试的函数审查：该函数在**当前版本中已被删除**。\n"
                    "请基于旧版本函数实现与删除意图推断，审查删除是否可能引入行为变化/缺失逻辑/调用方风险。\n"
                    "如果当前版本仍存在替代实现或调用迁移，请指出需要验证的点。\n\n"
                )
                if new_func and new_func.source_code:
                    extra_context = deleted_note + (
                        "当前版本仍存在同名/相关实现（用于对比）：\n\n"
                        f"当前版本文件: {new_func.file_path}\n"
                        f"当前版本函数名: {new_func.function_name}\n"
                        "当前版本代码:\n"
                        f"```c\n{new_func.source_code}\n```\n\n"
                    )
                if old_func and old_func.source_code:
                    extra_context += (
                        "以下是旧版本函数代码（被删除的实现）：\n\n"
                        f"旧版本文件: {old_func.file_path}\n"
                        f"旧版本函数名: {old_func.function_name}\n"
                        "旧版本代码:\n"
                        f"```c\n{old_func.source_code}\n```\n"
                    )

            review_result = agent.review_function(
                function_code=(target_func.source_code or ""),
                function_name=target_func.function_name,
                file_path=target_func.file_path or "",
                global_var_map=global_var_map,
                forbidden_rules=forbidden_rules,
                extra_context=extra_context,
            )

            problems = review_result.get("problems") or []
            function_info = review_result.get("function_info") or {}

            func_repo.update_function_info(
                target_func.id,
                function_description=function_info.get("function_description"),
                commented_code=function_info.get("commented_code"),
            )
            func_repo.update_function_analyzed(target_func.id, True)

            for p in problems:
                prob_repo.create_problem(
                    {
                        "task_id": task_id,
                        "file_id": target_func.file_id,
                        "function_id": target_func.id,
                        "file_name": p.get("file_name") or (target_func.file_path or ""),
                        "source_code": p.get("source_code") or (target_func.source_code or ""),
                        "problem_reason": p.get("problem_reason"),
                        "issue_level": p.get("issue_level"),
                        "issue_name": p.get("issue_name"),
                        "issue_location": p.get("issue_location"),
                        "description_requirement": p.get("description_requirement"),
                        "description_issue": p.get("description_issue"),
                        "description_location": p.get("description_location"),
                        "description_impact": p.get("description_impact"),
                    }
                )
                created_problems += 1

            db.commit()
            processed += 1

            # 持续更新任务进度（按函数对处理进度）
            try:
                if len(pairs) > 0:
                    pct = int((processed / len(pairs)) * 100)
                    task_repo.update_task_progress(task_id, pct)
            except Exception:
                # 进度更新失败不影响主流程
                pass

        return {
            "task_id": task_id,
            "processed_pairs": processed,
            "created_problems": created_problems,
        }

    finally:
        try:
            db.close()
        except Exception:
            pass
