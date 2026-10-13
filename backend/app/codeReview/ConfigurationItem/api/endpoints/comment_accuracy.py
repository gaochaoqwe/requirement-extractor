"""
注释准确率反馈API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from ...db.deps import get_db
from ...db.repository.task_repo import TaskRepository
from ...utils.logger import log_info, log_error

router = APIRouter()


class CommentAccuracyFeedbackRequest(BaseModel):
    """注释准确率反馈请求"""
    accuracy_rate: str  # 50%以下、50%-70%、70%-85%、85%-95%、95%-100%


class IncrementClickedFunctionRequest(BaseModel):
    """增加点击函数计数请求"""
    pass  # 不需要额外参数


@router.post("/{task_id}/comment_accuracy_feedback")
async def submit_comment_accuracy_feedback(
    task_id: int,
    request: CommentAccuracyFeedbackRequest,
    db: Session = Depends(get_db)
):
    """
    提交注释准确率反馈
    
    Args:
        task_id: 任务ID
        request: 反馈请求
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
        
        # 验证准确率选项
        valid_rates = ["50%以下", "50%-70%", "70%-85%", "85%-95%", "95%-100%"]
        if request.accuracy_rate not in valid_rates:
            raise HTTPException(status_code=400, detail="无效的准确率选项")
        
        # 更新任务的注释准确率
        updated_task = task_repo.update_comment_accuracy(
            task_id=task_id,
            accuracy_rate=request.accuracy_rate
        )
        
        if not updated_task:
            raise HTTPException(status_code=404, detail="更新失败")
        
        log_info(
            f"注释准确率反馈成功: task_id={task_id}, rate={request.accuracy_rate}",
            "comment_accuracy_api"
        )
        
        return {
            "success": True,
            "message": "感谢您的反馈！",
            "data": {
                "task_id": task_id,
                "accuracy_rate": request.accuracy_rate,
                "feedback_at": updated_task.comment_accuracy_feedback_at.isoformat() if updated_task.comment_accuracy_feedback_at else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        log_error(f"提交注释准确率反馈失败: task_id={task_id}", "comment_accuracy_api", e)
        raise HTTPException(status_code=500, detail=f"提交反馈失败: {str(e)}")


class IncrementClickedRequest(BaseModel):
    total_override: int = None


@router.post("/{task_id}/increment_clicked_function")
async def increment_clicked_function(
    task_id: int,
    request: IncrementClickedRequest = IncrementClickedRequest(),
    db: Session = Depends(get_db)
):
    """
    增加已点击函数计数
    
    Args:
        task_id: 任务ID
        db: 数据库会话
    
    Returns:
        操作结果，包括是否需要弹出反馈框
    """
    try:
        # 验证任务是否存在
        task_repo = TaskRepository(db)
        task = task_repo.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 如果已经反馈过，不再增加计数
        if task.comment_accuracy_rate:
            return {
                "success": True,
                "data": {
                    "clicked_count": task.clicked_function_count,
                    "total_functions": request.total_override or task_repo.get_total_function_count(task_id),
                    "should_show_feedback": False,
                    "already_feedback": True
                }
            }
        
        # 增加点击计数
        updated_task = task_repo.increment_clicked_function_count(task_id)
        if not updated_task:
            raise HTTPException(status_code=404, detail="更新失败")
        
        # 获取总函数数量（链路审查可通过total_override传入叶子功能点总数）
        total_functions = request.total_override or task_repo.get_total_function_count(task_id)
        
        # 判断是否需要弹出反馈框
        clicked_count = updated_task.clicked_function_count
        delayed_count = updated_task.feedback_delayed_count or 0
        should_show_feedback = False
        feedback_trigger_point = None
        
        if total_functions > 0:
            click_percentage = (clicked_count / total_functions) * 100
            prev_percentage = ((clicked_count - 1) / total_functions) * 100 if clicked_count > 1 else 0
            
            # 根据延迟次数决定触发点
            # delayed_count = 0: 15%时触发
            # delayed_count = 1: 30%时触发
            # delayed_count = 2: 50%时触发
            if delayed_count == 0:
                # 第一次：15%时触发
                if click_percentage > 15 and prev_percentage <= 15:
                    should_show_feedback = True
                    feedback_trigger_point = "15%"
            elif delayed_count == 1:
                # 第二次：30%时触发
                if click_percentage > 30 and prev_percentage <= 30:
                    should_show_feedback = True
                    feedback_trigger_point = "30%"
            elif delayed_count == 2:
                # 第三次：50%时触发
                if click_percentage >= 50 and prev_percentage < 50:
                    should_show_feedback = True
                    feedback_trigger_point = "50%"
        
        return {
            "success": True,
            "data": {
                "clicked_count": clicked_count,
                "total_functions": total_functions,
                "click_percentage": round((clicked_count / total_functions * 100), 2) if total_functions > 0 else 0,
                "should_show_feedback": should_show_feedback,
                "already_feedback": False,
                "delayed_count": delayed_count,
                "feedback_trigger_point": feedback_trigger_point
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        log_error(f"增加点击函数计数失败: task_id={task_id}", "comment_accuracy_api", e)
        raise HTTPException(status_code=500, detail=f"操作失败: {str(e)}")


@router.get("/{task_id}/comment_accuracy_status")
async def get_comment_accuracy_status(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    获取注释准确率反馈状态
    
    Args:
        task_id: 任务ID
        db: 数据库会话
    
    Returns:
        反馈状态信息
    """
    try:
        # 验证任务是否存在
        task_repo = TaskRepository(db)
        task = task_repo.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 获取总函数数量
        total_functions = task_repo.get_total_function_count(task_id)
        
        return {
            "success": True,
            "data": {
                "task_id": task_id,
                "clicked_count": task.clicked_function_count or 0,
                "total_functions": total_functions,
                "click_percentage": round((task.clicked_function_count / total_functions * 100), 2) if total_functions > 0 else 0,
                "comment_accuracy_rate": task.comment_accuracy_rate,
                "feedback_at": task.comment_accuracy_feedback_at.isoformat() if task.comment_accuracy_feedback_at else None,
                "has_feedback": task.comment_accuracy_rate is not None,
                "delayed_count": task.feedback_delayed_count or 0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"获取注释准确率状态失败: task_id={task_id}", "comment_accuracy_api", e)
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


@router.post("/{task_id}/delay_feedback")
async def delay_feedback(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    延迟反馈（用户点击"稍后反馈"）
    
    Args:
        task_id: 任务ID
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
        
        # 增加延迟计数
        updated_task = task_repo.increment_feedback_delayed_count(task_id)
        if not updated_task:
            raise HTTPException(status_code=404, detail="更新失败")
        
        delayed_count = updated_task.feedback_delayed_count
        
        # 确定下次触发点
        next_trigger = None
        if delayed_count == 1:
            next_trigger = "30%"
        elif delayed_count == 2:
            next_trigger = "50%"
        
        log_info(
            f"用户延迟反馈: task_id={task_id}, delayed_count={delayed_count}, next_trigger={next_trigger}",
            "comment_accuracy_api"
        )
        
        return {
            "success": True,
            "message": f"已延迟反馈，将在{next_trigger}时再次提醒" if next_trigger else "已延迟反馈",
            "data": {
                "delayed_count": delayed_count,
                "next_trigger": next_trigger
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        log_error(f"延迟反馈失败: task_id={task_id}", "comment_accuracy_api", e)
        raise HTTPException(status_code=500, detail=f"操作失败: {str(e)}")
