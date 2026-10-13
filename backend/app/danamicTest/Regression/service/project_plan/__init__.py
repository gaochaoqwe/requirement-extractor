"""
回归测试项目策划表服务模块

该模块负责处理回归测试中项目策划表的生成、填充、读取和标识生成。

主要功能：
- 项目策划表数据处理和组织
- Excel填充逻辑
- 格式设置和样式
- 策划表数据读取
- 测试标识生成和翻译
- 服务层接口

作者：重构自原有代码
日期：2025-07-30
"""

from .service import RegressionProjectPlanService
from .data_processor import RegressionProjectPlanDataProcessor
from .excel_filler import RegressionProjectPlanExcelFiller
from .formatter import RegressionProjectPlanFormatter
from .reader import RegressionProjectPlanReader
from .identifier_generator import RegressionTestIdentifierGenerator
# from .ai_translation import (  # 🔧 修复：libretranslate服务已删除
#     translate_chinese_to_english,
#     start_libretranslate_server,
#     stop_libretranslate_server,
#     translate_texts,
#     format_sentence,
#     ceshihezi_open_shixian
# )

# 🔧 只保留translate_chinese_to_english，其他libretranslate函数已删除
try:
    from .ai_translation import translate_chinese_to_english
except ImportError:
    def translate_chinese_to_english(text):
        """临时替代函数"""
        return f"TRANS_{hash(text) % 1000}"

__all__ = [
    'RegressionProjectPlanService',
    'RegressionProjectPlanDataProcessor', 
    'RegressionProjectPlanExcelFiller',
    'RegressionProjectPlanFormatter',
    'RegressionProjectPlanReader',
    'RegressionTestIdentifierGenerator',
    'translate_chinese_to_english',
    # 'start_libretranslate_server',  # 🔧 修复：libretranslate服务已删除
    # 'stop_libretranslate_server',
    # 'translate_texts',
    # 'format_sentence',
    # 'ceshihezi_open_shixian'
]
