"""
需求分析表AI翻译模块
负责将需求名称翻译成英文标识符，用于生成测试项标识
优先使用 OLLAMA 在线模型进行批量翻译，回退时使用规则生成
"""

import os
import re
import sys
from typing import List, Optional

# 新增：引入在线大模型配置与HTTP请求
import json
import requests
from .....utils.config_utils.config import OLLAMA_HOST, OLLAMA_MODEL

try:
    from ....utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from .....utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug


def _extract_function_name(requirement_name: str) -> str:
    """
    从需求名称中提取功能名称部分，移除编号
    
    Args:
        requirement_name: 原始需求名称
        
    Returns:
        str: 提取的功能名称
    """
    # 移除各种编号格式（如 3.2.1、3.2.2.1 等）
    patterns = [
        r'^\d+(\.\d+)*\.\s*',  # 开头的数字编号，如 "3.2.1. "
        r'^\d+(\.\d+)*\s+',    # 开头的数字编号，如 "3.2.1 "
        r'^\d+[\._]\d+[\._]*\d*\s*',  # 其他数字编号格式
    ]
    
    cleaned = requirement_name
    for pattern in patterns:
        cleaned = re.sub(pattern, '', cleaned)
    
    # 移除其他特殊字符
    cleaned = re.sub(r'[^\u4e00-\u9fff\w\s]', '', cleaned)  # 保留中文、字母、数字、空格
    cleaned = cleaned.strip()
    
    return cleaned if cleaned else requirement_name


def _generate_fallback_identifier(requirement_name: str) -> str:
    """
    生成回退标识符
    
    Args:
        requirement_name: 原始需求名称
        
    Returns:
        str: 回退标识符
    """
    # 尝试从中文生成简单的标识符
    cleaned = _extract_function_name(requirement_name)
    
    # 如果有内容，尝试格式化
    if cleaned and any('\u4e00' <= char <= '\u9fff' for char in cleaned):
        # 包含中文字符，但ArgosTranslate失败了
        return "RequirementFunction"
    else:
        # 可能是英文或其他内容
        formatted = _format_identifier(cleaned)
        return formatted if formatted != "UnknownFunction" else "RequirementFunction"


def _format_identifier(text: str) -> str:
    """
    格式化为驼峰命名法标识符
    
    Args:
        text: 原始文本
        
    Returns:
        str: 格式化后的标识符
    """
    if not text:
        return "UnknownFunction"
        
    # 移除特殊字符和数字
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\d+', '', text)
    
    # 分割单词并转换为驼峰命名法
    words = [word.strip() for word in text.split() if word.strip()]
    if not words:
        return "UnknownFunction"
        
    # 每个单词首字母大写
    formatted_words = []
    for word in words:
        if word and word.replace('_', '').isalpha():  # 只处理字母单词
            # 处理可能的下划线分隔
            sub_words = word.split('_')
            for sub_word in sub_words:
                if sub_word and sub_word.isalpha():
                    formatted_words.append(sub_word.capitalize())
    
    result = ''.join(formatted_words)
    
    # 确保不为空且符合标识符规范
    if not result or not all(c.isalpha() for c in result):
        return "UnknownFunction"
        
    return result


# 新增：一次性批量在线翻译（优先使用）
def _batch_translate_with_ollama(requirement_names: List[str]) -> Optional[List[str]]:
    """
    使用 OLLAMA 一次性翻译多个需求名称，返回按输入顺序的英文标识（驼峰）。
    失败或不可用返回 None。
    """
    try:
        if not requirement_names:
            log_warning("收到空的需求名称列表，直接返回空数组", "ai_translation")
            return []
        log_info(f"准备在线批量翻译，数量: {len(requirement_names)}，HOST: {OLLAMA_HOST}，MODEL: {OLLAMA_MODEL}", "ai_translation")
        # 组装提示词：让模型只返回 JSON 数组
        numbered = "\n".join([f"{i+1}. {name}" for i, name in enumerate(requirement_names)])
        prompt = (
            "你是软件需求抽取助手。请将以下中文需求名称翻译为简短的英文功能标识，采用驼峰命名，不含空格与标点，不加序号。\n"
            "严格只输出一个 JSON 数组，数组元素为字符串，顺序与输入一致。\n"
            "示例输入：1. 用户登录 2. 实时通知推送\n"
            "示例输出：[\"UserLogin\", \"RealtimeNotificationPush\"]\n"
            f"待翻译列表:\n{numbered}\n"
            "只输出JSON数组。"
        )
        url = f"{OLLAMA_HOST.rstrip('/')}/api/generate"
        payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
        log_debug(f"POST {url}，payload长度: {len(json.dumps(payload, ensure_ascii=False))}", "ai_translation")
        resp = requests.post(url, json=payload, timeout=120)
        log_debug(f"HTTP状态: {resp.status_code}", "ai_translation")
        resp.raise_for_status()
        data = resp.json()
        text = data.get("response") or data.get("text") or ""
        log_debug(f"模型原始返回前120字符: {text[:120]}...", "ai_translation")
        # 兼容可能包含解释文本：截取第一个JSON数组
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1 and end > start:
            json_str = text[start:end+1]
            arr = json.loads(json_str)
            if isinstance(arr, list):
                # 规整：仅保留字母字符，首字母大写驼峰
                cleaned: List[str] = []
                for item in arr:
                    s = str(item)
                    s = _clean_translation_result(s)
                    s = _format_identifier(s)
                    cleaned.append(s)
                log_info(f"在线批量翻译成功，返回数量: {len(cleaned)}", "ai_translation")
                if len(cleaned) == len(requirement_names):
                    # 打印前5个样例
                    log_debug(f"样例: {list(zip(requirement_names, cleaned))[:5]}", "ai_translation")
                    return cleaned
                log_warning("返回数量与输入不一致，放弃使用在线结果", "ai_translation")
        log_warning(f"无法从返回文本解析JSON数组", "ai_translation")
        return None
    except Exception as e:
        log_error(f"OLLAMA 批量翻译失败: {e}", "ai_translation")
        return None


def translate_chinese_to_english(requirement_name: str) -> str:
    """
    将需求名称翻译成英文标识符
    
    Args:
        requirement_name: 需求名称（中文）
        
    Returns:
        str: 英文标识符（驼峰命名法）
    """
    try:
        log_debug(f"开始翻译需求名称: {requirement_name}", "ai_translation")
        
        # 预处理：移除编号部分，只保留功能名称
        cleaned_name = _extract_function_name(requirement_name)
        log_debug(f"提取的功能名称: {cleaned_name}", "ai_translation")
        
        # 直接生成回退标识符
        formatted_identifier = _generate_fallback_identifier(requirement_name)
        
        log_info(f"翻译完成: '{requirement_name}' -> '{formatted_identifier}'", "ai_translation")
        return formatted_identifier
        
    except Exception as e:
        log_error(f"翻译需求名称失败: {e}", "ai_translation")
        # 返回默认格式
        fallback = _generate_fallback_identifier(requirement_name)
        log_warning(f"使用回退标识符: {fallback}", "ai_translation")
        return fallback


def _clean_translation_result(text: str) -> str:
    """
    清理翻译结果，移除数字和特殊字符
    
    Args:
        text: 原始翻译结果
        
    Returns:
        str: 清理后的结果
    """
    if not text:
        return ""
        
    # 移除所有数字编号模式（如 3.2.1、3_2_2 等）
    text = re.sub(r'\d+[\._]\d+[\._]*\d*', '', text)
    
    # 移除单独的数字
    text = re.sub(r'\b\d+\b', '', text)
    
    # 移除特殊字符，只保留字母和空格
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    
    # 移除多余的空格
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text


def batch_translate_requirements(requirement_names: List[str]) -> List[str]:
    """
    批量翻译需求名称。优先使用在线 OLLAMA 一次性翻译；若失败或不可用，再逐条使用默认规则回退。
    """
    log_info(f"开始批量翻译 {len(requirement_names)} 个需求名称", "ai_translation")
    # 优先在线批量
    online = _batch_translate_with_ollama(requirement_names)
    if online is not None and len(online) == len(requirement_names):
        log_info("使用 OLLAMA 批量翻译成功（将直接返回在线结果）", "ai_translation")
        return online

    log_warning("在线批量翻译不可用或失败，进入逐条默认规则回退", "ai_translation")
    # 回退：逐条默认处理
    results = []
    for i, requirement_name in enumerate(requirement_names):
        log_debug(f"回退翻译进度: {i+1}/{len(requirement_names)} - {requirement_name}", "ai_translation")
        english_identifier = translate_chinese_to_english(requirement_name)
        results.append(english_identifier)
    log_info(f"批量翻译完成（回退路径），共 {len(results)} 个结果", "ai_translation")
    return results


def get_translation_status() -> dict:
    """
    获取翻译服务状态信息
    
    Returns:
        dict: 状态信息
    """
    return {
        'ollama_host': OLLAMA_HOST,
        'ollama_model': OLLAMA_MODEL,
        'translation_method': 'OLLAMA_Online + Fallback'
    } 