"""
C/C++ Function Parser
"""
import re
from typing import List, Dict
import os

def log_debug(msg):
    try:
        # Path is relative to this file's location (.../parser)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # Navigate 6 levels up from 'parser' to 'backend'
        backend_dir = os.path.abspath(os.path.join(base_dir, '..', '..', '..', '..', '..', '..'))
        log_dir = os.path.join(backend_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, 'bg_debug.txt')
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("[function_parser] " + msg + "\n")
    except Exception:
        # Suppress logging errors if path resolution or writing fails
        pass

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
    """只用tree-sitter提取所有C/C++函数，不再回退正则。"""
    log_debug(f"extract_functions_from_code called, language={language}, code_len={len(code)}")
    return _extract_functions_ts(code, language)

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
