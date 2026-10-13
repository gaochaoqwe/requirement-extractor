"""
配置项测试用例模块（回退版）

保留基础的测试用例服务 TestCaseService（用于从“测试用例单”工作表抽取并入库），
并重新导出表单处理相关函数以兼容现有调用方（如 `form_builder.table_fillers.test_case_table_filler`）。
"""

from .test_case_service import TestCaseService
from .test_case_form_handler import (
    generate_test_cases_for_form,
    set_default_test_cases,
    write_test_cases_to_excel,
    get_test_time_info,
)

__all__ = [
    'TestCaseService',
    'generate_test_cases_for_form',
    'set_default_test_cases',
    'write_test_cases_to_excel',
    'get_test_time_info',
]