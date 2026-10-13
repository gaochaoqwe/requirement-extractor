from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.maintenance.api.feedback.schemas import (
    AdminReplyRequest,
    AdminReplyResponse,
    CreateFeedbackRequest,
    CreateFeedbackResponse,
    FeedbackItem,
    ListMyFeedbackResponse,
)
from app.maintenance.service.auth import require_admin, require_user
from app.maintenance.service import feedback_service

router = APIRouter()


@router.post("/", response_model=CreateFeedbackResponse)
def create_feedback(req: CreateFeedbackRequest, user: dict = Depends(require_user)):
    feedback_id = feedback_service.create_feedback(
        user_id=int(user["id"]),
        type=req.type,
        module=req.module,
        content=req.content,
        page_url=req.page_url,
    )
    return CreateFeedbackResponse(success=True, feedback_id=feedback_id)


@router.get("/mine", response_model=ListMyFeedbackResponse)
def list_my_feedback(
    user: dict = Depends(require_user),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    rows = feedback_service.list_my_feedback(user_id=int(user["id"]), limit=limit, offset=offset)
    return ListMyFeedbackResponse(success=True, data=[FeedbackItem(**r) for r in rows])


@router.get("/all", response_model=ListMyFeedbackResponse)
def list_all_feedback(
    user: dict = Depends(require_admin),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    rows = feedback_service.list_all_feedback(limit=limit, offset=offset)
    return ListMyFeedbackResponse(success=True, data=[FeedbackItem(**r) for r in rows])


@router.post("/{feedback_id}/reply", response_model=AdminReplyResponse)
def reply_feedback(
    feedback_id: int,
    req: AdminReplyRequest,
    user: dict = Depends(require_admin),
):
    feedback_service.admin_reply(
        feedback_id=int(feedback_id),
        admin_user_id=int(user["id"]),
        admin_reply=req.admin_reply,
    )
    return AdminReplyResponse(success=True)
