"""普通模式 FPGA：不确定类规则的文件级发现 Agent（复用科代工具能力，逻辑独立）。"""
from __future__ import annotations

import asyncio
import concurrent.futures
import json
import re
from typing import Any, Dict, List

from app.staticAnalysis.normalModeFpga.services.agent_base import CodeAnalysisAgentV2


class NormalModeFpgaAgent(CodeAnalysisAgentV2):
    """在普通模式目录内扩展：单规则 × 单文件违规发现。"""

    def discover_violations_in_file(
        self,
        rule_info: Dict[str, Any],
        file_item: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        try:
            file_path = file_item.get("file_path") or file_item.get("file_name") or ""
            self.logger.info("=" * 100)
            self.logger.info(">>> 普通模式FPGA Agent 文件级规则发现 <<<")
            self.logger.info(f"规则编号: {rule_info.get('rule_code', 'N/A')}")
            self.logger.info(f"目标文件: {file_path}")
            self.logger.info("=" * 100)

            if not self.codebase_path or not self.codebase_path.exists():
                self.logger.warning("无法访问代码库，跳过 Agent 发现")
                return []

            self.conversation_history = []
            self.tool_call_count = 0

            initial_prompt = self._build_normal_discovery_prompt(rule_info, file_item)
            result = self._react_loop_normal_discovery(initial_prompt)
            problems = result.get("problems") or []
            self.logger.info(f"普通模式FPGA发现完成，问题数={len(problems)}，工具调用={self.tool_call_count}")
            return problems if isinstance(problems, list) else []
        except Exception as e:
            self.logger.error(f"普通模式FPGA Agent 发现失败: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return []

    def _build_normal_discovery_prompt(
        self,
        rule_info: Dict[str, Any],
        file_item: Dict[str, Any],
    ) -> str:
        rule_code = rule_info.get("rule_code", "未知规则")
        rule_name = rule_info.get("rule_name", "未知规则名称")
        rule_desc = rule_info.get("rule_description", "无规则描述")
        file_path = file_item.get("file_path") or file_item.get("file_name") or "未知文件"
        language = file_item.get("language") or "verilog"
        display_language = "VHDL" if language == "vhdl" else "Verilog"

        return f"""你是一名专业的FPGA（{display_language}）静态分析审查专家。
你的任务是：仅针对下面这 **1 条规则**，审查当前这 **1 个源文件**，找出所有确定违反该规则的问题。

**规则信息：**
- 规则编号：{rule_code}
- 规则名称：{rule_name}
- 规则说明：{rule_desc}

**目标文件：**
- 路径：{file_path}
- 语言：{display_language}

**审查原则：宁可漏过，不可误报！**
只有在你能通过代码证据确认“一定违反该规则”时，才报告问题；不确定则不要报告。

**你可以使用的工具（按需调用）：**
1. get_file_outline(file_path)：了解文件/模块结构
2. read_file_range(file_path, start_line, end_line)：按行读取代码
3. get_function_context(file_path, line_number)：获取所在模块/过程完整代码
4. search_code(keyword, file_pattern)：搜索信号、模块实例化等
5. list_directory(directory_path)：浏览目录

**推荐步骤：**
1. 先用 get_file_outline 了解 `{file_path}` 结构
2. 按需 read_file_range / get_function_context 深入审查
3. 必要时跨文件 search_code 验证
4. 汇总所有确定违规点并给出最终 JSON

**最终回答格式（不要用 markdown 代码块包裹）：**
{{
  "problems": [
    {{
      "violation_rules": "{rule_code}",
      "issue_level": "建议改进/一般问题/重要问题",
      "issue_name": "问题名称",
      "issue_location": "{file_path}:行号",
      "description_requirement": "需求描述",
      "description_issue": "问题描述",
      "description_location": "问题定位",
      "description_impact": "影响分析"
    }}
  ]
}}

如果没有确定违规，返回：{{"problems": []}}

现在开始审查文件 `{file_path}`。请先调用工具获取必要上下文，再给出最终 JSON。"""

    def _react_loop_normal_discovery(self, initial_prompt: str) -> Dict[str, Any]:
        self.conversation_history.append({"role": "user", "content": initial_prompt})
        self.logger.info("开始普通模式FPGA发现 ReAct 循环...")

        while self.tool_call_count < self.max_tool_calls:
            self.logger.info(f"\n--- 普通模式FPGA发现 ReAct 第{self.tool_call_count + 1}轮 ---")
            try:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._call_ai_with_tools())
                    ai_response = future.result(timeout=120)
            except Exception as e:
                self.logger.error(f"普通模式FPGA发现调用AI失败: {e}")
                import traceback
                self.logger.error(traceback.format_exc())
                break

            if ai_response.get("tool_calls"):
                tool_calls = ai_response["tool_calls"]
                self.conversation_history.append({
                    "role": "assistant",
                    "content": ai_response.get("content") or "",
                    "tool_calls": tool_calls,
                })
                for tool_call in tool_calls:
                    if self.tool_call_count >= self.max_tool_calls:
                        return {"problems": []}
                    self.tool_call_count += 1
                    tool_result = self._execute_tool_call(tool_call)
                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.get("id"),
                        "name": tool_call["function"]["name"],
                        "content": json.dumps(tool_result, ensure_ascii=False),
                    })
            else:
                return self._parse_normal_discovery_answer(ai_response.get("content", ""))

        return {"problems": []}

    def _parse_normal_discovery_answer(self, content: str) -> Dict[str, Any]:
        try:
            json_match = re.search(r"\{[\s\S]*\}", content or "")
            if not json_match:
                return {"problems": []}
            result = json.loads(json_match.group())
            problems = result.get("problems", []) if isinstance(result, dict) else []
            if not isinstance(problems, list):
                return {"problems": []}
            normalized: List[Dict[str, Any]] = []
            for item in problems:
                if not isinstance(item, dict):
                    continue
                normalized.append({
                    "violation_rules": item.get("violation_rules", ""),
                    "issue_level": item.get("issue_level", "一般问题"),
                    "issue_name": item.get("issue_name", ""),
                    "issue_location": item.get("issue_location", ""),
                    "description_requirement": item.get("description_requirement", ""),
                    "description_issue": item.get("description_issue", ""),
                    "description_location": item.get("description_location", item.get("issue_location", "")),
                    "description_impact": item.get("description_impact", ""),
                })
            return {"problems": normalized}
        except Exception as e:
            self.logger.error(f"解析普通模式FPGA发现答案失败: {e}")
            return {"problems": []}
