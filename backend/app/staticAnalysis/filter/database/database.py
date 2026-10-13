"""
静态分析问题过滤工具数据库配置

支持SQLite和PostgreSQL两种数据库
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from app.staticAnalysis.filter.config.config import DATABASE_URL, DATABASE_TYPE, USE_POSTGRESQL
from app.staticAnalysis.filter.models.models import Base
import threading

# 线程安全的数据库引擎创建锁
_engine_lock = threading.Lock()
_engine = None

def get_engine():
    """获取或创建数据库引擎（线程安全）"""
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                # 根据数据库类型创建引擎
                if USE_POSTGRESQL:
                    # PostgreSQL引擎配置
                    _engine = create_engine(
                        DATABASE_URL,
                        poolclass=QueuePool,
                        pool_size=10,
                        max_overflow=20,
                        pool_pre_ping=True,
                        pool_recycle=3600,
                        echo=False
                    )
                else:
                    # SQLite引擎配置
                    _engine = create_engine(
                        DATABASE_URL,
                        connect_args={
                            "check_same_thread": False,
                            "timeout": 30  # 增加超时时间以支持并发
                        },
                        poolclass=QueuePool,  # 使用队列池以支持并发
                        pool_size=10,  # 连接池大小
                        max_overflow=20,  # 最大溢出连接数
                        pool_pre_ping=True,
                        pool_recycle=3600,  # 1小时回收连接
                        echo=False
                    )
                    
                    # 启用 SQLite WAL 模式以提高并发性能
                    @event.listens_for(_engine, "connect")
                    def enable_wal_mode(dbapi_conn, connection_record):
                        cursor = dbapi_conn.cursor()
                        cursor.execute("PRAGMA journal_mode=WAL")
                        cursor.execute("PRAGMA synchronous=NORMAL")  # 平衡性能和安全性
                        cursor.execute("PRAGMA busy_timeout=30000")  # 30秒busy超时
                        cursor.close()
    
    return _engine

# 获取引擎
engine = get_engine()

# 确保所有表已创建（在模块导入时自动执行，幂等）
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"[ERROR] Auto-create static analysis filter tables failed: {str(e)}")

# 创建线程安全的会话工厂
SessionLocal = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)

def create_tables():
    """创建数据库表"""
    Base.metadata.create_all(bind=engine)

def get_db_session():
    """获取数据库会话"""
    return SessionLocal()

def get_db():
    """FastAPI依赖项：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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