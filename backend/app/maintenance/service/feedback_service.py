"""反馈服务"""

from __future__ import annotations

from app.maintenance.db import database
from app.auth.db.database import UserModel


def _fill_user_fields(rows: list[dict]) -> list[dict]:
    user_cache: dict[int, dict] = {}
    for row in rows:
        submitter_id = row.get("user_id")
        if submitter_id is not None:
            submitter_id = int(submitter_id)
            if submitter_id not in user_cache:
                user_cache[submitter_id] = UserModel.get_user_by_id(submitter_id) or {}
            submitter = user_cache.get(submitter_id) or {}
            row["submitter_display_name"] = submitter.get("display_name")
            row["submitter_username"] = submitter.get("username")

        replied_by = row.get("replied_by")
        if replied_by is not None:
            replied_by = int(replied_by)
            if replied_by not in user_cache:
                user_cache[replied_by] = UserModel.get_user_by_id(replied_by) or {}
            replier = user_cache.get(replied_by) or {}
            row["replied_by_display_name"] = replier.get("display_name")
            row["replied_by_username"] = replier.get("username")

        # 不对外暴露 replied_by（接口 schema 不包含该字段）
        if "replied_by" in row:
            row.pop("replied_by", None)

    return rows


def create_feedback(*, user_id: int, type: str, module: str, content: str, page_url: str | None) -> int:
    row = database.fetch_one_dict(
        """
        INSERT INTO maintenance_feedback (user_id, type, module, content, page_url)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
        """,
        (user_id, type, module, content, page_url),
    )
    return int(row["id"])


def list_my_feedback(*, user_id: int, limit: int = 50, offset: int = 0) -> list[dict]:
    rows = database.fetch_all_dict(
        """
        SELECT
            f.id,
            f.user_id,
            NULL::text AS submitter_display_name,
            NULL::text AS submitter_username,
            f.type,
            f.module,
            f.content,
            f.page_url,
            f.status,
            f.admin_reply,
            f.replied_by,
            NULL::text AS replied_by_display_name,
            NULL::text AS replied_by_username,
            f.replied_at,
            f.created_at
        FROM maintenance_feedback f
        WHERE f.user_id = %s
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s;
        """,
        (user_id, limit, offset),
    )

    return _fill_user_fields(rows)


def list_all_feedback(*, limit: int = 200, offset: int = 0) -> list[dict]:
    rows = database.fetch_all_dict(
        """
        SELECT
            f.id,
            f.user_id,
            NULL::text AS submitter_display_name,
            NULL::text AS submitter_username,
            f.type,
            f.module,
            f.content,
            f.page_url,
            f.status,
            f.admin_reply,
            f.replied_by,
            NULL::text AS replied_by_display_name,
            NULL::text AS replied_by_username,
            f.replied_at,
            f.created_at
        FROM maintenance_feedback f
        ORDER BY f.created_at DESC
        LIMIT %s OFFSET %s;
        """,
        (limit, offset),
    )

    return _fill_user_fields(rows)


def admin_reply(*, feedback_id: int, admin_user_id: int, admin_reply: str) -> None:
    database.execute(
        """
        UPDATE maintenance_feedback
        SET admin_reply = %s,
            replied_by = %s,
            replied_at = NOW(),
            status = 'replied'
        WHERE id = %s;
        """,
        (admin_reply, admin_user_id, feedback_id),
    )
