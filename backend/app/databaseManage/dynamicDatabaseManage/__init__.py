"""
资产管理模块
"""
try:
    from .api import router
    from .db import init_db
    from .services import RequirementService
    
    __all__ = ["router", "init_db", "RequirementService"]
except ImportError as e:
    # 如果导入失败，设置默认值避免启动错误
    print(f"警告: 动态数据库管理模块导入失败: {e}")
    router = None
    init_db = lambda: None
    RequirementService = None
    
    __all__ = ["router", "init_db", "RequirementService"] 