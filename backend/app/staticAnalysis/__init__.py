"""
Static Analysis Package
仅保留：filter / filterFpga / normalModeC / normalModeFpga
"""
from fastapi import APIRouter
from .filter.api.api import router as filter_router
from .filterFpga.api.api import router as filter_fpga_router
from .normalModeC.api.api import router as normal_mode_c_router
from .normalModeFpga.api.api import router as normal_mode_fpga_router

router = APIRouter()

# 工具模式
router.include_router(filter_router, prefix="/filter", tags=["static-analysis-filter"])
router.include_router(filter_fpga_router, prefix="/filterFpga", tags=["static-analysis-filter-fpga"])

# 普通模式
router.include_router(normal_mode_c_router, prefix="/normalModeC", tags=["static-analysis-normal-c"])
router.include_router(normal_mode_fpga_router, prefix="/normalModeFpga", tags=["static-analysis-normal-fpga"])

static_analysis_router = router
