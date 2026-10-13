"""
用户认证数据库模型
"""
import os
from contextlib import contextmanager
from datetime import datetime
import hashlib
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

# 尝试加载 auth 模块自己的 .env（不覆盖已存在环境变量，避免污染其他模块）
try:
    from dotenv import load_dotenv

    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

# 从环境变量读取数据库配置（auth 模块独立库；优先 AUTH_POSTGRES_*，回退到全局 POSTGRES_*）
POSTGRES_HOST = os.getenv("AUTH_POSTGRES_HOST", os.getenv("POSTGRES_HOST", "localhost"))
POSTGRES_PORT = int(os.getenv("AUTH_POSTGRES_PORT", os.getenv("POSTGRES_PORT", 5432)))
POSTGRES_DB = os.getenv("AUTH_POSTGRES_DB", os.getenv("POSTGRES_DB", "auth"))
POSTGRES_USER = os.getenv("AUTH_POSTGRES_USER", os.getenv("POSTGRES_USER", "auth"))
POSTGRES_PASSWORD = os.getenv(
    "AUTH_POSTGRES_PASSWORD", os.getenv("POSTGRES_PASSWORD", "123456")
)


@contextmanager
def get_db_connection():
    """获取数据库连接的上下文管理器"""
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def hash_password(password):
    """使用SHA256哈希密码"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password, password_hash):
    """验证密码"""
    return hash_password(password) == password_hash


class UserModel:
    """用户模型"""
    
    @staticmethod
    def get_user_by_username(username):
        """根据用户名获取用户"""
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                "SELECT * FROM users WHERE username = %s AND is_active = TRUE",
                (username,)
            )
            user = cursor.fetchone()
            cursor.close()
            return dict(user) if user else None
    
    @staticmethod
    def get_user_by_id(user_id):
        """根据ID获取用户"""
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                "SELECT * FROM users WHERE id = %s AND is_active = TRUE",
                (user_id,)
            )
            user = cursor.fetchone()
            cursor.close()
            return dict(user) if user else None
    
    @staticmethod
    def authenticate(username, password):
        """验证用户登录"""
        user = UserModel.get_user_by_username(username)
        if not user:
            return None
        
        if verify_password(password, user['password_hash']):
            # 更新最后登录时间
            UserModel.update_last_login(user['id'])
            return user
        
        return None
    
    @staticmethod
    def update_last_login(user_id):
        """更新最后登录时间"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET last_login = %s WHERE id = %s",
                (datetime.now(), user_id)
            )
            cursor.close()
    
    @staticmethod
    def create_user(username, password, display_name):
        """创建新用户"""
        password_hash = hash_password(password)
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, display_name)
                VALUES (%s, %s, %s)
                RETURNING id, username, display_name, created_at
                """,
                (username, password_hash, display_name)
            )
            user = cursor.fetchone()
            cursor.close()
            return dict(user) if user else None
    
    @staticmethod
    def get_all_users():
        """获取所有用户（不包括密码）"""
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                """
                SELECT id, username, display_name, created_at, last_login, is_active
                FROM users
                ORDER BY id
                """
            )
            users = cursor.fetchall()
            cursor.close()
            return [dict(user) for user in users]
