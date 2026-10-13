"""
Agent工具集：供AI模型调用的工具函数
"""
import os
import json
import re
from typing import Dict, Any, List, Optional
from pathlib import Path


class AgentTools:
    """Agent可调用的工具集合"""
    
    def __init__(self, project_root: str, task_id: int, global_var_map: Dict[str, Any] = None):
        """
        初始化Agent工具
        
        Args:
            project_root: 项目根目录
            task_id: 任务ID（用于数据库查询）
            global_var_map: 全局变量映射（可选）
        """
        self.project_root = Path(project_root)
        self.task_id = task_id
        self.allowed_extensions = ['.c', '.cpp', '.h', '.hpp', '.cc', '.cxx', '.v', '.vhd', '.vhdl']
        
        # 缓存，避免重复读取
        self.global_var_cache = global_var_map or {}
        self.function_cache = {}
    
    def list_directory(self, relative_path: str = "", max_depth: int = 2) -> Dict[str, Any]:
        """
        列出目录内容
        
        Args:
            relative_path: 相对于项目根目录的路径（默认为项目根目录）
            max_depth: 最大递归深度
            
        Returns:
            目录结构信息
        """
        try:
            target_path = os.path.join(self.project_root, relative_path) if relative_path else self.project_root
            
            if not os.path.exists(target_path):
                return {"error": f"路径不存在: {relative_path}"}
            
            if not os.path.isdir(target_path):
                return {"error": f"不是目录: {relative_path}"}
            
            result = self._scan_directory(target_path, self.project_root, max_depth, 0)
            return {
                "path": relative_path or ".",
                "content": result
            }
        except Exception as e:
            return {"error": f"列出目录失败: {str(e)}"}
    
    def _scan_directory(self, path: str, root: str, max_depth: int, current_depth: int) -> List[Dict[str, Any]]:
        """递归扫描目录"""
        if current_depth >= max_depth:
            return []
        
        items = []
        try:
            for item in sorted(os.listdir(path)):
                # 跳过隐藏文件和特定目录
                if item.startswith('.') or item in ['__pycache__', 'node_modules', 'build', 'dist']:
                    continue
                
                item_path = os.path.join(path, item)
                rel_path = os.path.relpath(item_path, root)
                
                if os.path.isdir(item_path):
                    items.append({
                        "type": "directory",
                        "name": item,
                        "path": rel_path
                    })
                elif os.path.isfile(item_path):
                    ext = os.path.splitext(item)[1].lower()
                    if ext in self.allowed_extensions:
                        # 获取文件大小
                        size = os.path.getsize(item_path)
                        items.append({
                            "type": "file",
                            "name": item,
                            "path": rel_path,
                            "extension": ext,
                            "size": size
                        })
        except Exception as e:
            items.append({"error": f"扫描失败: {str(e)}"})
        
        return items
    
    def search_function_in_file(self, relative_path: str, function_name: str) -> Dict[str, Any]:
        """
        在文件中搜索特定函数
        
        Args:
            relative_path: 相对于项目根目录的文件路径
            function_name: 函数名
            
        Returns:
            函数代码片段
        """
        try:
            file_path = os.path.join(self.project_root, relative_path)
            
            if not os.path.exists(file_path):
                return {"error": f"文件不存在: {relative_path}"}
            
            # 读取文件内容
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
            content = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                return {"error": f"无法解码文件: {relative_path}"}
            
            # 简单的函数搜索（基于关键字匹配）
            lines = content.split('\n')
            function_start = -1
            function_end = -1
            brace_count = 0
            found = False
            
            for i, line in enumerate(lines):
                # 查找函数定义
                if function_name in line and ('(' in line or '{' in line):
                    # 简单检查是否是函数定义（不是函数调用）
                    stripped = line.strip()
                    if not stripped.startswith('//') and not stripped.startswith('/*'):
                        function_start = i
                        found = True
                
                # 找到函数后，计算大括号匹配
                if found:
                    brace_count += line.count('{') - line.count('}')
                    if brace_count == 0 and '{' in ''.join(lines[function_start:i+1]):
                        function_end = i
                        break
            
            if function_start == -1:
                return {
                    "error": f"在文件 {relative_path} 中未找到函数 {function_name}",
                    "suggestion": "请检查函数名是否正确，或使用read_file_range查看指定行范围"
                }
            
            if function_end == -1:
                function_end = min(function_start + 50, len(lines) - 1)
            
            function_code = '\n'.join(lines[function_start:function_end + 1])
            
            return {
                "path": relative_path,
                "function_name": function_name,
                "start_line": function_start + 1,
                "end_line": function_end + 1,
                "code": function_code
            }
        except Exception as e:
            return {"error": f"搜索函数失败: {str(e)}"}
    
    def search_function_by_name(self, function_name: str, limit: int = 10) -> Dict[str, Any]:
        """
        在项目中搜索函数（按函数名）
        
        Args:
            function_name: 函数名
            limit: 返回结果数量限制
            
        Returns:
            搜索结果列表
        """
        try:
            # 从数据库中搜索函数
            from ...config_database import get_db_session
            from ...db.models.function import AnalysisFunction
            from ...db.models.file import AnalysisFile
            
            with get_db_session() as db:
                # 查询函数
                functions = db.query(AnalysisFunction).join(AnalysisFile).filter(
                    AnalysisFile.task_id == self.task_id,
                    AnalysisFunction.function_name.like(f"%{function_name}%")
                ).limit(limit).all()
                
                results = []
                for func in functions:
                    results.append({
                        "function_name": func.function_name,
                        "file_path": func.file_path,
                        "start_line": func.start_line,
                        "end_line": func.end_line,
                        "has_source": func.source_code is not None
                    })
                
                return {
                    "query": function_name,
                    "count": len(results),
                    "results": results
                }
        except Exception as e:
            return {"error": f"搜索函数失败: {str(e)}"}
    
    def get_file_outline(self, relative_path: str) -> Dict[str, Any]:
        """
        获取文件的结构大纲：函数列表、全局变量、宏定义等
        
        Args:
            relative_path: 相对于项目根目录的文件路径
            
        Returns:
            文件结构信息
        """
        try:
            file_path = self.project_root / relative_path
            
            if not file_path.exists():
                return {"error": f"文件不存在: {relative_path}"}
            
            if not file_path.is_file():
                return {"error": f"不是文件: {relative_path}"}
            
            # 读取文件内容
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
            lines = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        lines = f.readlines()
                    break
                except UnicodeDecodeError:
                    continue
            
            if lines is None:
                return {"error": f"无法解码文件: {relative_path}"}
            
            functions = []
            global_vars = []
            macros = []
            includes = []
            
            # 简单的C/C++代码解析
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                
                # 匹配函数定义
                func_match = re.match(r'^([a-zA-Z_][\w\s\*]*)\s+([a-zA-Z_]\w*)\s*\([^)]*\)\s*\{?', stripped)
                if func_match and not stripped.startswith('//') and not stripped.startswith('/*'):
                    functions.append({
                        "name": func_match.group(2),
                        "signature": stripped.rstrip('{').strip(),
                        "line": i
                    })
                
                # 匹配宏定义
                if stripped.startswith('#define'):
                    macros.append({
                        "line": i,
                        "definition": stripped[:80]
                    })
                
                # 匹配include
                if stripped.startswith('#include'):
                    includes.append({
                        "line": i,
                        "file": stripped
                    })
            
            return {
                "file": relative_path,
                "total_lines": len(lines),
                "functions": [f['name'] for f in functions[:50]],  # 最多返回50个函数名
                "function_count": len(functions),
                "macros": macros[:20],
                "includes": [inc['file'].replace('#include', '').strip() for inc in includes[:20]],
                "note": f"文件共 {len(lines)} 行。使用 read_file_range 时，end_line 不能超过 {len(lines)}"
            }
        except Exception as e:
            return {"error": f"获取文件大纲失败: {str(e)}"}
    
    def read_file_range(self, relative_path: str, start_line: int, end_line: int) -> Dict[str, Any]:
        """
        按行范围读取文件内容（自动修正超出范围的行号）
        
        Args:
            relative_path: 相对于项目根目录的文件路径
            start_line: 起始行号（从1开始）
            end_line: 结束行号
            
        Returns:
            文件内容
        """
        try:
            file_path = self.project_root / relative_path
            
            if not file_path.exists():
                return {"error": f"文件不存在: {relative_path}"}
            
            # 读取文件
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
            all_lines = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        all_lines = f.readlines()
                    break
                except UnicodeDecodeError:
                    continue
            
            if all_lines is None:
                return {"error": f"无法解码文件: {relative_path}"}
            
            total_lines = len(all_lines)
            
            # 自动修正超出范围的行号
            warnings = []
            original_end_line = end_line
            
            if start_line < 1:
                warnings.append(f"起始行号 {start_line} 小于1，已自动修正为1")
                start_line = 1
            if start_line > total_lines:
                return {"error": f"起始行号 {start_line} 超出范围（文件共 {total_lines} 行）"}
            
            if end_line > total_lines:
                warnings.append(f"请求的结束行号 {end_line} 超出文件总行数 {total_lines}，已自动修正为 {total_lines}")
                end_line = total_lines
            
            if end_line < start_line:
                return {"error": f"结束行号 {end_line} 小于起始行号 {start_line}"}
            
            # 限制单次读取行数
            max_range = 500
            if end_line - start_line + 1 > max_range:
                warnings.append(f"请求的行数过多（{end_line - start_line + 1}行），已限制为最多{max_range}行")
                end_line = start_line + max_range - 1
            
            # 提取指定范围的行
            selected_lines = all_lines[start_line-1:end_line]
            
            # 添加行号
            numbered_lines = [f"{start_line + i:4d} | {line.rstrip()}" for i, line in enumerate(selected_lines)]
            
            result = {
                "file": relative_path,
                "start_line": start_line,
                "end_line": end_line,
                "line_count": len(selected_lines),
                "content": '\n'.join(numbered_lines)
            }
            
            # 添加警告信息（如果有）
            if warnings:
                result["warnings"] = warnings
            
            # 如果自动修正了行号，添加提示
            if original_end_line > total_lines:
                result["note"] = f"文件共 {total_lines} 行，已读取实际可用的行"
            
            return result
        except Exception as e:
            return {"error": f"读取文件范围失败: {str(e)}"}
    
    def get_function_context(self, relative_path: str, line_number: int) -> Dict[str, Any]:
        """
        获取指定行所在函数的完整代码
        
        Args:
            relative_path: 文件路径
            line_number: 行号
            
        Returns:
            函数代码
        """
        try:
            file_path = self.project_root / relative_path
            
            if not file_path.exists():
                return {"error": f"文件不存在: {relative_path}"}
            
            # 读取文件
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
            lines = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        lines = f.readlines()
                    break
                except UnicodeDecodeError:
                    continue
            
            if lines is None:
                return {"error": f"无法解码文件: {relative_path}"}
            
            if line_number < 1 or line_number > len(lines):
                return {"error": f"行号 {line_number} 超出范围"}
            
            # 向上查找函数开始
            function_start = line_number - 1
            brace_count = 0
            found_function = False
            
            for i in range(line_number - 1, -1, -1):
                line = lines[i]
                # 简单检测函数定义
                if '{' in line and '(' in line:
                    function_start = i
                    found_function = True
                    break
                # 检查是否到达另一个函数的结束
                if '}' in line and i < line_number - 1:
                    break
            
            if not found_function:
                # 尝试从当前行向下找到函数结束
                function_start = max(0, line_number - 20)
            
            # 向下查找函数结束
            function_end = line_number - 1
            brace_count = 0
            in_function = False
            
            for i in range(function_start, len(lines)):
                line = lines[i]
                if '{' in line:
                    in_function = True
                    brace_count += line.count('{')
                if '}' in line:
                    brace_count -= line.count('}')
                    if in_function and brace_count <= 0:
                        function_end = i
                        break
            else:
                function_end = min(function_start + 100, len(lines) - 1)
            
            # 提取函数代码
            function_lines = lines[function_start:function_end + 1]
            numbered_lines = [f"{function_start + i + 1:4d} | {line.rstrip()}" for i, line in enumerate(function_lines)]
            
            return {
                "path": relative_path,
                "line_number": line_number,
                "function_start": function_start + 1,
                "function_end": function_end + 1,
                "content": '\n'.join(numbered_lines)
            }
        except Exception as e:
            return {"error": f"获取函数上下文失败: {str(e)}"}
    
    def get_variable_usage(self, relative_path: str, variable_name: str, line_number: Optional[int] = None) -> Dict[str, Any]:
        """
        追踪变量在文件中的所有使用位置
        
        Args:
            relative_path: 文件路径
            variable_name: 变量名
            line_number: 可选，从哪一行开始查找
            
        Returns:
            变量使用情况
        """
        try:
            file_path = self.project_root / relative_path
            
            if not file_path.exists():
                return {"error": f"文件不存在: {relative_path}"}
            
            # 读取文件
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
            lines = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        lines = f.readlines()
                    break
                except UnicodeDecodeError:
                    continue
            
            if lines is None:
                return {"error": f"无法解码文件: {relative_path}"}
            
            usages = []
            var_pattern = r'\b' + re.escape(variable_name) + r'\b'
            
            for i, line in enumerate(lines, 1):
                if re.search(var_pattern, line):
                    # 判断使用类型
                    usage_type = "读取"
                    if '=' in line and variable_name in line.split('=')[0]:
                        usage_type = "赋值"
                    elif re.search(r'\b(int|char|float|double|void|struct|long|short)\s+.*' + re.escape(variable_name), line):
                        usage_type = "声明"
                    
                    usages.append({
                        "line": i,
                        "type": usage_type,
                        "code": line.strip()
                    })
            
            return {
                "path": relative_path,
                "variable_name": variable_name,
                "usage_count": len(usages),
                "usages": usages[:50]  # 最多返回50个使用位置
            }
        except Exception as e:
            return {"error": f"追踪变量使用失败: {str(e)}"}
    
    def get_call_graph(self, function_name: str, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        获取函数的调用关系
        
        Args:
            function_name: 函数名
            file_path: 可选，限定在某个文件中查找
            
        Returns:
            函数调用关系
        """
        try:
            # 简化实现：搜索函数调用
            callers = []  # 调用此函数的函数
            callees = []  # 此函数调用的函数
            
            # 如果指定了文件，只在该文件中搜索
            if file_path:
                search_path = self.project_root / file_path
                if not search_path.exists():
                    return {"error": f"文件不存在: {file_path}"}
                files_to_search = [search_path]
            else:
                # 搜索所有代码文件
                files_to_search = []
                for ext in self.allowed_extensions:
                    files_to_search.extend(self.project_root.rglob(f"*{ext}"))
            
            func_pattern = re.compile(r'\b' + re.escape(function_name) + r'\s*\(')
            
            for file in files_to_search[:100]:  # 限制搜索文件数
                try:
                    with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    
                    for i, line in enumerate(lines, 1):
                        if func_pattern.search(line):
                            callers.append({
                                "file": str(file.relative_to(self.project_root)),
                                "line": i,
                                "code": line.strip()
                            })
                except:
                    continue
            
            return {
                "function_name": function_name,
                "callers": callers[:20],  # 最多返回20个调用者
                "caller_count": len(callers)
            }
        except Exception as e:
            return {"error": f"获取调用关系失败: {str(e)}"}
    
    def search_code(self, keyword: str, file_pattern: Optional[str] = None) -> Dict[str, Any]:
        """
        在代码库中搜索关键字
        
        Args:
            keyword: 搜索关键字
            file_pattern: 文件模式，如 '*.c'
            
        Returns:
            搜索结果
        """
        try:
            results = []
            
            # 确定搜索文件
            if file_pattern:
                files_to_search = list(self.project_root.rglob(file_pattern))
            else:
                files_to_search = []
                for ext in self.allowed_extensions:
                    files_to_search.extend(self.project_root.rglob(f"*{ext}"))
            
            keyword_pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            
            for file in files_to_search[:100]:  # 限制搜索文件数
                try:
                    with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    
                    for i, line in enumerate(lines, 1):
                        if keyword_pattern.search(line):
                            results.append({
                                "file": str(file.relative_to(self.project_root)),
                                "line": i,
                                "code": line.strip()
                            })
                            
                            if len(results) >= 100:  # 限制结果数量
                                break
                except:
                    continue
                
                if len(results) >= 100:
                    break
            
            return {
                "keyword": keyword,
                "result_count": len(results),
                "results": results
            }
        except Exception as e:
            return {"error": f"搜索代码失败: {str(e)}"}
    
    def get_dependency_function(self, function_name: str) -> Dict[str, Any]:
        """
        获取依赖函数的代码
        
        Args:
            function_name: 函数名
            
        Returns:
            函数信息
        """
        try:
            # 检查缓存
            if function_name in self.function_cache:
                return self.function_cache[function_name]
            
            # 常见标准库函数列表
            standard_functions = {
                'malloc', 'free', 'calloc', 'realloc',
                'memcpy', 'memset', 'memmove', 'memcmp',
                'strcpy', 'strncpy', 'strcat', 'strncat', 'strcmp', 'strncmp', 'strlen', 'strstr',
                'printf', 'fprintf', 'sprintf', 'snprintf', 'scanf', 'fscanf', 'sscanf',
                'fopen', 'fclose', 'fread', 'fwrite', 'fseek', 'ftell', 'feof', 'ferror',
                'exit', 'abort', 'atexit', 'system',
                'sin', 'cos', 'tan', 'sqrt', 'pow', 'exp', 'log',
                'time', 'clock', 'sleep', 'usleep'
            }
            
            # 如果是标准库函数，直接返回友好提示
            if function_name.lower() in standard_functions:
                result = {
                    "function_name": function_name,
                    "found": False,
                    "is_standard_library": True,
                    "message": f"{function_name} 是C标准库函数，无需查看实现。请基于你对标准库的理解进行审查。"
                }
                self.function_cache[function_name] = result
                return result
            
            # 从数据库中搜索函数
            from ...config_database import get_db_session
            from ...db.models.function import AnalysisFunction
            from ...db.models.file import AnalysisFile
            
            with get_db_session() as db:
                func = db.query(AnalysisFunction).join(AnalysisFile).filter(
                    AnalysisFile.task_id == self.task_id,
                    AnalysisFunction.function_name == function_name
                ).first()
                
                if func and func.source_code:
                    result = {
                        "function_name": function_name,
                        "source_code": func.source_code,
                        "file_path": func.file_path,
                        "found": True
                    }
                else:
                    result = {
                        "function_name": function_name,
                        "found": False,
                        "is_standard_library": False,
                        "message": f"未找到函数 {function_name}，可能是外部库函数、系统调用或函数名不准确"
                    }
            
            # 缓存结果
            self.function_cache[function_name] = result
            return result
            
        except Exception as e:
            return {
                "function_name": function_name,
                "found": False,
                "error": f"查找函数时出错: {str(e)}"
            }
    
    def get_global_variable(self, variable_name: str) -> Dict[str, Any]:
        """
        获取全局变量/宏定义
        
        Args:
            variable_name: 变量名
            
        Returns:
            变量信息
        """
        try:
            if not self.global_var_cache:
                return {
                    "variable_name": variable_name,
                    "found": False,
                    "message": "全局变量缓存为空"
                }
            
            if variable_name in self.global_var_cache:
                var_info = self.global_var_cache[variable_name]
                return {
                    "variable_name": variable_name,
                    "type": var_info.get('type', 'variable'),
                    "file": var_info.get('file', ''),
                    "line": var_info.get('line', 0),
                    "code": var_info.get('code', ''),
                    "found": True
                }
            else:
                return {
                    "variable_name": variable_name,
                    "found": False,
                    "message": f"未找到全局变量 {variable_name}"
                }
        
        except Exception as e:
            return {
                "variable_name": variable_name,
                "found": False,
                "error": str(e)
            }
    
    def search_function_calls(self, function_name: str) -> Dict[str, Any]:
        """
        搜索函数调用位置
        
        Args:
            function_name: 函数名
            
        Returns:
            调用位置列表
        """
        try:
            # 简单实现：在项目中搜索函数调用
            call_pattern = re.compile(r'\b' + re.escape(function_name) + r'\s*\(')
            callers = []
            
            # 搜索代码文件
            for file_path in self.project_root.rglob('*'):
                if file_path.suffix.lower() in self.allowed_extensions:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                        
                        for i, line in enumerate(lines, 1):
                            if call_pattern.search(line):
                                callers.append({
                                    "file": str(file_path.relative_to(self.project_root)),
                                    "line": i,
                                    "code": line.strip()
                                })
                                
                                if len(callers) >= 10:  # 最多返回10个
                                    break
                    except:
                        continue
                    
                    if len(callers) >= 10:
                        break
            
            return {
                "function_name": function_name,
                "caller_count": len(callers),
                "callers": callers[:10]
            }
        
        except Exception as e:
            return {
                "function_name": function_name,
                "error": str(e)
            }
    
    def list_all_globals(self) -> Dict[str, Any]:
        """
        列出所有可用的全局变量
        
        Returns:
            全局变量列表
        """
        try:
            if not self.global_var_cache:
                return {"globals": [], "count": 0}
            
            globals_list = []
            for name, info in list(self.global_var_cache.items())[:50]:  # 最多50个
                globals_list.append({
                    "name": name,
                    "type": info.get('type', 'variable'),
                    "file": info.get('file', '')
                })
            
            return {
                "globals": globals_list,
                "count": len(globals_list),
                "total": len(self.global_var_cache)
            }
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def get_tool_definitions() -> List[Dict[str, Any]]:
        """
        获取工具定义（用于OpenAI Function Calling）
        
        Returns:
            工具定义列表
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "list_directory",
                    "description": "列出项目目录的文件和子目录，用于了解项目结构",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "relative_path": {
                                "type": "string",
                                "description": "相对于项目根目录的路径，空字符串表示项目根目录"
                            },
                            "max_depth": {
                                "type": "integer",
                                "description": "递归深度，默认为2",
                                "default": 2
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_function_by_name",
                    "description": "在项目中按函数名搜索函数，用于快速定位功能实现",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "function_name": {
                                "type": "string",
                                "description": "要搜索的函数名（支持部分匹配）"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "返回结果数量限制，默认10个",
                                "default": 10
                            }
                        },
                        "required": ["function_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_function_in_file",
                    "description": "在指定文件中搜索特定函数的代码",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "relative_path": {
                                "type": "string",
                                "description": "文件的相对路径"
                            },
                            "function_name": {
                                "type": "string",
                                "description": "要搜索的函数名"
                            }
                        },
                        "required": ["relative_path", "function_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_file_outline",
                    "description": "获取文件的结构大纲：函数列表、宏定义、include等。**首选工具**，适合快速了解大型文件",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "relative_path": {
                                "type": "string",
                                "description": "文件路径，相对于项目根目录"
                            }
                        },
                        "required": ["relative_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file_range",
                    "description": "按行范围读取文件内容，用于查看特定代码区域",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "relative_path": {
                                "type": "string",
                                "description": "文件路径"
                            },
                            "start_line": {
                                "type": "integer",
                                "description": "起始行号（从1开始）"
                            },
                            "end_line": {
                                "type": "integer",
                                "description": "结束行号"
                            }
                        },
                        "required": ["relative_path", "start_line", "end_line"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_function_context",
                    "description": "获取指定行所在函数的完整代码，用于理解函数上下文",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "relative_path": {
                                "type": "string",
                                "description": "文件路径"
                            },
                            "line_number": {
                                "type": "integer",
                                "description": "行号"
                            }
                        },
                        "required": ["relative_path", "line_number"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_variable_usage",
                    "description": "追踪变量在文件中的所有使用位置（声明、赋值、读取）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "relative_path": {
                                "type": "string",
                                "description": "文件路径"
                            },
                            "variable_name": {
                                "type": "string",
                                "description": "变量名"
                            },
                            "line_number": {
                                "type": "integer",
                                "description": "可选：从哪一行开始查找"
                            }
                        },
                        "required": ["relative_path", "variable_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_call_graph",
                    "description": "获取函数的调用关系：哪些地方调用了该函数",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "function_name": {
                                "type": "string",
                                "description": "函数名"
                            },
                            "file_path": {
                                "type": "string",
                                "description": "可选：限定在某个文件中查找"
                            }
                        },
                        "required": ["function_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_code",
                    "description": "在代码库中搜索包含指定关键字的代码行",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "keyword": {
                                "type": "string",
                                "description": "搜索关键字"
                            },
                            "file_pattern": {
                                "type": "string",
                                "description": "文件模式，如 '*.c'，默认搜索所有代码文件"
                            }
                        },
                        "required": ["keyword"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_dependency_function",
                    "description": "获取依赖函数的完整代码实现，用于理解函数调用的上下文",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "function_name": {
                                "type": "string",
                                "description": "要查询的函数名"
                            }
                        },
                        "required": ["function_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_global_variable",
                    "description": "获取全局变量、宏定义或数组的定义信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "variable_name": {
                                "type": "string",
                                "description": "变量、宏或数组的名称"
                            }
                        },
                        "required": ["variable_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_function_calls",
                    "description": "搜索某个函数在项目中被哪些地方调用，用于理解函数的使用上下文",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "function_name": {
                                "type": "string",
                                "description": "要搜索的函数名"
                            }
                        },
                        "required": ["function_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_all_globals",
                    "description": "列出代码中可能使用的所有全局变量、宏定义和数组的名称",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]

