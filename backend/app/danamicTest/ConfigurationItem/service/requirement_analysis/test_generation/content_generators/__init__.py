"""
内容生成层模块

专注于测试内容的业务逻辑生成，包括：
- 测试内容生成 (test_content_generator.py)
- 资产数据库增强 (asset_database_enhancer.py)
"""

from .test_content_generator import ConfigurationItemTestContentGenerator

__all__ = [
    'ConfigurationItemTestContentGenerator'
] 