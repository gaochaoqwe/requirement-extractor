"""
软件信息提取模块

该模块用于从需求规格说明文档中自动提取软件名称、软件版本、软件标识等信息。

简化设计：
- software_info_extractor: 基于python-docx的核心提取器
- software_info_service: 业务逻辑服务，管理提取、存储和获取功能

已移除复杂的XML解析方案，仅保留python-docx方案以提高可维护性。
"""

from .software_info_extractor import (
    SoftwareInfoExtractor,
    extract_software_info_from_document
)

from .software_info_service import (
    SoftwareInfoService, 
    get_software_info_service,
    software_info_service
)

__all__ = [
    'SoftwareInfoExtractor',
    'extract_software_info_from_document', 
    'SoftwareInfoService',
    'get_software_info_service',
    'software_info_service'
] 