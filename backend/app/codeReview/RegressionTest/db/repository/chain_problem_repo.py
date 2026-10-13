"""
链路审查问题数据访问层
"""
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from ..models.chain_problem import ChainReviewProblem

class ChainProblemRepository:
    def __init__(self, db: Session):
        self.db = db
        self.model = ChainReviewProblem
    
    def create_problem(self, problem_data: Dict[str, Any]) -> ChainReviewProblem:
        """创建单个链路审查问题"""
        problem = self.model(**problem_data)
        self.db.add(problem)
        self.db.flush()
        return problem
    
    def create_problems_batch(self, problems_data: List[Dict[str, Any]]) -> List[ChainReviewProblem]:
        """批量创建链路审查问题"""
        problems = [self.model(**data) for data in problems_data]
        self.db.add_all(problems)
        self.db.flush()
        return problems
    
    def get_problems_by_task(self, task_id: int) -> List[ChainReviewProblem]:
        """获取任务的所有链路审查问题"""
        return self.db.query(self.model).filter(
            self.model.task_id == task_id
        ).all()
    
    def get_problems_by_chain(self, task_id: int, chain_name: str) -> List[ChainReviewProblem]:
        """获取特定链路的所有问题"""
        return self.db.query(self.model).filter(
            self.model.task_id == task_id,
            self.model.chain_name == chain_name
        ).all()
    
    def get_problems_by_level(self, task_id: int, level: str) -> List[ChainReviewProblem]:
        """按严重程度获取问题"""
        return self.db.query(self.model).filter(
            self.model.task_id == task_id,
            self.model.issue_level == level
        ).all()
    
    def get_problems_summary(self, task_id: int) -> Dict[str, int]:
        """获取问题统计摘要"""
        problems = self.get_problems_by_task(task_id)
        
        summary = {
            'total': len(problems),
            '严重': 0,
            '一般': 0,
            '建议': 0,
            'chains_with_issues': set()
        }
        
        for problem in problems:
            summary[problem.issue_level] += 1
            summary['chains_with_issues'].add(problem.chain_name)
        
        summary['chains_with_issues'] = len(summary['chains_with_issues'])
        
        return summary
    
    def delete_by_task(self, task_id: int):
        """删除任务的所有链路审查问题"""
        self.db.query(self.model).filter(
            self.model.task_id == task_id
        ).delete()
    
    def delete_by_chain(self, task_id: int, chain_name: str):
        """删除特定链路的所有问题"""
        self.db.query(self.model).filter(
            self.model.task_id == task_id,
            self.model.chain_name == chain_name
        ).delete()
    
    def get_problems_for_export(self, task_id: int) -> List[Dict[str, Any]]:
        """获取用于Excel导出的问题数据"""
        problems = self.get_problems_by_task(task_id)
        return [problem.to_excel_dict() for problem in problems] 