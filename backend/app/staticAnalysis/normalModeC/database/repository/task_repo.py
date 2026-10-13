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
    
    def get_latest_task(self) -> Optional[AnalysisTask]:
        """获取最新的任务"""
        return self.db.query(AnalysisTask).order_by(AnalysisTask.id.desc()).first()
    
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
