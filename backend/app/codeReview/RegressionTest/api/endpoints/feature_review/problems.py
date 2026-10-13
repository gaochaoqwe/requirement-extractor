"""
功能审查问题接口
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ....db.deps import get_db
from ....db.repository.feature_repo import FeatureRepository, FeatureReviewProblemRepository

router = APIRouter()

@router.get("/problems/{feature_id}")
async def get_feature_problems(feature_id: int, db: Session = Depends(get_db)):
    """
    获取指定功能点的问题列表
    
    Args:
        feature_id: 功能点ID
        db: 数据库会话
        
    Returns:
        功能点信息和问题列表
    """
    try:
        feature_repo = FeatureRepository(db)
        problem_repo = FeatureReviewProblemRepository(db)
        
        # 确保表结构存在
        try:
            feature_repo._ensure_schema()
        except Exception as e:
            print(f"[get_feature_problems] _ensure_schema warning (feature): {e}")
        
        try:
            problem_repo._ensure_schema()
        except Exception as e:
            print(f"[get_feature_problems] _ensure_schema warning (problem): {e}")
        
        feature = feature_repo.get_feature(feature_id)
        if not feature:
            raise HTTPException(status_code=404, detail=f"功能点 {feature_id} 不存在")
        
        problems = problem_repo.get_problems_by_feature(feature_id)
        
        return {
            "feature": feature.to_dict(),
            "problems": [problem.to_dict() for problem in problems]
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"获取功能点问题失败: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=500, detail=f"获取功能点问题失败: {str(e)}")
