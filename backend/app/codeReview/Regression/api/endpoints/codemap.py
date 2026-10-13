"""
代码地图API端点

提供代码地图相关的RESTful API接口，包括：
- 获取代码地图数据
- 获取节点详情
- 获取问题信息
- 搜索功能
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
import json
import os
from pathlib import Path

from ...db.deps import get_db
from ...db.repository import RegressionTaskRepository, DiffMappingRepository
from ...db.repository.task_repo import TaskRepository
from ...service.codemap.codemap_builder import CodeMapBuilder, create_code_map
from ...schemas.responses.codemap import (
    CodeMapResponse, 
    NodeDetailResponse, 
    ProblemsResponse,
    SearchResponse
)

router = APIRouter()

@router.get("/codemap/{task_id}", response_model=CodeMapResponse, summary="获取代码地图数据")
async def get_code_map(
    task_id: str,
    db: Session = Depends(get_db)
):
    """
    获取指定任务的代码地图数据
    
    Args:
        task_id: 回归分析任务ID
        
    Returns:
        代码地图数据，包括节点、边、统计信息等
    """
    try:
        # 获取分析任务信息
        task_repo = TaskRepository(db)
        analysis_task = task_repo.get_task(str(task_id))
        if not analysis_task:
            raise HTTPException(status_code=404, detail="分析任务不存在")
        
        # 获取新版本代码文件的解压路径（回归测试主要分析新版本代码）
        extract_path = None
        if analysis_task.new_file and analysis_task.new_file.extract_path:
            extract_path = analysis_task.new_file.extract_path
        elif analysis_task.old_file and analysis_task.old_file.extract_path:
            # 如果新版本没有，使用旧版本作为备选
            extract_path = analysis_task.old_file.extract_path
        
        if not extract_path or not os.path.exists(extract_path):
            raise HTTPException(status_code=404, detail=f"代码解压路径不存在: {extract_path}")
        
        # 获取差异映射记录（相当于问题列表）
        diff_mapping_repo = DiffMappingRepository(db)
        diff_mappings = diff_mapping_repo.get_mappings_by_analysis_task(task_id)
        
        # 将差异映射转换为问题格式
        problems = []
        for mapping in diff_mappings:
            problems.append({
                'id': mapping.id,
                'function_name': mapping.function_name,
                'file_name': mapping.file_path,
                'issue_name': f"{mapping.change_type}变更",
                'description_issue': mapping.diff_summary or "代码变更",
                'problem_reason': mapping.mapping_reason or "",
                'severity': 'medium',  # 默认中等严重性
                'start_line': 1,  # 差异映射没有具体行号
                'end_line': 1,
                'source_code': mapping.new_code or mapping.old_code or ""
            })
        
        # 获取任务信息（用于函数描述）
        regression_task_repo = RegressionTaskRepository(db)
        tasks = regression_task_repo.get_tasks_by_analysis_id(str(task_id))
        functions = []
        task_data = []  # 新增任务数据
        
        for task in tasks:
            # 构建函数信息
            functions.append({
                'function_name': f"Task_{task.task_id}",
                'function_description': task.task_description,
                'commented_code': None  # 回归测试暂时没有注释代码
            })
            
            # 构建任务数据
            task_problems = [p for p in problems if p.get('task_id') == task.task_id]
            task_data.append({
                'id': f"task_{task.task_id}",
                'task_id': task.task_id,
                'task_name': task.task_name,
                'task_description': task.task_description,
                'change_type': task.change_type,
                'status': task.status,
                'problem_count': len(task_problems),
                'problems': task_problems
            })
        
        # 构建代码地图
        code_map = create_code_map(
            project_root=extract_path,
            language="auto",  # 自动检测项目类型
            problems=problems,
            functions=functions
        )
        
        # 转换为响应格式
        builder = CodeMapBuilder(extract_path, "auto")
        map_data = builder.to_dict(code_map)
        
        # 添加任务数据到响应中
        map_data['task_data'] = task_data
        map_data['filtered_problems'] = problems  # 所有问题作为初始过滤结果
        
        return CodeMapResponse(
            success=True,
            data=map_data,
            message="代码地图获取成功"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取代码地图失败: {str(e)}")


@router.get("/codemap/{task_id}/node/{node_id}", response_model=NodeDetailResponse, summary="获取节点详情")
async def get_node_detail(
    task_id: str,
    node_id: str,
    db: Session = Depends(get_db)
):
    """
    获取指定节点的详细信息
    
    Args:
        task_id: 回归分析任务ID
        node_id: 节点ID
        
    Returns:
        节点详细信息，包括源代码、调用关系、问题等
    """
    try:
        # 获取分析任务信息
        task_repo = TaskRepository(db)
        analysis_task = task_repo.get_task(str(task_id))
        if not analysis_task:
            raise HTTPException(status_code=404, detail="分析任务不存在")
        
        # 获取新版本代码文件的解压路径（回归测试主要分析新版本代码）
        extract_path = None
        if analysis_task.new_file and analysis_task.new_file.extract_path:
            extract_path = analysis_task.new_file.extract_path
        elif analysis_task.old_file and analysis_task.old_file.extract_path:
            # 如果新版本没有，使用旧版本作为备选
            extract_path = analysis_task.old_file.extract_path
        
        if not extract_path or not os.path.exists(extract_path):
            raise HTTPException(status_code=404, detail=f"代码解压路径不存在: {extract_path}")
        
        # 获取差异映射记录
        diff_mapping_repo = DiffMappingRepository(db)
        diff_mappings = diff_mapping_repo.get_mappings_by_analysis_task(task_id)
        
        # 将差异映射转换为问题格式
        problems = []
        for mapping in diff_mappings:
            problems.append({
                'id': mapping.id,
                'function_name': mapping.function_name,
                'file_name': mapping.file_path,
                'issue_name': f"{mapping.change_type}变更",
                'description_issue': mapping.diff_summary or "代码变更",
                'problem_reason': mapping.mapping_reason or "",
                'severity': 'medium',
                'start_line': 1,
                'end_line': 1,
                'source_code': mapping.new_code or mapping.old_code or ""
            })
        
        # 获取任务信息
        tasks = task_repo.get_tasks_by_analysis_id(task_id)
        functions = []
        for task in tasks:
            functions.append({
                'function_name': f"Task_{task.task_id}",
                'function_description': task.task_description,
                'commented_code': None
            })
        
        # 构建代码地图
        code_map = create_code_map(
            project_root=extract_path,
            language="auto",
            problems=problems,
            functions=functions
        )
        
        # 查找指定节点
        target_node = None
        for node in code_map.nodes:
            if node.id == node_id:
                target_node = node
                break
        
        if not target_node:
            raise HTTPException(status_code=404, detail="节点不存在")
        
        # 获取相关的边信息
        incoming_edges = [edge for edge in code_map.edges if edge.target == node_id]
        outgoing_edges = [edge for edge in code_map.edges if edge.source == node_id]
        
        return NodeDetailResponse(
            success=True,
            data={
                "node": target_node.__dict__,
                "incoming_edges": [edge.__dict__ for edge in incoming_edges],
                "outgoing_edges": [edge.__dict__ for edge in outgoing_edges],
                "related_nodes": {
                    "callers": [edge.source for edge in incoming_edges if edge.type == "calls"],
                    "callees": [edge.target for edge in outgoing_edges if edge.type == "calls"],
                    "children": target_node.children,
                    "parent": target_node.parent
                }
            },
            message="节点详情获取成功"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取节点详情失败: {str(e)}")


@router.get("/codemap/{task_id}/problems", response_model=ProblemsResponse, summary="获取问题列表")
async def get_problems(
    task_id: str,
    node_id: Optional[str] = Query(None, description="节点ID，用于过滤特定节点的问题"),
    db: Session = Depends(get_db)
):
    """
    获取代码地图中的问题列表（差异映射记录）
    
    Args:
        task_id: 回归分析任务ID
        node_id: 可选，节点ID，用于过滤特定节点的问题
        
    Returns:
        问题列表
    """
    try:
        # 获取分析任务信息
        task_repo = TaskRepository(db)
        analysis_task = task_repo.get_task(str(task_id))
        if not analysis_task:
            raise HTTPException(status_code=404, detail="分析任务不存在")
        
        # 获取新版本代码文件的解压路径（回归测试主要分析新版本代码）
        extract_path = None
        if analysis_task.new_file and analysis_task.new_file.extract_path:
            extract_path = analysis_task.new_file.extract_path
        elif analysis_task.old_file and analysis_task.old_file.extract_path:
            # 如果新版本没有，使用旧版本作为备选
            extract_path = analysis_task.old_file.extract_path
        
        if not extract_path or not os.path.exists(extract_path):
            raise HTTPException(status_code=404, detail=f"代码解压路径不存在: {extract_path}")
        
        # 获取差异映射记录
        diff_mapping_repo = DiffMappingRepository(db)
        diff_mappings = diff_mapping_repo.get_mappings_by_analysis_task(task_id)
        
        # 转换为问题格式
        problems = []
        for mapping in diff_mappings:
            problems.append({
                'id': mapping.id,
                'function_name': mapping.function_name,
                'file_name': mapping.file_path,
                'issue_name': f"{mapping.change_type}变更",
                'description_issue': mapping.diff_summary or "代码变更",
                'problem_reason': mapping.mapping_reason or "",
                'severity': 'medium',
                'start_line': 1,
                'end_line': 1,
                'source_code': mapping.new_code or mapping.old_code or "",
                'task_id': mapping.task_id,
                'mapping_confidence': mapping.mapping_confidence,
                'mapping_score': mapping.mapping_score
            })
        
        # 如果指定了节点ID，过滤问题
        if node_id:
            # 解析节点ID获取函数名
            if node_id.startswith("func:"):
                parts = node_id.split(":")
                if len(parts) >= 3:
                    function_name = parts[2]
                    problems = [p for p in problems if p.get('function_name') == function_name]
        
        return ProblemsResponse(
            success=True,
            data=problems,
            message="问题列表获取成功"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取问题列表失败: {str(e)}")


@router.get("/codemap/{task_id}/search", response_model=SearchResponse, summary="搜索代码地图")
async def search_code_map(
    task_id: str,
    query: str = Query(..., description="搜索关键词"),
    search_type: str = Query("all", description="搜索类型：all, function, file, problem"),
    db: Session = Depends(get_db)
):
    """
    在代码地图中搜索
    
    Args:
        task_id: 回归分析任务ID
        query: 搜索关键词
        search_type: 搜索类型
        
    Returns:
        搜索结果
    """
    try:
        # 获取分析任务信息
        task_repo = TaskRepository(db)
        analysis_task = task_repo.get_task(str(task_id))
        if not analysis_task:
            raise HTTPException(status_code=404, detail="分析任务不存在")
        
        # 获取新版本代码文件的解压路径（回归测试主要分析新版本代码）
        extract_path = None
        if analysis_task.new_file and analysis_task.new_file.extract_path:
            extract_path = analysis_task.new_file.extract_path
        elif analysis_task.old_file and analysis_task.old_file.extract_path:
            # 如果新版本没有，使用旧版本作为备选
            extract_path = analysis_task.old_file.extract_path
        
        if not extract_path or not os.path.exists(extract_path):
            raise HTTPException(status_code=404, detail=f"代码解压路径不存在: {extract_path}")
        
        # 获取差异映射记录
        diff_mapping_repo = DiffMappingRepository(db)
        diff_mappings = diff_mapping_repo.get_mappings_by_analysis_task(task_id)
        
        # 转换为问题格式
        problems = []
        for mapping in diff_mappings:
            problems.append({
                'id': mapping.id,
                'function_name': mapping.function_name,
                'file_name': mapping.file_path,
                'issue_name': f"{mapping.change_type}变更",
                'description_issue': mapping.diff_summary or "代码变更",
                'problem_reason': mapping.mapping_reason or "",
                'severity': 'medium'
            })
        
        # 获取任务信息
        tasks = task_repo.get_tasks_by_analysis_id(task_id)
        functions = []
        for task in tasks:
            functions.append({
                'function_name': f"Task_{task.task_id}",
                'function_description': task.task_description,
                'commented_code': None
            })
        
        # 构建代码地图
        code_map = create_code_map(
            project_root=extract_path,
            language="auto",
            problems=problems,
            functions=functions
        )
        
        # 执行搜索
        results = []
        query_lower = query.lower()
        
        # 搜索节点
        if search_type in ["all", "function", "file"]:
            for node in code_map.nodes:
                if search_type == "function" and node.type != "function":
                    continue
                if search_type == "file" and node.type != "file":
                    continue
                
                # 搜索节点名称
                if query_lower in node.name.lower():
                    results.append({
                        "type": "node",
                        "id": node.id,
                        "name": node.name,
                        "node_type": node.type,
                        "file_path": node.file_path,
                        "match_type": "name"
                    })
                
                # 搜索源代码内容
                if query_lower in node.source_code.lower():
                    results.append({
                        "type": "node",
                        "id": node.id,
                        "name": node.name,
                        "node_type": node.type,
                        "file_path": node.file_path,
                        "match_type": "source_code"
                    })
        
        # 搜索问题（差异映射）
        if search_type in ["all", "problem"]:
            for problem in problems:
                problem_text = f"{problem.get('issue_name', '')} {problem.get('description_issue', '')} {problem.get('problem_reason', '')}"
                if query_lower in problem_text.lower():
                    results.append({
                        "type": "problem",
                        "id": f"problem:{problem.get('id')}",
                        "name": problem.get('issue_name', ''),
                        "description": problem.get('description_issue', ''),
                        "function_name": problem.get('function_name', ''),
                        "file_name": problem.get('file_name', ''),
                        "match_type": "content"
                    })
        
        return SearchResponse(
            success=True,
            data=results,
            message=f"搜索完成，找到{len(results)}个结果"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.get("/codemap/{task_id}/statistics", summary="获取代码地图统计信息")
async def get_statistics(
    task_id: str,
    db: Session = Depends(get_db)
):
    """
    获取代码地图的统计信息
    
    Args:
        task_id: 回归分析任务ID
        
    Returns:
        统计信息
    """
    try:
        # 获取分析任务信息
        task_repo = TaskRepository(db)
        analysis_task = task_repo.get_task(str(task_id))
        if not analysis_task:
            raise HTTPException(status_code=404, detail="分析任务不存在")
        
        # 获取新版本代码文件的解压路径（回归测试主要分析新版本代码）
        extract_path = None
        if analysis_task.new_file and analysis_task.new_file.extract_path:
            extract_path = analysis_task.new_file.extract_path
        elif analysis_task.old_file and analysis_task.old_file.extract_path:
            # 如果新版本没有，使用旧版本作为备选
            extract_path = analysis_task.old_file.extract_path
        
        if not extract_path or not os.path.exists(extract_path):
            raise HTTPException(status_code=404, detail=f"代码解压路径不存在: {extract_path}")
        
        # 获取差异映射记录
        diff_mapping_repo = DiffMappingRepository(db)
        diff_mappings = diff_mapping_repo.get_mappings_by_analysis_task(task_id)
        
        # 转换为问题格式
        problems = []
        for mapping in diff_mappings:
            problems.append({
                'id': mapping.id,
                'function_name': mapping.function_name,
                'file_name': mapping.file_path,
                'issue_name': f"{mapping.change_type}变更",
                'description_issue': mapping.diff_summary or "代码变更",
                'problem_reason': mapping.mapping_reason or ""
            })
        
        # 获取任务信息
        tasks = task_repo.get_tasks_by_analysis_id(task_id)
        functions = []
        for task in tasks:
            functions.append({
                'function_name': f"Task_{task.task_id}",
                'function_description': task.task_description,
                'commented_code': None
            })
        
        # 构建代码地图
        code_map = create_code_map(
            project_root=extract_path,
            language="auto",
            problems=problems,
            functions=functions
        )
        
        return {
            "success": True,
            "data": code_map.statistics,
            "message": "统计信息获取成功"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.post("/codemap/{task_id}/export", summary="导出代码地图")
async def export_code_map(
    task_id: str,
    export_format: str = Query("json", description="导出格式：json, dot, svg"),
    db: Session = Depends(get_db)
):
    """
    导出代码地图到指定格式
    
    Args:
        task_id: 回归分析任务ID
        export_format: 导出格式
        
    Returns:
        导出结果
    """
    try:
        # 获取分析任务信息
        task_repo = TaskRepository(db)
        analysis_task = task_repo.get_task(str(task_id))
        if not analysis_task:
            raise HTTPException(status_code=404, detail="分析任务不存在")
        
        # 获取新版本代码文件的解压路径（回归测试主要分析新版本代码）
        extract_path = None
        if analysis_task.new_file and analysis_task.new_file.extract_path:
            extract_path = analysis_task.new_file.extract_path
        elif analysis_task.old_file and analysis_task.old_file.extract_path:
            # 如果新版本没有，使用旧版本作为备选
            extract_path = analysis_task.old_file.extract_path
        
        if not extract_path or not os.path.exists(extract_path):
            raise HTTPException(status_code=404, detail=f"代码解压路径不存在: {extract_path}")
        
        # 获取差异映射记录
        diff_mapping_repo = DiffMappingRepository(db)
        diff_mappings = diff_mapping_repo.get_mappings_by_analysis_task(task_id)
        
        # 转换为问题格式
        problems = []
        for mapping in diff_mappings:
            problems.append({
                'id': mapping.id,
                'function_name': mapping.function_name,
                'file_name': mapping.file_path,
                'issue_name': f"{mapping.change_type}变更",
                'description_issue': mapping.diff_summary or "代码变更",
                'problem_reason': mapping.mapping_reason or ""
            })
        
        # 获取任务信息
        tasks = task_repo.get_tasks_by_analysis_id(task_id)
        functions = []
        for task in tasks:
            functions.append({
                'function_name': f"Task_{task.task_id}",
                'function_description': task.task_description,
                'commented_code': None
            })
        
        # 构建代码地图
        code_map = create_code_map(
            project_root=extract_path,
            language="auto",
            problems=problems,
            functions=functions
        )
        
        # 根据格式导出
        if export_format == "json":
            builder = CodeMapBuilder(extract_path, "auto")
            data = builder.to_dict(code_map)
            return {
                "success": True,
                "data": data,
                "message": "JSON导出成功"
            }
        elif export_format == "dot":
            # 生成DOT格式（Graphviz）
            dot_content = _generate_dot_format(code_map)
            return {
                "success": True,
                "data": {"content": dot_content},
                "message": "DOT格式导出成功"
            }
        else:
            raise HTTPException(status_code=400, detail="不支持的导出格式")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


def _generate_dot_format(code_map) -> str:
    """生成DOT格式的图形描述"""
    lines = ["digraph CodeMap {"]
    lines.append("  rankdir=TB;")
    lines.append("  node [shape=box];")
    
    # 添加节点
    for node in code_map.nodes:
        color = "lightblue" if node.type == "file" else "lightgreen"
        if node.problems:
            color = "lightcoral"
        
        label = f"{node.name}\\n({node.type})"
        if node.problems:
            label += f"\\n{len(node.problems)} problems"
        
        lines.append(f'  "{node.id}" [label="{label}", fillcolor="{color}", style=filled];')
    
    # 添加边
    for edge in code_map.edges:
        style = "solid" if edge.type == "calls" else "dashed"
        lines.append(f'  "{edge.source}" -> "{edge.target}" [style="{style}"];')
    
    lines.append("}")
    return "\n".join(lines) 