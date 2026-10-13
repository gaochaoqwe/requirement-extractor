#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
可维护性测试项生成器

基于hanshutiqu_kaifa项目中的可维护性测试用例，
生成标准化的可维护性测试项。
"""

import logging
from typing import Dict, Any, List

# 导入日志工具
from .....utils.logging_utils.logger import log_info, log_debug, log_error, log_warning

logger = logging.getLogger(__name__)


class MaintainabilityTestGenerator:
    """可维护性测试项生成器"""
    
    def __init__(self):
        """初始化可维护性测试生成器"""
        self.logger = logger
        
    def create_maintainability_tests(self, basic_info: Dict[str, Any], current_test_count: int) -> List[Dict[str, Any]]:
        """
        创建可维护性测试项
        
        Args:
            basic_info: 基础信息
            current_test_count: 当前测试项数量
            
        Returns:
            List[Dict[str, Any]]: 可维护性测试项列表
        """
        try:
            log_info(f"[MAINTAINABILITY_TEST] 开始创建可维护性测试项，当前测试项数量: {current_test_count}", "maintainability_test_generator")
            
            # 🔧 基于hanshutiqu_kaifa项目的可维护性测试定义
            maintainability_tests = [
                {
                    'name': '可维护测试-代码注释率',
                    'requirement': '软件的注释率应满足大于20%的需求',
                    'test_description': '测试软件的注释率是否满足大于20%的需求。',
                    'test_method': '使用静态代码分析工具对软件进行扫描，查看其代码注释率是否高于20%。'
                }
            ]
            
            maintainability_test_items = []
            base_identifier = basic_info.get('base_identifier', 'CT-UNKNOWN')
            software_name = basic_info.get('software_name', '软件')
            
            for i, maintainability_def in enumerate(maintainability_tests, 1):
                # 生成可维护性测试项标识符 (按要求格式: CT-软件标识-版本-MaintainabilityTest-MT01)
                maintainability_identifier = f"{base_identifier}-MaintainabilityTest-MT{i:02d}"
                
                # 创建可维护性测试项
                maintainability_item = {
                    'index': current_test_count + i,
                    'name': maintainability_def['name'],
                    'pure_name': maintainability_def['name'],
                    'test_item_name': maintainability_def['name'],
                    'test_item_identifier': maintainability_identifier,
                    'english_identifier': 'MaintainabilityTest',  # 🔧 添加英文标识
                    'test_type': '功能测试',  # 🔧 修改为功能测试
                    'software_name': basic_info.get('software_name', '软件'),  # 🔧 添加软件名称
                    'software_version': basic_info.get('software_version', '1.0'),  # 🔧 添加软件版本
                    'requirement_description': maintainability_def['requirement'],  # 🔧 需求描述
                    'requirement_sub_description': maintainability_def['requirement'],  # 🔧 需求子项描述
                    'test_description': maintainability_def['test_description'],  # 🔧 测试描述
                    'test_method': maintainability_def['test_method'],
                    'task_requirement_trace': f"《{software_name}需求规格说明》 典型需求",  # 🔧 任务需求追踪
                    'software_requirement_trace': f"《{software_name}需求规格说明》 典型需求",  # 🔧 软件需求追踪
                    'requirements_source': '固定可维护性测试',
                    'tracking_info': '默认可维护性测试',
                    'chapter_number': '',
                    'adequacy_requirement': '所有可维护性测试用例执行完毕，对于未执行的用例说明未执行原因',
                    'pass_criteria': '各测试步骤、测试用例执行结果与预期一致，可维护性指标满足要求',
                    'created_method': 'fixed_maintainability_test',
                    '_is_maintainability_test': True  # 标记为可维护性测试项
                }
                
                maintainability_test_items.append(maintainability_item)
                log_debug(f"创建可维护性测试项: {maintainability_def['name']}", "maintainability_test_generator")
            
            log_info(f"[MAINTAINABILITY_TEST] 可维护性测试项创建完成，共{len(maintainability_test_items)}项", "maintainability_test_generator")
            return maintainability_test_items
            
        except Exception as e:
            log_error(f"[MAINTAINABILITY_TEST] 创建可维护性测试项失败: {e}", "maintainability_test_generator")
            import traceback
            log_error(f"[MAINTAINABILITY_TEST] 错误详情: {traceback.format_exc()}", "maintainability_test_generator")
            return []
    
    def is_maintainability_test_item(self, test_item: Dict[str, Any]) -> bool:
        """
        判断是否为可维护性测试项
        
        Args:
            test_item: 测试项字典
            
        Returns:
            bool: 是否为可维护性测试项
        """
        test_type = test_item.get('test_type', '')
        test_name = test_item.get('name', '')
        
        # 判断条件：测试类型为"可维护性测试"或测试名称包含"可维护"
        return (test_type == '可维护性测试' or 
                '可维护' in test_name or 
                test_item.get('_is_maintainability_item', False)) 