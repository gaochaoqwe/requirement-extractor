import re
from typing import Any, Dict, Optional

from ....utils.logger import get_session_logger
from .req_design_ai_client import ReqDesignAIClient


class ReqDesignApiTestAIClient(ReqDesignAIClient):
    def __init__(self, session_id: str):
        super().__init__(session_id)
        self.logger = get_session_logger(session_id)

    def _build_api_test_generate_prompt(self, test_item_name: str, template_test_item_desc: str, template_test_method: str) -> str:
        return (
            "你是测试工程师助手。\n"
            "任务：这是需求设计-接口测试(模板填空)。根据【测试项名称(O列)】，仅替换模板中的变量占位符，生成并回填【测试项描述(T列)】与【测试方法(U列)】。\n"
            "你必须严格输出 JSON，不能输出任何多余文字、不能使用 Markdown。\n"
            "输出 JSON 格式如下：\n"
            "{\"test_item_desc\": \"...\", \"test_method\": \"...\"}\n\n"
            "规则：\n"
            "1) 你只能在模板中替换变量内容，不能改动模板的其他任何文字、编号、标点、换行结构。\n"
            "2) 变量占位符出现在英文双引号内，形如：\"xx（SRIO/CAN等）\"、\"kk（接收/发送）\"。\n"
            "3) 你要根据测试项名称推断变量：例如 测试项名称=CAN数据发送，则 xx=CAN，kk=发送。\n"
            "4) 替换方式：必须保持引号存在，只替换引号内整段内容为最终值。即替换后仍然是【带引号】的形式。\n"
            "   例如：\"xx（SRIO/CAN等）\" -> \"CAN\"；\"kk（接收/发送）\" -> \"发送\"。\n"
            "5) 如果测试项名称无法确定某个变量的值：保留原占位符不变，不要编造。\n"
            "6) 为保证 JSON 合法：输出的 value 字符串中禁止出现英文双引号(\")。\n"
            "   如果需要输出带引号的效果（比如 \"CAN\" 这种），请用《》来表达引号：例如输出 《CAN》 。\n"
            "   后端会自动把《CAN》转换为 \"CAN\"，因此你必须保留《》以保证最终回填仍有引号。\n\n"
            f"测试项名称：{test_item_name}\n\n"
            f"测试项描述模板(T列)：\n{template_test_item_desc}\n\n"
            f"测试方法模板(U列)：\n{template_test_method}\n"
        )

    async def generate_api_test(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self._build_api_test_generate_prompt(
            payload.get('test_item_name', ''),
            payload.get('template_test_item_desc', ''),
            payload.get('template_test_method', ''),
        )
        return await self._call_ai_with_retry(prompt)
