import json
import re
import asyncio
import os
import httpx
from pathlib import Path
from typing import Any, Dict, Optional

from ....utils.logger import get_session_logger


class ReqDesignAIClient:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.logger = get_session_logger(session_id)
        self.config = self._load_config()
        self._init_client()

        self.request_timeout = 180.0
        self.max_retries = 3
        self.retry_delay = 1.5

        # 记录AI原始输出时的最大截断长度，避免日志爆炸
        self.max_log_chars = 2000

    def _sanitize_output_text(self, text: str) -> str:
        if not isinstance(text, str):
            return ''

        out = text
        # 兜底：移除示例说明（用户是举例，不希望出现在结果中）
        # 常见：xx（变量/硬件/中断等） 或 RS422（变量/硬件/中断等）
        out = re.sub(r"[（(]\s*变量\s*/\s*硬件\s*/\s*中断\s*等\s*[）)]", "", out)
        # 也可能出现中文逗号/顿号/空格分隔的变体
        out = re.sub(r"[（(][^）)]*(变量|硬件|中断)[^）)]*[）)]", "", out)
        # 将《变量》/【变量】这类“安全引用符号”统一转换为英文双引号 "变量"
        # 说明：我们在提示词里禁止 AI 在 JSON value 里直接输出英文双引号，以避免生成不合法 JSON。
        # 这里是在 Python 对象层面做替换，FastAPI 序列化时会自动进行 JSON 转义，因此不会再破坏 JSON。
        out = re.sub(r"《\s*([^》]+?)\s*》", r'"\1"', out)
        out = re.sub(r"【\s*([^】]+?)\s*】", r'"\1"', out)

        # 将中文引号也统一成英文双引号
        out = out.replace('“', '"').replace('”', '"')

        # 清理多余空格
        out = re.sub(r"\s{2,}", " ", out).strip()
        return out

    def _parse_known_keys_loose(self, raw: str) -> Optional[Dict[str, Any]]:
        """兜底解析：当 AI 在 value 里使用了未转义的英文双引号导致 JSON 不合法时，按固定 key 进行切片提取。

        目前只支持提取：test_item_desc / test_method / normalized
        """
        try:
            if not isinstance(raw, str) or not raw:
                return None

            s = raw.strip()
            # 粗略要求是 { ... }
            if '{' not in s or '}' not in s:
                return None

            # normalize 场景：只返回 normalized
            kn = '"normalized"'
            pn = s.find(kn)
            if pn >= 0:
                colonn = s.find(':', pn)
                if colonn < 0:
                    return None
                qn = s.find('"', colonn)
                if qn < 0:
                    return None
                segn = s[qn + 1 :]
                end_qn = segn.rfind('"')
                if end_qn < 0:
                    return None
                vn = segn[:end_qn]
                vn = vn.replace('"', '“')
                return {"normalized": vn}

            k1 = '"test_item_desc"'
            k2 = '"test_method"'
            p1 = s.find(k1)
            p2 = s.find(k2)
            if p1 < 0 or p2 < 0:
                return None

            # 取 test_item_desc
            colon1 = s.find(':', p1)
            if colon1 < 0:
                return None
            q1 = s.find('"', colon1)
            if q1 < 0:
                return None

            # test_item_desc 的结束位置：优先找 test_method key 的起点之前的最后一个引号
            seg1 = s[q1 + 1 : p2]
            end_quote_rel = seg1.rfind('"')
            if end_quote_rel < 0:
                return None
            v1 = seg1[:end_quote_rel]

            # 取 test_method
            colon2 = s.find(':', p2)
            if colon2 < 0:
                return None
            q2 = s.find('"', colon2)
            if q2 < 0:
                return None
            seg2 = s[q2 + 1 :]
            end_quote2 = seg2.rfind('"')
            if end_quote2 < 0:
                return None
            v2 = seg2[:end_quote2]

            # 宽松提取到的 value 里可能包含未转义的英文双引号；我们直接替换为中文引号避免再次干扰
            v1 = v1.replace('"', '“')
            v2 = v2.replace('"', '“')

            return {"test_item_desc": v1, "test_method": v2}
        except Exception:
            return None

    def _load_config(self) -> Dict[str, Any]:
        try:
            app_dir = next((p for p in Path(__file__).resolve().parents if p.name == 'app'), None)
            config_path = (app_dir / 'config.json') if app_dir else (Path(__file__).resolve().parents[6] / 'config.json')
            if not config_path.exists():
                self.logger.error(f'配置文件不存在: {config_path}')
                return {}
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            return {}

    def _init_client(self):
        openai_config = self.config.get("openai", {})
        self.api_key = openai_config.get("api_key")
        self.base_url = openai_config.get("base_url", "https://api.openai.com/v1")
        self.model_name = openai_config.get("model_name", "gpt-3.5-turbo")
        self.model_params = self.config.get("model_params", {})

        # 参照 codeReview 的实现：国内AI服务商接口通常不需要代理，且代理可能导致连接问题。
        # 通过设置 NO_PROXY/no_proxy 让 httpx 绕过系统代理。
        self._setup_no_proxy_for_domestic_ai(self.base_url)

    def _setup_no_proxy_for_domestic_ai(self, base_url: str):
        try:
            if not isinstance(base_url, str) or not base_url:
                return

            # 需要绕过代理的域名（按需扩充）
            bypass_proxy_domains = [
                "aliyuncs.com",
                "dashscope.aliyuncs.com",
                "qianfan.baidubce.com",
                "baidubce.com",
                "volces.com",
                "volcengine.com",
                "tencentcloudapi.com",
                "deepseek.com",
                "moonshot.cn",
                "bigmodel.cn",
                "minimax.chat",
                "lingyiwanwu.com",
                "siliconflow.cn",
                "siliconflow.com",
                "hyperbolic.xyz",
            ]

            should_bypass_proxy = any(domain in base_url for domain in bypass_proxy_domains)
            if not should_bypass_proxy:
                return

            no_proxy_list = ",".join(bypass_proxy_domains)
            os.environ["NO_PROXY"] = no_proxy_list
            os.environ["no_proxy"] = no_proxy_list
            self.logger.info(f"检测到国内AI服务商API，配置代理绕过 - base_url: {base_url}")
            self.logger.info(f"已设置NO_PROXY环境变量: {no_proxy_list}")
        except Exception as e:
            self.logger.warning(f"设置NO_PROXY失败: {e}")

    def _build_prompt(
        self,
        test_item_name: str,
        requirement_sub_item_desc: str,
        template_test_item_desc: str,
        template_test_method: str,
    ) -> str:
        # 关键点：只能替换模板中的变量部分，不允许改动模板结构；要求严格 JSON
        return (
            "你是测试工程师助手。\n"
            "任务：根据【测试项名称】和【需求子项描述】，在不改变模板固定文字的前提下，仅替换模板中变量xx的内容。\n"
            "你必须严格输出 JSON，不能输出任何多余文字、不能使用 Markdown。\n"
            "输出 JSON 格式如下：\n"
            "{\"test_item_desc\": \"...\", \"test_method\": \"...\"}\n\n"
            "约束：\n"
            "1) 保持模板固定语句不变，只替换变量部分 xx。\n"
            "2) 模板中可能包含示例说明（如：\"（变量/硬件/中断等）\"），这是举例说明：输出时必须去掉这些示例说明，不能原样带出。\n"
            "3) 为了保证JSON合法：输出的 value 字符串中禁止出现英文双引号 (\")。如果需要强调/引用对象，请使用《》或【】包裹，例如《RS422》。\n"
            "3) 变量内容应从测试项名称中抽取核心对象（如 RS422），必要时结合需求子项描述理解。\n"
            "4) 输出必须是合法 JSON，值必须是字符串。\n\n"
            f"测试项名称：{test_item_name}\n\n"
            f"需求子项描述：{requirement_sub_item_desc}\n\n"
            f"测试项描述模板：{template_test_item_desc}\n\n"
            f"测试方法模板：{template_test_method}\n"
        )

    def _build_common_prompt(
        self,
        test_item_name: str,
        requirement_sub_item_desc: str,
        test_item_desc: str,
        test_method: str,
        variables: Dict[str, Any],
    ) -> str:
        vars_json = "{}"
        try:
            vars_json = json.dumps(variables or {}, ensure_ascii=False)
        except Exception:
            vars_json = "{}"

        return (
            "你是测试工程师助手。\n"
            "任务：根据用户提供的变量取值，对【测试项描述(T列)】与【测试方法(U列)】中的变量占位内容进行替换与整理。\n"
            "注意：这是需求设计-通用功能。你必须只做变量替换与必要的文字清理，不要生成新的测试点/新的步骤，不要扩写。\n"
            "你必须严格输出 JSON，不能输出任何多余文字、不能使用 Markdown。\n"
            "输出 JSON 格式如下：\n"
            '{"test_item_desc": "...", "test_method": "..."}\n\n'
            "规则：\n"
            "1) 只对变量占位符进行替换：变量占位符通常在英文双引号内，内容包含 xx/yy/zz/mm/nn/kk 之一，例如 \"xx（随动/自动扫描等）\"。\n"
            "2) 替换方式：如果双引号内的内容与变量映射中的 key 完全一致，则将双引号内整段内容替换为该 key 对应的 value（value 可能包含 / 分隔的多个值）。\n"
            "3) 除变量替换外，尽量保持原句结构不变；不要新增任何原文没有的变量、步骤、条件、阈值。\n"
            "4) 允许清理示例说明括号（如（随动/自动扫描等））的残留，避免重复表达。\n"
            "5) 为保证 JSON 合法：输出 value 字符串中禁止出现英文双引号(\")，如需引用对象请用《》或【】包裹。\n\n"
            f"测试项名称：{test_item_name}\n\n"
            f"需求子项描述：{requirement_sub_item_desc}\n\n"
            f"变量映射(JSON)：{vars_json}\n\n"
            f"测试项描述(T列)：\n{test_item_desc}\n\n"
            f"测试方法(U列)：\n{test_method}\n"
        )

    def _build_self_check_normalize_prompt(self, raw_text: str) -> str:
        return (
            "你是测试工程师助手。\n"
            "任务：将用户输入的故障类别原始文本，转换成规范的、用英文斜杠/分隔的列表格式。\n"
            "要求：\n"
            "1) 输出必须严格为 JSON，不能输出任何多余文字、不能使用 Markdown。\n"
            "2) JSON 格式：{\"normalized\": \"...\"}\n"
            "3) normalized 的内容必须是：多个故障类别用 / 分隔，例如：主控板故障/随动控制板故障/图像板故障\n"
            "4) 只输出故障类别本身，不要输出编号、解释、换行。\n"
            "5) 为保证 JSON 合法：输出 value 字符串中禁止出现英文双引号(\")，如需引用请用《》或【】包裹。\n\n"
            f"用户输入原文：\n{raw_text}\n"
        )

    def _build_self_check_prompt(
        self,
        test_item_name: str,
        requirement_sub_item_desc: str,
        test_item_desc: str,
        test_method: str,
        variables: Dict[str, Any],
        fault_categories: str,
    ) -> str:
        vars_json = "{}"
        try:
            vars_json = json.dumps(variables or {}, ensure_ascii=False)
        except Exception:
            vars_json = "{}"

        return (
            "你是测试工程师助手。\n"
            "任务：这是需求设计-自检测。根据用户提供的故障类别列表与变量映射，对【测试项描述(T列)】与【测试方法(U列)】中的变量占位内容进行替换与整理。\n"
            "注意：你必须只做变量替换与必要的文字清理，不要生成新的测试点/新的步骤，不要扩写。\n"
            "你必须严格输出 JSON，不能输出任何多余文字、不能使用 Markdown。\n"
            "输出 JSON 格式如下：\n"
            '{"test_item_desc": "...", "test_method": "..."}\n\n'
            "规则：\n"
            "1) 只对变量占位符进行替换：变量占位符通常在英文双引号内，内容包含 xx/yy/zz/mm/nn/kk 之一。\n"
            "2) 替换方式：如果双引号内的内容与变量映射中的 key 完全一致，则将双引号内整段内容替换为该 key 对应的 value。\n"
            "3) fault_categories 仅用于帮助你理解变量替换的上下文，不要把它强行拼接到结果里；除变量替换外，尽量保持原句结构不变。\n"
            "4) 允许清理示例说明括号（如（随动/自动扫描等））的残留，避免重复表达。\n"
            "5) 为保证 JSON 合法：输出 value 字符串中禁止出现英文双引号(\")，如需引用对象请用《》或【】包裹。\n\n"
            f"测试项名称：{test_item_name}\n\n"
            f"需求子项描述：{requirement_sub_item_desc}\n\n"
            f"故障类别(规范格式)：{fault_categories}\n\n"
            f"变量映射(JSON)：{vars_json}\n\n"
            f"测试项描述(T列)：\n{test_item_desc}\n\n"
            f"测试方法(U列)：\n{test_method}\n"
        )

    async def generate_init(self, payload: Dict[str, str]) -> Dict[str, Any]:
        prompt = self._build_prompt(
            payload.get("test_item_name", ""),
            payload.get("requirement_sub_item_desc", ""),
            payload.get("template_test_item_desc", ""),
            payload.get("template_test_method", ""),
        )
        return await self._call_ai_with_retry(prompt)

    async def generate_common(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self._build_common_prompt(
            payload.get("test_item_name", ""),
            payload.get("requirement_sub_item_desc", ""),
            payload.get("test_item_desc", ""),
            payload.get("test_method", ""),
            payload.get("variables", {}) or {},
        )
        return await self._call_ai_with_retry(prompt)

    async def generate_self_check_normalize(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self._build_self_check_normalize_prompt(payload.get("raw_text", ""))
        return await self._call_ai_with_retry_generic(prompt, required_keys=["normalized"])

    async def generate_self_check(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self._build_self_check_prompt(
            payload.get("test_item_name", ""),
            payload.get("requirement_sub_item_desc", ""),
            payload.get("test_item_desc", ""),
            payload.get("test_method", ""),
            payload.get("variables", {}) or {},
            payload.get("fault_categories", ""),
        )
        return await self._call_ai_with_retry(prompt)

    async def _call_ai_with_retry_generic(self, prompt: str, required_keys: Optional[list] = None) -> Dict[str, Any]:
        last_error: Optional[str] = None
        required_keys = required_keys or []

        for attempt in range(self.max_retries):
            try:
                content = await self._call_ai(prompt)
                parsed = self._parse_json_strict(content)
                if not parsed:
                    snippet = (content or "")
                    if len(snippet) > self.max_log_chars:
                        snippet = snippet[: self.max_log_chars] + "...<truncated>"
                    self.logger.warning(f"AI原始返回内容(解析失败，已截断): {snippet}")
                    raise ValueError("AI返回不是合法JSON")

                for k in required_keys:
                    if k not in parsed:
                        raise ValueError(f"AI返回JSON缺少字段: {k}")

                data: Dict[str, Any] = {}
                for k in required_keys:
                    v = parsed.get(k)
                    if not isinstance(v, str):
                        raise ValueError(f"AI返回JSON字段类型错误: {k}")
                    data[k] = self._sanitize_output_text(v)

                return {"success": True, "data": data, "raw": content}
            except Exception as e:
                last_error = str(e)
                self.logger.warning(f"AI调用失败 attempt={attempt + 1}/{self.max_retries}: {last_error}")
                await asyncio.sleep(self.retry_delay)

        return {"success": False, "error": last_error or "AI调用失败"}

    async def _call_ai_with_retry(self, prompt: str) -> Dict[str, Any]:
        last_error: Optional[str] = None

        for attempt in range(self.max_retries):
            try:
                content = await self._call_ai(prompt)
                parsed = self._parse_json_strict(content)
                if not parsed:
                    snippet = (content or "")
                    if len(snippet) > self.max_log_chars:
                        snippet = snippet[: self.max_log_chars] + "...<truncated>"
                    self.logger.warning(f"AI原始返回内容(解析失败，已截断): {snippet}")
                    raise ValueError("AI返回不是合法JSON")

                test_item_desc = parsed.get("test_item_desc")
                test_method = parsed.get("test_method")
                if not isinstance(test_item_desc, str) or not isinstance(test_method, str):
                    raise ValueError("AI返回JSON缺少 test_item_desc/test_method 或类型错误")

                test_item_desc = self._sanitize_output_text(test_item_desc)
                test_method = self._sanitize_output_text(test_method)

                return {"success": True, "data": {"test_item_desc": test_item_desc, "test_method": test_method}, "raw": content}
            except Exception as e:
                last_error = str(e)
                self.logger.warning(f"AI调用失败 attempt={attempt + 1}/{self.max_retries}: {last_error}")
                await asyncio.sleep(self.retry_delay)

        return {"success": False, "error": last_error or "AI调用失败"}

    async def _call_ai(self, prompt: str) -> str:
        if not self.api_key:
            raise ValueError("缺少 openai.api_key 配置")

        url = self.base_url.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        body = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": "你是一个严谨的测试工程师助手。"},
                {"role": "user", "content": prompt},
            ],
        }
        body.update(self.model_params or {})

        timeout = httpx.Timeout(self.request_timeout)
        # trust_env=True: 让 httpx 读取 NO_PROXY/no_proxy 等环境变量，从而绕过代理
        async with httpx.AsyncClient(timeout=timeout, trust_env=True) as client:
            resp = await client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    def _parse_json_strict(self, content: str) -> Optional[Dict[str, Any]]:
        if not isinstance(content, str) or not content.strip():
            return None

        raw = content.strip()

        # 1) 优先处理 ```json ... ``` / ``` ... ``` 代码块
        try:
            fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw, flags=re.IGNORECASE)
            if fence:
                raw = fence.group(1).strip()
        except Exception:
            # ignore
            pass

        # 2) 直接 json.loads
        try:
            return json.loads(raw)
        except Exception:
            pass

        # 3) 尝试从文本中抽取第一个 {...}
        try:
            m = re.search(r"\{[\s\S]*\}", raw)
            if not m:
                return None
            return json.loads(m.group(0))
        except Exception:
            pass

        # 4) 兜底：按固定 key 宽松提取（处理 value 内未转义双引号）
        try:
            loose = self._parse_known_keys_loose(raw)
            return loose
        except Exception:
            return None
