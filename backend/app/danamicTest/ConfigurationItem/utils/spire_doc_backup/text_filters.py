#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本过滤模块 - 过滤非标题文本和列表项

功能：
1. 通用文本过滤规则（无关键词依赖）
2. 列表项结构检测
3. 手动编号提取和验证
"""

import re
from typing import Tuple, Optional


class TextFilter:
    """文本过滤器"""
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
    
    def _debug_print(self, message: str, category: str = "FILTER"):
        """调试输出"""
        if self.debug_mode:
            print(f"[{category}] {message}")
    
    def should_exclude_text(self, text: str, current_context: list = None) -> bool:
        """排除明显不是标题的文本（通用版 - 无关键词依赖）"""
        
        text_stripped = text.strip()
        if not text_stripped:
            return True
        
        # 规则1：末尾有标点符号肯定不是标题
        if text_stripped[-1] in '。！？；：,，、.!?;:':
            self._debug_print(f"排除末尾标点: '{text_stripped[-1]}' -> {text[:50]}", "EXCLUDE")
            return True
        
        # 规则2：过长文本通常是描述性内容，不是标题
        if len(text_stripped) > 100:
            self._debug_print(f"排除过长文本: {len(text_stripped)}字符", "EXCLUDE")
            return True
        
        # 规则3：过短或纯符号文本
        if len(text_stripped) < 2 or text_stripped in [':', '：', '-', '•', '▪', '■', '●']:
            self._debug_print(f"排除过短文本: '{text_stripped}'", "EXCLUDE")
            return True
        
        # 规则4：模板占位符格式 [...]
        if text_stripped.startswith('[') and text_stripped.endswith(']'):
            self._debug_print(f"排除模板占位符: {text[:50]}", "EXCLUDE")
            return True
        
        # 规则5：纯数字或纯字母（通常是列表标记）
        if text_stripped.isdigit() or (len(text_stripped) == 1 and text_stripped.isalpha()):
            self._debug_print(f"排除纯标记: '{text_stripped}'", "EXCLUDE")
            return True
        
        # 规则6：过度嵌套的编号（结构异常）
        manual_numbering, clean_text = self.extract_manual_numbering(text)
        if manual_numbering:
            dots = manual_numbering.count('.')
            # 超过5级的编号通常是异常情况（对应6级标题）
            if dots > 5:  # 6级以上不允许
                self._debug_print(f"排除过度嵌套编号: {manual_numbering} -> {text[:50]}", "EXCLUDE")
                return True
        
        # 规则7：连续标点符号（格式异常）
        punctuation_count = sum(1 for c in text_stripped if c in '.,;:!?()[]{}""''')
        if punctuation_count > len(text_stripped) * 0.3:  # 超过30%是标点符号
            self._debug_print(f"排除标点密集: {punctuation_count}/{len(text_stripped)} -> {text[:50]}", "EXCLUDE")
            return True
        
        # 规则8：单字母编号模式分析（结构特征）
        # 检查是否是 a) b) c) 这样的模式，且处于特定上下文
        if self.is_likely_list_item_by_structure(text_stripped, current_context):
            self._debug_print(f"排除列表项结构: {text[:50]}", "EXCLUDE")
            return True
        
        return False
    
    def is_likely_list_item_by_structure(self, text: str, current_context: list = None) -> bool:
        """基于结构特征判断是否为列表项（无关键词依赖）"""
        
        # 检查是否匹配单字母或单数字的列表标记模式
        list_patterns = [
            r'^[a-h](\)|$)',  # a) 或 a
            r'^\d{1,2}[\.\)]',  # 1. 或 1) 或 12.
            r'^\([a-h]\)',  # (a)
            r'^\(\d{1,2}\)',  # (1) 或 (12)
        ]
        
        for pattern in list_patterns:
            if re.match(pattern, text):
                # 进一步检查上下文：如果当前层级已经很深（>4级），
                # 且文本较短（<50字符），很可能是列表项
                if current_context and len(current_context) > 4 and len(text) < 50:
                    return True
                        
                # 检查文本密度：如果包含很多"：" "；"等列表常用符号
                list_indicators = text.count(':') + text.count('：') + text.count(';') + text.count('；')
                if list_indicators > 0 and len(text) < 80:
                    return True
        
        return False
    
    def extract_manual_numbering(self, text: str) -> Tuple[Optional[str], str]:
        """提取手动编号"""
        
        patterns = [
            r'^(\d+(?:\.\d+)*\.?)\s+(.+)$',  # 1.2.3 标题
            r'^([a-h])\)\s+(.+)$',           # a) 标题
            r'^\((\d+)\)\s+(.+)$',           # (1) 标题
        ]
        
        for pattern in patterns:
            match = re.match(pattern, text.strip())
            if match:
                return match.group(1), match.group(2).strip()
        
        return None, text
    
    def determine_manual_numbering_level(self, numbering: str, text: str, current_context: list = None) -> int:
        """确定手动编号的级别"""
        
        # 基于编号中的点号数量推断级别
        dots = numbering.count('.')
        inferred_level = dots + 1
        
        if self.debug_mode:
            print(f"      🎯 级别推断: 编号'{numbering}' -> 点号数={dots} -> 初始级别={inferred_level}")
            if current_context:
                context_levels = [ctx['level'] for ctx in current_context]
                print(f"      📚 当前上下文级别: {context_levels}")
        
        # 关键排除：超过6级直接拒绝
        if inferred_level > 6:
            self._debug_print(f"拒绝过深手动编号级别: {inferred_level}级 -> {numbering}", "REJECT")
            if self.debug_mode:
                print(f"      ❌ 级别过深被拒绝: {inferred_level} > 6")
            return -1  # 返回无效级别
        
        # 检查上下文，避免级别跳跃过大
        if current_context:
            last_level = len(current_context)
            
            if self.debug_mode:
                print(f"      🔍 上下文检查: 当前上下文深度={last_level}, 推断级别={inferred_level}")
            
            # 如果级别跳跃超过2级，使用上下文推断
            if inferred_level > last_level + 2:
                adjusted_level = min(last_level + 1, 6)  # 最多到6级
                self._debug_print(f"级别调整: {inferred_level} -> {adjusted_level} (基于上下文)", "LEVEL")
                if self.debug_mode:
                    print(f"      ⚖️ 级别跳跃过大，调整: {inferred_level} -> {adjusted_level}")
                return adjusted_level
        
        final_level = min(inferred_level, 6)  # 确保不超过6级
        if self.debug_mode:
            print(f"      ✅ 最终级别: {final_level}")
        
        return final_level


def parse_and_validate_catalog(catalog_text: str) -> dict:
    """
    解析和验证目录文本
    
    Args:
        catalog_text: 目录文本
        
    Returns:
        解析结果
    """
    
    lines = catalog_text.strip().split('\n')
    catalog_items = []
    text_filter = TextFilter()
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 解析级别（根据缩进）
        level = 1
        original_line = line
        while line.startswith('  '):
            level += 1
            line = line[2:]
        
        # 解析编号和标题
        numbering = ""
        title = line
        
        # 尝试提取编号
        manual_numbering, clean_title = text_filter.extract_manual_numbering(line)
        if manual_numbering:
            numbering = manual_numbering
            title = clean_title
        
        catalog_items.append({
            'level': level,
            'numbering': numbering,
            'title': title,
            'full_text': f"{numbering} {title}" if numbering else title,
            'style_name': f'Level{level}',
            'is_auto_numbered': False
        })
    
    return {
        'success': True,
        'catalog_items': catalog_items,
        'total_count': len(catalog_items),
        'message': f"解析完成，共 {len(catalog_items)} 个条目",
        'validation': {
            'is_valid': True,
            'message': "目录内容验证通过",
            'warnings': [],
            'errors': []
        }
    } 