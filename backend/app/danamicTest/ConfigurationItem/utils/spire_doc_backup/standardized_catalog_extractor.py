#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标准化文档目录提取器

专门用于处理已经标准化的文档（全是手动编号的文档）
主要特点：
1. 文档中的标题已经包含手动编号（如 3.2.1 标题名称）
2. 不需要生成编号，直接提取现有编号
3. 需要排除目录页（特征：有...........和页码）
4. 依然使用样式、大纲级别等方式确认标题
"""

import os
import zipfile
import re
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from .xml_parser import DocxXmlParser
from .text_filters import TextFilter


class StandardizedCatalogExtractor:
    """标准化文档目录提取器"""
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        
        # 初始化组件
        self.xml_parser = DocxXmlParser(debug_mode)
        self.text_filter = TextFilter(debug_mode)
        
        # 解析结果缓存
        self.style_defs = {}
        self.paragraphs = []
    
    def _debug_print(self, message: str, category: str = "STANDARDIZED"):
        """调试输出"""
        if self.debug_mode:
            print(f"[{category}] {message}")
    
    def extract_catalog_from_standardized_docx(self, docx_path: str) -> Dict[str, Any]:
        """
        从标准化DOCX文件提取目录结构
        
        Args:
            docx_path: 标准化DOCX文件路径
            
        Returns:
            包含标题列表和统计信息的字典
        """
        
        if not Path(docx_path).exists():
            raise FileNotFoundError(f"文档不存在: {docx_path}")
        
        self._debug_print(f"开始提取标准化文档目录: {docx_path}", "INIT")
        
        try:
            with zipfile.ZipFile(docx_path, 'r') as docx_zip:
                # 1. 解析 XML 结构
                self._parse_xml_files(docx_zip)
                
                # 2. 提取标准化标题
                headings = self._extract_standardized_headings()
                
                # 3. 过滤3.2子章节
                filtered_headings = self._filter_3_2_subsections(headings)
                
                # 4. 格式化结果
                result = self._format_extraction_result(filtered_headings)
                
                self._debug_print(f"提取完成，识别到 {len(headings)} 个标题，过滤后 {len(filtered_headings)} 个", "RESULT")
                return result
                
        except Exception as e:
            self._debug_print(f"提取失败: {e}", "ERROR")
            raise
    
    def _parse_xml_files(self, docx_zip: zipfile.ZipFile):
        """解析XML文件"""
        
        # 解析样式定义（用于标题识别）
        self.style_defs = self.xml_parser.parse_styles_xml(docx_zip)
        
        # 解析文档内容
        self.paragraphs = self.xml_parser.parse_document_xml(docx_zip)
    
    def _extract_standardized_headings(self) -> List[Dict[str, Any]]:
        """提取标准化文档中的标题"""
        
        headings = []
        
        for para in self.paragraphs:
            heading_info = self._analyze_standardized_paragraph(para)
            if heading_info:
                headings.append(heading_info)
        
        return headings
    
    def _analyze_standardized_paragraph(self, para: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """分析标准化文档中的段落是否为标题"""
        
        text = para['text'].strip()
        style_id = para['style_id']
        outline_level = para['outline_level']
        
        if self.debug_mode:
            print(f"\n🔎 分析标准化段落: '{text[:100]}{'...' if len(text) > 100 else ''}'")
            print(f"    styleId='{style_id}', outlineLevel={outline_level}")
        
        # 1. 排除明显不是标题的内容
        if not text or len(text) > 300:  # 标题不会太长
            if self.debug_mode:
                print(f"    ❌ 文本为空或过长")
            return None
        
        # 2. 排除目录页（关键特征：包含...........和页码）
        if self._is_table_of_contents_line(text):
            if self.debug_mode:
                print(f"    ❌ 识别为目录行")
            return None
        
        # 3. 检查是否包含手动编号
        numbering, title = self._extract_manual_numbering_from_text(text)
        if not numbering:
            if self.debug_mode:
                print(f"    ❌ 未找到手动编号")
            return None
        
        # 4. 验证是否为标题（通过样式、大纲级别等）
        if not self._is_likely_heading(para, numbering, title):
            if self.debug_mode:
                print(f"    ❌ 不符合标题特征")
            return None
        
        # 5. 推断标题级别
        level = self._infer_heading_level(numbering, para)
        
        if self.debug_mode:
            print(f"    ✅ 识别为标题: 编号='{numbering}', 标题='{title}', 级别={level}")
        
        return {
            'numbering': numbering,
            'title': title,
            'full_text': text,
            'level': level,
            'style_name': style_id or '',
            'source': 'standardized_manual',
            'is_auto_numbered': False,
            'outline_level': outline_level
        }
    
    def _is_table_of_contents_line(self, text: str) -> bool:
        """判断是否为目录行"""
        
        # 目录行的特征：
        # 1. 包含连续的点号（至少3个）
        # 2. 点号后面通常有页码数字
        # 3. 可能包含制表符或特殊空格
        
        # 检查是否包含连续的点号
        if '...' in text or '…' in text:
            # 进一步检查是否符合目录格式
            
            # 模式1: 标题...........页码
            pattern1 = r'.+\.{3,}\s*\d+\s*$'
            if re.search(pattern1, text):
                return True
            
            # 模式2: 标题 ............... 页码
            pattern2 = r'.+\s+\.{3,}\s+\d+\s*$'
            if re.search(pattern2, text):
                return True
            
            # 模式3: 包含大量点号的行（可能是目录分隔线）
            dot_count = text.count('.') + text.count('…')
            if dot_count > len(text) * 0.3:  # 超过30%是点号
                return True
        
        # 检查是否为纯页码行或目录标题行
        if re.match(r'^\s*目\s*录\s*$', text) or re.match(r'^\s*\d+\s*$', text):
            return True
        
        return False
    
    def _extract_manual_numbering_from_text(self, text: str) -> Tuple[Optional[str], str]:
        """从文本中提取手动编号"""
        
        # 匹配各种编号格式
        patterns = [
            r'^(\d+(?:\.\d+)*\.?)\s+(.+)$',  # 1.2.3 标题 或 1.2.3. 标题
            r'^(\d+(?:\.\d+)*)\s+(.+)$',     # 1.2.3 标题（无结尾点）
        ]
        
        for pattern in patterns:
            match = re.match(pattern, text.strip())
            if match:
                numbering = match.group(1).rstrip('.')  # 移除结尾的点
                title = match.group(2).strip()
                
                # 验证编号格式的合理性
                if self._is_valid_numbering(numbering):
                    return numbering, title
        
        return None, text
    
    def _is_valid_numbering(self, numbering: str) -> bool:
        """验证编号格式是否合理"""
        
        # 检查编号格式
        if not re.match(r'^\d+(?:\.\d+)*$', numbering):
            return False
        
        # 检查级别深度（不超过6级）
        level_count = numbering.count('.') + 1
        if level_count > 6:
            return False
        
        # 检查每个级别的数字是否合理（不超过999）
        parts = numbering.split('.')
        for part in parts:
            if not part.isdigit() or int(part) > 999 or int(part) < 1:
                return False
        
        return True
    
    def _is_likely_heading(self, para: Dict[str, Any], numbering: str, title: str) -> bool:
        """判断是否可能是标题"""
        
        style_id = para['style_id']
        outline_level = para['outline_level']
        
        # 1. 检查大纲级别（最可靠）
        if outline_level is not None:
            if self.debug_mode:
                print(f"      ✓ 有大纲级别: {outline_level}")
            return True
        
        # 2. 检查样式名称
        if style_id:
            heading_style_patterns = [
                'heading', 'title', 'head',  # 英文模式
                '标题', '级标题', '章标题', '节标题', '条标题'  # 中文模式
            ]
            
            for pattern in heading_style_patterns:
                if pattern.lower() in style_id.lower():
                    if self.debug_mode:
                        print(f"      ✓ 样式匹配: {style_id}")
                    return True
        
        # 3. 检查编号级别（3级以内更可能是标题）
        level_count = numbering.count('.') + 1
        if level_count <= 3:
            if self.debug_mode:
                print(f"      ✓ 编号级别合理: {level_count}级")
            return True
        
        # 4. 检查标题长度（合理的标题长度）
        if 3 <= len(title) <= 50:
            if self.debug_mode:
                print(f"      ✓ 标题长度合理: {len(title)}字符")
            return True
        
        return False
    
    def _infer_heading_level(self, numbering: str, para: Dict[str, Any]) -> int:
        """推断标题级别"""
        
        # 1. 优先使用大纲级别
        outline_level = para['outline_level']
        if outline_level is not None:
            return outline_level + 1  # Word大纲级别从0开始
        
        # 2. 根据编号推断级别
        level = numbering.count('.') + 1
        
        # 3. 限制最大级别
        return min(level, 6)
    
    def _filter_3_2_subsections(self, headings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """过滤出3.2子章节的标题"""
        
        filtered = []
        
        for heading in headings:
            numbering = heading['numbering']
            
            # 检查是否为3.2开头的编号
            if numbering.startswith('3.2'):
                # 进一步检查是否为3.2的直接子章节
                if self._is_3_2_subsection(numbering):
                    filtered.append(heading)
                    if self.debug_mode:
                        print(f"    ✓ 保留3.2子章节: {numbering} {heading['title']}")
                else:
                    if self.debug_mode:
                        print(f"    ❌ 跳过非3.2子章节: {numbering}")
        
        return filtered
    
    def _is_3_2_subsection(self, numbering: str) -> bool:
        """判断是否为3.2的子章节"""
        
        # 3.2本身
        if numbering == '3.2':
            return True
        
        # 3.2.x 格式（x可以是多级）
        if re.match(r'^3\.2\.\d+', numbering):
            return True
        
        return False
    
    def _format_extraction_result(self, headings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """格式化提取结果"""
        
        # 统计级别分布
        level_distribution = {}
        for heading in headings:
            level = heading['level']
            level_distribution[level] = level_distribution.get(level, 0) + 1
        
        return {
            'success': True,
            'message': f'成功提取 {len(headings)} 个3.2子章节标题',
            'total_count': len(headings),
            'catalog_items': headings,
            'level_distribution': level_distribution,
            'extraction_type': 'standardized_document',
            'filter_applied': '3.2_subsections_only'
        }


def extract_3_2_requirements_from_standardized_docx(docx_path: str, debug_mode: bool = False) -> Dict[str, Any]:
    """
    从标准化DOCX文档提取3.2子章节的测试需求
    
    Args:
        docx_path: 标准化DOCX文件路径
        debug_mode: 是否启用调试模式
        
    Returns:
        包含3.2子章节信息的字典
    """
    
    try:
        extractor = StandardizedCatalogExtractor(debug_mode)
        return extractor.extract_catalog_from_standardized_docx(docx_path)
    except Exception as e:
        return {
            'success': False,
            'message': f'从标准化文档提取3.2需求失败: {str(e)}',
            'total_count': 0,
            'catalog_items': [],
            'extraction_type': 'standardized_document',
            'error': str(e)
        } 