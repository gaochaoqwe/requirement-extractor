"""
问题状态SSE推送端点
用于实时推送问题状态更新
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import asyncio
import json
from datetime import datetime

from ...db.deps import get_db
from ...db.repository.task_repo import TaskRepository
from ...db.repository.problem_repo import ProblemRepository
from ...utils.logger import log_debug, log_info, log_error

router = APIRouter()


async def problem_status_event_generator(task_id: int, db: Session):
    """
    生成问题状态更新事件
    
    每60秒推送一次当前任务的问题状态统计
    """
    try:
        task_repo = TaskRepository(db)
        problem_repo = ProblemRepository(db)
        
        # 验证任务是否存在
        task = task_repo.get_task(task_id)
        if not task:
            yield f"data: {json.dumps({'error': '任务不存在'})}\n\n"
            return
        
        log_info(f"开始SSE推送: task_id={task_id}", "problem_status_stream")
        
        while True:
            try:
                # 获取问题状态统计
                statistics = problem_repo.get_problem_status_statistics(task_id)
                
                # 构建事件数据
                event_data = {
                    "task_id": task_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "statistics": statistics,
                    "status_descriptions": {
                        "1": "新发现（绿色）",
                        "2": "已查看（灰色）",
                        "3": "已过滤（灰色）",
                        "4": "已标记"
                    }
                }
                
                # 发送SSE事件
                yield f"data: {json.dumps(event_data)}\n\n"
                
                log_debug(f"SSE推送统计数据: task_id={task_id}, statistics={statistics}", "problem_status_stream")
                
                # 等待60秒
                await asyncio.sleep(60)
                
            except Exception as e:
                log_error(f"SSE推送出错: task_id={task_id}", "problem_status_stream", e)
                error_data = {
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
                yield f"data: {json.dumps(error_data)}\n\n"
                await asyncio.sleep(60)
                
    except Exception as e:
        log_error(f"SSE生成器初始化失败: task_id={task_id}", "problem_status_stream", e)
        yield f"data: {json.dumps({'error': str(e)})}\n\n"


@router.get("/{task_id}/problems/status/stream")
async def stream_problem_status(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    SSE端点：实时推送问题状态统计
    
    每60秒推送一次最新的问题状态统计信息
    
    Args:
        task_id: 任务ID
        db: 数据库会话
    
    Returns:
        SSE流
    """
    return StreamingResponse(
        problem_status_event_generator(task_id, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用Nginx缓冲
        }
    )


@router.get("/functionReview/{task_id}/problems/status/stream")
async def stream_problem_status_function_review(
    task_id: int,
    db: Session = Depends(get_db)
):
    return await stream_problem_status(task_id=task_id, db=db)

