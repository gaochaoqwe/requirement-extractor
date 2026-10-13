from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class AnnouncementOut(BaseModel):
    id: str
    title: str
    content: str
    publish_at: datetime


class LatestAnnouncementResponse(BaseModel):
    should_show: bool
    announcement: AnnouncementOut | None = None


class SnoozeRequest(BaseModel):
    announcement_id: str


class SnoozeResponse(BaseModel):
    success: bool
    snooze_until: datetime
