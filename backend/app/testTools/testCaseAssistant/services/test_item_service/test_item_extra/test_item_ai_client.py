import json
import re
import asyncio
import os
import httpx
from pathlib import Path
from typing import Any, Dict, Optional

from ....utils.logger import get_session_logger


class TestItemAIClient:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.logger = get_session_logger(session_id)
        self.config = self._load_config()
        self._init_client()

        self.request_timeout = 180.0
        self.max_retries = 3
        self.retry_delay = 1.5
        self.max_log_chars = 2000

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
            self.logger.error(f'加载配置文件失败: {e}')
            return {}

    def _init_client(self):
        openai_config = self.config.get('openai', {})
        self.api_key = openai_config.get('api_key')
        self.base_url = openai_config.get('base_url', 'https://api.openai.com/v1')
        self.model_name = openai_config.get('model_name', 'gpt-3.5-turbo')
        self.model_params = self.config.get('model_params', {})
        self._setup_no_proxy_for_domestic_ai(self.base_url)

    def _setup_no_proxy_for_domestic_ai(self, base_url: str):
        try:
            if not isinstance(base_url, str) or not base_url:
                return

            bypass_proxy_domains = [
                'aliyuncs.com',
                'dashscope.aliyuncs.com',
                'qianfan.baidubce.com',
                'baidubce.com',
                'volces.com',
                'volcengine.com',
                'tencentcloudapi.com',
                'deepseek.com',
                'moonshot.cn',
                'bigmodel.cn',
                'minimax.chat',
                'lingyiwanwu.com',
                'siliconflow.cn',
                'siliconflow.com',
                'hyperbolic.xyz',
            ]

            if not any(d in base_url for d in bypass_proxy_domains):
                return

            no_proxy_list = ','.join(bypass_proxy_domains)
            os.environ['NO_PROXY'] = no_proxy_list
            os.environ['no_proxy'] = no_proxy_list
        except Exception as e:
            self.logger.warning(f'设置NO_PROXY失败: {e}')

    def _sanitize_output_text(self, text: str) -> str:
        if not isinstance(text, str):
            return ''
        out = text
        out = out.replace('“', '"').replace('”', '"')
        out = re.sub(r"\s{2,}", " ", out).strip()
        return out

    def _parse_json_strict(self, content: str) -> Optional[Dict[str, Any]]:
        if not isinstance(content, str) or not content.strip():
            return None

        raw = content.strip()
        try:
            fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw, flags=re.IGNORECASE)
            if fence:
                raw = fence.group(1).strip()
        except Exception:
            pass

        try:
            return json.loads(raw)
        except Exception:
            pass

        try:
            m = re.search(r"\{[\s\S]*\}", raw)
            if not m:
                return None
            return json.loads(m.group(0))
        except Exception:
            return None

    def _build_prompt(self, extend_type: str, original_sub_requirement_desc: str, row_snapshot: Dict[str, Any]) -> str:
        mode_cn = '性能测试' if extend_type == 'perf' else '边界测试'
        # row_snapshot 为 0-based col -> text；这里只做上下文提供，不要求 AI 改模板，只输出新的S列描述
        snapshot_str = ''
        perf_hint = ''
        boundary_hint = ''
        try:
            keys = sorted(row_snapshot.keys(), key=lambda x: int(x) if str(x).isdigit() else 10**9)
            parts = []
            perf_parts = []
            boundary_parts = []
            boundary_keywords = ['边界', '范围', '最大', '最小', '上限', '下限', '极限', '临界', '溢出', '超时', '长度', '容量', '并发']
            for k in keys:
                v = row_snapshot.get(k)
                if v is None:
                    continue
                vs = str(v).strip()
                if not vs:
                    continue
                parts.append(f"col_{k}={vs}")

                if '性能' in vs:
                    perf_parts.append(vs)
                elif any(kw in vs for kw in boundary_keywords):
                    boundary_parts.append(vs)
            snapshot_str = '\n'.join(parts[:60])

            perf_hint = '\n'.join(perf_parts[:20])
            boundary_hint = '\n'.join(boundary_parts[:20])
        except Exception:
            snapshot_str = ''
            perf_hint = ''
            boundary_hint = ''

        return (
            '你是资深测试工程师助手。\n'
            f'任务：基于给定的“需求子项描述(S列)”和行快照内容，提取并整理出【{mode_cn}】相关的“需求约束/需求指标”。\n'
            '注意：当前工作是“需求提取/需求整理”（站在开发人员立场），不是测试用例设计、不是测试项分析。\n'
            '要求：\n'
            '1) 只输出 JSON，不能输出任何多余文字、不能输出 Markdown。\n'
            '2) JSON 格式：{"new_sub_requirement_desc": "..."}\n'
            '3) 输出必须结合上下文术语（例如接口名、模块名），不要杜撰不存在的接口/参数。\n'
            '4) 输出必须是“需求描述”，而不是测试用例/测试步骤/测试项枚举：禁止输出类似“长度为0/1/255/256时...”这类测试点列表。\n'
            '5) 禁止编造任何原文未明确给出的数值阈值/范围/枚举（例如不要凭空生成0/1/255/256、7/8/128/129等）。\n'
            '6) 如果原文中已经存在数值/阈值/范围/约束（如“≥8字符”“有效期2小时”“95%≤2秒”“并发50/s”等），允许原样引用并整理成清晰的需求句子。\n'
            '7) 当扩展类型为 perf（性能测试）时：你必须优先使用“行快照-性能字段候选”中的原文性能指标；不要从其他字段推断额外性能指标。\n'
            '8) 当扩展类型为 boundary（边界测试）时：你必须忽略“行快照-性能字段候选”，不能把性能指标当成边界需求来源；只从原S列以及其它非性能字段（输入/约束/限制/格式/长度/有效期/支持范围等）中提取边界相关需求，并整理为需求描述。\n\n'
            f'扩展类型：{extend_type}（{mode_cn}）\n\n'
            f'原S列需求子项描述：\n{original_sub_requirement_desc}\n\n'
            f'行快照-性能字段候选(仅 perf 可用，boundary 必须忽略)：\n{perf_hint}\n\n'
            f'行快照-边界线索候选(优先用于 boundary)：\n{boundary_hint}\n\n'
            f'同一行上下文字段快照(部分)：\n{snapshot_str}\n'
        )

    async def generate_sub_requirement_desc(self, extend_type: str, original_sub_requirement_desc: str, row_snapshot: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self._build_prompt(extend_type, original_sub_requirement_desc, row_snapshot)
        return await self._call_ai_with_retry(prompt)

    async def _call_ai_with_retry(self, prompt: str) -> Dict[str, Any]:
        last_error: Optional[str] = None
        for attempt in range(self.max_retries):
            try:
                content = await self._call_ai(prompt)
                parsed = self._parse_json_strict(content)
                if not parsed or not isinstance(parsed.get('new_sub_requirement_desc'), str):
                    snippet = (content or '')
                    if len(snippet) > self.max_log_chars:
                        snippet = snippet[: self.max_log_chars] + '...<truncated>'
                    self.logger.warning(f'AI原始返回内容(解析失败，已截断): {snippet}')
                    raise ValueError('AI返回不是合法JSON或缺少 new_sub_requirement_desc')

                data = {
                    'new_sub_requirement_desc': self._sanitize_output_text(parsed.get('new_sub_requirement_desc', '')),
                }
                return {'success': True, 'data': data, 'raw': content}
            except Exception as e:
                last_error = str(e)
                self.logger.warning(f'AI调用失败 attempt={attempt + 1}/{self.max_retries}: {last_error}')
                await asyncio.sleep(self.retry_delay)
        return {'success': False, 'error': last_error or 'AI调用失败'}

    async def _call_ai(self, prompt: str) -> str:
        if not self.api_key:
            raise ValueError('缺少 openai.api_key 配置')

        url = self.base_url.rstrip('/') + '/chat/completions'
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }

        body = {
            'model': self.model_name,
            'messages': [
                {'role': 'system', 'content': '你是一个严谨的测试工程师助手。'},
                {'role': 'user', 'content': prompt},
            ],
        }
        body.update(self.model_params or {})

        timeout = httpx.Timeout(self.request_timeout)
        async with httpx.AsyncClient(timeout=timeout, trust_env=True) as client:
            resp = await client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
            return data['choices'][0]['message']['content']
