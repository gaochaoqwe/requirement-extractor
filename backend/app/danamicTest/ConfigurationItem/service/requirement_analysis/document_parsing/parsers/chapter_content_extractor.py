#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
章节内容提取器
实现智能的章节间内容匹配算法：
1. 基本算法：匹配章节号+标题后，提取该章节到下一个同级或更高级章节之间的所有内容
2. 特殊处理：当四级及四级以上目录有子目录时，跳过有子目录的父目录
3. 字段验证：结合字段匹配算法进行内容验证
"""

import re
from typing import Dict, List, Tuple, Optional
from .....utils.logging_utils.logger import log_info, log_debug, log_error


class ChapterContentExtractor:
    """章节内容提取器"""
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        
    def extract_requirement_content(
        self, 
        document_lines: List[str], 
        requirement_names: List[str]
    ) -> Dict[str, Dict]:
        """
        智能提取需求内容
        
        Args:
            document_lines: 文档行列表
            requirement_names: 需求名称列表
            
        Returns:
            Dict[str, Dict]: 需求名称 -> 需求信息字典
        """
        log_info("开始智能章节内容提取", "chapter_content_extractor")
        
        results = {}
        
        # 1. 解析文档章节结构
        chapter_structure = self._parse_chapter_structure(document_lines)
        
        # 2. 为每个需求匹配内容
        for requirement_name in requirement_names:
            log_debug(f"处理需求: {requirement_name}", "chapter_content_extractor")
            
            requirement_content = self._extract_single_requirement_content(
                document_lines, chapter_structure, requirement_name
            )
            
            if requirement_content:
                results[requirement_name] = requirement_content
            else:
                log_debug(f"未找到需求内容: {requirement_name}", "chapter_content_extractor")
                results[requirement_name] = self._create_empty_requirement_info(requirement_name)
        
        log_info(f"章节内容提取完成，成功提取 {len([r for r in results.values() if r.get('content')])} 个需求", "chapter_content_extractor")
        return results
    
    def _parse_chapter_structure(self, document_lines: List[str]) -> List[Dict]:
        """
        解析文档的章节结构
        
        Returns:
            List[Dict]: 章节信息列表，每个字典包含：
                - line_index: 行索引
                - chapter_number: 章节编号
                - title: 标题
                - level: 章节级别
                - has_children: 是否有子章节
        """
        log_debug("开始解析文档章节结构", "chapter_content_extractor")
        
        chapters = []
        
        for i, line in enumerate(document_lines):
            line = line.strip()
            if not line:
                continue
                
            # 匹配章节编号格式 (如 3.2.1, 3.2.1.1, 3.2.1.1.1 等)
            chapter_match = re.match(r'^(\d+(?:\.\d+)*)\s+(.+)', line)
            if chapter_match:
                chapter_number = chapter_match.group(1)
                title = chapter_match.group(2).strip()
                level = len(chapter_number.split('.'))
                
                chapter_info = {
                    'line_index': i,
                    'chapter_number': chapter_number,
                    'title': title,
                    'level': level,
                    'has_children': False,  # 稍后填充
                    'full_title': f"{chapter_number} {title}"
                }
                
                chapters.append(chapter_info)
        
        # 判断哪些章节有子章节
        for i, chapter in enumerate(chapters):
            if i < len(chapters) - 1:
                next_chapter = chapters[i + 1]
                # 如果下一个章节的级别更深，说明当前章节有子章节
                if next_chapter['level'] > chapter['level']:
                    chapter['has_children'] = True
        
        log_debug(f"解析到 {len(chapters)} 个章节", "chapter_content_extractor")
        return chapters
    
    def _extract_single_requirement_content(
        self, 
        document_lines: List[str], 
        chapter_structure: List[Dict], 
        requirement_name: str
    ) -> Optional[Dict]:
        """
        提取单个需求的内容
        
        Args:
            document_lines: 文档行列表
            chapter_structure: 章节结构
            requirement_name: 需求名称
            
        Returns:
            Dict: 需求信息字典，如果未找到返回None
        """
        log_debug(f"开始提取需求内容: {requirement_name}", "chapter_content_extractor")
        
        # 1. 找到匹配的章节
        target_chapter = self._find_matching_chapter(chapter_structure, requirement_name)
        if not target_chapter:
            log_debug(f"未找到匹配的章节: {requirement_name}", "chapter_content_extractor")
            return None
        
        log_debug(f"找到匹配章节: {target_chapter['full_title']}", "chapter_content_extractor")
        
        # 2. 确定内容提取范围
        start_line, end_line = self._determine_content_range(chapter_structure, target_chapter)
        
        log_debug(f"内容提取范围: 行 {start_line} 到 {end_line}", "chapter_content_extractor")
        
        # 3. 提取原始内容
        raw_content = self._extract_raw_content(document_lines, start_line, end_line)
        
        # 4. 解析结构化内容
        structured_content = self._parse_structured_content(raw_content, requirement_name)
        
        return structured_content
    
    def _find_matching_chapter(self, chapter_structure: List[Dict], requirement_name: str) -> Optional[Dict]:
        """
        找到与需求名称匹配的章节
        
        匹配策略：
        1. 精确匹配标题
        2. 模糊匹配标题（去除标点符号）
        3. 章节号+标题匹配
        """
        clean_requirement = self._clean_text_for_matching(requirement_name)
        
        for chapter in chapter_structure:
            # 策略1：精确匹配标题
            if chapter['title'] == requirement_name:
                return chapter
            
            # 策略2：清理后的标题匹配
            clean_title = self._clean_text_for_matching(chapter['title'])
            if clean_title == clean_requirement:
                return chapter
            
            # 策略3：标题包含需求名称
            if requirement_name in chapter['title'] or chapter['title'] in requirement_name:
                return chapter
            
            # 策略4：章节号+标题完全匹配
            if chapter['full_title'] == requirement_name:
                return chapter
        
        return None
    
    def _clean_text_for_matching(self, text: str) -> str:
        """清理文本用于匹配（去除标点符号和空格）"""
        import string
        # 去除标点符号和空格
        cleaned = re.sub(r'[%s\s]+' % re.escape(string.punctuation), '', text)
        return cleaned.lower()
    
    def _determine_content_range(
        self, 
        chapter_structure: List[Dict], 
        target_chapter: Dict
    ) -> Tuple[int, int]:
        """
        确定内容提取的行范围
        
        实现用户描述的算法：
        1. 基本算法：找到下一个同级或更高级章节
        2. 特殊处理：跳过有子章节的父章节
        """
        start_line = target_chapter['line_index'] + 1  # 从标题下一行开始
        
        # 找到当前章节在结构中的位置
        current_index = chapter_structure.index(target_chapter)
        current_level = target_chapter['level']
        
        log_debug(f"当前章节级别: {current_level}, 有子章节: {target_chapter['has_children']}", "chapter_content_extractor")
        
        # 寻找结束位置
        end_line = len(chapter_structure)  # 默认到文档末尾
        
        for i in range(current_index + 1, len(chapter_structure)):
            next_chapter = chapter_structure[i]
            next_level = next_chapter['level']
            
            log_debug(f"检查章节: {next_chapter['full_title']}, 级别: {next_level}", "chapter_content_extractor")
            
            # 如果遇到同级或更高级的章节
            if next_level <= current_level:
                # 🌟 特殊处理：如果这个章节有子章节且级别>=4，继续寻找
                if next_level >= 4 and next_chapter['has_children']:
                    log_debug(f"跳过有子章节的父章节: {next_chapter['full_title']}", "chapter_content_extractor")
                    continue
                else:
                    end_line = next_chapter['line_index']
                    log_debug(f"找到结束章节: {next_chapter['full_title']}, 结束行: {end_line}", "chapter_content_extractor")
                    break
        
        return start_line, end_line
    
    def _extract_raw_content(self, document_lines: List[str], start_line: int, end_line: int) -> List[str]:
        """提取原始内容行"""
        if start_line >= len(document_lines):
            return []
        
        actual_end = min(end_line, len(document_lines))
        raw_lines = document_lines[start_line:actual_end]
        
        # 过滤空行和章节标题行
        content_lines = []
        for line in raw_lines:
            line = line.strip()
            if not line:
                continue
            
            # 跳过子章节标题
            if re.match(r'^\d+(?:\.\d+)*\s+', line):
                continue
                
            content_lines.append(line)
        
        return content_lines
    
    def _parse_structured_content(self, content_lines: List[str], requirement_name: str) -> Dict:
        """
        解析结构化内容
        
        结合字段匹配算法，提取标准化的需求信息
        """
        if not content_lines:
            return self._create_empty_requirement_info(requirement_name)
        
        # 合并所有内容
        full_content = '\n'.join(content_lines)
        
        # 尝试解析标准字段格式
        structured_info = self._parse_standard_fields(full_content)
        
        # 🔧 修复：验证是否包含足够的关键字段（至少4-5个）
        required_fields = ['identifier', 'description', 'entry_condition', 'input', 'output', 'processing']
        found_fields = [field for field in required_fields if structured_info.get(field, '').strip()]
        
        log_debug(f"找到 {len(found_fields)} 个关键字段: {found_fields}", "chapter_content_extractor")
        
        # 如果关键字段少于4个，认为内容结构不符合要求
        if len(found_fields) < 4:
            structured_info = {
                'identifier': '',
                'description': full_content[:500] + ('...' if len(full_content) > 500 else ''),
                'entry_condition': '',
                'input': '',
                'output': '',
                'processing': '',
                'performance': '',
                'constraints': ''
            }
        
        # 添加元数据
        structured_info.update({
            'content': full_content,
            'requirement_name': requirement_name,
            'extracted_by': 'chapter_content_extractor',
            'content_length': len(full_content)
        })
        
        return structured_info
    
    def _parse_standard_fields(self, content: str) -> Dict:
        """
        解析标准字段格式 (a) 标识号, b) 说明, c) 进入条件, 等)
        """
        fields = {
            'identifier': '',
            'description': '',
            'entry_condition': '',
            'input': '',
            'output': '',
            'processing': '',
            'performance': '',
            'constraints': ''
        }
        
        # 字段模式映射 - 标准格式：a) 标识号：、b) 说明：等
        field_patterns = {
            r'[a-h]\)\s*标识号[：:]\s*(.+?)(?=[a-h]\)|$)': 'identifier',
            r'[a-h]\)\s*说明[：:]\s*(.+?)(?=[a-h]\)|$)': 'description',
            r'[a-h]\)\s*进入条件[：:]\s*(.+?)(?=[a-h]\)|$)': 'entry_condition',
            r'[a-h]\)\s*输入[：:]\s*(.+?)(?=[a-h]\)|$)': 'input',
            r'[a-h]\)\s*输出[：:]\s*(.+?)(?=[a-h]\)|$)': 'output',
            r'[a-h]\)\s*处理[：:]\s*(.+?)(?=[a-h]\)|$)': 'processing',
            r'[a-h]\)\s*性能[：:]\s*(.+?)(?=[a-h]\)|$)': 'performance',
            r'[a-h]\)\s*约束[与和]?限制[：:]\s*(.+?)(?=[a-h]\)|$)': 'constraints'
        }
        
        for pattern, field_name in field_patterns.items():
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                fields[field_name] = match.group(1).strip()
        
        return fields
    
    def _create_empty_requirement_info(self, requirement_name: str) -> Dict:
        """创建空的需求信息"""
        return {
            'identifier': '',
            'description': '',
            'entry_condition': '',
            'input': '',
            'output': '',
            'processing': '',
            'performance': '',
            'constraints': '',
            'content': '',
            'requirement_name': requirement_name,
            'extracted_by': 'chapter_content_extractor',
            'content_length': 0
        } 