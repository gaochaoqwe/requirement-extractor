"""Excel 操作工具 - 对前端传入的 sheets_snapshot 做只读查询"""
from __future__ import annotations
from typing import Any, Dict, List, Optional


def _find_sheet(snapshot: List[Dict], sheet_name: str) -> Optional[Dict]:
    for s in snapshot:
        if s.get("name") == sheet_name:
            return s
    return None


def _get_cell_text(sheet: Dict, row: int, col: int) -> str:
    rows = sheet.get("rows", {})
    row_obj = rows.get(str(row)) or rows.get(row)
    if not row_obj:
        return ""
    cells = row_obj.get("cells", {})
    cell = cells.get(str(col)) or cells.get(col)
    if not cell:
        return ""
    return str(cell.get("text", ""))


def tool_list_sheets(snapshot: List[Dict], **_) -> Dict[str, Any]:
    return {"sheets": [s.get("name", "") for s in snapshot]}


def tool_get_sheet_info(snapshot: List[Dict], **_) -> Dict[str, Any]:
    return {
        "sheets": [
            {"index": i, "name": s.get("name", f"sheet{i}")}
            for i, s in enumerate(snapshot)
        ]
    }


def tool_read_range(
    snapshot: List[Dict],
    sheet: str,
    start_row: int,
    end_row: int,
    start_col: int = 0,
    end_col: int = 30,
    **_,
) -> Dict[str, Any]:
    ws = _find_sheet(snapshot, sheet)
    if not ws:
        return {"error": f"sheet '{sheet}' not found"}
    result = []
    for r in range(start_row, end_row + 1):
        row_data = [_get_cell_text(ws, r, c) for c in range(start_col, end_col + 1)]
        if any(v.strip() for v in row_data):
            result.append({"row": r, "cols": row_data})
    return {"sheet": sheet, "rows": result}


def tool_find_rows(
    snapshot: List[Dict],
    sheet: str,
    keyword: str,
    col: Optional[int] = None,
    max_results: int = 20,
    **_,
) -> Dict[str, Any]:
    ws = _find_sheet(snapshot, sheet)
    if not ws:
        return {"error": f"sheet '{sheet}' not found"}
    rows = ws.get("rows", {})
    matches = []
    for r_key, row_obj in rows.items():
        # 过滤 x-spreadsheet 的非数字特殊 key（如 "len"）
        if not str(r_key).lstrip("-").isdigit():
            continue
        r = int(r_key)
        cells = row_obj.get("cells", {}) if isinstance(row_obj, dict) else {}
        if col is not None:
            text = str((cells.get(str(col)) or cells.get(col) or {}).get("text", ""))
            if keyword.lower() in text.lower():
                matches.append({"row": r, "text": text})
        else:
            texts = [str(c.get("text", "")) for c in cells.values() if isinstance(c, dict)]
            full = " ".join(texts)
            if keyword.lower() in full.lower():
                matches.append({"row": r, "preview": full[:120]})
        if len(matches) >= max_results:
            break
    return {"sheet": sheet, "keyword": keyword, "matches": matches}


def tool_get_row_count(snapshot: List[Dict], sheet: str, **_) -> Dict[str, Any]:
    ws = _find_sheet(snapshot, sheet)
    if not ws:
        return {"error": f"sheet '{sheet}' not found"}
    rows = ws.get("rows", {})
    numeric_keys = [int(k) for k in rows if str(k).lstrip("-").isdigit()]
    max_r = max(numeric_keys, default=0)
    return {"sheet": sheet, "row_count": max_r + 1}
