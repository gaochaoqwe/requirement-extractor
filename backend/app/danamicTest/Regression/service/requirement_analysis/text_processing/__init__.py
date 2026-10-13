"""
文本处理模块 - Regression

处理文本相关的功能：
- 文本处理工具 (text_utils)
"""

from .text_utils import extract_requirement_name, extract_requirement_names_batch, extract_chapter_number, get_requirement_info

__all__ = [
    'extract_requirement_name',
    'extract_requirement_names_batch', 
    'extract_chapter_number',
    'get_requirement_info'
] 