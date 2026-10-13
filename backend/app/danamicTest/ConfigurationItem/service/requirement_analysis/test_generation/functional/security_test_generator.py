#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
安全性测试项生成器

基于hanshutiqu_kaifa项目中的安全性测试用例，
生成标准化的安全性测试项。
"""

import logging
from typing import Dict, Any, List

# 导入日志工具
from .....utils.logging_utils.logger import log_info, log_debug, log_error, log_warning

logger = logging.getLogger(__name__)


class SecurityTestGenerator:
    """安全性测试项生成器"""
    
    def __init__(self):
        """初始化安全性测试生成器"""
        self.logger = logger
        
    def create_security_tests(self, basic_info: Dict[str, Any], current_test_count: int) -> List[Dict[str, Any]]:
        """
        创建安全性测试项
        
        Args:
            basic_info: 基础信息
            current_test_count: 当前测试项数量
            
        Returns:
            List[Dict[str, Any]]: 安全性测试项列表
        """
        try:
            log_info(f"[SECURITY_TEST] 开始创建安全性测试项，当前测试项数量: {current_test_count}", "security_test_generator")
            
            # 🔧 基于hanshutiqu_kaifa项目的安全性测试定义
            security_tests = [
                {
                    'name': '安全性测试-异常数据处理1',
                    'requirement_description': '软件应能对异常数据进行处理，对输入数据进行帧头帧尾校验，确保数据完整性和系统安全性。',
                    'test_description': '测试软件是否能对异常数据处理，对输入数据进行帧头帧尾校验。',
                    'test_method': '通过代码插桩设置不完整的数据包(缺少帧头或帧尾)，发送到被测系统，观察并验证系统是否正确识别异常，并做出相应的错误处理反应，如丢弃无效帧或返回错误码。'
                },
                {
                    'name': '安全性测试-看门狗复位',
                    'requirement_description': '软件应具备看门狗功能，能够在系统异常时自动复位，确保系统可靠性和安全性。',
                    'test_description': '测试软件的看门狗功能是否正常。',
                    'test_method': '在软件main()函数的while(1)循环中进行插桩，通过调试计算机观察软件的看门狗是否触发，软件是否不断复位。'
                },
                {
                    'name': '安全性测试-看门狗复位时间',
                    'requirement_description': '软件的看门狗等待复位时间应符合设计文档要求，确保在规定时间内完成系统复位。',
                    'test_description': '测试软件的看门狗等待复位的时间是否与文档描述一致。',
                    'test_method': '在软件main()函数的while(1)循环中进行插桩，使用计时器记录调试计算机串口打印持续的时间，即为看门狗等待复位的时间。'
                },
                {
                    'name': '安全性测试-故障检出及上报',
                    'requirement_description': '软件应能实现对系统故障的检出和上报功能，确保故障能够及时发现和处理。',
                    'test_description': '测试软件是否能实现对故障的检出及上报。',
                    'test_method': '通过代码插桩模拟故障情况，软件正常运行，通过检测仪状态监控界面观察软件是否上报相应故障。'
                }
            ]
            
            security_test_items = []
            base_identifier = basic_info.get('base_identifier', 'CT-UNKNOWN')
            software_name = basic_info.get('software_name', '软件')
            software_version = basic_info.get('software_version', '1.0')  # 🔧 添加软件版本获取
            
            for i, security_def in enumerate(security_tests, 1):
                # 🔧 修复：使用固定的英文标识格式 SecurityTest1、SecurityTest2等
                english_identifier = f"SecurityTest{i}"
                
                # 生成安全性测试项标识符
                security_identifier = f"{base_identifier}-{english_identifier}-SC{i:02d}"
                
                # 🔧 添加：软件需求规格说明追踪字段（固定格式）
                software_requirement_trace = f"《{software_name}软件需求规格说明》 3.7 安全性需求"
                
                # 创建安全性测试项
                security_item = {
                    'index': current_test_count + i,
                    'name': security_def['name'],
                    'pure_name': security_def['name'],
                    'test_item_name': security_def['name'],
                    'test_item_identifier': security_identifier,
                    'english_identifier': english_identifier,  # 🔧 添加英文标识
                    'test_type': '安全性测试',
                    'software_name': software_name,
                    'software_version': software_version,
                    'requirement_description': security_def['requirement_description'],  # 🔧 新增：需求描述
                    'requirement_sub_description': security_def['requirement_description'],  # 🔧 需求子项描述
                    'test_description': security_def['test_description'],  # 🔧 修改：使用test_description
                    'test_method': security_def['test_method'],
                    'software_requirement_trace': software_requirement_trace,  # 🔧 添加：软件需求规格说明追踪
                    'software_requirement_trace_relation': software_requirement_trace,  # 🔧 添加：软件需求规格说明条目追踪关系
                    'requirements_source': '固定安全性测试',
                    'tracking_info': '默认安全性测试',
                    'chapter_number': '3.7',  # 🔧 添加：章节编号
                    'adequacy_requirement': '所有安全性用例执行完毕，对于未执行的用例说明未执行原因。',  # 🔧 修改：充分性要求
                    'pass_criteria': '各测试步骤、测试用例执行结果与预期一致，安全性指标满足要求',  # 🔧 修改：通过准则
                    'created_method': 'fixed_security_test',
                    '_is_security_test': True  # 标记为安全性测试项
                }
                
                security_test_items.append(security_item)
                log_debug(f"创建安全性测试项: {security_def['name']}", "security_test_generator")
            
            log_info(f"[SECURITY_TEST] 安全性测试项创建完成，共{len(security_test_items)}项", "security_test_generator")
            return security_test_items
            
        except Exception as e:
            log_error(f"[SECURITY_TEST] 创建安全性测试项失败: {e}", "security_test_generator")
            import traceback
            log_error(f"[SECURITY_TEST] 错误详情: {traceback.format_exc()}", "security_test_generator")
            return []
    
    def is_security_test_item(self, test_item: Dict[str, Any]) -> bool:
        """
        判断是否为安全性测试项
        
        Args:
            test_item: 测试项字典
            
        Returns:
            bool: 是否为安全性测试项
        """
        test_type = test_item.get('test_type', '')
        test_name = test_item.get('name', '')
        
        # 判断条件：测试类型为"安全性测试"或测试名称包含"安全性测试"
        return (test_type == '安全性测试' or 
                '安全性测试' in test_name or 
                '安全' in test_name or
                test_item.get('_is_security_item', False)) 