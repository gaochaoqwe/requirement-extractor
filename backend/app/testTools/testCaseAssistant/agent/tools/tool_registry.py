"""工具注册表：将工具名映射到实现函数，并生成 OpenAI function-calling schema"""
from __future__ import annotations
from typing import Any, Dict, List
from .excel_tools import (
    tool_list_sheets,
    tool_get_sheet_info,
    tool_read_range,
    tool_find_rows,
    tool_get_row_count,
)

TOOL_FUNCTIONS: Dict[str, Any] = {
    "list_sheets": tool_list_sheets,
    "get_sheet_info": tool_get_sheet_info,
    "read_range": tool_read_range,
    "find_rows": tool_find_rows,
    "get_row_count": tool_get_row_count,
    # sheet 管理类 op 由前端 bridge 执行，后端只需返回 op 数据，无需实现函数
}

TOOL_SCHEMAS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "list_sheets",
            "description": "列出当前表格所有 sheet 名称",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_sheet_info",
            "description": "列出所有 sheet 的名称和索引号，用于确认目标 sheet 的 index",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_range",
            "description": "读取指定 sheet 的某个行列范围内的单元格文本。先用 get_row_count 确认数据行数。",
            "parameters": {
                "type": "object",
                "properties": {
                    "sheet": {"type": "string", "description": "sheet 名称"},
                    "start_row": {"type": "integer", "description": "起始行号（0-based）"},
                    "end_row": {"type": "integer", "description": "结束行号（含，0-based）"},
                    "start_col": {"type": "integer", "description": "起始列号（0-based），默认 0"},
                    "end_col": {"type": "integer", "description": "结束列号（含，0-based），默认 30"},
                },
                "required": ["sheet", "start_row", "end_row"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_rows",
            "description": "在指定 sheet 中按关键词搜索行，返回匹配的行号和预览",
            "parameters": {
                "type": "object",
                "properties": {
                    "sheet": {"type": "string"},
                    "keyword": {"type": "string"},
                    "col": {"type": "integer", "description": "限定搜索的列号，不填则搜索全行"},
                    "max_results": {"type": "integer", "description": "最多返回条数，默认 20"},
                },
                "required": ["sheet", "keyword"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_row_count",
            "description": "获取指定 sheet 的有效数据行数",
            "parameters": {
                "type": "object",
                "properties": {
                    "sheet": {"type": "string"},
                },
                "required": ["sheet"],
            },
        },
    },
]

# EditPlan 中支持的 sheet 管理 op 类型说明（供 AI system prompt 使用）
SHEET_OP_DOCS = """
sheet 管理操作（写入 EditPlan operations 数组）：
- {"op": "switch_sheet", "sheet": "sheet名称"}  — 切换到指定 sheet（前端会切换显示）
- {"op": "add_sheet", "name": "新sheet名"}       — 新建一个 sheet 并切换到它
- {"op": "rename_sheet", "sheet": "旧名", "name": "新名"} — 重命名 sheet
- {"op": "delete_sheet", "sheet": "sheet名称"}   — 删除指定 sheet
"""


def dispatch_tool(name: str, args: Dict[str, Any], snapshot: List[Dict]) -> Any:
    fn = TOOL_FUNCTIONS.get(name)
    if fn is None:
        return {"error": f"unknown tool: {name}"}
    return fn(snapshot=snapshot, **args)
