"""
标记问题仓库
负责用户标记问题的CRUD操作
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from ..models.marked_problem import MarkedProblem
import traceback

# 导入统一的日志系统
from ...utils.logger import log_debug, log_info, log_error


class MarkedProblemRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_marked_problem(self, task_id: int, analysis_type: str, problem_key: str, problem_data: Dict[str, Any], marked_by: str = None) -> MarkedProblem:
        """
        保存标记的问题
        如果已存在则更新，不存在则创建
        
        Args:
            task_id: 任务ID
            analysis_type: 分析类型 (function, chain, feature)
            problem_key: 问题唯一标识
            problem_data: 问题完整数据
            marked_by: 标记人
        
        Returns:
            MarkedProblem: 标记的问题对象
        """
        try:
            # 检查是否已存在
            existing = self.db.query(MarkedProblem).filter(
                and_(
                    MarkedProblem.task_id == task_id,
                    MarkedProblem.analysis_type == analysis_type,
                    MarkedProblem.problem_key == problem_key
                )
            ).first()
            
            if existing:
                # 更新现有记录
                existing.problem_data = problem_data
                existing.marked_by = marked_by
                self.db.flush()
                log_debug(f"更新标记问题: task_id={task_id}, type={analysis_type}, key={problem_key[:50]}...", "marked_problem_repo")
                return existing
            else:
                # 创建新记录
                marked_problem = MarkedProblem(
                    task_id=task_id,
                    analysis_type=analysis_type,
                    problem_key=problem_key,
                    problem_data=problem_data,
                    marked_by=marked_by
                )
                self.db.add(marked_problem)
                self.db.flush()
                log_debug(f"创建标记问题: task_id={task_id}, type={analysis_type}, key={problem_key[:50]}...", "marked_problem_repo")
                return marked_problem
                
        except Exception as e:
            log_error(f"保存标记问题失败: task_id={task_id}, type={analysis_type}", "marked_problem_repo", e)
            raise

    def remove_marked_problem(self, task_id: int, analysis_type: str, problem_key: str) -> bool:
        """
        移除标记的问题
        
        Args:
            task_id: 任务ID
            analysis_type: 分析类型
            problem_key: 问题唯一标识
        
        Returns:
            bool: 是否成功删除
        """
        try:
            deleted_count = self.db.query(MarkedProblem).filter(
                and_(
                    MarkedProblem.task_id == task_id,
                    MarkedProblem.analysis_type == analysis_type,
                    MarkedProblem.problem_key == problem_key
                )
            ).delete(synchronize_session=False)
            
            self.db.flush()
            log_debug(f"删除标记问题: task_id={task_id}, type={analysis_type}, 删除数量={deleted_count}", "marked_problem_repo")
            return deleted_count > 0
            
        except Exception as e:
            log_error(f"删除标记问题失败: task_id={task_id}, type={analysis_type}", "marked_problem_repo", e)
            raise

    def get_marked_problems(self, task_id: int, analysis_type: str = None) -> List[MarkedProblem]:
        """
        获取任务的所有标记问题
        
        Args:
            task_id: 任务ID
            analysis_type: 分析类型（可选，如果不指定则获取所有类型）
        
        Returns:
            List[MarkedProblem]: 标记的问题列表
        """
        try:
            query = self.db.query(MarkedProblem).filter(MarkedProblem.task_id == task_id)
            
            if analysis_type:
                query = query.filter(MarkedProblem.analysis_type == analysis_type)
            
            marked_problems = query.order_by(MarkedProblem.marked_at.desc()).all()
            log_debug(f"获取标记问题: task_id={task_id}, type={analysis_type}, 数量={len(marked_problems)}", "marked_problem_repo")
            return marked_problems
            
        except Exception as e:
            log_error(f"获取标记问题失败: task_id={task_id}, type={analysis_type}", "marked_problem_repo", e)
            raise

    def get_marked_problem_count(self, task_id: int, analysis_type: str = None) -> int:
        """
        获取标记问题的数量
        
        Args:
            task_id: 任务ID
            analysis_type: 分析类型（可选）
        
        Returns:
            int: 标记问题的数量
        """
        try:
            query = self.db.query(MarkedProblem).filter(MarkedProblem.task_id == task_id)
            
            if analysis_type:
                query = query.filter(MarkedProblem.analysis_type == analysis_type)
            
            count = query.count()
            return count
            
        except Exception as e:
            log_error(f"获取标记问题数量失败: task_id={task_id}, type={analysis_type}", "marked_problem_repo", e)
            raise

    def clear_marked_problems(self, task_id: int, analysis_type: str = None) -> int:
        """
        清除任务的所有标记问题
        
        Args:
            task_id: 任务ID
            analysis_type: 分析类型（可选，如果不指定则清除所有类型）
        
        Returns:
            int: 删除的数量
        """
        try:
            query = self.db.query(MarkedProblem).filter(MarkedProblem.task_id == task_id)
            
            if analysis_type:
                query = query.filter(MarkedProblem.analysis_type == analysis_type)
            
            deleted_count = query.delete(synchronize_session=False)
            self.db.flush()
            log_debug(f"清除标记问题: task_id={task_id}, type={analysis_type}, 删除数量={deleted_count}", "marked_problem_repo")
            return deleted_count
            
        except Exception as e:
            log_error(f"清除标记问题失败: task_id={task_id}, type={analysis_type}", "marked_problem_repo", e)
            raise

    def get_marked_files_and_functions(self, task_id: int, analysis_type: str) -> Dict[str, Any]:
        """
        获取已标记问题所在的文件和函数
        用于在代码地图中高亮显示
        
        Args:
            task_id: 任务ID
            analysis_type: 分析类型
        
        Returns:
            Dict: {
                'files': [文件名列表],
                'functions': [函数名列表],
                'file_function_map': {文件名: [函数名列表]}
            }
        """
        try:
            marked_problems = self.get_marked_problems(task_id, analysis_type)
            
            files = set()
            functions = set()
            file_function_map = {}
            
            for mp in marked_problems:
                problem_data = mp.problem_data
                file_name = problem_data.get('file_name')
                function_name = problem_data.get('function_name')
                
                if file_name:
                    files.add(file_name)
                    
                if function_name:
                    functions.add(function_name)
                    
                if file_name and function_name:
                    if file_name not in file_function_map:
                        file_function_map[file_name] = set()
                    file_function_map[file_name].add(function_name)
            
            # 转换set为list
            result = {
                'files': list(files),
                'functions': list(functions),
                'file_function_map': {k: list(v) for k, v in file_function_map.items()}
            }
            
            log_debug(f"获取标记位置: task_id={task_id}, type={analysis_type}, 文件数={len(files)}, 函数数={len(functions)}", "marked_problem_repo")
            return result
            
        except Exception as e:
            log_error(f"获取标记位置失败: task_id={task_id}, type={analysis_type}", "marked_problem_repo", e)
            raise

