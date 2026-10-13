"""
调用图上下文管理 - 高效索引和查询 call_graph.json
"""
import json
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path


class CallGraphContext:
    """call_graph.json 的高效索引和查询接口"""
    
    def __init__(self, call_graph_data: Optional[Dict] = None):
        """
        初始化调用图上下文
        
        Args:
            call_graph_data: call_graph.json 的完整数据
        """
        self.data = call_graph_data or {}
        self._build_indexes()
    
    def _build_indexes(self):
        """构建快速查询索引"""
        self.functions_meta = self.data.get("functions", {}) or {}
        self.call_edges = self.data.get("call_edges", []) or []
        self.indexes = self.data.get("indexes", {}) or {}
        
        # 快速索引
        self.by_file = self._normalize_paths(self.indexes.get("by_file", {}))
        self.callers_by_node = self.indexes.get("callers_by_node", {})
        self.callees_by_node = self.indexes.get("callees_by_node", {})
        
        # 函数名 -> 文件映射
        self.function_to_file = self._build_function_to_file_map()
    
    def _normalize_paths(self, path_dict: Dict) -> Dict[str, List[str]]:
        """规范化路径（统一为 /）"""
        result = {}
        for path, nodes in path_dict.items():
            normalized = str(path or "").replace('\\', '/').strip('/')
            result[normalized] = [str(n) for n in (nodes or [])]
        return result
    
    def _build_function_to_file_map(self) -> Dict[str, str]:
        """构建函数名 -> 文件路径映射"""
        mapping = {}
        for node_id, meta in self.functions_meta.items():
            name = str(node_id or "").split("::")[-1]
            file_path = str(meta.get("file", "")).replace('\\', '/').strip('/')
            if name and file_path:
                mapping[name] = file_path
        return mapping
    
    def get_functions_in_file(self, file_path: str) -> List[str]:
        """获取文件中的所有函数"""
        normalized = str(file_path or "").replace('\\', '/').strip('/')
        return self.by_file.get(normalized, [])
    
    def get_callers(self, function_name: str) -> List[str]:
        """获取调用该函数的所有函数（支持纯函数名或完整节点ID）"""
        # 直接匹配（纯函数名作为key的情况）
        if function_name in self.callers_by_node:
            return [n.split("::")[-1] for n in self.callers_by_node[function_name]]
        # 模糊匹配：找所有以 ::function_name 结尾的节点
        results = []
        for node_id, callers in self.callers_by_node.items():
            if node_id.split("::")[-1] == function_name:
                results.extend(n.split("::")[-1] for n in callers)
        return results
    
    def get_callees(self, function_name: str) -> List[str]:
        """获取该函数调用的所有函数（支持纯函数名或完整节点ID）"""
        # 直接匹配
        if function_name in self.callees_by_node:
            return [n.split("::")[-1] for n in self.callees_by_node[function_name]]
        # 模糊匹配
        results = []
        for node_id, callees in self.callees_by_node.items():
            if node_id.split("::")[-1] == function_name:
                results.extend(n.split("::")[-1] for n in callees)
        return results
    
    def get_file_for_function(self, function_name: str) -> Optional[str]:
        """获取函数所在的文件"""
        return self.function_to_file.get(function_name)
    
    def expand_by_call_graph(
        self,
        seed_functions: List[str],
        hop: int = 1
    ) -> Tuple[Set[str], Dict[str, int]]:
        """
        基于调用图扩展函数集合（1-hop 或 2-hop）
        seed_functions: 纯函数名列表（如 ['radar_init', 'main']）
        Returns:
            (扩展后的纯函数名集合, 统计信息)
        """
        # 把纯函数名转换成节点ID集合（node_id 格式: module::func_name）
        seed_name_set = set(seed_functions)
        # 找到所有匹配的节点ID
        seed_node_ids = {
            node_id for node_id in list(self.callers_by_node.keys()) + list(self.callees_by_node.keys())
            if node_id.split("::")[-1] in seed_name_set
        }
        # 也把种子名字本身加入（兼容直接用纯名字作为key的情况）
        seed_node_ids |= seed_name_set
        
        visited = set(seed_node_ids)
        frontier = set(seed_node_ids)
        
        for _ in range(max(1, hop)):
            next_frontier = set()
            for node_id in frontier:
                for caller in self.callers_by_node.get(node_id, []):
                    if caller not in visited:
                        visited.add(caller)
                        next_frontier.add(caller)
                for callee in self.callees_by_node.get(node_id, []):
                    if callee not in visited:
                        visited.add(callee)
                        next_frontier.add(callee)
            frontier = next_frontier
            if not frontier:
                break
        
        # 把节点ID转换回纯函数名
        expanded_names = {node_id.split("::")[-1] for node_id in visited}
        
        return expanded_names, {
            "seed": len(seed_name_set),
            "expanded": len(expanded_names),
            "added": len(expanded_names) - len(seed_name_set)
        }
    
    def find_call_path(self, start: str, end: str, max_depth: int = 5) -> Optional[List[str]]:
        """查找从 start 到 end 的调用路径"""
        from collections import deque
        
        queue = deque([(start, [start])])
        visited = {start}
        
        while queue:
            node, path = queue.popleft()
            if node == end:
                return path
            if len(path) >= max_depth:
                continue
            
            for next_node in self.get_callees(node):
                if next_node not in visited:
                    visited.add(next_node)
                    queue.append((next_node, path + [next_node]))
        
        return None
    
    def is_valid(self) -> bool:
        """检查调用图是否有效"""
        return bool(self.functions_meta and self.call_edges)
    
    def get_stats(self) -> Dict:
        """获取调用图统计信息"""
        return {
            "total_functions": len(self.functions_meta),
            "total_edges": len(self.call_edges),
            "total_files": len(self.by_file)
        }

