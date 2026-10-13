"""
功能点审查进度查询API
"""
from fastapi import APIRouter, HTTPException
from ....service.feature_review import feature_runner

router = APIRouter()


@router.get("/progress/{task_id}")
async def get_feature_review_progress(task_id: int):
    """
    获取功能点审查进度
    
    返回:
    {
        "status": "processing|completed|failed",
        "progress": 60,  // 0-100
        "current_step": "正在AI审查...",
        "logs": [],
        // 兼容旧格式
        "total": 10,
        "completed": 3,
        "current_feature": "用户登录",
        "message": "正在分析功能点: 用户登录"
    }
    """
    try:
        progress_data = feature_runner.get_progress(task_id)
        
        # 计算百分比进度
        total = progress_data.get("total", 1)
        completed = progress_data.get("completed", 0)
        progress_percent = int((completed / total * 100)) if total > 0 else 0
        
        # 构建统一的返回格式
        result = {
            "status": progress_data.get("status", "idle"),
            "progress": progress_percent,
            "current_step": progress_data.get("message", ""),
            "logs": progress_data.get("logs", []),
            # 保留原有字段以兼容
            "total": total,
            "completed": completed,
            "current_feature": progress_data.get("current_feature", ""),
            "message": progress_data.get("message", "")
        }
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取进度失败: {str(e)}")

