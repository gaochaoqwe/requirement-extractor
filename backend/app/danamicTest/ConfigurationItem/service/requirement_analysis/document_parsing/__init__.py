"""
文档解析和预处理模块

该模块负责处理各种文档格式的解析和预处理工作，现在按功能组织为子模块：

子模块结构：
- parsers/: 各种专门的文档解析器
- analyzers/: 文档内容分析器
- processors/: 文档内容处理器
- utils/: 文档处理工具和实用函数

主要功能：
- DOCX文档的结构化解析
- 接口表格的提取和解析
- 性能章节的专门提取
- 章节内容的分析和提取
- 文档文本的预处理
"""

# 从子模块导入主要组件
try:
    from .parsers import (
        DocxRequirementParser,
        InterfaceTableParser,
        PerformanceChapterExtractor,
        ChapterContentExtractor,
        SpireRequirementExtractor
    )
except ImportError as e:
    print(f"Warning: Failed to import parsers: {e}")
    DocxRequirementParser = None
    InterfaceTableParser = None
    PerformanceChapterExtractor = None
    ChapterContentExtractor = None
    SpireRequirementExtractor = None

try:
    from .analyzers import (
        DocumentTextAnalyzer,
        ContentParser,
        RequirementMatcher
    )
except ImportError as e:
    print(f"Warning: Failed to import analyzers: {e}")
    DocumentTextAnalyzer = None
    ContentParser = None
    RequirementMatcher = None

try:
    from .processors import (
        RequirementContentProcessor
    )
except ImportError as e:
    print(f"Warning: Failed to import processors: {e}")
    RequirementContentProcessor = None

try:
    from .utils import (
        DebugLogger,
        extract_requirement_name,
        extract_requirement_names_batch,
        extract_chapter_number,
        get_requirement_info
    )
except ImportError as e:
    print(f"Warning: Failed to import utils: {e}")
    DebugLogger = None
    # 提供占位符函数
    def extract_requirement_name(name):
        return name
    
    def extract_requirement_names_batch(names):
        return [extract_requirement_name(name) for name in names]
    
    def extract_chapter_number(text):
        return ""
    
    def get_requirement_info(text):
        return {"name": text, "description": ""}

# 为向后兼容创建实例
try:
    document_analyzer = DocumentTextAnalyzer() if DocumentTextAnalyzer else None
except:
    document_analyzer = None

try:
    requirement_processor = RequirementContentProcessor() if RequirementContentProcessor else None
except:
    requirement_processor = None

try:
    debug_logger = DebugLogger() if DebugLogger else None
except:
    debug_logger = None

# SpireCatalogExtractor 是外部依赖，可能不可用
try:
    from app.danamicTest.ConfigurationItem.utils.spire_doc import SpireCatalogExtractor
except ImportError:
    SpireCatalogExtractor = None

# 动态构建导出列表，只包含成功导入的组件
__all__ = []

# 添加成功导入的组件
_components = {
    'DocxRequirementParser': DocxRequirementParser,
    'InterfaceTableParser': InterfaceTableParser,
    'PerformanceChapterExtractor': PerformanceChapterExtractor,
    'ChapterContentExtractor': ChapterContentExtractor,
    'SpireRequirementExtractor': SpireRequirementExtractor,
    'DocumentTextAnalyzer': DocumentTextAnalyzer,
    'ContentParser': ContentParser,
    'RequirementMatcher': RequirementMatcher,
    'RequirementContentProcessor': RequirementContentProcessor,
    'DebugLogger': DebugLogger,
    'document_analyzer': document_analyzer,
    'requirement_processor': requirement_processor,
    'debug_logger': debug_logger,
    'extract_requirement_name': extract_requirement_name,
    'extract_requirement_names_batch': extract_requirement_names_batch,
    'extract_chapter_number': extract_chapter_number,
    'get_requirement_info': get_requirement_info
}

for name, component in _components.items():
    if component is not None:
        __all__.append(name)

# 如果SpireCatalogExtractor可用，添加到导出列表
if SpireCatalogExtractor:
    __all__.append('SpireCatalogExtractor') 