"""
配置项审查模块

提供文档上传、审查和管理的功能。
"""
from .utils.document_types import DocumentType, get_document_config

# 导出公共接口
__all__ = [
    'DocumentType',
    'get_document_config',
]
