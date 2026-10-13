"""
AI提示词管理器

集中管理所有测试类型的AI提示词，避免重复和分散的提示词定义。
"""

from typing import Dict, Any, Tuple


class AIPromptManager:
    """AI提示词管理器 - 统一管理所有测试类型的提示词"""
    
    def __init__(self):
        """初始化提示词管理器"""
        pass
    
    def get_system_prompt(self, test_type: str, has_detector: bool = False) -> str:
        """
        获取系统提示词
        
        Args:
            test_type: 测试类型（功能测试、性能测试、边界测试等）
            has_detector: 是否有检测仪
            
        Returns:
            str: 系统提示词
        """
        detector_note = "注意测试激励的输入和被测软件状态的监控都是通过检测仪实现的，" if has_detector else ""
        
        # 功能测试、性能测试、边界测试都使用结构化提示词，不需要系统提示词
        if test_type in ['功能测试', '性能测试', '边界测试']:
            return ""  # 返回空字符串，因为这些测试类型使用结构化提示词
        
        # 其他类型的测试使用通用系统提示词
        return (
            '你是一个经验丰富的软件测试专家，专注于从软件需求中精准提炼出测试项任务。'
            '你的任务是根据用户提供的软件需求描述，深入分析并生成对应的测试项任务，每个测试项都必须包含以下两个关键部分：'
            '具体的测试内容描述、详细的测试方法描述。输出格式必须严格遵循JSON字符串数据格式，具体格式如下：'
            '[{"context": "具体的测试内容描述，明确说明要测试什么功能",  "method": "详细的测试方法描述，说明测试步骤"}]'
            f'注意：context字段必须是具体的测试内容描述，不能使用占位符文本！{detector_note}'
        )
    
    def get_user_prompt(self, test_type: str, requirement_content: str, has_detector: bool = False) -> str:
        """
        获取用户提示词（仅用于不支持结构化提示词的其他测试类型）
        
        Args:
            test_type: 测试类型
            requirement_content: 需求内容
            has_detector: 是否有检测仪
            
        Returns:
            str: 用户提示词
        """
        detector_desc = "通过检测仪" if has_detector else ""
        detector_method_desc = "，注意测试激励的输入和被测软件状态的监控都是通过检测仪实现的" if has_detector else ""
        
        # 功能测试、性能测试、边界测试都使用结构化提示词，不需要用户提示词
        if test_type in ['功能测试', '性能测试', '边界测试']:
            return ""  # 返回空字符串，因为这些测试类型使用结构化提示词
        
        # 其他类型的测试使用通用用户提示词
        return (
            f'请根据测试类型，分析以下软件需求描述，并根据要求生成测试项任务。测试类型为：{test_type}，软件需求描述为：{requirement_content}。'
            f'请确保生成的测试项任务覆盖所有关键功能点，并提供详细的测试内容和测试方法{detector_method_desc}。'
            f'重要：每个测试项的context字段必须是具体的测试内容描述，不能使用占位符！输出结果必须为结构化数据，且符合上述JSON格式。'
        )
    
    def get_structured_prompt_for_complete_generation(
        self, 
        test_type: str, 
        test_name: str, 
        requirement_content: str, 
        has_detector: bool = False
    ) -> str:
        """
        获取用于完整内容生成的结构化提示词（用于功能、性能和边界测试的结构化生成）
        
        Args:
            test_type: 测试类型
            test_name: 测试项名称
            requirement_content: 需求内容
            has_detector: 是否有检测仪
            
        Returns:
            str: 结构化提示词
        """
        detector_method_desc = "，注意测试激励的输入和被测软件状态的监控都是通过检测仪实现的" if has_detector else ""
        
        if test_type == '功能测试':
            return f"""你是软件测试专家，请分析以下需求内容，为测试项"{test_name}"生成功能测试相关的完整内容。

完整需求内容：
{requirement_content}

请按以下步骤分析：
1. 从需求中识别和提取功能相关内容（包括正常功能流程、异常处理、输入输出要求、业务逻辑等）
2. 基于提取的功能内容，生成一个测试项描述和对应的一个测试方法

**重要说明：**
- 可以生成多组测试内容和测试方法，每组一一对应
- 每条测试内容和测试方法都有自己的编号（1、2、3...）
- 每条内容内部不能再有子编号，保持简洁

请严格按照以下JSON格式输出，不要包含任何其他文字：

{{
    "test_pairs": [
        {{"description": "1验证具体功能点", "method": "1具体的测试操作{detector_method_desc}"}},
        {{"description": "2验证另一个功能点", "method": "2另一个具体的测试操作{detector_method_desc}"}},
        {{"description": "3验证第三个功能点", "method": "3第三个具体的测试操作{detector_method_desc}"}}
    ]
}}

输出示例：
{{
    "test_pairs": [
        {{"description": "1验证用户名密码验证的正确性", "method": "1输入不同的用户名和密码组合测试验证功能的正确性{detector_method_desc}"}},
        {{"description": "2验证登录状态管理的正确性", "method": "2观察登录情况和非登录情况下登录状态是否正确管理{detector_method_desc}"}},
        {{"description": "3验证权限控制的有效性", "method": "3测试不同权限用户的访问控制是否按预期工作{detector_method_desc}"}}
    ]
}}

注意：
- 每条description和method都以数字开头（1、2、3...）
- 每条内容内部不能再有编号，保持简洁描述
- 确保每个description和method一一对应
- 必须返回有效的JSON格式，不要包含任何解释性文字"""
        
        elif test_type == '性能测试':
            return f"""你是软件测试专家，请分析以下需求内容，为测试项"{test_name}"生成性能测试相关的完整内容。

完整需求内容：
{requirement_content}

请按以下步骤分析：
1. 从需求中识别和提取性能相关内容（重点关注g) 性能:段落，以及包含≤、≥、<、>、秒、毫秒、微秒、次/秒、ms、s、响应时间、处理时间、延迟、性能、TPS、QPS等性能指标的内容）
2. 基于提取的性能内容，生成测试项描述和测试方法

**重要说明：**
- requirement_description只有一条，不会有多条
- 可以生成多组测试内容和测试方法，每组一一对应
- 每条测试内容和测试方法都有自己的编号（1、2、3...）
- 每条内容内部不能再有子编号，保持简洁

请严格按照以下JSON格式输出，不要包含任何其他文字：

{{
    "requirement_description": "从原文中提取的性能相关需求内容",
    "test_pairs": [
        {{"description": "1验证具体性能指标", "method": "1具体的性能测试操作{detector_method_desc}"}},
        {{"description": "2验证另一个性能指标", "method": "2另一个具体的性能测试操作{detector_method_desc}"}}
    ]
}}

输出示例：
{{
    "requirement_description": "认证响应时间 ≤ 2 秒（95% 请求）。支持每秒 50 次并发认证请求。",
    "test_pairs": [
        {{"description": "1验证认证响应时间性能指标", "method": "1使用性能测试工具模拟并发请求监控95%请求响应时间是否≤2秒{detector_method_desc}"}},
        {{"description": "2验证并发处理能力性能指标", "method": "2配置50个并发用户持续请求验证系统每秒处理能力{detector_method_desc}"}}
    ]
}}

注意：
- requirement_description：必须从原文中准确提取性能相关内容，保持原文表述，只有一条
- 每条description和method都以数字开头（1、2、3...）
- 每条内容内部不能再有编号，保持简洁描述
- 确保每个description和method一一对应
- 必须返回有效的JSON格式，不要包含任何解释性文字"""
        
        elif test_type == '边界测试':
            return f"""你是软件测试专家，请分析以下需求内容，为测试项"{test_name}"生成边界测试相关的完整内容。

完整需求内容：
{requirement_content}

请按以下步骤分析：
1. 从需求中识别和提取边界相关内容（查找包含至少、最少、不少于、不超过、最多、范围、区间、边界、限制、约束、最大、最小等边界条件的内容）
2. 严格排除性能相关内容（如g) 性能:段落和包含响应时间、处理时间、延迟等性能指标的内容）
3. 基于提取的边界内容，生成测试项描述和测试方法

**重要说明：**
- requirement_description只有一条，不会有多条
- 可以生成多组测试内容和测试方法，每组一一对应
- 每条测试内容和测试方法都有自己的编号（1、2、3...）
- 每条内容内部不能再有子编号，保持简洁

请严格按照以下JSON格式输出，不要包含任何其他文字：

{{
    "requirement_description": "从原文中提取的边界相关需求内容",
    "test_pairs": [
        {{"description": "1验证具体边界条件", "method": "1具体的边界测试操作{detector_method_desc}"}},
        {{"description": "2验证另一个边界条件", "method": "2另一个具体的边界测试操作{detector_method_desc}"}}
    ]
}}

输出示例：
{{
    "requirement_description": "密码复杂度要求：至少 8 字符，包含大小写字母、数字及特殊符号。仅支持 TOTP（时间型动态令牌）和短信验证码。",
    "test_pairs": [
        {{"description": "1验证密码长度边界条件", "method": "1输入7字符和8字符密码测试长度边界处理{detector_method_desc}"}},
        {{"description": "2验证密码字符类型边界条件", "method": "2输入不同字符类型组合测试复杂度要求{detector_method_desc}"}},
        {{"description": "3验证验证码类型支持边界", "method": "3尝试使用支持和不支持的验证码类型测试边界{detector_method_desc}"}}
    ]
}}

注意：
- requirement_description：必须从原文中准确提取边界相关内容，完全排除性能相关内容，只有一条
- 每条description和method都以数字开头（1、2、3...）
- 每条内容内部不能再有编号，保持简洁描述
- 确保每个description和method一一对应
- 必须返回有效的JSON格式，不要包含任何解释性文字"""
        
        else:
            # 其他类型暂不支持结构化提示词
            return self.get_user_prompt(test_type, requirement_content, has_detector)
    
    def supports_structured_prompt(self, test_type: str) -> bool:
        """
        判断测试类型是否支持结构化提示词
        
        Args:
            test_type: 测试类型
            
        Returns:
            bool: 是否支持结构化提示词
        """
        return test_type in ['功能测试', '性能测试', '边界测试']
    
    def get_prompt_config(self, test_type: str, requirement_content: str, has_detector: bool = False, test_name: str = "") -> Dict[str, Any]:
        """
        获取完整的提示词配置
        
        Args:
            test_type: 测试类型
            requirement_content: 需求内容
            has_detector: 是否有检测仪
            test_name: 测试项名称（用于结构化提示词）
            
        Returns:
            Dict[str, Any]: 提示词配置字典
        """
        if self.supports_structured_prompt(test_type):
            # 使用结构化提示词
            return {
                'structured_prompt': self.get_structured_prompt_for_complete_generation(
                    test_type, test_name, requirement_content, has_detector
                ),
                'system_prompt': "",  # 结构化提示词不需要系统提示词
                'user_prompt': "",    # 结构化提示词不需要用户提示词
                'test_type': test_type,
                'has_detector': has_detector,
                'use_structured': True
            }
        else:
            # 使用传统的系统+用户提示词
            return {
                'system_prompt': self.get_system_prompt(test_type, has_detector),
                'user_prompt': self.get_user_prompt(test_type, requirement_content, has_detector),
                'test_type': test_type,
                'has_detector': has_detector,
                'use_structured': False
            }


# 全局提示词管理器实例
prompt_manager = AIPromptManager() 