"""
Round 2: AI 智能体根据 call_graph + 目录结构，为每个叶子功能定位代码路径并发现潜在问题

流程：
1. 遍历功能树，找到所有叶子节点（没有子功能的最底层功能）
2. 对每个叶子功能，构造包含 call_graph 摘要 + 目录结构的 prompt
3. AI 输出该功能对应的 related_files / key_functions / call_chain / issues
4. 非叶子节点的 related_files 由子节点聚合得到
"""
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

from .call_graph_context import CallGraphContext
from .....utils.concurrent_logger import (
    log_concurrent_info as log_info,
    log_concurrent_error as log_error,
    log_concurrent_debug as log_debug,
    log_concurrent_warning as log_warning,
)


class Round2CodeExplorer:
    """
    Round 2: AI 智能体探索代码库，为功能树中每个叶子节点定位代码。
    非叶子节点的代码路径由子节点聚合。
    """

    # 每次 prompt 中最多带多少函数签名条目
    MAX_FUNC_IN_PROMPT = 80
    # call_graph 摘要中最多展示多少条调用边
    MAX_EDGES_IN_SUMMARY = 60

    def __init__(
        self,
        project_root: str,
        ai_client,
        extractor,
        call_graph_data: Optional[Dict] = None,
    ):
        self.project_root = Path(project_root)
        self.ai_client = ai_client
        self.extractor = extractor
        self.cg = CallGraphContext(call_graph_data) if call_graph_data else None
        self.language = getattr(self.extractor, 'language', 'c')

        # 预先提取目录树文本 & 函数签名（复用，避免重复 IO）
        self._dir_tree_text = self._build_dir_tree_text()
        self._all_sigs = self.extractor.extract_function_signatures()
        self._actual_files = {
            sig.get("file", "").replace("\\", "/") for sig in self._all_sigs if sig.get("file")
        }
        self._actual_funcs = {sig.get("name", "") for sig in self._all_sigs if sig.get("name")}

    # ------------------------------------------------------------------
    # 公共入口
    # ------------------------------------------------------------------

    def analyze(self, features: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        对功能树执行代码探索。

        Args:
            features: Round 1 生成的功能树列表

        Returns:
            补全了代码信息的功能树
        """
        log_info(f"[Round 2] 开始代码探索，顶层功能数: {len(features)}", "progressive_discovery")

        cg_summary = self._build_cg_summary()
        enriched = self._process_list(features, cg_summary)

        log_info("[Round 2] 代码探索完成", "progressive_discovery")
        return {
            "method": "code_explorer",
            "summary": "AI 智能体根据 call_graph 为每个功能定位代码路径",
            "features": enriched,
        }

    # ------------------------------------------------------------------
    # 递归处理功能树
    # ------------------------------------------------------------------

    def _process_list(
        self, features: List[Dict[str, Any]], cg_summary: str
    ) -> List[Dict[str, Any]]:
        result = []
        for f in features:
            result.append(self._process_feature(f, cg_summary))
        return result

    def _process_feature(
        self, feature: Dict[str, Any], cg_summary: str
    ) -> Dict[str, Any]:
        f = dict(feature)
        sub = f.get("sub_features") or []

        if sub:
            # 非叶子节点：递归处理子节点，聚合 related_files
            enriched_sub = self._process_list(sub, cg_summary)
            f["sub_features"] = enriched_sub
            f["related_files"] = self._aggregate_files(enriched_sub)
            f["key_functions"] = self._aggregate_funcs(enriched_sub)
        else:
            # 叶子节点：调用 AI 探索
            explored = self._explore_leaf(f, cg_summary)
            f.update(explored)

        return f

    # ------------------------------------------------------------------
    # 叶子节点 AI 探索
    # ------------------------------------------------------------------

    def _explore_leaf(
        self, feature: Dict[str, Any], cg_summary: str
    ) -> Dict[str, Any]:
        """
        调用 AI，为单个叶子功能定位代码路径，并判断是否存在问题。
        """
        section = feature.get("section", "")
        name = feature.get("name", "未知功能")
        description = feature.get("description", name)

        log_info(f"[Round 2] 探索叶子功能: {section} {name}", "progressive_discovery")

        # 用函数签名文本作为候选
        func_text = self._format_signatures(self._all_sigs)
        code_unit_name = '模块/实体' if self.language == 'fpga' else '函数'
        language_name = 'FPGA（Verilog/VHDL）' if self.language == 'fpga' else '嵌入式C'

        system_prompt = """你是{language_name}代码架构分析专家。任务是：根据功能名称和代码库信息，找到该功能对应的源文件和{code_unit_name}，并判断实现是否存在问题。

输出要求（严格纯JSON，禁止 markdown）：
{{
  "related_files": ["相对路径1", "相对路径2"],
  "key_functions": ["代码单元1", "代码单元2"],
  "call_chain": "入口函数 → 函数A → 函数B",
  "issues": [
    {{
      "issue_name": "问题名称",
      "issue_level": "严重问题|一般问题|建议",
      "description_issue": "问题描述",
      "description_location": "定位说明",
      "description_impact": "影响说明"
    }}
  ]
}}

注意：
1. related_files 必须是代码库中真实存在的路径（从【可用文件列表】中选取）
2. key_functions 必须是【可用函数列表】中真实存在的代码单元名
3. issues 为空数组表示实现无问题
4. call_chain 用 → 分隔关键代码单元名，按调用顺序排列""".format(
            language_name=language_name,
            code_unit_name=code_unit_name,
        )

        user_message = f"""【功能信息】
章节号: {section}
功能名称: {name}
功能描述: {description}

【可用文件列表】
{self._dir_tree_text}

【可用代码单元列表（含所在文件）】
{func_text}

【调用图摘要（caller → callee）】
{cg_summary}

请分析：该功能的实现对应哪些文件和关键代码单元？调用链路是什么？是否存在实现问题？
"""

        raw = self._call_ai(system_prompt, user_message, f"{section} {name}")
        parsed = self._parse_response(raw, section, name)

        # 验证文件和函数是否真实存在
        parsed["related_files"] = self._validate_files(parsed.get("related_files", []))
        parsed["key_functions"] = self._validate_funcs(parsed.get("key_functions", []))

        return parsed

    # ------------------------------------------------------------------
    # AI 调用
    # ------------------------------------------------------------------

    def _call_ai(self, system_prompt: str, user_message: str, label: str) -> str:
        """调用 AI，返回原始文本"""
        conversation = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        try:
            response = self.ai_client.client.chat.completions.create(
                model=self.ai_client.default_model,
                messages=conversation,
                temperature=0.1,
            )
            content = response.choices[0].message.content or ""
            print(f"[DEBUG Round2] {label}: AI响应长度={len(content)}, 前120字: {content[:120]!r}")
            import sys; sys.stdout.flush()
            return content
        except Exception as e:
            import traceback
            log_error(f"[Round 2] AI调用失败 ({label}): {e}", "progressive_discovery")
            print(traceback.format_exc())
            import sys; sys.stdout.flush()
            return ""

    # ------------------------------------------------------------------
    # 响应解析
    # ------------------------------------------------------------------

    def _parse_response(self, content: str, section: str, name: str) -> Dict[str, Any]:
        """解析 AI 返回的 JSON，失败时返回空结构"""
        import re
        # 去掉思维链
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()

        default = {
            "related_files": [],
            "key_functions": [],
            "call_chain": "",
            "issues": [],
        }

        if not content:
            log_warning(f"[Round 2] {section} {name}: AI 返回空内容", "progressive_discovery")
            return default

        # 尝试直接解析
        try:
            parsed = json.loads(content.strip())
            return self._normalize_parsed(parsed, default)
        except Exception:
            pass

        # 尝试 markdown 代码块
        m = re.search(r'```(?:json)?\s*({.*?})\s*```', content, re.DOTALL)
        if m:
            try:
                parsed = json.loads(m.group(1))
                return self._normalize_parsed(parsed, default)
            except Exception:
                pass

        # 尝试最外层 {}
        start = content.find('{')
        end = content.rfind('}') + 1
        if start != -1 and end > start:
            try:
                parsed = json.loads(content[start:end])
                return self._normalize_parsed(parsed, default)
            except Exception:
                pass

        log_error(
            f"[Round 2] {section} {name}: 无法解析 JSON，原始内容前300字:\n{content[:300]}",
            "progressive_discovery",
        )
        return default

    @staticmethod
    def _normalize_parsed(parsed: Dict, default: Dict) -> Dict[str, Any]:
        """规范化解析结果，补全缺失字段"""
        result = dict(default)
        for key in default:
            val = parsed.get(key)
            if val is not None:
                result[key] = val
        # issues 里每个元素必须是 dict
        issues = result.get("issues", [])
        if isinstance(issues, list):
            result["issues"] = [i for i in issues if isinstance(i, dict)]
        else:
            result["issues"] = []
        return result

    # ------------------------------------------------------------------
    # 验证（过滤幻觉）
    # ------------------------------------------------------------------

    def _validate_files(self, files: List[str]) -> List[str]:
        """过滤不存在的文件路径"""
        valid = []
        for f in files:
            normalized = f.replace("\\", "/").strip("/")
            if any(
                normalized == af or af.endswith("/" + normalized) or normalized.endswith("/" + af.split("/")[-1])
                for af in self._actual_files
            ):
                valid.append(normalized)
            else:
                log_debug(f"[Round 2] 过滤幻觉文件: {f}", "progressive_discovery")
        return valid

    def _validate_funcs(self, funcs: List[str]) -> List[str]:
        """过滤不存在的函数名"""
        valid = []
        for fn in funcs:
            fname = fn.split('(')[0].strip()
            if fname in self._actual_funcs:
                valid.append(fname)
            else:
                log_debug(f"[Round 2] 过滤幻觉函数: {fn}", "progressive_discovery")
        return valid

    # ------------------------------------------------------------------
    # 聚合（非叶子节点）
    # ------------------------------------------------------------------

    @staticmethod
    def _aggregate_files(sub_features: List[Dict[str, Any]]) -> List[str]:
        """聚合子功能的 related_files（去重）"""
        seen = set()
        result = []
        for sf in sub_features:
            for f in sf.get("related_files", []) or []:
                if f not in seen:
                    seen.add(f)
                    result.append(f)
        return result

    @staticmethod
    def _aggregate_funcs(sub_features: List[Dict[str, Any]]) -> List[str]:
        """聚合子功能的 key_functions（去重）"""
        seen = set()
        result = []
        for sf in sub_features:
            for fn in sf.get("key_functions", []) or []:
                if fn not in seen:
                    seen.add(fn)
                    result.append(fn)
        return result

    # ------------------------------------------------------------------
    # 辅助：构建 prompt 素材
    # ------------------------------------------------------------------

    def _build_dir_tree_text(self) -> str:
        """提取目录树，返回文本"""
        try:
            tree = self.extractor.extract_directory_tree(max_depth=4)
            lines = []
            def walk(node, indent=0):
                prefix = "  " * indent
                if node.get("type") == "file":
                    lines.append(f"{prefix}- {node.get('path', '')}")
                else:
                    lines.append(f"{prefix}[{node.get('name', '')}]")
                    for child in node.get("children", []) or []:
                        walk(child, indent + 1)
            walk(tree)
            return "\n".join(lines[:300])  # 最多300行
        except Exception as e:
            log_warning(f"[Round 2] 目录树提取失败: {e}", "progressive_discovery")
            return "(无法获取目录树)"

    def _format_signatures(self, sigs: List[Dict[str, Any]]) -> str:
        """格式化函数签名列表"""
        lines = []
        for sig in sigs[:self.MAX_FUNC_IN_PROMPT]:
            lines.append(
                f"- {sig.get('name', '')}  //  {sig.get('file', '')}:{sig.get('line', 0)}"
            )
        if len(sigs) > self.MAX_FUNC_IN_PROMPT:
            lines.append(f"... 还有 {len(sigs) - self.MAX_FUNC_IN_PROMPT} 个函数")
        return "\n".join(lines)

    def _build_cg_summary(self) -> str:
        """构建 call_graph 摘要文本"""
        if not self.cg or not self.cg.is_valid():
            return "(无调用图)"
        lines = []
        callees_map = self.cg.callees_by_node
        count = 0
        for caller in sorted(callees_map.keys()):
            callees = callees_map.get(caller, [])
            if not callees:
                continue
            caller_name = caller.split("::")[-1]
            callee_names = [c.split("::")[-1] for c in callees[:5]]
            lines.append(f"- {caller_name} -> {', '.join(callee_names)}")
            count += 1
            if count >= self.MAX_EDGES_IN_SUMMARY:
                break
        return "\n".join(lines) if lines else "(调用图无有效边)"
