"""
API 端点模块
"""
from fastapi import APIRouter

# 导入各个路由模块
from .download_result import router as download_router
from .start_analysis import router as start_router
from .task_progress import router as progress_router
from .upload_file import router as upload_router
from .business_review import router as business_router

# 创建主路由
router = APIRouter()

# 包含各个子路由
router.include_router(download_router)
router.include_router(start_router)
router.include_router(progress_router)
router.include_router(upload_router)
router.include_router(business_router)

# 导出为 analysis_router
analysis_router = router
