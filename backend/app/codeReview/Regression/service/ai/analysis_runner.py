"""
回归测试分析器
负责执行回归测试静态分析和代码审查
"""
import os
import time
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session

from app.codeReview.Regression.db.repository.task_repo import TaskRepository
from app.codeReview.Regression.db.repository.file_repo import FileRepository
from app.codeReview.Regression.db.repository.problem_repo import ProblemRepository
from app.codeReview.Regression.service.ai.task_planner.regression_planner import RegressionTaskPlanner

# 导入性能监控工具
from ...utils.performance_monitor import PerformanceTimer, log_performance_summary, clear_performance_stats
from ...utils.logger import log_debug, log_info, log_error

STATIC_UPLOAD_FOLDERS = "./app/uploads/codeReviewRegression/folders"
STATIC_UPLOAD_ZIP = "./app/uploads/codeReviewRegression/zip"
TEMP_DIR = "./backend/temp"


class RegressionAnalysisRunner:
    """回归测试分析器"""
    
    def __init__(self, db: Session):
        """
        初始化回归测试分析器
        
        Args:
            db (Session): 数据库会话
        """
        self.db = db
        self.task_repo = TaskRepository(db)
        self.file_repo = FileRepository(db)
        self.problem_repo = ProblemRepository(db)
    
    def run_analysis(self, task_id: int, file_id: int) -> bool:
        """
        运行回归测试分析
        
        Args:
            task_id (int): 任务ID
            file_id (int): 文件ID
            
        Returns:
            bool: 是否分析成功
        """
        # 清除之前的性能统计
        clear_performance_stats()
        
        try:
            with PerformanceTimer("整体回归分析流程", "regression_analysis"):
                log_info(f"开始执行回归分析, task_id={task_id}, file_id={file_id}", "regression_analysis")
                
                with PerformanceTimer("任务状态更新", "database"):
                    # 更新任务状态为处理中
                    self.task_repo.update_task_status(task_id, "processing")
                    self.db.commit()
                
                with PerformanceTimer("回归测试审查执行", "ai_analysis"):
                    # 使用任务规划器执行回归测试审查
                    task_planner = RegressionTaskPlanner(self.db, task_id, file_id)
                    success = task_planner.run_regression_review()
                
                with PerformanceTimer("最终状态更新", "database"):
                    if success:
                        # 更新任务状态为已完成
                        self.task_repo.update_task_status(task_id, "completed")
                        self.task_repo.update_task_progress(task_id, 100)
                        log_info(f"回归分析完成成功, task_id={task_id}", "regression_analysis")
                    else:
                        # 更新任务状态为失败
                        self.task_repo.update_task_status(task_id, "failed")
                        log_error(f"回归分析失败, task_id={task_id}", "regression_analysis")
                    
                    self.db.commit()
            
            # 记录性能统计摘要
            log_performance_summary()
            return success

        except Exception as e:
            log_error(f"回归分析时出错: {e}", "regression_analysis", e)
            
            try:
                # 更新任务状态为失败
                self.task_repo.update_task_status(task_id, "failed")
                self.db.commit()
            except Exception:
                pass
                
            return False
