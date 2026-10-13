"""
从 Qwen3 模型文本中解析工具调用。

部分 vLLM / model_gateway 部署会把原生 XML 工具调用放在 reasoning / reasoning_content 中，
而 OpenAI 兼容响应的 message.tool_calls 为空。解析逻辑参考：
- Continue openaiTypeConverters.fromChatResponse：单独读取 reasoning_content / reasoning
- vLLM qwen3_xml 格式：<tool_call><function=name><parameter=key>val</parameter></function></tool_call>
- Continue CLI extractToolCalls：<tool>{"name":...,"arguments":...}</tool>
"""
from __future__ import annotations

import json
import re
import uuid
from typing import Any, Dict, List, Optional

# Qwen3 XML（vLLM qwen3_xml / qwen3_coder 常见输出）
_TOOL_CALL_BLOCK_RE = re.compile(
    r"<tool_call>\s*([\s\S]*?)\s*</tool_call>", re.IGNORECASE
)
_FUNCTION_EQ_RE = re.compile(r"<function=([^>\s/]+)\s*>", re.IGNORECASE)
_FUNCTION_NAME_ATTR_RE = re.compile(
    r'<function\s+name=["\']([^"\']+)["\']\s*>', re.IGNORECASE
)
_PARAMETER_EQ_RE = re.compile(
    r"<parameter=([^>\s]+)\s*>([\s\S]*?)</parameter>", re.IGNORECASE
)
_PARAMETER_NAME_ATTR_RE = re.compile(
    r'<parameter\s+name=["\']([^"\']+)["\']\s*>([\s\S]*?)</parameter>',
    re.IGNORECASE,
)

# Continue CLI：<tool>{"name":"x","arguments":{}}</tool>
_TOOL_JSON_BLOCK_RE = re.compile(r"<tool>\s*([\s\S]*?)\s*</tool>", re.IGNORECASE)

# 思考块标签（剥离后仅保留可解析片段）
_THINKING_WRAPPER_RE = re.compile(
    r"</?(?:think|redacted_thinking)[^>]*>", re.IGNORECASE
)


def _new_tool_call_id() -> str:
    return f"call_{uuid.uuid4().hex[:12]}"


def _normalize_arguments(arguments: Any) -> str:
    if arguments is None:
        return "{}"
    if isinstance(arguments, str):
        stripped = arguments.strip()
        if not stripped:
            return "{}"
        try:
            json.loads(stripped)
            return stripped
        except json.JSONDecodeError:
            return json.dumps({"value": stripped}, ensure_ascii=False)
    if isinstance(arguments, dict):
        return json.dumps(arguments, ensure_ascii=False)
    return json.dumps(arguments, ensure_ascii=False)


def _build_openai_tool_call(name: str, arguments: Any) -> Dict[str, Any]:
    return {
        "id": _new_tool_call_id(),
        "type": "function",
        "function": {
            "name": name,
            "arguments": _normalize_arguments(arguments),
        },
    }


def _parse_json_tool_payload(payload: str) -> Optional[Dict[str, Any]]:
    text = payload.strip()
    if not text:
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None

    name = data.get("name") or data.get("tool") or data.get("function")
    if not name or not isinstance(name, str):
        return None

    arguments = (
        data.get("arguments")
        if "arguments" in data
        else data.get("parameters", {})
    )
    return _build_openai_tool_call(name, arguments)


def _parse_function_block(block: str) -> Optional[Dict[str, Any]]:
    fn_match = _FUNCTION_EQ_RE.search(block) or _FUNCTION_NAME_ATTR_RE.search(block)
    if not fn_match:
        return None

    fn_name = fn_match.group(1).strip()
    args: Dict[str, Any] = {}

    for pm in _PARAMETER_EQ_RE.finditer(block):
        args[pm.group(1).strip()] = pm.group(2).strip()
    for pm in _PARAMETER_NAME_ATTR_RE.finditer(block):
        args[pm.group(1).strip()] = pm.group(2).strip()

    if args:
        return _build_openai_tool_call(fn_name, args)

    # <function=name> 后紧跟 JSON 对象
    after_fn = block[fn_match.end() :]
    end_fn = re.search(r"</function>", after_fn, re.IGNORECASE)
    body = after_fn[: end_fn.start()] if end_fn else after_fn
    body = body.strip()
    if body.startswith("{"):
        try:
            parsed = json.loads(body)
            if isinstance(parsed, dict):
                return _build_openai_tool_call(fn_name, parsed)
        except json.JSONDecodeError:
            pass

    return _build_openai_tool_call(fn_name, {})


def extract_reasoning_text(message: Any) -> str:
    """
    从 OpenAI ChatCompletionMessage 提取 reasoning 文本。
    对齐 Continue core/llm/openaiTypeConverters.ts fromChatResponse。
    """
    parts: List[str] = []

    for attr in ("reasoning_content", "reasoning"):
        value = getattr(message, attr, None)
        if isinstance(value, str) and value.strip():
            parts.append(value)

    if hasattr(message, "model_dump"):
        try:
            dumped = message.model_dump()
            for key in ("reasoning_content", "reasoning"):
                value = dumped.get(key)
                if isinstance(value, str) and value.strip() and value not in parts:
                    parts.append(value)
        except Exception:
            pass

    if hasattr(message, "model_extra") and message.model_extra:
        extra = message.model_extra
        if isinstance(extra, dict):
            for key in ("reasoning_content", "reasoning"):
                value = extra.get(key)
                if isinstance(value, str) and value.strip() and value not in parts:
                    parts.append(value)

    return "\n".join(parts)


def parse_tool_calls_from_text(text: str) -> List[Dict[str, Any]]:
    """从 content / reasoning 文本中解析 Qwen3 XML 或 Continue 风格工具调用。"""
    if not text or not text.strip():
        return []

    normalized = _THINKING_WRAPPER_RE.sub("\n", text)
    tool_calls: List[Dict[str, Any]] = []
    seen: set = set()

    def _add(call: Optional[Dict[str, Any]]) -> None:
        if not call:
            return
        key = (
            call["function"]["name"],
            call["function"]["arguments"],
        )
        if key in seen:
            return
        seen.add(key)
        tool_calls.append(call)

    for match in _TOOL_CALL_BLOCK_RE.finditer(normalized):
        block = match.group(1).strip()
        parsed_json = _parse_json_tool_payload(block)
        if parsed_json:
            _add(parsed_json)
            continue
        _add(_parse_function_block(block))

    for match in _TOOL_JSON_BLOCK_RE.finditer(normalized):
        _add(_parse_json_tool_payload(match.group(1)))

    return tool_calls


def supplement_tool_calls_from_reasoning(
    message: Any,
    existing_tool_calls: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    当 message.tool_calls 为空时，从 reasoning / content 中补全工具调用。
    """
    if existing_tool_calls:
        return existing_tool_calls

    reasoning = extract_reasoning_text(message)
    content = getattr(message, "content", None) or ""
    combined = "\n".join(part for part in (reasoning, content) if part)
    return parse_tool_calls_from_text(combined)
