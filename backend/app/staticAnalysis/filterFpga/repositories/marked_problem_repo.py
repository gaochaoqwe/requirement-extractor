"""
标记问题仓库
负责用户标记问题的CRUD操作
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from ..models.models import StaticAnalysisMarkedProblem
import json


class MarkedProblemRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_marked_problem(
        self, 
        session_id: str, 
        rule_type: str, 
        problem_key: str, 
        problem_data: Dict[str, Any], 
        marked_by: str = None
    ) -> StaticAnalysisMarkedProblem:
        """
        保存标记的问题
        如果已存在则更新，不存在则创建
        
        Args:
            session_id: 会话ID
            rule_type: 规则类型 ('gjb' 或 'cwe')
            problem_key: 问题唯一标识
            problem_data: 问题完整数据
            marked_by: 标记人
        
        Returns:
            StaticAnalysisMarkedProblem: 标记的问题对象
        """
        try:
            # 检查是否已存在
            existing = self.db.query(StaticAnalysisMarkedProblem).filter(
                and_(
                    StaticAnalysisMarkedProblem.session_id == session_id,
                    StaticAnalysisMarkedProblem.rule_type == rule_type,
                    StaticAnalysisMarkedProblem.problem_key == problem_key
                )
            ).first()
            
            # 将problem_data转换为JSON字符串
            problem_data_str = json.dumps(problem_data, ensure_ascii=False)
            
            if existing:
                # 更新现有记录
                existing.problem_data = problem_data_str
                existing.marked_by = marked_by
                self.db.flush()
                print(f"[MarkedProblemRepo] 更新标记问题: session_id={session_id}, type={rule_type}")
                return existing
            else:
                # 创建新记录
                marked_problem = StaticAnalysisMarkedProblem(
                    session_id=session_id,
                    rule_type=rule_type,
                    problem_key=problem_key,
                    problem_data=problem_data_str,
                    marked_by=marked_by
                )
                self.db.add(marked_problem)
                self.db.flush()
                print(f"[MarkedProblemRepo] 创建标记问题: session_id={session_id}, type={rule_type}")
                return marked_problem
                
        except Exception as e:
            print(f"[MarkedProblemRepo] 保存标记问题失败: {e}")
            raise

    def remove_marked_problem(self, session_id: str, rule_type: str, problem_key: str) -> bool:
        """
        移除标记的问题
        
        Args:
            session_id: 会话ID
            rule_type: 规则类型
            problem_key: 问题唯一标识
        
        Returns:
            bool: 是否成功删除
        """
        try:
            deleted_count = self.db.query(StaticAnalysisMarkedProblem).filter(
                and_(
                    StaticAnalysisMarkedProblem.session_id == session_id,
                    StaticAnalysisMarkedProblem.rule_type == rule_type,
                    StaticAnalysisMarkedProblem.problem_key == problem_key
                )
            ).delete(synchronize_session=False)
            
            self.db.flush()
            print(f"[MarkedProblemRepo] 删除标记问题: session_id={session_id}, type={rule_type}, 删除数量={deleted_count}")
            return deleted_count > 0
            
        except Exception as e:
            print(f"[MarkedProblemRepo] 删除标记问题失败: {e}")
            raise

    def get_marked_problems(self, session_id: str, rule_type: str = None) -> List[StaticAnalysisMarkedProblem]:
        """
        获取会话的所有标记问题
        
        Args:
            session_id: 会话ID
            rule_type: 规则类型（可选，如果不指定则获取所有类型）
        
        Returns:
            List[StaticAnalysisMarkedProblem]: 标记的问题列表
        """
        try:
            query = self.db.query(StaticAnalysisMarkedProblem).filter(
                StaticAnalysisMarkedProblem.session_id == session_id
            )
            
            if rule_type:
                query = query.filter(StaticAnalysisMarkedProblem.rule_type == rule_type)
            
            marked_problems = query.order_by(StaticAnalysisMarkedProblem.marked_at.desc()).all()
            print(f"[MarkedProblemRepo] 获取标记问题: session_id={session_id}, type={rule_type}, 数量={len(marked_problems)}")
            return marked_problems
            
        except Exception as e:
            print(f"[MarkedProblemRepo] 获取标记问题失败: {e}")
            raise

    def get_marked_problem_count(self, session_id: str, rule_type: str = None) -> int:
        """
        获取标记问题的数量
        
        Args:
            session_id: 会话ID
            rule_type: 规则类型（可选）
        
        Returns:
            int: 标记问题的数量
        """
        try:
            query = self.db.query(StaticAnalysisMarkedProblem).filter(
                StaticAnalysisMarkedProblem.session_id == session_id
            )
            
            if rule_type:
                query = query.filter(StaticAnalysisMarkedProblem.rule_type == rule_type)
            
            count = query.count()
            return count
            
        except Exception as e:
            print(f"[MarkedProblemRepo] 获取标记问题数量失败: {e}")
            raise

    def clear_marked_problems(self, session_id: str, rule_type: str = None) -> int:
        """
        清除会话的所有标记问题
        
        Args:
            session_id: 会话ID
            rule_type: 规则类型（可选，如果不指定则清除所有类型）
        
        Returns:
            int: 删除的数量
        """
        try:
            query = self.db.query(StaticAnalysisMarkedProblem).filter(
                StaticAnalysisMarkedProblem.session_id == session_id
            )
            
            if rule_type:
                query = query.filter(StaticAnalysisMarkedProblem.rule_type == rule_type)
            
            deleted_count = query.delete(synchronize_session=False)
            self.db.flush()
            print(f"[MarkedProblemRepo] 清除标记问题: session_id={session_id}, type={rule_type}, 删除数量={deleted_count}")
            return deleted_count
            
        except Exception as e:
            print(f"[MarkedProblemRepo] 清除标记问题失败: {e}")
            raise

    def get_marked_files(self, session_id: str, rule_type: str) -> Dict[str, Any]:
        """
        获取已标记问题所在的文件
        用于在代码树中高亮显示
        
        Args:
            session_id: 会话ID
            rule_type: 规则类型
        
        Returns:
            Dict: {
                'files': [文件名列表],
                'file_problems': {文件名: 问题数量}
            }
        """
        try:
            marked_problems = self.get_marked_problems(session_id, rule_type)
            
            files = set()
            file_problems = {}
            
            for mp in marked_problems:
                problem_data = json.loads(mp.problem_data) if isinstance(mp.problem_data, str) else mp.problem_data
                file_name = problem_data.get('issue_file')
                
                if file_name:
                    files.add(file_name)
                    file_problems[file_name] = file_problems.get(file_name, 0) + 1
            
            result = {
                'files': list(files),
                'file_problems': file_problems
            }
            
            print(f"[MarkedProblemRepo] 获取标记文件: session_id={session_id}, type={rule_type}, 文件数={len(files)}")
            return result
            
        except Exception as e:
            print(f"[MarkedProblemRepo] 获取标记文件失败: {e}")
            raise

