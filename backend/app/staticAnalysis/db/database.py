"""兼容 shim：canonical 实现在 normalModeC.database。"""
from app.staticAnalysis.normalModeC.database.database import (  # noqa: F401
    BASE_DIR,
    DATABASE_URL,
    Base,
    SessionLocal,
    ScopedSession,
    engine,
    get_db,
    get_db_session,
    get_scoped_session,
    init_db,
)
