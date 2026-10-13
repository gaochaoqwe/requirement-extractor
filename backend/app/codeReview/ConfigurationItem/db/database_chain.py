"""
PostgreSQL数据库配置 - 用于链路审查（支持高并发）

独立的链路审查数据库，避免与函数审查共享连接池
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

# PostgreSQL数据库配置 - 链路审查（共享同一个数据库）
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "code_review")  # 使用同一个数据库
POSTGRES_USER = os.getenv("POSTGRES_USER", "code_review")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "123456")

# 构建数据库URL
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# 创建数据库引擎 - 链路审查专用
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    poolclass=QueuePool,
    pool_size=20,              # 链路审查连接池（20个基础连接）
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
def get_chain_db_session() -> Session:
    """获取链路审查数据库会话的上下文管理器"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        log_error(f"链路审查数据库操作失败", "chain_postgresql", e)
        raise
    finally:
        db.close()

def get_chain_db():
    """获取链路审查数据库会话（用于依赖注入）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_chain_database():
    """初始化链路审查数据库"""
    try:
        # 导入链路审查相关模型（旧路径）
        from .models.chain_problem import ChainReviewProblem
        from .models.task import AnalysisTask
        from .models.file import AnalysisFile
        
        # 导入 models_chain.py 中的模型（包含 FunctionComment）
        from .models_chain import FunctionComment, ChainReviewProblem as ChainReviewProblem2
        from .models_chain import Base as ModelsChainBase
        
        # 用 models_chain.py 的 Base 创建其中定义的表（包含 function_comments）
        ModelsChainBase.metadata.create_all(bind=engine)
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        log_info(f"链路审查PostgreSQL数据库表已初始化，数据库: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}", "chain_postgresql")
        
    except Exception as e:
        log_error(f"链路审查PostgreSQL数据库初始化失败", "chain_postgresql", e)
        raise

def migrate_chain_database():
    """链路审查数据库迁移"""
    try:
        with engine.connect() as conn:
            # PostgreSQL支持的安全迁移
            try:
                conn.execute(text("""
                    ALTER TABLE chain_review_problems 
                    ADD COLUMN IF NOT EXISTS chain_function_description TEXT
                """))
                log_info("已添加 chain_function_description 字段", "chain_postgresql")
            except Exception as e:
                log_debug(f"chain_function_description 字段可能已存在: {e}", "chain_postgresql")
            
            conn.commit()
        log_info("链路审查PostgreSQL数据库迁移完成", "chain_postgresql")
    except Exception as e:
        log_error(f"链路审查PostgreSQL数据库迁移失败", "chain_postgresql", e)

def reset_chain_database():
    """重置链路审查数据库"""
    log_warning("警告：删除链路审查所有数据库表...", "chain_postgresql")
    Base.metadata.drop_all(bind=engine)
    init_chain_database()

def check_chain_database():
    """检查链路审查数据库连接和表结构"""
    try:
        init_chain_database()
        log_info("链路审查PostgreSQL数据库初始化完成", "chain_postgresql")
        
        # 列出所有表
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public'
            """))
            tables = result.fetchall()
            log_debug("链路审查PostgreSQL数据库中的表:", "chain_postgresql")
            for table in tables:
                log_debug(f"- {table[0]}", "chain_postgresql")
                
    except Exception as e:
        log_error(f"链路审查PostgreSQL数据库检查失败", "chain_postgresql", e)
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
    check_chain_database()

