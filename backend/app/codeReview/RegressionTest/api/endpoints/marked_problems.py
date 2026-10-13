"""
标记问题管理API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from ...db.deps import get_db
from ...db.repository.marked_problem_repo import MarkedProblemRepository
from ...db.repository.task_repo import TaskRepository
from ...utils.logger import log_debug, log_info, log_error

router = APIRouter()


# 请求模型
class SaveMarkedProblemRequest(BaseModel):
    """保存标记问题的请求"""
    analysis_type: str  # function, chain, feature
    problem_key: str
    problem_data: Dict[str, Any]
    marked_by: Optional[str] = None


class RemoveMarkedProblemRequest(BaseModel):
    """移除标记问题的请求"""
    analysis_type: str
    problem_key: str


# 响应模型
class MarkedProblemResponse(BaseModel):
    """标记问题响应"""
    id: int
    task_id: int
    analysis_type: str
    problem_key: str
    problem_data: Dict[str, Any]
    marked_by: Optional[str]
    marked_at: str


@router.post("/{task_id}/marked_problems")
async def save_marked_problem(
    task_id: int,
    request: SaveMarkedProblemRequest,
    db: Session = Depends(get_db)
):
    """
    保存标记的问题
    
    Args:
        task_id: 任务ID
        request: 保存请求
        db: 数据库会话
    
    Returns:
        标记的问题信息
    """
    try:
        # 验证任务是否存在
        task_repo = TaskRepository(db)
        task = task_repo.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 保存标记的问题
        marked_repo = MarkedProblemRepository(db)
        marked_problem = marked_repo.save_marked_problem(
            task_id=task_id,
            analysis_type=request.analysis_type,
            problem_key=request.problem_key,
            problem_data=request.problem_data,
            marked_by=request.marked_by
        )
        
        # 提交保存标记问题
        db.commit()

        # 更新任务的标记问题统计（目前先聚焦函数审查 analysis_type='function'）
        try:
            if request.analysis_type == 'function':
                count = marked_repo.get_marked_problem_count(task_id, request.analysis_type)
                task_repo.update_marked_problem_stats(
                    task_id=task_id,
                    has_marked=count > 0,
                    count=count
                )
        except Exception:
            # 统计更新失败不影响主流程
            pass
        
        log_info(f"保存标记问题成功: task_id={task_id}, type={request.analysis_type}", "marked_problems_api")
        
        return {
            "success": True,
            "message": "标记问题保存成功",
            "data": marked_problem.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        log_error(f"保存标记问题失败: task_id={task_id}", "marked_problems_api", e)
        raise HTTPException(status_code=500, detail=f"保存标记问题失败: {str(e)}")


@router.post("/functionReview/{task_id}/marked_problems")
async def save_marked_problem_function_review(
    task_id: int,
    request: SaveMarkedProblemRequest,
    db: Session = Depends(get_db)
):
    return await save_marked_problem(task_id=task_id, request=request, db=db)


@router.delete("/{task_id}/marked_problems")
async def remove_marked_problem(
    task_id: int,
    request: RemoveMarkedProblemRequest,
    db: Session = Depends(get_db)
):
    """
    移除标记的问题
    
    Args:
        task_id: 任务ID
        request: 移除请求
        db: 数据库会话
    
    Returns:
        操作结果
    """
    try:
        # 验证任务是否存在
        task_repo = TaskRepository(db)
        task = task_repo.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 移除标记的问题
        marked_repo = MarkedProblemRepository(db)
        success = marked_repo.remove_marked_problem(
            task_id=task_id,
            analysis_type=request.analysis_type,
            problem_key=request.problem_key
        )
        
        # 提交删除标记
        db.commit()

        # 更新任务的标记问题统计（仅函数审查）
        try:
            if request.analysis_type == 'function':
                count = marked_repo.get_marked_problem_count(task_id, request.analysis_type)
                task_repo.update_marked_problem_stats(
                    task_id=task_id,
                    has_marked=count > 0,
                    count=count
                )
        except Exception:
            pass
        
        if success:
            log_info(f"移除标记问题成功: task_id={task_id}, type={request.analysis_type}", "marked_problems_api")
            return {
                "success": True,
                "message": "标记问题移除成功"
            }
        else:
            return {
                "success": False,
                "message": "未找到要移除的标记问题"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        log_error(f"移除标记问题失败: task_id={task_id}", "marked_problems_api", e)
        raise HTTPException(status_code=500, detail=f"移除标记问题失败: {str(e)}")


@router.delete("/functionReview/{task_id}/marked_problems")
async def remove_marked_problem_function_review(
    task_id: int,
    request: RemoveMarkedProblemRequest,
    db: Session = Depends(get_db)
):
    return await remove_marked_problem(task_id=task_id, request=request, db=db)


@router.get("/{task_id}/marked_problems")
async def get_marked_problems(
    task_id: int,
    analysis_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取任务的所有标记问题
    
    Args:
        task_id: 任务ID
        analysis_type: 分析类型（可选）
        db: 数据库会话
    
    Returns:
        标记的问题列表
    """
    try:
        # 验证任务是否存在
        task_repo = TaskRepository(db)
        task = task_repo.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 获取标记的问题
        marked_repo = MarkedProblemRepository(db)
        marked_problems = marked_repo.get_marked_problems(task_id, analysis_type)
        
        log_debug(f"获取标记问题: task_id={task_id}, type={analysis_type}, 数量={len(marked_problems)}", "marked_problems_api")
        
        return {
            "success": True,
            "count": len(marked_problems),
            "data": [mp.to_dict() for mp in marked_problems]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"获取标记问题失败: task_id={task_id}", "marked_problems_api", e)
        raise HTTPException(status_code=500, detail=f"获取标记问题失败: {str(e)}")


@router.get("/functionReview/{task_id}/marked_problems")
async def get_marked_problems_function_review(
    task_id: int,
    analysis_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    return await get_marked_problems(task_id=task_id, analysis_type=analysis_type, db=db)


@router.get("/{task_id}/marked_problems/locations")
async def get_marked_problem_locations(
    task_id: int,
    analysis_type: str,
    db: Session = Depends(get_db)
):
    """
    获取已标记问题所在的文件和函数位置
    用于在代码地图中高亮显示
    
    Args:
        task_id: 任务ID
        analysis_type: 分析类型
        db: 数据库会话
    
    Returns:
        文件和函数位置信息
    """
    try:
        # 验证任务是否存在
        task_repo = TaskRepository(db)
        task = task_repo.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 获取标记位置
        marked_repo = MarkedProblemRepository(db)
        locations = marked_repo.get_marked_files_and_functions(task_id, analysis_type)
        
        log_debug(f"获取标记位置: task_id={task_id}, type={analysis_type}, 文件数={len(locations['files'])}", "marked_problems_api")
        
        return {
            "success": True,
            "data": locations
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"获取标记位置失败: task_id={task_id}", "marked_problems_api", e)
        raise HTTPException(status_code=500, detail=f"获取标记位置失败: {str(e)}")


@router.get("/functionReview/{task_id}/marked_problems/locations")
async def get_marked_problem_locations_function_review(
    task_id: int,
    analysis_type: str,
    db: Session = Depends(get_db)
):
    return await get_marked_problem_locations(task_id=task_id, analysis_type=analysis_type, db=db)


@router.get("/{task_id}/marked_problems/count")
async def get_marked_problem_count(
    task_id: int,
    analysis_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取标记问题的数量
    
    Args:
        task_id: 任务ID
        analysis_type: 分析类型（可选）
        db: 数据库会话
    
    Returns:
        标记问题的数量
    """
    try:
        # 验证任务是否存在
        task_repo = TaskRepository(db)
        task = task_repo.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 获取数量
        marked_repo = MarkedProblemRepository(db)
        count = marked_repo.get_marked_problem_count(task_id, analysis_type)
        
        return {
            "success": True,
            "count": count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"获取标记问题数量失败: task_id={task_id}", "marked_problems_api", e)
        raise HTTPException(status_code=500, detail=f"获取标记问题数量失败: {str(e)}")


@router.get("/functionReview/{task_id}/marked_problems/count")
async def get_marked_problem_count_function_review(
    task_id: int,
    analysis_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    return await get_marked_problem_count(task_id=task_id, analysis_type=analysis_type, db=db)

