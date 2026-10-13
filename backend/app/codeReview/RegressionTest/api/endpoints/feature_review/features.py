"""
功能点列表接口
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ....db.deps import get_db
from ....db.repository.feature_repo import FeatureRepository

router = APIRouter()

@router.get("/features/{task_id}")
async def get_task_features(task_id: int, db: Session = Depends(get_db)):
    """
    获取任务下的所有功能点
    
    Args:
        task_id: 任务ID
        db: 数据库会话
        
    Returns:
        功能点列表，每个功能点包含数据库ID
    """
    try:
        feature_repo = FeatureRepository(db)
        
        # 确保表结构存在
        try:
            feature_repo._ensure_schema()
        except Exception as e:
            print(f"[get_task_features] _ensure_schema warning: {e}")
        
        features = feature_repo.get_features_by_task(task_id)
        
        return {
            "task_id": task_id,
            "features": [feature.to_dict() for feature in features]
        }
    except Exception as e:
        import traceback
        error_detail = f"获取任务功能点失败: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=500, detail=f"获取任务功能点失败: {str(e)}")

