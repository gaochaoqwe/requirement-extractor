"""
软件配置AI生成器模块

从ai/AI_software_info_generator.py重构而来，提供软件配置信息的AI生成功能
"""

from .software_info_generator import generate_software_info_by_ai, format_software_info_for_excel

__all__ = [
    'generate_software_info_by_ai',
    'format_software_info_for_excel'
] 