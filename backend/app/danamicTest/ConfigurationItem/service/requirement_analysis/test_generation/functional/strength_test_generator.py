#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
强度测试项生成器

从原有的functional_test_creator.py中抽取强度测试生成逻辑，
提供独立的强度测试项生成功能。
"""

import logging
from typing import Dict, Any, List

# 导入日志工具
from .....utils.logging_utils.logger import log_info, log_debug, log_error, log_warning

logger = logging.getLogger(__name__)


class StrengthTestGenerator:
    """强度测试项生成器"""
    
    def __init__(self):
        """初始化强度测试生成器"""
        self.logger = logger
        
    def create_fixed_strength_tests(self, basic_info: Dict[str, Any], current_test_count: int) -> List[Dict[str, Any]]:
        """
        创建固定的强度测试项
        
        Args:
            basic_info: 基础信息
            current_test_count: 当前测试项数量
            
        Returns:
            List[Dict[str, Any]]: 固定强度测试项列表
        """
        try:
            log_info(f"[STRENGTH_TEST] 开始创建强度测试项，当前测试项数量: {current_test_count}", "strength_test_generator")
            
            # 🔧 固定的强度测试定义（增加需求描述字段）
            fixed_strength_tests = [
                {
                    'name': '强度测试-运行时间测试',
                    'requirement_description': '软件需连续运行7.2个小时无功能异常',
                    'description': '测试软件连续运行7.2个小时是否会出现功能异常。',
                    'test_method': '软件连续运行7.2个小时，通过调试计算机的内存监控及检测仪状态监控界面观察软件是否出现异常比如卡顿、故障等。'
                },
                {
                    'name': '强度测试-频繁指令处理测试',
                    'requirement_description': '软件需能处理高频率指令无故障',
                    'description': '测试软件对高频率的指令是否能进行处理。',
                    'test_method': '通过检测仪连续、随机发送各种测试指令，连续发送三分钟以上，通过调试计算机的内存监控及检测仪状态监控界面观察软件是否出现故障或卡顿。'
                }
            ]
            
            strength_test_items = []
            base_identifier = basic_info.get('base_identifier', 'CT-UNKNOWN')
            software_name = basic_info.get('software_name', '软件')
            
            for i, strength_def in enumerate(fixed_strength_tests, 1):
                # 生成强度测试项标识符 (按要求格式: CT-软件标识-版本-StrengthTest-ST01)
                strength_identifier = f"{base_identifier}-StrengthTest-ST{i:02d}"
                
                # 创建强度测试项（使用标准测试项字段结构）
                strength_item = {
                    'index': current_test_count + i,
                    'name': strength_def['name'],
                    'pure_name': strength_def['name'],
                    'test_item_name': strength_def['name'],
                    'test_item_identifier': strength_identifier,
                    'test_type': '强度测试',
                    'software_name': basic_info.get('software_name', '软件'),
                    'software_version': basic_info.get('software_version', '1.0'),
                    
                    # 🔧 修复：正确的字段映射
                    'requirement_description': strength_def['requirement_description'],  # 需求描述
                    'requirement_sub_description': strength_def['requirement_description'],  # 需求子项描述
                    'test_description': strength_def['description'],  # 测试项描述（AI可能会覆盖）
                    'test_method': strength_def['test_method'],  # 测试方法（AI可能会覆盖）
                    
                    # 标准测试项字段
                    'software_requirement_trace': f"《{basic_info.get('software_name', '软件')}需求规格说明》 典型需求",  # 🔧 修改格式
                    'chapter_number': '',
                    'software_requirement_trace_relation': f"《{basic_info.get('software_name', '软件')}需求规格说明》 典型需求",  # 🔧 修改格式
                    'requirement_name': strength_def['name'],
                    'standard_sub_requirement_name': strength_def['name'],
                    'standard_sub_requirement_unit': '0.2',
                    'task_requirement_trace': '无',
                    'software_requirement_name': strength_def['name'],
                    'adequacy_requirement': '所有强度测试用例执行完毕，对于未执行的用例说明未执行原因',
                    'pass_criteria': '各测试步骤、测试用例执行结果与预期一致，强度指标满足要求',
                    'english_identifier': f'StrengthTest{i:03d}',
                    
                    # 标记字段
                    '_is_strength_item': True,  # 标记为强度测试项
                    '_is_fixed_strength': True  # 标记为固定强度测试项
                }
                
                strength_test_items.append(strength_item)
                log_debug(f"创建固定强度测试项: {strength_def['name']}", "strength_test_generator")
            
            log_info(f"[STRENGTH_TEST] 强度测试项创建完成，共{len(strength_test_items)}项", "strength_test_generator")
            return strength_test_items
            
        except Exception as e:
            log_error(f"[STRENGTH_TEST] 创建固定强度测试项失败: {e}", "strength_test_generator")
            import traceback
            log_error(f"[STRENGTH_TEST] 错误详情: {traceback.format_exc()}", "strength_test_generator")
            return []
    
    def is_strength_test_item(self, test_item: Dict[str, Any]) -> bool:
        """
        判断是否为强度测试项
        
        Args:
            test_item: 测试项字典
            
        Returns:
            bool: 是否为强度测试项
        """
        test_type = test_item.get('test_type', '')
        test_name = test_item.get('name', '')
        
        # 判断条件：测试类型为"强度测试"或测试名称包含"强度测试"
        return (test_type == '强度测试' or 
                '强度测试' in test_name or 
                test_item.get('_is_strength_item', False)) 