from typing import Dict, Any, List, Tuple
from pathlib import Path
import json
import re

from ....config_database_chain import get_chain_db_session  # 使用链路审查数据库切换模块
from ....db.repository.task_repo import TaskRepository


def _normalize_text(text: str) -> str:
    if not text:
        return ""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _brief_line(text: str, max_len: int = 200) -> str:
    t = (_normalize_text(text).strip().split("\n") or [""])[0]
    return (t[:max_len] + ("..." if len(t) > max_len else "")) if t else ""


def _extract_signature(function_name: str, source_code: str) -> str:
    head = _normalize_text(source_code).split("\n", 1)[0] if source_code else ""
    return f"{function_name} :: {head[:160]}"


def build_hierarchy_index(task_id: int) -> Dict[str, Any]:
    """为任务构建分层索引：基于源文件和函数信息构建"""
    from collections import defaultdict
    import re
    
    files_docs: List[Dict[str, Any]] = []
    funcs_docs: List[Dict[str, Any]] = []

    with get_chain_db_session() as db:
        task_repo = TaskRepository(db)
        task = task_repo.get_task(task_id)
        if not task:
            return {"files": [], "functions": []}

        # 收集所有函数信息
        all_functions = []
        for file_record in task.files:
            all_functions.extend(file_record.functions)
        
        if not all_functions:
            return {"files": [], "functions": []}
        
        # 按源文件路径分组函数
        files_functions = defaultdict(list)
        for func in all_functions:
            file_path = func.file_path or "unknown"
            files_functions[file_path].append(func)
        
        # 解析合并的文件概述
        file_summaries_map = {}
        if task.files and task.files[0].file_function_summary:
            combined_summary = task.files[0].file_function_summary
            # 解析格式：[file_path]\n概述内容\n\n[next_file]...
            pattern = r'\[([^\]]+)\]\n(.*?)(?=\n\[|$)'
            matches = re.findall(pattern, combined_summary, re.DOTALL)
            for file_path, summary in matches:
                file_summaries_map[file_path] = summary.strip()
        
        # 为每个源文件构建文档
        for file_path, functions in files_functions.items():
            # 过滤有效的源文件
            if (file_path == "unknown" or 
                file_path.endswith('.zip') or 
                not any(file_path.endswith(ext) for ext in ['.c', '.cpp', '.h', '.hpp', '.cc', '.cxx'])):
                continue
            
            function_names = []
            brief_pieces = []
            
            # 处理文件中的函数
            for func in functions:
                function_names.append(func.function_name)
                brief_pieces.append(_extract_signature(func.function_name, func.source_code or ""))
                
                # 添加函数文档
                funcs_docs.append({
                    "id": f"func:{func.id}",
                    "type": "function",
                    "file": file_path,  # 使用源文件路径而不是ZIP文件名
                    "function": func.function_name,
                    "text": _normalize_text(func.source_code or "")[:4000],
                    "function_id": func.id,
                    "file_id": func.file_id,
                })
            
            # 获取文件概述
            file_summary = file_summaries_map.get(file_path, "")
            if not file_summary:
                # 如果没有AI生成的概述，使用函数签名汇总
                file_summary = "; ".join(brief_pieces[:30])
            
            # 添加文件文档
            files_docs.append({
                "id": f"sourcefile:{file_path}",
                "type": "file",
                "file": file_path,
                "summary": file_summary,
                "function_names": function_names,
                "function_count": len(functions),
                "file_id": functions[0].file_id if functions else None,
            })

    return {"files": files_docs, "functions": funcs_docs}


def save_index(task_id: int, index: Dict[str, Any], store_dir: Path) -> None:
    store_dir.mkdir(parents=True, exist_ok=True)
    (store_dir / "files.json").write_text(json.dumps(index.get("files", []), ensure_ascii=False), encoding="utf-8")
    (store_dir / "functions.json").write_text(json.dumps(index.get("functions", []), ensure_ascii=False), encoding="utf-8")


def load_index(task_id: int, store_dir: Path) -> Dict[str, Any]:
    files_p = store_dir / "files.json"
    funcs_p = store_dir / "functions.json"
    if files_p.exists() and funcs_p.exists():
        try:
            files = json.loads(files_p.read_text(encoding="utf-8"))
            funcs = json.loads(funcs_p.read_text(encoding="utf-8"))
            return {"files": files, "functions": funcs}
        except Exception:
            return {"files": [], "functions": []}
    return {"files": [], "functions": []} 