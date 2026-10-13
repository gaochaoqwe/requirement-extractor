#!/usr/bin/env python3
"""
文档文本分析模块
专门处理Word文档的文本解析、标题识别、章节分割等基础分析功能

功能包括：
- 标题识别和验证
- 目录行检测  
- 文档章节分割
- 章节级别计算
- 章节编号提取
"""

import re
from typing import Dict, List, Tuple
from pathlib import Path

# 导入日志工具
try:
    from .....utils.logging_utils.logger import log_info, log_error, log_debug, log_warning
except ImportError:
    try:
        from .....utils.logging_utils.logger import log_info, log_error, log_debug, log_warning
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_debug, log_warning


class DocumentTextAnalyzer:
    """文档文本分析器"""
    
    def __init__(self):
        """初始化分析器"""
        pass
    
    def is_likely_heading(self, paragraph: str) -> bool:
        """
        判断一个段落是否可能是标题（基于文档审查模块的算法）
        
        规则：
        1. 段落去除首尾空白后字符数 < 30
        2. 不包含标点符号（除了英文句点）
        3. 不包含关键字 "图" 或 "表"
        4. 不能是列表项格式（以字母/数字编号开头）
        5. 可以包含数字编号格式（如 3.2.2）
        6. 不能是方括号中的描述性文本
        7. 增强：智能排除目录页内容（基于行末页数）
        """
        text = paragraph.strip()

        # 1. 必须非空且少于 30 个字符
        if not text or len(text) >= 30:
            return False

        # 2. 排除列表项格式（a)、b)、c)等）
        if re.match(r'^[a-z]\)', text) or re.match(r'^\d+\)', text):
            return False

        # 3. 不能含有标点（除了英文句点）
        punctuation_pattern = r'[。！？；;：:,，、\?\!\(\)（）\-]'
        if re.search(punctuation_pattern, text):
            return False

        # 4. 不能包含图/表
        if ('图' in text) or ('表' in text):
            return False

        # 5. 不能是方括号中的描述性文本
        if text.startswith('[') and text.endswith(']'):
            return False
            
        # 6. 增强功能：排除目录页内容（基于行末页数）
        if self._is_table_of_contents_line(text):
            return False

        # 7. 标题类型判断：支持数字编号标题和功能性标题
        # 7.1 传统数字编号标题（如3.2.1 用户身份验证功能）
        is_numbered_heading = re.match(r'^\d+\.\d+', text)
        
        # 7.2 功能性需求标题（如用户身份验证功能）
        is_functional_heading = (
            text.endswith('功能') and 
            len(text) <= 50 and  # 标题长度合理
            not re.search(r'[，。；：？！]', text) and  # 不包含中文标点
            len(text) > 4  # 不能太短
        )
        
        if not (is_numbered_heading or is_functional_heading):
            return False

        # 8. 不能是纯数字（如页码）
        if text.isdigit():
            return False

        return True
    
    def _is_table_of_contents_line(self, text: str) -> bool:
        """
        智能判断是否是目录行
        基于用户建议：目录行的特点是末尾有页数
        
        目录行的典型模式：
        - 3.2.1 用户身份验证功能 ............................ 25
        - 3.2.2 数据批量导入功能 ...... 27
        - 3.2.3 实时通知推送功能...................................30
        """
        # 模式1: 标题 + 连续点号/破折号 + 页数
        pattern1 = r'^.+[\.。\-─]{3,}\s*\d+\s*$'
        if re.match(pattern1, text):
            # log_debug(f"识别到目录行(模式1-点号): {text}", "document_text_analyzer")
            return True
        
        # 模式2: 编号 + 标题 + 点号 + 页数
        pattern2 = r'^\d+(\.\d+)*\s+.+[\.。\-─]{2,}\s*\d+\s*$'
        if re.match(pattern2, text):
            # log_debug(f"识别到目录行(模式2-编号+点号): {text}", "document_text_analyzer")
            return True
        
        # 模式3: 行末尾是独立的数字（页数），且前面有较多空格或点号
        pattern3 = r'^.+[\s\.。\-─]{3,}\d{1,3}\s*$'
        if re.match(pattern3, text):
            if re.search(r'[\.。]{3,}|\s{5,}', text):
                # log_debug(f"识别到目录行(模式3-空格/点号+页数): {text}", "document_text_analyzer")
                return True
        
        # 模式4: 包含"第X页"、"页码"等明确页数标识
        pattern4 = r'.*(第\s*\d+\s*页|页码\s*:?\s*\d+|page\s+\d+).*'
        if re.match(pattern4, text, re.IGNORECASE):
            # log_debug(f"识别到目录行(模式4-页数标识): {text}", "document_text_analyzer")
            return True
        
        # 模式5: 整行主要由点号、破折号、空格和数字组成（目录填充行）
        text_without_numbering = re.sub(r'^\d+(\.\d+)*\s*', '', text)
        if len(text_without_numbering) > 10:
            fill_chars = len(re.findall(r'[\.。\-─\s]', text_without_numbering))
            total_chars = len(text_without_numbering)
            if fill_chars / total_chars > 0.6:  # 60%以上是填充字符
                # log_debug(f"识别到目录行(模式5-填充字符): {text}", "document_text_analyzer")
                return True
        
        return False
    
    def split_document_by_headings(self, text: str) -> List[Dict[str, str]]:
        """
        根据标题将文档分割为章节
        
        Args:
            text: 文档全文
            
        Returns:
            章节列表，每个章节包含 heading 和 content
        """
        lines = text.split('\n')
        sections = []
        current_heading = ""
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 判断是否为标题
            if self.is_likely_heading(line):
                # 如果有之前的章节，保存它
                if current_heading:
                    sections.append({
                        'heading': current_heading,
                        'content': '\n'.join(current_content).strip(),
                        'level': self._get_heading_level(current_heading)
                    })
                
                # 开始新章节
                current_heading = line
                current_content = []
            else:
                # 添加到当前章节内容
                if current_heading:  # 只有在有标题后才开始收集内容
                    current_content.append(line)
        
        # 保存最后一个章节
        if current_heading:
            sections.append({
                'heading': current_heading,
                'content': '\n'.join(current_content).strip(),
                'level': self._get_heading_level(current_heading)
            })
        
        # log_info(f"文档分割完成，共识别 {len(sections)} 个章节", "document_text_analyzer")
        return sections
    
    def _get_heading_level(self, heading: str) -> int:
        """计算标题级别（根据编号中点的数量）"""
        numbering, _, _ = self.extract_chapter_number(heading)
        if numbering:
            return numbering.count('.') + 1
        return 0
    
    def extract_chapter_number(self, text: str) -> Tuple[str, str, int]:
        """
        从文本中提取章节编号
        
        Args:
            text: 输入文本，如 "3.2.1 用户身份验证功能"
            
        Returns:
            元组 (章节号, 章节名称, 级别)
        """
        # 匹配模式：数字.数字(.数字)* + 空格 + 标题
        pattern = r'^(\d+(?:\.\d+)*)\s+(.+)$'
        match = re.match(pattern, text.strip())
        
        if match:
            numbering = match.group(1)
            title = match.group(2)
            level = numbering.count('.') + 1
            return numbering, title, level
        
        # 如果没有匹配到标准格式，返回空编号
        return '', text.strip(), 0


# 创建全局实例
document_analyzer = DocumentTextAnalyzer() 