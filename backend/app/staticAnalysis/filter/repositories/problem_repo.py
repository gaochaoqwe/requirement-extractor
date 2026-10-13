"""
问题仓库
负责问题状态管理的CRUD操作
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from ..config.config import USE_POSTGRESQL

# 根据数据库类型导入正确的模型
if USE_POSTGRESQL:
    from ..database.postgresql_models import StaticAnalysisIssue, StaticAnalysisSession
else:
    from ..models.models import StaticAnalysisIssue, StaticAnalysisSession


class ProblemRepository:
    def __init__(self, db: Session):
        self.db = db

    def update_problem_status(self, problem_id: int, status: int) -> bool:
        """
        更新单个问题的状态
        
        Args:
            problem_id: 问题ID
            status: 新状态 (1=新发现, 2=已查看, 3=已过滤, 4=已标记)
        
        Returns:
            bool: 是否成功更新
        """
        try:
            problem = self.db.query(StaticAnalysisIssue).filter(
                StaticAnalysisIssue.id == problem_id
            ).first()
            
            if problem:
                problem.problem_status = status
                self.db.flush()
                print(f"[ProblemRepo] 更新问题状态: id={problem_id}, status={status}")
                return True
            return False
            
        except Exception as e:
            print(f"[ProblemRepo] 更新问题状态失败: {e}")
            raise

    def update_problems_status(self, problem_ids: List[int], status: int) -> int:
        """
        批量更新问题状态
        
        Args:
            problem_ids: 问题ID列表
            status: 新状态
        
        Returns:
            int: 更新的数量
        """
        try:
            updated_count = self.db.query(StaticAnalysisIssue).filter(
                StaticAnalysisIssue.id.in_(problem_ids)
            ).update(
                {'problem_status': status},
                synchronize_session=False
            )
            
            self.db.flush()
            print(f"[ProblemRepo] 批量更新问题状态: count={updated_count}, status={status}")
            return updated_count
            
        except Exception as e:
            print(f"[ProblemRepo] 批量更新问题状态失败: {e}")
            raise

    def get_problem_status_statistics(self, session_id: str) -> Dict[str, int]:
        """
        获取会话的问题状态统计
        
        Args:
            session_id: 会话ID
        
        Returns:
            Dict: 状态统计
        """
        try:
            # 通过join获取该session的所有问题统计
            session = self.db.query(StaticAnalysisSession).filter(
                StaticAnalysisSession.session_id == session_id
            ).first()
            
            if not session:
                return {}
            
            # 统计各状态的问题数
            status_counts = self.db.query(
                StaticAnalysisIssue.problem_status,
                func.count(StaticAnalysisIssue.id).label('count')
            ).filter(
                StaticAnalysisIssue.task_id == session.id
            ).group_by(
                StaticAnalysisIssue.problem_status
            ).all()
            
            statistics = {
                'status_1': 0,  # 新发现
                'status_2': 0,  # 已查看
                'status_3': 0,  # 已过滤
                'status_4': 0,  # 已标记
            }
            
            for status, count in status_counts:
                statistics[f'status_{status}'] = count
            
            print(f"[ProblemRepo] 获取问题状态统计: session_id={session_id}, statistics={statistics}")
            return statistics
            
        except Exception as e:
            print(f"[ProblemRepo] 获取问题状态统计失败: {e}")
            raise

    def get_problems_by_session(
        self, 
        session_id: str, 
        status: Optional[int] = None,
        rule_type: Optional[str] = None
    ) -> List[StaticAnalysisIssue]:
        """
        获取会话的问题列表
        
        Args:
            session_id: 会话ID
            status: 状态过滤（可选）
            rule_type: 规则类型过滤（可选）
        
        Returns:
            List[StaticAnalysisIssue]: 问题列表
        """
        try:
            session = self.db.query(StaticAnalysisSession).filter(
                StaticAnalysisSession.session_id == session_id
            ).first()
            
            if not session:
                return []
            
            query = self.db.query(StaticAnalysisIssue).filter(
                StaticAnalysisIssue.task_id == session.id
            )
            
            if status is not None:
                query = query.filter(StaticAnalysisIssue.problem_status == status)
            
            if rule_type:
                query = query.filter(StaticAnalysisIssue.rule_type == rule_type)
            
            problems = query.all()
            print(f"[ProblemRepo] 获取问题列表: session_id={session_id}, status={status}, count={len(problems)}")
            return problems
            
        except Exception as e:
            print(f"[ProblemRepo] 获取问题列表失败: {e}")
            raise

    def mark_problems_as_viewed(self, problem_ids: List[int]) -> int:
        """
        将问题标记为已查看（状态2）
        
        Args:
            problem_ids: 问题ID列表
        
        Returns:
            int: 更新的数量
        """
        return self.update_problems_status(problem_ids, 2)

    def mark_problems_as_filtered(self, problem_ids: List[int]) -> int:
        """
        将问题标记为已过滤（状态3）
        
        Args:
            problem_ids: 问题ID列表
        
        Returns:
            int: 更新的数量
        """
        return self.update_problems_status(problem_ids, 3)

    def mark_problems_as_marked(self, problem_ids: List[int]) -> int:
        """
        将问题标记为已标记（状态4）
        
        Args:
            problem_ids: 问题ID列表
        
        Returns:
            int: 更新的数量
        """
        return self.update_problems_status(problem_ids, 4)
