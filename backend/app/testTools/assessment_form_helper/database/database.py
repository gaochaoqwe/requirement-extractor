"""
数据库连接和初始化
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from ..models.models import Base
from ..config.config import DATABASE_URL

# 创建数据库引擎 - 添加连接池和超时配置
engine = create_engine(
    DATABASE_URL, 
    connect_args={
        "check_same_thread": False,
        "timeout": 5  # 5秒连接超时
    },
    pool_pre_ping=True,  # 连接前检查
    pool_recycle=300,    # 5分钟回收连接
    echo=False
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_database():
    """初始化数据库表"""
    Base.metadata.create_all(bind=engine)

def get_db() -> Session:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_session() -> Session:
    """直接获取数据库会话（用于非FastAPI上下文）"""
    return SessionLocal() 