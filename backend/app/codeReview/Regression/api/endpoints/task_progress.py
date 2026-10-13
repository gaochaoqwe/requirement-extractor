"""
回归测试代码审查任务进度API端点
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ...db.deps import get_db
from ...db.repository import TaskRepository

router = APIRouter()

@router.get("/task_progress/{task_id}", summary="Get regression code review task progress")
def get_task_progress(task_id: str, db: Session = Depends(get_db)):
    """
    获取回归测试代码审查任务进度
    
    Args:
        task_id: 任务ID
    
    Returns:
        任务进度信息
    """
    task_repo = TaskRepository(db)
    task = task_repo.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail=f"任务不存在，ID: {task_id}")
    
    return {
        "task_id": task.id,
        "status": task.status,
        "progress": task.progress,
        "error_message": task.error_message,
        "old_file_id": task.old_file_id,
        "new_file_id": task.new_file_id,
        "report_file_id": task.report_file_id,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None
    }
