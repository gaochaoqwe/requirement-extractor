"""
配置项测试表单构建模块

提供配置项测试的完整表单构建服务，包括：
- 无策划表的表单生成
- 有策划表的表单生成  
- 需求文档读取和处理
- 文档验证和检查
"""

from .form_builder_service import (
    ConfigurationItemFormBuilderService
)

__all__ = [
    'ConfigurationItemFormBuilderService'
] 