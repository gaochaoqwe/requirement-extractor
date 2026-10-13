"""任务仓储"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.staticAnalysis.normalModeFpga.database.postgresql_models import AnalysisTask

class TaskRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **kwargs) -> AnalysisTask:
        task = AnalysisTask(**kwargs)
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def create_task(self, data: dict) -> AnalysisTask:
        return self.create(**data)

    def get_by_id(self, task_id: int) -> Optional[AnalysisTask]:
        return self.db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()

    def get_task(self, task_id: int) -> Optional[AnalysisTask]:
        return self.get_by_id(task_id)

    def update(self, task_id: int, **kwargs) -> Optional[AnalysisTask]:
        task = self.get_by_id(task_id)
        if task:
            for key, value in kwargs.items():
                setattr(task, key, value)
            self.db.commit()
            self.db.refresh(task)
        return task

    def update_task_status(self, task_id: int, status: str, message: str = None, **kwargs) -> Optional[AnalysisTask]:
        extra = {"message": message} if message is not None else {}
        extra.update(kwargs)
        return self.update(task_id, status=status, **extra)

    def update_task_progress(self, task_id: int, progress: int, **kwargs) -> Optional[AnalysisTask]:
        return self.update(task_id, progress=progress, **kwargs)

    def delete(self, task_id: int) -> bool:
        task = self.get_by_id(task_id)
        if task:
            self.db.delete(task)
            self.db.commit()
            return True
        return False

    def list_all(self, limit: int = 100) -> List[AnalysisTask]:
        return self.db.query(AnalysisTask).order_by(AnalysisTask.created_at.desc()).limit(limit).all()
