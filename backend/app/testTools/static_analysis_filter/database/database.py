"""
静态分析问题过滤工具数据库配置
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from ..config.config import DATABASE_URL
from ..models.models import Base

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 5  # 5秒连接超时
    },
    poolclass=StaticPool,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """创建数据库表"""
    Base.metadata.create_all(bind=engine)

def get_db_session():
    """获取数据库会话"""
    return SessionLocal()

def init_database():
    """初始化数据库"""
    try:
        # 确保database目录存在
        from pathlib import Path
        db_dir = Path(__file__).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        create_tables()
        print("[OK] Static analysis filter database initialized successfully")
        return True
    except Exception as e:
        print(f"[ERROR] Static analysis filter database initialization failed: {str(e)}")
        return False 