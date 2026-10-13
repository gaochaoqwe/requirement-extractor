"""旧共享 API 包保留为空壳，避免历史 import 报错。"""
from fastapi import APIRouter
from .endpoints import analysis_router

router = APIRouter()
router.include_router(analysis_router)
