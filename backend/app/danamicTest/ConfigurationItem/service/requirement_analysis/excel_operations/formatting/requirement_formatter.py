"""
需求格式化器

负责将需求数据格式化为标准的a-h格式的需求描述。
"""

import logging
from typing import Dict, List, Optional, Any

# 导入任务日志函数
from .....utils.logging_utils.logger import log_info, log_debug, log_error, log_warning

# 配置日志
logger = logging.getLogger(__name__)

class RequirementFormatter:
    """需求格式化器"""
    
    def __init__(self):
        """初始化需求格式化器"""
        self.logger = logger
    
    def format_requirement_description(self, requirement_data: Dict[str, Any]) -> str:
        """
        将需求数据格式化为标准的a-h格式
        
        Args:
            requirement_data: 需求数据字典
            
        Returns:
            str: 格式化后的需求描述
        """
        try:
            self.logger.debug("开始格式化需求描述")
            
            # 提取各个字段
            identifier = requirement_data.get('identifier', requirement_data.get('标识号', ''))
            description = requirement_data.get('description', requirement_data.get('说明', ''))
            entry_conditions = requirement_data.get('entry_conditions', requirement_data.get('进入条件', ''))
            inputs = requirement_data.get('inputs', requirement_data.get('输入', []))
            outputs = requirement_data.get('outputs', requirement_data.get('输出', []))
            processing = requirement_data.get('processing', requirement_data.get('处理', []))
            performance = requirement_data.get('performance', requirement_data.get('性能', ''))
            constraints = requirement_data.get('constraints', requirement_data.get('约束与限制', ''))
            
            # 构建格式化字符串
            formatted_parts = []
            
            # a) 标识号
            if identifier:
                formatted_parts.append(f"a) 标识号：{identifier}")
            
            # b) 说明
            if description:
                formatted_parts.append(f"b) 说明：{description}")
            
            # c) 进入条件
            if entry_conditions:
                formatted_parts.append(f"c) 进入条件：{entry_conditions}")
            
            # d) 输入
            if inputs:
                input_text = self._format_list_items(inputs, "输入")
                formatted_parts.append(f"d) 输入：{input_text}")
            
            # e) 输出
            if outputs:
                output_text = self._format_list_items(outputs, "输出")
                formatted_parts.append(f"e) 输出：{output_text}")
            
            # f) 处理
            if processing:
                processing_text = self._format_processing_steps(processing)
                formatted_parts.append(f"f) 处理：{processing_text}")
            
            # g) 性能
            if performance:
                formatted_parts.append(f"g) 性能：{performance}")
            
            # h) 约束与限制
            if constraints:
                formatted_parts.append(f"h) 约束与限制：{constraints}")
            
            # 组合所有部分
            result = "\n".join(formatted_parts)
            
            self.logger.debug(f"需求描述格式化完成，长度: {len(result)}")
            return result
            
        except Exception as e:
            self.logger.error(f"格式化需求描述时发生错误: {str(e)}")
            return str(requirement_data)  # 返回原始数据的字符串表示
    
    def _format_list_items(self, items: List[str], item_type: str) -> str:
        """
        格式化列表项
        
        Args:
            items: 项目列表
            item_type: 项目类型（用于日志）
            
        Returns:
            str: 格式化后的列表文本
        """
        try:
            if not items:
                return ""
            
            if isinstance(items, str):
                return items
            
            if len(items) == 1:
                return items[0]
            
            # 多个项目时使用项目符号
            formatted_items = []
            for item in items:
                if item.strip():
                    formatted_items.append(f"- {item.strip()}")
            
            return "\n".join(formatted_items)
            
        except Exception as e:
            self.logger.error(f"格式化{item_type}列表时发生错误: {str(e)}")
            return str(items)
    
    def _format_processing_steps(self, processing: List[str]) -> str:
        """
        格式化处理步骤
        
        Args:
            processing: 处理步骤列表
            
        Returns:
            str: 格式化后的处理步骤文本
        """
        try:
            if not processing:
                return ""
            
            if isinstance(processing, str):
                return processing
            
            # 处理步骤使用数字编号
            formatted_steps = []
            for i, step in enumerate(processing, 1):
                if step.strip():
                    formatted_steps.append(f"{i}. {step.strip()}")
            
            return "\n".join(formatted_steps)
            
        except Exception as e:
            self.logger.error(f"格式化处理步骤时发生错误: {str(e)}")
            return str(processing)
    
    def format_batch_requirements(self, requirements_list: List[Dict[str, Any]]) -> List[str]:
        """
        批量格式化需求描述
        
        Args:
            requirements_list: 需求数据列表
            
        Returns:
            List[str]: 格式化后的需求描述列表
        """
        try:
            self.logger.info(f"开始批量格式化 {len(requirements_list)} 个需求描述")
            
            formatted_descriptions = []
            for i, req_data in enumerate(requirements_list):
                try:
                    formatted = self.format_requirement_description(req_data)
                    formatted_descriptions.append(formatted)
                except Exception as e:
                    self.logger.error(f"格式化第 {i+1} 个需求时发生错误: {str(e)}")
                    formatted_descriptions.append(str(req_data))
            
            self.logger.info(f"批量格式化完成，成功格式化 {len(formatted_descriptions)} 个需求描述")
            return formatted_descriptions
            
        except Exception as e:
            self.logger.error(f"批量格式化需求描述时发生错误: {str(e)}")
            return [str(req) for req in requirements_list]
    
    def validate_requirement_format(self, requirement_text: str) -> bool:
        """
        验证需求描述格式是否符合a-h标准
        
        Args:
            requirement_text: 需求描述文本
            
        Returns:
            bool: 格式是否正确
        """
        try:
            # 检查是否包含必要的a-h格式标识
            required_patterns = ['a)', 'b)']  # 至少要有标识号和说明
            
            for pattern in required_patterns:
                if pattern not in requirement_text:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"验证需求格式时发生错误: {str(e)}")
            return False 