"""Excel 批量 AI 生成类任务的进度登记（进程内内存表）。

适用于「上传 Excel → 逐行/逐项调用 AI → 导出新 Excel」这类耗时较长的同步接口
（动态测试问题单生成 / 问题报告单归零意见生成等）：
前端在上传文件时携带自生成的 session_id，随后轮询本模块的进度，
避免用户面对一个没有任何反馈的阻塞请求。

注意：进度仅保存在当前进程内存中（单进程部署即可）；若使用多 worker 或多实例部署，
需替换为 Redis 等共享存储。
"""
from __future__ import annotations

import re
import threading
import time
import uuid
from typing import Any, Dict, List, Optional

_LOCK = threading.Lock()
_PROGRESS: Dict[str, Dict[str, Any]] = {}

# 单条进度最长保留时间（秒），超时自动清理，避免内存无限增长
_TTL_SECONDS = 2 * 60 * 60


def sanitize_session_id(raw: Optional[str]) -> str:
    """只保留安全字符，避免外部传入的 session_id 被用于拼接文件路径。"""
    if not raw:
        return ''
    return re.sub(r'[^0-9a-zA-Z_-]', '', str(raw))[:64]


def resolve_session_id(raw: Optional[str]) -> str:
    """优先使用前端传入的 session_id（便于轮询进度），否则服务端生成。"""
    return sanitize_session_id(raw) or str(uuid.uuid4())


def _new_record(session_id: str) -> Dict[str, Any]:
    return {
        'session_id': session_id,
        'status': 'running',      # running / done / error / not_found
        'percent': 0,
        'message': '',
        'current': 0,             # 已开始处理的条目序号
        'total': 0,               # 待处理的条目总数
        'current_label': '',      # 当前处理的条目名称（测试项名 / 行号）
        'updated_rows': 0,        # 已完成条数（通用计数）
        'error': '',
        'items': [],              # 逐条目明细 [{name, ok, detail}]
        'updated_at': time.time(),
    }


def _prune_locked() -> None:
    now = time.time()
    expired = [
        sid for sid, item in _PROGRESS.items()
        if now - float(item.get('updated_at') or 0) > _TTL_SECONDS
    ]
    for sid in expired:
        _PROGRESS.pop(sid, None)


def _save(session_id: str, **fields: Any) -> Dict[str, Any]:
    """写入/合并一条进度记录。"""
    if not session_id:
        return {}

    with _LOCK:
        record = _PROGRESS.setdefault(session_id, _new_record(session_id))

        append_item: Optional[Dict[str, Any]] = fields.pop('append_item', None)
        record.update(fields)

        if append_item:
            items: List[Dict[str, Any]] = record.setdefault('items', [])
            items.append(append_item)

        record['updated_at'] = time.time()
        _prune_locked()
        return dict(record)


def start_progress(session_id: str, message: str = '任务已开始…') -> Dict[str, Any]:
    """登记任务开始（新建一条 running 记录）。"""
    with _LOCK:
        _PROGRESS.pop(session_id, None)
    return _save(
        session_id,
        status='running',
        percent=1,
        message=message,
        current=0,
        total=0,
        current_label='',
        updated_rows=0,
        error='',
        items=[],
    )


def update_progress(session_id: str, **fields: Any) -> Dict[str, Any]:
    """更新进度字段（percent/message/current/total/current_label/updated_rows/append_item…）。"""
    return _save(session_id, **fields)


def finish_progress(session_id: str, message: str = '生成完成', **fields: Any) -> Dict[str, Any]:
    """标记任务成功完成。"""
    payload = {'status': 'done', 'percent': 100, 'message': message, 'error': ''}
    payload.update(fields)
    return _save(session_id, **payload)


def fail_progress(session_id: str, message: str = '生成失败') -> Dict[str, Any]:
    """标记任务失败。"""
    return _save(session_id, status='error', message=message, error=message)


def get_progress(session_id: str) -> Dict[str, Any]:
    """读取进度；不存在时返回 not_found，便于前端区分“尚未开始”和“已完成”。"""
    with _LOCK:
        record = _PROGRESS.get(session_id)
        if not record:
            return {
                'session_id': session_id,
                'status': 'not_found',
                'percent': 0,
                'message': '',
                'current': 0,
                'total': 0,
                'items': [],
            }
        return dict(record)


def clear_progress(session_id: str) -> None:
    with _LOCK:
        _PROGRESS.pop(session_id, None)
