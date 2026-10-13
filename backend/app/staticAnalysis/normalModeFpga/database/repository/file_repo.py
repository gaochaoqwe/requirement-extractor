"""文件仓储"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.staticAnalysis.normalModeFpga.database.postgresql_models import AnalysisFile

class FileRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, **kwargs) -> AnalysisFile:
        file = AnalysisFile(**kwargs)
        self.db.add(file)
        self.db.commit()
        self.db.refresh(file)
        return file
    
    def create_file(self, data: dict) -> AnalysisFile:
        return self.create(**data)
    
    def get_by_id(self, file_id: int) -> Optional[AnalysisFile]:
        return self.db.query(AnalysisFile).filter(AnalysisFile.id == file_id).first()
    
    def get_file(self, file_id: int) -> Optional[AnalysisFile]:
        return self.get_by_id(file_id)
    
    def get_by_task(self, task_id: int) -> List[AnalysisFile]:
        return self.db.query(AnalysisFile).filter(AnalysisFile.task_id == task_id).all()
    
    def update(self, file_id: int, **kwargs) -> Optional[AnalysisFile]:
        file = self.get_by_id(file_id)
        if file:
            for key, value in kwargs.items():
                setattr(file, key, value)
            self.db.commit()
            self.db.refresh(file)
        return file
    
    def update_file_status(self, file_id: int, status: str, **kwargs) -> Optional[AnalysisFile]:
        return self.update(file_id, status=status, **kwargs)
    
    def delete(self, file_id: int) -> bool:
        file = self.get_by_id(file_id)
        if file:
            self.db.delete(file)
            self.db.commit()
            return True
        return False
