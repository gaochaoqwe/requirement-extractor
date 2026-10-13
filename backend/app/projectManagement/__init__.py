from fastapi import FastAPI
from .api import router as project_api_router # 导入来自api包的router

# 创建一个专用于项目管理的FastAPI应用实例
pm_app = FastAPI(
    title="项目管理API",
    description="管理项目及其关联文档的API",
    version="0.1.0",
    openapi_url="/openapi.json", 
    docs_url="/docs",
    redoc_url="/redoc"
)

# 包含API路由器，确保路由能够正确处理
pm_app.include_router(project_api_router)

# The main export from this module for integration will be 'pm_app'.
