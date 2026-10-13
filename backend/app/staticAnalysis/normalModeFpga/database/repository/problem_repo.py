"""问题仓储"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.staticAnalysis.normalModeFpga.database.postgresql_models import AnalysisProblem

class ProblemRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, **kwargs) -> AnalysisProblem:
        problem = AnalysisProblem(**kwargs)
        self.db.add(problem)
        self.db.commit()
        self.db.refresh(problem)
        return problem
    
    def create_problem(self, data: dict) -> AnalysisProblem:
        return self.create(**data)
    
    def bulk_create(self, problems_data: List[dict]) -> List[AnalysisProblem]:
        problems = [AnalysisProblem(**data) for data in problems_data]
        self.db.add_all(problems)
        self.db.commit()
        for prob in problems:
            self.db.refresh(prob)
        return problems
    
    def get_by_id(self, problem_id: int) -> Optional[AnalysisProblem]:
        return self.db.query(AnalysisProblem).filter(AnalysisProblem.id == problem_id).first()
    
    def get_by_task(self, task_id: int) -> List[AnalysisProblem]:
        return self.db.query(AnalysisProblem).filter(AnalysisProblem.task_id == task_id).all()
    
    def get_problems_by_task(self, task_id: int) -> List[dict]:
        problems = self.get_by_task(task_id)
        return [
            {
                "id": p.id,
                "task_id": p.task_id,
                "file_id": p.file_id,
                "function_id": p.function_id,
                "file_name": p.file_name,
                "source_code": p.source_code,
                "violation_rules": p.violation_rules,
                "issue_level": p.issue_level,
                "issue_name": p.issue_name,
                "issue_location": p.issue_location,
                "description_requirement": p.description_requirement,
                "description_issue": p.description_issue,
                "description_location": p.description_location,
                "description_impact": p.description_impact,
            }
            for p in problems
        ]
    
    def get_by_function(self, function_id: int) -> List[AnalysisProblem]:
        return self.db.query(AnalysisProblem).filter(AnalysisProblem.function_id == function_id).all()
    
    def update(self, problem_id: int, **kwargs) -> Optional[AnalysisProblem]:
        problem = self.get_by_id(problem_id)
        if problem:
            for key, value in kwargs.items():
                setattr(problem, key, value)
            self.db.commit()
            self.db.refresh(problem)
        return problem
    
    def delete(self, problem_id: int) -> bool:
        problem = self.get_by_id(problem_id)
        if problem:
            self.db.delete(problem)
            self.db.commit()
            return True
        return False
