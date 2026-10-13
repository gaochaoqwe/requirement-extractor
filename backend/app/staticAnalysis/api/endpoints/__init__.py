"""旧共享 analysis 端点已下线，路由迁入 normalModeC / normalModeFpga。"""
from fastapi import APIRouter

router = APIRouter()
analysis_router = router
