#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
可靠性测试项生成器

基于hanshutiqu_kaifa项目中的可靠性测试用例，
生成标准化的可靠性测试项。
"""

import logging
from typing import Dict, Any, List

# 导入日志工具
from .....utils.logging_utils.logger import log_info, log_debug, log_error, log_warning

logger = logging.getLogger(__name__)


class ReliabilityTestGenerator:
    """可靠性测试项生成器"""
    
    def __init__(self):
        """初始化可靠性测试生成器"""
        self.logger = logger
        
    def create_reliability_tests(self, basic_info: Dict[str, Any], current_test_count: int) -> List[Dict[str, Any]]:
        """
        创建可靠性测试项
        
        Args:
            basic_info: 基础信息
            current_test_count: 当前测试项数量
            
        Returns:
            List[Dict[str, Any]]: 可靠性测试项列表
        """
        try:
            log_info(f"[RELIABILITY_TEST] 开始创建可靠性测试项，当前测试项数量: {current_test_count}", "reliability_test_generator")
            
            # 🔧 基于hanshutiqu_kaifa项目的可靠性测试定义
            reliability_tests = [
                {
                    'name': '可靠性测试-代码数初始化审查',
                    'requirement': '软件应对所有变量进行初始化，确保可靠性满足设计要求',
                    'test_description': '测试软件的可靠性是否满足设计要求，是否对所有变量进行初始化。',
                    'test_method': '静态测试完成后，使用静态代码扫描工具对代码进行扫描，测试软件是否对所有变量进行初始化。'
                }
            ]
            
            reliability_test_items = []
            base_identifier = basic_info.get('base_identifier', 'CT-UNKNOWN')
            software_name = basic_info.get('software_name', '软件')
            
            for i, reliability_def in enumerate(reliability_tests, 1):
                # 生成可靠性测试项标识符 (按要求格式: CT-软件标识-版本-ReliabilityTest-RT01)
                reliability_identifier = f"{base_identifier}-ReliabilityTest-RT{i:02d}"
                
                # 创建可靠性测试项
                reliability_item = {
                    'index': current_test_count + i,
                    'name': reliability_def['name'],
                    'pure_name': reliability_def['name'],
                    'test_item_name': reliability_def['name'],
                    'test_item_identifier': reliability_identifier,
                    'english_identifier': 'ReliabilityTest',  # 🔧 添加英文标识
                    'test_type': '功能测试',  # 🔧 修改为功能测试
                    'software_name': basic_info.get('software_name', '软件'),  # 🔧 添加软件名称
                    'software_version': basic_info.get('software_version', '1.0'),  # 🔧 添加软件版本
                    'requirement_description': reliability_def['requirement'],  # 🔧 需求描述
                    'requirement_sub_description': reliability_def['requirement'],  # 🔧 需求子项描述
                    'test_description': reliability_def['test_description'],  # 🔧 测试描述
                    'test_method': reliability_def['test_method'],
                    'task_requirement_trace': f"《{software_name}需求规格说明》 典型需求",  # 🔧 任务需求追踪
                    'software_requirement_trace': f"《{software_name}需求规格说明》 典型需求",  # 🔧 软件需求追踪
                    'requirements_source': '固定可靠性测试',
                    'tracking_info': '默认可靠性测试',
                    'chapter_number': '',
                    'adequacy_requirement': '所有可靠性测试用例执行完毕，对于未执行的用例说明未执行原因',
                    'pass_criteria': '各测试步骤、测试用例执行结果与预期一致，可靠性指标满足要求',
                    'created_method': 'fixed_reliability_test',
                    '_is_reliability_test': True  # 标记为可靠性测试项
                }
                
                reliability_test_items.append(reliability_item)
                log_debug(f"创建可靠性测试项: {reliability_def['name']}", "reliability_test_generator")
            
            log_info(f"[RELIABILITY_TEST] 可靠性测试项创建完成，共{len(reliability_test_items)}项", "reliability_test_generator")
            return reliability_test_items
            
        except Exception as e:
            log_error(f"[RELIABILITY_TEST] 创建可靠性测试项失败: {e}", "reliability_test_generator")
            import traceback
            log_error(f"[RELIABILITY_TEST] 错误详情: {traceback.format_exc()}", "reliability_test_generator")
            return []
    
    def is_reliability_test_item(self, test_item: Dict[str, Any]) -> bool:
        """
        判断是否为可靠性测试项
        
        Args:
            test_item: 测试项字典
            
        Returns:
            bool: 是否为可靠性测试项
        """
        test_type = test_item.get('test_type', '')
        test_name = test_item.get('name', '')
        
        # 判断条件：测试类型为"可靠性测试"或测试名称包含"可靠"
        return (test_type == '可靠性测试' or 
                '可靠' in test_name or 
                test_item.get('_is_reliability_item', False)) 