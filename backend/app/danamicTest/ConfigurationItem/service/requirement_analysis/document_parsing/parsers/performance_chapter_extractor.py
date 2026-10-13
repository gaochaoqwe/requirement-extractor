"""
性能章节提取器
从标准化文档中提取专门的性能需求章节内容，用于AI分析性能测试项和余量测试项
"""

import os
import re
from typing import List, Dict, Any, Optional, Tuple
from docx import Document
from .....utils.logging_utils.logger import log_info, log_warning, log_error, log_debug


class PerformanceChapterExtractor:
    """性能章节提取器"""
    
    def __init__(self):
        self.logger_name = "performance_chapter_extractor"
        # 性能需求章节的可能编号模式
        self.performance_chapter_patterns = [
            r'3\.11\.3\s*性能需求',
            r'3\.10\.3\s*性能需求', 
            r'3\.11\.2\s*性能需求',
            r'3\.10\.2\s*性能需求',
            r'3\.11\.1\s*性能需求',
            r'3\.10\.1\s*性能需求',
            # 也支持没有"性能需求"后缀的情况
            r'3\.11\.3\s*性能',
            r'3\.10\.3\s*性能',
            r'3\.11\.2\s*性能',
            r'3\.10\.2\s*性能',
            r'3\.11\.1\s*性能',
            r'3\.10\.1\s*性能'
        ]
    
    def extract_performance_chapter_content(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        从标准化文档中提取性能需求章节内容
        
        Args:
            file_path: 标准化文档路径
            
        Returns:
            包含章节标题、编号、内容的字典，如果未找到则返回None
        """
        try:
            log_info(f"开始从文档提取性能需求章节: {file_path}", self.logger_name)
            
            if not os.path.exists(file_path):
                log_warning(f"文档文件不存在: {file_path}", self.logger_name)
                return None
                
            doc = Document(file_path)
            
            # 查找性能需求章节
            chapter_info = self._find_performance_chapter(doc)
            if not chapter_info:
                log_warning("未找到性能需求章节", self.logger_name)
                return None
                
            # 提取章节内容
            chapter_content = self._extract_chapter_content(doc, chapter_info)
            
            result = {
                'chapter_number': chapter_info['number'],
                'chapter_title': chapter_info['title'],
                'content': chapter_content,
                'source_file': file_path
            }
            
            log_info(f"性能需求章节提取成功: {chapter_info['number']} {chapter_info['title']}", self.logger_name)
            log_debug(f"章节内容长度: {len(chapter_content)} 字符", self.logger_name)
            
            return result
            
        except Exception as e:
            log_error(f"性能需求章节提取失败: {e}", self.logger_name)
            import traceback
            log_error(f"详细错误: {traceback.format_exc()}", self.logger_name)
            return None
    
    def _find_performance_chapter(self, doc: Document) -> Optional[Dict[str, str]]:
        """
        在文档中查找性能需求章节
        
        Args:
            doc: docx文档对象
            
        Returns:
            包含章节编号和标题的字典，未找到返回None
        """
        try:
            for paragraph in doc.paragraphs:
                text = paragraph.text.strip()
                if not text:
                    continue
                    
                # 检查是否匹配性能需求章节模式
                for pattern in self.performance_chapter_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        # 提取章节编号
                        number_match = re.search(r'(3\.\d{1,2}\.\d)', text)
                        chapter_number = number_match.group(1) if number_match else ""
                        
                        log_info(f"找到性能需求章节: {text}", self.logger_name)
                        return {
                            'number': chapter_number,
                            'title': text
                        }
            
            return None
            
        except Exception as e:
            log_error(f"查找性能需求章节时出错: {e}", self.logger_name)
            return None
    
    def _extract_chapter_content(self, doc: Document, chapter_info: Dict[str, str]) -> str:
        """
        提取章节的完整内容
        
        Args:
            doc: docx文档对象
            chapter_info: 章节信息
            
        Returns:
            章节的完整文本内容
        """
        try:
            content_parts = []
            chapter_title = chapter_info['title']
            
            # 找到章节标题段落的位置（使用文本匹配）
            chapter_index = -1
            for i, paragraph in enumerate(doc.paragraphs):
                if paragraph.text.strip() == chapter_title:
                    chapter_index = i
                    log_debug(f"找到章节标题段落位置: {i}", self.logger_name)
                    break
            
            if chapter_index == -1:
                log_warning(f"无法定位章节标题段落: '{chapter_title}'", self.logger_name)
                # 尝试模糊匹配
                for i, paragraph in enumerate(doc.paragraphs):
                    text = paragraph.text.strip()
                    if chapter_info['number'] in text and '性能需求' in text:
                        chapter_index = i
                        log_info(f"使用模糊匹配找到章节位置: {i}, 文本: '{text}'", self.logger_name)
                        break
                
                if chapter_index == -1:
                    return ""
            
            # 从章节标题后开始收集内容，直到下一个同级或更高级章节
            for i in range(chapter_index + 1, len(doc.paragraphs)):
                paragraph = doc.paragraphs[i]
                text = paragraph.text.strip()
                
                if not text:
                    continue
                
                # 检查是否到达下一个章节（同级或更高级）
                if self._is_next_chapter(text, chapter_info['number']):
                    log_debug(f"遇到下一个章节，停止收集: '{text}'", self.logger_name)
                    break
                
                content_parts.append(text)
                log_debug(f"收集内容: '{text[:50]}...'", self.logger_name)
            
            content = '\n'.join(content_parts).strip()
            log_info(f"章节内容提取完成，长度: {len(content)} 字符", self.logger_name)
            if content:
                log_debug(f"提取到章节内容预览: {content[:200]}...", self.logger_name)
            else:
                log_warning("章节内容为空", self.logger_name)
            
            return content
            
        except Exception as e:
            log_error(f"提取章节内容时出错: {e}", self.logger_name)
            import traceback
            log_error(f"详细错误: {traceback.format_exc()}", self.logger_name)
            return ""
    
    def _is_next_chapter(self, text: str, current_chapter: str) -> bool:
        """
        判断是否是下一个章节（同级或更高级）
        
        Args:
            text: 段落文本
            current_chapter: 当前章节编号（如3.10.3）
            
        Returns:
            是否是下一个章节
        """
        try:
            # 匹配章节编号模式
            chapter_pattern = r'^(\d+(?:\.\d+)*)\s+'
            match = re.search(chapter_pattern, text)
            
            if not match:
                return False
                
            found_chapter = match.group(1)
            
            # 解析章节层级
            current_parts = current_chapter.split('.')
            found_parts = found_chapter.split('.')
            
            # 如果层级数不同
            if len(found_parts) <= len(current_parts):
                # 同级或更高级章节
                if len(found_parts) == len(current_parts):
                    # 同级章节，比较编号
                    return found_parts != current_parts
                else:
                    # 更高级章节
                    return True
            
            return False
            
        except Exception as e:
            log_debug(f"判断章节层级时出错: {e}", self.logger_name)
            return False
    
    def get_standardized_document_path(self, session_dir: str) -> Optional[str]:
        """
        获取会话目录中的标准化文档路径
        
        Args:
            session_dir: 会话目录路径
            
        Returns:
            标准化文档路径，未找到返回None
        """
        try:
            import glob
            
            # 查找标准化需求文档
            standardized_files = glob.glob(os.path.join(session_dir, "standardized_requirement_*"))
            
            if standardized_files:
                log_info(f"找到标准化文档: {standardized_files[0]}", self.logger_name)
                return standardized_files[0]
            else:
                log_warning(f"未找到标准化文档，会话目录: {session_dir}", self.logger_name)
                return None
                
        except Exception as e:
            log_error(f"查找标准化文档时出错: {e}", self.logger_name)
            return None 