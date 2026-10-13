"""maintenance 模块数据库访问与建表（PostgreSQL / psycopg2）

说明：
- 复用 auth 模块的 PostgreSQL 环境变量（POSTGRES_HOST/PORT/DB/USER/PASSWORD）
- 在同一个数据库中创建 maintenance 相关表
- 提供幂等的 init_database() 用于启动时初始化
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

# 尝试加载 maintenance 模块自己的 .env（不覆盖已存在环境变量，避免污染其他模块）
try:
    from dotenv import load_dotenv

    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

# maintenance 模块独立数据库配置（优先读取 MAINT_POSTGRES_*，回退到全局 POSTGRES_*）
POSTGRES_HOST = os.getenv("MAINT_POSTGRES_HOST", os.getenv("POSTGRES_HOST", "localhost"))
POSTGRES_PORT = int(os.getenv("MAINT_POSTGRES_PORT", os.getenv("POSTGRES_PORT", 5432)))
POSTGRES_DB = os.getenv("MAINT_POSTGRES_DB", os.getenv("POSTGRES_DB", "maintenance"))
POSTGRES_USER = os.getenv("MAINT_POSTGRES_USER", os.getenv("POSTGRES_USER", "maintenance"))
POSTGRES_PASSWORD = os.getenv(
    "MAINT_POSTGRES_PASSWORD", os.getenv("POSTGRES_PASSWORD", "123456")
)


@contextmanager
def get_db_connection():
    """获取数据库连接的上下文管理器（自动 commit/rollback）。"""
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def create_tables() -> None:
    """创建 maintenance 模块需要的数据表（幂等）。"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 公告“本周不再弹出”记录
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS maintenance_announcement_snooze (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                announcement_id VARCHAR(64) NOT NULL,
                snooze_until TIMESTAMP NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                UNIQUE(user_id, announcement_id)
            );
            """
        )

        # 用户反馈
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS maintenance_feedback (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                type VARCHAR(32) NOT NULL,
                module VARCHAR(128),
                content TEXT NOT NULL,
                page_url TEXT,
                status VARCHAR(32) NOT NULL DEFAULT 'open',
                admin_reply TEXT,
                replied_by INTEGER,
                replied_at TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            );
            """
        )

        # 兼容旧表：补齐缺失字段（幂等）
        cursor.execute("ALTER TABLE maintenance_feedback ADD COLUMN IF NOT EXISTS module VARCHAR(128);")
        cursor.execute("ALTER TABLE maintenance_feedback ADD COLUMN IF NOT EXISTS admin_reply TEXT;")
        cursor.execute("ALTER TABLE maintenance_feedback ADD COLUMN IF NOT EXISTS replied_by INTEGER;")
        cursor.execute("ALTER TABLE maintenance_feedback ADD COLUMN IF NOT EXISTS replied_at TIMESTAMP;")

        # 索引（幂等）
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_maintenance_feedback_user_id_created_at ON maintenance_feedback(user_id, created_at DESC);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_maintenance_feedback_replied_by ON maintenance_feedback(replied_by);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_maintenance_announcement_snooze_user_id ON maintenance_announcement_snooze(user_id);"
        )

        cursor.close()


def init_database() -> bool:
    """初始化 maintenance 数据库表。"""
    try:
        create_tables()
        return True
    except Exception as e:
        print(f"[ERROR] Maintenance database initialization failed: {str(e)}")
        return False


def fetch_one_dict(sql: str, params: tuple | None = None) -> dict | None:
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(sql, params or ())
        row = cursor.fetchone()
        cursor.close()
        return dict(row) if row else None


def fetch_all_dict(sql: str, params: tuple | None = None) -> list[dict]:
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(sql, params or ())
        rows = cursor.fetchall()
        cursor.close()
        return [dict(r) for r in rows]


def execute(sql: str, params: tuple | None = None) -> None:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params or ())
        cursor.close()
