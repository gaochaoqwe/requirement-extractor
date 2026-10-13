"""
回归测试需求分析模块

该模块负责处理回归测试中需求分析表的生成、填充、读取和分析。

主要功能：
- 需求分析表数据处理和组织
- Excel填充逻辑
- 格式设置和样式
- 测试描述和方法生成
- AI分析集成
- 数据库查询和匹配
- 服务层接口

作者：重构自原有代码
日期：2025-07-31
"""

from .service import RegressionRequirementAnalysisService
from .core import (
    RegressionRequirementAnalysisDataProcessor,
    RegressionRequirementAnalysisExcelFiller,
    RegressionRequirementAnalysisFormatter,
    RegressionRequirementAnalysisReader
)
from .content_generation import (
    RegressionTestContentGenerator,
    ceshi_leixing_biaoshi_choose,
    ceshixiang_pipei,
    read_excel_columns_three
)
from .text_processing import (
    extract_requirement_name,
    extract_requirement_names_batch,
    extract_chapter_number,
    get_requirement_info
)

__all__ = [
    'RegressionRequirementAnalysisService',
    'RegressionRequirementAnalysisDataProcessor', 
    'RegressionRequirementAnalysisExcelFiller',
    'RegressionRequirementAnalysisFormatter',
    'RegressionRequirementAnalysisReader',
    'RegressionTestContentGenerator',
    'ceshi_leixing_biaoshi_choose',
    'ceshixiang_pipei',
    'read_excel_columns_three',
    'extract_requirement_name',
    'extract_requirement_names_batch',
    'extract_chapter_number',
    'get_requirement_info'
] 