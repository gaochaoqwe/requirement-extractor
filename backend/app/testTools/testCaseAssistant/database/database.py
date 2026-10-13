"""
testCaseAssistant（用例设计）SQLite 数据库配置
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from typing import Generator

from ..config.config import DATABASE_URL
from ..models.models import Base

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_session():
    """获取数据库会话"""
    return SessionLocal()

def get_db() -> Generator:
    """FastAPI Depends 用：获取数据库会话（自动关闭）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """创建数据库表"""
    Base.metadata.create_all(bind=engine)

def init_database():
    """初始化数据库"""
    try:
        create_tables()
        print("✅ testCaseAssistant 数据库表创建成功")
        return True
    except Exception as e:
        print(f"❌ 数据库表创建失败: {str(e)}")
        return False