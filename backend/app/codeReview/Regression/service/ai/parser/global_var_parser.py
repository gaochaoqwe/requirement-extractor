"""
Global Variable Parser for C/C++ source files.

Returns a list of dictionaries, each with:
    name  : variable identifier
    code  : full declaration / definition line(s)
    line  : 1-based line number of the declaration

NOTE: • First tries tree-sitter if available.
      • Falls back to a simple regex which handles most single-line global
        declarations like `int g_count = 0;`, `static char *msg;` etc.
"""
from typing import List, Dict
import re
import os

# --- Centralized Logging Setup ---
LOG_FILE_PATH = None
try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    # Navigate 6 levels up from 'parser' to 'backend'
    BACKEND_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', '..', '..', '..', '..', '..'))
    LOG_DIR = os.path.join(BACKEND_DIR, 'logs')
    LOG_FILE_PATH = os.path.join(LOG_DIR, 'bg_debug.txt')
    os.makedirs(LOG_DIR, exist_ok=True)
except Exception:
    LOG_FILE_PATH = None # Disable logging if path fails

def log_debug(msg: str):
    """Helper to write to a central debug log."""
    if not LOG_FILE_PATH:
        return # Logging is disabled
    try:
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(f"[global_var_parser] {msg}\n")
    except Exception:
        pass # Suppress logging errors

# --- Tree-sitter Imports ---
try:
    from tree_sitter import Parser
    from .ts_loader import get_language, TS_AVAILABLE as _TS_AVAILABLE
except ImportError as e:
    log_debug(f"CRITICAL: Failed to import tree-sitter components. Error: {e}")
    _TS_AVAILABLE = False

__all__ = ["extract_globals_from_code"]

def _find_identifier(node):
    """递归查找声明中的标识符节点"""
    if node.type == "identifier":
        return node
    for child in node.children:
        if result := _find_identifier(child):
            return result
    return None

def _ts_extract_globals(code: str, language: str = "c") -> List[Dict]:
    if not _TS_AVAILABLE:
        log_debug("tree-sitter not available, skipping.")
        return []

    # Encode to bytes for parser, decode for source slicing
    code_bytes = code.encode('utf-8')

    # Helper to get source from node, correctly handling utf-8
    def _src(node):
        return code_bytes[node.start_byte:node.end_byte].decode('utf-8', errors='ignore')

    try:
        lang = "cpp" if language == "cpp" else "c"
        log_debug(f"Using {lang} parser")
        lang_obj = get_language(lang)
        parser = Parser()
        parser.set_language(lang_obj)
        tree = parser.parse(code_bytes)
        root = tree.root_node
        log_debug(f"Root node type: {root.type}")

        # Query for top-level declarations
        query_str = "(translation_unit (declaration) @decl)"
        query = lang_obj.query(query_str)
        
        globals_ = []
        seen_vars = set()

        captures = query.captures(root)
        log_debug(f"Found {len(captures)} declaration captures.")

        for node, tag in captures:
            # Skip function definitions. A function definition has a `compound_statement` (body)
            if node.child_by_field_name('body'):
                continue

            # A more robust check for function declarators vs. variable declarators
            # We are looking for declarations that are not function prototypes.
            # A function prototype will have a 'function_declarator' but no 'compound_statement' (body).
            is_function_prototype = False
            for child in node.children:
                if child.type == 'function_declarator':
                    is_function_prototype = True
                    break
            
            if is_function_prototype:
                continue

            decl_text = _src(node)
            
            # Iterate through declarators to handle `int a, b;`
            for declarator in node.children:
                if 'declarator' in declarator.type:
                    ident_node = _find_identifier(declarator)
                    if ident_node:
                        var_name = _src(ident_node)
                        if var_name and var_name not in seen_vars:
                            seen_vars.add(var_name)
                            globals_.append({
                                'name': var_name,
                                'code': decl_text.strip(),
                                'line': node.start_point[0] + 1,
                            })

        log_debug(f"Found {len(globals_)} global variables via tree-sitter.")
        for g in globals_:
            log_debug(f"  - Found: {g['name']} at line {g['line']}")
            
        return globals_
    except Exception as e:
        log_debug(f"tree-sitter error: {e}")
        import traceback
        log_debug(traceback.format_exc())
        return []

def _regex_extract_globals(code: str) -> List[Dict]:
    """Simple fallback regex: matches single-line global declarations."""
    results: List[Dict] = []
    code_no_comment = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    code_no_comment = re.sub(r'//.*', '', code_no_comment)
    lines = code_no_comment.splitlines()
    in_func = False
    brace_depth = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        # 跳过空行
        if not stripped:
            continue
        # 跳过函数体（通过大括号深度判断）
        brace_depth += line.count('{') - line.count('}')
        if brace_depth > 0:
            continue
        # 只在顶层（brace_depth==0）匹配变量定义
        m = re.match(r'^(?:static|extern)?\s*[\w\*\s]+\s+([A-Za-z_]\w*)\s*(?:=[^;]*)?;', stripped)
        if m:
            var_name = m.group(1)
            results.append({
                "name": var_name,
                "code": stripped,
                "line": i + 1
            })
    return results

def extract_globals_from_code(code: str, language: str = "c") -> List[Dict]:
    """Extract global variables from code using tree-sitter if available, else regex."""
    # 优先使用 tree-sitter
    globals_ = _ts_extract_globals(code, language)
    if globals_:
        return globals_
    # 如果 tree-sitter 不可用或解析失败，回退到正则
    return _regex_extract_globals(code)
