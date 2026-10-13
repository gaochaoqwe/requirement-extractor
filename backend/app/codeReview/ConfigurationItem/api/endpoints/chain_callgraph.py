"""
链路审查调用关系视图接口（两级加载）

- 第一级：按 feature 返回文件级调用关系图
- 第二级：按 feature + file 返回该文件内函数调用子图（仅文件内调用）

数据源：链路审查生成的 call_graph/call_graph.json + ProgressiveDiscovery memory/latest.json
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...db.deps import get_db
from ...db.repository import FileRepository, TaskRepository
from ...service.business_review.memory.memory_manager import MemoryManager


router = APIRouter()


def _load_call_graph(project_root: str) -> Dict[str, Any]:
    project_path = Path(project_root)
    candidates = [
        project_path / "call_graph" / "call_graph.json",
        project_path / "call_graph.json",
        project_path.parent / "call_graph" / "call_graph.json",
        project_path.parent / "call_graph.json",
    ]

    call_graph_file = next((p for p in candidates if p.exists()), None)
    if not call_graph_file:
        raise HTTPException(
            status_code=404,
            detail=f"调用图不存在: {', '.join(str(p) for p in candidates)}",
        )

    try:
        with open(call_graph_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"调用图读取失败: {e}")


def _get_project_root(task_id: int, db: Session) -> str:
    task_repo = TaskRepository(db)
    task = task_repo.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    file_repo = FileRepository(db)
    file_info = file_repo.get_file(task.code_file_id)
    if not file_info or not file_info.extract_path:
        raise HTTPException(status_code=404, detail="代码解压路径不存在")

    if not os.path.exists(file_info.extract_path):
        raise HTTPException(status_code=404, detail="代码解压路径不存在")

    return file_info.extract_path


def _get_feature(task_id: int, project_root: str, feature_id: str) -> Dict[str, Any]:
    memory = MemoryManager(task_id, project_root)
    feature = memory.get_feature_by_id(feature_id)
    if not feature:
        raise HTTPException(status_code=404, detail=f"feature不存在: {feature_id}")
    return feature


def _build_file_level_graph(call_graph: Dict[str, Any], related_files: List[str]) -> Dict[str, Any]:
    files_set = {f for f in (related_files or []) if isinstance(f, str) and f.strip()}

    nodes = [
        {
            "id": f"file:{path}",
            "name": Path(path).name or path,
            "type": "file",
            "path": path,
        }
        for path in sorted(files_set)
    ]

    functions: Dict[str, Dict[str, Any]] = call_graph.get("functions", {}) or {}
    call_edges: List[Dict[str, Any]] = call_graph.get("call_edges", []) or []

    agg: Dict[Tuple[str, str], int] = {}
    for edge in call_edges:
        caller_id = edge.get("from")
        callee_id = edge.get("to")
        if not caller_id or not callee_id:
            continue

        caller = functions.get(caller_id)
        callee = functions.get(callee_id)
        if not caller or not callee:
            continue

        caller_file = caller.get("file")
        callee_file = callee.get("file")
        if not caller_file or not callee_file:
            continue

        if caller_file not in files_set or callee_file not in files_set:
            continue

        if caller_file == callee_file:
            continue

        key = (caller_file, callee_file)
        agg[key] = agg.get(key, 0) + 1

    edges = [
        {
            "id": f"file:{src}->file:{dst}",
            "source": f"file:{src}",
            "target": f"file:{dst}",
            "type": "calls",
            "weight": weight,
        }
        for (src, dst), weight in sorted(agg.items(), key=lambda x: (-x[1], x[0][0], x[0][1]))
    ]

    return {"nodes": nodes, "edges": edges}


def _build_intra_file_function_graph(call_graph: Dict[str, Any], file_path: str) -> Dict[str, Any]:
    indexes = call_graph.get("indexes", {}) or {}
    by_file: Dict[str, List[str]] = indexes.get("by_file", {}) or {}

    func_ids = by_file.get(file_path) or []
    if not func_ids:
        return {"nodes": [], "edges": []}

    functions: Dict[str, Dict[str, Any]] = call_graph.get("functions", {}) or {}
    call_edges: List[Dict[str, Any]] = call_graph.get("call_edges", []) or []

    id_map = {fid: f"fn:{fid}" for fid in func_ids}

    nodes = []
    for fid in func_ids:
        f = functions.get(fid) or {}
        nodes.append(
            {
                "id": id_map[fid],
                "name": f.get("name") or fid,
                "type": "function",
                "file": f.get("file"),
                "line": f.get("line"),
                "end_line": f.get("end_line"),
                "signature": f.get("signature"),
                "raw_id": fid,
            }
        )

    edges = []
    for edge in call_edges:
        caller_id = edge.get("from")
        callee_id = edge.get("to")
        if caller_id in id_map and callee_id in id_map:
            edges.append(
                {
                    "id": f"{id_map[caller_id]}->{id_map[callee_id]}",
                    "source": id_map[caller_id],
                    "target": id_map[callee_id],
                    "type": "calls",
                }
            )

    return {"nodes": nodes, "edges": edges}


@router.get(
    "/chain_callgraph/{task_id}/feature/{feature_id}/files",
    summary="链路审查：按feature获取文件级调用关系图",
)
async def get_feature_file_graph(
    task_id: int,
    feature_id: str,
    db: Session = Depends(get_db),
):
    project_root = _get_project_root(task_id, db)
    call_graph = _load_call_graph(project_root)
    feature = _get_feature(task_id, project_root, feature_id)

    related_files = feature.get("related_files", []) or []
    graph = _build_file_level_graph(call_graph, related_files)

    return {
        "success": True,
        "data": {
            "feature": {"id": feature.get("id"), "name": feature.get("name")},
            "graph": graph,
        },
        "message": "ok",
    }


@router.get(
    "/chain_callgraph/{task_id}/feature/{feature_id}/file",
    summary="链路审查：按feature+file获取该文件内函数调用子图（仅文件内调用）",
)
async def get_feature_intra_file_function_graph(
    task_id: int,
    feature_id: str,
    path: str = Query(..., description="相对路径（与call_graph.json中的file字段一致）"),
    db: Session = Depends(get_db),
):
    project_root = _get_project_root(task_id, db)
    call_graph = _load_call_graph(project_root)
    feature = _get_feature(task_id, project_root, feature_id)

    related_files = feature.get("related_files", []) or []
    if path not in set(related_files):
        raise HTTPException(status_code=400, detail="file不在该feature的related_files范围内")

    graph = _build_intra_file_function_graph(call_graph, path)

    return {
        "success": True,
        "data": {
            "feature": {"id": feature.get("id"), "name": feature.get("name")},
            "file": {"path": path, "name": Path(path).name or path},
            "graph": graph,
        },
        "message": "ok",
    }
