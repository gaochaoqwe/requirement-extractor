"""
函数依赖图构建器

使用tree-sitter解析C/C++代码，构建函数调用关系图。
"""
import os
import sys
import re
from pathlib import Path
from typing import Dict, Set, List, Optional, Any
from collections import defaultdict, deque
import traceback

from tree_sitter import Parser

from .ts_loader import TS_AVAILABLE, get_language

# Optional: re-use the chardet based reader from function_parser if available
try:
    from .function_parser import read_file_with_encoding as _read_file_with_encoding  # type: ignore
except Exception:
    _read_file_with_encoding = None  # Fallback defined below


# ---------------------------------------------------------------------------
# Logging helper – write to the same central debug file used by other parsers
# ---------------------------------------------------------------------------

LOG_FILE_PATH: Optional[str] = None
try:
    BASE_DIR = Path(__file__).resolve().parent  # .../parser
    BACKEND_DIR = BASE_DIR.parents[5]           # navigate up to /backend
    LOG_FILE_PATH = str(BACKEND_DIR / "logs" / "bg_debug.txt")
    Path(LOG_FILE_PATH).parent.mkdir(parents=True, exist_ok=True)
except Exception:
    LOG_FILE_PATH = None


def log_debug(msg: str) -> None:  # pragma: no cover – dev helper
    if not LOG_FILE_PATH:
        return
    try:
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as fp:
            fp.write(f"[all_graph_parser] {msg}\n")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Encoding-aware file loader fallback
# ---------------------------------------------------------------------------

def _default_read_file(fp: os.PathLike) -> str:
    """Read file with naive utf-8 fallback when chardet is unavailable."""
    try:
        with open(fp, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        with open(fp, "rb") as f:
            raw = f.read()
        try:
            import chardet  # local optional dep

            enc = chardet.detect(raw).get("encoding", "utf-8") or "utf-8"
            return raw.decode(enc, errors="ignore")
        except Exception:
            # last resort – ignore errors
            return raw.decode("utf-8", errors="ignore")


# Choose reader
_read_file = _read_file_with_encoding or _default_read_file


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def _node_text(node, code_bytes: bytes) -> str:
    return code_bytes[node.start_byte : node.end_byte].decode("utf-8", errors="ignore")


def _extract_function_name(node, code_bytes: bytes) -> Optional[str]:
    """Return the function name for a `function_definition` node."""
    if node.type != "function_definition":
        return None
    
    # Find the declarator -> direct_declarator -> identifier
    declarator = node.child_by_field_name("declarator")
    if not declarator:
        return None
    
    # Navigate through nested declarators to find the identifier
    current = declarator
    while current and current.type != "identifier":
        if current.type == "function_declarator":
            current = current.child_by_field_name("declarator")
        elif current.type == "pointer_declarator":
            current = current.child_by_field_name("declarator")
        elif current.type == "direct_declarator":
            # Look for identifier child
            for child in current.children:
                if child.type == "identifier":
                    current = child
                    break
            else:
                break
        else:
            break
    
    if current and current.type == "identifier":
        return _node_text(current, code_bytes)
    return None


def _extract_callee_name(callee_node, code_bytes: bytes) -> Optional[str]:
    """Return the identifier name of the callee inside a call_expression."""
    if callee_node is None:
        return None

    node = callee_node
    # Peel wrappers like field_expression / pointer_expression etc.
    while node is not None:
        if node.type in {"identifier", "field_identifier"}:
            return _node_text(node, code_bytes)

        # object.method() or ptr->method()
        if node.type in {"field_expression", "pointer_expression", "member_expression"}:
            field = node.child_by_field_name("field")
            if field and field.type in {"identifier", "field_identifier"}:
                return _node_text(field, code_bytes)
            # else descend into first child to keep searching
            node = field or (node.children[0] if node.children else None)
            continue

        # qualified_identifier e.g. ns::func – take last component
        if node.type in {"qualified_identifier", "scoped_identifier"}:
            name_node = node.child_by_field_name("name")
            if name_node:
                node = name_node
                continue
            # fallback – choose last child
            if node.children:
                node = node.children[-1]
                continue

        # generic fall-through – pick first child
        node = node.children[0] if node.children else None

    return None


# ---------------------------------------------------------------------------
# Public APIs
# ---------------------------------------------------------------------------

def parse_file(file_path: os.PathLike, *, language: str = "c") -> List[Dict]:
    """Parse *one* source file and return a list of function dicts.

    Each dict contains:
        name         – function identifier (str)
        source_code  – full function source (str)
        calls        – list[str] of function names invoked inside
        start_line   – 1-based start line
        end_line     – 1-based end line
        file_path    – absolute path to the source file
    """
    if not TS_AVAILABLE:
        raise RuntimeError("Tree-sitter languages are not available – cannot parse call graph.")

    code = _read_file(file_path)
    if isinstance(code, tuple):
        code = code[0]  # when using read_file_with_encoding, discard encoding

    code_bytes = code.encode("utf-8")

    lang = "cpp" if language.lower() in {"cpp", "c++"} else "c"
    parser = Parser()
    parser.set_language(get_language(lang))
    tree = parser.parse(code_bytes)
    root = tree.root_node

    # Traverse AST – collect function definitions
    functions: List[Dict] = []
    stack: List = [root]
    while stack:
        node = stack.pop()
        if node.type == "function_definition":
            func_name = _extract_function_name(node, code_bytes)
            if func_name:
                # Collect called functions within body
                body = node.child_by_field_name("body")
                called: Set[str] = set()
                if body is not None:
                    body_stack = [body]
                    while body_stack:
                        n = body_stack.pop()
                        if n.type == "call_expression":
                            callee_node = n.child_by_field_name("function")
                            callee_name = _extract_callee_name(callee_node, code_bytes)
                            if callee_name:
                                called.add(callee_name)
                        body_stack.extend(n.children)
                functions.append(
                    {
                        "name": func_name,
                        "source_code": _node_text(node, code_bytes),
                        "calls": list(called),
                        "start_line": node.start_point[0] + 1,
                        "end_line": node.end_point[0] + 1,
                        "file_path": str(Path(file_path).resolve()),
                    }
                )
        stack.extend(node.children)

    log_debug(f"Parsed {file_path} – found {len(functions)} functions")
    return functions


SUPPORTED_EXTS = {".c", ".h", ".cpp", ".hpp", ".cc", ".cxx"}


def build_project_call_graph(project_root: os.PathLike, *, language: str = "c") -> Dict[str, Dict]:
    """Walk *project_root* recursively and build a mapping `func_name -> info`.

    Later duplicates (same function name in another file) are ignored to keep
    mapping stable.  If you need full overload support, adapt as required.
    """
    root_path = Path(project_root).resolve()
    if not root_path.is_dir():
        raise ValueError(f"Project root '{project_root}' is not a directory")

    call_graph: Dict[str, Dict] = {}

    for file_path in root_path.rglob("*"):
        if file_path.suffix.lower() not in SUPPORTED_EXTS or not file_path.is_file():
            continue
        try:
            funcs = parse_file(file_path, language=language)
            for f in funcs:
                if f["name"] not in call_graph:
                    call_graph[f["name"]] = f
        except Exception as e:
            log_debug(f"Failed to parse {file_path}: {e}")

    log_debug(f"Project scan complete – indexed {len(call_graph)} functions under {root_path}")
    return call_graph


def collect_function_with_dependencies(
    entry_function: str,
    project_root: os.PathLike,
    *,
    language: str = "c",
    max_depth: int = 3,
) -> Dict[str, Dict]:
    """Return mapping of *entry_function* and all callees up to *max_depth*.

    Depth=1 → only direct callees; Depth=0 → just entry itself.
    """
    index = build_project_call_graph(project_root, language=language)
    if entry_function not in index:
        raise KeyError(f"Function '{entry_function}' not found in project index")

    collected: Dict[str, Dict] = {}
    visited: Set[str] = set()

    # BFS queue (func_name, depth)
    queue: List[tuple[str, int]] = [(entry_function, 0)]

    while queue:
        func_name, depth = queue.pop(0)
        if func_name in visited:
            continue
        visited.add(func_name)
        func_info = index.get(func_name)
        if not func_info:
            # Definition not present (could be external / stdlib)
            continue
        collected[func_name] = func_info
        if depth < max_depth:
            for callee in func_info.get("calls", []):
                if callee not in visited:
                    queue.append((callee, depth + 1))

    return collected


# ---------------------------------------------------------------------------
# Self-test helper (run via `python -m app...all_graph_parser`)
# ---------------------------------------------------------------------------

def _self_test():  # pragma: no cover – manual smoke test
    """Quick smoke test using the bundled `tests/small_test` fixtures."""
    here = Path(__file__).resolve()
    project_root = here.parents[7] / "backend" / "tests" / "small_test"
    if not project_root.exists():
        sys.stderr.write("[self-test] test project not found – skipping\n")
        return

    sys.stderr.write("[self-test] Building index …\n")

    # 构建索引
    deps = collect_function_with_dependencies("main", project_root, "c", max_depth=2)

    sys.stderr.write(f"[self-test] Collected functions: {list(deps)}\n")
    for name, info in deps.items():
        sys.stderr.write(f"\n=== {name} ({Path(info['file_path']).name}) ===\n{info['source_code'][:200]}…\n")


if __name__ == "__main__":
    _self_test() 