"""Agent SSE 接口"""
from __future__ import annotations
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from .models import AgentChatRequest
from .service import AgentService

router = APIRouter()


async def _event_stream(request: AgentChatRequest):
    service = AgentService()
    try:
        async for event in service.run(
            message=request.message,
            history=request.history,
            snapshot=request.sheets_snapshot,
        ):
            payload = json.dumps(event.dict(), ensure_ascii=False)
            yield f"data: {payload}\n\n"
    except Exception as e:
        err = json.dumps({"type": "error", "data": str(e)}, ensure_ascii=False)
        yield f"data: {err}\n\n"


@router.post("/agent/chat")
async def agent_chat(request: AgentChatRequest):
    return StreamingResponse(
        _event_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
