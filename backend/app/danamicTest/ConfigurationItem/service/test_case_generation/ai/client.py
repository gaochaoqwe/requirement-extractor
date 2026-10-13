"""
AI 客户端模块
职责：封装与 OLLAMA 的交互与重试、清理、基础校验。返回 JSON 字符串或空串。
"""
from typing import Optional
import json
import logging
import re
import requests

try:
    from ...utils.config_utils.config import OLLAMA_HOST, OLLAMA_MODEL
    from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ....utils.config_utils.config import OLLAMA_HOST, OLLAMA_MODEL
        from ....utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.config_utils.config import OLLAMA_HOST, OLLAMA_MODEL
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

logger = logging.getLogger(__name__)


def _clean_response(response: str) -> str:
    """清理AI响应文本：移除think标签、markdown代码块包裹与多余空白"""
    # 移除think标签
    response = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL | re.IGNORECASE)
    # 移除markdown代码块标记
    response = re.sub(r"```json\s*", "", response)
    response = re.sub(r"```\s*$", "", response)
    return response.strip()


def call_ai_for_batch_generation(prompt: str, max_retry: int = 3) -> str:
    """
    调用AI模型进行批量测试用例生成。
    返回清理后的、可被 json.loads 解析的 JSON 字符串；失败返回空串。
    """
    try:
        params = {
            "system": "你是一个专业的软件测试工程师，专门负责根据测试方法生成详细的测试用例。请严格按照提供的JSON格式输出。",
            "prompt": prompt,
            "model": OLLAMA_MODEL,
            "stream": False,
        }
        for attempt in range(max_retry):
            try:
                log_debug(f"调用AI模型进行批量生成，第 {attempt + 1} 次尝试", "method_based_generator")
                res = requests.post(url=f"{OLLAMA_HOST}/api/generate", json=params, verify=False)
                response = res.json()["response"]
                cleaned = _clean_response(response)
                data = json.loads(cleaned)
                if isinstance(data, dict) and "test_cases_by_method" in data:
                    return json.dumps(data, ensure_ascii=False)
            except Exception as e:
                log_warning(f"第 {attempt + 1} 次AI调用失败: {str(e)}", "method_based_generator")
                if attempt == max_retry - 1:
                    log_error(f"批量生成失败，最后一次尝试失败: {str(e)}", "method_based_generator")
                    return ""
        return ""
    except Exception as e:
        log_error(f"调用AI模型进行批量生成失败: {str(e)}", "method_based_generator")
        return ""


def call_ai_for_simple_generation(system_prompt: str, user_prompt: str, max_retry: int = 3) -> str:
    """
    调用AI模型进行单测试项用例生成，期望返回格式：{"test_cases": [...]} 的JSON字符串；失败返回空串。
    """
    try:
        params = {
            "model": OLLAMA_MODEL,
            "stream": False,
            "system": system_prompt,
            "prompt": user_prompt,
        }
        for attempt in range(max_retry):
            try:
                log_debug(f"调用AI模型进行实时生成，第 {attempt + 1} 次尝试", "realtime_generator")
                res = requests.post(url=f"{OLLAMA_HOST}/api/generate", json=params, verify=False)
                response = res.json().get("response", "")
                cleaned = _clean_response(response)
                data = json.loads(cleaned)
                if isinstance(data, dict) and "test_cases" in data and isinstance(data["test_cases"], list):
                    return json.dumps(data, ensure_ascii=False)
            except Exception as e:
                log_warning(f"实时生成第 {attempt + 1} 次AI调用失败: {str(e)}", "realtime_generator")
                if attempt == max_retry - 1:
                    log_error(f"实时生成失败，最后一次尝试失败: {str(e)}", "realtime_generator")
                    return ""
        return ""
    except Exception as e:
        log_error(f"调用AI模型进行实时生成失败: {str(e)}", "realtime_generator")
        return ""
