#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
组织资产数据库检索增强模块

用于在AI内容生成前检索组织资产数据库，将匹配的测试项分析内容作为提示词增强
"""

import sqlite3
import os
import traceback
from typing import List, Dict, Any, Optional, Tuple
from difflib import SequenceMatcher
import logging

# 导入统一日志工具（使用绝对导入，避免相对导入层级错误）
from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import (
    log_info,
    log_debug,
    log_warning,
    log_error,
)


class AssetDatabaseEnhancer:
    """组织资产数据库检索增强器"""
    
    def __init__(self):
        """初始化组织资产数据库检索增强器"""
        self.logger_name = "asset_database_enhancer"
        
        # 组织资产数据库路径
        self.asset_db_path = os.path.join(
            os.path.dirname(__file__), 
            "..", "..", "..", "..", "..", "..", 
            "databaseManage", "dynamicDatabaseManage", "db", "asset_management.db"
        )
        
        # 规范化路径
        self.asset_db_path = os.path.normpath(self.asset_db_path)
        
        # 模糊匹配相似度阈值
        self.similarity_threshold = 0.6
        
        log_info(f"[ASSET_DB] 初始化组织资产数据库检索增强器", self.logger_name)
        log_debug(f"[ASSET_DB] 数据库路径: {self.asset_db_path}", self.logger_name)
    
    def enhance_prompt_with_asset_data(self, test_item_name: str, original_prompt: str, product_type: str = None) -> str:
        """
        使用组织资产数据库检索结果增强AI提示词
        
        Args:
            test_item_name: 测试项名称
            original_prompt: 原始提示词
            product_type: 产品类型（转塔、对抗告警、光电雷达、吊舱、火控、外挂、显示）
            
        Returns:
            str: 增强后的提示词
        """
        try:
            log_info(f"[ASSET_DB_ENHANCE] ========== 开始为测试项增强提示词 ==========", self.logger_name)
            log_info(f"[ASSET_DB_ENHANCE] 测试项名称: '{test_item_name}'", self.logger_name)
            log_info(f"[ASSET_DB_ENHANCE] 产品类型: '{product_type}'", self.logger_name)
            log_info(f"[ASSET_DB_ENHANCE] 原始提示词长度: {len(original_prompt)} 字符", self.logger_name)
            
            # 1. 检索匹配的组织资产数据
            matched_groups = self._search_similar_test_items(test_item_name, product_type)
            
            if not matched_groups:
                log_warning(f"[ASSET_DB_ENHANCE] ✗ 未找到匹配的组织资产数据: '{test_item_name}'", self.logger_name)
                log_info(f"[ASSET_DB_ENHANCE] 返回原始提示词（未增强）", self.logger_name)
                return original_prompt
            
            total_records = sum(len(group['items']) for group in matched_groups)
            log_info(f"[ASSET_DB_ENHANCE] ✓ 找到 {len(matched_groups)} 个匹配的测试项组，共 {total_records} 条记录", self.logger_name)
            
            # 2. 构建增强内容
            enhancement_content = self._build_enhancement_content(matched_groups, test_item_name)
            
            # 3. 合并到原始提示词中
            enhanced_prompt = self._merge_enhancement_to_prompt(original_prompt, enhancement_content)
            
            log_info(f"[ASSET_DB_ENHANCE] ✓ 提示词增强完成", self.logger_name)
            log_info(f"[ASSET_DB_ENHANCE] 增强内容长度: {len(enhancement_content)} 字符", self.logger_name)
            log_info(f"[ASSET_DB_ENHANCE] 最终提示词长度: {len(enhanced_prompt)} 字符", self.logger_name)
            log_info(f"[ASSET_DB_ENHANCE] ========================================", self.logger_name)
            return enhanced_prompt
            
        except Exception as e:
            log_error(f"[ASSET_DB] 提示词增强失败: {e}", self.logger_name)
            import traceback
            log_error(f"[ASSET_DB] 错误详情: {traceback.format_exc()}", self.logger_name)
            return original_prompt
    
    def get_matched_database_content(self, test_item_name: str, product_type: str = None) -> Tuple[List[str], List[str]]:
        """
        获取匹配的数据库测试内容和测试方法
        
        Args:
            test_item_name: 测试项名称
            product_type: 产品类型（转塔、对抗告警、光电雷达、吊舱、火控、外挂、显示）
            
        Returns:
            Tuple[List[str], List[str]]: (测试内容列表, 测试方法列表)
        """
        test_descriptions, test_methods = self._get_matched_database_content_internal(test_item_name, product_type)
        return test_descriptions, test_methods
    
    def get_matched_database_templates(self, test_item_name: str, product_type: str = None) -> Tuple[str, str, str, bool]:
        """
        获取匹配的数据库用例模板（用例名称、输入条件和预期结果）
        ⚠️ 已废弃：请使用 get_matched_templates_for_test_case 或 get_matched_content_for_requirement_analysis
        
        Args:
            test_item_name: 测试项名称或测试条目内容
            product_type: 产品类型（转塔、对抗告警、光电雷达、吊舱、火控、外挂、显示）
            
        Returns:
            Tuple[str, str, str, bool]: (用例名称模板, 输入条件模板, 预期结果模板, 是否匹配到数据库)
        """
        try:
            log_info(f"[ASSET_DB_TEMPLATE] ========== 获取数据库用例模板 ==========", self.logger_name)
            log_info(f"[ASSET_DB_TEMPLATE] 测试内容: '{test_item_name[:100]}...'", self.logger_name)
            log_info(f"[ASSET_DB_TEMPLATE] 产品类型: '{product_type}'", self.logger_name)
            
            # 1. 基于测试内容相似度进行匹配
            matched_item = self._search_by_content_similarity(test_item_name, product_type)
            
            if not matched_item:
                log_warning(f"[ASSET_DB_TEMPLATE] ✗ 未找到匹配的数据库内容", self.logger_name)
                return "", "", "", False
            
            # 2. 获取匹配项的模板信息
            name_template = matched_item.get('case_template_name', '') or ''
            input_template = matched_item.get('case_template_input', '') or ''
            expected_template = matched_item.get('case_template_expected', '') or ''
            
            log_info(f"[ASSET_DB_TEMPLATE] ✓ 找到匹配: '{matched_item.get('test_content', '')[:50]}...'", self.logger_name)
            log_info(f"[ASSET_DB_TEMPLATE] ✓ 模板信息: 用例名称长度={len(name_template)}, 输入条件长度={len(input_template)}, 预期结果长度={len(expected_template)}", self.logger_name)
            log_info(f"[ASSET_DB_TEMPLATE] ==========================================", self.logger_name)
            
            # 如果输入条件和预期结果模板都不为空，则认为匹配成功
            is_matched = bool(input_template.strip() and expected_template.strip())
            return name_template, input_template, expected_template, is_matched
            
        except Exception as e:
            log_error(f"[ASSET_DB_TEMPLATE] 获取数据库模板失败: {e}", self.logger_name)
            import traceback
            log_error(f"[ASSET_DB_TEMPLATE] 错误详情: {traceback.format_exc()}", self.logger_name)
            return "", "", "", False
    
    def get_matched_templates_for_test_case(self, test_description: str, product_type: str = None) -> Tuple[str, str, str, bool]:
        """
        为测试用例单获取匹配的数据库模板（基于测试描述匹配测试内容）
        
        Args:
            test_description: 测试描述（来自测试用例单的测试描述列）
            product_type: 产品类型（转塔、对抗告警、光电雷达、吊舱、火控、外挂、显示）
            
        Returns:
            Tuple[str, str, str, bool]: (用例名称模板, 输入条件模板, 预期结果模板, 是否匹配到数据库)
        """
        try:
            log_info(f"[TEST_CASE_TEMPLATE] ========== 为测试用例单获取数据库模板 ==========", self.logger_name)
            log_info(f"[TEST_CASE_TEMPLATE] 测试描述: '{test_description[:100]}...'", self.logger_name)
            log_info(f"[TEST_CASE_TEMPLATE] 产品类型: '{product_type}'", self.logger_name)
            
            # 基于测试内容相似度进行匹配（不匹配测试项名称）
            matched_item = self._search_by_content_similarity(test_description, product_type)
            
            if not matched_item:
                log_warning(f"[TEST_CASE_TEMPLATE] ✗ 未找到匹配的数据库内容", self.logger_name)
                return "", "", "", False
            
            # 获取匹配项的模板信息
            name_template = matched_item.get('case_template_name', '') or ''
            input_template = matched_item.get('case_template_input', '') or ''
            expected_template = matched_item.get('case_template_expected', '') or ''
            
            log_info(f"[TEST_CASE_TEMPLATE] ✓ 找到匹配: '{matched_item.get('test_content', '')[:50]}...'", self.logger_name)
            log_info(f"[TEST_CASE_TEMPLATE] ✓ 模板信息: 用例名称长度={len(name_template)}, 输入条件长度={len(input_template)}, 预期结果长度={len(expected_template)}", self.logger_name)
            log_info(f"[TEST_CASE_TEMPLATE] ==========================================", self.logger_name)
            
            # 如果输入条件和预期结果模板都不为空，则认为匹配成功
            is_matched = bool(input_template.strip() and expected_template.strip())
            return name_template, input_template, expected_template, is_matched
            
        except Exception as e:
            log_error(f"[TEST_CASE_TEMPLATE] 获取数据库模板失败: {e}", self.logger_name)
            import traceback
            log_error(f"[TEST_CASE_TEMPLATE] 错误详情: {traceback.format_exc()}", self.logger_name)
            return "", "", "", False
    
    def get_matched_content_for_requirement_analysis(self, test_item_name: str, product_type: str = None) -> Tuple[str, str, bool]:
        """
        为需求分析表获取匹配的数据库内容（基于测试项名称匹配，支持||分隔的多名称）
        
        Args:
            test_item_name: 测试项名称（来自需求分析表）
            product_type: 产品类型（转塔、对抗告警、光电雷达、吊舱、火控、外挂、显示）
            
        Returns:
            Tuple[str, str, bool]: (测试内容, 测试方法, 是否匹配到数据库)
        """
        try:
            log_info(f"[REQUIREMENT_ANALYSIS] ========== 为需求分析表获取数据库内容 ==========", self.logger_name)
            log_info(f"[REQUIREMENT_ANALYSIS] 测试项名称: '{test_item_name[:100]}...'", self.logger_name)
            log_info(f"[REQUIREMENT_ANALYSIS] 产品类型: '{product_type}'", self.logger_name)
            
            # 基于测试项名称相似度进行匹配（支持||分隔的多名称）
            matched_item = self._search_by_test_item_name_similarity(test_item_name, product_type)
            
            if not matched_item:
                log_warning(f"[REQUIREMENT_ANALYSIS] ✗ 未找到匹配的测试项名称", self.logger_name)
                return "", "", False
            
            # 获取匹配项的内容信息
            test_content = matched_item.get('test_content', '') or ''
            test_method = matched_item.get('test_method', '') or ''
            
            log_info(f"[REQUIREMENT_ANALYSIS] ✓ 找到匹配: '{matched_item.get('test_item_name', '')[:50]}...'", self.logger_name)
            log_info(f"[REQUIREMENT_ANALYSIS] ✓ 内容信息: 测试内容长度={len(test_content)}, 测试方法长度={len(test_method)}", self.logger_name)
            log_info(f"[REQUIREMENT_ANALYSIS] ==========================================", self.logger_name)
            
            # 如果测试内容和测试方法都不为空，则认为匹配成功
            is_matched = bool(test_content.strip() and test_method.strip())
            return test_content, test_method, is_matched
            
        except Exception as e:
            log_error(f"[REQUIREMENT_ANALYSIS] 获取数据库内容失败: {e}", self.logger_name)
            import traceback
            log_error(f"[REQUIREMENT_ANALYSIS] 错误详情: {traceback.format_exc()}", self.logger_name)
            return "", "", False
    
    def _search_by_content_similarity(self, test_content: str, product_type: str = None) -> Dict[str, Any]:
        """
        基于测试内容相似度搜索数据库记录（专用于测试用例单填充）
        
        Args:
            test_content: 测试内容（来自测试用例单的测试描述列）
            product_type: 产品类型
            
        Returns:
            Dict: 最匹配的数据库记录，如果没有匹配则返回None
        """
        try:
            # 检查数据库文件是否存在
            if not os.path.exists(self.asset_db_path):
                log_warning(f"[ASSET_DB] 组织资产数据库不存在: {self.asset_db_path}", self.logger_name)
                return None
            
            # 连接数据库
            conn = sqlite3.connect(self.asset_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 根据产品类型确定要查询的表
            table_name = self._get_table_name_by_product_type(product_type)
            if not table_name:
                log_warning(f"[ASSET_DB_SEARCH] 未知的产品类型: '{product_type}', 无法确定数据表", self.logger_name)
                conn.close()
                return None
            
            # 查询所有测试内容
            query = f"""
                SELECT test_item_name, test_content, test_method, 
                       case_template_name, case_template_input, case_template_expected 
                FROM {table_name} 
                WHERE test_content IS NOT NULL AND test_content != ''
                  AND case_template_input IS NOT NULL AND case_template_input != ''
                  AND case_template_expected IS NOT NULL AND case_template_expected != ''
            """
            
            cursor.execute(query)
            all_items = cursor.fetchall()
            conn.close()
            
            if not all_items:
                log_warning(f"[ASSET_DB_SEARCH] 数据表 '{table_name}' 中没有完整的测试内容和模板数据", self.logger_name)
                return None
            
            log_info(f"[ASSET_DB_SEARCH] 从数据表 '{table_name}' 获取到 {len(all_items)} 个完整记录", self.logger_name)
            
            # 清理输入的测试内容（去掉编号）
            clean_test_content = self._clean_test_content(test_content)
            
            # 计算与每个数据库记录的相似度
            best_match = None
            best_similarity = 0.0
            
            for item in all_items:
                # 仅基于测试内容的相似度匹配（测试用例单填充专用）
                db_content = item['test_content'] or ''
                clean_db_content = self._clean_test_content(db_content)
                similarity = self._calculate_similarity(clean_test_content, clean_db_content)
                
                log_debug(f"[CONTENT_MATCH] 内容相似度: {similarity:.3f} | 输入: '{clean_test_content[:30]}...' | 数据库内容: '{clean_db_content[:30]}...'", self.logger_name)
                
                if similarity > best_similarity and similarity >= self.similarity_threshold:
                    best_similarity = similarity
                    best_match = {
                        'test_item_name': item['test_item_name'],
                        'test_content': item['test_content'],
                        'test_method': item['test_method'],
                        'case_template_name': item['case_template_name'],
                        'case_template_input': item['case_template_input'],
                        'case_template_expected': item['case_template_expected'],
                        'similarity': similarity,
                        'match_type': 'content'
                    }
            
            if best_match:
                log_info(f"[CONTENT_MATCH] ✓ 找到最佳匹配: 相似度={best_similarity:.3f}", self.logger_name)
                return best_match
            else:
                log_info(f"[CONTENT_MATCH] ✗ 未找到相似度 >= {self.similarity_threshold} 的匹配", self.logger_name)
                return None
                
        except Exception as e:
            log_error(f"[CONTENT_MATCH] 内容相似度搜索失败: {e}", self.logger_name)
            return None
    
    def _search_by_test_item_name_similarity(self, test_item_name: str, product_type: str = None) -> Dict[str, Any]:
        """
        基于测试项名称相似度搜索数据库记录（专用于需求分析表填充）
        
        Args:
            test_item_name: 测试项名称（来自需求分析表）
            product_type: 产品类型
            
        Returns:
            Dict: 最匹配的数据库记录，如果没有匹配则返回None
        """
        try:
            # 检查数据库文件是否存在
            if not os.path.exists(self.asset_db_path):
                log_warning(f"[ASSET_DB] 组织资产数据库不存在: {self.asset_db_path}", self.logger_name)
                return None
            
            # 连接数据库
            conn = sqlite3.connect(self.asset_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 根据产品类型确定要查询的表
            table_name = self._get_table_name_by_product_type(product_type)
            if not table_name:
                log_warning(f"[ASSET_DB_SEARCH] 未知的产品类型: '{product_type}', 无法确定数据表", self.logger_name)
                conn.close()
                return None
            
            # 查询所有测试项名称
            query = f"""
                SELECT test_item_name, test_content, test_method, 
                       case_template_name, case_template_input, case_template_expected 
                FROM {table_name} 
                WHERE test_item_name IS NOT NULL AND test_item_name != ''
                  AND test_content IS NOT NULL AND test_content != ''
                  AND test_method IS NOT NULL AND test_method != ''
            """
            
            cursor.execute(query)
            all_items = cursor.fetchall()
            conn.close()
            
            if not all_items:
                log_warning(f"[ASSET_DB_SEARCH] 数据表 '{table_name}' 中没有完整的测试项数据", self.logger_name)
                return None
            
            log_info(f"[ASSET_DB_SEARCH] 从数据表 '{table_name}' 获取到 {len(all_items)} 个完整记录", self.logger_name)
            
            # 计算与每个数据库记录的相似度
            best_match = None
            best_similarity = 0.0
            
            for item in all_items:
                # 仅基于测试项名称的相似度匹配（需求分析表填充专用，支持||分隔的多名称）
                db_item_name = item['test_item_name'] or ''
                similarity = self._calculate_similarity(test_item_name, db_item_name)
                
                log_debug(f"[NAME_MATCH] 名称相似度: {similarity:.3f} | 输入: '{test_item_name[:30]}...' | 数据库名称: '{db_item_name[:30]}...'", self.logger_name)
                
                if similarity > best_similarity and similarity >= self.similarity_threshold:
                    best_similarity = similarity
                    best_match = {
                        'test_item_name': item['test_item_name'],
                        'test_content': item['test_content'],
                        'test_method': item['test_method'],
                        'case_template_name': item['case_template_name'],
                        'case_template_input': item['case_template_input'],
                        'case_template_expected': item['case_template_expected'],
                        'similarity': similarity,
                        'match_type': 'name'
                    }
            
            if best_match:
                log_info(f"[NAME_MATCH] ✓ 找到最佳匹配: 相似度={best_similarity:.3f}", self.logger_name)
                return best_match
            else:
                log_info(f"[NAME_MATCH] ✗ 未找到相似度 >= {self.similarity_threshold} 的匹配", self.logger_name)
                return None
                
        except Exception as e:
            log_error(f"[NAME_MATCH] 测试项名称相似度搜索失败: {e}", self.logger_name)
            return None
    
    def _clean_test_content(self, content: str) -> str:
        """
        清理测试内容，去掉编号和特殊字符，便于相似度比较
        
        Args:
            content: 原始测试内容
            
        Returns:
            str: 清理后的内容
        """
        import re
        
        if not content:
            return ""
        
        # 去掉开头的编号（如"1、"、"2."、"（1）"等）
        cleaned = re.sub(r'^[\s\d、．\.\(\)（）]*', '', content.strip())
        
        # 去掉多余的空白字符
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned.strip()
    
    def _get_matched_database_content_internal(self, test_item_name: str, product_type: str = None) -> Tuple[List[str], List[str]]:
        """
        内部方法：获取匹配的数据库内容
        
        Args:
            test_item_name: 测试项名称
            product_type: 产品类型
            
        Returns:
            Tuple[List[str], List[str]]: (测试内容列表, 测试方法列表)
        """
        try:
            # 搜索相似的测试项
            matched_groups = self._search_similar_test_items(test_item_name, product_type)
            
            if not matched_groups:
                log_info(f"[ASSET_DB] 未找到匹配的测试项: '{test_item_name}'", self.logger_name)
                return [], []
            
            # 提取最匹配组的内容
            best_match = matched_groups[0]
            test_contents = []
            test_methods = []
            
            log_info(f"[ASSET_DB] 使用最佳匹配: '{best_match['test_item_name']}' (相似度: {best_match['similarity']:.3f})", self.logger_name)
            
            for i, item in enumerate(best_match['items'], 1):
                content = item.get('test_content', '').strip()
                method = item.get('test_method', '').strip()
                
                if content:
                    # 🔧 新增：为组织资产库内容添加来源标记
                    marked_content = f"[DB_SOURCE]{content}"
                    test_contents.append(marked_content)
                    log_debug(f"[ASSET_DB] 添加测试内容 {i}: {content[:50]}...", self.logger_name)
                
                if method:
                    # 🔧 新增：为组织资产库方法添加来源标记
                    marked_method = f"[DB_SOURCE]{method}"
                    test_methods.append(marked_method)
                    log_debug(f"[ASSET_DB] 添加测试方法 {i}: {method[:50]}...", self.logger_name)
            
            log_info(f"[ASSET_DB] 成功提取: {len(test_contents)} 个测试内容, {len(test_methods)} 个测试方法", self.logger_name)
            return test_contents, test_methods
            
        except Exception as e:
            log_error(f"[ASSET_DB] 获取匹配数据库内容失败: {e}\n{traceback.format_exc()}", self.logger_name)
            return [], []
    
    def _search_similar_test_items(self, test_item_name: str, product_type: str = None) -> List[Dict[str, Any]]:
        """
        基于测试项名称和产品类型进行模糊匹配搜索
        
        Args:
            test_item_name: 测试项名称
            product_type: 产品类型（转塔、对抗告警、光电雷达、吊舱、火控、外挂、显示）
            
        Returns:
            List[Dict]: 匹配的资产数据列表
        """
        try:
            # 检查数据库文件是否存在
            if not os.path.exists(self.asset_db_path):
                log_warning(f"[ASSET_DB] 组织资产数据库不存在: {self.asset_db_path}", self.logger_name)
                return []
            
            log_info(f"[ASSET_DB_SEARCH] 开始搜索相似测试项: '{test_item_name}', 产品类型: '{product_type}'", self.logger_name)
            
            # 连接数据库
            conn = sqlite3.connect(self.asset_db_path)
            conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
            cursor = conn.cursor()
            
            # 根据产品类型确定要查询的表
            table_name = self._get_table_name_by_product_type(product_type)
            if not table_name:
                log_warning(f"[ASSET_DB_SEARCH] 未知的产品类型: '{product_type}', 无法确定数据表", self.logger_name)
                conn.close()
                return []
            
            log_info(f"[ASSET_DB_SEARCH] 产品类型 '{product_type}' 映射到数据表: '{table_name}'", self.logger_name)
            
            # 查询指定表中的测试项
            query = f"""
                SELECT software_category, test_item_name, test_content, test_method, 
                       case_template_input, case_template_expected, submitter 
                FROM {table_name} 
                WHERE test_item_name IS NOT NULL AND test_item_name != ''
                ORDER BY software_category, category_order, item_order
            """
            
            cursor.execute(query)
            all_items = cursor.fetchall()
            conn.close()
            
            if not all_items:
                log_warning(f"[ASSET_DB_SEARCH] 数据表 '{table_name}' 中没有测试项数据", self.logger_name)
                return []
            
            log_info(f"[ASSET_DB_SEARCH] 从数据表 '{table_name}' 获取到 {len(all_items)} 个测试项记录", self.logger_name)
            
            # 按测试项名称分组
            grouped_items = {}
            for item in all_items:
                item_name = item['test_item_name']
                if item_name not in grouped_items:
                    grouped_items[item_name] = []
                grouped_items[item_name].append(item)
            
            log_info(f"[ASSET_DB_SEARCH] 测试项分组完成，共 {len(grouped_items)} 个不同的测试项名称", self.logger_name)
            
            # 进行模糊匹配
            matched_groups = []
            match_count = 0
            total_checked = 0
            
            for item_name, items in grouped_items.items():
                total_checked += 1
                similarity = self._calculate_similarity(test_item_name, item_name)
                
                log_debug(f"[ASSET_DB_MATCH] 检查相似度: '{test_item_name}' vs '{item_name}' = {similarity:.3f} (阈值: {self.similarity_threshold})", self.logger_name)
                
                if similarity >= self.similarity_threshold:
                    match_count += 1
                    # 将同一测试项的所有条目组合
                    matched_group = {
                        'test_item_name': item_name,
                        'similarity': similarity,
                        'items': []
                    }
                    
                    for item in items:
                        matched_group['items'].append({
                            'software_category': item['software_category'] or '',
                            'test_content': item['test_content'] or '',
                            'test_method': item['test_method'] or '',
                            'case_template_input': item['case_template_input'] or '',
                            'case_template_expected': item['case_template_expected'] or '',
                            'submitter': item['submitter'] or ''
                        })
                    
                    matched_groups.append(matched_group)
                    log_info(f"[ASSET_DB_MATCH] ✓ 匹配成功: '{item_name}' (相似度: {similarity:.3f}, {len(items)}条记录)", self.logger_name)
            
            # 按相似度排序
            matched_groups.sort(key=lambda x: x['similarity'], reverse=True)
            
            # 记录匹配统计信息
            log_info(f"[ASSET_DB_MATCH] 匹配统计: 检查了 {total_checked} 个测试项，找到 {match_count} 个匹配项", self.logger_name)
            
            if matched_groups:
                log_info(f"[ASSET_DB_MATCH] 最佳匹配: '{matched_groups[0]['test_item_name']}' (相似度: {matched_groups[0]['similarity']:.3f})", self.logger_name)
                for i, group in enumerate(matched_groups):
                    total_records = len(group['items'])
                    log_info(f"[ASSET_DB_MATCH] 第{i+1}名: '{group['test_item_name']}' - {total_records}条记录", self.logger_name)
            else:
                log_warning(f"[ASSET_DB_MATCH] ✗ 未找到相似度超过 {self.similarity_threshold} 的测试项", self.logger_name)
            
            # 限制返回数量（最多取最匹配的1个测试项的所有条目）
            matched_groups = matched_groups[:1]
            
            final_count = sum(len(group['items']) for group in matched_groups)
            log_info(f"[ASSET_DB_SEARCH] 搜索完成，返回 {len(matched_groups)} 个测试项组，共 {final_count} 条记录", self.logger_name)
            return matched_groups
            
        except Exception as e:
            log_error(f"[ASSET_DB] 搜索相似测试项失败: {e}", self.logger_name)
            return []
    
    def _get_table_name_by_product_type(self, product_type: str) -> str:
        """
        根据产品类型获取对应的数据表名
        
        Args:
            product_type: 产品类型
            
        Returns:
            str: 表名
        """
        table_mapping = {
            '转塔': 'turret_requirements',
            '对抗告警': 'countermeasure_alarm_requirements',
            '光电雷达': 'opto_radar_requirements',
            '吊舱': 'pod_requirements',
            '火控': 'fire_control_requirements',
            '外挂': 'external_requirements',
            '显示': 'display_requirements'
        }
        
        return table_mapping.get(product_type, '')
    
    def _calculate_similarity(self, name1: str, name2: str) -> float:
        """
        计算两个测试项名称的相似度
        支持处理包含 || 分隔符的多个名称
        
        Args:
            name1: 测试项名称1（输入的需求名称）
            name2: 测试项名称2（数据库中的测试项名称，可能包含 || 分隔的多个名称）
            
        Returns:
            float: 相似度 (0-1)
        """
        if not name1 or not name2:
            return 0.0
        
        # 清理输入名称
        clean_name1 = self._clean_test_name(name1.strip())
        
        # 检查name2是否包含多个名称（用||分隔）
        if '||' in name2:
            # 分割多个名称并计算与每个名称的相似度
            name2_variants = [variant.strip() for variant in name2.split('||') if variant.strip()]
            max_similarity = 0.0
            best_match_variant = ""
            
            log_debug(f"[SIMILARITY_MULTI] 检测到多名称格式: '{name2}' -> {len(name2_variants)} 个变体", self.logger_name)
            
            for variant in name2_variants:
                clean_variant = self._clean_test_name(variant)
                
                # 使用SequenceMatcher计算相似度
                similarity = SequenceMatcher(None, clean_name1, clean_variant).ratio()
                
                # 如果包含关键词匹配，提高相似度
                if self._has_keyword_match(clean_name1, clean_variant):
                    similarity = min(1.0, similarity + 0.2)
                
                log_debug(f"[SIMILARITY_VARIANT] '{clean_name1}' vs '{clean_variant}' = {similarity:.3f}", self.logger_name)
                
                if similarity > max_similarity:
                    max_similarity = similarity
                    best_match_variant = variant
            
            if max_similarity > 0:
                log_info(f"[SIMILARITY_MULTI] 最佳匹配变体: '{best_match_variant}' (相似度: {max_similarity:.3f})", self.logger_name)
            
            return max_similarity
        else:
            # 单一名称的情况，使用原有逻辑
            clean_name2 = self._clean_test_name(name2.strip())
            
            # 使用SequenceMatcher计算相似度
            similarity = SequenceMatcher(None, clean_name1, clean_name2).ratio()
            
            # 如果包含关键词匹配，提高相似度
            if self._has_keyword_match(clean_name1, clean_name2):
                similarity = min(1.0, similarity + 0.2)
            
            return similarity
    
    def _clean_test_name(self, name: str) -> str:
        """
        清理测试项名称，去除测试类型后缀
        
        Args:
            name: 原始测试项名称
            
        Returns:
            str: 清理后的名称
        """
        # 去除常见的测试类型后缀
        suffixes_to_remove = [
            '（性能测试）', '（边界测试）', '（接口测试）', '（功能测试）',
            '(性能测试)', '(边界测试)', '(接口测试)', '(功能测试)',
            '性能测试', '边界测试', '接口测试', '功能测试'
        ]
        
        cleaned_name = name
        for suffix in suffixes_to_remove:
            if cleaned_name.endswith(suffix):
                cleaned_name = cleaned_name[:-len(suffix)].strip()
        
        return cleaned_name
    
    def _has_keyword_match(self, name1: str, name2: str) -> bool:
        """
        检查两个名称是否有关键词匹配
        
        Args:
            name1: 名称1
            name2: 名称2
            
        Returns:
            bool: 是否有关键词匹配
        """
        # 提取关键词（长度大于1的词）
        keywords1 = set([word for word in name1 if len(word) > 1])
        keywords2 = set([word for word in name2 if len(word) > 1])
        
        # 检查是否有交集
        return len(keywords1.intersection(keywords2)) > 0
    
    def _build_enhancement_content(self, matched_groups: List[Dict[str, Any]], test_item_name: str) -> str:
        """
        构建增强内容
        
        Args:
            matched_groups: 匹配的测试项组列表
            test_item_name: 当前测试项名称
            
        Returns:
            str: 增强内容
        """
        if not matched_groups:
            return ""
        
        enhancement_parts = [
            "\n=== 数据库中的测试项内容 ===",
            f"以下是数据库中与'{test_item_name}'相似的测试项内容，请参考这些内容的格式进行测试内容和测试方法的生成：\n"
        ]
        
        # 构建与AI返回格式一致的test_pairs格式
        all_test_pairs = []
        for group in matched_groups:
            enhancement_parts.append(f"【匹配的测试项】{group['test_item_name']} (相似度: {group['similarity']:.1%})")
            enhancement_parts.append(f"该测试项在数据库中共有 {len(group['items'])} 条测试内容：\n")
            
            # 按test_pairs格式展示，为数据库内容添加编号
            for i, item in enumerate(group['items'], 1):
                test_content = item['test_content']
                test_method = item['test_method'] if item['test_method'] else ""
                
                # 清理数据库内容格式，移除"、"符号，确保格式为"1验证xxx"
                current_index = len(all_test_pairs) + 1
                
                # 处理测试内容：统一重新编号以确保连续性
                import re
                if test_content.strip().startswith(tuple('123456789')):
                    # 如果已有编号，先移除原编号和"、"符号，然后重新编号
                    test_content_clean = re.sub(r'^(\d+)、?', '', test_content).strip()
                    test_content = f"{current_index}{test_content_clean}"
                else:
                    # 如果没有编号，直接添加编号
                    test_content = f"{current_index}{test_content}"
                
                # 处理测试方法：统一重新编号以确保连续性
                if test_method:
                    if test_method.strip().startswith(tuple('123456789')):
                        # 如果已有编号，先移除原编号和"、"符号，然后重新编号
                        test_method_clean = re.sub(r'^(\d+)、?', '', test_method).strip()
                        test_method = f"{current_index}{test_method_clean}"
                    else:
                        # 如果没有编号，直接添加编号
                        test_method = f"{current_index}{test_method}"
                
                # 添加到test_pairs列表
                all_test_pairs.append({
                    "test_description": test_content,
                    "test_method": test_method
                })
                
                # 按JSON格式展示给AI，转义引号，使用test_description和test_method格式
                escaped_content = test_content.replace('"', '\\"')
                escaped_method = test_method.replace('"', '\\"')
                enhancement_parts.append(f'    {{"test_description": "{escaped_content}", "test_method": "{escaped_method}"}},')
            
            enhancement_parts.append("")  # 空行分隔
        
        # 计算总的数据库条目数
        total_db_items = sum(len(group['items']) for group in matched_groups)
        
        enhancement_parts.extend([
            "=== AI生成指导 ===",
            "**重要说明：请根据后续的需求内容来生成测试项描述和测试方法，而不是根据上述数据库内容**",
            "",
            "上述数据库内容仅用于参考，表示我们已经有了这些测试项。请你：",
            "1. 仔细分析后续提供的需求内容",
            "2. 根据需求内容识别需要测试的功能点",
            "3. 排除上述数据库中已经覆盖的测试内容",
            "4. 只生成数据库中没有覆盖到的其他测试项和测试方法",
            "",
            "生成要求：",
            f"- 数据库中已有{total_db_items}条内容，你生成的新内容应该从第{total_db_items + 1}条开始编号",
            "- 每条test_description和test_method都以数字开头（如：1验证xxx、2验证xxx）",
            "- 每条内容内部不能再有子编号，保持简洁",
            "- 确保新生成的内容不与数据库已有内容重复",
            "- 按照JSON格式生成：{\"test_description\": \"...\", \"test_method\": \"...\"}",
            "- 注意：你只需要生成测试内容和测试方法，不需要生成输入条件和预期结果",
            "=== 数据库内容结束 ===\n"
        ])
        
        return "\n".join(enhancement_parts)
    
    def _merge_enhancement_to_prompt(self, original_prompt: str, enhancement_content: str) -> str:
        """
        将增强内容合并到原始提示词中
        
        Args:
            original_prompt: 原始提示词（可能是字典或字符串）
            enhancement_content: 增强内容
            
        Returns:
            str: 合并后的提示词
        """
        if not enhancement_content:
            return str(original_prompt)
        
        # 确保original_prompt是字符串格式
        if isinstance(original_prompt, dict):
            # 如果是字典，转换为a) b) c)格式
            formatted_parts = []
            
            # a) 标识号
            identifier = original_prompt.get('identifier')
            if identifier:
                formatted_parts.append(f"a) 标识号：{identifier}")
            
            # b) 说明
            description = original_prompt.get('description')
            if description:
                formatted_parts.append(f"b) 说明：{description}")
            
            # c) 进入条件
            entry_condition = original_prompt.get('entry_condition')
            if entry_condition:
                formatted_parts.append(f"c) 进入条件：{entry_condition}")
            
            # d) 输入
            input_data = original_prompt.get('input')
            if input_data:
                formatted_parts.append(f"d) 输入：{input_data}")
            
            # e) 输出
            output_data = original_prompt.get('output')
            if output_data:
                formatted_parts.append(f"e) 输出：{output_data}")
            
            # f) 处理
            processing = original_prompt.get('processing')
            if processing:
                formatted_parts.append(f"f) 处理：{processing}")
            
            # g) 性能
            performance = original_prompt.get('performance')
            if performance:
                formatted_parts.append(f"g) 性能：{performance}")
            
            # h) 约束与限制
            constraints = original_prompt.get('constraints')
            if constraints:
                formatted_parts.append(f"h) 约束与限制：{constraints}")
            
            original_prompt_str = "\n".join(formatted_parts)
        else:
            original_prompt_str = str(original_prompt)
        
        # 在原始提示词前添加增强内容
        enhanced_prompt = f"{enhancement_content}\n{original_prompt_str}"
        
        return enhanced_prompt
    
    def test_database_connection(self, product_type: str = "转塔") -> bool:
        """
        测试数据库连接
        
        Args:
            product_type: 产品类型，用于测试对应的表
            
        Returns:
            bool: 连接是否成功
        """
        try:
            if not os.path.exists(self.asset_db_path):
                log_error(f"[ASSET_DB] 数据库文件不存在: {self.asset_db_path}", self.logger_name)
                return False
            
            conn = sqlite3.connect(self.asset_db_path)
            cursor = conn.cursor()
            
            # 测试查询指定产品类型的表
            table_name = self._get_table_name_by_product_type(product_type)
            if table_name:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                log_info(f"[ASSET_DB] 数据库连接成功，{product_type}表共有 {count} 条记录", self.logger_name)
            else:
                log_warning(f"[ASSET_DB] 未知的产品类型: {product_type}", self.logger_name)
                return False
            
            conn.close()
            return True
            
        except Exception as e:
            log_error(f"[ASSET_DB] 数据库连接失败: {e}", self.logger_name)
            return False


# 创建全局实例
asset_enhancer = AssetDatabaseEnhancer()
