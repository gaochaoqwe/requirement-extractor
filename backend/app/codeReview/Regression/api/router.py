from fastapi import APIRouter

# 导入各个路由模块
from .endpoints import (
    upload_file,
    start_analysis,
    task_progress,
    download_result,
    codemap,
    health
)

# 创建主路由
regression_review_router = APIRouter()

# 包含所有端点
regression_review_router.include_router(upload_file.router, tags=["file"])
regression_review_router.include_router(start_analysis.router, tags=["analysis"])
regression_review_router.include_router(task_progress.router, tags=["task"])
regression_review_router.include_router(download_result.router, tags=["download"])
regression_review_router.include_router(codemap.router, tags=["codemap"])
regression_review_router.include_router(health.router, tags=["health"])

# 为了兼容性，创建一个别名
code_review_router = regression_review_router

# 记录路由信息到stderr
import sys
sys.stderr.write(f"回归测试代码审查路由注册成功，包含 {len(regression_review_router.routes)} 个端点\n")
for r in regression_review_router.routes:
    sys.stderr.write(f"  - {r.methods} {r.path}\n") 