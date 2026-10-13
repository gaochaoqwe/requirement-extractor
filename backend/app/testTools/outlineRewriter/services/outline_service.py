"""
大纲二次编写核心服务
使用 OfficeCLI 完成 docx 解析与填充
"""
import asyncio
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from ..config.config import OFFICECLI_EXE, AI_GENERATION_CONFIG
from ..utils.logger import get_session_logger
from .ai_client import OutlineAIClient

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "outline_prompt.md"


class OutlineRewriterService:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.logger = get_session_logger(session_id)
        self.ai_client = OutlineAIClient(session_id)
        self._prompt_template = self._load_prompt()

    # ------------------------------------------------------------------
    # 提示词
    # ------------------------------------------------------------------

    def _load_prompt(self) -> str:
        try:
            with open(PROMPT_PATH, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"加载提示词失败: {e}")
            return (
                "你正在协助编写《{document_title}》的鉴定测评大纲。\n"
                "当前章节：{section_number} {section_title}\n"
                "用户补充说明：{extra_info}\n\n"
                "请根据章节标题和补充说明，生成该章节的正文内容。"
                "要求语言专业、简洁，符合鉴定测评规范。不要输出markdown格式。"
            )

    # ------------------------------------------------------------------
    # OfficeCLI 工具方法
    # ------------------------------------------------------------------

    def _run_cli(self, *args: str, timeout: int = 60) -> Dict[str, Any]:
        """同步调用 OfficeCLI，返回解析后的 JSON"""
        cmd = [str(OFFICECLI_EXE)] + list(args) + ["--json"]
        self.logger.info(f"OfficeCLI: {' '.join(str(a) for a in args)}")
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=timeout,
            )
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            if stderr:
                self.logger.warning(f"OfficeCLI stderr: {stderr}")
            if not stdout:
                return {"success": False, "error": "OfficeCLI 无输出"}
            return json.loads(stdout)
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"OfficeCLI 超时（>{timeout}s）")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"OfficeCLI 返回无效 JSON: {e}")
        except Exception as e:
            self.logger.error(f"OfficeCLI 调用失败: {e}")
            raise

    async def _run_cli_async(self, *args: str, timeout: int = 60) -> Dict[str, Any]:
        """异步版本，避免阻塞 FastAPI 事件循环"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._run_cli(*args, timeout=timeout)
        )

    # ------------------------------------------------------------------
    # 解析大纲结构
    # ------------------------------------------------------------------

    async def parse_outline(self, file_path: str) -> Dict[str, Any]:
        """
        用 OfficeCLI view outline 解析 docx 章节结构。

        真实返回格式：
        {
          "success": true,
          "data": {
            "headings": [
              {"line": 9, "text": "1. 概述", "style": "Heading1", "level": 1},
              ...
            ]
          }
        }
        line 字段是段落在 body 中的 1-based 索引，对应路径 /body/p[line]
        """
        self.logger.info(f"使用 OfficeCLI 解析大纲: {file_path}")

        outline_result = await self._run_cli_async("view", file_path, "outline")
        sections = self._parse_outline_result(outline_result)
        document_title = self._extract_title(outline_result, file_path)

        self.logger.info(f"解析完成，共识别 {len(sections)} 个章节")

        return {
            "success": True,
            "data": {
                "documentTitle": document_title,
                "sections": sections,
                "totalSections": len(sections),
            },
        }

    def _parse_outline_result(self, outline_result: Dict) -> List[Dict[str, Any]]:
        """
        将 OfficeCLI outline 结果转换为统一章节列表。
        headings[].line 直接作为段落索引，对应 /body/p[line]
        """
        sections = []
        if not isinstance(outline_result, dict):
            return sections

        data = outline_result.get("data", {})
        headings = data.get("headings", [])

        for item in headings:
            if not isinstance(item, dict):
                continue
            text = item.get("text", "").strip()
            if not text:
                continue

            level = int(item.get("level", 1))
            line = int(item.get("line", 0))
            officecli_path = f"/body/p[{line}]" if line > 0 else ""
            number_text, title_text = self._split_number_and_title(text)

            sections.append({
                "paragraphIndex": line,
                "level": level,
                "numberText": number_text,
                "titleText": title_text,
                "fullText": text,
                "bodyText": "",
                "sourceType": item.get("style", "heading"),
                "officecliPath": officecli_path,
            })

        return sections

    def _split_number_and_title(self, text: str):
        """
        分离编号前缀和标题正文。
          "1. 概述"      → ("1.", "概述")
          "1.2 测试范围" → ("1.2", "测试范围")
          "（一）总则"   → ("（一）", "总则")
          "第三章 方法"  → ("第三章", "方法")
          "纯标题"       → ("", "纯标题")
        """
        patterns = [
            r"^(\d+(?:\.\d+)*\.?)\s+(.+)$",
            r"^(（[^）]+）)\s*(.+)$",
            r"^(\([^)]+\))\s*(.+)$",
            r"^(第[零一二三四五六七八九十百\d]+[章节条款])\s*(.+)$",
        ]
        for pat in patterns:
            m = re.match(pat, text.strip())
            if m:
                return m.group(1).strip(), m.group(2).strip()
        return "", text.strip()

    def _extract_title(self, outline_result: Dict, file_path: str) -> str:
        """从 outline 结果或文件名提取文档标题"""
        if isinstance(outline_result, dict):
            data = outline_result.get("data", {})
            # OfficeCLI outline 有时会在 data.fileName 里给文件名
            title = data.get("title", data.get("Title", ""))
            if title:
                return title
        return Path(file_path).stem

    # ------------------------------------------------------------------
    # AI 内容生成
    # ------------------------------------------------------------------

    async def generate_all_sections(
        self,
        sections: List[Dict[str, Any]],
        section_extras: Dict[int, str],
        document_title: str,
    ) -> List[Dict[str, Any]]:
        """
        只对 section_extras 中包含的章节（即用户勾选的章节）调用 AI 生成内容。
        section_extras: {paragraphIndex: extra_info_text}，key 不存在则跳过该章节。
        """
        if not section_extras:
            self.logger.warning("section_extras 为空，没有选中任何章节，跳过生成")
            return []

        # 建立 paragraphIndex -> section 的快速查找表
        sec_map = {sec["paragraphIndex"]: sec for sec in sections}

        fill_data = []
        for idx, extra in section_extras.items():
            sec = sec_map.get(idx)
            if sec is None:
                self.logger.warning(f"paragraphIndex={idx} 在解析结果中不存在，跳过")
                continue

            ai_result = await self.ai_client.generate_section_content(
                section_title=sec["titleText"],
                section_number=sec["numberText"] or str(sec["level"]),
                extra_info=extra or "",
                document_title=document_title,
                prompt_template=self._prompt_template,
            )
            if ai_result["success"]:
                fill_data.append({
                    "paragraphIndex": idx,
                    "officecliPath": sec.get("officecliPath", ""),
                    "generatedContent": ai_result["content"].strip(),
                })
            else:
                self.logger.warning(
                    f"章节 [{sec['numberText']}]{sec['titleText']} 生成失败: "
                    f"{ai_result.get('error')}"
                )
        return fill_data

    # ------------------------------------------------------------------
    # 填充内容到 docx
    # ------------------------------------------------------------------

    async def fill_docx(
        self,
        source_docx_path: str,
        fill_data: List[Dict[str, Any]],
    ) -> bytes:
        """
        用 OfficeCLI batch 将 AI 内容插入到每个章节标题段落之后。
        倒序插入避免行号因新增段落而前移。
        """
        self.logger.info(f"填充 docx，共 {len(fill_data)} 个章节: {source_docx_path}")

        if not fill_data:
            with open(source_docx_path, "rb") as f:
                return f.read()

        commands = []
        # 倒序：先处理靠后的章节，insert-after 不影响前面章节的行号
        for item in reversed(fill_data):
            path = item.get("officecliPath", "")
            content = item.get("generatedContent", "").strip()
            if not path or not content:
                continue

            # 多段内容拆成多个段落，同样倒序插入
            lines = [ln for ln in content.split("\n") if ln.strip()]
            for line_text in reversed(lines):
                commands.append({
                    "command": "add",
                    "parent": "/body",
                    "type": "paragraph",
                    "after": path,
                    "props": {"text": line_text},
                })

        if not commands:
            with open(source_docx_path, "rb") as f:
                return f.read()

        batch_path = Path(source_docx_path).parent / "batch_commands.json"
        with open(batch_path, "w", encoding="utf-8") as f:
            json.dump(commands, f, ensure_ascii=False, indent=2)

        self.logger.info(f"执行 batch，共 {len(commands)} 条插入命令")

        try:
            batch_result = await self._run_cli_async(
                "batch", source_docx_path,
                "--input", str(batch_path),
                "--force",
                timeout=120,
            )
            if isinstance(batch_result, dict) and batch_result.get("success") is False:
                raise RuntimeError(f"OfficeCLI batch 失败: {batch_result.get('error')}")
        finally:
            batch_path.unlink(missing_ok=True)

        with open(source_docx_path, "rb") as f:
            return f.read()

    # ------------------------------------------------------------------
    # 完整流水线
    # ------------------------------------------------------------------

    async def run_full_pipeline(
        self,
        local_docx_path: str,
        section_extras: Dict[int, str],
    ) -> bytes:
        """解析 → AI生成 → 填充 → 返回新 docx 字节"""
        parse_result = await self.parse_outline(local_docx_path)
        data = parse_result["data"]
        fill_data = await self.generate_all_sections(
            data["sections"], section_extras, data["documentTitle"]
        )
        return await self.fill_docx(local_docx_path, fill_data)
