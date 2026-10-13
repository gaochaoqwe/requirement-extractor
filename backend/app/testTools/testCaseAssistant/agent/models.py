from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field
import uuid


class CellOp(BaseModel):
    op: Literal["set_cell"]
    sheet: str
    row: int
    col: int
    value: str
    old_value: Optional[str] = None


class InsertRowOp(BaseModel):
    op: Literal["insert_row"]
    sheet: str
    after_row: int
    values: Dict[str, str] = Field(default_factory=dict)


class DeleteRowOp(BaseModel):
    op: Literal["delete_row"]
    sheet: str
    row: int


AnyOp = Union[CellOp, InsertRowOp, DeleteRowOp]


class EditPlan(BaseModel):
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    operations: List[Dict[str, Any]]
    summary: str


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "tool"]
    content: str
    plan: Optional[EditPlan] = None


class AgentChatRequest(BaseModel):
    task_id: str
    message: str
    mode: Literal["auto", "step"] = "step"
    history: List[Dict[str, str]] = Field(default_factory=list)
    sheets_snapshot: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="前端当前 spreadsheet 数据快照，用于 AI 读取上下文",
    )


class SSEEvent(BaseModel):
    type: Literal["text", "plan", "tool_call", "tool_result", "done", "error"]
    data: Any
