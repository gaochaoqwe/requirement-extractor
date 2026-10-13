"""
PostgreSQL数据库一键初始化脚本（maintenance）

在新电脑安装PostgreSQL后，运行此脚本即可完成数据库和表的创建。

使用方法：
1. 确保PostgreSQL已安装并启动
2. 如有需要修改下面的配置参数（管理员密码等）
3. 运行: python init_postgresql.py
4. 或自动确认: python init_postgresql.py --yes

功能：
- 自动创建1个数据库（maintenance）
- 自动创建数据库用户（maintenance）
- 自动创建 maintenance 模块需要的数据表
"""

import argparse
import os
import sys
from pathlib import Path

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# ==================== 配置参数 ====================
# PostgreSQL管理员配置
POSTGRES_HOST = "localhost"
POSTGRES_PORT = 5432
POSTGRES_ADMIN_USER = "postgres"
POSTGRES_ADMIN_PASSWORD = "123456"

# 要创建的数据库用户
DB_USER = "maintenance"
DB_PASSWORD = "123456"

# 要创建的数据库
DB_NAME = "maintenance"
DB_DESCRIPTION = "维护模块数据库（maintenance 模块独立使用）"
# ================================================


def print_banner():
    print("=" * 70)
    print("  PostgreSQL数据库一键初始化脚本".center(70))
    print("  Maintenance Module Database Initialization".center(70))
    print("=" * 70)
    print()
    print()


def check_config():
    print("配置信息：")
    print(f"  管理员用户: {POSTGRES_ADMIN_USER}")
    print(f"  管理员密码: {'*' * len(POSTGRES_ADMIN_PASSWORD)}")
    print(f"  数据库名称: {DB_NAME}")
    print(f"  数据库用户: {DB_USER}")
    print(f"  数据库密码: {'*' * len(DB_PASSWORD)}")
    print()
    print()


def create_user_and_database() -> bool:
    try:
        print(f"正在连接到PostgreSQL服务器 {POSTGRES_HOST}:{POSTGRES_PORT}...")
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_ADMIN_USER,
            password=POSTGRES_ADMIN_PASSWORD,
            database="postgres",
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        print("OK 连接成功\n")

        print(f"[1/3] 检查并创建数据库用户 '{DB_USER}'...")
        cursor.execute(f"SELECT 1 FROM pg_roles WHERE rolname = '{DB_USER}'")
        if cursor.fetchone():
            print(f"    WARNING  用户 '{DB_USER}' 已存在，跳过创建")
        else:
            cursor.execute(f"CREATE USER {DB_USER} WITH PASSWORD '{DB_PASSWORD}'")
            print(f"    OK 用户 '{DB_USER}' 创建成功")
        print()

        print(f"[2/3] 检查并创建数据库 '{DB_NAME}'...")
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
        if cursor.fetchone():
            print(f"    WARNING  数据库 '{DB_NAME}' 已存在，跳过创建")
        else:
            cursor.execute(f"CREATE DATABASE {DB_NAME} ENCODING 'UTF8'")
            print(f"    OK 数据库 '{DB_NAME}' 创建成功")
        print(f"    说明: {DB_DESCRIPTION}")
        print()

        print("[3/3] 授予用户权限...")
        cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO {DB_USER}")
        print(f"    OK 已授予 '{DB_USER}' 对数据库 '{DB_NAME}' 的所有权限")
        print()

        cursor.close()
        conn.close()
        return True

    except psycopg2.Error as e:
        print(f"\nERROR 错误: {e}")
        print("\n请检查：")
        print("1. PostgreSQL服务是否已启动")
        print("2. 管理员用户名和密码是否正确")
        print("3. 主机和端口是否可访问")
        return False
    except Exception as e:
        print(f"\nERROR 未知错误: {e}")
        return False


def grant_schema_privileges() -> bool:
    print("[4/5] 授予Schema权限...")
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_ADMIN_USER,
            password=POSTGRES_ADMIN_PASSWORD,
            database=DB_NAME,
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        cursor.execute(f"GRANT ALL ON SCHEMA public TO {DB_USER}")
        cursor.execute(f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {DB_USER}")
        cursor.execute(f"GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO {DB_USER}")
        cursor.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {DB_USER}")
        cursor.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO {DB_USER}")

        cursor.close()
        conn.close()

        print(f"    OK 数据库 '{DB_NAME}' schema权限配置完成")
        print()
        return True

    except Exception as e:
        print(f"    ERROR 数据库 '{DB_NAME}' schema权限配置失败: {e}")
        print()
        return False


def create_tables() -> bool:
    print("[5/5] 创建数据表...")

    os.environ["MAINT_POSTGRES_HOST"] = POSTGRES_HOST
    os.environ["MAINT_POSTGRES_PORT"] = str(POSTGRES_PORT)
    os.environ["MAINT_POSTGRES_USER"] = DB_USER
    os.environ["MAINT_POSTGRES_PASSWORD"] = DB_PASSWORD
    os.environ["MAINT_POSTGRES_DB"] = DB_NAME

    try:
        current_file = Path(__file__).resolve()
        db_dir = current_file.parent
        maintenance_dir = db_dir.parent
        app_dir = maintenance_dir.parent
        backend_dir = app_dir.parent
        project_root = backend_dir.parent

        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))

        print(f"    项目根目录: {project_root}")
        print(f"    后端目录: {backend_dir}")

        from backend.app.maintenance.db.database import init_database

        ok = init_database()
        if not ok:
            raise RuntimeError("maintenance init_database() failed")

        print("    OK maintenance 表创建完成")
        print()
        return True

    except Exception as e:
        print(f"\nERROR 创建数据表失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def print_success_info():
    print("=" * 70)
    print("  OK PostgreSQL数据库初始化完成！".center(70))
    print("=" * 70)
    print()
    print("数据库连接信息：")
    print(f"  主机: {POSTGRES_HOST}")
    print(f"  端口: {POSTGRES_PORT}")
    print(f"  用户: {DB_USER}")
    print(f"  密码: {DB_PASSWORD}")
    print(f"  数据库: {DB_NAME}")
    print()
    print("后续步骤：")
    print("1. 启动后端服务：")
    print("   python run_fastapi.py")
    print()


def main():
    parser = argparse.ArgumentParser(description="PostgreSQL数据库初始化脚本（maintenance）")
    parser.add_argument("--yes", "-y", action="store_true", help="自动确认，跳过交互式提示")
    args = parser.parse_args()

    print_banner()
    check_config()

    print("准备初始化PostgreSQL数据库...")
    print(f"将创建数据库: {DB_NAME}")
    print(f"数据库用户: {DB_USER}")
    print()

    if not args.yes:
        response = input("是否继续？(yes/no): ").strip().lower()
        if response not in ["yes", "y"]:
            print("\n已取消初始化")
            sys.exit(0)
    else:
        print("自动确认模式：继续执行...")

    print()

    if not create_user_and_database():
        sys.exit(1)

    if not grant_schema_privileges():
        print("\nWARNING  Schema权限配置失败，请手动配置")

    if not create_tables():
        print("\nWARNING  数据库和用户创建成功，但表创建失败")
        sys.exit(1)

    print_success_info()


if __name__ == "__main__":
    main()
