"""
PostgreSQL数据库配置 - 用于功能审查（支持高并发）

独立的功能审查数据库，避免与函数审查和链路审查共享连接池
直接使用PostgreSQL数据库，不再使用SQLite
"""
import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager

# 尝试加载.env文件
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # 如果没有安装dotenv，使用系统环境变量

# 导入统一的日志系统
from ..utils.logger import log_debug, log_info, log_warning, log_error

# PostgreSQL数据库配置 - 功能审查（回归测试专用数据库）
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB_REGRESSION", "code_review_regression")  # 回归测试使用独立数据库
POSTGRES_USER = os.getenv("POSTGRES_USER", "code_review")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "123456")

# 构建数据库URL
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# 创建数据库引擎 - 功能审查专用
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    poolclass=QueuePool,
    pool_size=20,              # 功能审查连接池（20个基础连接）
    max_overflow=15,           # 最大溢出连接（峰值35个连接）
    pool_timeout=60,
    pool_recycle=3600,
    pool_reset_on_return='rollback',
    connect_args={
        "connect_timeout": 10,
        "options": "-c timezone=Asia/Shanghai"  # 使用中国时区
    }
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

@contextmanager
def get_feature_db_session() -> Session:
    """获取功能审查数据库会话的上下文管理器"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        log_error(f"功能审查数据库操作失败", "feature_postgresql", e)
        raise
    finally:
        db.close()

def get_feature_db():
    """获取功能审查数据库会话（用于依赖注入）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_feature_database():
    """初始化功能审查数据库"""
    try:
        # 导入功能审查相关模型
        from .models.feature_problem import Feature, FeatureReviewProblem
        from .models.task import AnalysisTask
        from .models.file import AnalysisFile
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        log_info(f"功能审查PostgreSQL数据库表已初始化，数据库: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}", "feature_postgresql")
        
    except Exception as e:
        log_error(f"功能审查PostgreSQL数据库初始化失败", "feature_postgresql", e)
        raise

def migrate_feature_database():
    """功能审查数据库迁移"""
    try:
        with engine.connect() as conn:
            # PostgreSQL支持的安全迁移
            # 功能审查的表结构已经比较完善，这里预留迁移接口
            log_debug("功能审查数据库结构检查完成", "feature_postgresql")
            conn.commit()
        log_info("功能审查PostgreSQL数据库迁移完成", "feature_postgresql")
    except Exception as e:
        log_error(f"功能审查PostgreSQL数据库迁移失败", "feature_postgresql", e)

def reset_feature_database():
    """重置功能审查数据库"""
    log_warning("警告：删除功能审查所有数据库表...", "feature_postgresql")
    Base.metadata.drop_all(bind=engine)
    init_feature_database()

def check_feature_database():
    """检查功能审查数据库连接和表结构"""
    try:
        init_feature_database()
        log_info("功能审查PostgreSQL数据库初始化完成", "feature_postgresql")
        
        # 列出所有表
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public'
            """))
            tables = result.fetchall()
            log_debug("功能审查PostgreSQL数据库中的表:", "feature_postgresql")
            for table in tables:
                log_debug(f"- {table[0]}", "feature_postgresql")
                
    except Exception as e:
        log_error(f"功能审查PostgreSQL数据库检查失败", "feature_postgresql", e)
        raise

def get_connection_info():
    """获取数据库连接信息"""
    return {
        "host": POSTGRES_HOST,
        "port": POSTGRES_PORT,
        "database": POSTGRES_DB,
        "user": POSTGRES_USER,
        "pool_size": 20,
        "max_overflow": 15,
        "max_connections": 35
    }

if __name__ == "__main__":
    check_feature_database()

