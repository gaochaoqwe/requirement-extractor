"""
功能点审查API端点
"""
from fastapi import APIRouter
from .start import router as start_router
from .progress import router as progress_router
from .codemap import router as codemap_router
from .download import router as download_router
from .directory import router as directory_router
from .problems import router as problems_router
from .features import router as features_router

router = APIRouter()
router.include_router(start_router, prefix="/feature", tags=["feature_review"])
router.include_router(progress_router, prefix="/feature", tags=["feature_review"])
router.include_router(codemap_router, prefix="/feature", tags=["feature_review"])
router.include_router(download_router, prefix="/feature", tags=["feature_review"])
router.include_router(directory_router, prefix="/feature", tags=["feature_review"])
router.include_router(problems_router, prefix="/feature", tags=["feature_review"])
router.include_router(features_router, prefix="/feature", tags=["feature_review"])

