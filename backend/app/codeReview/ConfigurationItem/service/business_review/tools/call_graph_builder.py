"""
调用图构建器
使用 tree-sitter 静态分析构建项目的完整调用图
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
from collections import defaultdict

# 导入 tree-sitter 相关
try:
    from tree_sitter import Parser
    from ...ai.parser.ts_loader import get_language, get_parser, TS_AVAILABLE
    _TS_AVAILABLE = TS_AVAILABLE
except ImportError:
    _TS_AVAILABLE = False

from ....utils.concurrent_logger import (
    log_concurrent_info as log_info,
    log_concurrent_error as log_error,
    log_concurrent_debug as log_debug
)


class CallGraphBuilder:
    """调用图构建器"""
    
    def __init__(self, project_root: str, language: str = 'c'):
        """
        初始化
        
        Args:
            project_root: 项目根目录
            language: 编程语言 (c/cpp)
        """
        self.project_root = Path(project_root)
        self.language = language
        self.extensions = {'.c', '.cpp', '.cc', '.cxx', '.h', '.hpp'}
        
        # 调用图数据结构
        self.functions: Dict[str, Dict[str, Any]] = {}  # function_id -> 函数详情
        self.call_edges: List[Dict[str, Any]] = []  # 调用边列表
        self.callers: Dict[str, List[str]] = defaultdict(list)  # function_id -> [调用者列表]
        self.callees: Dict[str, List[str]] = defaultdict(list)  # function_id -> [被调用者列表]
        self.files: Dict[str, List[str]] = defaultdict(list)  # file_path -> [函数列表]
        
        # tree-sitter parser
        if _TS_AVAILABLE:
            try:
                # 使用 ts_loader 提供的 get_parser 函数（处理API版本兼容性）
                self.parser = get_parser(language)
                self.ts_enabled = True
                log_info(f"tree-sitter parser initialized for {language}", "call_graph_builder")
            except Exception as e:
                self.ts_enabled = False
                log_error(f"tree-sitter initialization failed: {e}, falling back to regex", "call_graph_builder")
        else:
            self.ts_enabled = False
            log_info("tree-sitter not available, using regex fallback", "call_graph_builder")
    
    def build(self) -> Dict[str, Any]:
        """
        构建完整的调用图
        
        Returns:
            调用图数据结构
        """
        log_info(f"开始构建调用图: {self.project_root}", "call_graph_builder")
        
        # 1. 收集所有代码文件
        code_files = self._collect_code_files()
        log_info(f"找到 {len(code_files)} 个代码文件", "call_graph_builder")
        
        # 2. 第一遍：提取所有函数定义
        for file_path in code_files:
            self._extract_functions_from_file(file_path)
        
        log_info(f"提取了 {len(self.functions)} 个函数定义", "call_graph_builder")
        
        # 3. 第二遍：提取所有函数调用
        for file_path in code_files:
            self._extract_calls_from_file(file_path)
        
        log_info(f"提取了 {len(self.call_edges)} 条调用边", "call_graph_builder")
        
        # 4. 构建索引
        self._build_indexes()
        
        # 5. 返回完整数据
        return self._to_dict()
    
    def _collect_code_files(self) -> List[Path]:
        """收集所有代码文件"""
        code_files = []
        for ext in self.extensions:
            code_files.extend(self.project_root.rglob(f"*{ext}"))
        return code_files
    
    def _extract_functions_from_file(self, file_path: Path):
        """从文件提取函数定义"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            log_error(f"读取文件失败: {file_path}", "call_graph_builder", e)
            return
        
        relative_path = str(file_path.relative_to(self.project_root))
        
        if self.ts_enabled:
            functions = self._extract_functions_ts(content, relative_path)
        else:
            functions = self._extract_functions_regex(content, relative_path)
        
        # 存储函数信息
        for func in functions:
            func_id = self._make_function_id(func['name'], relative_path)
            self.functions[func_id] = func
            self.files[relative_path].append(func_id)
    
    def _extract_functions_ts(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """使用 tree-sitter 提取函数定义"""
        functions = []
        
        try:
            content_bytes = content.encode('utf-8', errors='ignore')
            tree = self.parser.parse(content_bytes)
            root = tree.root_node
            
            # 查询所有函数定义
            query_str = "(function_definition) @func"
            lang_obj = get_language(self.language)
            query = lang_obj.query(query_str)
            captures = query.captures(root)
            
            for node, _ in captures:
                func_info = self._parse_function_node(node, content_bytes, file_path)
                if func_info:
                    functions.append(func_info)
        
        except Exception as e:
            log_error(f"tree-sitter 解析失败: {file_path}", "call_graph_builder", e)
        
        return functions
    
    def _parse_function_node(self, node: Any, content_bytes: bytes, file_path: str) -> Optional[Dict[str, Any]]:
        """解析函数节点"""
        # C/C++控制流关键字（必须排除）
        CONTROL_KEYWORDS = {
            'if', 'else', 'elif', 'for', 'while', 'do', 'switch', 'case',
            'return', 'break', 'continue', 'goto'
        }
        
        try:
            # 获取函数名
            declarator = node.child_by_field_name('declarator')
            func_name = self._extract_function_name(declarator, content_bytes)
            
            if not func_name:
                return None
            
            # ⚠️ 关键过滤：排除控制流关键字
            if func_name.lower() in CONTROL_KEYWORDS:
                return None
            
            # 获取返回类型
            return_type_node = node.child_by_field_name('type')
            return_type = self._slice_text(return_type_node, content_bytes, default="void")
            
            # 获取参数
            parameters = self._extract_parameters(declarator, content_bytes)
            
            # 构建签名
            signature = f"{return_type} {func_name}({parameters})"
            
            return {
                "name": func_name,
                "file": file_path,
                "line": node.start_point[0] + 1,
                "end_line": node.end_point[0] + 1,
                "signature": signature,
                "return_type": return_type,
                "parameters": parameters,
                "is_static": "static" in return_type,
                "is_main": func_name == "main"
            }
        
        except Exception as e:
            log_debug(f"解析函数节点失败: {e}", "call_graph_builder")
            return None

    def _slice_text(self, node: Any, content_bytes: bytes, default: str = "") -> str:
        """tree-sitter 的 start_byte/end_byte 是字节偏移，必须在 bytes 上切片再 decode。"""
        if not node:
            return default
        try:
            return content_bytes[node.start_byte:node.end_byte].decode('utf-8', errors='ignore')
        except Exception:
            return default
    
    def _extract_function_name(self, declarator: Any, content_bytes: bytes) -> Optional[str]:
        """从 declarator 提取函数名"""
        if not declarator:
            return None
        
        # 递归查找 identifier 节点
        def find_identifier(node):
            if node.type == 'identifier':
                return self._slice_text(node, content_bytes, default=None)
            for child in node.children:
                result = find_identifier(child)
                if result:
                    return result
            return None
        
        return find_identifier(declarator)
    
    def _extract_parameters(self, declarator: Any, content_bytes: bytes) -> str:
        """提取函数参数"""
        if not declarator:
            return ""
        
        # 查找 parameter_list 节点
        def find_params(node):
            if node.type == 'parameter_list':
                return self._slice_text(node, content_bytes, default="")
            for child in node.children:
                result = find_params(child)
                if result:
                    return result
            return ""
        
        params = find_params(declarator)
        return params.strip('()')
    
    def _extract_functions_regex(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """使用正则表达式提取函数定义（fallback）"""
        # C/C++控制流关键字（必须排除）
        CONTROL_KEYWORDS = {
            'if', 'else', 'elif', 'for', 'while', 'do', 'switch', 'case',
            'return', 'break', 'continue', 'goto'
        }

        sanitized = self._sanitize_for_regex(content)

        # C函数定义（fallback）：在去注释/去字符串后的文本上做多行匹配
        # 匹配: [修饰符] 返回类型 函数名(参数) {
        pattern = re.compile(
            r"(?m)^(?:\s*(?!#))"
            r"((?:static\s+)?(?:inline\s+)?(?:extern\s+)?(?:const\s+)?[A-Za-z_][\w\s\*]*?)"
            r"\s+([A-Za-z_]\w*)\s*"
            r"\(([^;\)]*)\)\s*\{",
            flags=re.MULTILINE,
        )

        functions: List[Dict[str, Any]] = []

        for match in pattern.finditer(sanitized):
            return_type = (match.group(1) or "").strip()
            func_name = (match.group(2) or "").strip()
            params = (match.group(3) or "").strip()

            if not func_name:
                continue

            if func_name.lower() in CONTROL_KEYWORDS:
                continue

            if any(kw in return_type for kw in ['struct', 'enum', 'union', 'typedef']):
                continue

            if not return_type or return_type.isspace():
                continue

            start_idx = match.start()
            body_open_idx = match.end() - 1
            end_idx = self._find_matching_brace(sanitized, body_open_idx)
            if end_idx is None:
                continue

            start_line = sanitized.count('\n', 0, start_idx) + 1
            end_line = sanitized.count('\n', 0, end_idx) + 1

            functions.append(
                {
                    "name": func_name,
                    "file": file_path,
                    "line": start_line,
                    "end_line": end_line,
                    "signature": f"{return_type} {func_name}({params})",
                    "return_type": return_type,
                    "parameters": params,
                    "is_static": "static" in return_type,
                    "is_main": func_name == "main",
                }
            )

        return functions

    def _extract_calls_from_file(self, file_path: Path):
        """从文件提取函数调用"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            log_error(f"读取文件失败: {file_path}", "call_graph_builder", e)
            return

        relative_path = str(file_path.relative_to(self.project_root))
        if self.ts_enabled:
            self._extract_calls_ts(content, relative_path)
        else:
            self._extract_calls_regex(content, relative_path)

    def _extract_calls_ts(self, content: str, file_path: str):
        """使用 tree-sitter 提取函数调用"""
        # C/C++关键字和控制流结构（需要过滤）
        KEYWORDS_TO_FILTER = {
            # 控制流
            'if', 'else', 'elif', 'for', 'while', 'do', 'switch', 'case', 'break', 'continue',
            # 跳转
            'goto', 'return',
            # 类型和存储
            'sizeof', 'typeof', 'alignof', 'static_assert',
            'typedef', 'struct', 'union', 'enum', 'class',
            # 运算符
            'new', 'delete', 'throw', 'catch', 'try',
            # 其他
            'static', 'extern', 'const', 'volatile', 'inline', 'virtual',
            'public', 'private', 'protected', 'namespace', 'using'
        }
        
        try:
            content_bytes = content.encode('utf-8', errors='ignore')
            tree = self.parser.parse(content_bytes)
            root = tree.root_node
            
            # 查询所有函数调用
            query_str = "(call_expression) @call"
            lang_obj = get_language(self.language)
            query = lang_obj.query(query_str)
            captures = query.captures(root)
            
            # 获取当前文件的函数定义
            file_functions = self.files.get(file_path, [])
            
            for node, _ in captures:
                # 获取被调用的函数名
                function_node = node.child_by_field_name('function')
                if not function_node:
                    continue
                
                callee_name = self._slice_text(function_node, content_bytes, default="")
                call_line = node.start_point[0] + 1
                
                # 过滤关键字（不区分大小写）
                if callee_name.lower() in KEYWORDS_TO_FILTER:
                    continue
                
                # 查找调用发生在哪个函数内
                caller_func = self._find_containing_function(file_functions, call_line)
                
                if caller_func:
                    # 记录调用边
                    self._add_call_edge(caller_func, callee_name, file_path, call_line)
        
        except Exception as e:
            log_error(f"提取函数调用失败: {file_path}", "call_graph_builder", e)
    
    def _extract_calls_regex(self, content: str, file_path: str):
        """使用正则表达式提取函数调用（fallback）"""
        # C/C++关键字和控制流结构（需要过滤）
        KEYWORDS_TO_FILTER = {
            # 控制流
            'if', 'else', 'elif', 'for', 'while', 'do', 'switch', 'case', 'break', 'continue',
            # 跳转
            'goto', 'return',
            # 类型和存储
            'sizeof', 'typeof', 'alignof', 'static_assert',
            'typedef', 'struct', 'union', 'enum', 'class',
            # 运算符
            'new', 'delete', 'throw', 'catch', 'try',
            # 其他
            'static', 'extern', 'const', 'volatile', 'inline', 'virtual',
            'public', 'private', 'protected', 'namespace', 'using'
        }
        
        sanitized = self._sanitize_for_regex(content)

        # 简单的函数调用模式
        pattern = re.compile(r'\b([A-Za-z_]\w*)\s*\(')

        file_functions = self.files.get(file_path, [])
        for match in pattern.finditer(sanitized):
            callee_name = match.group(1)
            if not callee_name:
                continue

            if callee_name.lower() in KEYWORDS_TO_FILTER:
                continue

            call_line = sanitized.count('\n', 0, match.start()) + 1
            caller_func = self._find_containing_function(file_functions, call_line)

            if caller_func:
                self._add_call_edge(caller_func, callee_name, file_path, call_line)

    def _sanitize_for_regex(self, content: str) -> str:
        """移除注释和字符串字面量，保留换行以维持行号一致。"""

        def repl_block_comment(m: re.Match) -> str:
            return "\n" * m.group(0).count("\n")

        def repl_line_comment(m: re.Match) -> str:
            return ""  # 行尾注释不含换行

        def repl_string(m: re.Match) -> str:
            s = m.group(0)
            if not s:
                return s
            # 保留引号，内部替换为空格，避免影响括号/分号位置
            inner = " " * max(0, len(s) - 2)
            return s[0] + inner + s[-1]

        # 1) block comments
        text = re.sub(r"/\*[\s\S]*?\*/", repl_block_comment, content)
        # 2) line comments
        text = re.sub(r"//[^\n]*", repl_line_comment, text)
        # 3) string literals
        text = re.sub(r"\"(?:\\.|[^\\\"])*\"", repl_string, text)
        # 4) char literals
        text = re.sub(r"'(?:\\.|[^\\'])*'", repl_string, text)
        return text

    def _find_matching_brace(self, text: str, open_brace_idx: int) -> Optional[int]:
        """从 open_brace_idx(指向'{') 开始，找到匹配的 '}' 的索引。"""
        if open_brace_idx < 0 or open_brace_idx >= len(text) or text[open_brace_idx] != '{':
            return None

        depth = 0
        for i in range(open_brace_idx, len(text)):
            ch = text[i]
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return i
        return None
    
    def _find_containing_function(self, file_functions: List[str], line: int) -> Optional[str]:
        """查找包含指定行的函数"""
        for func_id in file_functions:
            func = self.functions.get(func_id)
            if func and func['line'] <= line <= func['end_line']:
                return func_id
        return None
    
    def _add_call_edge(self, caller_id: str, callee_name: str, file_path: str, line: int):
        """添加调用边"""
        # 尝试解析被调用函数（可能在其他文件）
        callee_id = self._resolve_callee(callee_name, file_path)
        
        if not callee_id:
            # 可能是外部函数或无法解析
            return
        
        # 避免重复
        edge = {
            "from": caller_id,
            "to": callee_id,
            "from_file": file_path,
            "from_line": line,
            "call_type": "direct"
        }
        
        if edge not in self.call_edges:
            self.call_edges.append(edge)
    
    def _resolve_callee(self, callee_name: str, caller_file: str) -> Optional[str]:
        """解析被调用函数的完整ID"""
        # 1. 先在同文件查找
        for func_id in self.files.get(caller_file, []):
            func = self.functions.get(func_id)
            if func and func['name'] == callee_name:
                return func_id
        
        # 2. 在所有函数中查找
        for func_id, func in self.functions.items():
            if func['name'] == callee_name:
                return func_id
        
        return None
    
    def _make_function_id(self, func_name: str, file_path: str) -> str:
        """生成函数唯一ID"""
        # 格式: filename::function_name
        file_name = Path(file_path).stem
        return f"{file_name}::{func_name}"
    
    def _build_indexes(self):
        """构建索引"""
        for edge in self.call_edges:
            caller = edge['from']
            callee = edge['to']
            
            self.callers[callee].append(caller)
            self.callees[caller].append(callee)
    
    def _to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "project": {
                "name": self.project_root.name,
                "root": str(self.project_root),
                "language": self.language,
                "total_functions": len(self.functions),
                "total_files": len(self.files),
                "total_call_edges": len(self.call_edges)
            },
            "functions": self.functions,
            "call_edges": self.call_edges,
            "indexes": {
                "by_file": dict(self.files),
                "callers": dict(self.callers),
                "callees": dict(self.callees)
            }
        }
    
    def save_to_file(self, output_path: Path):
        """保存调用图到文件"""
        data = self._to_dict()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        log_info(f"调用图已保存: {output_path}", "call_graph_builder")

