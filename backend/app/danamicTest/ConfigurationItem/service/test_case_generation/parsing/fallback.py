"""
兜底用例生成策略模块
职责：在批量AI生成失败时，基于拆分后的测试方法逐个生成用例
说明：为保持纯度与复用性，通过回调传入拆分函数与单方法生成函数
"""
from typing import Callable, Dict, List, Any
import logging

try:
    from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ....utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

logger = logging.getLogger(__name__)


Splitter = Callable[[str], List[str]]
SingleMethodGenerator = Callable[[str, str, str, str, str, str, int], List[Dict[str, str]]]


def generate_fallback_cases(
    test_method: str,
    test_description: str,
    requirement_name: str,
    requirement_desc: str,
    ceshileixing: str,
    jianceyi_flag: str,
    splitter: Splitter,
    single_method_generator: SingleMethodGenerator,
) -> Dict[str, List[Dict[str, str]]]:
    """
    当批量AI生成失败时，使用传统逐个生成方法。
    通过回调获取“拆分测试方法”与“单方法用例生成”能力，以避免模块间强耦合。
    """
    try:
        # 拆分测试方法为独立的测试方法
        individual_methods = splitter(test_method)
        log_info(
            f"批量AI生成失败，使用传统方法: 测试项 '{requirement_name}' 拆分出 {len(individual_methods)} 个独立测试方法",
            "method_based_generator",
        )

        method_based_cases: Dict[str, List[Dict[str, str]]] = {}

        for method_index, individual_method in enumerate(individual_methods):
            if not individual_method or not individual_method.strip():
                continue

            log_info(
                f"为独立测试方法 '{individual_method[:50]}...' 生成用例",
                "method_based_generator",
            )

            # 生成该独立测试方法对应的测试用例
            test_cases = single_method_generator(
                individual_method,
                test_description,
                requirement_name,
                requirement_desc,
                ceshileixing,
                jianceyi_flag,
                method_index + 1,  # 用于区分同一测试项下的不同方法
            )

            if test_cases:
                method_based_cases[individual_method] = test_cases
            else:
                log_warning(
                    f"独立测试方法 '{individual_method[:50]}...' 未生成用例",
                    "method_based_generator",
                )

        return method_based_cases

    except Exception as e:
        log_error(
            f"fallback 生成测试用例失败: {str(e)}",
            "method_based_generator",
        )
        return {}
