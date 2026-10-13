#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
编号工具模块 - 处理编号生成和管理

功能：
1. 自动编号生成
2. 手动编号生成
3. 级别计数器管理
4. 上下文管理
"""

from typing import Dict, List, Any, Optional


class NumberingManager:
    """编号管理器"""
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        
        # 计数器
        self.auto_level_counters = {}
        self.manual_level_counters = {}
        
        # 上下文跟踪
        self.current_context = []
    
    def _debug_print(self, message: str, category: str = "NUMBERING"):
        """调试输出"""
        if self.debug_mode:
            print(f"[{category}] {message}")
    
    def generate_auto_numbering_text(self, numbering_defs: Dict, num_id: str, ilvl: int) -> str:
        """生成自动编号文本"""
        
        if num_id not in numbering_defs:
            return ""
        
        numbering_def = numbering_defs[num_id]
        if ilvl not in numbering_def:
            return ""
        
        level_def = numbering_def[ilvl]
        lvl_text = level_def['lvl_text']
        
        level = ilvl + 1
        
        # 替换占位符
        result = lvl_text
        for i in range(1, level + 1):
            placeholder = f"%{i}"
            if placeholder in result:
                counter_val = self.auto_level_counters.get(i, 1)
                result = result.replace(placeholder, str(counter_val))
        
        return result.strip()
    
    def generate_manual_numbering(self, level: int) -> str:
        """生成手动编号"""
        
        parts = []
        for i in range(1, level + 1):
            parts.append(str(self.manual_level_counters.get(i, 1)))
        return ".".join(parts)
    
    def update_auto_level_counters(self, level: int):
        """更新自动编号级别计数器"""
        
        # 清除更深级别的计数器
        for l in list(self.auto_level_counters.keys()):
            if l > level:
                del self.auto_level_counters[l]
        
        # 更新当前级别
        if level not in self.auto_level_counters:
            self.auto_level_counters[level] = 0
        self.auto_level_counters[level] += 1
    
    def update_manual_level_counters(self, level: int):
        """更新手动编号级别计数器"""
        
        # 清除更深级别的计数器
        for l in list(self.manual_level_counters.keys()):
            if l > level:
                del self.manual_level_counters[l]
        
        # 更新当前级别
        if level not in self.manual_level_counters:
            self.manual_level_counters[level] = 0
        self.manual_level_counters[level] += 1
    
    def update_context(self, heading_info: Dict[str, Any]):
        """更新上下文栈"""
        
        level = heading_info['level']
        
        # 更精确的上下文更新逻辑
        # 只移除比当前级别更深的上下文，保留同级和更浅的
        self.current_context = [ctx for ctx in self.current_context if ctx['level'] < level]
        
        # 添加当前标题
        self.current_context.append(heading_info)
        
        # 限制栈深度
        if len(self.current_context) > 6:
            self.current_context = self.current_context[-6:]
            
        self._debug_print(f"更新上下文: 添加{level}级标题，当前上下文: {[ctx['level'] for ctx in self.current_context]}", "CONTEXT")
    
    def reset(self):
        """重置所有计数器和上下文"""
        
        self.auto_level_counters.clear()
        self.manual_level_counters.clear()
        self.current_context.clear()
    
    def get_context_levels(self) -> List[int]:
        """获取当前上下文级别列表"""
        
        return [ctx['level'] for ctx in self.current_context]
    
    def get_current_depth(self) -> int:
        """获取当前上下文深度"""
        
        return len(self.current_context)


class HeadingGenerator:
    """标题生成器"""
    
    def __init__(self, numbering_manager: NumberingManager, debug_mode: bool = False):
        self.numbering_manager = numbering_manager
        self.debug_mode = debug_mode
    
    def _debug_print(self, message: str, category: str = "HEADING"):
        """调试输出"""
        if self.debug_mode:
            print(f"[{category}] {message}")
    
    def create_auto_numbered_heading(self, para: Dict[str, Any], numbering_defs: Dict, 
                                   num_id: str, ilvl: int) -> Dict[str, Any]:
        """创建自动编号标题"""
        
        level = ilvl + 1
        text = para['text']
        
        # 生成自动编号
        self.numbering_manager.update_auto_level_counters(level)
        numbering = self.numbering_manager.generate_auto_numbering_text(numbering_defs, num_id, ilvl)
        
        self._debug_print(f"✓ 自动编号: [{level}级] {numbering} {text}", "AUTO")
        
        return {
            'numbering': numbering,
            'title': text,
            'full_text': f"{numbering} {text}",
            'level': level,
            'style_name': para.get('style_id', ''),
            'source': 'auto_numbering',
            'is_auto_numbered': True
        }
    
    def create_style_heading(self, para: Dict[str, Any], style_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """创建样式标题"""
        
        text = para['text']
        
        # 使用检测到的标题级别，如果没有则使用大纲级别
        if style_info.get('heading_level') is not None:
            level = style_info['heading_level']
        elif style_info.get('outline_level') is not None:
            level = style_info['outline_level'] + 1
        else:
            level = 1
        
        # 排除7级及以上标题直接拒绝
        if level >= 7:
            self._debug_print(f"拒绝过深标题级别: {level}级 -> {text[:50]}", "REJECT")
            return None
        
        # 生成手动编号
        self.numbering_manager.update_manual_level_counters(level)
        numbering = self.numbering_manager.generate_manual_numbering(level)
        
        self._debug_print(f"✓ 样式标题: [{level}级] {numbering} {text}", "STYLE")
        
        return {
            'numbering': numbering,
            'title': text,
            'full_text': f"{numbering} {text}",
            'level': level,
            'style_name': style_info['name'],
            'source': 'style_based',
            'is_auto_numbered': False
        }
    
    def create_manual_numbered_heading(self, para: Dict[str, Any], manual_numbering: str, 
                                     clean_text: str, level: int) -> Dict[str, Any]:
        """创建手动编号标题"""
        
        self._debug_print(f"✓ 手动编号: [{level}级] {manual_numbering} {clean_text}", "MANUAL")
        
        return {
            'numbering': manual_numbering,
            'title': clean_text,
            'full_text': f"{manual_numbering} {clean_text}",
            'level': level,
            'style_name': para.get('style_id', ''),
            'source': 'manual_numbering',
            'is_auto_numbered': False
        }
    
    def create_outline_heading(self, para: Dict[str, Any], outline_level: int) -> Dict[str, Any]:
        """创建大纲级别标题"""
        
        level = outline_level + 1
        text = para['text']
        
        self.numbering_manager.update_manual_level_counters(level)
        numbering = self.numbering_manager.generate_manual_numbering(level)
        
        self._debug_print(f"✓ 大纲标题: [{level}级] {numbering} {text}", "OUTLINE")
        
        return {
            'numbering': numbering,
            'title': text,
            'full_text': f"{numbering} {text}",
            'level': level,
            'style_name': para.get('style_id', ''),
            'source': 'outline_level',
            'is_auto_numbered': False
        } 