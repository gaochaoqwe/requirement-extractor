"""
任务信息API - 用于获取任务详情

提供任务的基本信息，包括审查类型、状态等
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from ...config_database import get_db_session  # 使用智能数据库切换模块
from ...db.models.task import AnalysisTask
from ...utils.logger import log_info, log_error

router = APIRouter()


@router.get("/tasks/{task_id}")
async def get_task_info(task_id: int) -> Dict[str, Any]:
    """
    获取任务信息
    
    Args:
        task_id: 任务ID
        
    Returns:
        任务信息字典
    """
    try:
        with get_db_session() as db:
            task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
            
            if not task:
                raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")
            
            # 判断审查类型
            analysis_type = 'function'  # 默认函数审查
            
            if task.task_name:
                if '链路审查' in task.task_name:
                    analysis_type = 'chain'
                elif '功能审查' in task.task_name or '业务审查' in task.task_name:
                    analysis_type = 'feature'
            
            # 或者根据task_description判断
            if task.task_description:
                if '链路审查' in task.task_description or '链路功能' in task.task_description:
                    analysis_type = 'chain'
                elif '项目功能级别' in task.task_description:
                    analysis_type = 'feature'
            
            log_info(f"[任务信息] 任务{task_id}类型: {analysis_type}", "task_info")
            
            return {
                "success": True,
                "task": {
                    "id": task.id,
                    "task_name": task.task_name,
                    "task_description": task.task_description,
                    "analysis_type": analysis_type,
                    "status": task.status,
                    "progress": task.progress,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "updated_at": task.updated_at.isoformat() if task.updated_at else None,
                    "code_file_id": task.code_file_id
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"[任务信息] 获取任务{task_id}失败", "task_info", e)
        raise HTTPException(status_code=500, detail=f"获取任务信息失败: {str(e)}")

