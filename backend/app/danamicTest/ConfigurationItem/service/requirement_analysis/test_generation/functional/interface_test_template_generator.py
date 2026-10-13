#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
接口测试项固定模板生成器

根据用户需求，为接口测试项生成固定格式的测试描述和测试方法，
而不是使用AI生成，确保内容的一致性和标准化。
"""

import logging
from typing import Dict, Any, Tuple

# 导入日志工具
from .....utils.logging_utils.logger import log_info, log_debug, log_error, log_warning

logger = logging.getLogger(__name__)


class InterfaceTestTemplateGenerator:
    """接口测试项固定模板生成器"""
    
    def __init__(self):
        """初始化模板生成器"""
        self.logger = logger
        
    def generate_interface_test_content(self, interface_name: str, interface_desc: str = "") -> Tuple[str, str]:
        """
        为接口测试项生成固定模板的测试描述和测试方法
        
        Args:
            interface_name: 接口名称（如：用户认证服务接口）
            interface_desc: 接口描述（可选，用于增强模板内容）
            
        Returns:
            Tuple[str, str]: (测试描述, 测试方法)
        """
        try:
            log_info(f"[INTERFACE_TEMPLATE] 为接口生成固定模板内容: {interface_name}", "interface_template_generator")
            
            # 生成测试描述
            test_description = self._generate_test_description(interface_name, interface_desc)
            
            # 生成测试方法
            test_method = self._generate_test_method(interface_name, interface_desc)
            
            log_info(f"[INTERFACE_TEMPLATE] 模板内容生成完成: {interface_name}", "interface_template_generator")
            
            return test_description, test_method
            
        except Exception as e:
            log_error(f"[INTERFACE_TEMPLATE] 生成接口测试模板失败: {interface_name}, 错误: {e}", "interface_template_generator")
            # 返回默认模板
            return self._get_default_template(interface_name)
    
    def _generate_test_description(self, interface_name: str, interface_desc: str = "") -> str:
        """
        生成测试描述
        
        基于用户提供的模板：
        1、测试软件通信协议是否与软件修规格说明或者接口说明的描述一致
        2、测试软件接口是否对数据进行帧头、帧尾校验。
        3、测试软件接口是否能实现数据的正常发送或者接收。
        4、测试数据能否对超界数据进行异常处理。
        """
        # 将接口名称自然地融入到描述中
        description_lines = [
            f"1、测试{interface_name}的通信协议是否与软件需求规格说明或者接口说明的描述一致",
            f"2、测试{interface_name}是否对数据进行帧头、帧尾校验",
            f"3、测试{interface_name}是否能实现数据的正常发送或者接收",
            f"4、测试{interface_name}能否对超界数据进行异常处理"
        ]
        
        return "\n".join(description_lines)
    
    def _generate_test_method(self, interface_name: str, interface_desc: str = "") -> str:
        """
        生成测试方法
        
        基于用户提供的模板：
        1、按照文档描述进行代码插桩发送相应指令，验证系统响应是否符合接口协议中定义的功能要求和消息格式，记录实际响应内容并与预期结果对比，确认协议一致
        2、通过代码插桩设置不完整的数据包(缺少帧头或帧尾)，发送到被测系统，观察并验证系统是否正确识别异常，并做出相应的错误处理反应，如丢弃无效帧或返回错误码。
        3、使用检测仪或代码插桩模拟外部设备的数据交互操作(包括发送和接收)，验证系统能否完整、正确地处理接收到的数据，并按预期成功回复或转发，同时检查数据内容完整性与顺序一致性。
        4、通过代码插桩向接口发送超出协议定义范围的数值或不规范数据包，验证系统是否能够识别并拒绝此类数据，并按照预设规则进行相应的异常响应(如告警、记录日志或返回错误信息)。
        """
        # 将接口名称自然地融入到测试方法中
        method_lines = [
            f"1、按照文档描述进行代码插桩发送相应指令，验证{interface_name}的系统响应是否符合接口协议中定义的功能要求和消息格式，记录实际响应内容并与预期结果对比，确认协议一致",
            f"2、通过代码插桩设置不完整的数据包(缺少帧头或帧尾)，发送到{interface_name}，观察并验证系统是否正确识别异常，并做出相应的错误处理反应，如丢弃无效帧或返回错误码",
            f"3、使用检测仪或代码插桩模拟外部设备通过{interface_name}进行数据交互操作(包括发送和接收)，验证系统能否完整、正确地处理接收到的数据，并按预期成功回复或转发，同时检查数据内容完整性与顺序一致性",
            f"4、通过代码插桩向{interface_name}发送超出协议定义范围的数值或不规范数据包，验证系统是否能够识别并拒绝此类数据，并按照预设规则进行相应的异常响应(如告警、记录日志或返回错误信息)"
        ]
        
        return "\n".join(method_lines)
    
    def _get_default_template(self, interface_name: str) -> Tuple[str, str]:
        """
        获取默认模板（当生成失败时使用）
        """
        default_description = f"1、测试{interface_name}的通信协议是否与软件需求规格说明或者接口说明的描述一致\n" \
                             f"2、测试{interface_name}是否对数据进行帧头、帧尾校验\n" \
                             f"3、测试{interface_name}是否能实现数据的正常发送或者接收\n" \
                             f"4、测试{interface_name}能否对超界数据进行异常处理"
        
        default_method = f"1、按照文档描述进行代码插桩发送相应指令，验证{interface_name}的系统响应是否符合接口协议中定义的功能要求和消息格式，记录实际响应内容并与预期结果对比，确认协议一致\n" \
                        f"2、通过代码插桩设置不完整的数据包(缺少帧头或帧尾)，发送到{interface_name}，观察并验证系统是否正确识别异常，并做出相应的错误处理反应，如丢弃无效帧或返回错误码\n" \
                        f"3、使用检测仪或代码插桩模拟外部设备通过{interface_name}进行数据交互操作(包括发送和接收)，验证系统能否完整、正确地处理接收到的数据，并按预期成功回复或转发，同时检查数据内容完整性与顺序一致性\n" \
                        f"4、通过代码插桩向{interface_name}发送超出协议定义范围的数值或不规范数据包，验证系统是否能够识别并拒绝此类数据，并按照预设规则进行相应的异常响应(如告警、记录日志或返回错误信息)"
        
        return default_description, default_method
    
    def is_interface_test_item(self, test_item: Dict[str, Any]) -> bool:
        """
        判断是否为接口测试项
        
        Args:
            test_item: 测试项字典
            
        Returns:
            bool: 是否为接口测试项
        """
        test_type = test_item.get('test_type', '')
        test_name = test_item.get('name', '')
        
        # 判断条件：测试类型为"接口测试"或测试名称包含"接口"
        return (test_type == '接口测试' or 
                '接口' in test_name or 
                test_item.get('_is_interface_item', False)) 