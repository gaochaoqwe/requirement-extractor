import glob
import os
import re
from typing import Dict, List, Tuple


_ALLOWED_CODE_EXTENSIONS = [
    ".c",
    ".cc",
    ".cpp",
    ".cxx",
    ".h",
    ".hh",
    ".hpp",
    ".hxx",
]


def _index_to_line_col(s: str, idx: int) -> Tuple[int, int]:
    line = s.count("\n", 0, idx) + 1
    last_nl = s.rfind("\n", 0, idx)
    col = idx + 1 if last_nl < 0 else idx - last_nl
    return line, col


def _extract_functions_from_code(code: str) -> List[Dict]:
    text = code or ""

    # 覆盖常见形式：
    # - void Image::flipVertical() {
    # - Image::Image(...) {
    # - static int foo(int a) {
    # - inline auto Bar::baz() const {
    # 不追求 100% C++ 语法，只保证回归测试用例可稳定提取。
    head = r"(?:[~\w:<>&*\s]+?)"
    name = r"(?P<name>[~\w:]+)"
    args = r"\([^;{}]*\)"
    tail = r"(?:\s*const)?\s*(?:noexcept\s*)?(?:->\s*[^\{;]+)?\s*\{"
    pattern = re.compile(rf"(^|\n)\s*(?:{head}\s+)?{name}\s*{args}{tail}", re.MULTILINE)

    functions: List[Dict] = []
    seen = set()

    for m in pattern.finditer(text):
        fn = (m.group("name") or "").strip()
        if not fn:
            continue
        # 排除控制语句/宏等
        if fn in {"if", "for", "while", "switch", "catch"}:
            continue

        brace_open_idx = text.find("{", m.end() - 1)
        if brace_open_idx < 0:
            continue

        depth = 0
        i = brace_open_idx
        n = len(text)
        while i < n:
            ch = text[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end_idx = i + 1
                    break
            i += 1
        else:
            continue

        start_line, _ = _index_to_line_col(text, brace_open_idx)
        end_line, _ = _index_to_line_col(text, end_idx)

        uniq = (fn, start_line)
        if uniq in seen:
            continue
        seen.add(uniq)

        functions.append(
            {
                "function_name": fn,
                "start_line": start_line,
                "end_line": end_line,
                "source_code": text[m.start() + (0 if m.group(1) == "" else 1) : end_idx],
            }
        )

    return functions


def scan_all_c_cpp_functions(extract_path: str) -> List[Dict]:
    all_functions: List[Dict] = []

    def _normalize_rel_path(p: str) -> str:
        s = str(p or "")
        s = s.replace("\\", "/")
        # 统一去掉相对路径前缀
        if s.startswith("./"):
            s = s[2:]

        # 约定：无论用户把版本根目录命名为 old/new/源代码/新代码/1.00/1.01...
        # 只要是“第一级目录”，一律忽略，用其后的相对路径做配对 key。
        # 例：
        # - old/core/image.cpp -> core/image.cpp
        # - 源代码/core/image.cpp -> core/image.cpp
        # - 1.00/core/image.cpp -> core/image.cpp
        parts = [x for x in s.split("/") if x not in ("", ".")]
        if len(parts) >= 2:
            s = "/".join(parts[1:])
        else:
            s = "/".join(parts)
        return s

    for ext in _ALLOWED_CODE_EXTENSIONS:
        files = glob.glob(f"{extract_path}/**/*{ext}", recursive=True)
        files.sort()

        for abs_path in files:
            try:
                with open(abs_path, "rb") as f:
                    raw = f.read()
                # 简化：优先 utf-8，不可解码则忽略非法字符
                code = raw.decode("utf-8", errors="ignore")
                if not code:
                    continue

                try:
                    rel_path = os.path.relpath(abs_path, extract_path)
                except Exception:
                    rel_path = abs_path

                rel_path = _normalize_rel_path(rel_path)

                for func in _extract_functions_from_code(code):
                    func_name = func.get("function_name")
                    if not func_name:
                        continue
                    all_functions.append(
                        {
                            "function_name": func_name,
                            "source_code": func.get("source_code") or "",
                            "file_path": rel_path,
                            "start_line": func.get("start_line"),
                            "end_line": func.get("end_line"),
                        }
                    )
            except Exception:
                continue

    return all_functions
