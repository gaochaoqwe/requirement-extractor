from .router import regression_review_router, code_review_router

# 向外暴露与主项目一致的名称，兼容 run_fastapi 导入
analysis_router = regression_review_router 