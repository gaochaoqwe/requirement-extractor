"""
渐进式功能发现记忆查询接口

提供前端查询功能划分记忆的API，包括实时进度查询
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional, List
from pathlib import Path

from ...service.business_review.memory.memory_manager import MemoryManager
from ...service.business_review.chain_review_smart import get_chain_review_progress

router = APIRouter(tags=["progressive_memory"])


@router.get("/progressive/memory/{task_id}")
async def get_progressive_memory(task_id: int) -> Dict[str, Any]:
    """
    获取渐进式功能发现的记忆数据
    
    Args:
        task_id: 任务ID
        
    Returns:
        记忆数据（包含可视化格式）
    """
    try:
        # 查找项目根目录（从任务中获取）
        from ...db.database import get_db_session
        from ...db.models.task import AnalysisTask
        from ...db.models.file import AnalysisFile
        
        with get_db_session() as db:
            task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
            if not task:
                raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
            
            # 通过code_file_id查找文件记录
            if not task.code_file_id:
                raise HTTPException(status_code=400, detail=f"Task {task_id} has no associated file")
            
            file_record = db.query(AnalysisFile).filter(AnalysisFile.id == task.code_file_id).first()
            if not file_record:
                raise HTTPException(status_code=404, detail=f"File {task.code_file_id} not found")
            
            project_root = file_record.extract_path
        
        # 创建记忆管理器
        memory_manager = MemoryManager(task_id, project_root)
        
        # 加载最新记忆
        memory = memory_manager.load_latest()
        
        if not memory:
            return {
                "status": "no_memory",
                "message": "No progressive discovery memory found for this task",
                "task_id": task_id
            }
        
        # 获取可视化数据
        visualization = memory_manager.get_visualization_data()
        
        return {
            "status": "success",
            "task_id": task_id,
            "memory": memory,
            "visualization": visualization
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load memory: {str(e)}")


@router.get("/progressive/memory/{task_id}/round/{round_num}")
async def get_progressive_memory_round(task_id: int, round_num: int) -> Dict[str, Any]:
    """
    获取指定轮次的记忆数据
    
    Args:
        task_id: 任务ID
        round_num: 轮次编号（1, 2, 3...）
        
    Returns:
        指定轮次的记忆数据
    """
    try:
        from ...db.database import get_db_session
        from ...db.models.task import AnalysisTask
        from ...db.models.file import AnalysisFile
        
        with get_db_session() as db:
            task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
            if not task:
                raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
            
            # 通过code_file_id查找文件记录
            if not task.code_file_id:
                raise HTTPException(status_code=400, detail=f"Task {task_id} has no associated file")
            
            file_record = db.query(AnalysisFile).filter(AnalysisFile.id == task.code_file_id).first()
            if not file_record:
                raise HTTPException(status_code=404, detail=f"File {task.code_file_id} not found")
            
            project_root = file_record.extract_path
        
        memory_manager = MemoryManager(task_id, project_root)
        
        # 加载指定轮次
        memory = memory_manager.load_round(round_num)
        
        if not memory:
            raise HTTPException(
                status_code=404,
                detail=f"Round {round_num} memory not found for task {task_id}"
            )
        
        return {
            "status": "success",
            "task_id": task_id,
            "round": round_num,
            "memory": memory
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load round {round_num} memory: {str(e)}")


@router.get("/progressive/visualization/{task_id}")
async def get_progressive_visualization(task_id: int) -> Dict[str, Any]:
    """
    获取前端可视化数据（树形结构）
    
    Args:
        task_id: 任务ID
        
    Returns:
        可视化数据（树形结构、统计信息）
    """
    try:
        from ...db.database import get_db_session
        from ...db.models.task import AnalysisTask
        from ...db.models.file import AnalysisFile
        from ...service.business_review.chain_review_smart import _enhance_memory_with_issues
        import os
        
        with get_db_session() as db:
            task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
            if not task:
                raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
            
            # 通过code_file_id查找文件记录
            if not task.code_file_id:
                raise HTTPException(status_code=400, detail=f"Task {task_id} has no associated file")
            
            file_record = db.query(AnalysisFile).filter(AnalysisFile.id == task.code_file_id).first()
            if not file_record:
                raise HTTPException(status_code=404, detail=f"File {task.code_file_id} not found")
            
            project_root = file_record.extract_path
        
        memory_manager = MemoryManager(task_id, project_root)
        
        # 加载最新记忆
        memory = memory_manager.load_latest()
        
        if not memory:
            return {
                "status": "no_data",
                "message": "No progressive discovery data found",
                "task_id": task_id
            }
        
        # 为memory附加问题统计
        enhanced_memory = _enhance_memory_with_issues(memory, task_id)
        
        # 提取features列表（扁平化，并附加问题统计）
        features = enhanced_memory.get("features", [])
        
        # 构建实际的文件系统树（而不是功能抽象树）
        directory_tree = _build_directory_tree(project_root, features)
        
        # 获取统计信息
        visualization = memory_manager.get_visualization_data()
        
        return {
            "status": "success",
            "task_id": task_id,
            "features": features,  # 带问题统计的features数组，供CodeMapFullscreen使用
            "tree": directory_tree,  # 实际的文件系统树形结构
            "statistics": visualization.get("statistics"),
            "metadata": visualization.get("metadata")
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get visualization: {str(e)}")


@router.get("/progressive/problems/{task_id}")
async def get_chain_problems(task_id: int, feature: Optional[str] = Query(None, description="功能名称，用于按功能过滤问题")) -> Dict[str, Any]:
    """返回链路审查阶段保存的问题列表，可按功能名称过滤。"""
    try:
        from ...db.database_chain import get_chain_db_session
        with get_chain_db_session() as db:
            from ...db.models_chain import ChainReviewProblem
            query = db.query(ChainReviewProblem).filter(ChainReviewProblem.task_id == task_id)
            if feature:
                query = query.filter(ChainReviewProblem.chain_name == feature)
            rows = query.all()
            problems = []
            for row in rows:
                problems.append({
                    "chain_name": row.chain_name,
                    "chain_function_description": getattr(row, "chain_function_description", None),
                    "file_name": row.file_name,
                    "source_code": row.source_code,
                    "problem_reason": row.problem_reason,
                    "issue_level": row.issue_level,
                    "issue_name": row.issue_name,
                    "issue_location": row.issue_location,
                    "description_requirement": row.description_requirement,
                    "description_issue": row.description_issue,
                    "description_location": row.description_location,
                    "description_impact": row.description_impact,
                })
        return {"status": "success", "problems": problems}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chain problems: {str(e)}")


def _build_directory_tree(project_root: str, features: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    构建项目的实际文件系统树
    
    Args:
        project_root: 项目根目录
        features: 功能列表（用于标注调用链路顺序）
        
    Returns:
        文件系统树形结构
    """
    from pathlib import Path
    
    project_path = Path(project_root)
    
    # 收集所有features中涉及的文件和调用链
    file_chains = {}  # {file_path: chain_order}
    
    def extract_files_from_feature(feature: Dict[str, Any], parent_order: str = ""):
        """递归提取feature中的相关文件"""
        related_files = feature.get('related_files', [])
        call_chain = feature.get('call_chain', '')
        
        # 如果有调用链，尝试解析出顺序
        if call_chain:
            # 简单标记：从1开始给每个文件编号
            for idx, file_path in enumerate(related_files, start=1):
                order = f"{parent_order}{idx}" if parent_order else str(idx)
                file_chains[file_path] = order
        
        # 递归处理子功能
        for sub_feature in feature.get('sub_features', []):
            extract_files_from_feature(sub_feature, parent_order)
    
    for feature in features:
        extract_files_from_feature(feature)
    
    def build_tree_recursive(path: Path, base_path: Path) -> Dict[str, Any]:
        """递归构建目录树"""
        rel_path = str(path.relative_to(base_path)) if path != base_path else ""
        
        node = {
            "name": path.name or "项目根目录",
            "type": "directory" if path.is_dir() else "file",
            "path": rel_path,
            "children": []
        }
        
        # 如果是文件，检查是否在调用链中
        if path.is_file():
            file_name = path.name
            if file_name in file_chains:
                node["chainOrder"] = file_chains[file_name]
        
        # 如果是目录，递归构建子节点
        if path.is_dir():
            try:
                for child in sorted(path.iterdir()):
                    # 跳过隐藏文件和特定目录
                    if child.name.startswith('.') or child.name in ['__pycache__', 'node_modules', '.git']:
                        continue
                    
                    child_node = build_tree_recursive(child, base_path)
                    node["children"].append(child_node)
            except PermissionError:
                pass  # 跳过无权限访问的目录
        
        return node
    
    try:
        tree = build_tree_recursive(project_path, project_path)
        return tree
    except Exception as e:
        # 如果构建失败，返回简单结构
        return {
            "name": "项目根目录",
            "type": "directory",
            "path": "",
            "children": [],
            "error": str(e)
        }


@router.get("/progressive/feature/{task_id}/{feature_id}")
async def get_feature_detail(task_id: int, feature_id: str) -> Dict[str, Any]:
    """
    获取指定功能的详细信息
    
    Args:
        task_id: 任务ID
        feature_id: 功能ID
        
    Returns:
        功能详细信息
    """
    try:
        from ...db.database import get_db_session
        from ...db.models.task import AnalysisTask
        from ...db.models.file import AnalysisFile
        
        with get_db_session() as db:
            task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
            if not task:
                raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
            
            # 通过code_file_id查找文件记录
            if not task.code_file_id:
                raise HTTPException(status_code=400, detail=f"Task {task_id} has no associated file")
            
            file_record = db.query(AnalysisFile).filter(AnalysisFile.id == task.code_file_id).first()
            if not file_record:
                raise HTTPException(status_code=404, detail=f"File {task.code_file_id} not found")
            
            project_root = file_record.extract_path
        
        memory_manager = MemoryManager(task_id, project_root)
        
        # 加载最新记忆
        memory_manager.load_latest()
        
        # 获取功能
        feature = memory_manager.get_feature_by_id(feature_id)
        
        if not feature:
            raise HTTPException(
                status_code=404,
                detail=f"Feature {feature_id} not found in task {task_id}"
            )
        
        return {
            "status": "success",
            "task_id": task_id,
            "feature": feature
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get feature detail: {str(e)}")


@router.get("/progressive/progress/{task_id}")
async def get_progressive_progress(task_id: int) -> Dict[str, Any]:
    """
    获取链路审查实时进度（用于前端轮询）
    
    Args:
        task_id: 任务ID
        
    Returns:
        实时进度信息
    """
    try:
        progress = get_chain_review_progress(task_id)
        return progress
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get progress: {str(e)}")


@router.get("/progressive/rounds/{task_id}")
async def get_rounds_history(task_id: int) -> Dict[str, Any]:
    """
    获取所有轮次的历史记录
    
    Args:
        task_id: 任务ID
        
    Returns:
        轮次历史列表
    """
    try:
        from ...db.database import get_db_session
        from ...db.models.task import AnalysisTask
        from ...db.models.file import AnalysisFile
        
        with get_db_session() as db:
            task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
            if not task:
                raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
            
            # 通过code_file_id查找文件记录
            if not task.code_file_id:
                raise HTTPException(status_code=400, detail=f"Task {task_id} has no associated file")
            
            file_record = db.query(AnalysisFile).filter(AnalysisFile.id == task.code_file_id).first()
            if not file_record:
                raise HTTPException(status_code=404, detail=f"File {task.code_file_id} not found")
            
            project_root = file_record.extract_path
        
        memory_manager = MemoryManager(task_id, project_root)
        
        # 加载最新记忆
        memory = memory_manager.load_latest()
        
        if not memory:
            return {
                "status": "no_data",
                "message": "No progressive discovery data found",
                "task_id": task_id,
                "rounds": []
            }
        
        # 获取轮次历史
        rounds_history = memory.get("metadata", {}).get("rounds_history", [])
        
        return {
            "status": "success",
            "task_id": task_id,
            "total_rounds": memory.get("discovery", {}).get("total_rounds", 0),
            "current_round": memory.get("discovery", {}).get("current_round", 0),
            "discovery_status": memory.get("discovery", {}).get("status", "unknown"),
            "rounds": rounds_history
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get rounds history: {str(e)}")

