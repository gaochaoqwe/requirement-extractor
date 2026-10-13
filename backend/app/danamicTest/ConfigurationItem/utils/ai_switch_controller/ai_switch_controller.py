#!/usr/bin/env python3
"""
AI开关控制器
统一管理AI功能的启用和禁用控制

功能：
- 控制需求分析模块中测试项描述和测试方法的AI生成
- 控制用例单模块中四列的AI生成
- 提供统一的开关状态管理
- 支持分模块的精细控制
"""

from typing import Dict, Any, Optional, Tuple
from enum import Enum

# 导入日志工具
try:
    from .logging_utils.logger import log_info, log_error, log_debug, log_warning
except ImportError:
    try:
        from ..utils.logging_utils.logger import log_info, log_error, log_debug, log_warning
    except ImportError:
        try:
            from ...utils.logging_utils.logger import log_info, log_error, log_debug, log_warning
        except ImportError:
            # 作为后备，使用print语句
            def log_info(msg, tag="ai_switch"): print(f"INFO [{tag}] {msg}")
            def log_error(msg, tag="ai_switch"): print(f"ERROR [{tag}] {msg}")
            def log_debug(msg, tag="ai_switch"): print(f"DEBUG [{tag}] {msg}")
            def log_warning(msg, tag="ai_switch"): print(f"WARNING [{tag}] {msg}")


class AIModule(Enum):
    """AI模块类型枚举"""
    REQUIREMENT_ANALYSIS = "requirement_analysis"  # 需求分析模块
    TEST_CASE_GENERATION = "test_case_generation"   # 用例单生成模块
    OTHER_MODULES = "other_modules"                  # 其他模块


class AIComponent(Enum):
    """AI功能组件枚举"""
    # 需求分析模块组件
    TEST_DESCRIPTION = "test_description"           # 测试项描述
    TEST_METHOD = "test_method"                     # 测试方法
    
    # 用例单模块组件  
    CASE_NAME = "case_name"                         # 用例名称
    CASE_DESCRIPTION = "case_description"           # 用例描述
    INPUT_CONDITIONS = "input_conditions"           # 输入条件
    EXPECTED_RESULTS = "expected_results"           # 预期结果
    
    # 其他组件
    OTHER_AI_FEATURES = "other_ai_features"         # 其他AI功能


class AISwitchController:
    """AI开关控制器"""
    
    def __init__(self, global_ai_enabled: bool = True):
        """
        初始化AI开关控制器
        
        Args:
            global_ai_enabled: 全局AI开关状态
        """
        self.global_ai_enabled = global_ai_enabled
        
        # 各模块的AI开关控制
        self.module_switches = {
            AIModule.REQUIREMENT_ANALYSIS: {
                AIComponent.TEST_DESCRIPTION: global_ai_enabled,  # 受全局开关控制
                AIComponent.TEST_METHOD: global_ai_enabled,       # 受全局开关控制
            },
            AIModule.TEST_CASE_GENERATION: {
                AIComponent.CASE_NAME: global_ai_enabled,         # 受全局开关控制
                AIComponent.CASE_DESCRIPTION: global_ai_enabled,  # 受全局开关控制
                AIComponent.INPUT_CONDITIONS: global_ai_enabled,  # 受全局开关控制
                AIComponent.EXPECTED_RESULTS: global_ai_enabled,  # 受全局开关控制
            },
            AIModule.OTHER_MODULES: {
                AIComponent.OTHER_AI_FEATURES: True,              # 不受全局开关控制
            }
        }
        
        # log_info(f"AI开关控制器初始化 - 全局AI状态: {global_ai_enabled}", "ai_switch_controller")
        self._log_switch_status()
    
    def is_enabled(self, module: AIModule, component: AIComponent) -> bool:
        """
        检查指定模块的AI功能是否启用
        
        Args:
            module: AI模块
            component: AI组件
            
        Returns:
            bool: 是否启用AI功能
        """
        if module not in self.module_switches:
            # log_warning(f"未知的AI模块: {module}", "ai_switch_controller")
            return False
        
        if component not in self.module_switches[module]:
            # log_warning(f"模块{module}中未定义的AI组件: {component}", "ai_switch_controller")
            return False
        
        enabled = self.module_switches[module][component]
        # log_debug(f"AI开关检查 - {module.value}.{component.value}: {enabled}", "ai_switch_controller")
        return enabled
    
    def set_global_ai_switch(self, enabled: bool) -> None:
        """
        设置全局AI开关状态
        
        Args:
            enabled: 是否启用AI功能
        """
        old_status = self.global_ai_enabled
        self.global_ai_enabled = enabled
        
        # 更新受全局开关控制的组件
        self.module_switches[AIModule.REQUIREMENT_ANALYSIS][AIComponent.TEST_DESCRIPTION] = enabled
        self.module_switches[AIModule.REQUIREMENT_ANALYSIS][AIComponent.TEST_METHOD] = enabled
        
        self.module_switches[AIModule.TEST_CASE_GENERATION][AIComponent.CASE_NAME] = enabled
        self.module_switches[AIModule.TEST_CASE_GENERATION][AIComponent.CASE_DESCRIPTION] = enabled
        self.module_switches[AIModule.TEST_CASE_GENERATION][AIComponent.INPUT_CONDITIONS] = enabled
        self.module_switches[AIModule.TEST_CASE_GENERATION][AIComponent.EXPECTED_RESULTS] = enabled
        
        # 其他模块不受影响，保持独立控制
        
        # log_info(f"全局AI开关更新: {old_status} -> {enabled}", "ai_switch_controller")
        self._log_switch_status()
    
    def set_module_switch(self, module: AIModule, component: AIComponent, enabled: bool) -> None:
        """
        设置特定模块组件的AI开关状态
        
        Args:
            module: AI模块
            component: AI组件
            enabled: 是否启用AI功能
        """
        if module not in self.module_switches:
            # log_error(f"尝试设置未知AI模块的开关: {module}", "ai_switch_controller")
            return
        
        if component not in self.module_switches[module]:
            # log_error(f"尝试设置模块{module}中未定义的AI组件开关: {component}", "ai_switch_controller")
            return
        
        old_status = self.module_switches[module][component]
        self.module_switches[module][component] = enabled
        
        # log_info(f"模块开关更新: {module.value}.{component.value} {old_status} -> {enabled}", "ai_switch_controller")
    
    def get_ai_config(self, module: AIModule) -> Dict[str, Any]:
        """
        获取指定模块的AI配置信息
        
        Args:
            module: AI模块
            
        Returns:
            Dict: AI配置信息
        """
        if module not in self.module_switches:
            # log_error(f"获取未知AI模块的配置: {module}", "ai_switch_controller")
            return {'enable_ai_analysis': False}
        
        module_config = self.module_switches[module]
        
        if module == AIModule.REQUIREMENT_ANALYSIS:
            return {
                'enable_ai_analysis': (
                    module_config[AIComponent.TEST_DESCRIPTION] or 
                    module_config[AIComponent.TEST_METHOD]
                ),
                'enable_test_description': module_config[AIComponent.TEST_DESCRIPTION],
                'enable_test_method': module_config[AIComponent.TEST_METHOD],
                'ai_analysis_attempts': 4,
                'use_knowledge_optimization': False,
            }
        
        elif module == AIModule.TEST_CASE_GENERATION:
            return {
                'enable_ai_analysis': any(module_config.values()),
                'enable_case_name': module_config[AIComponent.CASE_NAME],
                'enable_case_description': module_config[AIComponent.CASE_DESCRIPTION], 
                'enable_input_conditions': module_config[AIComponent.INPUT_CONDITIONS],
                'enable_expected_results': module_config[AIComponent.EXPECTED_RESULTS],
                'ai_analysis_attempts': 4,
            }
        
        else:
            return {
                'enable_ai_analysis': module_config.get(AIComponent.OTHER_AI_FEATURES, True),
                'ai_analysis_attempts': 4,
            }
    
    def should_use_ai_for_requirement_analysis(self) -> Tuple[bool, bool]:
        """
        检查需求分析模块是否应该使用AI
        
        Returns:
            tuple: (是否使用AI生成测试项描述, 是否使用AI生成测试方法)
        """
        return (
            self.is_enabled(AIModule.REQUIREMENT_ANALYSIS, AIComponent.TEST_DESCRIPTION),
            self.is_enabled(AIModule.REQUIREMENT_ANALYSIS, AIComponent.TEST_METHOD)
        )
    
    def should_use_ai_for_test_case_generation(self) -> bool:
        """
        检查用例单模块是否应该使用AI
        
        Returns:
            bool: 是否使用AI生成用例单
        """
        return any([
            self.is_enabled(AIModule.TEST_CASE_GENERATION, AIComponent.CASE_NAME),
            self.is_enabled(AIModule.TEST_CASE_GENERATION, AIComponent.CASE_DESCRIPTION),
            self.is_enabled(AIModule.TEST_CASE_GENERATION, AIComponent.INPUT_CONDITIONS),
            self.is_enabled(AIModule.TEST_CASE_GENERATION, AIComponent.EXPECTED_RESULTS),
        ])
    
    def _log_switch_status(self) -> None:
        """记录当前开关状态"""
        # log_info("=== AI开关状态总览 ===", "ai_switch_controller")
        # log_info(f"全局AI开关: {self.global_ai_enabled}", "ai_switch_controller")
        
        for module, components in self.module_switches.items():
            # log_info(f"模块 {module.value}:", "ai_switch_controller")
            for component, enabled in components.items():
                # log_info(f"  - {component.value}: {enabled}", "ai_switch_controller")
        
                pass
        # log_info("=== AI开关状态总览结束 ===", "ai_switch_controller")


# 创建全局AI开关控制器实例
_global_ai_controller: Optional[AISwitchController] = None


def get_ai_controller() -> AISwitchController:
    """获取全局AI开关控制器实例"""
    global _global_ai_controller
    if _global_ai_controller is None:
        _global_ai_controller = AISwitchController(global_ai_enabled=True)
    return _global_ai_controller


def init_ai_controller(global_ai_enabled: bool) -> AISwitchController:
    """
    初始化全局AI开关控制器
    
    Args:
        global_ai_enabled: 全局AI开关状态
        
    Returns:
        AISwitchController: AI开关控制器实例
    """
    global _global_ai_controller
    _global_ai_controller = AISwitchController(global_ai_enabled)
    return _global_ai_controller 