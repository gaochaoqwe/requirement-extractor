import os
from typing import Any, Dict, List, Optional

from app.staticAnalysis.normalModeC.config.config import ALLOWED_CODE_EXTENSIONS


SUPPORTED_CPP_EXTENSIONS = {".cpp", ".cc", ".cxx", ".hpp", ".hxx", ".c++", ".h++"}


def scan_c_source_files(extract_path: str) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for root, _, files in os.walk(extract_path):
        for file_name in files:
            ext = os.path.splitext(file_name)[1].lower()
            if ext not in ALLOWED_CODE_EXTENSIONS:
                continue
            abs_path = os.path.join(root, file_name)
            rel_path = os.path.relpath(abs_path, extract_path)
            source_code = _read_text(abs_path)
            if source_code is None:
                continue
            items.append({
                "file_name": file_name,
                "file_path": rel_path,
                "absolute_path": abs_path,
                "language": "cpp" if ext in SUPPORTED_CPP_EXTENSIONS else "c",
                "source_code": source_code,
            })
    return items


def _read_text(path: str) -> Optional[str]:
    encodings = ["utf-8", "gbk", "gb2312", "gb18030", "latin-1"]
    for encoding in encodings:
        try:
            with open(path, "r", encoding=encoding) as f:
                return f.read()
        except Exception:
            continue
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return None
