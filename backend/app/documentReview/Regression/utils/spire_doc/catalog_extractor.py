#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
目录提取器 - 核心模块

基于直接XML解析的重构实现：
1. 直接解析 DOCX 内部 XML 结构
2. 获取真正的 Word 自动编号
3. 准确识别文档层级关系
4. 彻底解决编号识别问题
"""

import os
import zipfile
from typing import Dict, List, Optional, Any
from pathlib import Path

from .xml_parser import DocxXmlParser
from .text_filters import TextFilter
from .numbering_utils import NumberingManager, HeadingGenerator


class SpireCatalogExtractor:
    """Spire.Doc 目录提取器 - 重构版"""
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        
        # 初始化组件
        self.xml_parser = DocxXmlParser(debug_mode)
        self.text_filter = TextFilter(debug_mode)
        self.numbering_manager = NumberingManager(debug_mode)
        self.heading_generator = HeadingGenerator(self.numbering_manager, debug_mode)
        
        # 解析结果缓存
        self.numbering_defs = {}
        self.style_defs = {}
        self.paragraphs = []
    
    def _debug_print(self, message: str, category: str = "DEBUG"):
        """调试输出"""
        if self.debug_mode:
            print(f"[{category}] {message}")
    
    def extract_catalog_from_docx(self, docx_path: str) -> Dict[str, Any]:
        """
        从DOCX文件提取目录结构
        
        Args:
            docx_path: DOCX文件路径
            
        Returns:
            包含标题列表和统计信息的字典
        """
        
        if not Path(docx_path).exists():
            raise FileNotFoundError(f"文档不存在: {docx_path}")
        
        self._debug_print(f"开始提取目录: {docx_path}", "INIT")
        
        try:
            with zipfile.ZipFile(docx_path, 'r') as docx_zip:
                # 1. 解析 XML 结构
                self._parse_xml_files(docx_zip)
                
                # 2. 生成结构化标题
                headings = self._generate_structured_headings()
                
                # 3. 格式化结果
                result = self._format_extraction_result(headings)
                
                self._debug_print(f"提取完成，识别到 {len(headings)} 个标题", "RESULT")
                return result
                
        except Exception as e:
            self._debug_print(f"提取失败: {e}", "ERROR")
            raise
    
    def _parse_xml_files(self, docx_zip: zipfile.ZipFile):
        """解析所有XML文件"""
        
        # 解析编号定义
        self.numbering_defs = self.xml_parser.parse_numbering_xml(docx_zip)
        
        # 解析样式定义
        self.style_defs = self.xml_parser.parse_styles_xml(docx_zip)
        
        # 解析文档内容
        self.paragraphs = self.xml_parser.parse_document_xml(docx_zip)
    
    def _generate_structured_headings(self) -> List[Dict[str, Any]]:
        """生成结构化标题列表"""
        
        headings = []
        
        for para in self.paragraphs:
            heading_info = self._analyze_paragraph_for_heading(para)
            if heading_info:
                headings.append(heading_info)
                self.numbering_manager.update_context(heading_info)
        
        return headings
    
    def _analyze_paragraph_for_heading(self, para: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """分析段落是否为标题"""
        
        text = para['text']
        num_id = para['num_id']
        ilvl = para['ilvl']
        style_id = para['style_id']
        outline_level = para['outline_level']
        
        # 排除明显不是标题的内容
        if self.text_filter.should_exclude_text(text, self.numbering_manager.current_context):
            return None
        
        # 1. 检查自动编号（最高优先级）
        if num_id and num_id in self.numbering_defs and ilvl is not None:
            return self.heading_generator.create_auto_numbered_heading(
                para, self.numbering_defs, num_id, ilvl
            )
        
        # 2. 检查标题样式
        if style_id and style_id in self.style_defs:
            style_info = self.style_defs[style_id]
            if style_info['is_heading']:
                result = self.heading_generator.create_style_heading(para, style_info)
                if result is None:  # 如果被拒绝，直接返回None
                    self._debug_print(f"样式标题被拒绝: {text[:50]}", "REJECT")
                    return None
                return result
        
        # 3. 检查手动编号
        manual_result = self._analyze_manual_numbering(para)
        if manual_result:
            return manual_result
        
        # 4. 基于大纲级别
        if outline_level is not None:
            return self.heading_generator.create_outline_heading(para, outline_level)
        
        return None
    
    def _analyze_manual_numbering(self, para: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """分析手动编号"""
        
        text = para['text']
        
        # 提取手动编号
        manual_numbering, clean_text = self.text_filter.extract_manual_numbering(text)
        if not manual_numbering:
            return None
        
        # 确定级别
        level = self.text_filter.determine_manual_numbering_level(
            manual_numbering, text, self.numbering_manager.current_context
        )
        
        # 如果级别是-1，表示拒绝
        if level == -1:
            self._debug_print(f"手动编号被拒绝: {text[:50]}", "REJECT")
            return None
        
        return self.heading_generator.create_manual_numbered_heading(
            para, manual_numbering, clean_text, level
        )
    
    def _format_extraction_result(self, headings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """格式化提取结果"""
        
        # 统计信息
        total_count = len(headings)
        auto_numbered_count = sum(1 for h in headings if h.get('is_auto_numbered', False))
        manual_numbered_count = total_count - auto_numbered_count
        
        # 级别统计
        level_stats = {}
        for heading in headings:
            level = heading['level']
            level_stats[level] = level_stats.get(level, 0) + 1
        
        # 转换为原格式兼容
        catalog_items = []
        for heading in headings:
            catalog_items.append({
                'level': heading['level'],
                'numbering': heading['numbering'],
                'title': heading['title'],
                'full_text': heading['full_text'],
                'style_name': heading.get('style_name', ''),
                'is_auto_numbered': heading.get('is_auto_numbered', False)
            })
        
        return {
            'success': True,
            'catalog_items': catalog_items,
            'total_count': total_count,
            'auto_numbered_count': auto_numbered_count,
            'manual_numbered_count': manual_numbered_count,
            'level_distribution': level_stats,
            'message': f"成功识别 {total_count} 个标题（自动编号: {auto_numbered_count}, 手动编号: {manual_numbered_count}）"
        }


def extract_catalog_with_spire(docx_path: str, debug_mode: bool = False) -> Dict[str, Any]:
    """
    使用Spire.Doc提取DOCX文档目录（完整版）
    
    Args:
        docx_path: DOCX文件路径
        debug_mode: 是否启用调试模式
        
    Returns:
        包含目录信息的字典
    """
    
    try:
        extractor = SpireCatalogExtractor(debug_mode)
        return extractor.extract_catalog_from_docx(docx_path)
    except Exception as e:
        return {
            'success': False,
            'message': f'目录提取失败: {str(e)}',
            'total_count': 0,
            'catalog_items': []
        } 