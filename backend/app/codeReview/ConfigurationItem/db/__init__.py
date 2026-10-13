"""
数据库模块
"""
# 注意：这里不能直接从config_database导入，会造成循环导入
# 请在需要使用时直接 from ..config_database import get_db
from .repository import (
    RepositoryFactory,
    TaskRepository,
    FileRepository,
    FunctionRepository,
    ProblemRepository,
)

# 导出所有公共接口
__all__ = [
    'RepositoryFactory',
    'TaskRepository',
    'FileRepository',
    'FunctionRepository',
    'ProblemRepository',
]
