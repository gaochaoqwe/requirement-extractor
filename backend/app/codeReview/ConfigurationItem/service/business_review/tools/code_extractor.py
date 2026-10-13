"""
代码提取工具 - 用于渐进式分析

提供：
1. 目录树提取
2. 函数签名提取
3. main函数定位
4. 文件摘要
"""
import os
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import re

from ...ai.parser.fpga.fpga_parser import extract_fpga_files_from_code, read_file_with_encoding


class CodeExtractor:
    """代码提取工具"""
    
    # 支持的代码文件扩展名
    CODE_EXTENSIONS = {
        'c': ['.c', '.h'],
        'cpp': ['.cpp', '.cc', '.cxx', '.hpp', '.h', '.hxx'],
        'fpga': ['.v', '.sv', '.vhd', '.vhdl'],
        'python': ['.py'],
        'java': ['.java'],
        'javascript': ['.js', '.jsx'],
        'typescript': ['.ts', '.tsx']
    }
    
    # 忽略的目录
    IGNORE_DIRS = {
        '__pycache__', 'node_modules', '.git', 'venv', 'env',
        'dist', 'build', '.pytest_cache', '.mypy_cache', 'coverage'
    }
    
    def __init__(self, project_root: str, language: str = 'c'):
        """
        初始化代码提取器
        
        Args:
            project_root: 项目根目录
            language: 编程语言
        """
        self.project_root = Path(project_root)
        self.language = language
        self.extensions = self.CODE_EXTENSIONS.get(language, self.CODE_EXTENSIONS['c'])
    
    def extract_directory_tree(self, max_depth: int = 3) -> Dict[str, Any]:
        """
        提取目录树结构
        
        Args:
            max_depth: 最大深度
            
        Returns:
            目录树字典
        """
        tree = {
            "path": str(self.project_root),
            "name": self.project_root.name,
            "type": "directory",
            "children": [],
            "statistics": {
                "total_dirs": 0,
                "total_files": 0,
                "code_files": 0
            }
        }
        
        self._build_tree(self.project_root, tree, current_depth=0, max_depth=max_depth)
        
        return tree
    
    def _build_tree(self, path: Path, node: Dict[str, Any], current_depth: int, max_depth: int):
        """递归构建目录树"""
        if current_depth >= max_depth:
            return
        
        try:
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
        except PermissionError:
            return
        
        for item in items:
            # 忽略特殊目录
            if item.name in self.IGNORE_DIRS or item.name.startswith('.'):
                continue
            
            if item.is_dir():
                dir_node = {
                    "path": str(item.relative_to(self.project_root)),
                    "name": item.name,
                    "type": "directory",
                    "children": [],
                    "statistics": {
                        "total_dirs": 0,
                        "total_files": 0,
                        "code_files": 0
                    }
                }
                node["children"].append(dir_node)
                node["statistics"]["total_dirs"] += 1
                
                # 递归处理子目录
                self._build_tree(item, dir_node, current_depth + 1, max_depth)
            
            elif item.is_file() and item.suffix in self.extensions:
                file_node = {
                    "path": str(item.relative_to(self.project_root)),
                    "name": item.name,
                    "type": "file",
                    "extension": item.suffix,
                    "size": item.stat().st_size
                }
                node["children"].append(file_node)
                node["statistics"]["total_files"] += 1
                node["statistics"]["code_files"] += 1
    
    def extract_function_signatures(self, file_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        提取函数签名
        
        Args:
            file_path: 文件路径，None表示提取所有文件
            
        Returns:
            函数签名列表
        """
        signatures = []
        
        if file_path:
            # 提取单个文件
            full_path = self.project_root / file_path
            if full_path.exists():
                signatures.extend(self._extract_from_file(full_path))
        else:
            # 提取所有文件
            for file in self._get_all_code_files():
                signatures.extend(self._extract_from_file(file))
        
        return signatures
    
    def _get_all_code_files(self) -> List[Path]:
        """获取所有代码文件"""
        code_files = []
        for ext in self.extensions:
            code_files.extend(self.project_root.rglob(f"*{ext}"))
        
        # 过滤掉忽略目录中的文件
        filtered = []
        for file in code_files:
            skip = False
            for part in file.parts:
                if part in self.IGNORE_DIRS:
                    skip = True
                    break
            if not skip:
                filtered.append(file)
        
        return filtered
    
    def _extract_from_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """从单个文件提取函数签名"""
        signatures = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            return signatures
        
        # 根据语言选择不同的提取方法
        if self.language in ['c', 'cpp']:
            signatures = self._extract_c_functions(content, file_path)
        elif self.language == 'fpga':
            signatures = self._extract_fpga_modules(file_path)
        elif self.language == 'python':
            signatures = self._extract_python_functions(content, file_path)
        
        return signatures
    

    def _extract_fpga_modules(self, file_path: Path) -> List[Dict[str, Any]]:
        """提取 FPGA 文件中的模块/实体签名。"""
        signatures = []
        try:
            content, _ = read_file_with_encoding(str(file_path))
            if not content:
                return signatures

            fpga_infos = extract_fpga_files_from_code(content, str(file_path))
            rel_path = str(file_path.relative_to(self.project_root))
            for info in fpga_infos:
                signatures.append({
                    "name": info.get("function_name", file_path.stem),
                    "signature": info.get("function_name", file_path.stem),
                    "file": rel_path,
                    "line": info.get("start_line", 1),
                    "end_line": info.get("end_line", 1),
                    "type": "module",
                    "language": info.get("language", "verilog"),
                })
        except Exception:
            return signatures
        return signatures

    def _extract_c_functions(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """
        提取C/C++函数**定义**（非调用语句、非声明）。

        策略：
        1. 逐行扫描，对每行去掉行注释后做匹配。
        2. 函数定义行必须顶格（缩进 <= 1 字符）。
        3. 签名后跟 { 的才算定义（排除仅有 ; 的声明）。
        4. 允许 { 出现在同一行末尾，或紧跟在下一行开头。
        5. 排除控制流关键字及 struct/enum/union/typedef。
        """
        signatures = []

        # 逐行处理，去掉行内注释
        raw_lines = content.split('\n')

        # 先做一次块注释标记（标出哪些行在块注释内）
        in_block_comment = False
        line_in_comment: List[bool] = []
        for line in raw_lines:
            if in_block_comment:
                line_in_comment.append(True)
                if '*/' in line:
                    in_block_comment = False
            else:
                if '/*' in line and '*/' not in line.split('/*', 1)[1]:
                    in_block_comment = True
                line_in_comment.append(False)

        # 函数定义行正则：
        # [修饰符] 返回类型[*] 函数名 ( 参数 ) [const] {
        # 要求：行首无缩进（或仅1字符），且以 { 结尾（允许后面有注释）
        LINE_RE = re.compile(
            r'^(?P<modifiers>(?:(?:static|inline|extern|__inline__|__forceinline)\s+)*)'
            r'(?P<ret>(?:(?:const|volatile|unsigned|signed|long|short)\s+)*'
            r'(?:void|int|char|float|double|bool'
            r'|size_t|ssize_t|ptrdiff_t|intptr_t|uintptr_t'
            r'|uint8_t|uint16_t|uint32_t|uint64_t'
            r'|int8_t|int16_t|int32_t|int64_t'
            r'|[A-Za-z_][A-Za-z0-9_]*)'
            r'(?:\s*\*+)?)'
            r'\s+'
            r'(?P<name>[A-Za-z_][A-Za-z0-9_]*)'
            r'\s*\((?P<params>[^)]*)\)'
            r'(?:\s*const)?'
            r'\s*\{'
        )

        EXCLUDED_NAMES = {
            'if', 'else', 'while', 'for', 'switch', 'do', 'return',
            'sizeof', 'typedef', 'struct', 'enum', 'union', 'class',
            'namespace', 'template', 'operator', 'case', 'default'
        }
        EXCLUDED_RET_WORDS = {'struct', 'enum', 'union', 'typedef'}

        seen_names: set = set()
        rel_path = str(file_path.relative_to(self.project_root))

        for lineno, (raw_line, in_cmt) in enumerate(zip(raw_lines, line_in_comment), start=1):
            if in_cmt:
                continue

            # 去掉行注释
            stripped = re.sub(r'//.*', '', raw_line)

            # 必须顶格（缩进 <= 1）
            indent = len(stripped) - len(stripped.lstrip())
            if indent > 1:
                continue

            # 尝试在本行匹配
            m = LINE_RE.match(stripped.strip())
            if not m:
                # 尝试把下一行的 { 拼上来再匹配（定义体 { 在下一行的风格）
                if lineno < len(raw_lines):
                    next_stripped = re.sub(r'//.*', '', raw_lines[lineno]).strip()
                    combined = stripped.strip() + ' ' + next_stripped
                    m = LINE_RE.match(combined)
                if not m:
                    continue

            func_name = m.group('name')
            params = m.group('params').strip()
            ret_type = (m.group('modifiers') + m.group('ret')).strip()

            if func_name in EXCLUDED_NAMES:
                continue
            if any(kw in ret_type.split() for kw in EXCLUDED_RET_WORDS):
                continue
            if not ret_type:
                continue
            if func_name in seen_names:
                continue

            seen_names.add(func_name)
            signatures.append({
                "name": func_name,
                "signature": f"{ret_type} {func_name}({params})",
                "return_type": ret_type,
                "parameters": params,
                "file": rel_path,
                "line": lineno,
                "is_main": func_name == "main"
            })

        return signatures
    
    def _extract_python_functions(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """提取Python函数签名"""
        signatures = []
        
        pattern = r'def\s+(\w+)\s*\((.*?)\)\s*(?:->.*?)?:'
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            match = re.search(pattern, line)
            if match:
                func_name = match.group(1)
                params = match.group(2).strip()
                
                signatures.append({
                    "name": func_name,
                    "signature": line.strip(),
                    "parameters": params,
                    "file": str(file_path.relative_to(self.project_root)),
                    "line": i,
                    "is_main": func_name == "main"
                })
        
        return signatures
    
    def find_main_function(self) -> Optional[Dict[str, Any]]:
        """
        查找main函数
        
        Returns:
            main函数信息
        """
        all_signatures = self.extract_function_signatures()
        
        for sig in all_signatures:
            if sig.get("is_main"):
                return sig
        
        return None
    
    def get_file_summary(self, file_path: str) -> Dict[str, Any]:
        """
        获取文件摘要信息
        
        Args:
            file_path: 文件路径（相对于项目根目录）
            
        Returns:
            文件摘要
        """
        full_path = self.project_root / file_path
        
        if not full_path.exists():
            return {"error": "File not found"}
        
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            return {"error": str(e)}
        
        lines = content.split('\n')
        functions = self._extract_from_file(full_path)
        
        # 提取全局变量（简化版）
        global_vars = []
        if self.language in ['c', 'cpp']:
            # 简单匹配: 类型 变量名;
            for line in lines:
                if re.match(r'^\s*(?:static\s+)?(?:const\s+)?[\w\s\*]+\s+\w+\s*(?:=.*)?;', line):
                    global_vars.append(line.strip())
        
        summary = {
            "file": file_path,
            "total_lines": len(lines),
            "total_functions": len(functions),
            "functions": [f["name"] for f in functions],
            "global_variables_count": len(global_vars),
            "has_main": any(f.get("is_main") for f in functions)
        }
        
        return summary
    
    def list_files_by_directory(self, directory: Optional[str] = None) -> Dict[str, List[str]]:
        """
        按目录列出文件
        
        Args:
            directory: 目录路径，None表示根目录
            
        Returns:
            目录->文件列表的映射
        """
        base_path = self.project_root
        if directory:
            base_path = self.project_root / directory
        
        result = {}
        
        for file in self._get_all_code_files():
            if base_path in file.parents or file.parent == base_path:
                dir_name = str(file.parent.relative_to(self.project_root))
                if dir_name not in result:
                    result[dir_name] = []
                result[dir_name].append(str(file.relative_to(self.project_root)))
        
        return result
    
    def get_compact_overview(self) -> str:
        """
        获取紧凑的项目概览（用于AI第一轮分析）
        
        Returns:
            格式化的字符串
        """
        tree = self.extract_directory_tree(max_depth=2)
        main_func = self.find_main_function()
        all_functions = self.extract_function_signatures()
        
        overview = f"# 项目概览\n\n"
        overview += f"## 基本信息\n"
        overview += f"- 项目名称: {self.project_root.name}\n"
        overview += f"- 编程语言: {self.language}\n"
        overview += f"- 代码文件数: {tree['statistics']['code_files']}\n"
        overview += f"- 总函数数: {len(all_functions)}\n\n"
        
        overview += f"## 目录结构\n"
        overview += self._format_tree(tree, indent=0)
        
        if main_func:
            overview += f"\n## 入口函数\n"
            overview += f"- 位置: {main_func['file']}:{main_func['line']}\n"
            overview += f"- 签名: {main_func['signature']}\n"
        
        overview += f"\n## 主要函数列表（前20个）\n"
        for func in all_functions[:20]:
            overview += f"- {func['name']} @ {func['file']}\n"
        
        return overview
    
    def _format_tree(self, node: Dict[str, Any], indent: int) -> str:
        """格式化目录树"""
        output = ""
        prefix = "  " * indent
        
        if node["type"] == "directory":
            output += f"{prefix}📁 {node['name']}/\n"
        else:
            output += f"{prefix}📄 {node['name']}\n"
        
        for child in node.get("children", []):
            output += self._format_tree(child, indent + 1)
        
        return output

