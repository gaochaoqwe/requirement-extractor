from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends

from app.maintenance.db import database
from app.maintenance.service.announcement_service import (
    get_end_of_natural_week,
    get_latest_announcement,
)
from app.maintenance.service.auth import require_user
from app.maintenance.api.announcement.schemas import (
    AnnouncementOut,
    LatestAnnouncementResponse,
    SnoozeRequest,
    SnoozeResponse,
)

router = APIRouter()


@router.get("/latest", response_model=LatestAnnouncementResponse)
def latest_announcement(user: dict = Depends(require_user)):
    ann = get_latest_announcement()

    row = database.fetch_one_dict(
        """
        SELECT snooze_until
        FROM maintenance_announcement_snooze
        WHERE user_id = %s AND announcement_id = %s;
        """,
        (user["id"], ann.id),
    )

    now = datetime.now()
    if row and row.get("snooze_until") and row["snooze_until"] > now:
        return LatestAnnouncementResponse(should_show=False, announcement=None)

    # 如果公告还未发布，也不弹
    if ann.publish_at > now:
        return LatestAnnouncementResponse(should_show=False, announcement=None)

    return LatestAnnouncementResponse(
        should_show=True,
        announcement=AnnouncementOut(
            id=ann.id,
            title=ann.title,
            content=ann.content,
            publish_at=ann.publish_at,
        ),
    )


@router.post("/snooze-week", response_model=SnoozeResponse)
def snooze_week(req: SnoozeRequest, user: dict = Depends(require_user)):
    now = datetime.now()
    snooze_until = get_end_of_natural_week(now)

    database.execute(
        """
        INSERT INTO maintenance_announcement_snooze (user_id, announcement_id, snooze_until, created_at, updated_at)
        VALUES (%s, %s, %s, NOW(), NOW())
        ON CONFLICT (user_id, announcement_id)
        DO UPDATE SET snooze_until = EXCLUDED.snooze_until, updated_at = NOW();
        """,
        (user["id"], req.announcement_id, snooze_until),
    )

    return SnoozeResponse(success=True, snooze_until=snooze_until)
