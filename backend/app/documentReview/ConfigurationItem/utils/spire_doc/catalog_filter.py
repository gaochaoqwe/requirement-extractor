#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
目录过滤模块 - 专门处理测试需求的目录过滤

功能：
1. 3.2.x章节过滤
2. 叶子节点识别和过滤
3. 测试需求分类统计
"""

from typing import Dict, List, Any


class CatalogFilter:
    """目录过滤器"""
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
    
    def _debug_print(self, message: str, category: str = "FILTER"):
        """调试输出"""
        if self.debug_mode:
            print(f"[{category}] {message}")
    
    def filter_for_testing(self, catalog_items: List[Dict[str, Any]], debug_mode: bool = False) -> Dict[str, Any]:
        """
        过滤目录，用于测试需求提取
        
        过滤规则：
        1. 只保留3.2.x开头的目录项
        2. 对于4级及以上级别，删除有子章节的需求项，只保留叶子节点需求
        
        Args:
            catalog_items: 完整的目录项列表
            debug_mode: 是否启用调试模式
            
        Returns:
            过滤后的结果字典
        """
        
        if debug_mode:
            print("\n" + "="*60)
            print("🔍 开始目录过滤 (测试需求专用)")
            print("="*60)
        
        # 第一步：只保留3.2.x开头的目录项
        step1_filtered = self._filter_by_3_2_prefix(catalog_items, debug_mode)
        
        # 第二步：对于4级及以上级别，只保留叶子节点
        step2_filtered = self._filter_leaf_nodes(step1_filtered, debug_mode)
        
        # 统计和分类
        result = self._generate_filter_result(catalog_items, step1_filtered, step2_filtered, debug_mode)
        
        return result
    
    def _filter_by_3_2_prefix(self, catalog_items: List[Dict[str, Any]], debug_mode: bool) -> List[Dict[str, Any]]:
        """第一步过滤：只保留3.2.x开头的目录项"""
        
        step1_filtered = []
        
        for item in catalog_items:
            numbering = item.get('numbering', '')
            # 只保留3.2的子章节（3.2.1、3.2.2等），排除3.2本身
            if numbering.startswith('3.2.') and numbering != '3.2':
                step1_filtered.append(item)
                if debug_mode:
                    print(f"✅ 保留: [{item['level']}级] {numbering} {item['title'][:50]}...")
            elif debug_mode and numbering:
                print(f"❌ 排除: [{item['level']}级] {numbering} {item['title'][:50]}... (非3.2.x子章节)")
        
        if debug_mode:
            print(f"\n📊 第一步过滤结果: {len(catalog_items)} -> {len(step1_filtered)} 项")
        
        return step1_filtered
    
    def _filter_leaf_nodes(self, step1_filtered: List[Dict[str, Any]], debug_mode: bool) -> List[Dict[str, Any]]:
        """第二步过滤：对于4级及以上级别，只保留叶子节点"""
        
        step2_filtered = []
        
        # 构建层级关系映射
        hierarchy_map = self._build_hierarchy_map(step1_filtered)
        
        # 过滤逻辑：对于4级及以上，只保留叶子节点
        for numbering, node in hierarchy_map.items():
            item = node['item']
            level = node['level']
            has_children = len(node['children']) > 0
            
            if level < 4:
                # 1-3级标题始终保留
                step2_filtered.append(item)
                if debug_mode:
                    print(f"✅ 保留: [{level}级] {numbering} {item['title'][:50]}... (高级标题)")
            elif level >= 4 and not has_children:
                # 4级及以上，只保留叶子节点
                step2_filtered.append(item)
                if debug_mode:
                    print(f"✅ 保留: [{level}级] {numbering} {item['title'][:50]}... (叶子节点)")
            elif level >= 4 and has_children:
                # 4级及以上，有子节点的排除
                if debug_mode:
                    print(f"❌ 排除: [{level}级] {numbering} {item['title'][:50]}... (有子章节)")
        
        if debug_mode:
            print(f"\n📊 第二步过滤结果: {len(step1_filtered)} -> {len(step2_filtered)} 项")
        
        return step2_filtered
    
    def _build_hierarchy_map(self, items: List[Dict[str, Any]]) -> Dict[str, Dict]:
        """构建层级关系映射"""
        
        hierarchy_map = {}
        
        # 初始化节点
        for item in items:
            numbering = item.get('numbering', '')
            level = item.get('level', 0)
            hierarchy_map[numbering] = {
                'item': item,
                'level': level,
                'children': []
            }
        
        # 建立父子关系
        for numbering, node in hierarchy_map.items():
            parts = numbering.split('.')
            if len(parts) > 1:
                # 找父节点
                parent_parts = parts[:-1]
                parent_numbering = '.'.join(parent_parts)
                if parent_numbering in hierarchy_map:
                    hierarchy_map[parent_numbering]['children'].append(numbering)
        
        return hierarchy_map
    
    def _generate_filter_result(self, original_items: List[Dict[str, Any]], 
                               step1_filtered: List[Dict[str, Any]], 
                               step2_filtered: List[Dict[str, Any]], 
                               debug_mode: bool) -> Dict[str, Any]:
        """生成过滤结果"""
        
        # 统计级别分布
        level_distribution = {}
        for item in step2_filtered:
            level = item.get('level', 0)
            level_distribution[level] = level_distribution.get(level, 0) + 1
        
        # 分类统计
        functional_requirements = []  # 功能需求 (3.2.x的具体功能)
        sub_functions = []           # 子功能 (4级及以上的叶子节点)
        
        for item in step2_filtered:
            level = item.get('level', 0)
            numbering = item.get('numbering', '')
            
            if level == 3 and numbering.startswith('3.2.'):
                functional_requirements.append(item)
            elif level >= 4:
                sub_functions.append(item)
        
        result = {
            'success': True,
            'total_count': len(step2_filtered),
            'level_distribution': level_distribution,
            'catalog_items': step2_filtered,
            'functional_requirements_count': len(functional_requirements),
            'sub_functions_count': len(sub_functions),
            'functional_requirements': functional_requirements,
            'sub_functions': sub_functions,
            'filter_info': {
                'original_count': len(original_items),
                'after_3_2_filter': len(step1_filtered),
                'after_leaf_filter': len(step2_filtered),
                'filtered_out_count': len(original_items) - len(step2_filtered)
            }
        }
        
        if debug_mode:
            self._print_filter_statistics(result)
        
        return result
    
    def _print_filter_statistics(self, result: Dict[str, Any]):
        """打印过滤统计信息"""
        
        print("\n" + "="*60)
        print("📈 过滤统计结果")
        print("="*60)
        print(f"原始目录项: {result['filter_info']['original_count']}")
        print(f"3.2.x过滤后: {result['filter_info']['after_3_2_filter']}")
        print(f"叶子节点过滤后: {result['filter_info']['after_leaf_filter']}")
        print(f"过滤掉: {result['filter_info']['filtered_out_count']} 项")
        print(f"\n功能需求(3级): {result['functional_requirements_count']} 项")
        print(f"子功能(4级+): {result['sub_functions_count']} 项")
        print(f"级别分布: {result['level_distribution']}")


def extract_testing_requirements_with_spire(docx_path: str, debug_mode: bool = False) -> Dict[str, Any]:
    """
    提取测试需求目录（专用于测试需求）
    
    先完整提取目录，然后进行专门的过滤：
    1. 只保留3.2.x开头的目录项
    2. 对于4级及以上级别，删除有子章节的需求项，只保留叶子节点需求
    
    Args:
        docx_path: DOCX文件路径
        debug_mode: 是否启用调试模式
        
    Returns:
        过滤后的测试需求结果字典
    """
    
    # 导入需要延迟以避免循环导入
    from .catalog_extractor import extract_catalog_with_spire
    
    try:
        # 第一步：完整提取目录
        if debug_mode:
            print("🚀 第一阶段：完整目录提取")
            print("-" * 40)
        
        full_result = extract_catalog_with_spire(docx_path, debug_mode)
        
        if not full_result['success']:
            return full_result
        
        # 第二步：应用测试需求过滤
        if debug_mode:
            print("\n🔄 第二阶段：测试需求过滤")
            print("-" * 40)
        
        catalog_filter = CatalogFilter(debug_mode)
        filtered_result = catalog_filter.filter_for_testing(
            full_result['catalog_items'], 
            debug_mode
        )
        
        # 合并结果信息
        filtered_result['original_extraction'] = {
            'total_count': full_result['total_count'],
            'level_distribution': full_result['level_distribution']
        }
        
        return filtered_result
        
    except Exception as e:
        return {
            'success': False,
            'message': f'提取测试需求失败: {str(e)}',
            'total_count': 0,
            'catalog_items': []
        } 