"""
任务仓库模块
"""
from sqlalchemy.orm import Session
from ..models.task import AnalysisTask
from typing import Dict, Any, Optional, List

class TaskRepository:
    """
    任务仓库类
    """
    def __init__(self, db: Session):
        self.db = db
    
    def create_task(self, task_data: Dict[str, Any]) -> AnalysisTask:
        """
        创建新任务
        
        Args:
            task_data: 任务数据字典
        
        Returns:
            创建的任务对象
        """
        task = AnalysisTask(**task_data)
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task
    
    def get_task(self, task_id: str) -> Optional[AnalysisTask]:
        """
        根据ID获取任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            任务对象，如果不存在则返回None
        """
        return self.db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
    
    def update_task(self, task_id: str, update_data: Dict[str, Any]) -> Optional[AnalysisTask]:
        """
        更新任务
        
        Args:
            task_id: 任务ID
            update_data: 更新数据字典
        
        Returns:
            更新后的任务对象，如果任务不存在则返回None
        """
        task = self.get_task(task_id)
        if not task:
            return None
        
        for key, value in update_data.items():
            setattr(task, key, value)
        
        self.db.commit()
        self.db.refresh(task)
        return task
    
    def delete_task(self, task_id: str) -> bool:
        """
        删除任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            是否成功删除
        """
        task = self.get_task(task_id)
        if not task:
            return False
        
        self.db.delete(task)
        self.db.commit()
        return True
    
    def list_tasks(self, skip: int = 0, limit: int = 100) -> List[AnalysisTask]:
        """
        列出任务
        
        Args:
            skip: 跳过数量
            limit: 限制数量
        
        Returns:
            任务列表
        """
        return self.db.query(AnalysisTask).order_by(AnalysisTask.created_at.desc()).offset(skip).limit(limit).all() 