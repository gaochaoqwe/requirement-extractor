"""
PostgreSQL数据库配置 - 用于函数审查（支持高并发）

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

# PostgreSQL数据库配置
# 可以通过环境变量配置，方便部署
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "code_review")  # 统一使用一个数据库
POSTGRES_USER = os.getenv("POSTGRES_USER", "code_review")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "123456")

# 构建数据库URL
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# 创建数据库引擎 - 针对高并发优化
engine = create_engine(
    DATABASE_URL,
    echo=False,  # 生产环境建议关闭SQL日志
    pool_pre_ping=True,  # 连接前测试可用性
    poolclass=QueuePool,  # 使用队列池
    pool_size=100,  # 基础连接池大小（支持100个并发连接）
    max_overflow=20,  # 最大溢出连接（峰值可达120个连接）
    pool_timeout=60,  # 获取连接的超时时间（秒）
    pool_recycle=3600,  # 连接回收时间（1小时），防止连接过期
    pool_reset_on_return='rollback',  # 连接返回池时回滚未提交的事务
    connect_args={
        "connect_timeout": 10,  # 连接超时（秒）
        "options": "-c timezone=Asia/Shanghai"  # 使用中国时区（东八区）
    }
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

@contextmanager
def get_db_session() -> Session:
    """获取数据库会话的上下文管理器"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        log_error(f"数据库操作失败", "postgresql", e)
        raise
    finally:
        db.close()

def get_db():
    """获取数据库会话（用于依赖注入）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """初始化数据库"""
    try:
        # 导入函数审查核心模型
        from .models.file import AnalysisFile
        from .models.function import AnalysisFunction
        from .models.problem import AnalysisProblem
        from .models.task import AnalysisTask
        from .models.problem_filter import ProblemFilterRule  # 导入过滤规则模型
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        log_info(f"PostgreSQL数据库表已初始化，数据库位置: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}", "postgresql")
        
        # 执行数据库迁移
        migrate_database()
        
    except Exception as e:
        log_error(f"PostgreSQL数据库初始化失败", "postgresql", e)
        raise

def migrate_database():
    """数据库迁移 - 添加新字段（如果需要）"""
    try:
        with engine.connect() as conn:
            # PostgreSQL支持ALTER TABLE IF EXISTS语法，更安全
            
            # 为functions表添加AI分析结果字段（如果不存在）
            try:
                conn.execute(text("""
                    ALTER TABLE code_review_functions 
                    ADD COLUMN IF NOT EXISTS function_description TEXT
                """))
                log_info("已添加 function_description 字段", "postgresql")
            except Exception as e:
                log_debug(f"function_description 字段可能已存在: {e}", "postgresql")
            
            try:
                conn.execute(text("""
                    ALTER TABLE code_review_functions 
                    ADD COLUMN IF NOT EXISTS commented_code TEXT
                """))
                log_info("已添加 commented_code 字段", "postgresql")
            except Exception as e:
                log_debug(f"commented_code 字段可能已存在: {e}", "postgresql")

            # 为files表添加业务功能概述字段
            try:
                conn.execute(text("""
                    ALTER TABLE code_review_files 
                    ADD COLUMN IF NOT EXISTS file_function_summary TEXT
                """))
                log_info("已添加 file_function_summary 字段", "postgresql")
            except Exception as e:
                log_debug(f"file_function_summary 字段可能已存在: {e}", "postgresql")
            
            # 【新增】为problems表添加问题状态字段
            try:
                conn.execute(text("""
                    ALTER TABLE code_review_problems 
                    ADD COLUMN IF NOT EXISTS problem_status INTEGER DEFAULT 1 NOT NULL
                """))
                log_info("已添加 problem_status 字段", "postgresql")
            except Exception as e:
                log_debug(f"problem_status 字段可能已存在: {e}", "postgresql")
            
            # 【新增】为problem_status字段添加索引（如果不存在）
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_code_review_problems_status 
                    ON code_review_problems(problem_status)
                """))
                log_info("已添加 problem_status 索引", "postgresql")
            except Exception as e:
                log_debug(f"problem_status 索引可能已存在: {e}", "postgresql")
            
            # 【新增】为problems表添加问题来源字段
            try:
                conn.execute(text("""
                    ALTER TABLE code_review_problems 
                    ADD COLUMN IF NOT EXISTS problem_source VARCHAR(64) DEFAULT 'main_review'
                """))
                conn.execute(text("""
                    UPDATE code_review_problems
                    SET problem_source = 'main_review'
                    WHERE problem_source IS NULL OR problem_source = ''
                """))
                log_info("已添加并初始化 problem_source 字段", "postgresql")
            except Exception as e:
                log_debug(f"problem_source 字段可能已存在: {e}", "postgresql")

            # 【新增】为problem_source字段添加索引（如果不存在）
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_code_review_problems_source 
                    ON code_review_problems(problem_source)
                """))
                log_info("已添加 problem_source 索引", "postgresql")
            except Exception as e:
                log_debug(f"problem_source 索引可能已存在: {e}", "postgresql")

            # 【新增】为tasks表添加任务恢复相关字段
            try:
                conn.execute(text("""
                    ALTER TABLE code_review_tasks 
                    ADD COLUMN IF NOT EXISTS paused_at TIMESTAMP NULL
                """))
                log_info("已添加 paused_at 字段", "postgresql")
            except Exception as e:
                log_debug(f"paused_at 字段可能已存在: {e}", "postgresql")
            
            try:
                conn.execute(text("""
                    ALTER TABLE code_review_tasks 
                    ADD COLUMN IF NOT EXISTS execution_context TEXT NULL
                """))
                log_info("已添加 execution_context 字段", "postgresql")
            except Exception as e:
                log_debug(f"execution_context 字段可能已存在: {e}", "postgresql")
            
            # 【新增】为tasks表添加测试人员姓名字段（2024-12-12）
            try:
                conn.execute(text("""
                    ALTER TABLE code_review_tasks 
                    ADD COLUMN IF NOT EXISTS tester_name VARCHAR(100) NULL
                """))
                log_info("已添加 tester_name 字段", "postgresql")
            except Exception as e:
                log_debug(f"tester_name 字段可能已存在: {e}", "postgresql")
            
            # 【新增】为tasks表添加注释准确率反馈相关字段（2024-12-XX）
            try:
                conn.execute(text("""
                    ALTER TABLE code_review_tasks 
                    ADD COLUMN IF NOT EXISTS comment_accuracy_rate VARCHAR(50) NULL
                """))
                log_info("已添加 comment_accuracy_rate 字段", "postgresql")
            except Exception as e:
                log_debug(f"comment_accuracy_rate 字段可能已存在: {e}", "postgresql")
            
            try:
                conn.execute(text("""
                    ALTER TABLE code_review_tasks 
                    ADD COLUMN IF NOT EXISTS comment_accuracy_feedback_at TIMESTAMP NULL
                """))
                log_info("已添加 comment_accuracy_feedback_at 字段", "postgresql")
            except Exception as e:
                log_debug(f"comment_accuracy_feedback_at 字段可能已存在: {e}", "postgresql")
            
            try:
                conn.execute(text("""
                    ALTER TABLE code_review_tasks 
                    ADD COLUMN IF NOT EXISTS clicked_function_count INTEGER DEFAULT 0
                """))
                log_info("已添加 clicked_function_count 字段", "postgresql")
            except Exception as e:
                log_debug(f"clicked_function_count 字段可能已存在: {e}", "postgresql")
            
            try:
                conn.execute(text("""
                    ALTER TABLE code_review_tasks 
                    ADD COLUMN IF NOT EXISTS feedback_delayed_count INTEGER DEFAULT 0
                """))
                log_info("已添加 feedback_delayed_count 字段", "postgresql")
            except Exception as e:
                log_debug(f"feedback_delayed_count 字段可能已存在: {e}", "postgresql")
            
            conn.commit()
        log_info("PostgreSQL数据库迁移完成", "postgresql")
    except Exception as e:
        log_error(f"PostgreSQL数据库迁移失败", "postgresql", e)

def reset_database():
    """重置数据库（删除所有表并重新创建）"""
    log_warning("警告：删除所有数据库表...", "postgresql")
    Base.metadata.drop_all(bind=engine)
    init_database()

def check_database():
    """检查数据库连接和表结构"""
    try:
        init_database()
        log_info("PostgreSQL数据库初始化完成，表结构已创建", "postgresql")
        
        # 列出所有表
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public'
            """))
            tables = result.fetchall()
            log_debug("PostgreSQL数据库中的表:", "postgresql")
            for table in tables:
                log_debug(f"- {table[0]}", "postgresql")
                
    except Exception as e:
        log_error(f"PostgreSQL数据库检查失败", "postgresql", e)
        raise

def get_connection_info():
    """获取数据库连接信息（用于调试）"""
    return {
        "host": POSTGRES_HOST,
        "port": POSTGRES_PORT,
        "database": POSTGRES_DB,
        "user": POSTGRES_USER,
        "pool_size": 30,
        "max_overflow": 20,
        "max_connections": 50
    }

if __name__ == "__main__":
    check_database()

