"""
回归测试用例生成AI分析模块

从ai/test_analysis.py重构而来，提供回归测试相关的AI分析功能
"""

from .test_analysis import (
    translate_chinese_to_english, 
    analyze_requirement_text, 
    analyze_code_impact
)

__all__ = [
    'translate_chinese_to_english',
    'analyze_requirement_text',
    'analyze_code_impact'
] 