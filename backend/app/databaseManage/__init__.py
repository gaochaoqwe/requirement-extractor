"""
数据库管理聚合包

提供对动态数据库管理(dynamicDatabaseManage)与静态数据库管理(staticDatabaseManage)子包的汇总入口。
"""

try:
    from fastapi import APIRouter

    router = APIRouter()

    _init_fns = []

    try:
        from .dynamicDatabaseManage import router as dynamic_router, init_db as dynamic_init_db  # noqa: F401
        if dynamic_router is not None:
            router.include_router(dynamic_router)
        if callable(dynamic_init_db):
            _init_fns.append(dynamic_init_db)
    except Exception:
        pass

    try:
        from .optoKnowledge import router as opto_router, init_db as opto_init_db  # noqa: F401
        if opto_router is not None:
            router.include_router(opto_router)
        if callable(opto_init_db):
            _init_fns.append(opto_init_db)
    except Exception:
        pass

    try:
        from .automationDashboard import router as automation_router, init_db as automation_init_db  # noqa: F401
        if automation_router is not None:
            router.include_router(automation_router)
        if callable(automation_init_db):
            _init_fns.append(automation_init_db)
    except Exception:
        pass

    def init_db():
        for fn in _init_fns:
            try:
                fn()
            except Exception:
                continue

except Exception:
    router = None

    def init_db():
        return None
