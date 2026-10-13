"""
普通模式静态分析 PostgreSQL 连接（与工具模式共用同一 PostgreSQL 实例）。
表名使用 nm_ 前缀与工具模式的表隔离。
"""
import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session

from .base import Base

# 注册模型
from . import models  # noqa: F401

POSTGRES_HOST     = os.getenv("STATIC_POSTGRES_HOST",     "localhost")
POSTGRES_PORT     = os.getenv("STATIC_POSTGRES_PORT",     "5432")
POSTGRES_DB       = os.getenv("STATIC_POSTGRES_DB",       "static_analysis_filter")
POSTGRES_USER     = os.getenv("STATIC_POSTGRES_USER",     "static_analysis")
POSTGRES_PASSWORD = os.getenv("STATIC_POSTGRES_PASSWORD", "123456")

DATABASE_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
)

SessionLocal  = sessionmaker(autocommit=False, autoflush=False, bind=engine)
ScopedSession = scoped_session(SessionLocal)


@contextmanager
def get_db() -> Generator[Session, None, None]:
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
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_scoped_session() -> Session:
    return ScopedSession()


def init_db(drop_all: bool = False) -> None:
    if drop_all:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
