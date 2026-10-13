
"""
回归测试模块

本模块负责处理回归测试相关的表单生成和分析功能。
"""

# 只导入确实存在的模块和函数
from .main import ceshibiaodan_tianchong, ceshibiaodan_tianchong_have_cehua, read_word_tables

__all__ = [
    'ceshibiaodan_tianchong',
    'read_word_tables',
    'ceshibiaodan_tianchong_have_cehua'
]

__version__ = '1.0.0' 