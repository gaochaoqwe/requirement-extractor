"""
问题仓库
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ..models.problem import AnalysisProblem
import traceback

class ProblemRepository:
    """问题仓库类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_problem(self, problem_data: Dict[str, Any]) -> AnalysisProblem:
        """创建问题记录"""
        try:
            # 打印调试信息
            print(f"创建问题记录: {problem_data.get('violation_rules', '未知规则')} - {problem_data.get('issue_name', '未知问题')}")
            
            problem = AnalysisProblem(**problem_data)
            self.db.add(problem)
            
            # 注意：这里不调用commit，因为在analysis_runner.py中会显式调用commit
            # 这样可以确保事务的完整性和一致性
            # self.db.commit()
            
            # 刷新对象以获取数据库生成的ID
            self.db.flush()
            self.db.refresh(problem)
            
            print(f"问题记录创建成功，ID: {problem.id}")
            return problem
        except Exception as e:
            print(f"创建问题记录时出错: {str(e)}")
            print(traceback.format_exc())
            # 不在这里处理回滚，由调用者处理
            raise
    
    def batch_create_problems(self, problems_data: List[Dict[str, Any]]) -> List[AnalysisProblem]:
        """批量创建问题记录"""
        if not problems_data:
            return []
        
        try:    
            problems = [AnalysisProblem(**data) for data in problems_data]
            self.db.bulk_save_objects(problems)
            # 注意：这里不调用commit，因为在analysis_runner.py中会显式调用commit
            # self.db.commit()
            print(f"批量创建了 {len(problems)} 条问题记录")
            return problems
        except Exception as e:
            print(f"批量创建问题记录时出错: {str(e)}")
            print(traceback.format_exc())
            # 不在这里处理回滚，由调用者处理
            raise
    
    def get_problem(self, problem_id: int) -> Optional[AnalysisProblem]:
        """获取问题详情"""
        return self.db.query(AnalysisProblem).filter(
            AnalysisProblem.id == problem_id
        ).first()
    
    def get_problems_by_task(self, task_id: int) -> List[Dict[str, Any]]:
        """获取任务下的所有问题"""
        from ..models.function import AnalysisFunction
        # 移除 AnalysisFile 导入，因为不再需要从该表获取文件信息
        # from ..models.file import AnalysisFile
        
        problems = self.db.query(
            AnalysisProblem,
            AnalysisFunction.function_name # 仅获取函数名
        ).join(
            AnalysisFunction, AnalysisFunction.id == AnalysisProblem.function_id
        # 移除与 AnalysisFile 的 join，因为 AnalysisProblem 本身已经包含了正确的 file_name
        # ).join(
        #     AnalysisFile, AnalysisFile.id == AnalysisFunction.file_id
        ).filter(
            AnalysisProblem.task_id == task_id
        ).all()
        
        result = []
        for problem, func_name in problems: # 调整循环变量
            problem_dict = problem.to_dict()
            problem_dict['function_name'] = func_name
            # 不需要再覆盖 file_name，因为 problem.to_dict() 已经包含了正确的 file_name
            result.append(problem_dict)
            
        return result
    
    def get_problems_by_function(self, function_id: int) -> List[AnalysisProblem]:
        """获取函数下的所有问题"""
        return self.db.query(AnalysisProblem).filter(
            AnalysisProblem.function_id == function_id
        ).all()
    
    def get_problem_stats(self, task_id: int) -> Dict[str, int]:
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
