#!/usr/bin/env python3
"""
需求内容处理协调器（轻量版）
协调需求匹配器和内容解析器的工作

功能包括：
- 协调需求匹配和内容解析
- 提供统一的对外接口
- 保持向后兼容性
"""

from typing import Dict, List, Tuple

# 导入日志工具
try:
    from .....utils.logging_utils.logger import log_info, log_error, log_debug, log_warning
except ImportError:
    try:
        from .....utils.logging_utils.logger import log_info, log_error, log_debug, log_warning
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_debug, log_warning

# 导入专门模块
from ..analyzers.requirement_matcher import requirement_matcher
from ..analyzers.content_parser import content_parser


class RequirementContentProcessor:
    """需求内容处理协调器（轻量版）"""
    
    def __init__(self):
        """初始化协调器"""
        self.matcher = requirement_matcher
        self.parser = content_parser
    
    def find_requirement_in_sections(self, sections: List[Dict], req_name: str) -> Dict[str, str]:
        """
        在章节列表中查找指定需求的内容
        
        Args:
            sections: 章节列表
            req_name: 需求名称
            
        Returns:
            需求详细信息字典
        """
        # log_debug(f"正在查找需求: {req_name}", "requirement_content_processor")
        
        for section in sections:
            heading = section.get('heading', '')
            content = section.get('content', '')
            
            # 使用匹配器判断是否匹配
            if self.matcher.is_requirement_name_match(heading, req_name):
                # log_info(f"找到匹配需求: {heading}", "requirement_content_processor")
                # 使用解析器提取内容
                return self.parser.extract_requirement_sections_from_content(content, req_name)
        
        # 如果没有找到匹配的需求，返回默认信息
        # log_warning(f"未找到需求: {req_name}，返回默认信息", "requirement_content_processor")
        return self.parser.create_default_requirement_info(req_name)
    
    # 向后兼容的方法委托
    def _is_requirement_name_match(self, heading: str, req_name: str) -> bool:
        """匹配方法（委托给匹配器）"""
        return self.matcher.is_requirement_name_match(heading, req_name)
    
    def _extract_requirement_sections_from_content(self, content: str, req_name: str) -> Dict[str, str]:
        """内容提取方法（委托给解析器）"""
        return self.parser.extract_requirement_sections_from_content(content, req_name)
    
    def _create_default_requirement_info(self, req_name: str) -> Dict[str, str]:
        """默认信息生成（委托给解析器）"""
        return self.parser.create_default_requirement_info(req_name)
    
    def _parse_requirement_name(self, requirement_name: str) -> Tuple[str, str]:
        """需求名称解析（委托给匹配器）"""
        return self.matcher.parse_requirement_name(requirement_name)
    
    def _has_numbering_in_requirements(self, requirement_names: List[str]) -> bool:
        """编号检查（委托给匹配器）"""
        return self.matcher.has_numbering_in_requirements(requirement_names)
    
    def _calculate_title_similarity_simple(self, title1: str, title2: str) -> float:
        """相似度计算（委托给匹配器）"""
        return self.matcher.calculate_title_similarity(title1, title2)
    
    # 为了向后兼容，保留一些原有的方法名
    def _identify_section_type(self, paragraph: str):
        """段落类型识别（委托给解析器）"""
        return self.parser.identify_section_type(paragraph)
    
    def _extract_content_after_marker(self, paragraph: str) -> str:
        """标记后内容提取（委托给解析器）"""
        return self.parser.extract_content_after_marker(paragraph)
    
    def _process_section_content(self, content_list: List[str]) -> str:
        """段落内容处理（委托给解析器）"""
        return self.parser.process_section_content(content_list)


# 创建全局实例（保持向后兼容）
requirement_processor = RequirementContentProcessor() 