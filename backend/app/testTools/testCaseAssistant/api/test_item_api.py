from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import uuid

from ..services.test_item_service.test_item_extra.test_item_service import TestItemService

router = APIRouter()


class TestItemExtendRequest(BaseModel):
    extend_type: str = Field(..., description="扩展类型：perf 或 boundary")
    original_sub_requirement_desc: str = Field('', description="原 S 列 需求子项描述")
    row_snapshot: Dict[str, Any] = Field(default_factory=dict, description="原行A~W快照（0-based列索引->文本）")
    session_id: Optional[str] = Field(None, description="可选，会话ID用于日志归档")


class TestItemExtendResponse(BaseModel):
    success: bool
    session_id: str
    new_sub_requirement_desc: str


@router.post('/test-item/extend', response_model=TestItemExtendResponse)
async def test_item_extend(payload: TestItemExtendRequest):
    """测试项扩展：生成新的 S 列需求子项描述"""
    try:
        sid = payload.session_id or str(uuid.uuid4())
        service = TestItemService(session_id=sid)
        new_desc = await service.extend_sub_requirement_desc(
            extend_type=payload.extend_type,
            original_sub_requirement_desc=payload.original_sub_requirement_desc,
            row_snapshot=payload.row_snapshot,
        )
        return {
            'success': True,
            'session_id': sid,
            'new_sub_requirement_desc': new_desc,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
