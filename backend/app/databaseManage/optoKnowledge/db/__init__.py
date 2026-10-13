try:
    from .database import engine, SessionLocal, Base, get_db, init_database
    from . import models

    __all__ = ["engine", "SessionLocal", "Base", "get_db", "init_database", "models"]
except Exception as e:
    print(f"警告: optoKnowledge.db 导入失败: {e}")
    engine = None
    SessionLocal = None
    Base = None
    get_db = lambda: None
    init_database = lambda: None
    models = None

    __all__ = ["engine", "SessionLocal", "Base", "get_db", "init_database", "models"]
