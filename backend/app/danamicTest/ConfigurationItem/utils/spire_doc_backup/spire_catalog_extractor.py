#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Spire.Doc 目录提取器 - 重构版（主入口）

提供向后兼容的公共接口。
核心功能已拆分到各个专门的模块中：

- catalog_extractor.py - 核心提取器
- xml_parser.py - XML解析
- text_filters.py - 文本过滤
- numbering_utils.py - 编号工具
- catalog_filter.py - 测试需求过滤
"""

from typing import Dict, Any

# 导入核心功能
from .catalog_extractor import extract_catalog_with_spire, SpireCatalogExtractor
from .catalog_filter import extract_testing_requirements_with_spire


def parse_and_validate_catalog(catalog_text: str) -> Dict[str, Any]:
    """
    解析和验证目录文本（兼容性函数）
    
    Args:
        catalog_text: 目录文本
        
    Returns:
        解析结果
    """
    # 导入延迟以避免循环导入
    from .text_filters import parse_and_validate_catalog as _parse_and_validate_catalog
    return _parse_and_validate_catalog(catalog_text)


# 导出所有公共接口
__all__ = [
    'extract_catalog_with_spire',
    'extract_testing_requirements_with_spire', 
    'parse_and_validate_catalog',
    'SpireCatalogExtractor'
]