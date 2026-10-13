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
from typing import List, Dict, Any
import re
import os

# 导入统一的日志系统
from ....utils.logger import log_debug

# --- Tree-sitter Imports ---
try:
    from tree_sitter import Parser
    from .ts_loader import get_language, TS_AVAILABLE as _TS_AVAILABLE
except ImportError as e:
    log_debug(f"CRITICAL: Failed to import tree-sitter components. Error: {e}")
    _TS_AVAILABLE = False

__all__ = ["extract_globals_from_code", "extract_macros_from_code", "extract_arrays_from_code", "detect_actual_global_usage"]

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

        globals_ = []
        seen_vars = set()

        # 直接遍历translation_unit的子节点，查找声明
        def extract_from_node(node):
            if node.type == "declaration":
                # 跳过函数声明（函数原型）
                is_function_decl = False
                for child in node.children:
                    if child.type == 'function_declarator':
                        is_function_decl = True
                        break
                
                if is_function_decl:
                    log_debug(f"Skipping function declaration: {_src(node).strip()}")
                    return
                
                decl_text = _src(node).strip()
                log_debug(f"Processing declaration: {decl_text}")
                
                # 查找所有变量标识符
                def find_identifiers(n):
                    identifiers = []
                    if n.type == "identifier":
                        # 确保这个identifier是变量名，不是类型名
                        parent = n.parent
                        if parent and parent.type in ["init_declarator", "declarator", "array_declarator"]:
                            identifiers.append(n)
                    else:
                        for child in n.children:
                            identifiers.extend(find_identifiers(child))
                    return identifiers
                
                identifiers = find_identifiers(node)
                for ident_node in identifiers:
                    var_name = _src(ident_node)
                    if var_name and var_name not in seen_vars:
                        seen_vars.add(var_name)
                        globals_.append({
                            'name': var_name,
                            'code': decl_text,
                            'line': node.start_point[0] + 1,
                        })
                        log_debug(f"  - Found variable: {var_name}")
            
            # 递归处理子节点（但只在顶层处理）
            elif node.type == "translation_unit":
                for child in node.children:
                    extract_from_node(child)

        extract_from_node(root)

        log_debug(f"Found {len(globals_)} global variables via tree-sitter.")
        return globals_
    except Exception as e:
        log_debug(f"tree-sitter error: {e}")
        import traceback
        log_debug(traceback.format_exc())
        return []

def _regex_extract_globals(code: str) -> List[Dict]:
    """Improved fallback regex: matches global variable declarations."""
    results: List[Dict] = []
    
    # 移除注释
    code_no_comment = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    code_no_comment = re.sub(r'//.*$', '', code_no_comment, flags=re.MULTILINE)
    
    lines = code_no_comment.splitlines()
    brace_depth = 0
    paren_depth = 0
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
            
        # 跟踪大括号和圆括号深度
        brace_depth += line.count('{') - line.count('}')
        paren_depth += line.count('(') - line.count(')')
        
        # 只在顶层（brace_depth==0）处理
        if brace_depth > 0:
            continue
            
        # 跳过预处理指令
        if stripped.startswith('#'):
            continue
            
        # 跳过函数声明/定义（包含括号的行）
        if '(' in stripped and ')' in stripped and not stripped.endswith(';'):
            continue
            
        # 改进的全局变量匹配模式
        patterns = [
            # 基本类型：int var = value; static int var; extern int var;
            r'^(?:static\s+|extern\s+|const\s+|volatile\s+)*(?:unsigned\s+|signed\s+)?(?:int|char|short|long|float|double|bool|void|size_t|uint32_t|int32_t)\s*\*?\s*([a-zA-Z_]\w*)\s*(?:\[[^\]]*\])?\s*(?:=\s*[^;]+)?\s*;',
            
            # 复合类型：struct Type var; union Type var; enum Type var;
            r'^(?:static\s+|extern\s+|const\s+|volatile\s+)*(?:struct|union|enum)\s+\w+\s*\*?\s*([a-zA-Z_]\w*)\s*(?:\[[^\]]*\])?\s*(?:=\s*[^;]+)?\s*;',
            
            # 匿名结构体：struct { ... } var;
            r'^(?:static\s+|extern\s+|const\s+|volatile\s+)*(?:struct|union)\s*\{[^}]*\}\s*([a-zA-Z_]\w*)\s*(?:=\s*[^;]+)?\s*;',
            
            # typedef类型：MyType var;
            r'^(?:static\s+|extern\s+|const\s+|volatile\s+)*[A-Z]\w*\s+([a-zA-Z_]\w*)\s*(?:\[[^\]]*\])?\s*(?:=\s*[^;]+)?\s*;',
            
            # 函数指针：int (*func_ptr)(int); 
            r'^(?:static\s+|extern\s+|const\s+|volatile\s+)*\w+\s*\(\s*\*\s*([a-zA-Z_]\w*)\s*\)\s*\([^)]*\)\s*(?:=\s*[^;]+)?\s*;',
        ]
        
        for pattern in patterns:
            match = re.match(pattern, stripped)
            if match:
                var_name = match.group(1)
                # 避免匹配到类型名或关键字
                if var_name not in ['int', 'char', 'float', 'double', 'void', 'bool', 'short', 'long']:
                    results.append({
                        "name": var_name,
                        "code": stripped,
                        "line": i + 1
                    })
                break
    
    return results

def extract_globals_from_code(code: str, language: str = "c") -> List[Dict]:
    """Extract global variables from code using tree-sitter if available, else regex."""
    # 优先使用 tree-sitter
    globals_ = _ts_extract_globals(code, language)
    if globals_:
        return globals_
    # 如果 tree-sitter 不可用或解析失败，回退到正则
    return _regex_extract_globals(code)


def _ts_extract_macros(code: str, language: str = "c") -> List[Dict]:
    """使用 tree-sitter 提取宏定义"""
    if not _TS_AVAILABLE:
        log_debug("tree-sitter not available for macro extraction")
        return []

    code_bytes = code.encode('utf-8')
    
    try:
        lang = "cpp" if language == "cpp" else "c"
        lang_obj = get_language(lang)
        if not lang_obj:
            log_debug(f"Language '{lang}' not available for tree-sitter.")
            return []
        
        parser = Parser()
        parser.set_language(lang_obj)
        tree = parser.parse(code_bytes)
        root = tree.root_node
        
        macros = []
        seen_macros = set()
        
        def extract_macros_from_node(node):
            if node.type == "preproc_def":
                # 获取宏定义的完整文本
                macro_text = code_bytes[node.start_byte:node.end_byte].decode('utf-8', errors='ignore').strip()
                
                # 查找宏名称
                name_node = node.child_by_field_name('name')
                if name_node:
                    macro_name = code_bytes[name_node.start_byte:name_node.end_byte].decode('utf-8')
                    if macro_name and macro_name not in seen_macros:
                        seen_macros.add(macro_name)
                        macros.append({
                            'name': macro_name,
                            'code': macro_text,
                            'line': node.start_point[0] + 1,
                            'type': 'macro'
                        })
                        log_debug(f"Found macro: {macro_name}")
            
            # 递归处理子节点
            for child in node.children:
                extract_macros_from_node(child)
        
        extract_macros_from_node(root)
        log_debug(f"Found {len(macros)} macros via tree-sitter")
        return macros
        
    except Exception as e:
        log_debug(f"tree-sitter macro extraction error: {e}")
        import traceback
        log_debug(traceback.format_exc())
        return []


def _regex_extract_macros(code: str) -> List[Dict]:
    """使用正则表达式提取宏定义（回退方案）"""
    macros = []
    seen_macros = set()
    
    # 移除多行注释
    code_no_multiline_comments = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    
    lines = code_no_multiline_comments.splitlines()
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # 移除单行注释
        if '//' in line:
            line = line[:line.index('//')]
        
        if not line:
            i += 1
            continue
        
        # 匹配 #define 宏定义
        if line.startswith('#define'):
            macro_lines = [lines[i]]
            original_line_num = i + 1
            
            # 处理多行宏定义（以反斜杠结尾）
            while i < len(lines) - 1 and lines[i].rstrip().endswith('\\'):
                i += 1
                macro_lines.append(lines[i])
            
            full_macro = '\n'.join(macro_lines)
            
            # 提取宏名称
            match = re.match(r'#define\s+([a-zA-Z_]\w*)', line)
            if match:
                macro_name = match.group(1)
                if macro_name not in seen_macros:
                    seen_macros.add(macro_name)
                    macros.append({
                        'name': macro_name,
                        'code': full_macro,
                        'line': original_line_num,
                        'type': 'macro'
                    })
                    log_debug(f"Found macro (regex): {macro_name}")
        
        i += 1
    
    log_debug(f"Found {len(macros)} macros via regex")
    return macros


def extract_macros_from_code(code: str, language: str = "c") -> List[Dict]:
    """提取宏定义，优先使用tree-sitter，回退到正则表达式"""
    log_debug(f"extract_macros_from_code called, language={language}")
    
    # 优先使用 tree-sitter
    macros = _ts_extract_macros(code, language)
    if macros:
        return macros
    
    # 回退到正则表达式
    return _regex_extract_macros(code)


def _ts_extract_arrays(code: str, language: str = "c") -> List[Dict]:
    """使用 tree-sitter 提取数组变量声明"""
    if not _TS_AVAILABLE:
        log_debug("tree-sitter not available for array extraction")
        return []

    code_bytes = code.encode('utf-8')
    
    try:
        lang = "cpp" if language == "cpp" else "c"
        lang_obj = get_language(lang)
        if not lang_obj:
            log_debug(f"Language '{lang}' not available for tree-sitter.")
            return []
        
        parser = Parser()
        parser.set_language(lang_obj)
        tree = parser.parse(code_bytes)
        root = tree.root_node
        
        arrays = []
        seen_arrays = set()
        
        def extract_arrays_from_node(node):
            if node.type == "declaration":
                # 跳过函数声明
                is_function_decl = False
                for child in node.children:
                    if child.type == 'function_declarator':
                        is_function_decl = True
                        break
                
                if is_function_decl:
                    return
                
                decl_text = code_bytes[node.start_byte:node.end_byte].decode('utf-8', errors='ignore').strip()
                
                # 查找数组声明器
                def find_array_declarators(n):
                    array_info = []
                    if n.type == "array_declarator":
                        # 找到数组名称
                        declarator = n.child_by_field_name('declarator')
                        if declarator and declarator.type == 'identifier':
                            array_name = code_bytes[declarator.start_byte:declarator.end_byte].decode('utf-8')
                            array_info.append((array_name, n))
                    else:
                        for child in n.children:
                            array_info.extend(find_array_declarators(child))
                    return array_info
                
                array_declarators = find_array_declarators(node)
                for array_name, array_node in array_declarators:
                    if array_name and array_name not in seen_arrays:
                        seen_arrays.add(array_name)
                        arrays.append({
                            'name': array_name,
                            'code': decl_text,
                            'line': node.start_point[0] + 1,
                            'type': 'array'
                        })
                        log_debug(f"Found array: {array_name}")
            
            # 只在顶层处理
            elif node.type == "translation_unit":
                for child in node.children:
                    extract_arrays_from_node(child)
        
        extract_arrays_from_node(root)
        log_debug(f"Found {len(arrays)} arrays via tree-sitter")
        return arrays
        
    except Exception as e:
        log_debug(f"tree-sitter array extraction error: {e}")
        import traceback
        log_debug(traceback.format_exc())
        return []


def _regex_extract_arrays(code: str) -> List[Dict]:
    """使用正则表达式提取数组变量声明（回退方案）"""
    arrays = []
    seen_arrays = set()
    
    # 移除注释
    code_no_comment = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    code_no_comment = re.sub(r'//.*$', '', code_no_comment, flags=re.MULTILINE)
    
    lines = code_no_comment.splitlines()
    brace_depth = 0
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
            
        # 跟踪大括号深度，只在顶层处理
        brace_depth += line.count('{') - line.count('}')
        if brace_depth > 0:
            continue
            
        # 跳过预处理指令
        if stripped.startswith('#'):
            continue
            
        # 跳过函数声明/定义
        if '(' in stripped and ')' in stripped and not stripped.endswith(';'):
            continue
        
        # 数组声明的正则模式
        patterns = [
            # 基本数组：int arr[10]; static char buf[256]; extern float matrix[10][10];
            r'^(?:static\s+|extern\s+|const\s+|volatile\s+)*(?:unsigned\s+|signed\s+)?(?:int|char|short|long|float|double|bool|void|size_t|uint32_t|int32_t)\s*\*?\s*([a-zA-Z_]\w*)\s*(\[[^\]]*\](?:\s*\[[^\]]*\])*)\s*(?:=\s*[^;]+)?\s*;',
            
            # 结构体数组：struct Point points[100]; union Data data_array[50];
            r'^(?:static\s+|extern\s+|const\s+|volatile\s+)*(?:struct|union|enum)\s+\w+\s*\*?\s*([a-zA-Z_]\w*)\s*(\[[^\]]*\](?:\s*\[[^\]]*\])*)\s*(?:=\s*[^;]+)?\s*;',
            
            # typedef类型数组：MyType array[SIZE];
            r'^(?:static\s+|extern\s+|const\s+|volatile\s+)*[A-Z]\w*\s+([a-zA-Z_]\w*)\s*(\[[^\]]*\](?:\s*\[[^\]]*\])*)\s*(?:=\s*[^;]+)?\s*;',
        ]
        
        for pattern in patterns:
            match = re.match(pattern, stripped)
            if match:
                array_name = match.group(1)
                dimensions = match.group(2)
                if array_name and array_name not in seen_arrays:
                    seen_arrays.add(array_name)
                    arrays.append({
                        'name': array_name,
                        'code': stripped,
                        'line': i + 1,
                        'type': 'array'
                    })
                    log_debug(f"Found array (regex): {array_name} with dimensions {dimensions}")
                break
    
    log_debug(f"Found {len(arrays)} arrays via regex")
    return arrays


def extract_arrays_from_code(code: str, language: str = "c") -> List[Dict]:
    """提取数组变量声明，优先使用tree-sitter，回退到正则表达式"""
    log_debug(f"extract_arrays_from_code called, language={language}")
    
    # 优先使用 tree-sitter
    arrays = _ts_extract_arrays(code, language)
    if arrays:
        return arrays
    
    # 回退到正则表达式
    return _regex_extract_arrays(code)


# === 智能全局变量使用检测功能 ===

def extract_local_variable_names(function_code: str, language: str = "c") -> set:
    """
    从函数代码中提取局部变量名称
    
    Args:
        function_code: 函数源代码
        language: 编程语言 ("c" 或 "cpp")
    
    Returns:
        set: 局部变量名称集合
    """
    local_vars = set()
    
    # 移除注释
    code_no_comments = _remove_comments(function_code)
    
    # 移除字符串字面量，避免误匹配
    code_no_strings = re.sub(r'"[^"]*"', '""', code_no_comments)
    code_no_strings = re.sub(r"'[^']*'", "''", code_no_strings)
    
    # C/C++ 局部变量声明的常见模式
    patterns = [
        # 基本类型声明: int var, char buffer[size], float *ptr
        r'(?:^|[^a-zA-Z_])(?:const\s+|volatile\s+|static\s+|register\s+)*(?:unsigned\s+|signed\s+)?(?:int|char|short|long|float|double|bool|void|size_t|uint32_t|int32_t|uint16_t|int16_t|uint8_t|int8_t|ssize_t)\s*\*?\s*([a-zA-Z_]\w*)\s*(?:\[[^\]]*\])?\s*(?:[=,;]|$)',
        
        # struct/union/enum 声明: struct Point p; union Data d;
        r'(?:^|[^a-zA-Z_])(?:const\s+|volatile\s+|static\s+|register\s+)*(?:struct|union|enum)\s+\w+\s*\*?\s*([a-zA-Z_]\w*)\s*(?:\[[^\]]*\])?\s*(?:[=,;]|$)',
        
        # typedef 类型: MyType var; (只匹配以大写字母开头的类型名)
        r'(?:^|[^a-zA-Z_])(?:const\s+|volatile\s+|static\s+|register\s+)*([A-Z]\w*)\s+([a-zA-Z_]\w*)\s*(?:\[[^\]]*\])?\s*(?:[=,;]|$)',
        
        # for 循环中的变量声明
        r'for\s*\(\s*(?:int|char|short|long|float|double|size_t)\s+([a-zA-Z_]\w*)',
        
        # 函数参数（在函数签名中）
        r'(?:^|[^a-zA-Z_])(?:const\s+|volatile\s+)*(?:unsigned\s+|signed\s+)?(?:int|char|short|long|float|double|bool|void|size_t)\s*\*?\s*([a-zA-Z_]\w*)\s*(?:\[[^\]]*\])?\s*[,)]',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, code_no_strings, re.MULTILINE)
        for match in matches:
            # 提取变量名（通常在最后一个捕获组中）
            if match.groups():
                var_name = match.groups()[-1]
                if var_name and _is_valid_identifier(var_name):
                    # 排除C关键字和常见类型名
                    if var_name not in ['int', 'char', 'float', 'double', 'void', 'bool', 'short', 'long', 'const', 'volatile', 'static', 'register', 'unsigned', 'signed', 'size_t', 'ssize_t']:
                        local_vars.add(var_name)
    
    # 处理多变量声明：int a, b, c;
    multi_var_patterns = [
        r'(?:^|[^a-zA-Z_])(?:const\s+|volatile\s+|static\s+|register\s+)*(?:unsigned\s+|signed\s+)?(?:int|char|short|long|float|double|bool|void|size_t)\s*\*?\s*([a-zA-Z_]\w*(?:\s*,\s*\*?\s*[a-zA-Z_]\w*)*)\s*[;=]',
        r'(?:^|[^a-zA-Z_])(?:struct|union|enum)\s+\w+\s*\*?\s*([a-zA-Z_]\w*(?:\s*,\s*\*?\s*[a-zA-Z_]\w*)*)\s*[;=]'
    ]
    
    for pattern in multi_var_patterns:
        multi_matches = re.findall(pattern, code_no_strings, re.MULTILINE)
        for match in multi_matches:
            # 分割逗号分隔的变量名，处理指针
            var_names = re.findall(r'([a-zA-Z_]\w*)', match)
            for var_name in var_names:
                if var_name not in ['int', 'char', 'float', 'double', 'void', 'bool', 'short', 'long'] and _is_valid_identifier(var_name):
                    local_vars.add(var_name)
    
    return local_vars


def extract_local_macro_names(function_code: str) -> set:
    """
    从函数代码中提取局部宏定义名称（函数内部定义的宏）
    
    Args:
        function_code: 函数源代码
    
    Returns:
        set: 局部宏定义名称集合
    """
    local_macros = set()
    
    # 移除注释
    code_no_comments = _remove_comments(function_code)
    
    # 查找函数内部的 #define 语句
    lines = code_no_comments.splitlines()
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('#define'):
            match = re.match(r'#define\s+([a-zA-Z_]\w*)', stripped)
            if match:
                macro_name = match.group(1)
                if _is_valid_identifier(macro_name):
                    local_macros.add(macro_name)
    
    return local_macros


def detect_actual_global_usage(
    function_code: str, 
    global_var_map: Dict[str, Dict[str, Any]], 
    language: str = "c"
) -> List[str]:
    """
    智能检测函数中实际使用的全局变量、宏定义和数组变量
    
    Args:
        function_code: 函数源代码
        global_var_map: 全局变量映射字典，包含变量、宏和数组
        language: 编程语言
    
    Returns:
        List[str]: 实际使用的全局变量/宏/数组名称列表
    """
    if not global_var_map:
        return []
    
    # 1. 提取函数中声明的局部变量和宏
    local_vars = extract_local_variable_names(function_code, language)
    local_macros = extract_local_macro_names(function_code)
    
    # 2. 对每个全局项目，检查是否真正被使用
    actually_used_globals = []
    
    for global_name, global_info in global_var_map.items():
        global_type = global_info.get('type', 'variable')  # 默认为变量类型
        
        # 根据类型决定是否被局部定义遮蔽
        is_shadowed = False
        if global_type == 'macro':
            # 宏被局部宏遮蔽
            is_shadowed = global_name in local_macros
        else:
            # 变量和数组被局部变量遮蔽
            is_shadowed = global_name in local_vars
        
        if is_shadowed:
            continue
            
        # 检查全局项目是否在代码中被引用
        if _is_global_item_referenced(function_code, global_name, global_type):
            actually_used_globals.append(global_name)
    
    return actually_used_globals


def _is_global_item_referenced(function_code: str, item_name: str, item_type: str = 'variable') -> bool:
    """
    检查全局项目（变量、宏、数组）是否在函数代码中被引用
    
    Args:
        function_code: 函数源代码
        item_name: 项目名称
        item_type: 项目类型 ('variable', 'macro', 'array')
    
    Returns:
        bool: 是否被引用
    """
    # 使用词边界确保完整匹配变量名
    pattern = r'\b' + re.escape(item_name) + r'\b'
    
    # 移除注释
    code_no_comments = _remove_comments(function_code)
    
    # 查找所有匹配
    matches = list(re.finditer(pattern, code_no_comments))
    
    if not matches:
        return False
    
    # 进一步检查：排除在变量声明中的出现
    for match in matches:
        # 获取匹配位置的上下文
        start = max(0, match.start() - 50)
        end = min(len(code_no_comments), match.end() + 10)
        context = code_no_comments[start:end]
        
        # 检查是否是变量声明（简单的启发式规则）
        # 如果匹配前面有类型关键字，可能是声明
        before_match = code_no_comments[start:match.start()]
        
        # 常见的类型关键字
        type_keywords = [
            'int', 'char', 'short', 'long', 'float', 'double', 'bool', 'void',
            'unsigned', 'signed', 'struct', 'union', 'const', 'static', 'extern'
        ]
        
        # 检查是否是声明语句
        is_declaration = False
        for keyword in type_keywords:
            if re.search(r'\b' + keyword + r'\s+[^;]*$', before_match):
                is_declaration = True
                break
        
        # 对于宏，还要检查是否是 #define 语句
        if item_type == 'macro':
            # 检查是否在 #define 语句中
            line_start = code_no_comments.rfind('\n', 0, match.start()) + 1
            line_content = code_no_comments[line_start:match.end()]
            if line_content.strip().startswith('#define'):
                is_declaration = True
        
        # 如果不是声明，则认为是使用
        if not is_declaration:
            return True
    
    return False


def _remove_comments(code: str) -> str:
    """移除C/C++代码中的注释"""
    # 移除单行注释
    code = re.sub(r'//.*$', '', code, flags=re.MULTILINE)
    # 移除多行注释
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    return code


def _is_valid_identifier(name: str) -> bool:
    """检查是否是有效的C/C++标识符"""
    return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name))
