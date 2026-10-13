"""
问题记录仓库
负责问题数据的CRUD操作
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ..models.problem import AnalysisProblem
import traceback

# 导入统一的日志系统
from ...utils.logger import log_debug, log_info, log_error

# 导入全局过滤服务
from ...service.filter.global_filter_service import get_global_filter_service

class ProblemRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_problem(self, problem_data: Dict[str, Any]) -> AnalysisProblem:
        """创建新的问题记录（自动应用全局过滤规则）"""
        try:
            problem_reason = problem_data.get("problem_reason", "")

            # 检查是否应该被全局过滤规则过滤
            filter_service = get_global_filter_service()
            should_filter, rule_name = filter_service.should_filter_problem(problem_reason)

            # 根据过滤结果设置初始状态
            # 状态1: 未处理, 状态3: 已过滤
            initial_status = 3 if should_filter else 1

            if should_filter:
                log_debug(f"问题被全局规则'{rule_name}'过滤: {problem_data.get('issue_name', '未知问题')}", "problem_repo")

            problem = AnalysisProblem(
                task_id=problem_data.get("task_id"),
                file_id=problem_data.get("file_id"),
                function_id=problem_data.get("function_id"),
                file_name=problem_data.get("file_name"),
                source_code=problem_data.get("source_code"),
                problem_reason=problem_reason,
                problem_source=problem_data.get("problem_source", "main_review"),
                issue_level=problem_data.get("issue_level"),
                issue_name=problem_data.get("issue_name"),
                issue_location=problem_data.get("issue_location"),
                description_requirement=problem_data.get("description_requirement"),
                description_issue=problem_data.get("description_issue"),
                description_location=problem_data.get("description_location"),
                description_impact=problem_data.get("description_impact"),
                problem_status=initial_status  # 根据过滤结果设置状态
            )

            self.db.add(problem)
            self.db.flush()

            # 如果被全局过滤，更新任务的算法过滤计数
            if should_filter:
                task_id = problem_data.get("task_id")
                if task_id:
                    from ..models.task import AnalysisTask
                    task = self.db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
                    if task:
                        current_count = task.algorithm_filtered_count or 0
                        task.algorithm_filtered_count = current_count + 1
                        self.db.flush()
                        log_debug(f"任务 {task_id} 全局过滤计数+1: {current_count} -> {task.algorithm_filtered_count}", "problem_repo")

            log_debug(f"问题记录创建成功，ID: {problem.id}, 状态: {initial_status}", "problem_repo")
            return problem
        except Exception as e:
            log_error(f"创建问题记录时出错", "problem_repo", e)
            raise

    def create_problems_batch(self, problems_data: List[Dict[str, Any]]) -> List[AnalysisProblem]:
        """批量创建问题记录（自动应用全局过滤规则）"""
        try:
            filter_service = get_global_filter_service()
            problems = []
            filtered_count = 0
            task_id_set = set()

            for problem_data in problems_data:
                problem_reason = problem_data.get("problem_reason", "")

                # 检查是否应该被过滤
                should_filter, rule_name = filter_service.should_filter_problem(problem_reason)

                # 设置初始状态
                initial_status = 3 if should_filter else 1
                problem_data['problem_status'] = initial_status
                problem_data['problem_source'] = problem_data.get('problem_source', 'main_review')

                if should_filter:
                    filtered_count += 1

                # 收集任务ID用于后续更新计数
                task_id = problem_data.get("task_id")
                if task_id:
                    task_id_set.add(task_id)

                problem = AnalysisProblem(**problem_data)
                problems.append(problem)
                self.db.add(problem)

            self.db.flush()

            # 更新任务的算法过滤计数（批量）
            if filtered_count > 0 and task_id_set:
                from ..models.task import AnalysisTask
                for task_id in task_id_set:
                    task = self.db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
                    if task:
                        current_count = task.algorithm_filtered_count or 0
                        # 统计该批次中属于该任务的过滤数量
                        task_filtered_count = sum(
                            1 for pd in problems_data
                            if pd.get("task_id") == task_id
                            and filter_service.should_filter_problem(pd.get("problem_reason", ""))[0]
                        )
                        task.algorithm_filtered_count = current_count + task_filtered_count
                        log_info(f"任务 {task_id} 批量全局过滤计数+{task_filtered_count}: {current_count} -> {task.algorithm_filtered_count}", "problem_repo")
                self.db.flush()

            log_info(f"批量创建了 {len(problems)} 条问题记录，其中 {filtered_count} 条被自动过滤", "problem_repo")
            return problems
        except Exception as e:
            log_error(f"批量创建问题记录时出错", "problem_repo", e)
            raise

    def get_problems_by_task(self, task_id: int) -> List[Dict[str, Any]]:
        """根据任务ID获取所有问题（包含函数名）"""
        from ..models.function import AnalysisFunction
        
        # 使用JOIN查询获取问题和对应的函数名
        problems_with_function = self.db.query(
            AnalysisProblem,
            AnalysisFunction.function_name
        ).join(
            AnalysisFunction, AnalysisProblem.function_id == AnalysisFunction.id
        ).filter(
            AnalysisProblem.task_id == task_id
        ).all()
        
        # 转换为字典格式
        result = []
        for problem, function_name in problems_with_function:
            problem_dict = problem.to_dict()
            problem_dict['function_name'] = function_name
            result.append(problem_dict)
        
        return result

    def get_problems_by_file(self, file_id: int) -> List[AnalysisProblem]:
        """根据文件ID获取所有问题"""
        return self.db.query(AnalysisProblem).filter(AnalysisProblem.file_id == file_id).all()

    def get_problems_by_function(self, function_id: int) -> List[AnalysisProblem]:
        """根据函数ID获取所有问题"""
        return self.db.query(AnalysisProblem).filter(AnalysisProblem.function_id == function_id).all()

    def get_problem_by_id(self, problem_id: int) -> Optional[AnalysisProblem]:
        """根据ID获取问题"""
        return self.db.query(AnalysisProblem).filter(AnalysisProblem.id == problem_id).first()

    def update_problem(self, problem_id: int, update_data: Dict[str, Any]) -> Optional[AnalysisProblem]:
        """更新问题记录"""
        problem = self.get_problem_by_id(problem_id)
        if problem:
            for key, value in update_data.items():
                if hasattr(problem, key):
                    setattr(problem, key, value)
            self.db.flush()
        return problem

    def delete_problem(self, problem_id: int) -> bool:
        """删除问题记录"""
        problem = self.get_problem_by_id(problem_id)
        if problem:
            self.db.delete(problem)
            self.db.flush()
            return True
        return False

    def delete_problems_by_task(self, task_id: int) -> int:
        """删除任务的所有问题记录"""
        count = self.db.query(AnalysisProblem).filter(AnalysisProblem.task_id == task_id).count()
        self.db.query(AnalysisProblem).filter(AnalysisProblem.task_id == task_id).delete()
        self.db.flush()
        return count
    
    def update_problems_status(self, problem_ids: List[int], status: int) -> int:
        """批量更新问题状态"""
        try:
            updated_count = self.db.query(AnalysisProblem).filter(
                AnalysisProblem.id.in_(problem_ids)
            ).update(
                {"problem_status": status},
                synchronize_session=False
            )
            self.db.flush()
            log_debug(f"更新了 {updated_count} 个问题的状态为 {status}", "problem_repo")
            return updated_count
        except Exception as e:
            log_error(f"批量更新问题状态时出错", "problem_repo", e)
            raise
    
    def get_problem_status_statistics(self, task_id: int) -> Dict[int, int]:
        """获取任务的问题状态统计
        
        Returns:
            Dict[int, int]: 状态 -> 数量的映射
        """
        try:
            from sqlalchemy import func
            
            # 查询每个状态的数量
            result = self.db.query(
                AnalysisProblem.problem_status,
                func.count(AnalysisProblem.id).label('count')
            ).filter(
                AnalysisProblem.task_id == task_id
            ).group_by(
                AnalysisProblem.problem_status
            ).all()
            
            # 转换为字典
            statistics = {row.problem_status: row.count for row in result}
            
            # 确保所有状态都有值（即使是0）
            for status in [1, 2, 3, 4]:
                if status not in statistics:
                    statistics[status] = 0
            
            log_debug(f"任务 {task_id} 的问题状态统计: {statistics}", "problem_repo")
            return statistics
        except Exception as e:
            log_error(f"获取问题状态统计时出错", "problem_repo", e)
            raise
    
    def get_problems_by_status(self, task_id: int, status: int) -> List[Dict[str, Any]]:
        """根据任务ID和状态获取问题"""
        from ..models.function import AnalysisFunction
        
        # 使用JOIN查询获取问题和对应的函数名
        problems_with_function = self.db.query(
            AnalysisProblem,
            AnalysisFunction.function_name
        ).join(
            AnalysisFunction, AnalysisProblem.function_id == AnalysisFunction.id
        ).filter(
            AnalysisProblem.task_id == task_id,
            AnalysisProblem.problem_status == status
        ).all()
        
        # 转换为字典格式
        result = []
        for problem, function_name in problems_with_function:
            problem_dict = problem.to_dict()
            problem_dict['function_name'] = function_name
            result.append(problem_dict)
        
        return result