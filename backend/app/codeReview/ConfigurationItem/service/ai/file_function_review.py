"""
文件+函数集成审查模块

自动识别项目类型（C/C++或FPGA）并调用相应的审查流程
"""
import threading
from typing import Dict, Any
from pathlib import Path

from .analysis_runner import run_code_review
from .function_comment_review_runner import run_function_comment_review_task
from ...config_database import get_db
from ...db.repository.task_repo import TaskRepository
from ...db.repository.problem_filter_repo import ProblemFilterRepository
from ...utils.logger import log_error, log_info
from ...utils.task_cancel_manager import task_cancel_manager


class FileFunctionReviewer:
    """文件+函数集成审查器（自动识别项目类型：C/C++或FPGA）"""
    
    def __init__(self, task_id: int, project_root: str, file_id: int, entry_function: str = 'main', tester_name: str = None):
        """
        初始化审查器
        
        Args:
            task_id: 任务ID
            project_root: 项目根目录
            file_id: 文件ID
            entry_function: 入口函数名称（暂时不使用，未来可用于优化）
            tester_name: 测试人员姓名
        """
        self.task_id = task_id
        self.file_id = file_id
        self.project_root = Path(project_root)
        self.entry_function = entry_function
        self.tester_name = tester_name

    def _run_main_review(self, results: Dict[str, Any]) -> None:
        db_gen = get_db()
        db = next(db_gen)
        try:
            run_code_review(self.file_id, self.task_id, db, tester_name=self.tester_name, finalize_task=False)
            results['main'] = {'status': 'completed'}
        except Exception as exc:
            results['main'] = {'status': 'failed', 'error': str(exc)}
            log_error(f"[函数审查] 主任务执行失败，任务ID: {self.task_id}", "file_function_review", exc)
        finally:
            try:
                db.close()
            except Exception as close_exc:
                log_error(f"[函数审查] 主任务数据库会话关闭失败，任务ID: {self.task_id}", "file_function_review", close_exc)

    def _run_comment_review(self, results: Dict[str, Any]) -> None:
        print(f"[comment_review][thread] 注释专项线程启动: task_id={self.task_id}, file_id={self.file_id}, project_root={self.project_root}")
        try:
            results['comment'] = run_function_comment_review_task(
                task_id=self.task_id,
                file_id=self.file_id,
                project_root=str(self.project_root),
            )
            print(f"[comment_review][thread] 注释专项线程结束: task_id={self.task_id}, result={results['comment']}")
        except Exception as exc:
            print(f"[comment_review][thread] 注释专项线程异常: task_id={self.task_id}, error={exc}")
            results['comment'] = {'status': 'failed', 'error': str(exc)}
            log_error(f"[函数审查] 注释专项任务执行失败，任务ID: {self.task_id}", "file_function_review", exc)
        
    def run_review(self) -> Dict[str, Any]:
        """
        运行文件+函数集成审查
        
        自动识别项目类型（C/C++、FPGA或混合），并调用相应的审查流程
        
        Returns:
            审查结果统计
        """
        log_info(f"[函数审查] 开始，任务ID: {self.task_id}", "file_function_review")
        log_info(f"[函数审查] 自动识别项目类型（支持C/C++和FPGA）", "file_function_review")
        log_info(f"[函数审查] 已启用并行注释专项检查", "file_function_review")

        results: Dict[str, Any] = {
            'main': {'status': 'pending'},
            'comment': {'status': 'pending'},
        }

        main_thread = threading.Thread(
            target=self._run_main_review,
            args=(results,),
            name=f"function_main_{self.task_id}",
        )
        comment_thread = threading.Thread(
            target=self._run_comment_review,
            args=(results,),
            name=f"function_comment_{self.task_id}",
        )

        main_thread.start()
        comment_thread.start()
        main_thread.join()
        comment_thread.join()

        main_status = results.get('main', {}).get('status')
        comment_status = results.get('comment', {}).get('status')

        if task_cancel_manager.is_cancelled(self.task_id):
            log_info(f"[函数审查] 任务已取消，任务ID: {self.task_id}", "file_function_review")
            return {
                'status': 'cancelled',
                'message': '函数审查任务已取消',
                'main_review': results.get('main', {}),
                'comment_review': results.get('comment', {}),
            }

        db_gen = get_db()
        db = next(db_gen)
        try:
            task_repo = TaskRepository(db)
            log_info(
                f"[函数审查] 并行任务汇总，任务ID: {self.task_id}, main={main_status}, comment={comment_status}, detail={results}",
                "file_function_review"
            )
            if main_status == 'completed' and comment_status in {'completed', 'cancelled', 'failed'}:
                # 统计并更新问题总数
                total_problems = task_repo.update_task_total_problems(self.task_id)
                log_info(f"[函数审查] 任务 {self.task_id} 问题总数统计完成: {total_problems} 个问题", "file_function_review")

                # 自动应用过滤规则
                try:
                    filter_repo = ProblemFilterRepository(db)
                    enabled_filters = filter_repo.get_enabled_filters(self.task_id)

                    if enabled_filters:
                        filtered_count = filter_repo.apply_filters_to_problems(self.task_id, enabled_filters)

                        # 更新任务的算法过滤计数
                        if filtered_count > 0:
                            task = task_repo.get_task(self.task_id)
                            current_count = task.algorithm_filtered_count or 0
                            task.algorithm_filtered_count = current_count + filtered_count
                            db.flush()
                            log_info(f"[函数审查] 任务 {self.task_id} 自动过滤了 {filtered_count} 个问题", "file_function_review")
                except Exception as filter_exc:
                    log_error(f"[函数审查] 自动应用过滤规则失败，任务ID: {self.task_id}", "file_function_review", filter_exc)
                    # 过滤失败不影响任务完成

                task_repo.update_task_status(self.task_id, 'completed')
                task_repo.update_task_progress(self.task_id, 100)
                task_cancel_manager.unregister_task(self.task_id)
                if comment_status == 'failed':
                    log_info(
                        f"[函数审查] 主任务完成，注释专项任务失败但不影响总任务完成，任务ID: {self.task_id}, detail={results.get('comment', {})}",
                        "file_function_review"
                    )
                else:
                    log_info(f"[函数审查] 主任务和注释专项任务均已完成，任务ID: {self.task_id}", "file_function_review")
                return {
                    'status': 'completed',
                    'message': '函数审查已完成（含注释专项检查）',
                    'main_review': results.get('main', {}),
                    'comment_review': results.get('comment', {}),
                }

            task_repo.update_task_status(self.task_id, 'failed')
            log_error(
                f"[函数审查] 并行任务执行失败，任务ID: {self.task_id}, main={main_status}, comment={comment_status}",
                'file_function_review'
            )
            return {
                'status': 'failed',
                'message': '函数审查执行失败',
                'main_review': results.get('main', {}),
                'comment_review': results.get('comment', {}),
            }
        finally:
            try:
                db.close()
            except Exception as close_exc:
                log_error(f"[函数审查] 汇总阶段数据库会话关闭失败，任务ID: {self.task_id}", "file_function_review", close_exc)
