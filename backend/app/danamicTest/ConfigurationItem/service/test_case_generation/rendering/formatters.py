"""
渲染与格式化模块
职责：将方法-用例映射格式化为 Excel 写入所需的数据结构
说明：通过回调传入 DB 读取与匹配函数，保持纯函数、便于测试
"""
from typing import Dict, List, Any, Callable, Optional
import logging

try:
    from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ....utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

logger = logging.getLogger(__name__)


LoadRequirementAnalysisFn = Callable[[str], Dict[str, Dict[str, Any]]]
FindMatchingRequirementFn = Callable[[str, Dict[str, Dict[str, Any]]], Dict[str, Any]]
ExtractCorrespondingDescFn = Callable[[str, str], str]


def format_test_cases_for_excel_impl(
    method_based_cases: Dict[str, List[Dict[str, str]]],
    software_info: Dict[str, Any],
    task_id: Optional[str],
    load_requirement_analysis_fn: LoadRequirementAnalysisFn,
    find_matching_requirement_fn: FindMatchingRequirementFn,
    extract_corresponding_desc_fn: ExtractCorrespondingDescFn,
) -> List[Dict[str, Any]]:
    """将基于方法的测试用例格式化为 Excel 写入格式（纯函数+回调）"""
    try:
        requirement_analysis_mapping: Dict[str, Dict[str, Any]] = {}
        if task_id:
            requirement_analysis_mapping = load_requirement_analysis_fn(task_id) or {}
            log_info(f"从数据库加载了 {len(requirement_analysis_mapping)} 条需求分析记录", "method_based_generator")

        formatted_cases: List[Dict[str, Any]] = []
        case_counter = 1

        for test_method, test_cases in method_based_cases.items():
            matching_requirement = {}
            if requirement_analysis_mapping:
                matching_requirement = find_matching_requirement_fn(test_method, requirement_analysis_mapping) or {}

            for case in test_cases:
                if matching_requirement:
                    requirement_traceability = matching_requirement.get('software_requirement_identifier', '')
                    test_item_name = matching_requirement.get('test_item_name', '')
                    test_item_identifier = matching_requirement.get('test_item_identifier', '')
                    software_requirement_trace = matching_requirement.get('software_requirement_trace', '')
                    full_test_description = matching_requirement.get('test_description', '')
                    corresponding_test_description = extract_corresponding_desc_fn(test_method, full_test_description)
                    log_debug(
                        f"测试方法 '{test_method[:50]}...' 匹配到需求分析数据: 测试项名称='{test_item_name}', 标识='{test_item_identifier}', 对应测试描述='{corresponding_test_description[:50]}...'",
                        "method_based_generator",
                    )
                else:
                    import logging as _logging
                    _logger = _logging.getLogger("db_operations")
                    _logger.warning(f"[DB_USE_DEFAULT] 未匹配测试方法，使用默认值: {test_method[:50]}...")
                    requirement_traceability = "待补充需求追溯"
                    test_item_name = "待确认测试项"
                    test_item_identifier = f'TI{case_counter:03d}'
                    software_requirement_trace = '待补充软件需求追溯'
                    corresponding_test_description = test_method
                    _logger.info(f"[DB_DEFAULT_DETAILS] 默认值详情 - 计数器: {case_counter}, 测试项名称: {test_item_name}, 标识: {test_item_identifier}")

                formatted_case = {
                    'sequence_number': case_counter,
                    'software_item_name': software_info.get('software_name', ''),
                    'software_version': software_info.get('software_version', '1.0.0'),
                    'test_round': '第一轮',
                    'requirement_traceability': requirement_traceability,
                    'test_item_name': test_item_name,
                    'test_item_identifier': test_item_identifier,
                    'test_case_name': case.get('case_name', ''),
                    'test_case_number': f'TC{case_counter:03d}',
                    'test_type': '功能测试',
                    'test_description': corresponding_test_description,
                    'input_conditions': case.get('input_conditions', ''),
                    'expected_results': case.get('expected_results', ''),
                    'pass_criteria': '测试步骤执行结果与预期一致',
                    'case_designer': '系统自动生成',
                    'design_time': '',
                    'test_personnel': '',
                    'test_time': '',
                    'test_result': '',
                    'test_conclusion': '',
                    'execution_year_month': '',
                    'issues_found_count': 0,
                    'software_requirement_trace': software_requirement_trace,
                }
                formatted_cases.append(formatted_case)
                case_counter += 1

        log_info(f"格式化了 {len(formatted_cases)} 个测试用例", "method_based_generator")
        return formatted_cases

    except Exception as e:
        log_error(f"格式化测试用例失败: {str(e)}", "method_based_generator")
        return []
