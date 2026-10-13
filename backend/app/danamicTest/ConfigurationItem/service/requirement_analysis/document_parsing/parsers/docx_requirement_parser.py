#!/usr/bin/env python3
"""
DOCX需求解析器（主协调器）
基于DOCX库的需求规格说明文档解析和处理主接口

功能说明：
1. 作为对外的主要API接口
2. 协调各个专门模块的工作
3. 管理增强功能（Spire.Doc）的集成
4. 提供向后兼容的接口

模块架构：
- DocumentTextAnalyzer: 文档文本分析
- RequirementContentProcessor: 需求内容处理  
- DebugLogger: 调试日志记录
- SpireRequirementExtractor: Spire.Doc增强功能
"""

import os
import re
from typing import Dict, List, Optional, Tuple
from docx import Document
from pathlib import Path

# 导入spire.doc模块
try:
    from app.danamicTest.ConfigurationItem.utils.spire_doc import (
        extract_catalog_with_spire, 
        extract_testing_requirements_with_spire,
        SpireCatalogExtractor
    )
    SPIRE_DOC_AVAILABLE = True
except ImportError as e:
    SPIRE_DOC_AVAILABLE = False
    print(f"Warning: spire.doc module not available: {e}")

# 检查增强版匹配器是否可用
try:
    # 尝试导入SpireRequirementExtractor来检查是否可用
    from .spire_requirement_extractor import SpireRequirementExtractor
    ENHANCED_MATCHER_AVAILABLE = True
except ImportError:
    ENHANCED_MATCHER_AVAILABLE = False

# 导入日志工具
try:
    from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_debug, log_warning
except ImportError:
    try:
        from .....utils.logging_utils.logger import log_info, log_error, log_debug, log_warning
    except ImportError:
        try:
            from .....utils.logging_utils.logger import log_info, log_error, log_debug, log_warning
        except ImportError:
            # 作为后备，使用print语句
            def log_info(msg, tag=""): print(f"INFO [{tag}] {msg}")
            def log_error(msg, tag=""): print(f"ERROR [{tag}] {msg}")
            def log_debug(msg, tag=""): print(f"DEBUG [{tag}] {msg}")
            def log_warning(msg, tag=""): print(f"WARNING [{tag}] {msg}")

# 导入新创建的模块
from ..analyzers.document_text_analyzer import document_analyzer
from ..processors.requirement_content_processor import requirement_processor  
from ..utils.debug_logger import debug_logger


class DocxRequirementParser:
    """DOCX需求解析器（主协调器）"""
    
    def __init__(self):
        """初始化解析器"""
        # 初始化增强版匹配器（如果可用）
        self.enhanced_matcher = None
        if ENHANCED_MATCHER_AVAILABLE:
            try:
                self.enhanced_matcher = SpireRequirementExtractor()
                # log_info("Spire.Doc增强匹配器初始化成功", "docx_requirement_parser")
            except Exception as e:
                # log_warning(f"Spire.Doc增强匹配器初始化失败: {e}", "docx_requirement_parser")
                self.enhanced_matcher = None
        
    def find_requirement_content(self, requirement_file_path: str, requirement_names: List[str],
                                   session_id: str = None, catalog_dict: Dict[str, str] = None) -> Dict[str, Dict]:
        """
        查找需求内容 (使用多种策略)
        
        优先级顺序：
        1. 标准化文档 (最高优先级)
        2. 位置缓存快速提取
        3. 智能章节内容提取器 (新增)
        4. Spire.Doc增强匹配
        5. 传统DOCX解析 (兜底)
        """
        # log_info(f"开始查找需求内容，共 {len(requirement_names)} 个需求", "docx_requirement_parser")
        # log_debug(f"需求列表: {requirement_names}", "docx_requirement_parser")

        # 🌟 最高优先级：尝试使用标准化文档进行匹配
        standardized_doc_path = self._check_for_standardized_document(requirement_file_path)
        if standardized_doc_path:
            # log_info(f"发现标准化文档，优先使用: {standardized_doc_path}", "docx_requirement_parser")
            try:
                # 使用标准化文档进行传统DOCX解析（因为标题已经带编号，匹配准确率极高）
                standardized_results = self._find_requirement_content_traditional(
                    standardized_doc_path, requirement_names, catalog_dict
                )
                if standardized_results and len(standardized_results) > 0:
                    # log_info(f"标准化文档匹配成功，获得 {len(standardized_results)} 个需求", "docx_requirement_parser")
                    return standardized_results
            except Exception as std_error:
                # log_error(f"标准化文档处理异常: {std_error}, 回退到常规方法", "docx_requirement_parser")
                pass
        
        # 🚀 新增：尝试使用位置缓存快速提取（第二优先级）
        if session_id:
            try:
                from ....utils.position_cache_manager import get_position_cache_manager
                position_manager = get_position_cache_manager(debug_mode=False) # 关闭debug减少日志
                if position_manager.is_positions_cached(session_id, requirement_file_path):
                    # log_info("发现位置缓存，尝试快速提取内容", "docx_requirement_parser")
                    cached_results = self._extract_content_using_position_cache(
                        session_id, requirement_file_path, requirement_names, position_manager, catalog_dict
                    )
                    if cached_results and len(cached_results) > 0:
                        # log_info(f"位置缓存快速提取成功，获得 {len(cached_results)} 个需求", "docx_requirement_parser")
                        return cached_results
            except Exception as cache_error:
                # log_error(f"位置缓存处理异常: {cache_error}, 回退到常规方法", "docx_requirement_parser")

                pass
        # 🆕 新增：尝试使用智能章节内容提取器（第三优先级）
        try:
            from .chapter_content_extractor import ChapterContentExtractor
            
            # log_info("尝试使用智能章节内容提取器", "docx_requirement_parser")
            
            # 读取文档内容
            from docx import Document
            doc = Document(requirement_file_path)
            document_lines = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    document_lines.append(paragraph.text.strip())
            
            if document_lines:
                extractor = ChapterContentExtractor(debug_mode=False) # 关闭debug减少日志
                chapter_results = extractor.extract_requirement_content(
                    document_lines, requirement_names
                )
                
                # 检查提取结果质量
                valid_results = {
                    name: content for name, content in chapter_results.items()
                    if content.get('content') and len(content.get('content', '').strip()) > 10
                }
                
                if valid_results and len(valid_results) > 0:
                    # log_info(f"智能章节内容提取成功，获得 {len(valid_results)} 个有效需求", "docx_requirement_parser")
                    return valid_results
            else:
                    # log_info("智能章节内容提取结果质量不足，继续尝试其他方法", "docx_requirement_parser")
            
                pass
        except Exception as chapter_error:
            # log_error(f"智能章节内容提取异常: {chapter_error}, 继续尝试其他方法", "docx_requirement_parser")
        
            pass
        # 尝试使用增强版匹配器（如果可用且需求包含章节编号）
        if self.enhanced_matcher and requirement_processor._has_numbering_in_requirements(requirement_names):
            # log_info("尝试使用Spire.Doc增强匹配器", "docx_requirement_parser")
            try:
                enhanced_results = self.enhanced_matcher.extract_requirement_content(
                    requirement_file_path, requirement_names
                )
                if enhanced_results and len(enhanced_results) > 0:
                    # log_info(f"增强版匹配器成功，获得 {len(enhanced_results)} 个需求", "docx_requirement_parser")
                    return enhanced_results
            except Exception as enhanced_error:
                # log_error(f"增强版匹配器异常: {enhanced_error}, 回退到传统方法", "docx_requirement_parser")

                pass
        # 使用传统DOCX方法
        # log_info("使用传统DOCX解析方法", "docx_requirement_parser")
        return self._find_requirement_content_traditional(requirement_file_path, requirement_names, catalog_dict)
    
    def _find_requirement_content_traditional(self, requirement_file_path: str, requirement_names: List[str], catalog_dict: Dict[str, str] = None) -> Dict[str, Dict]:
        """
        使用传统方法查找需求内容（基于python-docx库）
        
        Args:
            requirement_file_path: 需求规格说明文档路径
            requirement_names: 需求名称列表
            catalog_dict: 章节编号字典 {需求名称: 章节编号}
            
        Returns:
            需求详细信息字典
        """
        try:
            # 读取Word文档内容
            doc = Document(requirement_file_path)
            full_text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
            
            # 调试日志记录
            debug_logger.log_requirement_spec_content(requirement_file_path, full_text)
            
            # 使用文档分析器分割章节
            sections = document_analyzer.split_document_by_headings(full_text)
            debug_logger.log_section_analysis(sections)
            
            # 使用内容处理器匹配需求
            requirement_details = {}
            matched_count = 0
            
            for req_name in requirement_names:
                req_info = requirement_processor.find_requirement_in_sections(sections, req_name)
                
                # 🔧 修复：添加章节编号信息到需求信息中
                if catalog_dict and req_name in catalog_dict:
                    req_info['chapter_number'] = catalog_dict[req_name]
                    # log_debug(f"为需求 '{req_name}' 添加章节编号: {catalog_dict[req_name]}", "docx_requirement_parser")
                else:
                    req_info['chapter_number'] = ''
                    # log_debug(f"需求 '{req_name}' 未找到章节编号", "docx_requirement_parser")
                
                requirement_details[req_name] = req_info
                
                # 检查是否找到有效内容（不是默认值）
                found = any(value and value != f'验证{req_name}的功能实现' for value in req_info.values())
                if found:
                    matched_count += 1
                
                debug_logger.log_requirement_matching_result(req_name, found, req_info)
            
            # 记录处理摘要
            debug_logger.log_processing_summary(requirement_file_path, len(sections), matched_count)
            
            # log_info(f"传统方法处理完成，匹配 {matched_count}/{len(requirement_names)} 个需求", "docx_requirement_parser")
            return requirement_details
            
        except Exception as e:
            # log_error(f"传统方法处理失败: {e}", "docx_requirement_parser", e)
            # 返回默认信息，包含章节编号
            default_details = {}
            for req_name in requirement_names:
                req_info = requirement_processor._create_default_requirement_info(req_name)
                # 🔧 修复：为默认信息也添加章节编号
                if catalog_dict and req_name in catalog_dict:
                    req_info['chapter_number'] = catalog_dict[req_name]
                else:
                    req_info['chapter_number'] = ''
                default_details[req_name] = req_info
            return default_details
    
    def parse_catalog_document(self, catalog_file_path: str) -> Dict[str, str]:
        """
        解析需求目录文档，提取需求项目列表
        
        Args:
            catalog_file_path: 目录文档路径
            
        Returns:
            需求项目字典 {需求名称: 章节编号}
        """
        if not os.path.exists(catalog_file_path):
            # log_error(f"目录文档不存在: {catalog_file_path}", "docx_requirement_parser")
            return {}
            
        try:
            # log_info(f"解析目录文档: {catalog_file_path}", "docx_requirement_parser")
            
            # 读取文档内容
            if catalog_file_path.endswith('.docx'):
                doc = Document(catalog_file_path)
                content = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
            else:
                # 假设是txt文件
                with open(catalog_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            debug_logger.log_catalog_content(catalog_file_path, content)
            
            # 使用文档分析器提取章节信息
            catalog_dict = {}
            lines = content.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 跳过目录行（调用公共方法）
                if document_analyzer.is_likely_heading(line) and hasattr(document_analyzer, '_is_table_of_contents_line'):
                    # 直接访问私有方法进行目录行检测
                    if document_analyzer._is_table_of_contents_line(line):
                        continue
                
                # 提取章节编号和标题
                numbering, title, level = document_analyzer.extract_chapter_number(line)
                if numbering and title:
                    catalog_dict[title] = numbering
                    # log_debug(f"提取目录项: {numbering} - {title}", "docx_requirement_parser")
            
            # log_info(f"目录解析完成，提取 {len(catalog_dict)} 个需求项", "docx_requirement_parser")
            return catalog_dict
            
        except Exception as e:
            # log_error(f"解析目录文档失败: {e}", "docx_requirement_parser", e)
            return {}
        
    def generate_requirements_from_spec(self, catalog_file_path: str, requirement_file_path: str, 
                                       session_id: str = None) -> Dict[str, str]:
        """
        从规格说明生成需求列表（组合API方法）
        
        Args:
            catalog_file_path: 目录文档路径
            requirement_file_path: 需求规格说明文档路径
            
        Returns:
            生成的需求字典
        """
        # log_info("开始从规格说明生成需求列表", "docx_requirement_parser")
        
        try:
            # 解析目录文档
            catalog_dict = self.parse_catalog_document(catalog_file_path)
            if not catalog_dict:
                # log_warning("目录解析失败或为空，无法生成需求列表", "docx_requirement_parser")
                return {}
                
            # 获取需求名称列表
            requirement_names = list(catalog_dict.keys())
            
            # 🔧 修复：查找需求详细内容时传递章节编号信息
            requirement_details = self.find_requirement_content(requirement_file_path, requirement_names, session_id, catalog_dict)
            
            # log_info(f"需求列表生成完成，共 {len(requirement_details)} 个需求", "docx_requirement_parser")
            return requirement_details
            
        except Exception as e:
            # log_error(f"从规格说明生成需求列表失败: {e}", "docx_requirement_parser", e)
            return {}
    
    # 向后兼容的方法别名
    def is_likely_heading(self, paragraph: str) -> bool:
        """标题识别（委托给文档分析器）"""
        return document_analyzer.is_likely_heading(paragraph)
    
    def split_document_by_headings(self, text: str) -> List[Dict[str, str]]:
        """文档章节分割（委托给文档分析器）"""
        return document_analyzer.split_document_by_headings(text)
    
    def extract_chapter_number(self, text: str) -> Tuple[str, str, int]:
        """章节编号提取（委托给文档分析器）"""
        return document_analyzer.extract_chapter_number(text)
    
    def _parse_requirement_name(self, requirement_name: str) -> Tuple[str, str]:
        """需求名称解析（委托给内容处理器）"""
        return requirement_processor._parse_requirement_name(requirement_name)
    
    def _extract_requirement_sections_from_content(self, content: str, req_name: str) -> Dict[str, str]:
        """需求段落提取（委托给内容处理器）"""
        return requirement_processor._extract_requirement_sections_from_content(content, req_name)
    
    def _extract_content_using_position_cache(self, session_id: str, requirement_file_path: str, 
                                            requirement_names: List[str], position_manager, catalog_dict: Dict[str, str] = None) -> Dict[str, Dict]:
        """
        使用位置缓存快速提取需求内容
        
        Args:
            session_id: 会话ID
            requirement_file_path: 需求文档路径
            requirement_names: 需求名称列表
            position_manager: 位置缓存管理器
            catalog_dict: 章节编号字典 {需求名称: 章节编号}
            
        Returns:
            需求详细信息字典
        """
        requirement_details = {}
        cache_hit_count = 0
        
        try:
            from docx import Document
            
            # 读取文档（只需要读一次）
            doc = Document(requirement_file_path)
            all_paragraphs = [p.text for p in doc.paragraphs]
            
            # log_info(f"文档加载完成，共 {len(all_paragraphs)} 个段落", "docx_requirement_parser")
            
            for req_name in requirement_names:
                # 从缓存获取位置信息
                position_info = position_manager.get_requirement_position(session_id, req_name)
                
                if position_info:
                    cache_hit_count += 1
                    
                    # 使用位置信息快速定位内容
                    paragraph_index = position_info.get('paragraph_index', 0)
                    confidence_score = position_info.get('extraction_metadata', {}).get('confidence_score', 0.0)
                    
                    # log_debug(f"位置缓存命中: {req_name}, 段落索引: {paragraph_index}, 置信度: {confidence_score}", "docx_requirement_parser")
                    
                    # 提取需求内容（从标题开始的后续20个段落）
                    content_lines = 20
                    end_index = min(paragraph_index + content_lines, len(all_paragraphs))
                    
                    if paragraph_index < len(all_paragraphs):
                        content_paragraphs = all_paragraphs[paragraph_index:end_index]
                        full_content = '\n'.join(content_paragraphs).strip()
                        
                        # 使用内容处理器解析结构化内容
                        parsed_content = requirement_processor._extract_requirement_sections_from_content(full_content, req_name)
                        
                        if parsed_content and any(v.strip() for v in parsed_content.values()):
                            # 🔧 修复：添加章节编号信息
                            if catalog_dict and req_name in catalog_dict:
                                parsed_content['chapter_number'] = catalog_dict[req_name]
                            else:
                                parsed_content['chapter_number'] = ''
                            requirement_details[req_name] = parsed_content
                            # log_info(f"位置缓存成功提取内容: {req_name}", "docx_requirement_parser")
                        else:
                            # 回退到默认内容，但标记为低置信度
                            default_info = requirement_processor._create_default_requirement_info(req_name)
                            # 🔧 修复：为默认信息添加章节编号
                            if catalog_dict and req_name in catalog_dict:
                                default_info['chapter_number'] = catalog_dict[req_name]
                            else:
                                default_info['chapter_number'] = ''
                            requirement_details[req_name] = default_info
                            # log_warning(f"位置缓存提取内容为空，使用默认内容: {req_name}", "docx_requirement_parser")
                    else:
                        # 段落索引超出范围
                        default_info = requirement_processor._create_default_requirement_info(req_name)
                        # 🔧 修复：为默认信息添加章节编号
                        if catalog_dict and req_name in catalog_dict:
                            default_info['chapter_number'] = catalog_dict[req_name]
                        else:
                            default_info['chapter_number'] = ''
                        requirement_details[req_name] = default_info
                        # log_warning(f"位置缓存段落索引超出范围: {req_name} (索引: {paragraph_index})", "docx_requirement_parser")
                else:
                    # 没有位置缓存，使用默认值
                    default_info = requirement_processor._create_default_requirement_info(req_name)
                    # 🔧 修复：为默认信息添加章节编号
                    if catalog_dict and req_name in catalog_dict:
                        default_info['chapter_number'] = catalog_dict[req_name]
                    else:
                        default_info['chapter_number'] = ''
                    requirement_details[req_name] = default_info
                    # log_debug(f"无位置缓存: {req_name}", "docx_requirement_parser")
            
            # log_info(f"位置缓存处理完成: {cache_hit_count}/{len(requirement_names)} 命中", "docx_requirement_parser")
            return requirement_details
            
        except Exception as e:
            # log_error(f"位置缓存内容提取异常: {e}", "docx_requirement_parser")
            return {}
            
    def _check_for_standardized_document(self, original_doc_path: str) -> Optional[str]:
        """
        检查是否存在标准化版本的文档（使用标准化管理器）
        
        Args:
            original_doc_path: 原始文档路径
            
        Returns:
            标准化文档路径（如果存在），否则返回None
        """
        try:
            # 🚀 使用标准化管理器
            from ...utils.standardization_manager import get_standardization_manager
            standardization_manager = get_standardization_manager()
            
            # 从路径中提取session_id
            from pathlib import Path
            original_path = Path(original_doc_path)
            
            # 尝试从路径中提取session_id
            session_id = None
            path_parts = original_path.parts
            for i, part in enumerate(path_parts):
                if part == "configuration" and i + 1 < len(path_parts):
                    session_id = path_parts[i + 1]
                    break
            
            if session_id:
                # 使用标准化管理器查找标准化文档
                standardized_path = standardization_manager.get_standardized_document_path(
                    session_id, original_doc_path
                )
                if standardized_path:
                    # log_info(f"找到标准化文档: {standardized_path}", "docx_requirement_parser")
                    return standardized_path
            
            # 回退到原有逻辑（兼容性）
            possible_paths = [
                # 1. 同目录下的 standardized_ 前缀版本
                original_path.parent / f"standardized_{original_path.name}",
                
                # 2. 同目录下的 _standardized 后缀版本  
                original_path.parent / f"{original_path.stem}_standardized{original_path.suffix}",
                
                # 3. 同名但在 standardized 子目录下
                original_path.parent / "standardized" / original_path.name
            ]
            
            for possible_path in possible_paths:
                if possible_path.exists():
                    # log_info(f"找到标准化文档: {possible_path}", "docx_requirement_parser")
                    return str(possible_path)
            
            # 没有找到标准化文档
            # log_debug(f"未找到标准化文档，使用原始文档: {original_doc_path}", "docx_requirement_parser")
            return None
            
        except Exception as e:
            # log_error(f"检查标准化文档时发生异常: {e}", "docx_requirement_parser")
            return None


# 为了向后兼容，保持原有的类名
RequirementSpecMatcher = DocxRequirementParser

# 创建全局实例（向后兼容）
requirement_spec_matcher = DocxRequirementParser() 