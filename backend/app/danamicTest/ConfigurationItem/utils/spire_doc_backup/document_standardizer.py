#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档标准化器

基于目录中的编号信息，为需求规格说明文档中的标题添加编号，
生成一份标准化文档，大大提高后续匹配的成功率。
"""

import os
import shutil
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from docx import Document
from docx.shared import Inches
from docx.enum.style import WD_STYLE_TYPE

from .catalog_extractor import SpireCatalogExtractor
from ..logging_utils.logger import log_info, log_error, log_debug, log_warning


class DocumentStandardizer:
    """文档标准化器 - 为标题添加编号"""
    
    def __init__(self, debug_mode: bool = False):
        """
        初始化文档标准化器
        
        Args:
            debug_mode: 是否启用调试模式
        """
        self.debug_mode = debug_mode
        self.catalog_extractor = SpireCatalogExtractor(debug_mode)  # 🔧 修复：添加缺失的catalog_extractor初始化
        
        # 编号到标题的映射关系
        self.number_to_title_map = {}
        self.title_to_number_map = {}
    
    def _debug_print(self, message: str, category: str = "DEBUG"):
        """调试输出"""
        if self.debug_mode:
            print(f"[document_standardizer] [{category}] {message}")
            
        # 同时写入日志（但不打印到控制台）
        log_debug(message, "document_standardizer")
    
    def create_standardized_document(self, catalog_docx_path: str, 
                                   requirement_docx_path: str,
                                   output_path: str = None) -> str:
        """
        创建标准化的需求规格说明文档
        
        Args:
            catalog_docx_path: 目录文档路径
            requirement_docx_path: 需求规格说明文档路径
            output_path: 输出路径（可选，默认在原文档同目录下）
            
        Returns:
            标准化文档的路径
        """
        
        try:
            # 1. 从目录文档中提取编号映射关系
            log_info(f"开始分析目录文档: {catalog_docx_path}", "document_standardizer")
            self._extract_number_mapping_from_catalog(catalog_docx_path)
            
            # 2. 生成输出路径
            if not output_path:
                requirement_path = Path(requirement_docx_path)
                output_path = str(requirement_path.parent / f"standardized_{requirement_path.name}")
            
            # 3. 复制原文档作为基础
            shutil.copy2(requirement_docx_path, output_path)
            log_info(f"已复制原文档到: {output_path}", "document_standardizer")
            
            # 4. 为标题添加编号
            self._add_numbering_to_document(output_path)
            
            log_info(f"✅ 文档标准化完成: {output_path}", "document_standardizer")
            return output_path
            
        except Exception as e:
            error_msg = f"文档标准化失败: {str(e)}"
            log_error(error_msg, "document_standardizer")
            raise Exception(error_msg)
    
    def _extract_number_mapping_from_catalog(self, catalog_docx_path: str):
        """从目录文档中提取编号到标题的映射关系"""
        
        # 使用SpireCatalogExtractor提取目录信息
        catalog_result = self.catalog_extractor.extract_catalog_from_docx(catalog_docx_path)
        
        if not catalog_result.get('success', False):
            raise Exception(f"目录提取失败: {catalog_result.get('message', '未知错误')}")
        
        catalog_items = catalog_result.get('catalog_items', [])
        self._debug_print(f"从目录中提取到 {len(catalog_items)} 个条目", "EXTRACT")
        
        # 建立映射关系
        for item in catalog_items:
            numbering = item.get('numbering', '').strip()
            title = item.get('title', '').strip()
            
            if numbering and title:
                self.number_to_title_map[numbering] = title
                self.title_to_number_map[title] = numbering
                self._debug_print(f"映射: {numbering} -> {title}", "MAPPING")
        
        log_info(f"建立了 {len(self.title_to_number_map)} 个标题到编号的映射关系", "document_standardizer")
    
    def _add_numbering_to_document(self, docx_path: str):
        """为文档中的标题添加编号"""
        
        doc = Document(docx_path)
        modified_count = 0
        
        log_info(f"开始处理文档，共 {len(doc.paragraphs)} 个段落", "document_standardizer")
        
        for para in doc.paragraphs:
            original_text = para.text.strip()
            
            if not original_text:
                continue
            
            # 检查是否是需要添加编号的标题
            matched_number = self._find_matching_number(original_text)
            
            if matched_number:
                # 检查是否已经有编号了
                if not self._already_has_numbering(original_text):
                    new_text = f"{matched_number} {original_text}"
                    para.clear()
                    para.add_run(new_text)
                    
                    modified_count += 1
                    self._debug_print(f"添加编号: '{original_text}' -> '{new_text}'", "MODIFY")
                    log_debug(f"标题编号添加: {original_text} -> {new_text}", "document_standardizer")
                else:
                    self._debug_print(f"标题已有编号，跳过: {original_text}", "SKIP")
        
        # 保存修改
        doc.save(docx_path)
        log_info(f"文档处理完成，修改了 {modified_count} 个标题", "document_standardizer")
    
    def _find_matching_number(self, text: str) -> Optional[str]:
        """
        为给定的文本查找匹配的编号
        
        采用多种策略进行匹配：
        1. 精确匹配
        2. 包含匹配
        3. 关键词匹配
        4. 模糊匹配
        
        但排除明显不是标题的格式：
        - a) b) c) 等列表项格式
        - [模板占位符] 格式
        - 1、2、3 等列表编号格式
        """
        
        # 🚫 排除规则：不应该被识别为标题的格式
        import re
        
        # 排除 a) b) c) 等列表项格式
        if re.match(r'^[a-h](\)|）)\s*', text):
            self._debug_print(f"排除列表项格式: {text[:50]}", "EXCLUDE")
            return None
        
        # 排除 (a) (b) (c) 等格式
        if re.match(r'^\([a-h]\)\s*', text):
            self._debug_print(f"排除括号列表项格式: {text[:50]}", "EXCLUDE")
            return None
        
        # 排除 1、2、3 或 1) 2) 3) 等数字列表格式
        if re.match(r'^\d{1,2}[、）)]\s*', text):
            self._debug_print(f"排除数字列表格式: {text[:50]}", "EXCLUDE")
            return None
        
        # 排除 [模板占位符] 格式
        if text.strip().startswith('[') and text.strip().endswith(']'):
            self._debug_print(f"排除模板占位符格式: {text[:50]}", "EXCLUDE")
            return None
        
        # 排除包含冒号的短文本（通常是列表项的标签部分）
        if ':' in text or '：' in text:
            if len(text.strip()) < 100:  # 短文本且包含冒号，很可能是列表项
                self._debug_print(f"排除包含冒号的短文本: {text[:50]}", "EXCLUDE")
                return None
        
        # 排除以标点符号结尾的文本
        if text.strip() and text.strip()[-1] in '。！？；：,，、.!?;:':
            self._debug_print(f"排除以标点结尾的文本: {text[:50]}", "EXCLUDE")
            return None
        
        # 1. 精确匹配
        if text in self.title_to_number_map:
            return self.title_to_number_map[text]
        
        # 2. 包含匹配（文本包含在某个映射的标题中）
        for title, number in self.title_to_number_map.items():
            if text in title or title in text:
                self._debug_print(f"包含匹配: '{text}' <-> '{title}' -> {number}", "MATCH")
                return number
        
        # 3. 关键词匹配（去除"功能"等后缀）
        text_keywords = text.replace('功能', '').replace('需求', '').strip()
        if len(text_keywords) > 2:
            for title, number in self.title_to_number_map.items():
                title_keywords = title.replace('功能', '').replace('需求', '').strip()
                if text_keywords == title_keywords:
                    self._debug_print(f"关键词匹配: '{text}' ({text_keywords}) <-> '{title}' ({title_keywords}) -> {number}", "MATCH")
                    return number
        
        # 4. 模糊匹配（字符重叠度）
        for title, number in self.title_to_number_map.items():
            overlap_score = self._calculate_text_overlap(text, title)
            if overlap_score > 0.8:  # 80%以上重叠
                self._debug_print(f"模糊匹配: '{text}' <-> '{title}' (重叠度: {overlap_score:.2f}) -> {number}", "MATCH")
                return number
        
        return None
    
    def _calculate_text_overlap(self, text1: str, text2: str) -> float:
        """计算两个文本的字符重叠度"""
        if not text1 or not text2:
            return 0.0
        
        # 转换为字符集合
        chars1 = set(text1)
        chars2 = set(text2)
        
        # 计算交集和并集
        intersection = chars1 & chars2
        union = chars1 | chars2
        
        if len(union) == 0:
            return 0.0
        
        return len(intersection) / len(union)
    
    def _already_has_numbering(self, text: str) -> bool:
        """检查文本是否已经包含编号"""
        
        # 检查是否以数字+点的模式开头（如"3.2.1 "）
        import re
        pattern = r'^\d+(\.\d+)*\s+'
        return bool(re.match(pattern, text))
    
    def get_standardized_mapping(self) -> Dict[str, str]:
        """
        获取标准化后的映射关系
        
        Returns:
            标题到完整标题（带编号）的映射
        """
        standardized_mapping = {}
        
        for title, number in self.title_to_number_map.items():
            full_title = f"{number} {title}"
            standardized_mapping[title] = full_title
        
        return standardized_mapping
    
    def create_standardized_document_from_single_file(self,
                                                    document_path: str,
                                                    output_path: str = None,
                                                    debug_mode: bool = False) -> str:
        """
        从单个文档创建标准化文档（不需要单独的目录文档）
        
        Args:
            document_path: 源文档路径
            output_path: 输出路径（可选）
            debug_mode: 调试模式
            
        Returns:
            标准化文档路径
        """
        
        try:
            log_info(f"开始处理单文档标准化: {document_path}", "document_standardizer")
            
            # 检查输入文件是否存在
            if not os.path.exists(document_path):
                raise FileNotFoundError(f"源文档不存在: {document_path}")
            
            # 2. 生成输出路径
            if not output_path:
                doc_path = Path(document_path)
                output_path = str(doc_path.parent / f"standardized_{doc_path.name}")
            
            # 3. 复制原文档作为基础
            shutil.copy2(document_path, output_path)
            log_info(f"已复制原文档到: {output_path}", "document_standardizer")
            
            # 4. 执行基本的文档标准化处理
            self._perform_basic_standardization(output_path)
            
            log_info(f"✅ 单文档标准化完成: {output_path}", "document_standardizer")
            return output_path
            
        except Exception as e:
            error_msg = f"单文档标准化失败: {str(e)}"
            log_error(error_msg, "document_standardizer")
            raise Exception(error_msg)
    
    def _perform_basic_standardization(self, document_path: str):
        """执行基本的文档标准化处理"""
        
        try:
            # 1. 首先从文档本身提取目录结构
            log_info(f"开始从文档提取目录结构: {document_path}", "document_standardizer")
            self._extract_catalog_from_document(document_path)
            
            # 2. 打开文档进行标准化处理
            doc = Document(document_path)
            log_info(f"打开文档进行标准化处理: {document_path}", "document_standardizer")
            
            # 统计处理的段落数
            processed_count = 0
            modified_count = 0
            
            # 检查并保留表格
            table_count = len(doc.tables)
            log_info(f"文档中包含 {table_count} 个表格，将保留所有表格", "document_standardizer")
            
            # 遍历文档的段落，查找可能的标题并添加编号
            for paragraph in doc.paragraphs:
                text = paragraph.text.strip()
                if text and self._is_potential_heading(paragraph):
                    processed_count += 1
                    log_debug(f"发现可能的标题: {text}", "document_standardizer")
                    
                    # 如果是潜在标题且还没有编号，尝试添加编号
                    if not self._already_has_numbering(text):
                        matched_number = self._find_matching_number(text)
                        if matched_number:
                            new_text = f"{matched_number} {text}"
                            paragraph.clear()
                            paragraph.add_run(new_text)
                            modified_count += 1
                            log_debug(f"添加编号: '{text}' -> '{new_text}'", "document_standardizer")
                        else:
                            log_debug(f"未找到匹配编号: {text}", "document_standardizer")
                    else:
                        log_debug(f"标题已有编号，跳过: {text}", "document_standardizer")
            
            # 保存文档（保留所有表格）
            doc.save(document_path)
            log_info(f"文档标准化处理完成，处理了 {processed_count} 个潜在标题，修改了 {modified_count} 个标题，保留了 {table_count} 个表格", "document_standardizer")
            
        except Exception as e:
            log_warning(f"基本标准化处理出错: {e}，但文档复制成功", "document_standardizer")
    
    def _is_potential_heading(self, paragraph) -> bool:
        """判断段落是否可能是标题（基于样式和内容）"""
        
        text = paragraph.text.strip()
        
        # 基本过滤
        if not text or len(text) > 200:  # 太长的不是标题
            return False
        
        # 1. 优先检查大纲级别（最可靠的标题标识）
        try:
            # 尝试从段落XML中提取大纲级别
            xml = paragraph._p.xml
            if xml.find('<w:outlineLvl') >= 0:
                import re
                start_index = xml.find('<w:outlineLvl')
                end_index = xml.find('>', start_index)
                outline_lvl_xml = xml[start_index:end_index+1]
                outline_level_match = re.search(r"\d+", outline_lvl_xml)
                if outline_level_match:
                    xml_outline_level = int(outline_level_match.group())
                    actual_level = xml_outline_level + 1  # Word从0开始，我们从1开始
                    log_debug(f"大纲级别匹配标题: '{text}' (XML级别: {xml_outline_level} -> 实际级别: {actual_level})", "document_standardizer")
                    return True
        except Exception as e:
            # 如果XML解析失败，继续其他检查
            pass
        
        # 2. 检查段落样式
        style_name = paragraph.style.name if paragraph.style else ""
        
        # 标题样式模式（英文和中文）
        heading_style_patterns = [
            'heading', 'title', 'head',  # 英文模式
            '标题', '级标题', '章标题', '节标题', '条标题'  # 中文模式
        ]
        
        # 如果样式明确是标题样式，直接返回True
        for pattern in heading_style_patterns:
            if pattern.lower() in style_name.lower():
                log_debug(f"样式匹配标题: '{text}' (样式: {style_name})", "document_standardizer")
                return True
        
        # 3. 检查是否已有手动编号（如 3.2.1 开头）
        import re
        if re.match(r'^\d+(\.\d+)*\s+', text):
            log_debug(f"编号格式匹配标题: '{text}'", "document_standardizer")
            return True
        
        # 4. 如果样式不是标题样式，但内容可能是标题，需要更严格的判断
        if not any(pattern.lower() in style_name.lower() for pattern in heading_style_patterns):
            # 检查段落格式特征
            if paragraph.runs:
                first_run = paragraph.runs[0]
                # 检查是否加粗
                is_bold = first_run.bold if first_run.bold is not None else False
                # 检查字体大小（如果比正文大）
                font_size = first_run.font.size
                is_larger_font = font_size and font_size.pt > 12 if font_size else False
                
                # 只有在格式特征明显时才考虑内容匹配
                if is_bold or is_larger_font:
                    # 严格的标题关键词检查
                    strict_heading_indicators = [
                        '概述', '引言', '目的', '范围', '需求', '接口需求',
                        'CSCI', '系统概述', '软件概述', '文档概述',
                        '能力需求', '外部接口需求', '内部接口需求',
                        '适应性需求', '安全性需求', '环境需求'
                    ]
                    
                    # 必须完全匹配或以这些词开头/结尾
                    for indicator in strict_heading_indicators:
                        if (text == indicator or 
                            text.startswith(indicator) or 
                            text.endswith(indicator)):
                            log_debug(f"格式+内容匹配标题: '{text}' (加粗: {is_bold}, 大字体: {is_larger_font})", "document_standardizer")
                            return True
        
        return False
    
    def _extract_catalog_from_document(self, document_path: str):
        """从文档本身提取目录结构"""
        
        try:
            # 使用SpireCatalogExtractor提取目录信息
            catalog_result = self.catalog_extractor.extract_catalog_from_docx(document_path)
            
            if not catalog_result.get('success', False):
                log_warning(f"从文档提取目录失败: {catalog_result.get('message', '未知错误')}", "document_standardizer")
                return
            
            catalog_items = catalog_result.get('catalog_items', [])
            log_info(f"从文档中提取到 {len(catalog_items)} 个目录条目", "document_standardizer")
            
            # 建立映射关系
            for item in catalog_items:
                numbering = item.get('numbering', '').strip()
                title = item.get('title', '').strip()
                
                if numbering and title:
                    self.number_to_title_map[numbering] = title
                    self.title_to_number_map[title] = numbering
                    log_debug(f"映射: {numbering} -> {title}", "document_standardizer")
            
            log_info(f"建立了 {len(self.title_to_number_map)} 个标题到编号的映射关系", "document_standardizer")
            
        except Exception as e:
            log_warning(f"从文档提取目录结构失败: {e}", "document_standardizer")


def create_standardized_requirement_document(catalog_path: str, 
                                           requirement_path: str,
                                           output_path: str = None,
                                           debug_mode: bool = False) -> str:
    """
    创建标准化的需求规格说明文档
    
    Args:
        catalog_path: 目录文档路径
        requirement_path: 需求规格说明文档路径  
        output_path: 输出路径（可选）
        debug_mode: 调试模式
        
    Returns:
        标准化文档路径
    """
    
    try:
        standardizer = DocumentStandardizer(debug_mode)
        return standardizer.create_standardized_document(
            catalog_path, requirement_path, output_path
        )
    except Exception as e:
        log_error(f"创建标准化文档失败: {e}", "document_standardizer")
        import traceback
        log_error(f"详细错误信息: {traceback.format_exc()}", "document_standardizer")
        if debug_mode:
            print(f"❌ 标准化文档创建失败: {e}")
            print(f"详细错误: {traceback.format_exc()}")
        raise


# 测试函数
def create_standardized_document_from_single_file(document_path: str,
                                                 output_path: str = None,
                                                 debug_mode: bool = False) -> str:
    """
    从单个文档创建标准化文档（函数级接口）
    
    Args:
        document_path: 源文档路径
        output_path: 输出路径（可选）
        debug_mode: 调试模式
        
    Returns:
        标准化文档路径
    """
    
    standardizer = DocumentStandardizer(debug_mode)
    return standardizer.create_standardized_document_from_single_file(document_path, output_path)


if __name__ == "__main__":
    # 测试用例
    test_catalog = "test_catalog.docx"
    test_requirement = "test_requirement.docx"
    
    if os.path.exists(test_catalog) and os.path.exists(test_requirement):
        try:
            result_path = create_standardized_requirement_document(
                test_catalog, test_requirement, debug_mode=True
            )
            print(f"✅ 标准化文档创建成功: {result_path}")
        except Exception as e:
            print(f"❌ 测试失败: {e}")
    else:
        print("❌ 测试文件不存在") 