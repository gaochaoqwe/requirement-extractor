"""
问题记录仓库
负责问题数据的CRUD操作
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ..models.problem import AnalysisProblem
import traceback
from ...utils.logger import log_debug, log_error, log_info

class ProblemRepository:
    """问题仓库类"""
    
    def __init__(self, db: Session):
        self.db = db

    def create_problem(self, problem_data: Dict[str, Any]) -> AnalysisProblem:
        """创建新的问题记录"""
        try:
            log_debug(f"创建问题记录: {problem_data.get('violation_rules', '未知规则')} - {problem_data.get('issue_name', '未知问题')}", "problem_repo")
            
            problem = AnalysisProblem(
                task_id=problem_data.get("task_id"),
                file_id=problem_data.get("file_id"),
                function_id=problem_data.get("function_id"),
                file_name=problem_data.get("file_name", ""),
                source_code=problem_data.get("source_code", ""),
                violation_rules=problem_data.get("violation_rules", ""),
                issue_level=problem_data.get("issue_level", ""),
                issue_name=problem_data.get("issue_name", ""),
                issue_location=problem_data.get("issue_location", ""),
                description_requirement=problem_data.get("description_requirement", ""),
                description_issue=problem_data.get("description_issue", ""),
                description_location=problem_data.get("description_location", ""),
                description_impact=problem_data.get("description_impact", "")
            )
            
            self.db.add(problem)
            self.db.flush()  # 获取ID但不提交
            log_info(f"问题记录创建成功，ID: {problem.id}", "problem_repo")
            return problem
        except Exception as e:
            log_error(f"创建问题记录时出错", "problem_repo", e)
            raise

    def create_problems_batch(self, problems_data: List[Dict[str, Any]]) -> List[AnalysisProblem]:
        """批量创建问题记录"""
        try:
            problems = []
            for problem_data in problems_data:
                problem = AnalysisProblem(**problem_data)
                problems.append(problem)
                self.db.add(problem)
            
            self.db.flush()  # 获取ID但不提交
            log_info(f"批量创建了 {len(problems)} 条问题记录", "problem_repo")
            return problems
            
        except Exception as e:
            log_error(f"批量创建问题记录时出错", "problem_repo", e)
            raise
    
    def get_problem(self, problem_id: int) -> Optional[AnalysisProblem]:
        """获取问题详情"""
        return self.db.query(AnalysisProblem).filter(
            AnalysisProblem.id == problem_id
        ).first()
    
    def get_problems_by_task(self, task_id: str) -> List[Dict[str, Any]]:
        """获取任务下的所有问题"""
        from ..models.function import AnalysisFunction
        
        problems = self.db.query(
            AnalysisProblem,
            AnalysisFunction.function_name
        ).join(
            AnalysisFunction, AnalysisFunction.id == AnalysisProblem.function_id
        ).filter(
            AnalysisProblem.task_id == task_id
        ).all()
        
        result = []
        for problem, func_name in problems:
            problem_dict = problem.to_dict()
            problem_dict['function_name'] = func_name
            result.append(problem_dict)
            
        return result
    
    def get_problems_by_task_sorted_by_regression_task(self, task_id: str) -> List[Dict[str, Any]]:
        """获取任务下的所有问题，按回归测试任务ID排序"""
        from ..models.function import AnalysisFunction
        
        problems = self.db.query(
            AnalysisProblem,
            AnalysisFunction.function_name
        ).join(
            AnalysisFunction, AnalysisFunction.id == AnalysisProblem.function_id
        ).filter(
            AnalysisProblem.task_id == task_id
        ).order_by(
            AnalysisProblem.regression_task_id.asc().nulls_last(),
            AnalysisProblem.id.asc()
        ).all()
        
        result = []
        for problem, func_name in problems:
            problem_dict = problem.to_dict()
            problem_dict['function_name'] = func_name
            result.append(problem_dict)
            
        return result
    
    def get_problems_by_function(self, function_id: int) -> List[AnalysisProblem]:
        """获取函数下的所有问题"""
        return self.db.query(AnalysisProblem).filter(
            AnalysisProblem.function_id == function_id
        ).all()
    
    def get_problem_stats(self, task_id: str) -> Dict[str, int]:
        """获取问题统计信息"""
        from sqlalchemy import func
        
        # 按规则分组统计问题数
        stats = self.db.query(
            AnalysisProblem.violation_rules,
            func.count(AnalysisProblem.id).label('count')
        ).filter(
            AnalysisProblem.task_id == task_id
        ).group_by(
            AnalysisProblem.violation_rules
        ).all()
        
        # 转换为字典格式
        return {rule: count for rule, count in stats}
