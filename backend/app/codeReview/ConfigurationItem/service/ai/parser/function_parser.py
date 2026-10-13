"""
C/C++ Function Parser
"""
import re
from typing import List, Dict
import os

# 导入统一的日志系统
from ....utils.logger import log_debug, log_warning

# 使用新的手动加载器
try:
    from tree_sitter import Parser
    # 从本地加载器导入
    from .ts_loader import get_language
    from .ts_loader import TS_AVAILABLE as _TS_AVAILABLE
except ImportError as e:
    # Log the specific import error to the debug file for visibility
    log_debug(f"CRITICAL: Failed to import tree-sitter components. Error: {e}")
    _TS_AVAILABLE = False

# 新增 chardet 用于自动识别编码
try:
    import chardet
    _CHARDET_AVAILABLE = True
except ImportError:
    _CHARDET_AVAILABLE = False


def is_valid_c_identifier(name):
    return re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name) is not None


def find_identifier_in_declarator(node, code):
    if node.type == "identifier":
        name = code[node.start_byte:node.end_byte]
        if is_valid_c_identifier(name):
            return name
    for child in node.children:
        result = find_identifier_in_declarator(child, code)
        if result:
            return result
    return None


def print_node(node, code, indent=0):
    try:
        log_debug('  ' * indent + f"{node.type}: {code[node.start_byte:node.end_byte].replace(chr(10), ' ')}")
        for child in node.children:
            print_node(child, code, indent + 1)
    except Exception as e:
        log_debug(f"print_node异常: {e}")


def _extract_functions_ts(code: str, lang: str) -> List[Dict]:
    """使用 tree-sitter 解析函数定义，包括类/结构体成员函数。"""
    log_debug(f"_extract_functions_ts called, language={lang}, code_len={len(code)}")
    lang_obj = get_language(lang)
    if not lang_obj:
        log_debug(f"[function_parser] Language '{lang}' not available for tree-sitter.")
        return []
    log_debug(f"get_language({lang}) 返回: {lang_obj}")

    try:
        parser = Parser()
        parser.set_language(lang_obj)
        tree = parser.parse(code.encode())
        root = tree.root_node
    except Exception as e:
        log_debug(f"[function_parser] tree-sitter解析异常: {e}")
        return []

    query_str = """
    (function_definition) @func
    """
    try:
        query = lang_obj.query(query_str)
        captures = query.captures(root)
    except Exception as e:
        log_debug(f"[function_parser] tree-sitter查询异常: {e}")
        return []

    functions = []
    unique_functions = {}

    for node, name in captures:
        if name == "func":
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            func_code = node.text.decode('utf8', errors='ignore')

            # Robustly find the function name by traversing the declarator chain
            func_name = ""
            declarator_node = node.child_by_field_name('declarator')
            
            temp_node = declarator_node
            while temp_node:
                # If the current node is the identifier, we found it.
                if temp_node.type == 'identifier':
                    func_name = temp_node.text.decode('utf8')
                    break
                
                # The actual identifier is usually nested in a 'declarator' field.
                # We traverse down this chain until we can't anymore.
                declarator_child = temp_node.child_by_field_name('declarator')
                if declarator_child:
                    temp_node = declarator_child
                    continue

                # If there's no 'declarator' child, the identifier might be a direct child.
                # This handles cases like `int (*func)()` where the identifier is inside a parenthesized_declarator.
                found_identifier = False
                for child in temp_node.children:
                    if child.type == 'identifier':
                        temp_node = child
                        found_identifier = True
                        break
                if found_identifier:
                    continue
                
                # If we reach here, we've exhausted our search down the tree.
                break

            if func_name:
                if func_name not in unique_functions:
                    unique_functions[func_name] = start_line
                    functions.append({
                        'function_name': func_name,
                        'source_code': func_code,
                        'start_line': start_line,
                        'end_line': end_line
                    })
            else:
                snippet = func_code[:80].replace('\n', ' ')
                log_debug(f"function_definition原始代码: {snippet}")
                log_debug(f"未能识别函数名，节点起止行: {start_line}-{end_line}")

    log_debug(f"_extract_functions_ts 提取完成，共{len(functions)}个函数")
    return functions


def extract_functions_from_code(code: str, language: str = "c") -> List[Dict]:
    """提取C/C++函数，优先使用tree-sitter，失败时回退到正则表达式。"""
    log_debug(f"extract_functions_from_code called, language={language}, code_len={len(code)}")
    
    # 尝试使用 tree-sitter
    try:
        return _extract_functions_ts(code, language)
    except RuntimeError as e:
        # tree-sitter 不可用，回退到正则表达式
        log_warning(f"Tree-sitter 不可用，回退到正则表达式提取: {e}")
        return _extract_functions_regex_fallback(code, language)
    except Exception as e:
        # 其他错误也回退
        log_warning(f"Tree-sitter 提取失败，回退到正则表达式: {e}")
        return _extract_functions_regex_fallback(code, language)


def _extract_functions_regex_fallback(code: str, language: str = "c") -> List[Dict]:
    """使用正则表达式提取函数（回退方案）"""
    import re
    
    functions = []
    lines = code.split('\n')
    
    # C/C++ 函数定义的正则模式
    # 匹配：返回类型 函数名(参数) {
    pattern = r'^\s*((?:static\s+)?(?:inline\s+)?(?:extern\s+)?(?:const\s+)?[\w\s\*]+)\s+(\w+)\s*\((.*?)\)\s*\{'
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 跳过注释和预处理指令
        if line.strip().startswith('//') or line.strip().startswith('#'):
            i += 1
            continue
        
        # 尝试匹配函数定义（可能跨多行）
        # 先尝试单行匹配
        match = re.match(pattern, line)
        
        if not match and i + 1 < len(lines):
            # 尝试跨行匹配（函数定义可能在多行）
            combined_line = line + ' ' + lines[i + 1]
            match = re.match(pattern, combined_line)
            if match:
                i += 1  # 跳过下一行
        
        if match:
            return_type = match.group(1).strip()
            func_name = match.group(2)
            params = match.group(3).strip()
            
            # 过滤掉非函数的关键字
            if any(kw in return_type for kw in ['struct', 'enum', 'union', 'typedef', 'class']):
                i += 1
                continue
            
            # 查找函数体结束位置
            start_line = i + 1  # 行号从1开始
            brace_count = 1
            end_line = start_line
            
            j = i + 1
            while j < len(lines) and brace_count > 0:
                brace_count += lines[j].count('{') - lines[j].count('}')
                if brace_count == 0:
                    end_line = j + 1
                    break
                j += 1
            
            # 提取函数体
            if end_line > start_line:
                body_lines = lines[i:j+1]
                body = '\n'.join(body_lines)
            else:
                body = line
            
            functions.append({
                "name": func_name,
                "start_line": start_line,
                "end_line": end_line,
                "code": body,
                "return_type": return_type,
                "parameters": params
            })
        
        i += 1
    
    log_debug(f"[正则表达式回退] 提取到 {len(functions)} 个函数")
    return functions

# 自动识别文件编码并读取内容
def read_file_with_encoding(filepath):
    if not _CHARDET_AVAILABLE:
        raise ImportError("chardet 未安装，无法自动识别编码")
    with open(filepath, 'rb') as f:
        raw = f.read()
    result = chardet.detect(raw)
    encoding = result['encoding'] or 'utf-8'
    try:
        return raw.decode(encoding), encoding
    except Exception:
        return raw.decode('utf-8', errors='ignore'), 'utf-8'
