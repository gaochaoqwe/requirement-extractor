"""
问题状态管理API端点
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from ..database.database import get_db
from ..repositories.problem_repo import ProblemRepository

router = APIRouter()


# 请求模型
class UpdateProblemStatusRequest(BaseModel):
    """更新问题状态的请求"""
    problem_ids: List[int]  # 问题ID列表
    status: int  # 状态：1=新发现(绿色)，2=已查看(灰色)，3=已过滤(灰色)，4=已标记(蓝色)


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
    task_id: str,
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
        
        print(f"[API] 更新问题状态成功: task_id={task_id}, status={request.status}, count={updated_count}")
        
        return {
            "success": True,
            "message": "问题状态更新成功",
            "updated_count": updated_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"[API] 更新问题状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新问题状态失败: {str(e)}")


@router.patch("/{task_id}/problems/{problem_id}/status")
async def update_single_problem_status(
    task_id: str,
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
        # 验证状态值
        if status not in [1, 2, 3, 4]:
            raise HTTPException(status_code=400, detail="无效的状态值，必须是1-4之间")
        
        # 更新问题状态
        problem_repo = ProblemRepository(db)
        success = problem_repo.update_problem_status(
            problem_id=problem_id,
            status=status
        )
        
        db.commit()
        
        if not success:
            raise HTTPException(status_code=404, detail="问题不存在")
        
        print(f"[API] 更新单个问题状态: task_id={task_id}, problem_id={problem_id}, status={status}")
        
        return {
            "success": True,
            "message": "问题状态更新成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"[API] 更新问题状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新问题状态失败: {str(e)}")


@router.get("/{task_id}/problems/status/statistics")
async def get_problem_status_statistics(
    task_id: str,
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
        # 获取问题状态统计
        problem_repo = ProblemRepository(db)
        statistics = problem_repo.get_problem_status_statistics(task_id)
        
        print(f"[API] 获取问题状态统计: task_id={task_id}, statistics={statistics}")
        
        return {
            "success": True,
            "data": {
                "task_id": task_id,
                "statistics": statistics,
                "status_descriptions": {
                    "1": "新发现（绿色）",
                    "2": "已查看（灰色）",
                    "3": "已过滤（灰色）",
                    "4": "已标记（蓝色）"
                }
            },
            "message": "获取统计信息成功"
        }
        
    except Exception as e:
        print(f"[API] 获取问题状态统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取问题状态统计失败: {str(e)}")


@router.post("/{task_id}/problems/status/batch")
async def batch_update_problem_status(
    task_id: str,
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
            success = problem_repo.update_problem_status(
                problem_id=problem_id,
                status=status
            )
            if success:
                total_updated += 1
        
        db.commit()
        
        print(f"[API] 批量更新问题状态成功: task_id={task_id}, count={total_updated}")
        
        return {
            "success": True,
            "message": "批量更新成功",
            "updated_count": total_updated
        }
        
    except Exception as e:
        db.rollback()
        print(f"[API] 批量更新问题状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量更新失败: {str(e)}")

