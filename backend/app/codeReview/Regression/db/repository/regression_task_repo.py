"""
回归测试任务Repository
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.regression_task import RegressionTask


class RegressionTaskRepository:
    """回归测试任务Repository"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_task(self, task_data: Dict[str, Any]) -> RegressionTask:
        """
        创建新的回归测试任务
        
        Args:
            task_data: 任务数据
            
        Returns:
            RegressionTask: 创建的任务对象
        """
        task = RegressionTask(
            analysis_task_id=task_data["analysis_task_id"],
            task_id=task_data["task_id"],
            task_name=task_data["task_name"],
            task_description=task_data.get("task_description", ""),
            change_type=task_data.get("change_type", "unknown"),
            original_report_content=task_data.get("original_report_content", "")  # 新增字段
        )
        
        self.db.add(task)
        self.db.flush()  # 获取ID但不提交
        return task
    
    def batch_create_tasks(self, tasks_data: List[Dict[str, Any]]) -> List[RegressionTask]:
        """
        批量创建回归测试任务
        
        Args:
            tasks_data: 任务数据列表
            
        Returns:
            List[RegressionTask]: 创建的任务对象列表
        """
        tasks = []
        for task_data in tasks_data:
            task = RegressionTask(
                analysis_task_id=task_data["analysis_task_id"],
                task_id=task_data["task_id"],
                task_name=task_data["task_name"],
                task_description=task_data.get("task_description", ""),
                change_type=task_data.get("change_type", "unknown"),
                original_report_content=task_data.get("original_report_content", "")  # 新增字段
            )
            tasks.append(task)
        
        self.db.add_all(tasks)
        self.db.flush()  # 获取ID但不提交
        return tasks
    
    def get_tasks_by_analysis_id(self, analysis_task_id: str) -> List[RegressionTask]:
        """
        根据分析任务ID获取所有任务
        
        Args:
            analysis_task_id: 分析任务ID
            
        Returns:
            List[RegressionTask]: 任务列表
        """
        return self.db.query(RegressionTask).filter(
            RegressionTask.analysis_task_id == analysis_task_id
        ).order_by(RegressionTask.task_id).all()
    
    def get_task_by_ids(self, analysis_task_id: str, task_id: str) -> Optional[RegressionTask]:
        """
        根据分析任务ID和任务ID获取特定任务
        
        Args:
            analysis_task_id: 分析任务ID
            task_id: 任务ID
            
        Returns:
            Optional[RegressionTask]: 任务对象或None
        """
        return self.db.query(RegressionTask).filter(
            and_(
                RegressionTask.analysis_task_id == analysis_task_id,
                RegressionTask.task_id == task_id
            )
        ).first()
    
    def update_task_status(self, analysis_task_id: str, task_id: str, status: str) -> bool:
        """
        更新任务状态
        
        Args:
            analysis_task_id: 分析任务ID
            task_id: 任务ID
            status: 新状态
            
        Returns:
            bool: 是否更新成功
        """
        task = self.get_task_by_ids(analysis_task_id, task_id)
        if task:
            task.status = status
            return True
        return False
    
    def update_task_progress(self, analysis_task_id: str, task_id: str, progress: float) -> bool:
        """
        更新任务进度
        
        Args:
            analysis_task_id: 分析任务ID
            task_id: 任务ID
            progress: 进度百分比
            
        Returns:
            bool: 是否更新成功
        """
        task = self.get_task_by_ids(analysis_task_id, task_id)
        if task:
            task.progress = progress
            return True
        return False
    
    def update_task_result(self, analysis_task_id: str, task_id: str, result: str) -> bool:
        """
        更新任务结果
        
        Args:
            analysis_task_id: 分析任务ID
            task_id: 任务ID
            result: 审查结果
            
        Returns:
            bool: 是否更新成功
        """
        task = self.get_task_by_ids(analysis_task_id, task_id)
        if task:
            task.result = result
            return True
        return False
    
    def delete_task(self, task_id: int) -> bool:
        """
        删除任务
        
        Args:
            task_id: 任务的数据库ID
            
        Returns:
            bool: 是否删除成功
        """
        task = self.db.query(RegressionTask).filter(RegressionTask.id == task_id).first()
        if task:
            self.db.delete(task)
            return True
        return False 