"""
取消任务API端点（管理员功能）
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ...config_database import get_db
from ...db.repository.task_repo import TaskRepository
from ...db.models.task import AnalysisTask
from ...db.models.chain_problem import ChainReviewProblem
from ...utils.task_cancel_manager import task_cancel_manager
from ...config import ADMIN_PASSWORD
from ...utils.logger import log_info, log_warning, log_error

router = APIRouter()

class CancelTaskRequest(BaseModel):
    pause: bool = False  # 是否暂停（而非取消）


@router.post("/cancel_task/{task_id}", summary="Cancel or pause a running task (Admin only)")
def cancel_task(
    task_id: int,
    req: CancelTaskRequest,
    db: Session = Depends(get_db)
):
    """
    取消或暂停正在运行的任务（管理员功能）
    
    Args:
        task_id: 任务ID
        req: 包含管理员密码和暂停标志的请求
        db: 数据库会话
        
    Returns:
        dict: 操作结果
    """
    try:
        action = "暂停" if req.pause else "取消"
        log_info(f"[管理员操作] 收到{action}任务请求: task_id={task_id}", "cancel_task")
        
        # 检查任务是否存在
        task_repo = TaskRepository(db)
        task = task_repo.get_task(task_id)
        
        if not task:
            log_warning(f"[管理员操作] 任务不存在: task_id={task_id}", "cancel_task")
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 检查任务状态
        if task.status not in ['pending', 'processing']:
            log_warning(
                f"[管理员操作] 任务状态不支持{action}: task_id={task_id}, status={task.status}",
                "cancel_task"
            )
            raise HTTPException(
                status_code=400,
                detail=f"任务当前状态为 {task.status}，无法{action}（只能{action} pending 或 processing 状态的任务）"
            )
        
        # 根据pause标志选择操作
        if req.pause:
            # 暂停任务（持久化到数据库）
            success = task_cancel_manager.pause_task(task_id, db)
            final_status = "paused"
            message = f"任务 {task.task_name} (ID: {task_id}) 已被暂停，可在后端重启后恢复"
        else:
            # 取消任务
            success = task_cancel_manager.cancel_task(task_id)
            
            if not success:
                log_warning(
                    f"[管理员操作] 任务未注册到取消管理器，直接更新数据库状态: task_id={task_id}",
                    "cancel_task"
                )
            
            # 更新数据库状态为cancelled
            task_repo.update_task_status(task_id, "cancelled")
            db.commit()
            final_status = "cancelled"
            message = f"任务 {task.task_name} (ID: {task_id}) 已被取消"
        
        log_info(
            f"[管理员操作] 任务{action}成功: task_id={task_id}, task_name={task.task_name}",
            "cancel_task"
        )
        
        return {
            "success": True,
            "message": message,
            "task_id": task_id,
            "previous_status": task.status,
            "new_status": final_status
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        log_error(f"[管理员操作] {action}任务失败: task_id={task_id}", "cancel_task", e)
        raise HTTPException(status_code=500, detail=f"{action}任务失败: {str(e)}")


@router.get("/task/{task_id}/can_cancel", summary="Check if a task can be cancelled")
def check_can_cancel(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    检查任务是否可以被取消
    
    Args:
        task_id: 任务ID
        db: 数据库会话
        
    Returns:
        dict: 包含是否可取消的信息
    """
    try:
        task_repo = TaskRepository(db)
        task = task_repo.get_task(task_id)
        
        if not task:
            return {
                "can_cancel": False,
                "reason": "任务不存在"
            }
        
        can_cancel = task.status in ['pending', 'processing']
        reason = "" if can_cancel else f"任务状态为 {task.status}，不可取消"
        
        return {
            "can_cancel": can_cancel,
            "reason": reason,
            "task_status": task.status,
            "task_name": task.task_name
        }
        
    except Exception as e:
        log_error(f"检查任务是否可取消失败: task_id={task_id}", "check_can_cancel", e)
        raise HTTPException(status_code=500, detail=f"检查失败: {str(e)}")


@router.get("/admin/tasks", summary="Get all tasks (Admin only)")
def get_all_tasks(
    status: str = None,  # 可选的状态过滤
    limit: int = 500,  # 增加默认限制到500条，支持更多任务查看
    db: Session = Depends(get_db)
):
    """
    获取所有任务列表（管理员功能）
    
    Args:
        status: 任务状态过滤（可选）
        limit: 返回数量限制
        db: 数据库会话
        
    Returns:
        dict: 包含任务列表的响应
    """
    try:
        query = db.query(AnalysisTask)
        
        # 状态过滤
        if status:
            query = query.filter(AnalysisTask.status == status)
        
        # 按创建时间倒序排列，最新的在前面
        tasks = query.order_by(AnalysisTask.created_at.desc()).limit(limit).all()
        
        task_list = []
        for task in tasks:
            # 对chain_review任务补填total_problems（历史任务可能为0）
            if task.analysis_type == 'chain_review' and (task.total_problems or 0) == 0:
                try:
                    chain_count = db.query(ChainReviewProblem).filter(
                        ChainReviewProblem.task_id == task.id
                    ).count()
                    if chain_count > 0:
                        task.total_problems = chain_count
                        db.commit()
                except Exception as e:
                    log_info(f"[诊断] chain_review任务 id={task.id} 补填total_problems异常: {e}", "get_all_tasks")
            # 对chain_review任务补填marked_problem_count（历史数据用type='chain'存的）
            if task.analysis_type == 'chain_review' and (task.marked_problem_count or 0) == 0:
                try:
                    from ...db.models.marked_problem import MarkedProblem
                    marked_count = db.query(MarkedProblem).filter(
                        MarkedProblem.task_id == task.id,
                        MarkedProblem.analysis_type.in_(['chain', 'chain_review'])
                    ).count()
                    if marked_count > 0:
                        task.marked_problem_count = marked_count
                        task.has_marked_problems = True
                        db.commit()
                except Exception as e:
                    log_info(f"[诊断] chain_review任务 id={task.id} 补填marked_problem_count异常: {e}", "get_all_tasks")
            task_dict = task.to_dict()
            # 添加是否可取消的标志
            task_dict['can_cancel'] = task.status in ['pending', 'processing']
            task_list.append(task_dict)

        log_info(f"[管理员] 返回任务列表: 共 {len(task_list)} 个任务", "get_all_tasks")
        
        return {
            "tasks": task_list,
            "total": len(task_list)
        }
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        log_error(f"[管理员] 获取任务列表失败: {error_detail}", "get_all_tasks", e)
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")


@router.post("/cancel_my_task/{task_id}", summary="Cancel my own task (No password required)")
def cancel_my_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    用户自助取消任务（无需密码）
    
    Args:
        task_id: 任务ID
        db: 数据库会话
        
    Returns:
        dict: 操作结果
    """
    try:
        log_info(f"[用户操作] 收到取消任务请求: task_id={task_id}", "cancel_my_task")
        
        # 检查任务是否存在
        task_repo = TaskRepository(db)
        task = task_repo.get_task(task_id)
        
        if not task:
            log_warning(f"[用户操作] 任务不存在: task_id={task_id}", "cancel_my_task")
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 检查任务状态
        if task.status not in ['pending', 'processing']:
            log_warning(
                f"[用户操作] 任务状态不支持取消: task_id={task_id}, status={task.status}",
                "cancel_my_task"
            )
            raise HTTPException(
                status_code=400,
                detail=f"任务当前状态为 {task.status}，无法取消（只能取消 pending 或 processing 状态的任务）"
            )
        
        # 设置取消标志
        success = task_cancel_manager.cancel_task(task_id)
        
        if not success:
            log_warning(
                f"[用户操作] 任务未注册到取消管理器，直接更新数据库状态: task_id={task_id}",
                "cancel_my_task"
            )
        
        # 更新数据库状态
        task_repo.update_task_status(task_id, "cancelled")
        db.commit()
        
        log_info(
            f"[用户操作] 任务取消成功: task_id={task_id}, task_name={task.task_name}",
            "cancel_my_task"
        )
        
        return {
            "success": True,
            "message": f"任务已成功取消",
            "task_id": task_id,
            "task_name": task.task_name
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        log_error(f"[用户操作] 取消任务失败: task_id={task_id}, error={error_detail}", "cancel_my_task", e)
        raise HTTPException(status_code=500, detail=f"取消任务失败: {str(e)}")


@router.get("/admin/running_tasks", summary="Get running tasks (Admin only)")
def get_running_tasks(
    db: Session = Depends(get_db)
):
    """
    获取所有正在运行的任务（管理员功能）
    
    Args:
        db: 数据库会话
        
    Returns:
        dict: 包含运行中任务列表的响应
    """
    try:
        # 查询 pending 或 processing 状态的任务
        tasks = db.query(AnalysisTask).filter(
            AnalysisTask.status.in_(['pending', 'processing'])
        ).order_by(AnalysisTask.created_at.desc()).all()
        
        task_list = []
        for task in tasks:
            task_dict = task.to_dict()
            task_dict['can_cancel'] = True  # 所有运行中的任务都可以取消
            task_list.append(task_dict)
        
        log_info(f"[管理员] 返回运行中任务列表: 共 {len(task_list)} 个任务", "get_running_tasks")
        
        return {
            "tasks": task_list,
            "total": len(task_list)
        }
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        log_error(f"[管理员] 获取运行中任务列表失败: {error_detail}", "get_running_tasks", e)
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")

