"""
删除PostgreSQL数据库脚本

⚠️ 警告：此脚本会删除整个数据库和用户，包括所有数据！
使用前请确保已备份重要数据。

使用方法：
cd backend/app/staticAnalysis/filter/database
python drop_database.py
或自动确认: python drop_database.py --yes
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
    # 找到 backend/.env 文件
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

# 从环境变量读取配置（如果存在），否则使用默认值
# 数据库配置
POSTGRES_HOST = os.getenv("STATIC_POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("STATIC_POSTGRES_PORT", "5432"))
POSTGRES_ADMIN_USER = os.getenv("POSTGRES_ADMIN_USER", "postgres")
POSTGRES_ADMIN_PASSWORD = os.getenv("POSTGRES_ADMIN_PASSWORD", "123456")

# 要删除的数据库和用户
DB_NAME = os.getenv("STATIC_POSTGRES_DB", "static_analysis_filter")
DB_USER = os.getenv("STATIC_POSTGRES_USER", "static_analysis")


def drop_database_and_user(auto_yes=False):
    """删除数据库和用户"""
    try:
        print("="*70)
        print("  PostgreSQL数据库删除脚本".center(70))
        print("  静态分析过滤工具".center(70))
        print("="*70)
        print()
        print(f"警告：即将删除以下内容：")
        print(f"  - 数据库: {DB_NAME}")
        print(f"  - 用户: {DB_USER}")
        print()
        
        if not auto_yes:
            response = input("确认删除？(yes/no): ").strip().lower()
            if response not in ['yes', 'y']:
                print("\n已取消删除")
                return False
        else:
            print("自动确认模式：继续删除...")
        
        print()
        print(f"正在连接到PostgreSQL服务器 {POSTGRES_HOST}:{POSTGRES_PORT}...")
        
        # 连接到postgres数据库
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_ADMIN_USER,
            password=POSTGRES_ADMIN_PASSWORD,
            database="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("OK 连接成功\n")
        
        # 1. 终止所有到目标数据库的连接
        print(f"[1/3] 终止所有到数据库 '{DB_NAME}' 的连接...")
        try:
            cursor.execute(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{DB_NAME}'
                AND pid <> pg_backend_pid()
            """)
            print("    OK 已终止所有连接")
        except Exception as e:
            print(f"    WARNING 终止连接时出错（可能数据库不存在）: {e}")
        print()
        
        # 2. 删除数据库
        print(f"[2/3] 删除数据库 '{DB_NAME}'...")
        try:
            cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
            print("    OK 数据库删除成功")
        except Exception as e:
            print(f"    WARNING 删除数据库失败: {e}")
        print()
        
        # 3. 删除用户
        print(f"[3/3] 删除用户 '{DB_USER}'...")
        try:
            cursor.execute(f"DROP USER IF EXISTS {DB_USER}")
            print("    OK 用户删除成功")
        except Exception as e:
            print(f"    WARNING 删除用户失败: {e}")
        print()
        
        cursor.close()
        conn.close()
        
        print("="*70)
        print("  OK 删除完成".center(70))
        print("="*70)
        print()
        print("后续步骤：")
        print("1. 运行 init_postgresql.py 重新创建数据库")
        print("   python init_postgresql.py --yes")
        print()
        
        return True
        
    except psycopg2.Error as e:
        print(f"\nERROR: {e}")
        print("\n请检查：")
        print("1. PostgreSQL服务是否已启动")
        print("2. 管理员用户名和密码是否正确")
        print("3. 主机和端口是否可访问")
        return False
    except Exception as e:
        print(f"\nERROR 未知错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='PostgreSQL数据库删除脚本')
    parser.add_argument('--yes', '-y', action='store_true', help='自动确认，跳过交互式提示')
    args = parser.parse_args()
    
    success = drop_database_and_user(auto_yes=args.yes)
    sys.exit(0 if success else 1)

