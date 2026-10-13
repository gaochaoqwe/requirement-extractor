"""maintenance 模块总路由"""

from fastapi import APIRouter

from app.maintenance.api.announcement.routes import router as announcement_router
from app.maintenance.api.feedback.routes import router as feedback_router

router = APIRouter(prefix="/maintenance", tags=["维护"])

router.include_router(announcement_router, prefix="/announcement")
router.include_router(feedback_router, prefix="/feedback")
