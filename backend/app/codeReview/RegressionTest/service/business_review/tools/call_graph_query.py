"""
调用图查询工具
提供快速查询调用关系的API
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
from collections import deque

from ....utils.concurrent_logger import (
    log_concurrent_debug as log_debug,
    log_concurrent_error as log_error
)


class CallGraphQuery:
    """调用图查询器"""
    
    def __init__(self, call_graph_file: Path):
        """
        初始化
        
        Args:
            call_graph_file: 调用图JSON文件路径
        """
        self.call_graph_file = call_graph_file
        self.data: Optional[Dict[str, Any]] = None
        self.functions: Dict[str, Dict[str, Any]] = {}
        self.callers: Dict[str, List[str]] = {}
        self.callees: Dict[str, List[str]] = {}
        self.files: Dict[str, List[str]] = {}
        
        # 加载数据
        self._load()
    
    def _load(self):
        """加载调用图数据"""
        try:
            with open(self.call_graph_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            
            self.functions = self.data.get('functions', {})
            indexes = self.data.get('indexes', {})
            self.callers = indexes.get('callers', {})
            self.callees = indexes.get('callees', {})
            self.files = indexes.get('by_file', {})
            
            log_debug(f"调用图加载成功: {len(self.functions)} 个函数", "call_graph_query")
        
        except Exception as e:
            log_error(f"加载调用图失败: {self.call_graph_file}", "call_graph_query", e)
            self.data = {}
    
    def query(
        self, 
        function_name: str, 
        file_path: Optional[str] = None,
        depth: int = 2,
        direction: str = "callees"
    ) -> Dict[str, Any]:
        """
        查询函数的调用图
        
        Args:
            function_name: 函数名
            file_path: 函数所在文件（可选，用于消歧义）
            depth: 查询深度（1-5）
            direction: 查询方向（callers/callees/both）
        
        Returns:
            调用图数据
        """
        # 1. 查找函数ID
        func_id = self._find_function_id(function_name, file_path)
        
        if not func_id:
            # 提供更友好的错误信息和建议
            similar_funcs = self._find_similar_functions(function_name)
            all_function_names = [func['name'] for func in self.functions.values()]
            
            error_response = {
                "error": f"Function '{function_name}' not found",
                "nodes": [],
                "edges": [],
                "suggestions": {
                    "message": "函数未在调用图中找到。可能的原因：",
                    "reasons": [
                        "1. 调用图构建时未包含此函数（可能是外部库函数）",
                        "2. 函数名称拼写错误或不匹配",
                        "3. 此函数是控制流关键字（如if/for）而非真正的函数"
                    ],
                    "alternatives": [
                        "使用 search_function_by_name 工具搜索函数",
                        "使用 get_dependency_function 工具获取函数代码",
                        "使用 search_function_calls 工具查找函数调用位置"
                    ]
                }
            }
            
            # 添加相似函数建议
            if similar_funcs:
                error_response["suggestions"]["similar_functions"] = similar_funcs[:5]
                error_response["suggestions"]["note"] = f"在调用图中找到 {len(similar_funcs)} 个相似的函数名"
            
            # 添加调用图统计信息
            error_response["call_graph_info"] = {
                "total_functions_in_graph": len(self.functions),
                "example_functions": all_function_names[:10] if all_function_names else []
            }
            
            return error_response
        
        # 2. BFS搜索指定深度的调用关系
        nodes, edges = self._bfs_search(func_id, depth, direction)
        
        # 3. 构建返回结果
        return {
            "function": function_name,
            "function_id": func_id,
            "file": self.functions[func_id]['file'] if func_id in self.functions else "",
            "call_graph": {
                "direction": direction,
                "depth": depth,
                "nodes": nodes,
                "edges": edges
            },
            "summary": {
                "total_nodes": len(nodes),
                "max_depth_reached": self._calculate_max_depth(nodes),
                "modules_involved": self._extract_modules(nodes)
            }
        }
    
    def _find_similar_functions(self, function_name: str, max_results: int = 5) -> List[str]:
        """查找相似的函数名"""
        similar = []
        func_name_lower = function_name.lower()
        
        for func_id, func in self.functions.items():
            name = func.get('name', '')
            # 模糊匹配：包含、相似前缀等
            if (func_name_lower in name.lower() or 
                name.lower().startswith(func_name_lower[:3]) or
                func_name_lower.startswith(name.lower()[:3])):
                similar.append(name)
            
            if len(similar) >= max_results:
                break
        
        return similar
    
    def _find_function_id(self, function_name: str, file_path: Optional[str] = None) -> Optional[str]:
        """查找函数ID"""
        candidates = []
        
        for func_id, func in self.functions.items():
            if func['name'] == function_name:
                if file_path and func['file'] == file_path:
                    return func_id  # 精确匹配
                candidates.append(func_id)
        
        # 如果没有精确匹配，返回第一个候选
        return candidates[0] if candidates else None
    
    def _bfs_search(
        self, 
        start_func_id: str, 
        max_depth: int, 
        direction: str
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
        """BFS搜索调用关系"""
        visited = {start_func_id}
        nodes = []
        edges = []
        
        # 初始化队列：(function_id, depth, node_type)
        queue = deque([(start_func_id, 0, "entry")])
        
        while queue:
            func_id, current_depth, node_type = queue.popleft()
            
            # 添加节点
            func_info = self.functions.get(func_id, {})
            nodes.append({
                "id": func_id,
                "name": func_info.get('name', func_id),
                "file": func_info.get('file', ''),
                "line": func_info.get('line', 0),
                "type": node_type,
                "depth": current_depth
            })
            
            # 达到最大深度，停止扩展
            if current_depth >= max_depth:
                continue
            
            # 扩展邻居
            neighbors = []
            if direction == "callees":
                neighbors = self.callees.get(func_id, [])
                edge_direction = "calls"
            elif direction == "callers":
                neighbors = self.callers.get(func_id, [])
                edge_direction = "called_by"
            elif direction == "both":
                # 双向搜索
                callees_neighbors = self.callees.get(func_id, [])
                callers_neighbors = self.callers.get(func_id, [])
                neighbors = callees_neighbors + callers_neighbors
                edge_direction = "related"
            
            for neighbor_id in neighbors:
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, current_depth + 1, "related"))
                    
                    # 添加边
                    if direction == "callers" or (direction == "both" and neighbor_id in self.callers.get(func_id, [])):
                        edges.append({
                            "from": neighbor_id,
                            "to": func_id,
                            "type": "calls"
                        })
                    else:
                        edges.append({
                            "from": func_id,
                            "to": neighbor_id,
                            "type": "calls"
                        })
        
        return nodes, edges
    
    def _calculate_max_depth(self, nodes: List[Dict[str, Any]]) -> int:
        """计算实际到达的最大深度"""
        return max((node['depth'] for node in nodes), default=0)
    
    def _extract_modules(self, nodes: List[Dict[str, Any]]) -> List[str]:
        """提取涉及的模块（按文件目录分组）"""
        modules = set()
        for node in nodes:
            file_path = node['file']
            if '/' in file_path:
                module = file_path.split('/')[0]
                modules.add(module)
        return sorted(list(modules))
    
    def get_function_info(self, function_name: str, file_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """获取函数详细信息"""
        func_id = self._find_function_id(function_name, file_path)
        if not func_id:
            return None
        
        return self.functions.get(func_id)
    
    def list_functions_in_file(self, file_path: str) -> List[Dict[str, Any]]:
        """列出文件中的所有函数"""
        func_ids = self.files.get(file_path, [])
        return [self.functions[fid] for fid in func_ids if fid in self.functions]
    
    def find_entry_points(self) -> List[Dict[str, Any]]:
        """查找入口点（没有调用者的函数，如main）"""
        entry_points = []
        for func_id, func in self.functions.items():
            if func.get('is_main') or not self.callers.get(func_id):
                entry_points.append({
                    "id": func_id,
                    "name": func['name'],
                    "file": func['file'],
                    "is_main": func.get('is_main', False)
                })
        return entry_points
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取调用图统计信息"""
        if not self.data:
            return {}
        
        return {
            "project": self.data.get('project', {}),
            "total_functions": len(self.functions),
            "total_files": len(self.files),
            "total_call_edges": len(self.data.get('call_edges', [])),
            "entry_points": len(self.find_entry_points()),
            "average_callees_per_function": sum(len(v) for v in self.callees.values()) / len(self.functions) if self.functions else 0
        }

