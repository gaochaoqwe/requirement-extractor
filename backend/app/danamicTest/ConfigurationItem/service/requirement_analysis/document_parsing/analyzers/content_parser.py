#!/usr/bin/env python3
"""
内容解析器模块
专门处理需求段落内容的解析和提取

功能包括：
- a)、b)、c)段落识别
- 段落内容提取
- 段落类型识别
- 内容格式化
"""

import re
from typing import Dict, List, Optional

# 导入日志工具
try:
    from .....utils.logging_utils.logger import log_info, log_error, log_debug, log_warning
except ImportError:
    try:
        from .....utils.logging_utils.logger import log_info, log_error, log_debug, log_warning
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_debug, log_warning


class ContentParser:
    """内容解析器"""
    
    def __init__(self):
        """初始化解析器"""
        self.requirement_patterns = [
            # a) 格式：英文字母+英文括号
            (r'([a-h])\)\s*', 'en_paren'),
            # a）格式：英文字母+中文括号  
            (r'([a-h])）\s*', 'cn_paren'),
        ]
    
    def extract_requirement_sections_from_content(self, content: str, req_name: str) -> Dict[str, str]:
        """
        从章节内容中提取需求的a)、b)、c)等详细信息段落
        
        Args:
            content: 章节内容
            req_name: 需求名称
            
        Returns:
            结构化的需求信息
        """
        # log_debug(f"开始提取需求段落: {req_name}", "content_parser")
        
        # 初始化结果字典
        requirement_info = {
            'identifier': '',        # a) 标识号
            'description': '',       # b) 说明
            'entry_condition': '',   # c) 进入条件
            'input': '',            # d) 输入
            'output': '',           # e) 输出
            'processing': '',       # f) 处理
            'performance': '',      # g) 性能
            'constraints': ''       # h) 约束与限制
        }
        
        if not content.strip():
            # log_warning(f"需求内容为空: {req_name}", "content_parser")
            return self.create_default_requirement_info(req_name)
        
        # 按行分割内容
        lines = content.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 识别段落类型
            section_type = self.identify_section_type(line)
            
            if section_type:
                # 保存之前的段落
                if current_section and current_content:
                    requirement_info[current_section] = self.process_section_content(current_content)
                
                # 开始新段落
                current_section = section_type
                current_content = [self.extract_content_after_marker(line)]
            else:
                # 添加到当前段落
                if current_section:
                    current_content.append(line)
        
        # 保存最后一个段落
        if current_section and current_content:
            requirement_info[current_section] = self.process_section_content(current_content)
        
        # 如果没有提取到任何结构化信息，将整个内容作为描述
        if not any(requirement_info.values()):
            requirement_info['description'] = content.strip()[:200]  # 限制长度
            # log_info(f"未找到结构化段落，使用全文作为描述: {req_name}", "content_parser")
        
        # log_info(f"需求段落提取完成: {req_name}", "content_parser")
        return requirement_info
    
    def identify_section_type(self, paragraph: str) -> Optional[str]:
        """
        识别段落类型（a)、b)、c)等）
        
        Returns:
            段落类型标识符，如果不是标准格式则返回None
        """
        # 匹配各种格式的段落标记
        for pattern, format_type in self.requirement_patterns:
            match = re.match(pattern, paragraph)
            if match:
                letter = match.group(1).lower()
                
                # 映射字母到字段名 - 🔧 修复字段映射错误
                mapping = {
                    'a': 'identifier',       # a) 标识号 (通常不需要，但保留以避免错误)
                    'b': 'description',      # b) 说明
                    'c': 'entry_condition',  # c) 进入条件
                    'd': 'input',           # d) 输入
                    'e': 'output',          # e) 输出
                    'f': 'processing',      # f) 处理
                    'g': 'performance',     # g) 性能
                    'h': 'constraints'      # h) 约束与限制
                }
                
                return mapping.get(letter)
        
        return None
    
    def extract_content_after_marker(self, paragraph: str) -> str:
        """
        提取段落标记后的内容
        
        Args:
            paragraph: 包含标记的段落，如 "a) 用户登录时..."
            
        Returns:
            去除标记后的内容
        """
        # 去除段落标记（a)、b)等）
        for pattern, _ in self.requirement_patterns:
            content = re.sub(pattern, '', paragraph).strip()
            if content != paragraph.strip():  # 如果有变化，说明匹配了
                # 🔧 修复：提取冒号后的内容
                if '：' in content:
                    parts = content.split('：', 1)
                    if len(parts) > 1:
                        return parts[1].strip()
                elif ':' in content:
                    parts = content.split(':', 1)
                    if len(parts) > 1:
                        return parts[1].strip()
                return content
        
        return paragraph.strip()
    
    def process_section_content(self, content_list: List[str]) -> str:
        """
        处理段落内容列表，合并为单个字符串
        
        Args:
            content_list: 内容行列表
            
        Returns:
            处理后的内容字符串
        """
        if not content_list:
            return ''
        
        # 合并所有行
        combined_content = ' '.join(line.strip() for line in content_list if line.strip())
        
        # 清理多余的空格
        combined_content = re.sub(r'\s+', ' ', combined_content).strip()
        
        return combined_content
    
    def create_default_requirement_info(self, req_name: str) -> Dict[str, str]:
        """
        为需求创建默认信息
        
        Args:
            req_name: 需求名称
            
        Returns:
            默认的需求信息字典
        """
        return {
            'identifier': '',        # a) 标识号
            'description': f'验证{req_name}的功能实现',
            'entry_condition': '系统正常运行状态',
            'input': '相关输入参数',
            'output': '预期输出结果',
            'processing': f'执行{req_name}相关处理逻辑',
            'performance': '满足系统性能要求',
            'constraints': '符合系统约束条件'
        }


# 创建全局实例
content_parser = ContentParser() 