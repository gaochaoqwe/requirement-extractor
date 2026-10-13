#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
余量测试项生成器

从原有的functional_test_creator.py中抽取余量测试生成逻辑，
提供独立的余量测试项生成功能。
"""

import logging
from typing import Dict, Any, List

# 导入日志工具
from .....utils.logging_utils.logger import log_info, log_debug, log_error, log_warning

# 导入英文标识生成器
from .english_identifier_generator import identifier_generator

logger = logging.getLogger(__name__)


class AllowanceTestGenerator:
    """余量测试项生成器"""
    
    def __init__(self):
        """初始化余量测试生成器"""
        self.logger = logger
        
    def create_fixed_allowance_tests(self, basic_info: Dict[str, Any], current_test_count: int) -> List[Dict[str, Any]]:
        """
        创建固定的余量测试项（基于hanshutiqu_kaifa项目的思路）
        
        Args:
            basic_info: 基础信息
            current_test_count: 当前测试项数量
            
        Returns:
            List[Dict[str, Any]]: 固定余量测试项列表
        """
        try:
            log_info(f"[ALLOWANCE_TEST] 开始创建余量测试项，当前测试项数量: {current_test_count}", "allowance_test_generator")
            
            # 🔧 固定的余量测试定义（增加需求描述字段，添加编号）
            fixed_allowance_tests = [
                {
                    'name': 'DDR内存余量',
                    'requirement_description': '软件的DDR内存余量需大于30%',
                    'description': '1测试软件的DDR内存余量是否满足需求大于30%的要求',
                    'test_method': '1查看软件DDR存储空间的大小，以及软件编译后的软件的大小，两者相除，即为DDR空间的占有率，用1减去这个数即为软件的DDR存储余量'
                },
                {
                    'name': 'FLASH内存余量',
                    'requirement_description': '软件的FLASH内存余量需大于30%',
                    'description': '1测试软件的FLASH内存余量是否满足需求大于30%的要求',
                    'test_method': '1软件通过代码审查计算软件，运行时需要占用的flash内存的大小，然后与FLASH的内存相除，用1减去这个数即为软件的FLASH存储余量'
                },
                {
                    'name': 'CPU余量',
                    'requirement_description': '软件的CPU运行余量需大于30%',
                    'description': '1测试软件的CPU运行余量是否满足需求大于30%的要求',
                    'test_method': '1软件正常运行，通过调试计算机中软件编译环境的内存监控功能查看软件的运行余量是否大于30%'
                }
            ]
            
            allowance_test_items = []
            base_identifier = basic_info.get('base_identifier', 'CT-UNKNOWN')
            software_name = basic_info.get('software_name', '软件')
            
            for i, allowance_def in enumerate(fixed_allowance_tests, 1):
                # 生成余量测试项标识符 (按要求格式: CT-软件标识-版本-AllowanceTest-AL01)
                allowance_identifier = f"{base_identifier}-AllowanceTest-AL{i:02d}"
                
                # 创建余量测试项（修复：正确的字段映射，符合测试项标准结构）
                allowance_item = {
                    'index': current_test_count + i,
                    'name': allowance_def['name'],
                    'pure_name': allowance_def['name'],
                    'test_item_name': allowance_def['name'],
                    'test_item_identifier': allowance_identifier,
                    'test_type': '余量测试',
                    'software_name': basic_info.get('software_name', '软件'),
                    'software_version': basic_info.get('software_version', '1.0'),
                    
                    # 🔧 修复：正确的字段映射
                    'requirement_description': allowance_def['requirement_description'],  # 需求描述
                    'requirement_sub_description': allowance_def['requirement_description'],  # 需求子项描述
                    'test_description': allowance_def['description'],  # 测试项描述（AI可能会覆盖）
                    'test_method': allowance_def['test_method'],  # 测试方法（AI可能会覆盖）
                    
                    # 标准测试项字段
                    'software_requirement_trace': '典型需求',
                    'chapter_number': '',
                    'software_requirement_trace_relation': f"《{basic_info.get('software_name', '软件')}》 余量测试",
                    'requirement_name': allowance_def['name'],
                    'standard_sub_requirement_name': allowance_def['name'],
                    'standard_sub_requirement_unit': '0.2',
                    'task_requirement_trace': '无',
                    'software_requirement_name': allowance_def['name'],
                    'adequacy_requirement': '所有余量测试用例执行完毕，系统余量满足要求。',
                    'pass_criteria': '各测试步骤、测试用例执行结果与预期一致，余量满足要求',
                    'english_identifier': identifier_generator.generate_fixed_allowance_identifier(i),
                    
                    # 标记字段
                    '_is_allowance_item': True,  # 标记为余量测试项
                    '_is_fixed_allowance': True  # 标记为固定余量测试项
                }
                
                allowance_test_items.append(allowance_item)
                log_debug(f"创建固定余量测试项: {allowance_def['name']}", "allowance_test_generator")
            
            log_info(f"[ALLOWANCE_TEST] 余量测试项创建完成，共{len(allowance_test_items)}项", "allowance_test_generator")
            return allowance_test_items
            
        except Exception as e:
            log_error(f"[ALLOWANCE_TEST] 创建固定余量测试项失败: {e}", "allowance_test_generator")
            import traceback
            log_error(f"[ALLOWANCE_TEST] 错误详情: {traceback.format_exc()}", "allowance_test_generator")
            return []
    
    def is_allowance_test_item(self, test_item: Dict[str, Any]) -> bool:
        """
        判断是否为余量测试项
        
        Args:
            test_item: 测试项字典
            
        Returns:
            bool: 是否为余量测试项
        """
        test_type = test_item.get('test_type', '')
        test_name = test_item.get('name', '')
        
        # 判断条件：测试类型为"余量测试"或测试名称包含"余量"
        return (test_type == '余量测试' or 
                '余量' in test_name or 
                test_item.get('_is_allowance_item', False)) 