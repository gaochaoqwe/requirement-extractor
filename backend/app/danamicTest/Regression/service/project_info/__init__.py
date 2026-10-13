"""
回归测试项目基本信息表服务模块

该模块负责处理回归测试中项目基本信息表的生成、填充和格式设置。

主要功能：
- 数据处理和组织
- Excel填充逻辑
- 格式设置和样式
- 服务层接口

作者：重构自原有代码
日期：2025-07-30
"""

from .service import RegressionProjectInfoService
from .data_processor import RegressionProjectInfoDataProcessor
from .excel_filler import RegressionProjectInfoExcelFiller
from .formatter import RegressionProjectInfoFormatter

__all__ = [
    'RegressionProjectInfoService',
    'RegressionProjectInfoDataProcessor', 
    'RegressionProjectInfoExcelFiller',
    'RegressionProjectInfoFormatter'
]
