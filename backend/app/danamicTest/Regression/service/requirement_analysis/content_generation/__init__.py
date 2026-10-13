"""
内容生成模块 - Regression

负责生成回归测试相关的内容和标识：
- 测试内容生成器 (test_content_generator)
- 测试类型分类器 (test_type_classifier)
- 测试标识符处理 (test_identifier)
"""

from .test_content_generator import RegressionTestContentGenerator
from .test_type_classifier import ceshi_leixing_biaoshi_choose, ceshixiang_pipei
from .test_identifier import read_excel_columns_three

__all__ = [
    'RegressionTestContentGenerator',
    'ceshi_leixing_biaoshi_choose',
    'ceshixiang_pipei', 
    'read_excel_columns_three'
] 