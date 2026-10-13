"""
普通模式静态分析 PostgreSQL 表删除脚本

⚠️ 警告：此脚本只删除 nm_ 开头的四张普通模式表，不会删除数据库本身，
也不会影响工具模式的任何表（static_analysis_sessions / issues / rules 等）。

使用方法：
cd backend/app/staticAnalysis/normalModeC/database
python drop_tables.py
或自动确认: python drop_tables.py --yes
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys
import os
import argparse
from pathlib import Path

# ========== 加载 .env 文件 ==========
try:
    from dotenv import load_dotenv
    current_file = Path(__file__).resolve()
    backend_dir = current_file.parent.parent.parent.parent.parent
    env_path = backend_dir / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[配置] 已加载环境变量文件: {env_path}")
    else:
        print(f"[配置] 未找到 .env 文件: {env_path}，使用默认配置")
except ImportError:
    print("[配置] python-dotenv 未安装，使用默认配置")
except Exception as e:
    print(f"[配置] 加载 .env 文件时出错: {e}，使用默认配置")
# ====================================

POSTGRES_HOST          = os.getenv("STATIC_POSTGRES_HOST",     "localhost")
POSTGRES_PORT          = int(os.getenv("STATIC_POSTGRES_PORT", "5432"))
DB_USER                = os.getenv("STATIC_POSTGRES_USER",     "static_analysis")
DB_PASSWORD            = os.getenv("STATIC_POSTGRES_PASSWORD", "123456")
DB_NAME                = os.getenv("STATIC_POSTGRES_DB",       "static_analysis_filter")

# 按依赖顺序删除（先子表后父表）
DROP_ORDER = [
    "nm_analysis_problems",
    "nm_analysis_functions",
    "nm_analysis_files",
    "nm_analysis_tasks",
]


def print_banner():
    print("=" * 70)
    print("  普通模式静态分析 PostgreSQL 表删除脚本".center(70))
    print("=" * 70)
    print()
    print("⚠️  警告：此操作将删除以下四张表的全部数据且不可恢复！")
    for t in DROP_ORDER:
        print(f"     - {t}")
    print()
    print("工具模式的表（static_analysis_* / gjb8114_* / cwe_*）不受影响。")
    print()


def drop_tables(auto_yes: bool = False) -> bool:
    print_banner()

    if not auto_yes:
        resp = input("确认删除？(yes/no): ").strip().lower()
        if resp not in ("yes", "y"):
            print("\n已取消删除")
            return False
    else:
        print("自动确认模式：继续删除...")
    print()

    try:
        print(f"正在连接到 {POSTGRES_HOST}:{POSTGRES_PORT} / {DB_NAME} ...")
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        print("    OK 连接成功\n")
    except psycopg2.Error as e:
        print(f"    ERROR 连接失败: {e}")
        return False

    total = len(DROP_ORDER)
    for i, table in enumerate(DROP_ORDER, 1):
        print(f"[{i}/{total}] 删除表 {table} ...")
        try:
            cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
            print(f"    OK {table} 已删除")
        except Exception as e:
            print(f"    WARNING 删除 {table} 失败: {e}")
        print()

    cursor.close()
    conn.close()

    print("=" * 70)
    print("  OK 删除完成".center(70))
    print("=" * 70)
    print()
    print("后续步骤：")
    print("  重新建表: python init_postgresql.py --yes")
    print()
    return True


def main():
    parser = argparse.ArgumentParser(description="普通模式静态分析 PostgreSQL 表删除脚本")
    parser.add_argument("--yes", "-y", action="store_true", help="自动确认，跳过交互提示")
    args = parser.parse_args()

    success = drop_tables(auto_yes=args.yes)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
