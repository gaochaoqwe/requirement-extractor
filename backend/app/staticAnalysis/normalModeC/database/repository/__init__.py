"""
数据访问层
"""
from typing import Type, Dict, TypeVar, Any
from sqlalchemy.orm import Session

T = TypeVar('T')

# 导入所有仓库类
from .task_repo import TaskRepository
from .file_repo import FileRepository
from .function_repo import FunctionRepository
from .problem_repo import ProblemRepository

class RepositoryFactory:
    """仓库工厂类，用于管理所有仓库实例"""
    
    _repositories = {
        'task': TaskRepository,
        'file': FileRepository,
        'function': FunctionRepository,
        'problem': ProblemRepository,
    }
    
    @classmethod
    def get_repository(
        cls, 
        repo_name: str, 
        db: Session
    ) -> Any:
        """
        获取指定名称的仓库实例
        
        Args:
            repo_name: 仓库名称，如 'task', 'file' 等
            db: 数据库会话
            
        Returns:
            对应的仓库实例
            
        Raises:
            ValueError: 当指定的仓库不存在时
        """
        repo_class = cls._repositories.get(repo_name)
        if not repo_class:
            raise ValueError(f"Unknown repository: {repo_name}")
            
        return repo_class(db)
    
    @classmethod
    def register_repository(
        cls, 
        name: str, 
        repository_class: Type[Any]
    ) -> None:
        """
        注册自定义仓库类
        
        Args:
            name: 仓库名称
            repository_class: 仓库类
        """
        cls._repositories[name] = repository_class

# 导出所有仓库类
__all__ = [
    'TaskRepository',
    'FileRepository',
    'FunctionRepository',
    'ProblemRepository',
    'RepositoryFactory',
]
