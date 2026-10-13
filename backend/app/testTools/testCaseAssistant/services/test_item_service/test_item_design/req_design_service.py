from typing import Any, Dict, List, Tuple

from ....utils.logger import setup_session_logger
from .req_design_ai_client import ReqDesignAIClient


class RequirementDesignService:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.logger = setup_session_logger(session_id)
        self.ai_client = ReqDesignAIClient(session_id)

    async def req_design_init(self, rows) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        results: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []

        for row in rows:
            try:
                payload = {
                    "test_item_name": row.test_item_name,
                    "requirement_sub_item_desc": row.requirement_sub_item_desc,
                    "template_test_item_desc": row.template_test_item_desc,
                    "template_test_method": row.template_test_method,
                }

                self.logger.info(f"需求设计-初始化：开始处理 row_index={row.row_index}, 测试项名称={row.test_item_name}")
                ai_res = await self.ai_client.generate_init(payload)
                if not ai_res.get("success"):
                    raise ValueError(ai_res.get("error") or "AI调用失败")

                data = ai_res["data"]
                results.append(
                    {
                        "row_index": row.row_index,
                        "test_item_desc": data["test_item_desc"],
                        "test_method": data["test_method"],
                    }
                )
                self.logger.info(f"需求设计-初始化：完成 row_index={row.row_index}")
            except Exception as e:
                err = {"row_index": getattr(row, "row_index", None), "error": str(e)}
                errors.append(err)
                self.logger.error(f"需求设计-初始化：失败 row_index={err['row_index']}, error={err['error']}")

        return results, errors

    async def req_design_common(
        self,
        test_item_name: str,
        requirement_sub_item_desc: str,
        test_item_desc: str,
        test_method: str,
        variables: Dict[str, str],
    ) -> Dict[str, Any]:
        payload = {
            "test_item_name": test_item_name or "",
            "requirement_sub_item_desc": requirement_sub_item_desc or "",
            "test_item_desc": test_item_desc or "",
            "test_method": test_method or "",
            "variables": variables or {},
        }

        self.logger.info(f"需求设计-通用功能：开始处理 测试项名称={test_item_name}")
        ai_res = await self.ai_client.generate_common(payload)
        if not ai_res.get("success"):
            raise ValueError(ai_res.get("error") or "AI调用失败")

        data = ai_res["data"]
        self.logger.info("需求设计-通用功能：完成")
        return {
            "test_item_desc": data["test_item_desc"],
            "test_method": data["test_method"],
        }

    async def req_design_self_check_normalize_fault_categories(self, raw_text: str) -> str:
        payload = {
            "raw_text": raw_text or "",
        }

        self.logger.info("需求设计-自检测：故障类别格式转换开始")
        ai_res = await self.ai_client.generate_self_check_normalize(payload)
        if not ai_res.get("success"):
            raise ValueError(ai_res.get("error") or "AI调用失败")

        data = ai_res["data"]
        normalized = data.get("normalized")
        if not isinstance(normalized, str):
            raise ValueError("AI返回normalized类型错误")

        self.logger.info("需求设计-自检测：故障类别格式转换完成")
        return normalized

    async def req_design_self_check(
        self,
        test_item_name: str,
        requirement_sub_item_desc: str,
        test_item_desc: str,
        test_method: str,
        variables: Dict[str, str],
        fault_categories: str,
    ) -> Dict[str, Any]:
        payload = {
            "test_item_name": test_item_name or "",
            "requirement_sub_item_desc": requirement_sub_item_desc or "",
            "test_item_desc": test_item_desc or "",
            "test_method": test_method or "",
            "variables": variables or {},
            "fault_categories": fault_categories or "",
        }

        self.logger.info("需求设计-自检测：开始处理")
        ai_res = await self.ai_client.generate_self_check(payload)
        if not ai_res.get("success"):
            raise ValueError(ai_res.get("error") or "AI调用失败")

        data = ai_res["data"]
        self.logger.info("需求设计-自检测：完成")
        return {
            "test_item_desc": data["test_item_desc"],
            "test_method": data["test_method"],
        }
