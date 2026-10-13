"""
回归测试用例生成模块

负责处理回归测试中的测试用例生成相关功能，包括：
- AI驱动的测试用例生成
- 测试分析和内容生成
- 表单填充中的测试用例相关部分
"""

from .test_case_generator import (
    AI_generate_yongli,
    generate_test_yongli,
    generate_test_yonglisheji
)

from .test_analysis import generate_test_cases

from .test_case_form_handler import (
    generate_test_cases_for_form,
    set_default_test_cases,
    write_test_cases_to_excel,
    write_simple_test_cases_to_excel,
    get_test_time_info
)

from .ai_analysis import (
    translate_chinese_to_english,
    analyze_requirement_text,
    analyze_code_impact
)

__all__ = [
    'AI_generate_yongli',
    'generate_test_yongli', 
    'generate_test_yonglisheji',
    'generate_test_cases',
    'generate_test_cases_for_form',
    'set_default_test_cases',
    'write_test_cases_to_excel',
    'write_simple_test_cases_to_excel',
    'get_test_time_info',
    'translate_chinese_to_english',
    'analyze_requirement_text',
    'analyze_code_impact'
] 