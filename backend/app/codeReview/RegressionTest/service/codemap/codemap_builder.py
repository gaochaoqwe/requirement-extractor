"""
代码库地图构建器

基于tree-sitter解析结果，构建完整的代码库调用关系图，
支持层次化显示、问题关联和交互式可视化。
"""

import os
import json
from typing import Dict, List, Set, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import defaultdict

from ..ai.parser.all_graph_parser import build_project_call_graph, parse_file, log_debug
from ..ai.parser.fpga.fpga_parser import extract_fpga_files_from_code, read_file_with_encoding, detect_fpga_language
from ...config import ALLOWED_CODE_EXTENSIONS, FPGA_CODE_EXTENSIONS, ALL_SUPPORTED_EXTENSIONS, get_file_type


@dataclass
class CodeNode:
    """代码节点数据结构"""
    id: str                    # 唯一标识
    name: str                  # 节点名称
    type: str                  # 节点类型：file, function, class
    file_path: str             # 文件路径
    start_line: int            # 起始行号
    end_line: int              # 结束行号
    source_code: str           # 源代码
    calls: List[str]           # 调用的函数列表
    called_by: List[str]       # 被调用的函数列表
    problems: List[Dict]       # 关联的问题列表
    level: int                 # 层级深度
    parent: Optional[str]      # 父节点ID
    children: List[str]        # 子节点ID列表
    function_description: Optional[str] = None  # AI生成的函数描述
    commented_code: Optional[str] = None        # AI生成的注释后代码


@dataclass
class CodeEdge:
    """代码边数据结构"""
    id: str                    # 边的唯一标识
    source: str                # 源节点ID
    target: str                # 目标节点ID
    type: str                  # 边类型：calls, contains, depends
    weight: int                # 权重（调用次数等）
    line_number: Optional[int] # 调用位置行号


@dataclass
class CodeMap:
    """代码地图数据结构"""
    nodes: List[CodeNode]           # 所有节点
    edges: List[CodeEdge]           # 所有边
    root_nodes: List[str]           # 根节点ID列表
    file_tree: List[Dict[str, Any]] # 文件树结构（数组格式，每个文件包含函数children）
    statistics: Dict[str, Any]      # 统计信息


class CodeMapBuilder:
    """代码地图构建器"""
    
    def __init__(self, project_root: str, language: str = "auto"):
        self.project_root = Path(project_root).resolve()
        self.language = language
        self.project_type = self._detect_project_type() if language == "auto" else language
        self.nodes: Dict[str, CodeNode] = {}
        self.edges: List[CodeEdge] = []
        self.call_graph: Dict[str, Dict] = {}
        self.file_functions: Dict[str, List[str]] = defaultdict(list)
        self.problems_by_function: Dict[str, List[Dict]] = defaultdict(list)
        self.fpga_files: Dict[str, Dict] = {}  # 存储FPGA文件信息
        self.db_functions: Dict[str, Dict] = {}  # 存储数据库中的函数信息（兼容旧逻辑：按函数名）
        self.db_functions_by_file_and_name: Dict[Tuple[str, str], Dict] = {}
    
    def _detect_project_type(self) -> str:
        """检测项目类型：c_cpp, fpga, mixed"""
        c_cpp_files = []
        fpga_files = []
        
        # 扫描项目目录下的所有文件
        for file_path in self.project_root.rglob("*"):
            if file_path.is_file():
                file_type = get_file_type(str(file_path))
                if file_type == "c_cpp":
                    c_cpp_files.append(file_path)
                elif file_type == "fpga":
                    fpga_files.append(file_path)
        
        log_debug(f"项目类型识别: C/C++文件 {len(c_cpp_files)} 个, FPGA文件 {len(fpga_files)} 个")
        
        if c_cpp_files and fpga_files:
            return "mixed"
        elif fpga_files:
            return "fpga"
        elif c_cpp_files:
            return "c_cpp"
        else:
            return "unknown"
        
    def build_code_map(self) -> CodeMap:
        """构建完整的代码地图"""
        log_debug(f"开始构建代码地图，项目类型：{self.project_type}")
        
        if self.project_type == "fpga":
            return self._build_fpga_code_map()
        elif self.project_type == "mixed":
            return self._build_mixed_code_map()
        else:  # c_cpp 或其他
            return self._build_c_cpp_code_map()
    
    def _build_c_cpp_code_map(self) -> CodeMap:
        """构建C/C++代码地图"""
        log_debug("构建C/C++代码地图...")
        
        # 1. 构建项目调用图
        self._build_call_graph()
        
        # 2. 创建文件节点
        self._create_file_nodes()
        
        # 3. 创建函数节点
        self._create_function_nodes()
        
        # 4. 创建调用关系边
        self._create_call_edges()
        
        # 5. 创建包含关系边
        self._create_containment_edges()
        
        # 6. 构建文件树
        file_tree = self._build_file_tree()
        
        # 7. 计算统计信息
        statistics = self._calculate_statistics()
        
        # 8. 确定根节点
        root_nodes = self._find_root_nodes()
        
        code_map = CodeMap(
            nodes=list(self.nodes.values()),
            edges=self.edges,
            root_nodes=root_nodes,
            file_tree=file_tree,
            statistics=statistics
        )
        
        log_debug(f"C/C++代码地图构建完成：{len(self.nodes)}个节点，{len(self.edges)}条边")
        return code_map
    
    def _build_fpga_code_map(self) -> CodeMap:
        """构建FPGA代码地图"""
        log_debug("构建FPGA代码地图...")
        
        # 1. 扫描FPGA文件
        self._scan_fpga_files()
        
        # 2. 创建FPGA文件节点
        self._create_fpga_file_nodes()
        
        # 3. 创建FPGA模块节点
        self._create_fpga_module_nodes()
        
        # 4. 创建包含关系边
        self._create_fpga_containment_edges()
        
        # 5. 构建文件树
        file_tree = self._build_fpga_file_tree()
        
        # 6. 计算统计信息
        statistics = self._calculate_fpga_statistics()
        
        # 7. 确定根节点
        root_nodes = self._find_fpga_root_nodes()
        
        code_map = CodeMap(
            nodes=list(self.nodes.values()),
            edges=self.edges,
            root_nodes=root_nodes,
            file_tree=file_tree,
            statistics=statistics
        )
        
        log_debug(f"FPGA代码地图构建完成：{len(self.nodes)}个节点，{len(self.edges)}条边")
        return code_map
    
    def _build_mixed_code_map(self) -> CodeMap:
        """构建混合项目代码地图"""
        log_debug("构建混合项目代码地图...")
        
        # 1. 构建C/C++调用图
        self._build_call_graph()
        
        # 2. 扫描FPGA文件
        self._scan_fpga_files()
        
        # 3. 创建所有节点
        self._create_file_nodes()
        self._create_function_nodes()
        self._create_fpga_file_nodes()
        self._create_fpga_module_nodes()
        
        # 4. 创建边
        self._create_call_edges()
        self._create_containment_edges()
        self._create_fpga_containment_edges()
        
        # 5. 构建文件树
        file_tree = self._build_mixed_file_tree()
        
        # 6. 计算统计信息
        statistics = self._calculate_mixed_statistics()
        
        # 7. 确定根节点
        root_nodes = self._find_mixed_root_nodes()
        
        code_map = CodeMap(
            nodes=list(self.nodes.values()),
            edges=self.edges,
            root_nodes=root_nodes,
            file_tree=file_tree,
            statistics=statistics
        )
        
        log_debug(f"混合项目代码地图构建完成：{len(self.nodes)}个节点，{len(self.edges)}条边")
        return code_map
    
    def _build_call_graph(self):
        """构建项目调用图"""
        try:
            self.call_graph = build_project_call_graph(self.project_root, language=self.language)
            log_debug(f"成功构建调用图，包含{len(self.call_graph)}个函数")
        except Exception as e:
            log_debug(f"构建调用图失败：{e}")
            self.call_graph = {}
    
    def _create_file_nodes(self):
        """创建文件节点"""
        files_processed = set()
        
        for func_name, func_info in self.call_graph.items():
            file_path = func_info.get('file_path', '')
            if file_path and file_path not in files_processed:
                files_processed.add(file_path)
                
                # 计算相对路径
                try:
                    rel_path = str(Path(file_path).relative_to(self.project_root))
                except ValueError:
                    rel_path = os.path.basename(file_path)
                
                # 读取文件内容
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                        line_count = len(file_content.splitlines())
                except Exception:
                    file_content = ""
                    line_count = 0
                
                file_node = CodeNode(
                    id=f"file:{rel_path}",
                    name=os.path.basename(file_path),
                    type="file",
                    file_path=rel_path,
                    start_line=1,
                    end_line=line_count,
                    source_code=file_content,
                    calls=[],
                    called_by=[],
                    problems=[],
                    level=0,
                    parent=None,
                    children=[],
                    function_description=None,
                    commented_code=None
                )
                
                self.nodes[file_node.id] = file_node
                self.file_functions[rel_path] = []
    
    def _create_function_nodes(self):
        """创建函数节点"""
        for func_name, func_info in self.call_graph.items():
            file_path = func_info.get('file_path', '')
            if not file_path:
                continue
                
            try:
                rel_path = str(Path(file_path).relative_to(self.project_root))
            except ValueError:
                rel_path = os.path.basename(file_path)
            
            # 获取数据库中的函数信息（如果存在）
            db_func_info: Dict[str, Any] = {}
            try:
                # 优先：file+name 精确匹配（最可靠）
                db_func_info = self.db_functions_by_file_and_name.get((rel_path.replace('\\', '/'), func_name), {})
                if not db_func_info:
                    # 次选：单函数名匹配（兼容历史逻辑）
                    db_func_info = self.db_functions.get(func_name, {})
                if not db_func_info and '::' in func_name:
                    # 兼容：去命名空间（例如 Pixel::brightness -> brightness）
                    short_name = func_name.split('::')[-1]
                    db_func_info = self.db_functions_by_file_and_name.get((rel_path.replace('\\', '/'), short_name), {})
                    if not db_func_info:
                        db_func_info = self.db_functions.get(short_name, {})
            except Exception:
                db_func_info = {}
            
            # 创建函数节点
            func_node = CodeNode(
                id=f"func:{rel_path}:{func_name}",
                name=func_name,
                type="function",
                file_path=rel_path,
                start_line=func_info.get('start_line', 0),
                end_line=func_info.get('end_line', 0),
                source_code=func_info.get('source_code', ''),
                calls=func_info.get('calls', []),
                called_by=[],
                problems=self.problems_by_function.get(func_name, []),
                level=1,
                parent=f"file:{rel_path}",
                children=[],
                # 添加AI生成的字段
                function_description=db_func_info.get('function_description'),
                commented_code=db_func_info.get('commented_code')
            )
            
            self.nodes[func_node.id] = func_node
            self.file_functions[rel_path].append(func_name)
            
            # 更新文件节点的子节点列表
            file_node_id = f"file:{rel_path}"
            if file_node_id in self.nodes:
                self.nodes[file_node_id].children.append(func_node.id)
    
    def _create_call_edges(self):
        """创建调用关系边"""
        edge_id = 0
        
        for func_name, func_info in self.call_graph.items():
            file_path = func_info.get('file_path', '')
            if not file_path:
                continue
                
            try:
                rel_path = str(Path(file_path).relative_to(self.project_root))
            except ValueError:
                rel_path = os.path.basename(file_path)
            
            source_id = f"func:{rel_path}:{func_name}"
            
            for called_func in func_info.get('calls', []):
                # 查找被调用函数的信息
                target_info = self.call_graph.get(called_func)
                if target_info:
                    target_file = target_info.get('file_path', '')
                    if target_file:
                        try:
                            target_rel_path = str(Path(target_file).relative_to(self.project_root))
                        except ValueError:
                            target_rel_path = os.path.basename(target_file)
                        
                        target_id = f"func:{target_rel_path}:{called_func}"
                        
                        # 创建调用边
                        edge = CodeEdge(
                            id=f"edge:{edge_id}",
                            source=source_id,
                            target=target_id,
                            type="calls",
                            weight=1,
                            line_number=None
                        )
                        
                        self.edges.append(edge)
                        edge_id += 1
                        
                        # 更新被调用函数的called_by列表
                        if target_id in self.nodes:
                            self.nodes[target_id].called_by.append(source_id)
    
    def _create_containment_edges(self):
        """创建包含关系边"""
        edge_id = len(self.edges)
        
        for node_id, node in self.nodes.items():
            if node.parent:
                edge = CodeEdge(
                    id=f"edge:{edge_id}",
                    source=node.parent,
                    target=node_id,
                    type="contains",
                    weight=1,
                    line_number=None
                )
                
                self.edges.append(edge)
                edge_id += 1
    
    def _build_file_tree(self) -> List[Dict[str, Any]]:
        """
        构建文件树结构（数组格式，适配前端）
        
        Returns:
            文件树列表，每个文件包含其函数列表
        """
        file_tree = []
        
        for node_id, node in self.nodes.items():
            if node.type == "file":
                # 获取该文件的所有函数节点
                function_children = []
                for func_name in self.file_functions.get(node.file_path, []):
                    func_node_id = f"func:{node.file_path}:{func_name}"
                    func_node = self.nodes.get(func_node_id)
                    
                    if func_node:
                        function_children.append({
                            'id': func_node_id,
                            'name': func_name,
                            'type': 'function',
                            'file_path': node.file_path,
                            'start_line': func_node.start_line,
                            'end_line': func_node.end_line,
                            'source_code': func_node.source_code,
                            'problems': func_node.problems,
                            'problemCount': len(func_node.problems),
                            'function_description': func_node.function_description,
                            'commented_code': func_node.commented_code
                        })
                
                # 添加文件节点
                file_tree.append({
                    'id': node_id,
                    'name': Path(node.file_path).name,
                    'type': 'file',
                    'file_path': node.file_path,
                    'problems': node.problems,
                    'problemCount': len(node.problems),
                    'children': function_children
                })
        
        return file_tree
    
    def _calculate_statistics(self) -> Dict[str, Any]:
        """计算统计信息"""
        file_count = sum(1 for node in self.nodes.values() if node.type == "file")
        function_count = sum(1 for node in self.nodes.values() if node.type == "function")
        call_count = sum(1 for edge in self.edges if edge.type == "calls")
        problem_count = sum(len(node.problems) for node in self.nodes.values())
        
        # 计算复杂度指标
        max_calls_out = max((len(node.calls) for node in self.nodes.values() if node.type == "function"), default=0)
        max_calls_in = max((len(node.called_by) for node in self.nodes.values() if node.type == "function"), default=0)
        
        return {
            'file_count': file_count,
            'function_count': function_count,
            'call_count': call_count,
            'problem_count': problem_count,
            'max_calls_out': max_calls_out,
            'max_calls_in': max_calls_in,
            'avg_calls_per_function': call_count / function_count if function_count > 0 else 0
        }
    
    def _find_root_nodes(self) -> List[str]:
        """查找根节点（没有被调用的函数）"""
        root_nodes = []
        
        for node_id, node in self.nodes.items():
            if node.type == "function" and not node.called_by:
                root_nodes.append(node_id)
        
        return root_nodes
    
    def associate_problems(self, problems: List[Dict]):
        """关联问题到函数节点"""
        for problem in problems:
            # 获取问题信息
            func_name = problem.get('function_name')
            file_name = problem.get('file_name', '')
            
            if func_name:
                # 存储问题到函数名映射
                self.problems_by_function[func_name].append(problem)
                
                # 同时按文件路径存储问题，用于FPGA项目
                if file_name:
                    # 标准化文件路径（处理路径分隔符）
                    normalized_path = file_name.replace('\\', '/')
                    self.problems_by_function[f"file:{normalized_path}"].append(problem)
    
    def associate_functions(self, functions: List):
        """关联数据库中的函数信息（包含AI生成的描述和注释代码）"""
        self.db_functions = {}
        self.db_functions_by_file_and_name = {}

        def _norm_path(p: Any) -> str:
            s = str(p or "")
            s = s.replace('\\', '/')
            if s.startswith('./'):
                s = s[2:]
            parts = [x for x in s.split('/') if x not in ("", ".")]
            # 回归测试约定：忽略第一级目录（old/new/... -> ...）
            if len(parts) >= 2:
                return '/'.join(parts[1:])
            return '/'.join(parts)

        def _name_variants(n: Any) -> List[str]:
            name = str(n or '').strip()
            if not name:
                return []
            out = {name}
            if '::' in name:
                out.add(name.split('::')[-1])
            return list(out)

        for func in functions:
            # 将函数对象转换为字典（如果需要）
            if hasattr(func, 'to_dict'):
                func_dict = func.to_dict()
            else:
                func_dict = func
            
            func_name = func_dict.get('function_name')
            file_path = _norm_path(func_dict.get('file_path'))
            for nv in _name_variants(func_name):
                # 兼容旧：按 name 做索引（可能会被同名函数覆盖，但保留行为）
                self.db_functions[nv] = func_dict
                # 更可靠：按 (file_path, name) 建索引，避免跨文件同名覆盖
                if file_path:
                    self.db_functions_by_file_and_name[(file_path, nv)] = func_dict
    
    def to_dict(
        self,
        code_map: CodeMap,
        project_name: Optional[str] = None,
        project_root: Optional[str] = None,
        mode: str = "function"
    ) -> Dict[str, Any]:
        """转换为字典格式，便于JSON序列化"""

        data = {
            'nodes': [asdict(node) for node in code_map.nodes],
            'edges': [asdict(edge) for edge in code_map.edges],
            'root_nodes': code_map.root_nodes,
            'file_tree': code_map.file_tree,
            'statistics': code_map.statistics,
            'project': {
                'name': project_name or self.project_root.name,
                'mode': mode,
                'root_path': str(project_root or self.project_root)
            }
        }

        return data
    
    def save_to_file(self, code_map: CodeMap, output_path: str):
        """保存代码地图到文件"""
        try:
            data = self.to_dict(code_map)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            log_debug(f"代码地图已保存到：{output_path}")
        except Exception as e:
            log_debug(f"保存代码地图失败：{e}")

    # FPGA相关方法
    def _scan_fpga_files(self):
        """扫描FPGA文件"""
        for file_path in self.project_root.rglob("*"):
            if file_path.is_file() and get_file_type(str(file_path)) == "fpga":
                try:
                    content, encoding = read_file_with_encoding(str(file_path))
                    file_info_list = extract_fpga_files_from_code(content, str(file_path))
                    if file_info_list:
                        rel_path = str(file_path.relative_to(self.project_root))
                        self.fpga_files[rel_path] = file_info_list[0]
                        log_debug(f"扫描到FPGA文件: {rel_path}")
                except Exception as e:
                    log_debug(f"扫描FPGA文件失败: {file_path}, 错误: {e}")
    
    def _create_fpga_file_nodes(self):
        """创建FPGA文件节点"""
        for rel_path, file_info in self.fpga_files.items():
            # 查找该文件相关的问题
            normalized_path = rel_path.replace('\\', '/')
            file_problems = self.problems_by_function.get(f"file:{normalized_path}", [])
            
            # 获取数据库中的函数信息（FPGA文件以function_name为键）
            display_name = file_info.get('function_name', '')
            db_func_info = {}
            if display_name:
                db_func_info = self.db_functions.get(display_name, {})
            
            file_node = CodeNode(
                id=f"fpga_file:{rel_path}",
                name=os.path.basename(rel_path),
                type="fpga_file",
                file_path=rel_path,
                start_line=1,
                end_line=file_info.get('end_line', 1),
                source_code=file_info.get('source_code', ''),
                calls=[],
                called_by=[],
                problems=file_problems,
                level=0,
                parent=None,
                children=[],
                # 从数据库中获取AI生成的信息
                function_description=db_func_info.get('function_description'),
                commented_code=db_func_info.get('commented_code')
            )
            self.nodes[file_node.id] = file_node
    
    def _create_fpga_module_nodes(self):
        """创建FPGA模块节点
        
        注意：FPGA项目以文件为审查单位，不需要创建子模块节点
        所有审查数据都关联到文件级别
        """
        # FPGA项目不创建子模块节点，因为：
        # 1. 审查单位是文件而非模块
        # 2. 所有问题和AI注释都关联到文件
        # 3. 代码树只需要显示文件，不需要显示子模块
        pass
    
    def _create_fpga_containment_edges(self):
        """创建FPGA包含关系边
        
        注意：FPGA项目以文件为审查单位，不创建子模块节点，因此也不需要包含关系边
        """
        # FPGA项目不创建模块节点，因此不需要创建包含关系边
        pass
    
    def _build_fpga_file_tree(self) -> List[Dict]:
        """构建FPGA文件树
        
        注意：FPGA项目以文件为审查单位，不创建子节点
        """
        file_tree = []
        
        for rel_path, file_info in self.fpga_files.items():
            file_id = f"fpga_file:{rel_path}"
            if file_id not in self.nodes:
                continue
                
            file_node = self.nodes[file_id]
            
            # FPGA文件不需要子节点，因为审查单位是文件
            # 所有问题和AI注释都直接关联到文件节点
            file_tree.append({
                "id": file_node.id,
                "name": file_node.name,
                "type": file_node.type,
                "file_path": file_node.file_path,
                "start_line": file_node.start_line,
                "end_line": file_node.end_line,
                "source_code": file_node.source_code,
                "problems": file_node.problems,
                "problemCount": len(file_node.problems),
                # 使用节点实际的AI生成信息
                "function_description": file_node.function_description,
                "commented_code": file_node.commented_code,
                "children": []  # FPGA文件不显示子模块
            })
        
        # 按文件名排序
        file_tree.sort(key=lambda x: x["name"])
        return file_tree
    
    def _calculate_fpga_statistics(self) -> Dict[str, Any]:
        """计算FPGA统计信息
        
        注意：FPGA项目以文件为审查单位，统计信息中的functions数量为0
        """
        fpga_files = [n for n in self.nodes.values() if n.type == "fpga_file"]
        
        return {
            "total_nodes": len(self.nodes),
            "total_files": len(fpga_files),
            "total_functions": 0,  # FPGA项目以文件为单位，不统计函数/模块数
            "total_problems": sum(len(n.problems) for n in self.nodes.values()),
            "total_edges": len(self.edges),
            "max_depth": 0,  # FPGA项目只有文件层级，没有子节点
            "project_type": "fpga"
        }
    
    def _find_fpga_root_nodes(self) -> List[str]:
        """查找FPGA根节点"""
        return [node_id for node_id, node in self.nodes.items() if node.type == "fpga_file"]
    
    def _build_mixed_file_tree(self) -> List[Dict]:
        """构建混合项目文件树"""
        # 合并C/C++和FPGA的文件树
        c_cpp_tree = self._build_file_tree()
        fpga_tree = self._build_fpga_file_tree()
        return c_cpp_tree + fpga_tree
    
    def _calculate_mixed_statistics(self) -> Dict[str, Any]:
        """计算混合项目统计信息"""
        c_cpp_files = [n for n in self.nodes.values() if n.type == "file"]
        c_cpp_functions = [n for n in self.nodes.values() if n.type == "function"]
        fpga_files = [n for n in self.nodes.values() if n.type == "fpga_file"]
        fpga_modules = [n for n in self.nodes.values() if n.type == "fpga_module"]
        
        return {
            "total_nodes": len(self.nodes),
            "total_files": len(c_cpp_files) + len(fpga_files),
            "total_functions": len(c_cpp_functions) + len(fpga_modules),
            "total_problems": sum(len(n.problems) for n in self.nodes.values()),
            "total_edges": len(self.edges),
            "max_depth": max(n.level for n in self.nodes.values()) if self.nodes else 0,
            "project_type": "mixed",
            "c_cpp_files": len(c_cpp_files),
            "c_cpp_functions": len(c_cpp_functions),
            "fpga_files": len(fpga_files),
            "fpga_modules": len(fpga_modules)
        }
    
    def _find_mixed_root_nodes(self) -> List[str]:
        """查找混合项目根节点"""
        return [node_id for node_id, node in self.nodes.items() 
                if node.type in ["file", "fpga_file"]]


def create_code_map(
    project_root: str,
    language: str = "auto",
    problems: Optional[List[Dict]] = None,
    functions: Optional[List] = None
) -> Dict[str, Any]:
    """创建代码地图的便捷函数"""
    builder = CodeMapBuilder(project_root, language)
    
    if problems:
        builder.associate_problems(problems)
    
    if functions:
        builder.associate_functions(functions)
    
    code_map = builder.build_code_map()
    return builder.to_dict(code_map)


if __name__ == "__main__":
    # 测试代码地图构建
    test_project = "/path/to/test/project"
    code_map = create_code_map(test_project, "auto")  # 使用自动检测
    
    builder = CodeMapBuilder(test_project, "auto")
    builder.save_to_file(code_map, "code_map.json") 