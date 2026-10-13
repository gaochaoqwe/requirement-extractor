"""
Regression模块性能统计API端点
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from ...db.database import get_db
from ...db.repository.task_repo import TaskRepository
from ...utils.performance_monitor import get_performance_summary, get_all_performance_stats

router = APIRouter()

@router.get("/performance_stats", summary="Get performance statistics for a specific task")
def get_performance_stats(
    task_id: Optional[int] = None,
    file_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    获取指定任务的性能统计信息
    
    Args:
        task_id: 任务ID (可选)
        file_id: 文件ID (可选)
        db: 数据库会话
        
    Returns:
        dict: 性能统计数据
    """
    try:
        task_repo = TaskRepository(db)
        
        # 如果提供了task_id，验证任务是否存在
        if task_id:
            task = task_repo.get_task(task_id)
            if not task:
                raise HTTPException(status_code=404, detail="任务不存在")
        
        # 获取性能统计
        stats = get_performance_summary()
        
        return {
            "task_id": task_id,
            "file_id": file_id,
            "performance_stats": stats,
            "timestamp": stats.get("timestamp")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取性能统计失败: {str(e)}")

@router.get("/performance_stats/all", summary="Get all performance statistics")
def get_all_performance_statistics():
    """
    获取所有性能统计数据
    
    Returns:
        dict: 所有性能统计数据
    """
    try:
        all_stats = get_all_performance_stats()
        summary = get_performance_summary()
        
        return {
            "summary": summary,
            "detailed_stats": all_stats,
            "categories": list(all_stats.keys())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取性能统计失败: {str(e)}")

@router.get("/performance_stats/latest", summary="Get performance statistics for the latest task")
def get_latest_performance_stats(db: Session = Depends(get_db)):
    """
    获取最新任务的性能统计信息
    
    Args:
        db: 数据库会话
        
    Returns:
        dict: 最新任务的性能统计数据
    """
    try:
        task_repo = TaskRepository(db)
        
        # 获取最新任务
        latest_task = task_repo.get_latest_task()
        if not latest_task:
            raise HTTPException(status_code=404, detail="没有找到任务")
        
        # 获取性能统计
        stats = get_performance_summary()
        
        return {
            "task_id": latest_task.id,
            "task_name": getattr(latest_task, 'task_name', ''),
            "task_status": latest_task.status,
            "performance_stats": stats,
            "task_info": {
                "created_at": latest_task.created_at.isoformat() if latest_task.created_at else None,
                "updated_at": latest_task.updated_at.isoformat() if latest_task.updated_at else None,
                "progress": getattr(latest_task, 'progress', 0)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取最新任务性能统计失败: {str(e)}") 