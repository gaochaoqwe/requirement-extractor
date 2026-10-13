#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
需求位置缓存管理器

用于管理需求在Word文档中的精确位置信息，
实现快速定位和内容提取的性能优化。
"""

import hashlib
import os
from typing import Dict, List, Optional, Any
from pathlib import Path

from ..db.optimized_models import OptimizedDynamicTestDatabase

# 尝试导入 catalog_extractor
try:
    from .spire_doc.catalog_extractor import SpireCatalogExtractor
except ImportError:
    try:
        from .spire_doc_backup.catalog_extractor import SpireCatalogExtractor
    except ImportError:
        # 如果都导入失败，创建一个简单的替代类
        class SpireCatalogExtractor:
            def __init__(self, debug_mode=False):
                self.debug_mode = debug_mode
            
            def extract_catalog(self, *args, **kwargs):
                return {"items": [], "total": 0}


class RequirementPositionCacheManager:
    """需求位置缓存管理器"""
    
    def __init__(self, db_path: str = None, debug_mode: bool = False):
        self.db = OptimizedDynamicTestDatabase(db_path)
        self.debug_mode = debug_mode
        self.catalog_extractor = SpireCatalogExtractor(debug_mode=debug_mode)
    
    def _debug_print(self, message: str, category: str = "POSITION_CACHE"):
        """调试输出"""
        if self.debug_mode:
            print(f"[{category}] {message}")
    
    def calculate_document_hash(self, document_path: str) -> str:
        """计算文档的MD5哈希值"""
        try:
            with open(document_path, 'rb') as f:
                content = f.read()
                return hashlib.md5(content).hexdigest()
        except Exception as e:
            self._debug_print(f"计算文档哈希失败: {e}", "ERROR")
            return ""
    
    def cache_requirement_positions(self, session_id: str, document_path: str, 
                                   requirement_names: List[str]) -> bool:
        """
        缓存需求位置信息
        
        Args:
            session_id: 会话ID
            document_path: 需求规格说明文档路径
            requirement_names: 需求名称列表（来自用户确认的目录）
        
        Returns:
            是否成功缓存
        """
        try:
            # 检查文档是否存在
            if not os.path.exists(document_path):
                self._debug_print(f"文档不存在: {document_path}", "ERROR")
                return False
            
            # 计算文档哈希
            document_hash = self.calculate_document_hash(document_path)
            if not document_hash:
                return False
            
            # 检查是否已缓存
            if self.db.is_document_positions_cached(session_id, document_path, document_hash):
                self._debug_print(f"位置信息已缓存: {document_path}", "INFO")
                return True
            
            # 清除旧的缓存（如果文档已变更）
            self.db.clear_requirement_positions(session_id, document_path)
            
            # 提取文档结构和位置信息
            self._debug_print(f"开始提取位置信息: {document_path}", "INFO")
            extraction_result = self.catalog_extractor.extract_catalog_from_docx(document_path)
            
            if not extraction_result.get('success'):
                self._debug_print(f"文档结构提取失败", "ERROR")
                return False
            
            # 获取所有标题段落的位置信息
            headings = extraction_result.get('headings', [])
            
            # 为每个需求名称查找对应的位置信息
            cached_count = 0
            for req_name in requirement_names:
                position_info = self._find_requirement_position(req_name, headings)
                
                if position_info:
                    # 保存位置信息到数据库
                    position_data = {
                        'requirement_name': req_name,
                        'chapter_number': position_info.get('numbering', ''),
                        'paragraph_index': position_info.get('paragraph_index'),
                        'char_start_offset': position_info.get('char_start_offset'),
                        'char_end_offset': position_info.get('char_end_offset'),
                        'heading_text': position_info.get('text', ''),
                        'content_preview': position_info.get('text', '')[:100],
                        'num_id': position_info.get('num_id'),
                        'ilvl': position_info.get('ilvl'),
                        'style_id': position_info.get('style_id'),
                        'outline_level': position_info.get('outline_level'),
                        'extraction_metadata': {
                            'confidence_score': position_info.get('confidence_score', 0.0),
                            'match_method': position_info.get('match_method', 'unknown'),
                            'heading_level': position_info.get('level', 0)
                        }
                    }
                    
                    if self.db.save_requirement_position(session_id, document_path, 
                                                        document_hash, position_data):
                        cached_count += 1
                        self._debug_print(f"已缓存位置信息: {req_name}", "SUCCESS")
                    else:
                        self._debug_print(f"位置信息缓存失败: {req_name}", "ERROR")
                else:
                    self._debug_print(f"未找到位置信息: {req_name}", "WARNING")
            
            self._debug_print(f"位置信息缓存完成: {cached_count}/{len(requirement_names)}", "INFO")
            return cached_count > 0
            
        except Exception as e:
            self._debug_print(f"缓存位置信息异常: {e}", "ERROR")
            return False
    
    def _find_requirement_position(self, req_name: str, headings: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        在标题列表中查找需求的位置信息
        
        Args:
            req_name: 需求名称
            headings: 文档标题列表
        
        Returns:
            位置信息字典或None
        """
        # 尝试精确匹配（包括带章节编号的标题）
        for heading in headings:
            heading_text = heading.get('text', '')
            
            # 1. 直接完全匹配
            if req_name == heading_text:
                self._debug_print(f"完全匹配找到: {req_name} -> {heading_text}", "MATCH")
                return {**heading, 'match_method': 'exact_match', 'confidence_score': 1.0}
            
            # 2. 标题结尾匹配（如"3.2.1 用户身份验证功能" 匹配 "用户身份验证功能"）
            if heading_text.endswith(req_name):
                self._debug_print(f"结尾匹配找到: {req_name} -> {heading_text}", "MATCH")
                return {**heading, 'match_method': 'ending_match', 'confidence_score': 0.9}
        
        # 尝试包含匹配（双向）
        for heading in headings:
            heading_text = heading.get('text', '')
            
            # 3. 需求名称包含在标题中
            if req_name in heading_text:
                self._debug_print(f"包含匹配找到: {req_name} -> {heading_text}", "MATCH")
                return {**heading, 'match_method': 'contains_match', 'confidence_score': 0.8}
            
            # 4. 标题包含在需求名称中（反向匹配）
            if heading_text in req_name:
                self._debug_print(f"反向包含匹配找到: {req_name} -> {heading_text}", "MATCH")
                return {**heading, 'match_method': 'reverse_contains_match', 'confidence_score': 0.7}
        
        # 尝试关键词匹配（去除"功能"后缀）
        req_keywords = req_name.replace('功能', '').strip()
        if req_keywords and len(req_keywords) > 2:  # 关键词长度至少3个字符
            for heading in headings:
                heading_text = heading.get('text', '')
                if req_keywords in heading_text:
                    self._debug_print(f"关键词匹配找到: {req_name} ({req_keywords}) -> {heading_text}", "MATCH")
                    return {**heading, 'match_method': 'keyword_match', 'confidence_score': 0.6}
        
        # 尝试模糊匹配（基于字符重叠度）
        for heading in headings:
            heading_text = heading.get('text', '')
            
            # 计算字符重叠度
            overlap_score = self._calculate_text_overlap(req_name, heading_text)
            if overlap_score > 0.7:  # 70%以上重叠
                self._debug_print(f"模糊匹配找到: {req_name} -> {heading_text} (重叠度: {overlap_score:.2f})", "MATCH")
                return {**heading, 'match_method': 'fuzzy_match', 'confidence_score': overlap_score * 0.5}
        
        return None
    
    def _calculate_text_overlap(self, text1: str, text2: str) -> float:
        """
        计算两个文本的字符重叠度
        
        Args:
            text1: 第一个文本
            text2: 第二个文本
            
        Returns:
            重叠度 (0.0 - 1.0)
        """
        if not text1 or not text2:
            return 0.0
        
        # 移除空格和标点符号
        clean_text1 = ''.join(c for c in text1 if c.isalnum())
        clean_text2 = ''.join(c for c in text2 if c.isalnum())
        
        if not clean_text1 or not clean_text2:
            return 0.0
        
        # 计算共同字符数
        common_chars = set(clean_text1) & set(clean_text2)
        
        # 计算重叠度
        max_len = max(len(clean_text1), len(clean_text2))
        overlap_ratio = len(common_chars) / max_len if max_len > 0 else 0.0
        
        return overlap_ratio
    
    def get_requirement_position(self, session_id: str, requirement_name: str) -> Optional[Dict[str, Any]]:
        """
        获取需求的位置信息
        
        Args:
            session_id: 会话ID
            requirement_name: 需求名称
        
        Returns:
            位置信息字典或None
        """
        return self.db.get_requirement_position_by_name(session_id, requirement_name)
    
    def get_all_cached_positions(self, session_id: str, document_path: str = None) -> List[Dict[str, Any]]:
        """
        获取所有缓存的位置信息
        
        Args:
            session_id: 会话ID  
            document_path: 可选的文档路径过滤
        
        Returns:
            位置信息列表
        """
        return self.db.get_requirement_positions(session_id, document_path)
    
    def is_positions_cached(self, session_id: str, document_path: str) -> bool:
        """
        检查位置信息是否已缓存
        
        Args:
            session_id: 会话ID
            document_path: 文档路径
        
        Returns:
            是否已缓存
        """
        document_hash = self.calculate_document_hash(document_path)
        if not document_hash:
            return False
        
        return self.db.is_document_positions_cached(session_id, document_path, document_hash)
    
    def clear_cache(self, session_id: str, document_path: str = None) -> bool:
        """
        清除位置信息缓存
        
        Args:
            session_id: 会话ID
            document_path: 可选的文档路径
        
        Returns:
            是否成功清除
        """
        return self.db.clear_requirement_positions(session_id, document_path)
    
    def extract_content_by_position(self, document_path: str, position_info: Dict[str, Any], 
                                   content_lines: int = 20) -> str:
        """
        根据位置信息快速提取需求内容
        
        Args:
            document_path: 文档路径
            position_info: 位置信息
            content_lines: 要提取的内容行数
        
        Returns:
            提取的内容文本
        """
        try:
            from docx import Document
            
            # 使用python-docx读取文档
            doc = Document(document_path)
            paragraphs = [p.text for p in doc.paragraphs]
            
            # 获取起始位置
            start_index = position_info.get('paragraph_index', 0)
            
            # 提取指定行数的内容
            end_index = min(start_index + content_lines, len(paragraphs))
            content_paragraphs = paragraphs[start_index:end_index]
            
            # 组合内容
            content = '\n'.join(content_paragraphs).strip()
            
            self._debug_print(f"快速提取内容成功: {len(content)} 字符", "SUCCESS")
            return content
            
        except Exception as e:
            self._debug_print(f"快速提取内容失败: {e}", "ERROR")
            return ""


# 全局实例（单例模式）
_position_cache_manager = None

def get_position_cache_manager(debug_mode: bool = False) -> RequirementPositionCacheManager:
    """获取位置缓存管理器实例（单例）"""
    global _position_cache_manager
    if _position_cache_manager is None:
        _position_cache_manager = RequirementPositionCacheManager(debug_mode=debug_mode)
    return _position_cache_manager 