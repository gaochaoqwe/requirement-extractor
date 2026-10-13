"""
链路审查问题数据访问层
"""
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from ..models.chain_problem import ChainReviewProblem

class ChainReviewProblemRepository:
    """链路审查问题仓储"""
    def __init__(self, db: Session):
        self.db = db
    
    def create_problem(self, problem_data: Dict[str, Any]) -> ChainReviewProblem:
        problem = ChainReviewProblem(**problem_data)
        self.db.add(problem)
        self.db.commit()
        self.db.refresh(problem)
        return problem
    
    def get_problems_by_task(self, task_id: int) -> List[ChainReviewProblem]:
        return self.db.query(ChainReviewProblem).filter(
            ChainReviewProblem.task_id == task_id
        ).order_by(ChainReviewProblem.id).all()
    
    def delete_by_task(self, task_id: int) -> None:
        self.db.query(ChainReviewProblem).filter(
            ChainReviewProblem.task_id == task_id
        ).delete()
        self.db.commit()
