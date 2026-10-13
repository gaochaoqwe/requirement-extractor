#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Spire.Doc 目录提取模块

重构版本：
- 核心功能拆分到多个专门模块
- 提供完整的目录提取和测试需求过滤功能
- 支持XML直接解析和高精度标题识别

主要模块：
- catalog_extractor: 核心提取器
- xml_parser: XML解析器
- text_filters: 文本过滤器  
- numbering_utils: 编号工具
- catalog_filter: 测试需求过滤器
"""

# 导入主要接口
from .spire_catalog_extractor import (
    extract_catalog_with_spire,
    extract_testing_requirements_with_spire,
    parse_and_validate_catalog,
    SpireCatalogExtractor
)

# 导入文档标准化接口
from .document_standardizer import (
    create_standardized_requirement_document,
    create_standardized_document_from_single_file,
    DocumentStandardizer
)

# 导入标准化文档提取接口
from .standardized_catalog_extractor import (
    extract_3_2_requirements_from_standardized_docx,
    StandardizedCatalogExtractor
)

# 导入子模块类（供高级用户使用）
from .catalog_extractor import SpireCatalogExtractor as _CoreExtractor
from .xml_parser import DocxXmlParser
from .text_filters import TextFilter
from .numbering_utils import NumberingManager, HeadingGenerator
from .catalog_filter import CatalogFilter

__all__ = [
    # 主要公共接口
    'extract_catalog_with_spire',
    'extract_testing_requirements_with_spire', 
    'parse_and_validate_catalog',
    'SpireCatalogExtractor',
    
    # 文档标准化接口
    'create_standardized_requirement_document',
    'create_standardized_document_from_single_file',
    'DocumentStandardizer',
    
    # 标准化文档提取接口
    'extract_3_2_requirements_from_standardized_docx',
    'StandardizedCatalogExtractor',
    
    # 子模块类（高级功能）
    'DocxXmlParser',
    'TextFilter', 
    'NumberingManager',
    'HeadingGenerator',
    'CatalogFilter'
] 