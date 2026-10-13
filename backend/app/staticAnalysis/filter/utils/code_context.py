"""
代码上下文提取工具

从 api.py 抽取，供代码视图展示与自动修复共用。
基于花括号栈自动截取"函数签名 + 问题行附近"的上下文。
"""


def build_function_aware_source_snippet(source_code: str, line_no: int, context: int = 3) -> str:
    if not source_code:
        return ''

    lines = source_code.splitlines()
    if line_no <= 0 or line_no > len(lines):
        return source_code[:2000]

    target_idx = line_no - 1

    def is_control_signature(text: str) -> bool:
        stripped = text.strip()
        control_prefixes = ('if ', 'if(', 'for ', 'for(', 'while ', 'while(', 'switch ', 'switch(', 'catch ', 'catch(', 'else', 'do ', 'do{')
        type_prefixes = ('struct ', 'enum ', 'union ', 'typedef ')
        return stripped.startswith(control_prefixes) or stripped.startswith(type_prefixes)

    brace_stack = []
    for idx, line in enumerate(lines[:target_idx + 1]):
        for char in line:
            if char == '{':
                brace_stack.append(idx)
            elif char == '}' and brace_stack:
                brace_stack.pop()

    def signature_start(open_idx: int) -> int:
        start = open_idx
        while start > 0:
            prev = lines[start - 1].strip()
            if not prev or prev.startswith('#') or prev.endswith(';') or prev.endswith('}') or prev.endswith('{'):
                break
            start -= 1
        return start

    function_open_idx = None
    function_sig_start = None
    for open_idx in reversed(brace_stack):
        sig_start = signature_start(open_idx)
        signature = ' '.join(line.strip() for line in lines[sig_start:open_idx + 1])
        if '(' in signature and ')' in signature and not is_control_signature(signature):
            function_open_idx = open_idx
            function_sig_start = sig_start
            break

    if function_open_idx is None:
        start = max(0, target_idx - context)
        end = min(len(lines) - 1, target_idx + context)
        snippet = []
        if start > 0:
            snippet.append('......')
        snippet.extend(lines[start:end + 1])
        if end < len(lines) - 1:
            snippet.append('......')
        return '\n'.join(snippet)

    depth = 0
    function_close_idx = len(lines) - 1
    for idx in range(function_open_idx, len(lines)):
        for char in lines[idx]:
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    function_close_idx = idx
                    break
        if depth == 0 and idx >= function_open_idx:
            break

    context_start = max(function_open_idx + 1, target_idx - context)
    context_end = min(function_close_idx - 1, target_idx + context)

    snippet = []
    snippet.extend(lines[function_sig_start:function_open_idx + 1])
    if context_start > function_open_idx + 1:
        snippet.append('......')
    if context_start <= context_end:
        snippet.extend(lines[context_start:context_end + 1])
    if context_end < function_close_idx - 1:
        snippet.append('......')
    if function_close_idx > function_open_idx:
        snippet.append(lines[function_close_idx])

    return '\n'.join(snippet)


def read_file_with_multiple_encodings(file_path: str, preferred: str = None):
    """
    多编码兜底读取文本文件。

    参照 codeReview/ConfigurationItem/api/endpoints/codemap.py:read_file_with_multiple_encodings。

    Returns:
        Tuple[Optional[str], str]: (文件内容, 实际命中的编码)
        读取失败时返回 (None, 'utf-8')
    """
    encodings = []
    if preferred:
        encodings.append(preferred)
    for enc in ('utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'gb18030', 'big5', 'latin-1'):
        if enc not in encodings:
            encodings.append(enc)

    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read(), encoding
        except (UnicodeDecodeError, LookupError):
            continue
        except Exception:
            break

    # 最后兜底：utf-8 + 替换非法字符
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read(), 'utf-8'
    except Exception:
        return None, 'utf-8'


def detect_encoding(file_path: str) -> str:
    """探测文件编码（不返回内容），用于写回时保持一致。"""
    _, encoding = read_file_with_multiple_encodings(file_path)
    return encoding or 'utf-8'
