"""
数据库连接和会话管理
"""
import sys
import os
from typing import Generator, Optional
from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from pathlib import Path
from ..config import DATABASE_URL
import logging

# 判断运行环境，设置数据库路径
if getattr(sys, 'frozen', False):  # PyInstaller 环境
    # 数据库文件随打包结果被放置在 _internal/app/codeReview/ConfigurationItem/db 目录下
    BASE_DIR = Path(sys.executable).resolve().parent / "_internal" / "app" / "codeReview" / "ConfigurationItem" / "db"
else:
    # 开发环境：数据库文件放置在当前文件所在目录
    BASE_DIR = Path(__file__).parent

# 确保目录存在（打包环境下可能需要手动创建）
BASE_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = BASE_DIR / "codeReview.db"
# print(f"[CRITICAL] CodeReview DB 路径: {DATABASE_PATH}")

# 创建数据库引擎
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

def get_db():
    """
    获取数据库会话
    
    Yields:
        数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_scoped_session():
    """
    获取作用域会话
    
    Returns:
        作用域会话
    """
    return scoped_session(SessionLocal)()

def init_db(drop_all: bool = False):
    """
    初始化数据库，创建所有表
    
    Args:
        drop_all: 是否删除所有已存在的表
    """
    try:
        # 导入所有模型，确保它们被注册到Base中
        from .models.file import AnalysisFile
        from .models.task import AnalysisTask
        from .models.function import AnalysisFunction
        from .models.problem import AnalysisProblem
        # 导入新的模型
        from .models.regression_task import RegressionTask
        from .models.diff_mapping import DiffMapping
        
        if drop_all:
            print("警告：删除所有数据库表...")
            Base.metadata.drop_all(bind=engine)
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        
        # 检查是否需要添加新字段
        try:
            # 尝试查询新字段，如果失败则说明需要添加
            from sqlalchemy import text
            with engine.connect() as conn:
                result = conn.execute(text("SELECT regression_task_id FROM code_review_problems LIMIT 1"))
                sys.stderr.write("数据库字段 regression_task_id 已存在\n")
        except Exception as e:
            sys.stderr.write(f"需要添加新字段 regression_task_id: {e}\n")
            # 尝试添加字段
            try:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE code_review_problems ADD COLUMN regression_task_id VARCHAR(50)"))
                    conn.commit()
                    sys.stderr.write("成功添加字段 regression_task_id\n")
            except Exception as add_error:
                sys.stderr.write(f"添加字段失败: {add_error}\n")
        
        logging.info("回归测试代码审查数据库表初始化成功")
    except Exception as e:
        logging.error(f"回归测试代码审查数据库表初始化失败: {e}")
        raise

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    获取数据库会话生成器
    
    使用示例:
    db = next(get_db_session())
    try:
        # 使用db进行数据库操作
        pass
    finally:
        db.close()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    # 当脚本直接运行时，初始化数据库
    init_db(drop_all=False)
    print("数据库初始化完成，表结构已创建")
    
    # 显示所有表名
    import sqlite3
    from pathlib import Path
    db_path = str(DATABASE_PATH)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("数据库中的表:")
    for table in tables:
        print(f"- {table[0]}")
    conn.close()
