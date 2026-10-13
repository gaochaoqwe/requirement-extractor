"""
文件审查问题数据访问层
"""
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from ..models.file_problem import FileReviewProblem

class FileProblemRepository:
    def __init__(self, db: Session):
        self.db = db
        self.model = FileReviewProblem
    
    def create_problem(self, problem_data: Dict[str, Any]) -> FileReviewProblem:
        """创建单个文件审查问题"""
        problem = self.model(**problem_data)
        self.db.add(problem)
        self.db.flush()
        return problem
    
    def create_problems_batch(self, problems_data: List[Dict[str, Any]]) -> List[FileReviewProblem]:
        """批量创建文件审查问题"""
        problems = [self.model(**data) for data in problems_data]
        self.db.add_all(problems)
        self.db.flush()
        return problems
    
    def get_problems_by_task(self, task_id: int) -> List[FileReviewProblem]:
        """获取任务的所有文件审查问题"""
        return self.db.query(self.model).filter(
            self.model.task_id == task_id
        ).all()
    
    def get_problems_by_file(self, task_id: int, file_name: str) -> List[FileReviewProblem]:
        """获取特定文件的所有问题"""
        return self.db.query(self.model).filter(
            self.model.task_id == task_id,
            self.model.file_name == file_name
        ).all()
    
    def get_problems_by_level(self, task_id: int, level: str) -> List[FileReviewProblem]:
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
            'files_with_issues': set()
        }
        
        for problem in problems:
            summary[problem.issue_level] += 1
            summary['files_with_issues'].add(problem.file_name)
        
        summary['files_with_issues'] = len(summary['files_with_issues'])
        
        return summary
    
    def delete_by_task(self, task_id: int):
        """删除任务的所有文件审查问题"""
        self.db.query(self.model).filter(
            self.model.task_id == task_id
        ).delete()
    
    def delete_by_file(self, task_id: int, file_name: str):
        """删除特定文件的所有问题"""
        self.db.query(self.model).filter(
            self.model.task_id == task_id,
            self.model.file_name == file_name
        ).delete()
    
    def get_problems_for_export(self, task_id: int) -> List[Dict[str, Any]]:
        """获取用于Excel导出的问题数据"""
        problems = self.get_problems_by_task(task_id)
        return [problem.to_excel_dict() for problem in problems] 