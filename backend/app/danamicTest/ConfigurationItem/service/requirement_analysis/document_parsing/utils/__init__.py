"""
文档处理工具模块

包含各种文档处理工具：
- DebugLogger: 调试日志记录器
- 文本处理工具函数
"""

from .debug_logger import DebugLogger

# 从text_utils导入工具函数
try:
    from .text_utils import (
        extract_requirement_name,
        extract_requirement_names_batch,
        extract_chapter_number,
        get_requirement_info
    )
except ImportError:
    # 提供占位符函数
    def extract_requirement_name(name):
        return name
    
    def extract_requirement_names_batch(names):
        return [extract_requirement_name(name) for name in names]
    
    def extract_chapter_number(text):
        return ""
    
    def get_requirement_info(text):
        return {"name": text, "description": ""}

__all__ = [
    'DebugLogger',
    'extract_requirement_name',
    'extract_requirement_names_batch', 
    'extract_chapter_number',
    'get_requirement_info'
] 