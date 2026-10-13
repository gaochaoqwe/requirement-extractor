"""
批量AI响应解析模块
职责：解析批量生成的测试用例JSON，并进行基本字段验证
"""
from typing import Dict, List, Any
import json
import logging

try:
    from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ....utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

logger = logging.getLogger(__name__)


def _validate_test_case(case: Dict[str, Any]) -> bool:
    required_fields = ['case_name', 'case_description', 'input_conditions', 'expected_results']
    if not isinstance(case, dict):
        return False
    for field in required_fields:
        if field not in case or not isinstance(case[field], str) or not case[field].strip():
            return False
    return True


def parse_batch_ai_response(response: str, method_items: List[str]) -> Dict[str, List[Dict[str, str]]]:
    """
    解析AI模型返回的批量测试用例JSON响应

    Args:
        response: AI模型返回的JSON字符串
        method_items: 测试方法条目列表（仅用于日志对齐）

    Returns:
        Dict[str, List[Dict[str, str]]]: 以测试方法为key的测试用例字典
    """
    try:
        data = json.loads(response)
        if isinstance(data, dict) and 'test_cases_by_method' in data:
            test_cases_by_method = data['test_cases_by_method']
            if isinstance(test_cases_by_method, list):
                method_based_cases: Dict[str, List[Dict[str, str]]] = {}
                for item in test_cases_by_method:
                    if not (isinstance(item, dict) and 'method_index' in item and 'test_method' in item and 'test_cases' in item):
                        log_warning("解析失败: 项格式不正确，缺少 method_index 或 test_method 或 test_cases", "method_based_generator")
                        continue
                    method_index = item['method_index']
                    test_method_text = item['test_method']
                    test_cases = item['test_cases']

                    if isinstance(test_cases, list):
                        valid_cases = [case for case in test_cases if _validate_test_case(case)]
                        if valid_cases:
                            method_based_cases[test_method_text] = valid_cases
                            log_debug(f"解析成功: 方法索引 {method_index}, 方法文本 '{test_method_text[:50]}...', 生成 {len(valid_cases)} 个用例", "method_based_generator")
                        else:
                            log_warning(f"解析失败: 方法索引 {method_index}, 方法文本 '{test_method_text[:50]}...', 生成用例失败", "method_based_generator")
                    else:
                        log_warning(f"解析失败: 方法索引 {method_index}, 方法文本 '{test_method_text[:50]}...', test_cases 不是列表", "method_based_generator")
                return method_based_cases
        log_warning("批量解析失败，响应格式不符合预期", "method_based_generator")
        return {}
    except json.JSONDecodeError as e:
        log_warning(f"批量JSON解析失败: {str(e)}", "method_based_generator")
        return {}
    except Exception as e:
        log_warning(f"批量响应解析失败: {str(e)}", "method_based_generator")
        return {}
