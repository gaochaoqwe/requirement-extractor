"""
文档审查回归测试数据库连接和会话管理
"""
import sys
import os
from typing import Generator
from contextlib import contextmanager
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from pathlib import Path

# 判断运行环境，设置数据库路径
if getattr(sys, 'frozen', False):  # PyInstaller 环境
    BASE_DIR = Path(sys.executable).resolve().parent / "_internal" / "app" / "documentReview" / "Regression" / "db"
else:
    # 开发环境：数据库文件放置在当前文件所在目录
    BASE_DIR = Path(__file__).parent

# 确保目录存在
BASE_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = BASE_DIR / "regressionReview.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# 确保SQLite外键约束生效
def _fk_pragma_on_connect(dbapi_con, con_record):
    if "sqlite" in DATABASE_URL:
        cursor = dbapi_con.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    pool_pre_ping=True,  # 启用连接健康检查
    echo=os.getenv("SQL_ECHO", "false").lower() == "true"  # 通过环境变量控制SQL日志
)

# 为SQLite添加外键支持
event.listen(engine, 'connect', _fk_pragma_on_connect)

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 创建线程安全的会话工厂
ScopedSession = scoped_session(SessionLocal)

# 声明基类
Base = declarative_base()

@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话的上下文管理器
    
    使用示例:
    with get_db() as db:
        # 使用db进行数据库操作
        pass
    
    或者使用FastAPI依赖注入:
    def some_endpoint(db: Session = Depends(get_db)):
        # 使用db进行数据库操作
        pass
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def get_db_session() -> Generator[Session, None, None]:
    """
    获取数据库会话生成器
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_scoped_session() -> Session:
    """
    获取线程作用域的数据库会话
    """
    return ScopedSession()

def init_db(drop_all: bool = False) -> None:
    """
    初始化数据库，创建所有表
    
    Args:
        drop_all: 是否删除所有已存在的表
    """
    # 导入所有模型，确保它们被注册到Base.metadata中
    try:
        from .models.review_session import ReviewSession
        from .models.regression_result import RegressionResult
    except ImportError:
        # 如果相对导入失败，尝试绝对导入
        import sys
        current_dir = Path(__file__).parent
        sys.path.insert(0, str(current_dir))
        from models.review_session import ReviewSession
        from models.regression_result import RegressionResult
    
    if drop_all:
        import sys
        sys.stderr.write("警告：删除所有数据库表...\n")
        Base.metadata.drop_all(bind=engine)
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    sys.stderr.write(f"文档审查回归测试数据库表已初始化，数据库位置: {DATABASE_URL}\n")

if __name__ == "__main__":
    # 当脚本直接运行时，初始化数据库
    init_db(drop_all=False)
    import sys
    sys.stderr.write("数据库初始化完成，表结构已创建\n")
    
    # 显示所有表名
    import sqlite3
    from pathlib import Path
    db_path = str(DATABASE_PATH)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    sys.stderr.write("数据库中的表:\n")
    for table in tables:
        sys.stderr.write(f"- {table[0]}\n")
    conn.close() 