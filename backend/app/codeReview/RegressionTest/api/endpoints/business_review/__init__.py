from fastapi import APIRouter
from .start import router as start_router
from .progress import router as progress_router
from .kb import router as kb_router
from .download import router as download_router

router = APIRouter()
router.include_router(start_router, prefix="/business", tags=["business_review"])
router.include_router(progress_router, prefix="/business", tags=["business_review"])
router.include_router(kb_router, prefix="/business", tags=["business_review"])
router.include_router(download_router, prefix="/business", tags=["business_review"]) 