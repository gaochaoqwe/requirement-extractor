"""
问题状态管理API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from ...db.deps import get_db
from ...db.repository.task_repo import TaskRepository
from ...db.repository.problem_repo import ProblemRepository
from ...utils.logger import log_debug, log_info, log_error

router = APIRouter()


# 请求模型
class UpdateProblemStatusRequest(BaseModel):
    """更新问题状态的请求"""
    problem_ids: List[int]  # 问题ID列表
    status: int  # 状态：1=新发现(绿色)，2=已查看(灰色)，3=已过滤(灰色)，4=已标记


class BatchUpdateProblemStatusRequest(BaseModel):
    """批量更新问题状态的请求"""
    updates: List[dict]  # 更新列表，每个元素包含 problem_id 和 status


# 响应模型
class ProblemStatusResponse(BaseModel):
    """问题状态响应"""
    success: bool
    message: str
    updated_count: Optional[int] = None


@router.patch("/{task_id}/problems/status")
async def update_problem_status(
    task_id: int,
    request: UpdateProblemStatusRequest,
    db: Session = Depends(get_db)
):
    """
    更新问题状态
    
    Args:
        task_id: 任务ID
        request: 更新请求
        db: 数据库会话
    
    Returns:
        更新结果
    """
    try:
        # 验证任务是否存在
        task_repo = TaskRepository(db)
        task = task_repo.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 验证状态值
        if request.status not in [1, 2, 3, 4]:
            raise HTTPException(status_code=400, detail="无效的状态值，必须是1-4之间")
        
        # 更新问题状态
        problem_repo = ProblemRepository(db)
        updated_count = problem_repo.update_problems_status(
            problem_ids=request.problem_ids,
            status=request.status
        )
        
        db.commit()
        
        log_info(
            f"更新问题状态成功: task_id={task_id}, status={request.status}, count={updated_count}",
            "problem_status_api"
        )
        
        return {
            "success": True,
            "message": "问题状态更新成功",
            "updated_count": updated_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        log_error(f"更新问题状态失败: task_id={task_id}", "problem_status_api", e)
        raise HTTPException(status_code=500, detail=f"更新问题状态失败: {str(e)}")


@router.patch("/functionReview/{task_id}/problems/status")
async def update_problem_status_function_review(
    task_id: int,
    request: UpdateProblemStatusRequest,
    db: Session = Depends(get_db)
):
    return await update_problem_status(task_id=task_id, request=request, db=db)


@router.patch("/{task_id}/problems/{problem_id}/status")
async def update_single_problem_status(
    task_id: int,
    problem_id: int,
    status: int,
    db: Session = Depends(get_db)
):
    """
    更新单个问题的状态
    
    Args:
        task_id: 任务ID
        problem_id: 问题ID
        status: 新状态
        db: 数据库会话
    
    Returns:
        更新结果
    """
    try:
        # 验证任务是否存在
        task_repo = TaskRepository(db)
        task = task_repo.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 验证状态值
        if status not in [1, 2, 3, 4]:
            raise HTTPException(status_code=400, detail="无效的状态值，必须是1-4之间")
        
        # 更新问题状态
        problem_repo = ProblemRepository(db)
        updated_count = problem_repo.update_problems_status(
            problem_ids=[problem_id],
            status=status
        )
        
        db.commit()
        
        if updated_count == 0:
            raise HTTPException(status_code=404, detail="问题不存在")
        
        log_debug(
            f"更新单个问题状态: task_id={task_id}, problem_id={problem_id}, status={status}",
            "problem_status_api"
        )
        
        return {
            "success": True,
            "message": "问题状态更新成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        log_error(f"更新问题状态失败: problem_id={problem_id}", "problem_status_api", e)
        raise HTTPException(status_code=500, detail=f"更新问题状态失败: {str(e)}")


@router.patch("/functionReview/{task_id}/problems/{problem_id}/status")
async def update_single_problem_status_function_review(
    task_id: int,
    problem_id: int,
    status: int,
    db: Session = Depends(get_db)
):
    return await update_single_problem_status(task_id=task_id, problem_id=problem_id, status=status, db=db)


@router.get("/{task_id}/problems/status/statistics")
async def get_problem_status_statistics(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    获取任务的问题状态统计
    
    Args:
        task_id: 任务ID
        db: 数据库会话
    
    Returns:
        问题状态统计信息
    """
    try:
        # 验证任务是否存在
        task_repo = TaskRepository(db)
        task = task_repo.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 获取问题状态统计
        problem_repo = ProblemRepository(db)
        statistics = problem_repo.get_problem_status_statistics(task_id)
        
        log_debug(
            f"获取问题状态统计: task_id={task_id}, 统计={statistics}",
            "problem_status_api"
        )
        
        return {
            "success": True,
            "data": {
                "task_id": task_id,
                "statistics": statistics,
                "status_descriptions": {
                    "1": "新发现（绿色）",
                    "2": "已查看（灰色）",
                    "3": "已过滤（灰色）",
                    "4": "已标记"
                }
            },
            "message": "获取统计信息成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"获取问题状态统计失败: task_id={task_id}", "problem_status_api", e)
        raise HTTPException(status_code=500, detail=f"获取问题状态统计失败: {str(e)}")


@router.get("/functionReview/{task_id}/problems/status/statistics")
async def get_problem_status_statistics_function_review(
    task_id: int,
    db: Session = Depends(get_db)
):
    return await get_problem_status_statistics(task_id=task_id, db=db)


@router.post("/{task_id}/problems/status/batch")
async def batch_update_problem_status(
    task_id: int,
    request: BatchUpdateProblemStatusRequest,
    db: Session = Depends(get_db)
):
    """
    批量更新不同问题的不同状态
    
    Args:
        task_id: 任务ID
        request: 批量更新请求
        db: 数据库会话
    
    Returns:
        批量更新结果
    """
    try:
        # 验证任务是否存在
        task_repo = TaskRepository(db)
        task = task_repo.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 批量更新
        problem_repo = ProblemRepository(db)
        total_updated = 0
        
        for update in request.updates:
            problem_id = update.get('problem_id')
            status = update.get('status')
            
            # 验证状态值
            if status not in [1, 2, 3, 4]:
                continue
            
            # 更新单个问题
            updated = problem_repo.update_problems_status(
                problem_ids=[problem_id],
                status=status
            )
            total_updated += updated
        
        db.commit()
        
        log_info(
            f"批量更新问题状态成功: task_id={task_id}, count={total_updated}",
            "problem_status_api"
        )
        
        return {
            "success": True,
            "message": "批量更新成功",
            "updated_count": total_updated
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        log_error(f"批量更新问题状态失败: task_id={task_id}", "problem_status_api", e)
        raise HTTPException(status_code=500, detail=f"批量更新失败: {str(e)}")

