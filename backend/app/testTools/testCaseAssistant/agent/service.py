"""Agent 编排：AI tool-calling 循环 + 流式最终回复"""
from __future__ import annotations
import json
import re
import uuid
import os
import httpx
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

from .models import EditPlan, SSEEvent
from .tools.tool_registry import TOOL_SCHEMAS, dispatch_tool

SYSTEM_PROMPT = """你是一个 Excel 智能助手，帮助用户对测试表格进行编辑。

你可以调用以下工具来读取表格内容：
- list_sheets：列出所有 sheet 名称
- get_sheet_info：列出所有 sheet 的名称和索引号
- get_row_count：获取 sheet 行数
- read_range：读取指定行列范围
- find_rows：按关键词搜索行

完成读取后，输出 EditPlan（用 editplan 代码块包裹）：
{
  "operations": [
    {"op": "set_cell", "sheet": "s", "row": 0, "col": 0, "value": "v", "old_value": "old"},
    {"op": "insert_row", "sheet": "s", "after_row": 5, "values": {"0": "A", "1": "B"}},
    {"op": "delete_row", "sheet": "s", "row": 3},
    {"op": "switch_sheet", "sheet": "s"},
    {"op": "add_sheet", "name": "新名"},
    {"op": "rename_sheet", "sheet": "旧名", "name": "新名"},
    {"op": "delete_sheet", "sheet": "s"}
  ],
  "summary": "一句话描述"
}
行列号从 0 开始，old_value 尽量填写。
"""


def _load_ai_config() -> Dict[str, Any]:
    try:
        app_dir = next(
            (p for p in Path(__file__).resolve().parents if p.name == "app"), None
        )
        if app_dir:
            cfg_path = app_dir / "config.json"
            if cfg_path.exists():
                with open(cfg_path, "r", encoding="utf-8") as f:
                    return json.load(f)
    except Exception:
        pass
    return {}


def _extract_edit_plan(text: str) -> Optional[EditPlan]:
    m = re.search(r"```editplan\s*([\s\S]*?)```", text)
    if not m:
        return None
    try:
        data = json.loads(m.group(1).strip())
        return EditPlan(
            plan_id=str(uuid.uuid4()),
            operations=data.get("operations", []),
            summary=data.get("summary", ""),
        )
    except Exception:
        return None


class AgentService:
    MAX_TOOL_ROUNDS = 8

    def __init__(self):
        cfg = _load_ai_config()
        oc = cfg.get("openai", {})
        self.api_key: str = oc.get("api_key", "")
        self.base_url: str = oc.get("base_url", "https://api.openai.com/v1")
        self.model: str = oc.get("model_name") or oc.get("model") or "gpt-4o"
        self._configure_proxy()

    def _configure_proxy(self):
        bypass = ["aliyuncs.com", "deepseek.com", "siliconflow.cn", "moonshot.cn", "bigmodel.cn"]
        if any(d in self.base_url for d in bypass):
            domains = ",".join(bypass)
            os.environ.setdefault("NO_PROXY", domains)
            os.environ.setdefault("no_proxy", domains)

    def _headers(self):
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    async def _call_with_tools(self, client: httpx.AsyncClient, messages: List[Dict]) -> Dict:
        body = {"model": self.model, "messages": messages,
                "tools": TOOL_SCHEMAS, "tool_choice": "auto", "temperature": 0.2}
        resp = await client.post(f"{self.base_url}/chat/completions",
                                 headers=self._headers(), json=body, timeout=120.0)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]

    async def _stream_reply(self, client: httpx.AsyncClient, messages: List[Dict]):
        body = {"model": self.model, "messages": messages, "temperature": 0.2, "stream": True}
        async with client.stream("POST", f"{self.base_url}/chat/completions",
                                 headers=self._headers(), json=body, timeout=120.0) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.startswith("data:"):
                    continue
                raw = line[5:].strip()
                if raw == "[DONE]":
                    return
                try:
                    chunk = json.loads(raw)
                except Exception:
                    continue
                token = (chunk.get("choices") or [{}])[0].get("delta", {}).get("content") or ""
                if token:
                    yield token

    async def run(
        self,
        message: str,
        history: List[Dict[str, str]],
        snapshot: List[Dict[str, Any]],
    ) -> AsyncGenerator[SSEEvent, None]:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for h in history[-10:]:
            messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": message})

        async with httpx.AsyncClient(timeout=120.0) as client:
            for _round in range(self.MAX_TOOL_ROUNDS):
                msg = await self._call_with_tools(client, messages)
                messages.append(msg)

                tool_calls = msg.get("tool_calls") or []
                if tool_calls:
                    for tc in tool_calls:
                        fn_name = tc["function"]["name"]
                        fn_args = json.loads(tc["function"]["arguments"] or "{}")
                        yield SSEEvent(type="tool_call", data={"name": fn_name, "args": fn_args})
                        result = dispatch_tool(fn_name, fn_args, snapshot)
                        yield SSEEvent(type="tool_result", data={"name": fn_name, "result": result})
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": json.dumps(result, ensure_ascii=False),
                        })
                    continue

                # 无 tool_calls：移除非流式 assistant 消息，改用流式重新输出
                messages.pop()
                full_text = ""
                async for token in self._stream_reply(client, messages):
                    full_text += token
                    yield SSEEvent(type="token", data=token)

                plan = _extract_edit_plan(full_text)
                if plan:
                    yield SSEEvent(type="plan", data=plan.dict())

                yield SSEEvent(type="done", data=None)
                return

        yield SSEEvent(type="error", data="超过最大工具调用轮次限制")
