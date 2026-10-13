from typing import Any, Dict, List, Tuple

from ....utils.logger import setup_session_logger
from .req_design_api_test_ai_client import ReqDesignApiTestAIClient


class ReqDesignApiTestService:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.logger = setup_session_logger(session_id)
        self.ai_client = ReqDesignApiTestAIClient(session_id)

    async def generate(self, rows) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        results: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []

        for row in rows:
            try:
                payload = {
                    'test_item_name': getattr(row, 'test_item_name', '') or '',
                    'template_test_item_desc': getattr(row, 'template_test_item_desc', '') or '',
                    'template_test_method': getattr(row, 'template_test_method', '') or '',
                }

                self.logger.info(
                    f"需求设计-接口测试：开始处理 row_index={getattr(row, 'row_index', None)}, 测试项名称={payload['test_item_name']}"
                )

                ai_res = await self.ai_client.generate_api_test(payload)
                if not ai_res.get('success'):
                    raise ValueError(ai_res.get('error') or 'AI调用失败')

                data = ai_res['data']

                results.append(
                    {
                        'row_index': getattr(row, 'row_index', None),
                        'test_item_desc': data.get('test_item_desc', ''),
                        'test_method': data.get('test_method', ''),
                    }
                )
                self.logger.info(f"需求设计-接口测试：完成 row_index={getattr(row, 'row_index', None)}")
            except Exception as e:
                err = {'row_index': getattr(row, 'row_index', None), 'error': str(e)}
                errors.append(err)
                self.logger.error(f"需求设计-接口测试：失败 row_index={err['row_index']}, error={err['error']}")

        return results, errors
