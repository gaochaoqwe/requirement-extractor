"""
渐进式功能发现模块（新版）

新流程：
- Round 1: 解析用户上传的需求文档功能目录 → 构建功能层级树（不调用AI）
- Round 2: AI 智能体根据 call_graph + 目录结构，为每个叶子功能定位代码路径 + 发现问题
"""
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

from .rounds.round1_requirement_parser import Round1RequirementParser
from .rounds.round2_code_explorer import Round2CodeExplorer
from .rounds.call_graph_context import CallGraphContext

from ..memory.memory_manager import MemoryManager
from ..tools.code_extractor import CodeExtractor
from ...ai.ai_client import AIClient
from ....utils.concurrent_logger import (
    log_concurrent_info as log_info,
    log_concurrent_error as log_error,
    log_concurrent_debug as log_debug,
    set_current_thread_task
)


class ProgressiveDiscovery:
    """渐进式功能发现器（新版：需求文档驱动）"""
    
    def __init__(
        self,
        task_id: int,
        project_root: str,
        language: str = 'c',
        entry_function: str = 'main',
        requirement_text: Optional[str] = None,
    ):
        """
        初始化
        
        Args:
            task_id: 任务ID
            project_root: 项目根目录
            language: 编程语言
            entry_function: 入口函数名称
            requirement_text: 用户上传的需求文档文本（功能目录）
        """
        self.task_id = task_id
        self.project_root = Path(project_root)
        self.language = language
        self.entry_function = entry_function
        self.requirement_text = requirement_text or ""
        
        # 核心组件
        self.memory = MemoryManager(task_id, project_root)
        self.extractor = CodeExtractor(project_root, language)
        self.ai_client = AIClient()
        
        # 加载 call_graph
        self.call_graph_data = self._load_call_graph()
    
    def run_discovery(self) -> Dict[str, Any]:
        """运行完整的功能发现流程"""
        set_current_thread_task(self.task_id, self.task_id, "progressive_discovery")
        log_info(f"[渐进式发现] 开始任务 {self.task_id}", "progressive_discovery")
        
        project_info = {
            "name": self.project_root.name,
            "language": self.language,
            "entry_point": self.entry_function,
        }
        self.memory.create_initial_memory(project_info)
        
        # ------------------------------------------------------------------
        # Round 1: 解析需求文档，构建功能层级树
        # ------------------------------------------------------------------
        log_info("[Round 1] 开始: 解析需求文档功能目录", "progressive_discovery")
        self.memory.update_current_round(1)

        round1_parser = Round1RequirementParser()

        if self.requirement_text.strip():
            round1_result = round1_parser.analyze(self.requirement_text)
        else:
            log_info("[Round 1] 未提供需求文档，使用空功能树", "progressive_discovery")
            round1_result = {
                "method": "requirement_parser",
                "summary": "未提供需求文档",
                "features": [],
            }

        self.memory.save_round(1, round1_result)
        l1_features = round1_result.get("features", [])

        def _count_all(features):
            n = len(features)
            for f in features:
                n += _count_all(f.get("sub_features", []))
            return n

        total_nodes = _count_all(l1_features)
        log_info(
            f"[Round 1] 完成，解析出 {len(l1_features)} 个顶层功能，共 {total_nodes} 个节点",
            "progressive_discovery",
        )

        # ------------------------------------------------------------------
        # Round 2: AI 智能体探索代码库，为每个功能定位代码路径 + 发现问题
        # ------------------------------------------------------------------
        log_info("[Round 2] 开始: AI 代码探索", "progressive_discovery")
        self.memory.update_current_round(2)

        round2_explorer = Round2CodeExplorer(
            str(self.project_root),
            self.ai_client,
            self.extractor,
            self.call_graph_data,
        )
        round2_result = round2_explorer.analyze(l1_features)
        self.memory.save_round(2, round2_result)
        all_features = round2_result.get("features", [])

        def _count_leaves(features):
            n = 0
            for f in features:
                subs = f.get("sub_features", [])
                if subs:
                    n += _count_leaves(subs)
                else:
                    n += 1
            return n

        total_leaves = _count_leaves(all_features)
        log_info(
            f"[Round 2] 完成，{total_leaves} 个叶子功能已定位代码",
            "progressive_discovery",
        )

        self.memory.mark_discovery_complete()
        log_info("[渐进式发现] 完成！", "progressive_discovery")
        
        return {
            "status": "completed",
            "total_rounds": 2,
            "memory_path": str(self.memory.memory_dir / "latest.json"),
            "visualization_data": self.memory.get_visualization_data(),
        }

    def _load_call_graph(self) -> Optional[Dict[str, Any]]:
        """加载 call_graph.json"""
        candidates = [
            self.project_root / "call_graph" / "call_graph.json",
            self.project_root / "call_graph.json",
            self.project_root.parent / "call_graph" / "call_graph.json",
        ]

        for path in candidates:
            if path.exists():
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        data = json.load(f)
                    log_info(f"[初始化] 调用图加载成功: {path}", "progressive_discovery")
                    return data
                except Exception as e:
                    log_error(f"[初始化] 读取调用图失败: {path} | {e}", "progressive_discovery")

        # 递归查找
        try:
            for p in self.project_root.rglob("call_graph.json"):
                with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                    data = json.load(f)
                log_info(f"[初始化] 调用图加载成功(递归): {p}", "progressive_discovery")
                return data
        except Exception:
            pass

        log_debug("[初始化] 未找到 call_graph.json", "progressive_discovery")
        return None
