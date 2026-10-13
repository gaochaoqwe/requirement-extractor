"""
静态分析过滤工具PostgreSQL数据库配置和连接

功能：
1. 提供数据库连接和会话管理
2. 初始化数据库表结构
3. 执行数据库迁移
"""
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from pathlib import Path
import sys

# 添加项目根目录到路径
current_file = Path(__file__).resolve()
db_dir = current_file.parent
filter_dir = db_dir.parent
static_analysis_dir = filter_dir.parent
app_dir = static_analysis_dir.parent
backend_dir = app_dir.parent
project_root = backend_dir.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.staticAnalysis.filterFpga.database.postgresql_config import DATABASE_URL
from app.staticAnalysis.filterFpga.database.postgresql_models import Base
from app.staticAnalysis.filterFpga.utils.logger import setup_module_logger

logger = setup_module_logger(__name__, "postgresql_database.log")

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=50,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

# 创建线程安全的会话工厂
SessionLocal = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)

def create_tables():
    """创建数据库表"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("PostgreSQL数据库表创建成功")
        return True
    except Exception as e:
        logger.error(f"创建数据库表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

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
        logger.info("开始初始化PostgreSQL数据库...")
        
        # 创建所有表
        create_tables()
        
        # 执行数据库迁移（添加新字段）
        migrate_database()
        
        logger.info("PostgreSQL数据库初始化完成")
        return True
    except Exception as e:
        logger.error(f"PostgreSQL数据库初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def migrate_database():
    """数据库迁移 - 添加新字段（如果需要）"""
    try:
        logger.info("检查数据库迁移...")
        
        with engine.connect() as conn:
            # 检查并添加 problem_status 字段（如果不存在）
            try:
                conn.execute(text("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns 
                            WHERE table_name='static_analysis_issues' 
                            AND column_name='problem_status'
                        ) THEN
                            ALTER TABLE static_analysis_issues 
                            ADD COLUMN problem_status INTEGER DEFAULT 1 NOT NULL;
                            CREATE INDEX IF NOT EXISTS idx_static_analysis_issues_status 
                            ON static_analysis_issues(problem_status);
                        END IF;
                    END $$;
                """))
                conn.commit()
                logger.info("数据库迁移检查完成")
            except Exception as e:
                logger.debug(f"迁移检查信息(static_analysis_issues): {e}")

            # 检查并添加 fpga_rules.accuracy_type 字段（如果不存在）
            try:
                conn.execute(text("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name='fpga_rules'
                            AND column_name='accuracy_type'
                        ) THEN
                            ALTER TABLE fpga_rules
                            ADD COLUMN accuracy_type VARCHAR(20) NOT NULL DEFAULT 'accurate';
                            CREATE INDEX IF NOT EXISTS idx_fpga_rules_accuracy ON fpga_rules(accuracy_type);
                        END IF;
                    END $$;
                """))
                conn.commit()
            except Exception as e:
                logger.debug(f"迁移检查信息(fpga_rules.accuracy_type): {e}")

            # 检查并添加 fpga_rules.is_selected 字段（如果不存在）
            try:
                conn.execute(text("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name='fpga_rules'
                            AND column_name='is_selected'
                        ) THEN
                            ALTER TABLE fpga_rules
                            ADD COLUMN is_selected BOOLEAN DEFAULT TRUE;
                            CREATE INDEX IF NOT EXISTS idx_fpga_rules_is_selected ON fpga_rules(is_selected);
                            -- 初始化所有现有规则的 is_selected 为 TRUE
                            UPDATE fpga_rules SET is_selected = TRUE WHERE is_selected IS NULL;
                        END IF;
                    END $$;
                """))
                conn.commit()
                logger.info("数据库迁移: is_selected 字段检查完成")
            except Exception as e:
                logger.debug(f"迁移检查信息(fpga_rules.is_selected): {e}")

        logger.info("PostgreSQL数据库迁移完成")
        return True
    except Exception as e:
        logger.error(f"PostgreSQL数据库迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_connection():
    """测试数据库连接"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("PostgreSQL数据库连接测试成功")
            return True
    except Exception as e:
        logger.error(f"PostgreSQL数据库连接测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("="*70)
    print("静态分析过滤工具PostgreSQL数据库初始化")
    print("="*70)
    print()
    
    # 测试连接
    print("[1/2] 测试数据库连接...")
    if test_connection():
        print("    OK 连接成功")
    else:
        print("    ERROR 连接失败")
        sys.exit(1)
    
    print()
    
    # 初始化数据库
    print("[2/2] 初始化数据库表...")
    if init_database():
        print("    OK 初始化成功")
    else:
        print("    ERROR 初始化失败")
        sys.exit(1)
    
    print()
    print("="*70)
    print("数据库初始化完成！")
    print("="*70)

