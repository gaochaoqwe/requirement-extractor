"""PostgreSQL数据库配置 - 光电知识系统（独立模块）

 对齐 app.codeReview.ConfigurationItem.db.database 的实现风格：
 - SQLAlchemy engine + QueuePool
 - SessionLocal + get_db 依赖注入
 - init_database + migrate_database 轻量迁移
 """

import os
from pathlib import Path
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

# 尝试加载.env文件
try:
    from dotenv import load_dotenv

    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

# PostgreSQL数据库配置
POSTGRES_HOST = os.getenv("OPTO_POSTGRES_HOST", os.getenv("POSTGRES_HOST", "localhost"))
POSTGRES_PORT = os.getenv("OPTO_POSTGRES_PORT", os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("OPTO_POSTGRES_DB", os.getenv("POSTGRES_DB", "opto_knowledge"))
POSTGRES_USER = os.getenv("OPTO_POSTGRES_USER", os.getenv("POSTGRES_USER", "opto_knowledge"))
POSTGRES_PASSWORD = os.getenv("OPTO_POSTGRES_PASSWORD", os.getenv("POSTGRES_PASSWORD", "123456"))

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    poolclass=QueuePool,
    pool_size=50,
    max_overflow=10,
    pool_timeout=60,
    pool_recycle=3600,
    pool_reset_on_return='rollback',
    connect_args={
        "connect_timeout": 10,
        "options": "-c timezone=Asia/Shanghai",
    },
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


@contextmanager
def get_db_session() -> Session:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database():
    """初始化数据库"""
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    migrate_database()
    seed_database()


def migrate_database():
    """轻量迁移：为后续扩展预留"""
    try:
        with engine.connect() as conn:
            conn.commit()
    except Exception:
        return


def seed_database():
    """初始化默认入口节点（仅在为空时插入）"""
    from .models import OptoKnowledgeNode

    default_domains = [
        ("turret", "转塔"),
        ("countermeasure", "对抗告警"),
        ("optoradar", "光雷"),
        ("pod", "吊舱"),
    ]

    db = SessionLocal()
    try:
        for domain, name in default_domains:
            exists = (
                db.query(OptoKnowledgeNode)
                .filter(OptoKnowledgeNode.domain == domain)
                .filter(OptoKnowledgeNode.type == "Product")
                .filter(OptoKnowledgeNode.name == name)
                .first()
            )
            if exists:
                continue

            db.add(
                OptoKnowledgeNode(
                    domain=domain,
                    type="Product",
                    name=name,
                    summary=None,
                    content_json=None,
                    plain_text=None,
                    tags=None,
                )
            )
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def reset_database():
    Base.metadata.drop_all(bind=engine)
    init_database()


def check_database():
    init_database()
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))


if __name__ == "__main__":
    check_database()
