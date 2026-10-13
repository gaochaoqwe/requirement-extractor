"""函数仓储"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.staticAnalysis.normalModeFpga.database.postgresql_models import AnalysisFunction

class FunctionRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, **kwargs) -> AnalysisFunction:
        function = AnalysisFunction(**kwargs)
        self.db.add(function)
        self.db.commit()
        self.db.refresh(function)
        return function
    
    def create_function(self, data: dict) -> AnalysisFunction:
        return self.create(**data)
    
    def bulk_create(self, functions_data: List[dict]) -> List[AnalysisFunction]:
        functions = [AnalysisFunction(**data) for data in functions_data]
        self.db.add_all(functions)
        self.db.commit()
        for func in functions:
            self.db.refresh(func)
        return functions
    
    def get_by_id(self, function_id: int) -> Optional[AnalysisFunction]:
        return self.db.query(AnalysisFunction).filter(AnalysisFunction.id == function_id).first()
    
    def get_by_file(self, file_id: int) -> List[AnalysisFunction]:
        return self.db.query(AnalysisFunction).filter(AnalysisFunction.file_id == file_id).all()
    
    def get_functions_by_file(self, file_id: int) -> List[AnalysisFunction]:
        return self.get_by_file(file_id)
    
    def update(self, function_id: int, **kwargs) -> Optional[AnalysisFunction]:
        function = self.get_by_id(function_id)
        if function:
            for key, value in kwargs.items():
                setattr(function, key, value)
            self.db.commit()
            self.db.refresh(function)
        return function
    
    def delete(self, function_id: int) -> bool:
        function = self.get_by_id(function_id)
        if function:
            self.db.delete(function)
            self.db.commit()
            return True
        return False
