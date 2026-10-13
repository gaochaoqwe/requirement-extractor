"""
普通模式 FPGA PostgreSQL 数据库引擎和会话管理
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from pathlib import Path
import sys

current_file = Path(__file__).resolve()
db_dir = current_file.parent
normalModeFpga_dir = db_dir.parent
static_analysis_dir = normalModeFpga_dir.parent
app_dir = static_analysis_dir.parent
backend_dir = app_dir.parent
project_root = backend_dir.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.staticAnalysis.normalModeFpga.database.postgresql_config import DATABASE_URL
from app.staticAnalysis.normalModeFpga.database.postgresql_models import Base
from app.staticAnalysis.filter.utils.logger import setup_module_logger

logger = setup_module_logger(__name__, "postgresql_normalModeFpga.log")

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=50,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

SessionLocal = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)

def create_tables():
    """创建数据库表"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("普通模式FPGA PostgreSQL表创建成功")
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

def get_scoped_session():
    """获取线程安全的scoped session"""
    return SessionLocal()

def init_database():
    """初始化数据库"""
    try:
        logger.info("开始初始化普通模式FPGA PostgreSQL数据库...")
        create_tables()
        logger.info("普通模式FPGA PostgreSQL数据库初始化完成")
        return True
    except Exception as e:
        logger.error(f"普通模式FPGA PostgreSQL数据库初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_connection():
    """测试数据库连接"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("普通模式FPGA PostgreSQL数据库连接测试成功")
            return True
    except Exception as e:
        logger.error(f"普通模式FPGA PostgreSQL数据库连接测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("="*70)
    print("普通模式FPGA PostgreSQL数据库初始化")
    print("="*70)
    print()
    
    print("[1/2] 测试数据库连接...")
    if test_connection():
        print("    OK 连接成功")
    else:
        print("    ERROR 连接失败")
        sys.exit(1)
    
    print()
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
