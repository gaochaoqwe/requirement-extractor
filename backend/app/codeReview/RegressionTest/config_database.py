"""
数据库配置模块 - 函数审查

直接使用PostgreSQL数据库，不再使用SQLite
"""
from .db.database import (
    engine,
    SessionLocal,
    Base,
    get_db_session,
    get_db,
    init_database,
    migrate_database,
    reset_database,
    check_database,
    DATABASE_URL,
    get_connection_info
)

print("[OK] 函数审查使用PostgreSQL数据库")

# 导出所有数据库操作接口
__all__ = [
    'engine',
    'SessionLocal',
    'Base',
    'get_db_session',
    'get_db',
    'init_database',
    'migrate_database',
    'reset_database',
    'check_database',
    'DATABASE_URL',
    'get_connection_info'
]

