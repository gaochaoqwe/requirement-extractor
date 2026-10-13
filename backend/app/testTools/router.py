"""
测试工具模块路由配置
"""
from fastapi import APIRouter
from .assessment_form_helper.api.api import router as assessment_router
from .static_analysis_filter.api.api import router as static_analysis_router
from .test_case_summary.api.api import router as test_case_summary_router
from .testCase2testMethod.api.api import router as test_case_reverse_router
from .testEnvironmentDiagram.api.api import router as test_environment_router
from .testCaseAssistant.api.api import router as test_case_assistant_router
from .outlineRewriter.api.api import router as outline_rewriter_router

router = APIRouter()

# 鉴定测评表单辅助工具
router.include_router(
    assessment_router, 
    prefix="/assessment-form-helper", 
    tags=["assessment-form-helper"]
)

# 静态分析问题过滤工具
router.include_router(
    static_analysis_router,
    prefix="/static-analysis-filter", 
    tags=["static-analysis-filter"]
)

# 测试用例反向推导工具
router.include_router(
    test_case_reverse_router,
    prefix="/test-case-reverse",
    tags=["test-case-reverse"]
)

# 测试用例总结工具
router.include_router(
    test_case_summary_router,
    prefix="/test-case-summary",
    tags=["test-case-summary"]
)

# 测试环境图工具
router.include_router(
    test_environment_router,
    prefix="/test-environment-diagram",
    tags=["test-environment-diagram"]
)

# 需求/用例设计（Excel助手）
router.include_router(
    test_case_assistant_router,
    prefix="/test-case-assistant",
    tags=["test-case-assistant"]
)

# 大纲二次编写工具
router.include_router(
    outline_rewriter_router,
    prefix="/outline-rewriter",
    tags=["outline-rewriter"]
)

@router.get("/list")
async def get_tools_list():
    """获取所有可用的测试工具列表"""
    # 🚀 优化：返回静态数据，提高响应速度
    tools_data = [
            {
                "id": "static_analysis_filter",
                "name": "静态分析问题过滤工具",
                "description": "上传静态分析工具扫描结果，自动过滤并生成格式化的问题单",
                "icon": "static_analysis_filter.png",
                "route": "/test-tools/static-analysis-filter",
                "status": "active"
            },
            {
                "id": "assessment_form_helper",
                "name": "充分性要求、通过准则列生成工具",
                "description": "根据表单中已有的内容，自动生成充分性要求列和通过准则列",
                "icon": "assessment_form.png",
                "route": "/test-tools/assessment-form-helper",
                "status": "active"
            },
            {
                "id": "outline_rewriter",
                "name": "鉴定测评大纲二次编写工具",
                "description": "上传大纲docx，填写各章节补充说明，AI自动生成正文内容并输出新文档",
                "icon": "outline_rewriter.png",
                "route": "/test-tools/outline-rewriter",
                "status": "active"
            }
        ]
    
    return {
        "success": True,
        "tools": tools_data
    } 