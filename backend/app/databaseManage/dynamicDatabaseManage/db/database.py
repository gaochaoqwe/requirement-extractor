"""
数据库管理模块的数据库配置
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 获取当前文件所在目录（backend/app/databaseManage/db/）
DB_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_FILE = os.path.join(DB_DIR, 'asset_management.db')
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATABASE_FILE}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    echo=False  # 设置为True可以看到SQL语句
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# 依赖注入函数，用于获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 获取数据库文件路径的函数
def get_database_path():
    """返回数据库文件的完整路径"""
    return DATABASE_FILE 