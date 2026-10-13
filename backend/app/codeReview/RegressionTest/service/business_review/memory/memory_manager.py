"""
记忆文件管理模块 - 用于渐进式功能发现

负责：
1. 存储每一轮分析的结果（功能划分）
2. 加载之前的记忆供AI参考
3. 支持版本历史和回溯
4. 提供前端可视化的数据格式
"""
import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime


class MemoryManager:
    """功能划分记忆管理器"""
    
    def __init__(self, task_id: int, project_root: str):
        """
        初始化记忆管理器
        
        Args:
            task_id: 任务ID
            project_root: 项目根目录
        """
        self.task_id = task_id
        self.project_root = Path(project_root)
        
        # 记忆文件存储路径（与日志文件夹统一）
        # 路径结构: logs/task_{task_id}/memory/
        logs_base_dir = Path(__file__).parent.parent.parent.parent / "logs"
        task_folder = logs_base_dir / f"task_{task_id}"
        self.memory_dir = task_folder / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # 当前记忆
        self.current_memory = None
    
    def create_initial_memory(self, project_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建初始记忆结构
        
        Args:
            project_info: 项目基本信息
            
        Returns:
            初始记忆字典
        """
        memory = {
            "version": "1.0",
            "task_id": self.task_id,
            "project": {
                "name": project_info.get("name", "Unknown"),
                "root_path": str(self.project_root),
                "entry_point": project_info.get("entry_point", "main"),
                "language": project_info.get("language", "c")
            },
            "discovery": {
                "status": "in_progress",  # in_progress, completed
                "current_round": 0,
                "total_rounds": 0,
                "method": "progressive_analysis"  # 渐进式分析
            },
            "review": {
                "status": "not_started",  # not_started, in_progress, completed
                "total_features": 0,
                "reviewed_features": 0,
                "started_at": None,
                "completed_at": None
            },
            "features": [],  # 功能列表
            "call_graph": {
                "nodes": [],
                "edges": []
            },
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "rounds_history": []  # 每轮的决策历史
            }
        }
        
        self.current_memory = memory
        return memory
    
    def _count_features(self, features: List[Dict[str, Any]]) -> int:
        """递归统计功能数量（包含子功能）"""
        total = 0
        if not features:
            return total

        for feature in features:
            total += 1
            sub_features = feature.get("sub_features", []) or []
            if sub_features:
                total += self._count_features(sub_features)

        return total

    def save_round(self, round_num: int, round_data: Dict[str, Any]) -> str:
        """
        保存某一轮的分析结果
        
        Args:
            round_num: 轮次编号
            round_data: 这一轮的数据
            
        Returns:
            保存的文件路径
        """
        # 更新记忆
        self.current_memory["discovery"]["current_round"] = round_num
        self.current_memory["discovery"]["total_rounds"] = max(
            round_num,
            self.current_memory["discovery"]["total_rounds"]
        )
        self.current_memory["metadata"]["last_updated"] = datetime.now().isoformat()
        
        # 记录这一轮的元数据
        round_metadata = {
            "round": round_num,
            "timestamp": datetime.now().isoformat(),
            "method": round_data.get("method", "unknown"),
            "summary": round_data.get("summary", ""),
            "ai_decisions": round_data.get("ai_decisions", [])
        }
        self.current_memory["metadata"]["rounds_history"].append(round_metadata)
        
        # 更新功能列表
        if "features" in round_data:
            self.current_memory["features"] = round_data["features"]
        
        # 更新调用图
        if "call_graph" in round_data:
            self.current_memory["call_graph"] = round_data["call_graph"]
        
        # 保存到文件
        filename = f"round_{round_num}_{round_data.get('method', 'analysis')}.json"
        filepath = self.memory_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.current_memory, f, ensure_ascii=False, indent=2)
        
        # 同时保存一个"最新"的副本
        latest_path = self.memory_dir / "latest.json"
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(self.current_memory, f, ensure_ascii=False, indent=2)
        
        return str(filepath)
    
    def load_round(self, round_num: int) -> Optional[Dict[str, Any]]:
        """
        加载指定轮次的记忆
        
        Args:
            round_num: 轮次编号，-1表示最新
            
        Returns:
            记忆数据，如果不存在返回None
        """
        if round_num == -1:
            # 加载最新的
            latest_path = self.memory_dir / "latest.json"
            if latest_path.exists():
                with open(latest_path, 'r', encoding='utf-8') as f:
                    self.current_memory = json.load(f)
                return self.current_memory
        else:
            # 查找对应轮次的文件
            for filepath in self.memory_dir.glob(f"round_{round_num}_*.json"):
                with open(filepath, 'r', encoding='utf-8') as f:
                    self.current_memory = json.load(f)
                return self.current_memory
        
        return None
    
    def load_latest(self) -> Optional[Dict[str, Any]]:
        """加载最新的记忆"""
        return self.load_round(-1)
    
    def get_feature_by_id(self, feature_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取功能
        
        Args:
            feature_id: 功能ID
            
        Returns:
            功能数据
        """
        if not self.current_memory:
            self.load_latest()
        
        if not self.current_memory:
            return None
        
        for feature in self.current_memory.get("features", []):
            if feature.get("id") == feature_id:
                return feature
            
            # 递归查找子功能
            sub_feature = self._find_in_sub_features(feature, feature_id)
            if sub_feature:
                return sub_feature
        
        return None
    
    def _find_in_sub_features(self, feature: Dict[str, Any], target_id: str) -> Optional[Dict[str, Any]]:
        """递归查找子功能"""
        for sub_feature in feature.get("sub_features", []):
            if sub_feature.get("id") == target_id:
                return sub_feature
            
            result = self._find_in_sub_features(sub_feature, target_id)
            if result:
                return result
        
        return None
    
    def mark_discovery_complete(self):
        """标记功能发现阶段完成"""
        if self.current_memory:
            self.current_memory["discovery"]["status"] = "completed"
            self.current_memory["review"]["status"] = "not_started"
            features = self.current_memory.get("features", [])
            self.current_memory["review"]["total_features"] = self._count_features(features)
            self.save_round(
                self.current_memory["discovery"]["current_round"],
                {"method": "completion", "summary": "功能发现完成"}
            )
    
    def start_review(self):
        """标记审查阶段开始"""
        if self.current_memory:
            self.current_memory["review"]["status"] = "in_progress"
            self.current_memory["review"]["started_at"] = datetime.now().isoformat()
            self.save_current()
    
    def set_review_total_features(self, total: int):
        """手动更新审查阶段的功能总数（支持后续动态调整）"""
        if self.current_memory:
            self.current_memory["review"]["total_features"] = max(0, int(total))
            self.save_current()

    def update_review_progress(self, reviewed_count: int):
        """更新审查进度"""
        if self.current_memory:
            self.current_memory["review"]["reviewed_features"] = reviewed_count
            self.save_current()
    
    def mark_review_complete(self):
        """标记审查阶段完成"""
        if self.current_memory:
            self.current_memory["review"]["status"] = "completed"
            self.current_memory["review"]["completed_at"] = datetime.now().isoformat()
            self.save_current()
    
    def save_current(self):
        """保存当前内存状态"""
        if self.current_memory:
            self.current_memory["metadata"]["last_updated"] = datetime.now().isoformat()
            latest_path = self.memory_dir / "latest.json"
            with open(latest_path, 'w', encoding='utf-8') as f:
                json.dump(self.current_memory, f, ensure_ascii=False, indent=2)
    
    def get_visualization_data(self) -> Dict[str, Any]:
        """
        获取用于前端可视化的数据格式
        
        Returns:
            树形结构的功能图
        """
        if not self.current_memory:
            self.load_latest()
        
        if not self.current_memory:
            return {"error": "No memory found"}
        
        # 转换为树形结构
        tree = {
            "name": self.current_memory["project"]["name"],
            "type": "project",
            "children": []
        }
        
        for feature in self.current_memory.get("features", []):
            tree["children"].append(self._feature_to_tree_node(feature))
        
        return {
            "tree": tree,
            "statistics": {
                "total_features": self._count_features(self.current_memory["features"]),
                "total_rounds": self.current_memory["discovery"]["total_rounds"],
                "status": self.current_memory["discovery"]["status"]
            },
            "metadata": self.current_memory["metadata"]
        }
    
    def _feature_to_tree_node(self, feature: Dict[str, Any]) -> Dict[str, Any]:
        """将功能转换为树节点"""
        node = {
            "id": feature.get("id"),
            "name": feature.get("name"),
            "description": feature.get("description", ""),
            "confidence": feature.get("confidence", "medium"),
            "status": feature.get("review_status", "pending"),
            "issues_count": len(feature.get("issues_found", [])),
            "children": []
        }
        
        for sub_feature in feature.get("sub_features", []):
            node["children"].append(self._feature_to_tree_node(sub_feature))
        
        return node
    
    def _count_features(self, features: List[Dict[str, Any]]) -> int:
        """递归计数功能数量"""
        count = len(features)
        for feature in features:
            count += self._count_features(feature.get("sub_features", []))
        return count
    
    def export_for_frontend(self, output_path: Optional[str] = None) -> str:
        """
        导出前端可用的JSON文件
        
        Args:
            output_path: 输出路径，None则使用默认路径
            
        Returns:
            输出文件路径
        """
        if not output_path:
            output_path = self.memory_dir / "frontend_visualization.json"
        
        data = self.get_visualization_data()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return str(output_path)

