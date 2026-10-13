"""
文档审查配置项数据库模型模块
"""
from .review_session import ReviewSession
from .review_result import ReviewResult

# 导出所有模型类
__all__ = [
    'ReviewSession',
    'ReviewResult',
] 