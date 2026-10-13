"""
问题过滤规则仓库
负责过滤规则的CRUD操作
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ..models.problem_filter import ProblemFilterRule
from ..models.problem import AnalysisProblem
from datetime import datetime

# 导入统一的日志系统
from ...utils.logger import log_debug, log_info, log_error


class ProblemFilterRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_filter(
        self,
        task_id: int,
        keywords: List[str],
        filter_name: Optional[str] = None,
        is_enabled: bool = True,
        logic_type: str = 'AND',
        template_id: Optional[int] = None
    ) -> ProblemFilterRule:
        """创建过滤规则"""
        try:
            log_debug(f"创建过滤规则: task_id={task_id}, keywords={keywords}", "problem_filter_repo")
            
            filter_rule = ProblemFilterRule(
                task_id=task_id,
                filter_name=filter_name,
                keywords=keywords,  # SQLAlchemy会自动转换为JSON
                logic_type=logic_type,
                template_id=template_id,
                is_enabled=is_enabled
            )
            
            self.db.add(filter_rule)
            self.db.flush()
            log_debug(f"过滤规则创建成功，ID: {filter_rule.id}", "problem_filter_repo")
            return filter_rule
        except Exception as e:
            log_error(f"创建过滤规则时出错", "problem_filter_repo", e)
            raise

    def get_filter_by_id(self, filter_id: int) -> Optional[ProblemFilterRule]:
        """根据ID获取过滤规则"""
        return self.db.query(ProblemFilterRule).filter(ProblemFilterRule.id == filter_id).first()

    def get_filters_by_task(self, task_id: int) -> List[ProblemFilterRule]:
        """获取任务的所有过滤规则"""
        return self.db.query(ProblemFilterRule).filter(ProblemFilterRule.task_id == task_id).all()

    def get_enabled_filters(self, task_id: int) -> List[ProblemFilterRule]:
        """获取任务的所有启用的过滤规则"""
        return self.db.query(ProblemFilterRule).filter(
            ProblemFilterRule.task_id == task_id,
            ProblemFilterRule.is_enabled == True
        ).all()

    def update_filter(self, filter_id: int, update_data: Dict[str, Any]) -> Optional[ProblemFilterRule]:
        """更新过滤规则"""
        filter_rule = self.get_filter_by_id(filter_id)
        if filter_rule:
            for key, value in update_data.items():
                if hasattr(filter_rule, key):
                    setattr(filter_rule, key, value)
            filter_rule.updated_at = datetime.utcnow()
            self.db.flush()
        return filter_rule

    def delete_filter(self, filter_id: int) -> bool:
        """删除过滤规则"""
        filter_rule = self.get_filter_by_id(filter_id)
        if filter_rule:
            self.db.delete(filter_rule)
            self.db.flush()
            return True
        return False

    def apply_filters_to_problems(
        self,
        task_id: int,
        filters: List[ProblemFilterRule]
    ) -> int:
        """
        将过滤规则应用到问题上
        
        Args:
            task_id: 任务ID
            filters: 要应用的过滤规则列表
        
        Returns:
            被过滤的问题数量
        """
        try:
            # 获取任务的所有问题
            from ..models.function import AnalysisFunction
            
            problems = self.db.query(AnalysisProblem).filter(
                AnalysisProblem.task_id == task_id
            ).all()
            
            filtered_count = 0
            problem_ids_to_filter = set()
            
            for problem in problems:
                # 跳过已标记的问题（状态4）
                if problem.problem_status == 4:
                    continue
                
                problem_reason = problem.problem_reason or ""
                
                # 检查是否匹配任何过滤规则
                for filter_rule in filters:
                    if not filter_rule.is_enabled:
                        continue
                    
                    keywords = filter_rule.keywords
                    if not keywords:
                        continue
                    
                    # 根据逻辑类型进行匹配
                    logic_type = getattr(filter_rule, 'logic_type', 'AND')
                    
                    if logic_type == 'OR':
                        # OR逻辑：任一关键词存在即匹配
                        match = any(
                            keyword.lower() in problem_reason.lower()
                            for keyword in keywords
                        )
                    else:
                        # AND逻辑：所有关键词都必须存在
                        match = all(
                            keyword.lower() in problem_reason.lower()
                            for keyword in keywords
                        )
                    
                    if match:
                        problem_ids_to_filter.add(problem.id)
                        break  # 匹配任一规则即可
            
            # 批量更新状态为3（已过滤）
            if problem_ids_to_filter:
                filtered_count = self.db.query(AnalysisProblem).filter(
                    AnalysisProblem.id.in_(problem_ids_to_filter)
                ).update(
                    {"problem_status": 3},
                    synchronize_session=False
                )
                self.db.flush()
            
            log_info(f"应用过滤规则: task_id={task_id}, 过滤了 {filtered_count} 个问题", "problem_filter_repo")
            return filtered_count
        except Exception as e:
            log_error(f"应用过滤规则时出错", "problem_filter_repo", e)
            raise

    def get_filtered_problems(self, task_id: int) -> List[Dict[str, Any]]:
        """获取被过滤的问题（状态为3）"""
        from ..models.function import AnalysisFunction
        
        problems_with_function = self.db.query(
            AnalysisProblem,
            AnalysisFunction.function_name
        ).join(
            AnalysisFunction, AnalysisProblem.function_id == AnalysisFunction.id
        ).filter(
            AnalysisProblem.task_id == task_id,
            AnalysisProblem.problem_status == 3
        ).all()
        
        result = []
        for problem, function_name in problems_with_function:
            problem_dict = problem.to_dict()
            problem_dict['function_name'] = function_name
            result.append(problem_dict)
        
        return result

