"""
任务仓库
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from ..models.task import AnalysisTask
from ..models.file import AnalysisFile
from ..models.function import AnalysisFunction
from ..models.problem import AnalysisProblem

class TaskRepository:
    """任务仓库类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_task(self, task_data: Dict[str, Any]) -> AnalysisTask:
        """创建新任务"""
        task = AnalysisTask(**task_data)
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task
    
    def get_task(self, task_id: int) -> Optional[AnalysisTask]:
        """获取任务详情"""
        return self.db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
    
    def update_task_status(self, task_id: int, status: str, **kwargs) -> Optional[AnalysisTask]:
        """更新任务状态"""
        task = self.get_task(task_id)
        if not task:
            return None
        
        # 如果任务已处于暂停或取消状态，避免被后续流程误改为 completed
        # 例如：任务已被暂停/取消，但收尾逻辑仍然尝试将其标记为 completed
        if task.status in ["paused", "cancelled"] and status == "completed":
            return task
        
        task.status = status
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
                
        self.db.commit()
        self.db.refresh(task)
        return task
    
    def update_task_progress(self, task_id: int, progress: float) -> Optional[AnalysisTask]:
        """更新任务进度"""
        task = self.get_task(task_id)
        if not task:
            return None
        
        # 如果任务已处于暂停或取消状态，则不再更新进度
        # 目的：保持暂停/取消时的进度值，避免后续收尾逻辑把进度强行拉到100
        if task.status in ["paused", "cancelled"]:
            return task
        
        # 确保进度在0-100之间
        progress = max(0, min(100, progress))
        task.progress = int(progress)
        
        self.db.commit()
        self.db.refresh(task)
        return task
    
    def delete_task(self, task_id: int) -> bool:
        """删除任务（级联删除相关数据）"""
        task = self.get_task(task_id)
        if not task:
            return False
            
        self.db.delete(task)
        self.db.commit()
        return True
    
    def list_tasks(self, skip: int = 0, limit: int = 100) -> List[AnalysisTask]:
        """获取任务列表"""
        return self.db.query(AnalysisTask).offset(skip).limit(limit).all()
    
    def get_task_problems(self, task_id: int) -> List[Dict[str, Any]]:
        """获取任务的所有问题"""
        problems = self.db.query(
            AnalysisProblem,
            AnalysisFunction.function_name,
            AnalysisFile.file_name
        ).join(
            AnalysisFunction, AnalysisFunction.id == AnalysisProblem.function_id
        ).join(
            AnalysisFile, AnalysisFile.id == AnalysisFunction.file_id
        ).filter(
            AnalysisProblem.task_id == task_id
        ).all()
        
        result = []
        for problem, func_name, file_name in problems:
            problem_dict = problem.to_dict()
            problem_dict['function_name'] = func_name
            problem_dict['file_name'] = file_name
            result.append(problem_dict)
            
        return result

    def update_marked_problem_stats(self, task_id: int, has_marked: bool, count: int) -> Optional[AnalysisTask]:
        """更新任务的标记问题统计信息"""
        task = self.get_task(task_id)
        if not task:
            return None

        task.has_marked_problems = has_marked
        task.marked_problem_count = count

        self.db.commit()
        self.db.refresh(task)
        return task

    def set_marked_problems_exported(self, task_id: int) -> Optional[AnalysisTask]:
        """标记任务已导出过标记问题"""
        task = self.get_task(task_id)
        if not task:
            return None

        task.marked_problems_exported = True

        self.db.commit()
        self.db.refresh(task)
        return task

    def update_task_total_problems(self, task_id: int) -> int:
        """
        统计并更新任务的总问题数
        
        Args:
            task_id: 任务ID
            
        Returns:
            问题总数
        """
        task = self.get_task(task_id)
        if not task:
            return 0
        
        # 统计该任务的所有问题
        problem_count = self.db.query(AnalysisProblem).filter(
            AnalysisProblem.task_id == task_id
        ).count()
        
        task.total_problems = problem_count
        self.db.commit()
        self.db.refresh(task)
        
        return problem_count
    
    def increment_clicked_function_count(self, task_id: int) -> Optional[AnalysisTask]:
        """
        增加已点击函数数量
        
        Args:
            task_id: 任务ID
            
        Returns:
            更新后的任务对象
        """
        task = self.get_task(task_id)
        if not task:
            return None
        
        task.clicked_function_count = (task.clicked_function_count or 0) + 1
        self.db.commit()
        self.db.refresh(task)
        return task
    
    def update_comment_accuracy(self, task_id: int, accuracy_rate: str) -> Optional[AnalysisTask]:
        """
        更新任务的注释准确率反馈
        
        Args:
            task_id: 任务ID
            accuracy_rate: 准确率区间
            
        Returns:
            更新后的任务对象
        """
        from datetime import datetime
        
        task = self.get_task(task_id)
        if not task:
            return None
        
        task.comment_accuracy_rate = accuracy_rate
        task.comment_accuracy_feedback_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(task)
        return task
    
    def get_total_function_count(self, task_id: int) -> int:
        """
        获取任务的总函数数量
        
        Args:
            task_id: 任务ID
            
        Returns:
            函数总数
        """
        task = self.get_task(task_id)
        if not task:
            return 0
        
        # 统计该任务下所有文件的函数数量
        function_count = (
            self.db.query(AnalysisFunction)
            .join(AnalysisFile, AnalysisFunction.file_id == AnalysisFile.id)
            .filter(AnalysisFile.task_id == task_id)
            .count()
        )
        
        return function_count
    
    def increment_feedback_delayed_count(self, task_id: int) -> Optional[AnalysisTask]:
        """
        增加延迟反馈次数
        
        Args:
            task_id: 任务ID
            
        Returns:
            更新后的任务对象
        """
        task = self.get_task(task_id)
        if not task:
            return None
        
        task.feedback_delayed_count = (task.feedback_delayed_count or 0) + 1
        self.db.commit()
        self.db.refresh(task)
        return task
