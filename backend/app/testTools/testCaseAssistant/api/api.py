"""testCaseAssistant API（需求设计相关）"""

from fastapi import APIRouter

from .req_design_api import router as req_design_router
from .req_design_api_test_api import router as req_design_api_test_router
from .tasks_api import router as tasks_router
from .case_design_api import router as case_design_router
from .case_fill_api import router as case_fill_router
from .dynamic_issue_report_api import router as dynamic_issue_report_router
from .issue_report_opinion_api import router as issue_report_opinion_router
from .test_item_api import router as test_item_router
from .asset_reuse_selected_api import router as asset_reuse_selected_router
from ..assetReuseExport.api import router as asset_reuse_export_router
from ..agent.api import router as agent_router

router = APIRouter()

router.include_router(req_design_router, prefix="", tags=["test-case-assistant"]) 
router.include_router(req_design_api_test_router, prefix="", tags=["test-case-assistant"]) 
router.include_router(tasks_router, prefix="", tags=["test-case-assistant"])
router.include_router(case_design_router, prefix="", tags=["test-case-assistant"])
router.include_router(case_fill_router, prefix="", tags=["test-case-assistant"])
router.include_router(issue_report_opinion_router, prefix="", tags=["test-case-assistant"])
router.include_router(dynamic_issue_report_router, prefix="", tags=["test-case-assistant"])
router.include_router(test_item_router, prefix="", tags=["test-case-assistant"])
router.include_router(asset_reuse_selected_router, prefix="", tags=["test-case-assistant"])
router.include_router(asset_reuse_export_router, prefix="", tags=["test-case-assistant"])
router.include_router(agent_router, prefix="", tags=["test-case-assistant"])