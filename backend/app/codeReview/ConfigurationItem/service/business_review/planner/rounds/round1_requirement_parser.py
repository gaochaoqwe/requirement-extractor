"""
Round 1: 解析用户上传的需求文档功能目录，构建功能层级树

输入格式示例（每行一个条目）:
    3.1.1  系统初始化  10
    3.2.2.2  某子功能  25

规则:
- 章节号按 '.' 分隔，第1段固定为 '3'（顶层软件），第2段起按层级划分
- 末尾的数字视为页码，忽略
- 中间的文字为功能名称
- 层级深度不限（支持 3.x / 3.x.x / 3.x.x.x / 3.x.x.x.x 等）
"""
import re
from typing import Dict, Any, List, Optional

from .....utils.concurrent_logger import (
    log_concurrent_info as log_info,
    log_concurrent_error as log_error,
    log_concurrent_debug as log_debug,
)


class Round1RequirementParser:
    """
    Round 1: 将需求文档功能目录解析为标准功能层级树
    
    不调用 AI，纯文本解析，结果确定且稳定。
    """

    def __init__(self):
        pass

    def analyze(self, requirement_text: str) -> Dict[str, Any]:
        """
        解析需求文档，返回功能层级树

        Args:
            requirement_text: 需求文档文本（一行一个功能条目）

        Returns:
            标准功能树 dict，格式与原 Round1 保持兼容
        """
        log_info("[Round 1] 开始解析需求文档目录", "progressive_discovery")

        entries = self._parse_lines(requirement_text)
        if not entries:
            log_error("[Round 1] 未能从需求文档中解析出任何功能条目", "progressive_discovery")
            return {"method": "requirement_parser", "summary": "解析失败", "features": []}

        log_debug(f"[Round 1] 解析出 {len(entries)} 个条目", "progressive_discovery")
        features = self._build_tree(entries)
        log_info(f"[Round 1] 构建功能树完成，顶层功能数: {len(features)}", "progressive_discovery")

        return {
            "method": "requirement_parser",
            "summary": f"从需求文档解析出 {len(entries)} 个功能条目",
            "features": features,
        }

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _parse_lines(self, text: str) -> List[Dict[str, Any]]:
        """
        逐行解析，提取 (章节号列表, 功能名称)

        章节号格式：3.1 / 3.1.1 / 3.1.1.1 / 3.1.1.1.1
        末尾孤立的整数视为页码，忽略。
        """
        entries = []
        # 匹配形如 "3.1.2  系统初始化  10" 或 "3.2.3.1 某功能" 的行
        # 章节号：以数字开头，由数字和点组成，不以点结尾
        pattern = re.compile(
            r'^\s*'
            r'(?P<section>\d+(?:\.\d+)+)'   # 章节号，如 3.1.2
            r'\s+'
            r'(?P<rest>.+)$'                  # 剩余部分
        )
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            m = pattern.match(line)
            if not m:
                log_debug(f"[Round 1] 跳过无法解析的行: {line!r}", "progressive_discovery")
                continue

            section_str = m.group('section')   # e.g. "3.1.2"
            rest = m.group('rest').strip()      # e.g. "系统初始化  10"

            # 去掉末尾的页码（末尾孤立整数，允许与文字之间无空格）
            name = re.sub(r'\s*\d+\s*$', '', rest).strip()
            if not name:
                log_debug(f"[Round 1] 跳过名称为空的行: {line!r}", "progressive_discovery")
                continue

            section_parts = section_str.split('.')  # ["3", "1", "2"]
            entries.append({
                "section": section_str,
                "parts": section_parts,   # 含顶层 "3"
                "name": name,
            })

        return entries

    def _build_tree(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        将扁平条目列表构建为嵌套的功能树。

        章节号第1段固定为 "3"，代表整个软件，不单独建节点。
        第2段起每一段对应一层功能：
          - parts[1] 不同 → 不同一级功能
          - parts[2]       → 二级功能
          - parts[3]       → 三级功能
          - parts[4]       → 四级功能
          依此类推。
        """
        # 用字典缓存已创建的节点，key 为章节号前缀（不含第1段 "3"）
        # e.g. "3.1" → 一级功能节点, "3.1.2" → 二级功能节点
        node_map: Dict[str, Dict[str, Any]] = {}
        roots: List[Dict[str, Any]] = []  # 一级功能列表

        for entry in entries:
            parts = entry["parts"]  # ["3", "1", "2", ...]
            section = entry["section"]
            name = entry["name"]

            if len(parts) < 2:
                # 只有一段（如 "3"），忽略
                continue

            # 确保从第2段起的所有祖先节点都已创建（处理目录中间层可能缺失的情况）
            for depth in range(2, len(parts) + 1):
                ancestor_section = ".".join(parts[:depth])
                if ancestor_section not in node_map:
                    # 祖先节点缺失，用章节号作为占位名称
                    ancestor_name = name if depth == len(parts) else ancestor_section
                    node = self._make_node(ancestor_section, ancestor_name)
                    node_map[ancestor_section] = node

                    if depth == 2:
                        # 一级功能，挂到 roots
                        roots.append(node)
                    else:
                        # 挂到父节点
                        parent_section = ".".join(parts[:depth - 1])
                        parent_node = node_map.get(parent_section)
                        if parent_node is not None:
                            parent_node["sub_features"].append(node)
                else:
                    # 节点已存在（之前作为占位创建），如果当前行就是该节点，更新名称
                    if ancestor_section == section:
                        node_map[ancestor_section]["name"] = name

        return roots

    @staticmethod
    def _make_node(section: str, name: str) -> Dict[str, Any]:
        """创建标准功能节点"""
        # 用章节号生成稳定的 id，如 "3.1.2" → "feature_3_1_2"
        node_id = "feature_" + section.replace(".", "_")
        return {
            "id": node_id,
            "section": section,
            "name": name,
            "description": name,
            "confidence": "high",
            "related_directories": [],
            "related_files": [],
            "key_functions": [],
            "call_chain": "",
            "issues": [],
            "sub_features": [],
        }

