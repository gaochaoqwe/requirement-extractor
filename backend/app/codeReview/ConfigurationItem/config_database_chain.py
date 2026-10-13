"""
链路审查数据库配置模块

直接使用PostgreSQL数据库，不再使用SQLite
"""
from .db.database_chain import (
    engine,
    SessionLocal,
    Base,
    get_chain_db_session,
    get_chain_db,
    init_chain_database,
    reset_chain_database,
    check_chain_database,
    DATABASE_URL,
    get_connection_info
)

print("[OK] 链路审查使用PostgreSQL数据库")

# 导出所有数据库操作接口
__all__ = [
    'engine',
    'SessionLocal',
    'Base',
    'get_chain_db_session',
    'get_chain_db',
    'init_chain_database',
    'reset_chain_database',
    'check_chain_database',
    'DATABASE_URL',
    'get_connection_info'
]

