from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class CreateFeedbackRequest(BaseModel):
    type: str = Field(..., description="bug/feature/question/other")
    module: str = Field(..., description="模块")
    content: str
    page_url: str | None = None


class CreateFeedbackResponse(BaseModel):
    success: bool
    feedback_id: int


class FeedbackItem(BaseModel):
    id: int
    user_id: int
    submitter_display_name: str | None = None
    submitter_username: str | None = None
    type: str
    module: str | None = None
    content: str
    page_url: str | None = None
    status: str
    admin_reply: str | None = None
    replied_by_display_name: str | None = None
    replied_by_username: str | None = None
    replied_at: datetime | None = None
    created_at: datetime


class ListMyFeedbackResponse(BaseModel):
    success: bool
    data: list[FeedbackItem]


class AdminReplyRequest(BaseModel):
    admin_reply: str


class AdminReplyResponse(BaseModel):
    success: bool
