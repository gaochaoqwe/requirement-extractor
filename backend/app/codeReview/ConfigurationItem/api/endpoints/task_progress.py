"""
任务进度查询API端点（代码审查）
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import TimeoutError as SQLAlchemyTimeoutError
from ...db.deps import get_db
from ...db.repository import TaskRepository
from ...utils.logger import log_debug, log_warning, log_error
import time

router = APIRouter()

# 进度缓存：当数据库连接失败时使用
_progress_cache = {}

@router.get("/task/{task_id}/progress", summary="Query code review task progress")
def get_task_progress(task_id: int, db: Session = Depends(get_db)):
    print(f"[task_progress][entry] task_id={task_id}")
    """
    获取任务进度（带容错机制）
    
    容错策略：
    1. 如果数据库连接超时，返回缓存的进度
    2. 如果缓存也没有，返回默认的processing状态
    3. 确保前端不会因为数据库问题而停止轮询
    """
    try:
        task_repo = TaskRepository(db)
        db_task = task_repo.get_task(task_id)
        print(f"[task_progress][db] task_exists={db_task is not None}, task_id={task_id}")
        if not db_task:
            raise HTTPException(status_code=404, detail="Task not found")

            # 检查是否是链路审查任务（通过任务名称判断）
        # 函数审查：task_name包含"函数审查"
        # 链路审查：task_name包含"链路审查"
        # 功能审查：task_name包含"功能审查"
        is_business_review = False
        if db_task.task_name:
            # 只有链路审查才需要并行进度
            if "链路审查" in db_task.task_name:
                is_business_review = True
            # 兼容旧的任务名称
            elif "项目功能级别" in db_task.task_name:
                is_business_review = True

        log_debug(f"任务 {task_id} 审查类型判断: is_business_review={is_business_review}, task_name={db_task.task_name}", "task_progress")

        if is_business_review:
            # 并行审查模式：获取两种审查的进度，显示最慢的进度
            try:
                # 获取链路审查进度（使用链路审查专用的进度API）
                from ...service.business_review.chain_review_smart import get_chain_review_progress
                business_progress = get_chain_review_progress(task_id)
                log_debug(f"获取链路审查进度: {business_progress}", "task_progress")
                
                # 计算链路审查进度百分比
                # 链路审查返回的是overall_progress字段，直接使用
                business_percentage = business_progress.get("overall_progress", 0)
                if business_percentage is None:
                    # 如果没有overall_progress，尝试从其他字段计算
                    business_total = business_progress.get("total", 0)
                    business_completed = business_progress.get("completed", 0)
                    if business_total > 0:
                        business_percentage = min(100, int((business_completed / business_total) * 100))
                    else:
                        business_percentage = 0 if business_progress.get("status") in ["idle", "processing"] else 100
                
                # 获取函数审查进度（从数据库）
                function_percentage = db_task.progress or 0
                function_status = db_task.status or "pending"
                
                log_debug(f"函数审查进度: {function_percentage}%, 业务审查进度: {business_percentage}%", "task_progress")
                
                # 使用最慢的进度（确保两种审查都完成才显示100%）
                overall_progress = min(business_percentage, function_percentage)
                
                # 状态优先级：processing > idle > completed > pending
                if business_progress.get("status") == "processing" or function_status == "processing":
                    overall_status = "processing"
                elif business_progress.get("status") == "idle" or function_status == "idle":
                    overall_status = "idle"
                elif business_percentage >= 100 and function_percentage >= 100:
                    overall_status = "completed"
                else:
                    overall_status = "processing"
                
                # 构建综合消息
                business_msg = business_progress.get("message", "")
                function_msg = f"函数审查: {function_percentage}%"
                business_status_msg = f"链路审查: {business_percentage}%"
                
                if business_msg:
                    combined_message = f"{function_msg}, {business_status_msg} ({business_msg})"
                else:
                    combined_message = f"{function_msg}, {business_status_msg}"
                
                result = {
                    "task_id": db_task.id,
                    "status": overall_status,
                    "progress": overall_progress,
                    "message": combined_message,
                    "analysis_type": "parallel_review",
                    "details": {
                        "function_progress": function_percentage,
                        "business_progress": business_percentage,
                        "function_status": function_status,
                        "business_status": business_progress.get("status", "pending")
                    }
                }
                
                # 更新缓存
                _progress_cache[task_id] = result
                return result
                
            except Exception as e:
                log_debug(f"获取业务审查进度失败，回退到数据库进度: {e}", "task_progress")
                # 回退到数据库中的进度信息
                pass

        # 使用数据库中的进度信息（单函数审查或回退方案）
        log_debug(f"返回单函数审查进度: status={db_task.status}, progress={db_task.progress}", "task_progress")
        
        result = {
            "task_id": db_task.id,
            "status": db_task.status,
            "progress": db_task.progress,
            "analysis_type": "function_review"
        }
        print(f"[task_progress][result] task_id={task_id}, status={db_task.status}, progress={db_task.progress}")
        
        # 更新缓存
        _progress_cache[task_id] = result
        return result
        
    except SQLAlchemyTimeoutError as e:
        # 数据库连接池超时：使用缓存的进度
        log_warning(f"数据库连接池超时，使用缓存进度: task_id={task_id}", "task_progress")
        
        if task_id in _progress_cache:
            cached = _progress_cache[task_id]
            log_debug(f"返回缓存进度: {cached}", "task_progress")
            return cached
        else:
            # 没有缓存，返回默认的processing状态
            log_warning(f"没有缓存进度，返回默认状态: task_id={task_id}", "task_progress")
            return {
                "task_id": task_id,
                "status": "processing",
                "progress": 0,
                "message": "任务正在处理中，系统繁忙请稍候...",
                "analysis_type": "unknown"
            }
    
    except Exception as e:
        print(f"[task_progress][error] task_id={task_id}, error={e}")
        # 其他异常：记录错误并返回缓存或默认值
        log_error(f"获取任务进度失败: task_id={task_id}", "task_progress", e)
        
        if task_id in _progress_cache:
            cached = _progress_cache[task_id]
            log_debug(f"返回缓存进度: {cached}", "task_progress")
            return cached
        else:
            # 没有缓存，返回默认的processing状态
            return {
                "task_id": task_id,
                "status": "processing",
                "progress": 0,
                "message": "任务正在处理中，请稍候...",
                "analysis_type": "unknown"
            }
