"""
测试项生成模块

负责根据需求内容生成各种类型的测试项。

重构后的新架构：
- ai_services/: AI服务层（AI API调用、提示词管理、内容优化）
- content_generators/: 内容生成层（测试内容生成、资产数据库增强）
- functional/: 功能测试生成（各种测试类型生成器）
- identifiers/: 标识符生成（测试标识符相关）
- ai_content/: 向后兼容层（保留旧的导入路径）
"""

# 功能测试生成
from .functional import FunctionalTestCreator, PerformanceSeparator

# AI内容生成（从新位置导入）
from .content_generators import ConfigurationItemTestContentGenerator
from .ai_services.ai_content_optimizer import translate_chinese_to_english, batch_translate_requirements

# 标识符生成
from .identifiers import TestIdentifierGenerator

# 为向后兼容，创建AIContentOptimizer包装类
class AIContentOptimizer:
    """AI内容优化器（向后兼容包装）"""
    @staticmethod
    def translate_chinese_to_english(requirement_name: str) -> str:
        return translate_chinese_to_english(requirement_name)
    
    @staticmethod
    def batch_translate_requirements(requirement_names: list) -> list:
        return batch_translate_requirements(requirement_names)

__all__ = [
    'FunctionalTestCreator',
    'PerformanceSeparator', 
    'ConfigurationItemTestContentGenerator',
    'AIContentOptimizer',
    'TestIdentifierGenerator'
] 