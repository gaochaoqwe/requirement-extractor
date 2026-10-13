"""
回归测试任务规划器
负责执行回归测试代码审查的三阶段流程：
1. 任务规划阶段：生成任务列表并存储到数据库
2. 差异映射阶段：扫描代码差异并映射到任务
3. 深度审查阶段：执行具体的代码审查（支持并发处理）
"""
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from ..openai.client import AIClient
from .task_generator import generate_tasks
from .enhanced_diff_mapper import EnhancedDiffMapper
from .deep_reviewer import perform_deep_review
from ....db.models import RegressionTask, DiffMapping
from ....db.repository.regression_task_repo import RegressionTaskRepository
from ....db.repository.diff_mapping_repo import DiffMappingRepository
from ....db.repository.task_repo import TaskRepository
from ....db.repository.file_repo import FileRepository

# 导入性能监控工具
from ....utils.performance_monitor import PerformanceTimer
from ....utils.logger import log_debug, log_info, log_error

# 导入并发日志系统
from ....utils.concurrent_logger import (
    init_concurrent_regression_task, set_current_regression_thread_task, 
    clear_current_regression_thread_task, log_regression_concurrent_debug, 
    log_regression_concurrent_info, log_regression_concurrent_warning, 
    log_regression_concurrent_error, log_regression_concurrent_ai_result,
    finalize_concurrent_regression_task
)

# 导入并发配置
from ....config import AI_CONCURRENT_REQUESTS


class RegressionTaskPlanner:
    """回归测试任务规划器"""
    
    def __init__(self, db: Session, analysis_task_id: str, file_id: int):
        """
        初始化回归测试任务规划器
        
        Args:
            db: 数据库会话
            analysis_task_id: 分析任务ID
            file_id: 文件ID
        """
        self.db = db
        self.analysis_task_id = analysis_task_id
        self.task_id = analysis_task_id  # 使用analysis_task_id作为task_id
        self.file_id = file_id
        
        # 初始化Repository
        self.task_repo = TaskRepository(db)
        self.file_repo = FileRepository(db)
        self.regression_task_repo = RegressionTaskRepository(db)
        self.diff_mapping_repo = DiffMappingRepository(db)
        
        # 初始化AI客户端
        self.ai_client = AIClient()
        
        # 初始化增强的差异映射器
        self.enhanced_diff_mapper = EnhancedDiffMapper(db, analysis_task_id)
        
        # 初始化数据存储
        self.extract_path = None
        self.impact_report_content = None
        self.tasks = []
    
    def run_regression_review(self) -> bool:
        """
        执行回归测试审查流程（优化的三阶段 + 并发处理）
        
        Returns:
            bool: 是否成功完成审查
        """
        log_info(f"开始执行回归测试审查，task_id={self.task_id}, file_id={self.file_id}", "regression_planner")
        
        # 初始化并发日志系统
        task_folder = init_concurrent_regression_task(self.task_id, self.file_id)
        log_info(f"回归测试并发日志系统已初始化，任务文件夹: {task_folder.name}", "concurrent_logger")
        
        try:
            with PerformanceTimer("数据准备阶段", "regression_planner"):
                # 阶段0: 准备数据
                if not self._prepare_data():
                    return False
            
            with PerformanceTimer("任务规划阶段", "regression_planner"):
                # 阶段1: 任务规划 - 生成任务列表并存储到数据库
                if not self._stage1_task_planning():
                    return False
            
            with PerformanceTimer("差异映射阶段", "regression_planner"):
                # 阶段2: 差异映射 - 扫描代码差异并映射到任务，存储映射信息
                if not self._stage2_diff_mapping():
                    return False
            
            with PerformanceTimer("深度审查阶段", "regression_planner"):
                # 阶段3: 深度审查 - 基于映射信息执行代码审查（支持并发）
                if not self._stage3_concurrent_deep_review():
                    return False
            
            with PerformanceTimer("报告生成阶段", "regression_planner"):
                # 阶段4: 完成报告准备
                if not self._stage4_generate_report():
                    return False
            
            # 完成审查
            log_info(f"回归测试审查完成", "regression_planner")
            self.task_repo.update_task_status(self.task_id, "completed")
            self.db.commit()
            return True
            
        except Exception as e:
            log_error(f"回归测试审查过程中出错", "regression_planner", e)
            return False
            
        finally:
            # 结束并发任务日志
            finalize_concurrent_regression_task(self.task_id)
    
    def _prepare_data(self) -> bool:
        """
        准备审查所需的数据
        
        Returns:
            bool: 是否成功准备数据
        """
        from .data_preparation import prepare_review_data
        
        try:
            log_info(f"开始准备数据", "regression_planner")
            
            result = prepare_review_data(self.db, self.file_id, self.task_id)
            if not result.get("success"):
                log_error(f"准备数据失败: {result.get('message', 'unknown error')}", "regression_planner")
                self.task_repo.update_task_status(self.task_id, "failed")
                self.db.commit()
                return False
            
            self.extract_path = result.get("extract_path")
            self.impact_report_content = result.get("impact_report_content")
            
            log_info(f"数据准备完成", "regression_planner")
            return True
            
        except Exception as e:
            log_error(f"准备数据时出错: {e}", "regression_planner")
            self.task_repo.update_task_status(self.task_id, "failed")
            self.db.commit()
            return False
    
    def _stage1_task_planning(self) -> bool:
        """
        阶段1: 任务规划 - 生成任务列表并存储到数据库
        
        Returns:
            bool: 是否成功完成任务规划
        """
        log_info(f"开始阶段1：任务规划", "regression_planner")
        
        try:
            # 验证输入数据
            if not self.impact_report_content:
                log_error(f"影响域分析报告内容为空", "regression_planner")
                self.task_repo.update_task_status(self.task_id, "failed")
                self.db.commit()
                return False
            
            log_info(f"影响域报告内容长度: {len(self.impact_report_content)} 字符", "regression_planner")
            
            # 调用改进的任务生成器，传入数据库会话和分析任务ID
            result = generate_tasks(
                self.ai_client, 
                self.impact_report_content,
                db=self.db,
                analysis_task_id=self.analysis_task_id
            )
            
            log_info(f"任务生成器返回结果: {result}", "regression_planner")
            
            if not result.get("success"):
                error_msg = result.get('message', 'unknown error')
                log_error(f"任务规划失败: {error_msg}", "regression_planner")
                self.task_repo.update_task_status(self.task_id, "failed")
                self.db.commit()
                return False
            
            tasks = result.get("tasks", [])
            log_info(f"阶段1完成：成功生成 {len(tasks)} 个任务", "regression_planner")
            return True
            
        except Exception as e:
            import traceback
            log_error(f"阶段1任务规划时出错: {e}", "regression_planner")
            log_error(f"详细错误信息: {traceback.format_exc()}", "regression_planner")
            self.task_repo.update_task_status(self.task_id, "failed")
            self.db.commit()
            return False
    
    def _stage2_diff_mapping(self) -> bool:
        """
        阶段2: 差异映射 - 扫描代码差异并映射到任务，存储映射信息
        现已支持并发处理以提高性能
        
        Returns:
            bool: 是否成功完成差异映射
        """
        log_info(f"开始阶段2：差异映射（支持并发处理）", "regression_planner")
        
        try:
            # 使用增强的差异映射器（已集成并发处理）
            mapping_result = self.enhanced_diff_mapper.map_diffs_to_tasks(
                self.ai_client,
                self.extract_path,
                self.impact_report_content
            )
            
            if not mapping_result.get("success"):
                log_error(f"差异映射失败: {mapping_result.get('message', 'unknown error')}", "regression_planner")
                # 差异映射失败不一定要终止整个流程，可能是没有代码变更
                if "没有找到代码差异" in mapping_result.get("message", ""):
                    log_info("[INFO] 没有找到代码差异，跳过差异映射阶段", "regression_planner")
                    return True
                else:
                    return False
            
            # 记录映射统计信息
            total_files = mapping_result.get("total_files", 0)
            total_functions = mapping_result.get("total_changes", 0)  # 更正字段名
            total_mappings = mapping_result.get("total_mappings", 0)
            
            log_info(f"阶段2完成：扫描 {total_files} 个文件，{total_functions} 个函数差异，创建 {total_mappings} 个映射", "regression_planner")
            return True
            
        except Exception as e:
            log_error(f"阶段2差异映射时出错: {e}", "regression_planner")
            return False
    
    def _stage3_deep_review(self) -> bool:
        """
        阶段3: 深度审查 - 基于映射信息执行代码审查
        
        Returns:
            bool: 是否成功完成深度审查
        """
        log_info(f"开始阶段3：深度审查", "regression_planner")
        
        try:
            # 从数据库获取任务列表
            db_tasks = self.regression_task_repo.get_tasks_by_analysis_id(self.analysis_task_id)
            
            if not db_tasks:
                log_info("[WARNING] 数据库中没有找到任务，跳过深度审查", "regression_planner")
                return True
            
            # 逐个任务执行深度审查
            completed_tasks = 0
            for i, db_task in enumerate(db_tasks):
                # 获取该任务的映射信息
                task_mappings = self.diff_mapping_repo.get_mappings_by_task_id(
                    self.analysis_task_id, 
                    db_task.task_id
                )
                
                if task_mappings:
                    log_info(f"执行深度审查 {i+1}/{len(db_tasks)}: {db_task.task_name} (映射数: {len(task_mappings)})", "regression_planner")
                    
                    # 转换为旧格式以兼容现有的深度审查函数
                    task_dict = {
                        "task_id": db_task.task_id,
                        "task_name": db_task.task_name,
                        "task_description": db_task.task_description,
                        "change_type": db_task.change_type,
                        "original_report_content": db_task.original_report_content or ""  # 添加原始报告内容
                    }
                    
                    # 转换映射信息为旧格式
                    mappings_dict = []
                    for mapping in task_mappings:
                        mapping_dict = {
                            "file_path": mapping.file_path,
                            "function_name": mapping.function_name,
                            "change_type": mapping.change_type,
                            "old_code": mapping.old_code,
                            "new_code": mapping.new_code,
                            "diff_summary": mapping.diff_summary,
                            "mapping_confidence": mapping.mapping_confidence,
                            "mapping_reason": mapping.mapping_reason
                        }
                        mappings_dict.append(mapping_dict)
                    
                    # 执行深度审查
                    success = self._perform_deep_review(task_dict, mappings_dict)
                    
                    if success:
                        completed_tasks += 1
                        # 更新数据库中的任务状态
                        self.regression_task_repo.update_task_status(
                            self.analysis_task_id, 
                            db_task.task_id, 
                            "completed"
                        )
                    else:
                        log_error(f"[WARNING] 任务 {db_task.task_id} 深度审查失败", "regression_planner")
                        self.regression_task_repo.update_task_status(
                            self.analysis_task_id, 
                            db_task.task_id, 
                            "failed"
                        )
                else:
                    log_info(f"跳过任务 {i+1}: {db_task.task_name} (无映射的代码变更)", "regression_planner")
                    # 没有映射也标记为完成
                    self.regression_task_repo.update_task_status(
                        self.analysis_task_id, 
                        db_task.task_id, 
                        "completed"
                    )
                    completed_tasks += 1
                
                # 更新进度
                progress = ((i + 1) / len(db_tasks)) * 100
                self.task_repo.update_task_progress(self.task_id, min(progress, 99))
            
            log_info(f"阶段3完成：成功完成 {completed_tasks}/{len(db_tasks)} 个任务的深度审查", "regression_planner")
            return True
            
        except Exception as e:
            log_error(f"阶段3深度审查时出错: {e}", "regression_planner")
            return False
    
    def _perform_deep_review(self, task: Dict[str, Any], task_mappings: List[Dict[str, Any]]) -> bool:
        """
        对特定任务进行深度审查
        
        Args:
            task: 任务信息（包含original_report_content）
            task_mappings: 该任务的所有映射结果
            
        Returns:
            bool: 是否成功执行深度审查
        """
        try:
            result = perform_deep_review(
                self.ai_client,
                task,
                task_mappings,
                None,  # 不再传递完整的impact_report_content，使用任务中的original_report_content
                self.db,
                self.task_id,
                self.file_id
            )
            
            return result.get("success", False)
            
        except Exception as e:
            log_error(f"深度审查任务 {task.get('task_id')} 时出错: {e}", "regression_planner")
            return False

    def _stage4_generate_report(self) -> bool:
        """
        阶段4: 完成报告准备
        
        Returns:
            bool: 是否成功完成报告准备
        """
        log_info(f"开始阶段4：完成报告准备", "regression_planner")
        
        try:
            from .report_generator import generate_regression_report
            
            # 完成报告准备
            result = generate_regression_report(
                self.db,
                self.analysis_task_id,
                self.task_id,
                self.file_id,
                self.impact_report_content
            )
            
            if not result.get("success"):
                log_error(f"报告准备失败: {result.get('message', 'unknown error')}", "regression_planner")
                return False
            
            log_info(f"阶段4完成：报告数据已准备完成，可通过下载接口获取Excel报告", "regression_planner")
            return True
            
        except Exception as e:
            log_error(f"阶段4报告准备时出错: {e}", "regression_planner")
            return False
    
    def _stage3_concurrent_deep_review(self) -> bool:
        """
        阶段3：并发深度审查 - 基于映射信息执行代码审查
        
        Returns:
            bool: 是否成功执行审查
        """
        log_info(f"开始阶段3：并发深度审查", "regression_planner")
        
        try:
            # 从数据库获取任务列表
            db_tasks = self.regression_task_repo.get_tasks_by_analysis_id(self.analysis_task_id)
            
            if not db_tasks:
                log_info("[WARNING] 数据库中没有找到任务，跳过深度审查", "regression_planner")
                return True

            # 使用并发执行深度审查
            completed_tasks = self._process_tasks_concurrently(db_tasks)
            
            self.db.commit()
            log_info(f"阶段3：并发深度审查 - 总计 {completed_tasks}/{len(db_tasks)} 个任务完成", "regression_planner")
            return completed_tasks > 0
            
        except Exception as e:
            self.db.rollback()
            log_error(f"阶段3深度审查失败", "regression_planner", e)
            return False
    
    def _process_tasks_concurrently(self, db_tasks: List) -> int:
        """
        并发处理所有回归测试任务
        
        Args:
            db_tasks: 数据库任务列表
            
        Returns:
            int: 成功完成的任务数量
        """
        total_tasks = len(db_tasks)
        completed_tasks = 0
        processed_counter = {'count': 0}
        progress_lock = threading.Lock()
        
        # 使用线程池执行器进行并发处理
        with ThreadPoolExecutor(max_workers=AI_CONCURRENT_REQUESTS) as executor:
            log_info(f"启动并发处理，最大并发数: {AI_CONCURRENT_REQUESTS}, 总任务数: {total_tasks}", "concurrent_processor")
            
            # 提交所有任务到线程池
            futures = []
            for i, db_task in enumerate(db_tasks):
                future = executor.submit(
                    self._process_single_regression_task_with_new_db,
                    db_task, i, total_tasks, processed_counter, progress_lock
                )
                futures.append(future)
            
            # 等待所有任务完成
            for future in as_completed(futures):
                try:
                    success = future.result()  # 获取结果
                    if success:
                        completed_tasks += 1
                except Exception as e:
                    log_error(f"并发处理回归测试任务时发生错误", "concurrent_processor", e)
            
            # 线程池执行完成后，清理所有活跃的线程上下文
            log_info(f"回归测试并发处理完成，清理线程上下文", "concurrent_processor")
        
        return completed_tasks
    
    def _process_single_regression_task_with_new_db(self, db_task, task_index: int, 
                                                   total_tasks: int, processed_counter: dict, 
                                                   progress_lock: threading.Lock) -> bool:
        """
        使用新数据库会话处理单个回归测试任务（线程安全版本）
        
        Args:
            db_task: 数据库任务对象
            task_index: 任务索引
            total_tasks: 总任务数
            processed_counter: 已处理计数器
            progress_lock: 进度更新锁
            
        Returns:
            bool: 是否处理成功
        """
        from ....db.database import get_db
        from ....db.repository.regression_task_repo import RegressionTaskRepository
        from ....db.repository.diff_mapping_repo import DiffMappingRepository
        
        # 为每个线程创建独立的数据库会话
        db_gen = get_db()
        new_db = next(db_gen)
        
        try:
            # 使用实际线程ID设置线程专用日志，避免重复创建
            actual_thread_id = threading.current_thread().ident
            thread_name = f"regression_worker_{actual_thread_id}"
            
            # 检查是否已经设置过线程任务（避免重复初始化）
            from ....utils.concurrent_logger import get_current_regression_thread_info
            current_task_id, current_file_id, current_log_file, current_thread_name = get_current_regression_thread_info()
            
            if current_task_id != self.task_id or current_thread_name != thread_name:
                set_current_regression_thread_task(self.task_id, self.file_id, thread_name)
                log_regression_concurrent_info(f"回归测试线程 {thread_name} 初始化完成", "thread_manager")
            
            log_regression_concurrent_info(f"线程 {thread_name} 开始处理任务: {db_task.task_name}", "task_processor")
            
            # 创建仓储对象
            regression_task_repo = RegressionTaskRepository(new_db)
            diff_mapping_repo = DiffMappingRepository(new_db)
            
            # 获取该任务的映射信息
            task_mappings = diff_mapping_repo.get_mappings_by_task_id(
                self.analysis_task_id, 
                db_task.task_id
            )
            
            if task_mappings:
                log_regression_concurrent_info(f"执行深度审查: {db_task.task_name} (映射数: {len(task_mappings)})", "regression_planner")
                
                # 转换为旧格式以兼容现有的深度审查函数
                task_dict = {
                    "task_id": db_task.task_id,
                    "task_name": db_task.task_name,
                    "task_description": db_task.task_description,
                    "change_type": db_task.change_type,
                    "original_report_content": db_task.original_report_content or ""
                }
                
                # 转换映射信息为旧格式
                mappings_dict = []
                for mapping in task_mappings:
                    mapping_dict = {
                        "file_path": mapping.file_path,
                        "function_name": mapping.function_name,
                        "change_type": mapping.change_type,
                        "old_code": mapping.old_code,
                        "new_code": mapping.new_code,
                        "diff_summary": mapping.diff_summary,
                        "mapping_confidence": mapping.mapping_confidence,
                        "mapping_reason": mapping.mapping_reason
                    }
                    mappings_dict.append(mapping_dict)
                
                # 执行深度审查
                success = self._perform_deep_review_concurrent(task_dict, mappings_dict, new_db)
                
                # 更新任务状态
                if success:
                    regression_task_repo.update_task_status(
                        self.analysis_task_id, 
                        db_task.task_id, 
                        "completed"
                    )
                    log_regression_concurrent_info(f"任务 {db_task.task_id} 深度审查成功", "regression_planner")
                else:
                    regression_task_repo.update_task_status(
                        self.analysis_task_id, 
                        db_task.task_id, 
                        "failed"
                    )
                    log_regression_concurrent_error(f"任务 {db_task.task_id} 深度审查失败", "regression_planner")
                
                new_db.commit()
                
                # 更新进度
                with progress_lock:
                    processed_counter['count'] += 1
                    progress = (processed_counter['count'] / total_tasks) * 100
                    log_regression_concurrent_info(f"进度: {processed_counter['count']}/{total_tasks} ({progress:.1f}%)", "concurrent_processor")
                
                return success
            else:
                log_regression_concurrent_info(f"任务 {db_task.task_id} 没有映射信息，跳过", "regression_planner")
                return True
                
        except Exception as e:
            new_db.rollback()
            log_regression_concurrent_error(f"处理任务 {db_task.task_id} 时发生严重错误", "regression_analyzer", e)
            return False
            
        finally:
            # 注意：不在这里清除线程日志上下文，因为同一线程可能处理多个任务
            # 线程日志上下文会在线程真正结束时自动清除
            
            # 确保数据库会话被正确关闭
            try:
                new_db.close()
            except Exception as e:
                print(f"关闭数据库会话时出错: {e}")
    
    def _perform_deep_review_concurrent(self, task: Dict[str, Any], task_mappings: List[Dict[str, Any]], db: Session) -> bool:
        """
        并发版本的深度审查函数
        
        Args:
            task: 任务信息
            task_mappings: 任务映射信息
            db: 数据库会话
            
        Returns:
            bool: 是否审查成功
        """
        try:
            # 调用原始的深度审查函数，但传入新的数据库会话
            result = perform_deep_review(
                self.ai_client,
                task,
                task_mappings,
                self.impact_report_content or "",
                db,
                self.task_id,
                self.file_id
            )
            
            # 记录AI结果
            log_regression_concurrent_ai_result(result, task.get("task_name", ""), "ai_analyzer")
            
            return result.get("success", False)
            
        except Exception as e:
            log_regression_concurrent_error(f"深度审查执行失败: {task.get('task_name')}", "deep_reviewer", e)
            return False
