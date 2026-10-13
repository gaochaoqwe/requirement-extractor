#!/usr/bin/env python3
"""
需求匹配器模块
专门处理需求名称的匹配和相似度计算

功能包括：
- 需求名称匹配
- 标题相似度计算
- 关键词匹配
- 编号识别
"""

import re
from typing import List, Tuple

# 导入日志工具
try:
    from ....utils.logging_utils.logger import log_info, log_error, log_debug, log_warning
except ImportError:
    try:
        from .....utils.logging_utils.logger import log_info, log_error, log_debug, log_warning
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_debug, log_warning


class RequirementMatcher:
    """需求匹配器"""
    
    def __init__(self):
        """初始化匹配器"""
        pass
    
    def is_requirement_name_match(self, heading: str, req_name: str) -> bool:
        """
        判断标题是否与需求名称匹配
        
        支持多种匹配模式：
        1. 完全匹配
        2. 包含匹配
        3. 去除标点后匹配
        4. 关键词匹配
        """
        if not heading or not req_name:
            return False
        
        heading_clean = heading.strip()
        req_name_clean = req_name.strip()
        
        # 1. 完全匹配
        if heading_clean == req_name_clean:
            log_debug(f"完全匹配: '{heading_clean}' == '{req_name_clean}'", "requirement_matcher")
            return True
        
        # 2. 包含匹配（标题包含需求名称或反之）
        if req_name_clean in heading_clean or heading_clean in req_name_clean:
            log_debug(f"包含匹配: '{heading_clean}' <-> '{req_name_clean}'", "requirement_matcher")
            return True
        
        # 3. 去除编号后匹配（提取标题中的实际名称部分）
        # 匹配模式：3.2.1 用户身份验证功能 -> 用户身份验证功能
        heading_title_match = re.search(r'^\d+(\.\d+)*\s+(.+)$', heading_clean)
        if heading_title_match:
            heading_title = heading_title_match.group(2)
            if heading_title == req_name_clean or req_name_clean in heading_title:
                log_debug(f"标题匹配: '{heading_title}' <-> '{req_name_clean}'", "requirement_matcher")
                return True
        
        # 4. 关键词匹配（去除功能、模块等通用词后比较）
        heading_keywords = set(heading_clean.replace('功能', '').replace('模块', '').split())
        req_keywords = set(req_name_clean.replace('功能', '').replace('模块', '').split())
        
        # 如果有75%以上的关键词重叠，认为匹配
        if req_keywords and heading_keywords:
            intersection = heading_keywords & req_keywords
            similarity = len(intersection) / len(req_keywords)
            if similarity >= 0.75:
                log_debug(f"关键词匹配 ({similarity:.2f}): '{heading_clean}' <-> '{req_name_clean}'", "requirement_matcher")
                return True
        
        return False
    
    def calculate_title_similarity(self, title1: str, title2: str) -> float:
        """
        计算两个标题的相似度
        
        Args:
            title1: 标题1
            title2: 标题2
            
        Returns:
            相似度分数 (0.0 - 1.0)
        """
        if not title1 or not title2:
            return 0.0
        
        title1_clean = title1.strip().lower()
        title2_clean = title2.strip().lower()
        
        # 完全匹配
        if title1_clean == title2_clean:
            return 1.0
        
        # 包含匹配
        if title1_clean in title2_clean or title2_clean in title1_clean:
            shorter = min(len(title1_clean), len(title2_clean))
            longer = max(len(title1_clean), len(title2_clean))
            return shorter / longer
        
        # 关键词匹配
        words1 = set(title1_clean.replace('功能', '').replace('模块', '').split())
        words2 = set(title2_clean.replace('功能', '').replace('模块', '').split())
        
        if words1 and words2:
            intersection = words1 & words2
            union = words1 | words2
            return len(intersection) / len(union)
        
        return 0.0
    
    def parse_requirement_name(self, requirement_name: str) -> Tuple[str, str]:
        """
        从需求名称中解析编号和标题
        如果名称包含编号，则分离；否则使用空编号
        """
        # 匹配类似 "3.2.1 用户身份验证功能" 的格式
        pattern = r'^(\d+\.\d+(?:\.\d+)*)\s+(.+)$'
        match = re.match(pattern, requirement_name.strip())
        
        if match:
            return match.group(1), match.group(2)
        else:
            # 如果没有找到编号，返回空编号和完整名称
            return '', requirement_name.strip()
    
    def has_numbering_in_requirements(self, requirement_names: List[str]) -> bool:
        """
        检查需求列表中是否包含编号格式
        
        Args:
            requirement_names: 需求名称列表
            
        Returns:
            True如果至少一个需求包含编号格式
        """
        for name in requirement_names:
            numbering, _ = self.parse_requirement_name(name)
            if numbering:
                return True
        return False


# 创建全局实例
requirement_matcher = RequirementMatcher() 