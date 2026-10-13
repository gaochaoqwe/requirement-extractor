try:
    from fastapi import APIRouter
    from . import requirements
    
    router = APIRouter()
    
    # Include requirements-related routes
    router.include_router(requirements.router, prefix="/database-manage", tags=["Database Management"])
    
    __all__ = ["router"]
except ImportError as e:
    # 如果导入失败，设置默认值避免启动错误
    print(f"警告: API模块导入失败: {e}")
    router = None
    
    __all__ = ["router"] 