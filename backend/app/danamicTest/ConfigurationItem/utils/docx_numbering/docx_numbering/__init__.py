"""
DOCX Numbering Package

A Python package for reading automatic numbering from DOCX files.
"""

from .reader import NumberedDocxReader
from .exceptions import (
    DocxNumberingError,
    InvalidDocxFileError,
    NumberingNotFoundError,
    NumberFormatError,
    UnsupportedFormatError,
)

__version__ = "0.4.0"
__all__ = [
    "NumberedDocxReader",
    "DocxNumberingError",
    "InvalidDocxFileError",
    "NumberingNotFoundError",
    "NumberFormatError",
    "UnsupportedFormatError",
]

# 版本更新说明：
# v0.4.0 - 重大修复：编号读取准确性
#   - _extract_displayed_numbering(): 直接从段落文本提取显示的编号
#   - _infer_numbering_level_from_display(): 基于显示编号推断正确层级
#   - 修复编号计数器错误，现在显示正确的1.、1.1、1.2.1等编号
#   - 避免Word内部计数器导致的7.、9.等错误编号
# v0.4.0 - 修复编号重复问题和算法优化 (最新推荐版本)
#   - 🔧 修复编号重复问题：避免 "1.  1. 验证用户名..." 这样的重复显示
#   - 🚀 新增显示编号提取：优先使用段落文本中的可见编号
#   - ⚡ 缓存重置优化：确保get_full_document_content使用最新逻辑
#   - ✅ 推荐方法：get_numbering_structure(), get_full_document_content(), get_complete_formatted_document()
#   - ⚠️ 废弃方法：get_paragraphs_with_numbering(), get_numbered_paragraphs_only(), get_enhanced_numbering_info()
# v0.3.0 - 新增完整文档内容读取功能
#   - get_full_document_content(): 获取文档所有段落（编号+普通段落）
#   - get_complete_formatted_document(): 获取完整格式化文档（包含所有内容）
#   - 大幅改进内容完整性：从50行增加到143行，包含所有正文内容
# v0.2.0 - 新增Word样式内容组合功能（部分方法已废弃）
#   - get_word_like_content(): 获取Word样式的编号+文本组合
#   - get_formatted_document(): 获取格式化的完整文档
#   - get_enhanced_word_like_content(): 获取增强的Word样式内容