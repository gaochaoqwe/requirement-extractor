from __future__ import annotations

from typing import Any, Dict

from ....utils.logger import setup_session_logger
from .test_item_ai_client import TestItemAIClient


class TestItemService:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.logger = setup_session_logger(session_id)
        self.ai_client = TestItemAIClient(session_id)

    async def extend_sub_requirement_desc(
        self,
        extend_type: str,
        original_sub_requirement_desc: str,
        row_snapshot: Dict[str, Any],
    ) -> str:
        t = str(extend_type or '').strip().lower()
        if t not in {'perf', 'boundary'}:
            raise ValueError('extend_type 必须是 perf 或 boundary')

        self.logger.info('测试项扩展：开始生成S列 extend_type=%s', t)
        self.logger.info('测试项扩展：original_sub_requirement_desc_len=%d', len(str(original_sub_requirement_desc or '')))

        ai_res = await self.ai_client.generate_sub_requirement_desc(
            extend_type=t,
            original_sub_requirement_desc=str(original_sub_requirement_desc or ''),
            row_snapshot=row_snapshot or {},
        )
        if not ai_res.get('success'):
            raise ValueError(ai_res.get('error') or 'AI调用失败')

        new_desc = str(ai_res.get('data', {}).get('new_sub_requirement_desc', '') or '').strip()
        if not new_desc:
            raise ValueError('AI未返回 new_sub_requirement_desc')

        self.logger.info('测试项扩展：生成完成 new_desc_len=%d', len(new_desc))
        return new_desc
