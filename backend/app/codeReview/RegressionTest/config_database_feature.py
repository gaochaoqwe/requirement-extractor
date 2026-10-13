"""
功能审查数据库配置模块

直接使用PostgreSQL数据库，不再使用SQLite
"""
from .db.database_feature import (
    engine,
    SessionLocal,
    Base,
    get_feature_db_session,
    get_feature_db,
    init_feature_database,
    reset_feature_database,
    check_feature_database,
    DATABASE_URL,
    get_connection_info
)

print("[OK] 功能审查使用PostgreSQL数据库")

# 导出所有数据库操作接口
__all__ = [
    'engine',
    'SessionLocal',
    'Base',
    'get_feature_db_session',
    'get_feature_db',
    'init_feature_database',
    'reset_feature_database',
    'check_feature_database',
    'DATABASE_URL',
    'get_connection_info'
]

