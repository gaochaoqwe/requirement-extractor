"""
FPGA support helpers for smart chain review.

Keep FPGA-specific project detection and lightweight call-graph generation
outside `chain_review_smart.py` so the main workflow stays compact.
"""
import json
import re
from pathlib import Path
from typing import Any, Dict, List

from ....config import get_file_type
from ....service.ai.parser.fpga.fpga_parser import (
    extract_fpga_files_from_code,
    read_file_with_encoding,
)


def detect_chain_review_language(project_root: str) -> str:
    """Return `fpga`, `c`, or `mixed` based on project contents."""
    project_path = Path(project_root)
    has_c = False
    has_fpga = False

    for file_path in project_path.rglob("*"):
        if not file_path.is_file():
            continue
        file_type = get_file_type(str(file_path))
        if file_type == "c_cpp":
            has_c = True
        elif file_type == "fpga":
            has_fpga = True
        if has_c and has_fpga:
            return "mixed"

    if has_fpga and not has_c:
        return "fpga"
    if has_c:
        return "c"
    return "c"


def _extract_display_name_parts(display_name: str) -> List[str]:
    """Split parser display name into stable module/entity candidates."""
    if not display_name:
        return []

    parts: List[str] = []
    base_name = display_name.strip()
    if base_name:
        parts.append(base_name)

    match = re.search(r"\((modules|entities):\s*(.*?)\)", display_name, re.IGNORECASE)
    if match:
        module_names = [item.strip() for item in match.group(2).split(',') if item.strip()]
        parts.extend(module_names)

    filename = display_name.split(" (", 1)[0].strip()
    if filename:
        parts.append(filename)
        stem = Path(filename).stem
        if stem:
            parts.append(stem)

    ordered: List[str] = []
    seen = set()
    for item in parts:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def build_fpga_call_graph(project_root: str) -> Dict[str, Any]:
    """Build a lightweight module-level graph structure for FPGA projects."""
    project_path = Path(project_root)
    functions: Dict[str, Dict[str, Any]] = {}
    by_file: Dict[str, list[str]] = {}

    for file_path in project_path.rglob("*"):
        if not file_path.is_file() or get_file_type(str(file_path)) != "fpga":
            continue
        try:
            content, _ = read_file_with_encoding(str(file_path))
            infos = extract_fpga_files_from_code(content, str(file_path))
        except Exception:
            continue

        rel_path = str(file_path.relative_to(project_path)).replace("\\", "/")
        file_nodes: list[str] = []
        for info in infos:
            display_name = info.get("function_name") or file_path.stem
            candidate_names = _extract_display_name_parts(display_name)
            node_name = candidate_names[0] if candidate_names else file_path.stem
            node_id = f"{rel_path}::{node_name}"
            functions[node_id] = {
                "name": node_name,
                "aliases": candidate_names,
                "display_name": display_name,
                "file": rel_path,
                "line": info.get("start_line", 1),
                "end_line": info.get("end_line", 1),
                "signature": display_name,
                "return_type": info.get("language", "verilog"),
                "parameters": "",
                "is_static": False,
                "is_main": False,
                "language": info.get("language", "verilog"),
            }
            file_nodes.append(node_id)
        if file_nodes:
            by_file[rel_path] = file_nodes

    return {
        "project": {
            "root": str(project_path),
            "language": "fpga",
            "total_functions": len(functions),
            "total_files": len(by_file),
            "total_call_edges": 0,
        },
        "functions": functions,
        "call_edges": [],
        "indexes": {
            "by_file": by_file,
            "callers_by_node": {},
            "callees_by_node": {},
        },
    }


def save_fpga_call_graph(project_root: str, output_path: Path) -> Dict[str, Any]:
    """Build and persist the lightweight FPGA call-graph JSON."""
    call_graph_data = build_fpga_call_graph(project_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(call_graph_data, f, ensure_ascii=False, indent=2)
    return call_graph_data

