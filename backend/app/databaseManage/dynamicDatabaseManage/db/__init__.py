"""
数据库相关模块
"""
try:
    from .database import engine, Base, SessionLocal, get_db, get_database_path
    from .models import OptoelectronicRequirement
    from .crud import (
        get_requirement,
        get_requirements,
        get_requirements_count,
        create_requirement,
        create_requirements_batch,
        update_requirement,
        delete_requirement,
        delete_all_requirements
    )
    from .init import init_db
    
    __all__ = [
        "engine", "Base", "SessionLocal", "get_db", "get_database_path",
        "OptoelectronicRequirement",
        "get_requirement",
        "get_requirements", 
        "get_requirements_count",
        "create_requirement",
        "create_requirements_batch",
        "update_requirement",
        "delete_requirement",
        "delete_all_requirements",
        "init_db"
    ]
except ImportError as e:
    # 如果导入失败，设置默认值避免启动错误
    print(f"警告: 数据库模块导入失败: {e}")
    engine = None
    Base = None
    SessionLocal = None
    get_db = lambda: None
    get_database_path = lambda: None
    OptoelectronicRequirement = None
    get_requirement = lambda *args, **kwargs: None
    get_requirements = lambda *args, **kwargs: []
    get_requirements_count = lambda *args, **kwargs: 0
    create_requirement = lambda *args, **kwargs: None
    create_requirements_batch = lambda *args, **kwargs: []
    update_requirement = lambda *args, **kwargs: None
    delete_requirement = lambda *args, **kwargs: False
    delete_all_requirements = lambda *args, **kwargs: 0
    init_db = lambda: None
    
    __all__ = [
        "engine", "Base", "SessionLocal", "get_db", "get_database_path",
        "OptoelectronicRequirement",
        "get_requirement",
        "get_requirements", 
        "get_requirements_count",
        "create_requirement",
        "create_requirements_batch",
        "update_requirement",
        "delete_requirement",
        "delete_all_requirements",
        "init_db"
    ] 