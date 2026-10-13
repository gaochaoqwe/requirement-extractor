"""
回归测试软件配置项信息表服务模块

该模块负责处理回归测试中软件配置项信息表的生成、填充和格式设置。

主要功能：
- 数据处理和组织
- Excel填充逻辑
- 格式设置和样式
- 服务层接口
- AI信息生成集成
- 代码统计集成
- 环境信息智能提取

作者：重构自原有代码
日期：2025-07-30
"""

from .service import RegressionSoftwareConfigService
from .data_processor import RegressionSoftwareConfigDataProcessor
from .excel_filler import RegressionSoftwareConfigExcelFiller
from .formatter import RegressionSoftwareConfigFormatter
from .ai_generator import generate_software_info_by_ai, format_software_info_for_excel

__all__ = [
    'RegressionSoftwareConfigService',
    'RegressionSoftwareConfigDataProcessor', 
    'RegressionSoftwareConfigExcelFiller',
    'RegressionSoftwareConfigFormatter',
    'generate_software_info_by_ai',
    'format_software_info_for_excel'
]
