"""
AI内容生成模块（向后兼容层）

注意：此模块已重构，文件已移动到新的目录结构：
- AI服务 → ai_services/
- 内容生成 → content_generators/

此文件保留用于向后兼容。
"""

# 从新位置导入
from ..content_generators.test_content_generator import ConfigurationItemTestContentGenerator
from ..ai_services.ai_content_optimizer import translate_chinese_to_english, batch_translate_requirements

# 为向后兼容，创建一个包装类
class AIContentOptimizer:
    """AI内容优化器（向后兼容包装）"""
    @staticmethod
    def translate_chinese_to_english(requirement_name: str) -> str:
        return translate_chinese_to_english(requirement_name)
    
    @staticmethod
    def batch_translate_requirements(requirement_names: list) -> list:
        return batch_translate_requirements(requirement_names)

__all__ = ['ConfigurationItemTestContentGenerator', 'AIContentOptimizer'] 