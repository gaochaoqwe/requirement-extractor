from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple, Any

import re


@dataclass
class SnippetLocation:
    file_path: str
    start_line: int
    end_line: int


def _normalize_line(s: str) -> str:
    return ''.join((s or '').split())


def _normalize_lines(text: str) -> List[str]:
    lines = (text or '').replace('\r\n', '\n').replace('\r', '\n').split('\n')
    # 去掉全空行（但保留相对顺序）
    return [_normalize_line(ln) for ln in lines if _normalize_line(ln)]


def locate_snippet_in_repo(
    repo_root: str,
    snippet: str,
    exts: Optional[List[str]] = None,
    logger: Optional[Any] = None,
) -> Optional[SnippetLocation]:
    """在解压后的repo中定位代码片段所在文件与行号（MVP：按去空白后的逐行匹配）。"""

    root = Path(repo_root)
    if not root.exists() or not root.is_dir():
        return None

    target_lines = _normalize_lines(snippet)
    if not target_lines:
        if logger:
            logger.warning('code_locator: snippet 归一化后为空，无法定位')
        return None

    # 默认搜索 C/C++ 常见扩展名
    if not exts:
        exts = ['.c', '.h', '.cpp', '.hpp', '.cc', '.cxx', '.hh', '.ino']

    # 控制文件大小：跳过超大文件避免卡顿
    max_bytes = 5 * 1024 * 1024

    scanned_files = 0
    scanned_lines_total = 0
    best_candidate: Optional[Tuple[str, int, int, str]] = None  # (file, start_line, matched_lines, first_line)

    for p in root.rglob('*'):
        if not p.is_file():
            continue
        if p.suffix.lower() not in exts:
            continue
        try:
            if p.stat().st_size > max_bytes:
                continue
        except Exception:
            continue

        try:
            content = p.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue

        scanned_files += 1

        raw_lines = content.replace('\r\n', '\n').replace('\r', '\n').split('\n')
        # 与 snippet 侧保持一致：忽略空行（归一化后为空的行）
        # 同时保留 filtered->raw 行号映射，便于返回准确行号范围
        filtered: List[Tuple[int, str, str]] = []  # (raw_line_no(1-based), norm_line, raw_line)
        for idx, ln in enumerate(raw_lines):
            norm = _normalize_line(ln)
            if not norm:
                continue
            filtered.append((idx + 1, norm, ln))

        scanned_lines_total += len(filtered)

        # 滑窗匹配（基于 filtered 序列）
        n = len(filtered)
        m = len(target_lines)
        if m > n:
            continue

        for i in range(0, n - m + 1):
            if filtered[i][1] != target_lines[0]:
                continue
            ok = True
            for j in range(1, m):
                if filtered[i + j][1] != target_lines[j]:
                    ok = False
                    break
            if ok:
                start_raw = filtered[i][0]
                end_raw = filtered[i + m - 1][0]
                return SnippetLocation(
                    file_path=str(p),
                    start_line=start_raw,
                    end_line=end_raw,
                )

            # 记录最接近候选：以“从第一行开始连续相等的行数”为评分
            matched = 1
            for j in range(1, m):
                if filtered[i + j][1] == target_lines[j]:
                    matched += 1
                else:
                    break
            if matched > 0:
                first_line = filtered[i][2].strip() if 0 <= i < len(filtered) else ''
                if not best_candidate or matched > best_candidate[2]:
                    best_candidate = (str(p), filtered[i][0], matched, first_line)

    if logger:
        logger.warning(
            'code_locator: 未找到完全匹配；repo_root=%s, exts=%s, snippet_lines=%d, scanned_files=%d, scanned_lines_total=%d',
            str(root),
            ','.join(exts or []),
            len(target_lines),
            scanned_files,
            scanned_lines_total,
        )
        logger.warning(
            'code_locator: snippet_first_norm_line=%s',
            target_lines[0] if target_lines else '',
        )
        if best_candidate:
            logger.warning(
                'code_locator: best_candidate file=%s start_line=%d matched_lines=%d first_raw_line=%s',
                best_candidate[0],
                best_candidate[1],
                best_candidate[2],
                best_candidate[3],
            )

    return None


def guess_function_name_from_snippet(snippet: str) -> str:
    """粗略从代码片段猜测函数名（优先识别形如 'xxx(...)' 的定义行）。"""

    text = (snippet or '').replace('\r\n', '\n').replace('\r', '\n')
    for line in text.split('\n'):
        s = line.strip()
        if not s:
            continue
        if '(' in s and ')' in s and '{' in s:
            # 取最后一个标识符 + '('
            left = s.split('(')[0].strip()
            parts = left.replace('*', ' ').split()
            if parts:
                cand = parts[-1].strip()
                if cand and cand not in {'if', 'for', 'while', 'switch'}:
                    return cand
    return ''


def extract_call_line_for_test_item(test_item_name: str, snippet: str) -> str:
    """从入口函数代码片段里提取与测试项名称相关的调用语句（例如 RS422_Init();）。

    MVP：
    - 取测试项名称中“初始化”前的核心token（字母数字下划线连续段）
    - 在 snippet 中找包含该 token 且包含 '(' ')' ';' 的行
    """

    name = (test_item_name or '').strip()
    if not name:
        return ''

    core = name
    if '初始化' in core:
        core = core.split('初始化')[0]
    core = core.strip('"\' ').strip()

    # 只保留常见标识符字符
    import re

    m = re.search(r'[A-Za-z_][A-Za-z0-9_]*|[0-9A-Za-z_]+', core)
    token = m.group(0) if m else core
    token = token.strip()
    if not token:
        return ''

    lines = (snippet or '').replace('\r\n', '\n').replace('\r', '\n').split('\n')
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if token in s and '(' in s and ')' in s and ';' in s:
            return s
    return ''


def _extract_func_name_from_signature(signature_text: str) -> str:
    s = (signature_text or '').strip()
    if not s:
        return ''

    # 去掉可能的宏/属性等干扰
    s = re.sub(r'__attribute__\s*\(\([^)]*\)\)', ' ', s)
    s = re.sub(r'\s+', ' ', s)

    m = re.findall(r'([A-Za-z_][A-Za-z0-9_]*)\s*\(', s)
    if not m:
        return ''
    cand = m[-1]
    if cand in {'if', 'for', 'while', 'switch', 'return', 'sizeof'}:
        return ''
    return cand


def find_enclosing_function_in_file(file_path: str, line_no: int) -> Tuple[str, int, int, str]:
    """根据文件路径与行号粗略解析所在函数名、函数起止行，以及函数源码上下文。

    - line_no: 1-based
    返回: (func_name, func_start_line, func_end_line, context_text)
    """

    p = Path(file_path)
    if not p.exists() or not p.is_file():
        return ('', 0, 0, '')

    try:
        raw = p.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return ('', 0, 0, '')

    lines = raw.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    if not lines:
        return ('', 0, 0, '')

    idx = max(0, min(len(lines) - 1, int(line_no) - 1))

    # 1) 向上找函数签名（允许签名跨多行）。注意：很多C代码风格是签名与"{"分行，
    # 因此这里允许“签名在上方、{ 在后续几行”。
    sig_start = None
    sig_end = None
    signature_buf: List[str] = []
    max_back = 80
    for j in range(idx, max(-1, idx - max_back), -1):
        ln = lines[j]
        if ln.strip().startswith('//'):
            continue
        signature_buf.insert(0, ln)
        joined = ' '.join(signature_buf)

        # 先判断是否像函数签名（含括号、且不像声明结尾“;”）
        looks_like_sig = ('(' in joined and ')' in joined and ';' not in joined)
        if looks_like_sig:
            # 向下窥视几行，看是否出现“{”来确认是定义而不是声明
            lookahead = ' '.join(lines[j : min(len(lines), j + 6)])
            if '{' in lookahead:
                # 简单排除结构体/枚举等
                if re.search(r'\b(struct|enum|union)\b', joined):
                    continue
                name = _extract_func_name_from_signature(joined)
                if name:
                    sig_start = j + 1
                    sig_end = j + 1
                    break
        # 遇到明显的函数边界就停止
        if ln.strip().endswith('}'):
            signature_buf = []

    if not sig_start:
        return ('', 0, 0, '')

    func_name = _extract_func_name_from_signature(' '.join(signature_buf))

    # 2) 从签名开始向下做大括号配对，找函数结束行
    brace = 0
    started = False
    end_line = sig_start
    for k in range(sig_start - 1, len(lines)):
        ln = lines[k]
        # 粗略计数（忽略字符串/注释的精确处理，MVP 足够用）
        for ch in ln:
            if ch == '{':
                brace += 1
                started = True
            elif ch == '}':
                brace -= 1
        if started and brace <= 0:
            end_line = k + 1
            break

    # 3) 上下文：函数签名到函数结束，最多截断到 200 行
    ctx_max_lines = 200
    ctx_lines = lines[sig_start - 1 : min(len(lines), sig_start - 1 + ctx_max_lines)]
    context_text = '\n'.join(ctx_lines)
    return (func_name, sig_start, end_line, context_text)


def find_instrumentation_anchor_in_function(
    file_path: str,
    func_start_line: int,
    func_end_line: int,
) -> Tuple[int, str]:
    """在函数范围内寻找一个适合插桩的位置：优先挑选“if (...) { return IR_FAULT_*; }”里的 if 行。

    返回 (instrument_line, anchor_line_text)
    - instrument_line: 1-based
    - anchor_line_text: 对应行的原始文本（trim 后）
    """

    p = Path(file_path)
    if not p.exists() or not p.is_file():
        return (0, '')

    try:
        raw = p.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return (0, '')

    lines = raw.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    if not lines:
        return (0, '')

    start = max(1, int(func_start_line) or 1)
    end = max(start, int(func_end_line) or start)
    start_idx = max(0, min(len(lines) - 1, start - 1))
    end_idx = max(0, min(len(lines) - 1, end - 1))

    # 1) 优先：if 行附近(向下 6 行)存在 return IR_FAULT_*
    for i in range(start_idx, end_idx + 1):
        s = (lines[i] or '').strip()
        if not s:
            continue
        if not s.startswith('if'):
            continue
        window_end = min(end_idx, i + 6)
        for j in range(i, window_end + 1):
            t = (lines[j] or '').strip()
            if 'return' in t and 'IR_FAULT_' in t:
                return (i + 1, s)

    # 2) 退化：直接找第一条 return IR_FAULT_* 并向上回溯最近 if
    for i in range(start_idx, end_idx + 1):
        s = (lines[i] or '').strip()
        if 'return' in s and 'IR_FAULT_' in s:
            back = max(start_idx, i - 10)
            for k in range(i, back - 1, -1):
                a = (lines[k] or '').strip()
                if a.startswith('if'):
                    return (k + 1, a)
            return (i + 1, s)

    return (0, '')
