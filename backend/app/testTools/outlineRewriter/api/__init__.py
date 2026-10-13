from fastapi import APIRouter
from .outline_api import router as outline_router

router = APIRouter()
router.include_router(outline_router, prefix="", tags=["outline-rewriter"])
