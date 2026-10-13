import os
import difflib
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from ...db.models.file import AnalysisFile


def _get_extract_path(db: Session, task_id: int, version: str) -> str:
    v = (version or "").strip().lower()
    if v not in {"old", "new"}:
        raise ValueError("version只允许old或new")

    file_obj = (
        db.query(AnalysisFile)
        .filter(AnalysisFile.task_id == task_id, AnalysisFile.version == v)
        .first()
    )
    if not file_obj or not file_obj.extract_path:
        raise ValueError(f"task_id={task_id} 未找到 version={v} 的解压目录")

    extract_path = file_obj.extract_path
    if not os.path.exists(extract_path):
        raise ValueError(f"解压目录不存在: {extract_path}")

    return extract_path


def _is_safe_join(base: str, rel_path: str) -> Tuple[bool, str]:
    rel = (rel_path or "").lstrip("/\\")
    target = os.path.abspath(os.path.join(base, rel))
    base_abs = os.path.abspath(base)
    if os.path.commonpath([base_abs, target]) != base_abs:
        return False, target
    return True, target


def _read_text_file(path: str) -> str:
    encodings = ["utf-8", "gbk", "gb2312", "gb18030", "big5", "latin-1"]
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, LookupError):
            continue
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def _normalize_rel_path_for_match(p: str) -> str:
    s = str(p or "").replace("\\", "/")
    if s.startswith("./"):
        s = s[2:]
    parts = [x for x in s.split("/") if x not in ("", ".")]
    if len(parts) >= 2:
        return "/".join(parts[1:])
    return "/".join(parts)


def _resolve_file_abs_path(base: str, version: str, path: str) -> Optional[str]:
    candidates = []
    raw = (path or "").lstrip("/\\")
    if raw:
        candidates.append(raw)
    v = (version or "").strip().lower()
    if raw and v:
        candidates.append(f"{v}/{raw}")

    for rel in candidates:
        ok, abs_path = _is_safe_join(base, rel)
        if ok and os.path.exists(abs_path) and os.path.isfile(abs_path):
            return abs_path

    want = _normalize_rel_path_for_match(raw)
    if not want:
        return None
    base_abs = os.path.abspath(base)
    for cur_root, _, files in os.walk(base_abs):
        for fn in files:
            abs_path = os.path.abspath(os.path.join(cur_root, fn))
            try:
                rel = os.path.relpath(abs_path, base_abs)
            except Exception:
                continue
            if _normalize_rel_path_for_match(rel) == want:
                return abs_path
    return None


def build_file_tree(db: Session, task_id: int, version: str) -> Dict[str, Any]:
    base = _get_extract_path(db, task_id, version)

    def make_node(name: str, path: str, node_type: str) -> Dict[str, Any]:
        return {
            "name": name,
            "path": path.replace("\\", "/"),
            "type": node_type,
            "children": [],
        }

    root = make_node(name=version, path="", node_type="dir")
    node_map: Dict[str, Dict[str, Any]] = {"": root}

    for cur_root, dirs, files in os.walk(base):
        rel_dir = os.path.relpath(cur_root, base)
        if rel_dir == ".":
            rel_dir = ""
        rel_dir = rel_dir.replace("\\", "/")

        parent = node_map.get(rel_dir)
        if not parent:
            parts = [p for p in rel_dir.split("/") if p]
            cur = ""
            for p in parts:
                next_path = f"{cur}/{p}" if cur else p
                if next_path not in node_map:
                    node_map[next_path] = make_node(p, next_path, "dir")
                    node_map[cur]["children"].append(node_map[next_path])
                cur = next_path
            parent = node_map.get(rel_dir)

        dirs.sort()
        files.sort()

        for d in dirs:
            child_path = f"{rel_dir}/{d}" if rel_dir else d
            if child_path not in node_map:
                node_map[child_path] = make_node(d, child_path, "dir")
                parent["children"].append(node_map[child_path])

        for fn in files:
            file_path = f"{rel_dir}/{fn}" if rel_dir else fn
            parent["children"].append(make_node(fn, file_path, "file"))

    return {"task_id": task_id, "version": version, "root": root}


def get_file_content(db: Session, task_id: int, version: str, path: str) -> Dict[str, Any]:
    base = _get_extract_path(db, task_id, version)

    abs_path = _resolve_file_abs_path(base, version, path)
    if not abs_path:
        ok, _ = _is_safe_join(base, path)
        if not ok:
            raise ValueError("非法路径")
        raise ValueError("文件不存在")

    content = _read_text_file(abs_path)
    return {
        "task_id": task_id,
        "version": version,
        "path": path.replace("\\", "/"),
        "content": content,
    }


def get_file_diff(db: Session, task_id: int, path: str) -> Dict[str, Any]:
    old_base = _get_extract_path(db, task_id, "old")
    new_base = _get_extract_path(db, task_id, "new")

    old_abs = _resolve_file_abs_path(old_base, "old", path)
    new_abs = _resolve_file_abs_path(new_base, "new", path)

    ok_old, _ = _is_safe_join(old_base, path)
    ok_new, _ = _is_safe_join(new_base, path)
    if not ok_old or not ok_new:
        raise ValueError("非法路径")

    old_exists = bool(old_abs) and os.path.exists(old_abs) and os.path.isfile(old_abs)
    new_exists = bool(new_abs) and os.path.exists(new_abs) and os.path.isfile(new_abs)

    old_text = _read_text_file(old_abs) if old_exists and old_abs else ""
    new_text = _read_text_file(new_abs) if new_exists and new_abs else ""

    diff_lines = difflib.unified_diff(
        old_text.splitlines(keepends=True),
        new_text.splitlines(keepends=True),
        fromfile=f"old:{path}",
        tofile=f"new:{path}",
    )

    return {
        "task_id": task_id,
        "path": path.replace("\\", "/"),
        "old_exists": old_exists,
        "new_exists": new_exists,
        "diff": "".join(diff_lines),
    }
