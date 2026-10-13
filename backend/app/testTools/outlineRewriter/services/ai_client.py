"""
大纲二次编写 AI 客户端
复用项目现有的 httpx + OpenAI 兼容接口调用模式
"""
import json
import time
import httpx
from pathlib import Path
from typing import Dict, Any

from ..utils.logger import get_session_logger


class OutlineAIClient:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.logger = get_session_logger(session_id)
        self.config = self._load_config()
        self._init_client()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = Path(__file__).parent.parent.parent.parent / "config.json"
            if not config_path.exists():
                self.logger.error(f"配置文件不存在: {config_path}")
                return {}
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            return {}

    def _init_client(self):
        try:
            openai_cfg = self.config.get("openai", {})
            self.api_key = openai_cfg.get("api_key", "")
            self.base_url = openai_cfg.get("base_url", "https://api.openai.com/v1")
            self.model_name = openai_cfg.get("model_name", "gpt-3.5-turbo")
            self.model_params = self.config.get("model_params", {})

            self.proxies = None
            proxy_cfg = self.config.get("proxy", {})
            if proxy_cfg.get("enabled", False) and "hyperbolic.xyz" not in self.base_url:
                self.proxies = {
                    "http://": proxy_cfg.get("http"),
                    "https://": proxy_cfg.get("https"),
                }
            self.logger.info(f"AI客户端初始化完成 - 模型: {self.model_name}")
        except Exception as e:
            self.logger.error(f"初始化AI客户端失败: {e}")

    async def generate_section_content(
        self,
        section_title: str,
        section_number: str,
        extra_info: str,
        document_title: str,
        prompt_template: str,
    ) -> Dict[str, Any]:
        """
        为单个章节生成内容

        Args:
            section_title:    章节标题文本
            section_number:   章节编号（如 "1.2"）
            extra_info:       用户在前端填写的额外说明
            document_title:   大纲文档标题
            prompt_template:  提示词模板（从 prompts/outline_prompt.md 读取）
        """
        prompt = prompt_template.format(
            document_title=document_title,
            section_number=section_number,
            section_title=section_title,
            extra_info=extra_info or "无",
        )

        self.logger.info(f"开始生成章节内容: [{section_number}] {section_title}")
        result = await self._call_ai(prompt)
        if result["success"]:
            self.logger.info(f"章节 [{section_number}] 生成成功")
        return result

    async def _call_ai(self, prompt: str) -> Dict[str, Any]:
        start = time.time()
        try:
            self.logger.info("=" * 60)
            self.logger.info(f"AI请求提示词:\n{prompt}")
            self.logger.info("=" * 60)

            request_data = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                **self.model_params,
            }

            async with httpx.AsyncClient(timeout=120.0, proxies=self.proxies) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=request_data,
                )
                response.raise_for_status()
                result = response.json()

            content = result["choices"][0]["message"]["content"]
            elapsed = time.time() - start
            self.logger.info(f"AI响应（{elapsed:.2f}s）:\n{content}")
            return {"success": True, "content": content, "elapsed": elapsed}

        except Exception as e:
            elapsed = time.time() - start
            self.logger.error(f"AI调用失败（{elapsed:.2f}s）: {e}")
            return {"success": False, "error": str(e), "elapsed": elapsed}
