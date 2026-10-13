"""
配置项测试需求分析表服务模块

该模块负责处理配置项测试中需求分析表的生成、填充、读取和分析。
经过重构，现在按照处理阶段进行模块化组织。

主要功能：
- 文档解析和预处理 (01_document_parsing)
- 内容分析和理解 (02_content_analysis) 
- 测试项生成 (03_test_generation)
- Excel操作 (04_excel_operations)
- 服务协调 (05_orchestration)

重构日期：2025-08-19
"""

import sys
import importlib
from pathlib import Path

# 获取当前模块路径
current_path = Path(__file__).parent

# 为了向后兼容，定义一些空的类和函数
class ConfigurationItemRequirementAnalysisExcelFiller:
    """Excel填充器（向后兼容占位符）"""
    def __init__(self):
        print("Warning: Using placeholder Excel filler. Please update imports to use new structure.")

class ConfigurationItemRequirementAnalysisService:
    """需求分析服务（向后兼容占位符）"""
    def __init__(self):
        # 尝试导入实际的服务实现
        try:
            import sys
            import os
            current_dir = os.path.dirname(__file__)
            service_path = os.path.join(current_dir, "05_orchestration", "requirement_analysis_service.py")
            if os.path.exists(service_path):
                # 动态导入实际的服务
                import importlib.util
                spec = importlib.util.spec_from_file_location("actual_service", service_path)
                if spec and spec.loader:
                    actual_service_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(actual_service_module)
                    self._actual_service = actual_service_module.ConfigurationItemRequirementAnalysisService()
                else:
                    self._actual_service = None
            else:
                self._actual_service = None
        except Exception as e:
            print(f"Warning: Could not load actual service: {e}")
            self._actual_service = None
    
    def __getattr__(self, name):
        """代理所有方法调用到实际的服务实例"""
        if self._actual_service and hasattr(self._actual_service, name):
            return getattr(self._actual_service, name)
        else:
            # 如果没有实际服务或方法不存在，返回一个占位符方法
            def placeholder_method(*args, **kwargs):
                print(f"Warning: Calling placeholder method '{name}'. Please update imports to use new structure.")
                return False
            return placeholder_method

class ConfigurationItemRequirementAnalysisDataProcessor:
    """数据处理器（向后兼容占位符）"""
    def __init__(self):
        print("Warning: Using placeholder data processor. Please update imports to use new structure.")

class PerformanceSeparator:
    """性能分离器（向后兼容占位符）"""
    def __init__(self):
        print("Warning: Using placeholder performance separator. Please update imports to use new structure.")

class InterfaceTestExtractor:
    """接口测试提取器（向后兼容占位符）"""
    def __init__(self):
        print("Warning: Using placeholder interface extractor. Please update imports to use new structure.")

class ConfigurationItemTestContentGenerator:
    """测试内容生成器（向后兼容占位符）"""
    def __init__(self):
        print("Warning: Using placeholder content generator. Please update imports to use new structure.")

class ConfigurationItemRequirementAnalysisFormatter:
    """格式化器（向后兼容占位符）"""
    def __init__(self):
        print("Warning: Using placeholder formatter. Please update imports to use new structure.")

class ConfigurationItemRequirementAnalysisReader:
    """读取器（向后兼容占位符）"""
    def __init__(self):
        print("Warning: Using placeholder reader. Please update imports to use new structure.")

class RequirementSpecMatcher:
    """需求规格匹配器（向后兼容占位符）"""
    def __init__(self):
        print("Warning: Using placeholder matcher. Please update imports to use new structure.")

# 导入核心组件 - 现在使用标准Python导入
from .document_parsing import DocxRequirementParser
from .content_analysis import ceshi_leixing_biaoshi_choose, PerformanceAIAnalyzer, InterfaceTestExtractor
from .test_generation import FunctionalTestCreator, PerformanceSeparator, ConfigurationItemTestContentGenerator
from .excel_operations import ConfigurationItemRequirementAnalysisReader, ConfigurationItemRequirementAnalysisFormatter
from .excel_operations.excel_main_filler import ConfigurationItemRequirementAnalysisExcelFiller
from .orchestration import ConfigurationItemRequirementAnalysisService, RealtimeRequirementAnalysisService

# 为了向后兼容，创建别名
ConfigurationItemRequirementAnalysisDataProcessor = FunctionalTestCreator

class InterfaceTableParser:
    """接口表格解析器（向后兼容占位符）"""
    def __init__(self):
        print("Warning: Using placeholder table parser. Please update imports to use new structure.")

class DocumentTextAnalyzer:
    """文档文本分析器（向后兼容占位符）"""
    def analyze(self, text):
        return {"content": text}

class RequirementContentProcessor:
    """需求内容处理器（向后兼容占位符）"""
    def process(self, content):
        return content

class DebugLogger:
    """调试日志器（向后兼容占位符）"""
    def log(self, message):
        print(f"[DEBUG] {message}")

# 向后兼容的函数
def extract_requirement_name(name):
    """提取需求名称（向后兼容函数）"""
    return name

def extract_requirement_names_batch(names):
    """批量提取需求名称（向后兼容函数）"""
    return [extract_requirement_name(name) for name in names]

def extract_chapter_number(text):
    """提取章节编号（向后兼容函数）"""
    return ""

def get_requirement_info(text):
    """获取需求信息（向后兼容函数）"""
    return {"name": text, "description": ""}

# 新增的重构后组件别名（向后兼容）
FunctionalTestCreator = ConfigurationItemRequirementAnalysisDataProcessor

# 导出所有公共接口（保持向后兼容）
__all__ = [
    # 核心组件
    'ConfigurationItemRequirementAnalysisDataProcessor', 
    'ConfigurationItemRequirementAnalysisExcelFiller',
    'ConfigurationItemRequirementAnalysisFormatter',
    'ConfigurationItemRequirementAnalysisReader',
    'PerformanceSeparator',
    'InterfaceTestExtractor',
    
    # 内容生成
    'ConfigurationItemTestContentGenerator',
    
    # 主服务
    'ConfigurationItemRequirementAnalysisService',
    
    # 文本处理工具
    'extract_requirement_name',
    'extract_requirement_names_batch',
    'extract_chapter_number',
    'get_requirement_info',
    'RequirementSpecMatcher',
    'DocxRequirementParser',
    'DocumentTextAnalyzer',
    'RequirementContentProcessor',
    'DebugLogger',
    'InterfaceTableParser',
    
    # 新增的重构后组件
    'FunctionalTestCreator',
]
