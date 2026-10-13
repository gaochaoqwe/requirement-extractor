"""
恢复任务API端点（管理员功能）

提供暂停任务的恢复功能，支持从上次中断的位置继续执行
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ...config_database import get_db
from ...db.repository.task_repo import TaskRepository
from ...db.repository.file_repo import FileRepository
from ...db.models.task import AnalysisTask
from ...utils.task_cancel_manager import task_cancel_manager
from ...utils.logger import log_info, log_warning, log_error
import threading

router = APIRouter()


@router.post("/resume_task/{task_id}", summary="Resume a paused task")
async def resume_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    恢复暂停的任务
    
    Args:
        task_id: 任务ID
        db: 数据库会话
        
    Returns:
        dict: 操作结果
    """
    try:
        log_info(f"[任务恢复] 收到恢复任务请求: task_id={task_id}", "resume_task")
        
        task_repo = TaskRepository(db)
        task = task_repo.get_task(task_id)
        
        if not task:
            log_warning(f"[任务恢复] 任务不存在: task_id={task_id}", "resume_task")
            raise HTTPException(status_code=404, detail="任务不存在")
        
        if task.status != 'paused':
            log_warning(
                f"[任务恢复] 任务状态不是paused: task_id={task_id}, status={task.status}",
                "resume_task"
            )
            raise HTTPException(
                status_code=400,
                detail=f"任务状态为 {task.status}，只能恢复暂停状态(paused)的任务"
            )
        
        # 检查代码文件是否存在
        if not task.code_file_id:
            log_error(f"[任务恢复] 任务没有关联的代码文件: task_id={task_id}", "resume_task")
            raise HTTPException(status_code=400, detail="任务没有关联的代码文件")
        
        file_repo = FileRepository(db)
        code_file = file_repo.get_file(task.code_file_id)
        
        if not code_file:
            log_error(f"[任务恢复] 代码文件不存在: file_id={task.code_file_id}", "resume_task")
            raise HTTPException(status_code=404, detail="代码文件不存在，无法恢复任务")
        
        # 清除取消标志
        task_cancel_manager.resume_task(task_id)
        
        # 更新数据库状态为 processing
        task_repo.update_task_status(task_id, "processing")
        db.commit()
        
        log_info(f"[任务恢复] 任务状态已更新为processing: task_id={task_id}", "resume_task")
        
        # 异步启动任务恢复执行
        from ...service.ai.task_resume_runner import resume_task_execution
        
        thread = threading.Thread(
            target=resume_task_execution,
            args=(task_id, task.code_file_id),
            daemon=True
        )
        thread.start()
        
        log_info(
            f"[任务恢复] 任务已恢复执行: task_id={task_id}, task_name={task.task_name}",
            "resume_task"
        )
        
        return {
            "success": True,
            "message": f"任务 {task.task_name} 已恢复执行",
            "task_id": task_id,
            "task_name": task.task_name,
            "previous_progress": task.progress
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        log_error(f"[任务恢复] 恢复任务失败: task_id={task_id}", "resume_task", e)
        raise HTTPException(status_code=500, detail=f"恢复任务失败: {str(e)}")


@router.get("/admin/paused_tasks", summary="Get all paused tasks")
def get_paused_tasks(
    db: Session = Depends(get_db)
):
    """
    获取所有暂停的任务列表
    
    Args:
        db: 数据库会话
        
    Returns:
        dict: 包含暂停任务列表的响应
    """
    try:
        # 查询所有暂停状态的任务
        tasks = db.query(AnalysisTask).filter(
            AnalysisTask.status == 'paused'
        ).order_by(AnalysisTask.paused_at.desc()).all()
        
        task_list = []
        for task in tasks:
            task_dict = task.to_dict()
            task_dict['can_resume'] = True  # 所有暂停的任务都可以恢复
            task_list.append(task_dict)
        
        log_info(f"[管理员] 返回暂停任务列表: 共 {len(task_list)} 个任务", "get_paused_tasks")
        
        return {
            "tasks": task_list,
            "total": len(task_list)
        }
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        log_error(f"[管理员] 获取暂停任务列表失败: {error_detail}", "get_paused_tasks", e)
        raise HTTPException(status_code=500, detail=f"获取暂停任务列表失败: {str(e)}")


@router.post("/resume_all_paused_tasks", summary="Resume all paused tasks")
async def resume_all_paused_tasks(
    db: Session = Depends(get_db)
):
    """
    批量恢复所有暂停的任务
    
    Args:
        db: 数据库会话
        
    Returns:
        dict: 操作结果
    """
    try:
        log_info("[批量恢复] 收到批量恢复所有暂停任务请求", "resume_all")
        
        # 查询所有暂停的任务
        tasks = db.query(AnalysisTask).filter(
            AnalysisTask.status == 'paused'
        ).all()
        
        if not tasks:
            return {
                "success": True,
                "message": "没有暂停的任务需要恢复",
                "resumed_count": 0
            }
        
        resumed_count = 0
        failed_tasks = []
        
        for task in tasks:
            try:
                # 清除取消标志
                task_cancel_manager.resume_task(task.id)
                
                # 更新状态
                task.status = 'processing'
                
                # 启动恢复执行
                from ...service.ai.task_resume_runner import resume_task_execution
                
                thread = threading.Thread(
                    target=resume_task_execution,
                    args=(task.id, task.code_file_id),
                    daemon=True
                )
                thread.start()
                
                resumed_count += 1
                log_info(f"[批量恢复] 任务 {task.id} 已恢复", "resume_all")
                
            except Exception as e:
                failed_tasks.append({
                    "task_id": task.id,
                    "task_name": task.task_name,
                    "error": str(e)
                })
                log_error(f"[批量恢复] 恢复任务 {task.id} 失败", "resume_all", e)
        
        db.commit()
        
        result = {
            "success": True,
            "message": f"成功恢复 {resumed_count} 个任务",
            "resumed_count": resumed_count,
            "total_paused": len(tasks)
        }
        
        if failed_tasks:
            result["failed_tasks"] = failed_tasks
            result["message"] += f"，{len(failed_tasks)} 个任务恢复失败"
        
        log_info(f"[批量恢复] 批量恢复完成: {resumed_count}/{len(tasks)}", "resume_all")
        
        return result
        
    except Exception as e:
        log_error("[批量恢复] 批量恢复失败", "resume_all", e)
        raise HTTPException(status_code=500, detail=f"批量恢复失败: {str(e)}")
