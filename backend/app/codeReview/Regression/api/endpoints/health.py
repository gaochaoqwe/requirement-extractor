"""
Health Check API Endpoint
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/health", summary="Health check")
def health_check():
    """
    健康检查端点
    
    Returns:
        dict: 服务状态信息
    """
    return {
        "status": "healthy",
        "service": "Regression Code Review",
        "version": "1.0.0"
    } 