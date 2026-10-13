import os
import difflib
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from ...db.models.file import AnalysisFile
from ...db.models.function import AnalysisFunction
from ...db.models.function_pair import RegressionFunctionPair
from .function_scanner import scan_all_c_cpp_functions


@dataclass
class VersionFiles:
    old_file: AnalysisFile
    new_file: AnalysisFile


def _normalize_key(file_path: str, function_name: str) -> Tuple[str, str]:
    return (os.path.normcase(os.path.normpath(file_path or "")), function_name or "")


def _unified_diff(old_code: str, new_code: str, fromfile: str, tofile: str) -> str:
    old_lines = (old_code or "").splitlines(keepends=True)
    new_lines = (new_code or "").splitlines(keepends=True)
    diff_lines = difflib.unified_diff(old_lines, new_lines, fromfile=fromfile, tofile=tofile)
    return "".join(diff_lines)


def _similarity(old_code: str, new_code: str) -> float:
    sm = difflib.SequenceMatcher(a=(old_code or ""), b=(new_code or ""))
    return float(sm.ratio())


def _normalize_code_for_compare(code: str) -> str:
    s = code or ""
    # 去掉 UTF-8 BOM，避免“看起来一样但字符串不同”
    if s.startswith("\ufeff"):
        s = s.lstrip("\ufeff")
    # 统一换行
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    # 去掉每行行尾空白
    lines = [ln.rstrip() for ln in s.split("\n")]
    # 去掉首尾空行（仅空白/空字符串）
    while lines and lines[0].strip() == "":
        lines.pop(0)
    while lines and lines[-1].strip() == "":
        lines.pop()
    return "\n".join(lines)


def _read_text_file_best_effort(path: str) -> str:
    # 回归目录对比：不要求严格编码，尽可能稳定地读出文本用于比较
    encodings = ["utf-8", "gbk", "gb2312", "gb18030", "big5", "latin-1"]
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, LookupError, OSError):
            continue
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except OSError:
        return ""


def _scan_code_files(base_dir: str) -> Dict[str, str]:
    """扫描 extract_path 下的代码文件，返回 rel_path -> abs_path

    注意：这里的 rel_path 与函数扫描保持一致，会剥离第一级目录，用于跨版本对齐。
    """
    exts = {
        ".c",
        ".cc",
        ".cpp",
        ".cxx",
        ".h",
        ".hh",
        ".hpp",
        ".hxx",
    }

    out: Dict[str, str] = {}
    base_abs = os.path.abspath(base_dir)
    for cur_root, _, files in os.walk(base_abs):
        for fn in files:
            ext = os.path.splitext(fn)[-1].lower()
            if ext not in exts:
                continue
            abs_path = os.path.join(cur_root, fn)
            try:
                rel = os.path.relpath(abs_path, base_abs)
            except Exception:
                continue
            rel = rel.replace("\\", "/")
            # 与 function_scanner._normalize_rel_path 保持一致：剥离第一级目录
            parts = [x for x in rel.split("/") if x not in ("", ".")]
            if len(parts) >= 2:
                rel = "/".join(parts[1:])
            else:
                rel = "/".join(parts)
            if not rel:
                continue
            # 去重：同名冲突时保留第一条
            if rel not in out:
                out[rel] = abs_path
    return out


def _detect_file_changes(old_extract: str, new_extract: str) -> Dict[str, str]:
    """返回 rel_path -> change_type (new/deleted/modified/unchanged)"""
    old_files = _scan_code_files(old_extract)
    new_files = _scan_code_files(new_extract)

    keys = set(old_files.keys()) | set(new_files.keys())
    out: Dict[str, str] = {}

    for rel in sorted(keys):
        o = old_files.get(rel)
        n = new_files.get(rel)

        if o and not n:
            out[rel] = "deleted"
            continue
        if n and not o:
            out[rel] = "new"
            continue
        if not o or not n:
            continue

        old_text = _normalize_code_for_compare(_read_text_file_best_effort(o))
        new_text = _normalize_code_for_compare(_read_text_file_best_effort(n))
        out[rel] = "unchanged" if old_text == new_text else "modified"

    return out


def get_task_version_files(db: Session, task_id: int) -> VersionFiles:
    files = db.query(AnalysisFile).filter(AnalysisFile.task_id == task_id).all()
    old_file = next((f for f in files if (f.version or "").lower() == "old"), None)
    new_file = next((f for f in files if (f.version or "").lower() == "new"), None)
    if not old_file or not new_file:
        raise ValueError("该task_id下必须同时存在version=old和version=new的上传记录")
    if not old_file.extract_path or not os.path.exists(old_file.extract_path):
        raise ValueError(f"旧版本解压目录不存在: {old_file.extract_path}")
    if not new_file.extract_path or not os.path.exists(new_file.extract_path):
        raise ValueError(f"新版本解压目录不存在: {new_file.extract_path}")
    return VersionFiles(old_file=old_file, new_file=new_file)


def refresh_functions_for_file(db: Session, file_obj: AnalysisFile, version: str) -> List[AnalysisFunction]:
    db.query(AnalysisFunction).filter(AnalysisFunction.file_id == file_obj.id).delete(synchronize_session=False)
    db.flush()

    funcs = scan_all_c_cpp_functions(file_obj.extract_path)
    func_rows: List[AnalysisFunction] = []
    for f in funcs:
        func_rows.append(
            AnalysisFunction(
                file_id=file_obj.id,
                function_name=f.get("function_name"),
                start_line=int(f.get("start_line") or 0) or 1,
                end_line=int(f.get("end_line") or 0) or 1,
                source_code=f.get("source_code") or "",
                analyzed=False,
                file_path=f.get("file_path"),
                version=version,
            )
        )

    if func_rows:
        db.bulk_save_objects(func_rows)
    db.flush()

    return db.query(AnalysisFunction).filter(AnalysisFunction.file_id == file_obj.id).all()


def refresh_task_change_detection(db: Session, task_id: int) -> Dict[str, int]:
    vf = get_task_version_files(db, task_id)

    db.query(RegressionFunctionPair).filter(RegressionFunctionPair.task_id == task_id).delete(synchronize_session=False)
    db.flush()

    old_funcs = refresh_functions_for_file(db, vf.old_file, version="old")
    new_funcs = refresh_functions_for_file(db, vf.new_file, version="new")

    old_map: Dict[Tuple[str, str], AnalysisFunction] = {}
    for f in old_funcs:
        old_map[_normalize_key(f.file_path, f.function_name)] = f

    new_map: Dict[Tuple[str, str], AnalysisFunction] = {}
    for f in new_funcs:
        new_map[_normalize_key(f.file_path, f.function_name)] = f

    all_keys = set(old_map.keys()) | set(new_map.keys())

    created_pairs: List[RegressionFunctionPair] = []
    stats = {"new": 0, "modified": 0, "deleted": 0, "unchanged": 0}

    for key in sorted(all_keys):
        old_f = old_map.get(key)
        new_f = new_map.get(key)

        if old_f and new_f:
            old_code = old_f.source_code or ""
            new_code = new_f.source_code or ""

            old_cmp = _normalize_code_for_compare(old_code)
            new_cmp = _normalize_code_for_compare(new_code)

            if old_cmp == new_cmp:
                change_type = "unchanged"
                should_review = False
            else:
                change_type = "modified"
                should_review = True

            diff_text = _unified_diff(
                old_code,
                new_code,
                fromfile=f"old:{old_f.file_path}:{old_f.function_name}",
                tofile=f"new:{new_f.file_path}:{new_f.function_name}",
            )
            score = _similarity(old_code, new_code)

            old_f.change_type = change_type
            new_f.change_type = change_type
            old_f.paired_function_id = new_f.id
            new_f.paired_function_id = old_f.id
            new_f.code_diff = diff_text

            created_pairs.append(
                RegressionFunctionPair(
                    task_id=task_id,
                    old_function_id=old_f.id,
                    new_function_id=new_f.id,
                    change_type=change_type,
                    similarity_score=score,
                    should_review=should_review,
                )
            )
            stats[change_type] += 1

        elif old_f and not new_f:
            change_type = "deleted"
            old_f.change_type = change_type
            old_f.paired_function_id = None

            created_pairs.append(
                RegressionFunctionPair(
                    task_id=task_id,
                    old_function_id=old_f.id,
                    new_function_id=None,
                    change_type=change_type,
                    similarity_score=None,
                    should_review=False,
                )
            )
            stats[change_type] += 1

        elif new_f and not old_f:
            change_type = "new"
            new_f.change_type = change_type
            new_f.paired_function_id = None

            created_pairs.append(
                RegressionFunctionPair(
                    task_id=task_id,
                    old_function_id=None,
                    new_function_id=new_f.id,
                    change_type=change_type,
                    similarity_score=None,
                    should_review=True,
                )
            )
            stats[change_type] += 1

    if created_pairs:
        db.bulk_save_objects(created_pairs)

    db.commit()
    return stats


def get_task_changes(db: Session, task_id: int, refresh: bool = False) -> Dict:
    if refresh:
        stats = refresh_task_change_detection(db, task_id)
    else:
        stats = None

    pairs = (
        db.query(RegressionFunctionPair)
        .filter(RegressionFunctionPair.task_id == task_id)
        .order_by(RegressionFunctionPair.id)
        .all()
    )

    def _func_brief(func_id: Optional[int]) -> Optional[Dict]:
        if not func_id:
            return None
        f = db.query(AnalysisFunction).filter(AnalysisFunction.id == func_id).first()
        if not f:
            return None
        return {
            "id": f.id,
            "file_id": f.file_id,
            "file_path": f.file_path,
            "function_name": f.function_name,
            "start_line": f.start_line,
            "end_line": f.end_line,
            "version": f.version,
            "change_type": f.change_type,
            "paired_function_id": f.paired_function_id,
        }

    items = []
    for p in pairs:
        items.append(
            {
                "pair_id": p.id,
                "task_id": p.task_id,
                "change_type": p.change_type,
                "similarity_score": p.similarity_score,
                "should_review": p.should_review,
                "old": _func_brief(p.old_function_id),
                "new": _func_brief(p.new_function_id),
            }
        )

    if stats is None:
        stats = {"new": 0, "modified": 0, "deleted": 0, "unchanged": 0}
        for it in items:
            ct = it.get("change_type")
            if ct in stats:
                stats[ct] += 1

    # 文件级变更（用于头文件等无函数体场景的颜色/统计）
    try:
        vf = get_task_version_files(db, task_id)
        file_changes = _detect_file_changes(vf.old_file.extract_path, vf.new_file.extract_path)
    except Exception:
        file_changes = {}

    return {"task_id": task_id, "stats": stats, "items": items, "file_changes": file_changes}
