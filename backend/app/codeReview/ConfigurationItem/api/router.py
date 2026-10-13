from fastapi import APIRouter

# 导入各个路由模块
from .endpoints.download_result import router as download_router
from .endpoints.start_analysis import router as start_router
from .endpoints.task_progress import router as progress_router
from .endpoints.upload_file import router as upload_router
from .endpoints.codemap import router as codemap_router
from .endpoints.business_review import router as business_router
from .endpoints.feature_review import router as feature_router
from .endpoints.progressive_memory import router as progressive_memory_router
from .endpoints.task_info import router as task_info_router
from .endpoints.marked_problems import router as marked_problems_router
from .endpoints.problem_status import router as problem_status_router
from .endpoints.problem_filter import router as problem_filter_router
from .endpoints.problem_status_stream import router as problem_status_stream_router
from .endpoints.cancel_task import router as cancel_task_router
from .endpoints.resume_task import router as resume_task_router
from .endpoints.chain_callgraph import router as chain_callgraph_router
from .endpoints.upload_requirement import router as upload_requirement_router
from .endpoints.comment_accuracy import router as comment_accuracy_router

# 创建主路由（不带前缀）
router = APIRouter()

# 包含各个子路由
router.include_router(download_router)
router.include_router(start_router)
router.include_router(progress_router)
router.include_router(upload_router)
router.include_router(codemap_router)
router.include_router(business_router)
router.include_router(feature_router)
router.include_router(progressive_memory_router)
router.include_router(task_info_router)
router.include_router(marked_problems_router)
router.include_router(problem_status_router)
router.include_router(problem_filter_router)
router.include_router(problem_status_stream_router)
router.include_router(cancel_task_router)  # 管理员取消任务
router.include_router(resume_task_router)  # 管理员恢复任务
router.include_router(chain_callgraph_router)
router.include_router(upload_requirement_router)
router.include_router(comment_accuracy_router)  # 注释准确率反馈

# 导出为 code_review_router
code_review_router = router