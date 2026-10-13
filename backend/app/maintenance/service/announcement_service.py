"""公告服务（后端写死公告内容）"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class Announcement:
    id: str
    title: str
    content: str
    publish_at: datetime


def get_latest_announcement() -> Announcement:
    """返回当前最新公告（写死）。"""
    # 你可以在这里直接修改内容、发布时间、ID。
    return Announcement(
        id="2025-W51",
        title="本周更新内容",
        content=(
            "1. 新增链路审查模块\n"
            "   - 入口：代码审查 -> 配置项测试测试 -> 链路审查\n"
            "   - 用途：基于功能列表调用链路分析，对功能链路进行AI代码审查，生成问题单\n"
            "\n"
            "2. 函数审查后台新增注释专项审查\n"
            "   - 用途：检查代码中的中文注释与代码逻辑不符、以及注释掉关键逻辑等问题\n"
        ),
        publish_at=datetime(2025, 12, 18, 0, 0, 0),
    )


def get_end_of_natural_week(now: datetime) -> datetime:
    """计算自然周结束时间（下周一 00:00:00）。

    规则：周一为一周开始；“本周不再弹出”= 抑制到下周一零点。
    """
    # Python: Monday=0 ... Sunday=6
    days_until_next_monday = (7 - now.weekday()) % 7
    if days_until_next_monday == 0:
        days_until_next_monday = 7
    next_monday = (now + timedelta(days=days_until_next_monday)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return next_monday
