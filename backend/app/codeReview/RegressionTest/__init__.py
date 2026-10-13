"""
Code Review Package
"""
from fastapi import APIRouter
from .api import analysis_router

# 创建主路由
router = APIRouter()

# 包含API路由
router.include_router(analysis_router)

# 导出路由
code_review_router = analysis_router
