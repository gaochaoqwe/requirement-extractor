"""
修复PostgreSQL数据库权限脚本

用于修复已创建数据库但权限不足的问题

使用方法：
cd backend/app/staticAnalysis/filter/database
python fix_permissions.py --yes
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys
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

import os

# 从环境变量读取配置（如果存在），否则使用默认值
POSTGRES_HOST = os.getenv("STATIC_POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("STATIC_POSTGRES_PORT", "5432"))
POSTGRES_ADMIN_USER = os.getenv("POSTGRES_ADMIN_USER", "postgres")
POSTGRES_ADMIN_PASSWORD = os.getenv("POSTGRES_ADMIN_PASSWORD", "123456")

DB_NAME = os.getenv("STATIC_POSTGRES_DB", "static_analysis_filter")
DB_USER = os.getenv("STATIC_POSTGRES_USER", "static_analysis")


def fix_permissions(auto_yes=False):
    """修复数据库权限"""
    try:
        print("="*70)
        print("  PostgreSQL数据库权限修复脚本".center(70))
        print("  静态分析过滤工具".center(70))
        print("="*70)
        print()
        print(f"将修复以下数据库的权限：")
        print(f"  - 数据库: {DB_NAME}")
        print(f"  - 用户: {DB_USER}")
        print()
        
        if not auto_yes:
            response = input("确认修复？(yes/no): ").strip().lower()
            if response not in ['yes', 'y']:
                print("\n已取消修复")
                return False
        else:
            print("自动确认模式：继续修复...")
        
        print()
        print(f"正在连接到PostgreSQL服务器 {POSTGRES_HOST}:{POSTGRES_PORT}...")
        
        # 连接到数据库
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_ADMIN_USER,
            password=POSTGRES_ADMIN_PASSWORD,
            database=DB_NAME
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("OK 连接成功\n")
        
        # 1. 授予schema权限
        print(f"[1/5] 授予Schema权限...")
        try:
            cursor.execute(f"GRANT ALL ON SCHEMA public TO {DB_USER}")
            cursor.execute(f"GRANT USAGE ON SCHEMA public TO {DB_USER}")
            print("    OK Schema权限已授予")
        except Exception as e:
            print(f"    WARNING: {e}")
        print()
        
        # 2. 更改所有表的所有者为目标用户
        print(f"[2/5] 更改表所有者...")
        try:
            cursor.execute("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public'
            """)
            tables = cursor.fetchall()
            changed_count = 0
            for (table_name,) in tables:
                try:
                    cursor.execute(f'ALTER TABLE "{table_name}" OWNER TO {DB_USER}')
                    changed_count += 1
                except Exception as e:
                    print(f"    警告：无法更改 {table_name} 的所有者: {e}")
            print(f"    OK 已更改 {changed_count} 个表的所有者")
        except Exception as e:
            print(f"    WARNING: {e}")
        print()
        
        # 3. 授予所有表的权限
        print(f"[3/5] 授予所有表的权限...")
        try:
            cursor.execute(f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {DB_USER}")
            # 查询表数量
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            """)
            table_count = cursor.fetchone()[0]
            print(f"    OK 已授予 {table_count} 个表的权限")
        except Exception as e:
            print(f"    WARNING: {e}")
        print()
        
        # 4. 授予所有序列的权限
        print(f"[4/5] 授予所有序列的权限...")
        try:
            cursor.execute(f"GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO {DB_USER}")
            # 查询序列数量
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.sequences 
                WHERE sequence_schema = 'public'
            """)
            seq_count = cursor.fetchone()[0]
            print(f"    OK 已授予 {seq_count} 个序列的权限")
        except Exception as e:
            print(f"    WARNING: {e}")
        print()
        
        # 5. 设置默认权限（对未来创建的对象）
        print(f"[5/5] 设置默认权限...")
        try:
            cursor.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {DB_USER}")
            cursor.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO {DB_USER}")
            cursor.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO {DB_USER}")
            print("    OK 默认权限已设置")
        except Exception as e:
            print(f"    WARNING: {e}")
        print()
        
        cursor.close()
        conn.close()
        
        print("="*70)
        print("  OK 权限修复完成".center(70))
        print("="*70)
        print()
        print("现在可以使用Navicat连接数据库并查看表了！")
        print()
        
        return True
        
    except psycopg2.Error as e:
        print(f"\nERROR: {e}")
        print("\n请检查：")
        print("1. PostgreSQL服务是否已启动")
        print("2. 管理员用户名和密码是否正确")
        print("3. 数据库是否存在")
        return False
    except Exception as e:
        print(f"\nERROR 未知错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='PostgreSQL数据库权限修复脚本')
    parser.add_argument('--yes', '-y', action='store_true', help='自动确认，跳过交互式提示')
    args = parser.parse_args()
    
    success = fix_permissions(auto_yes=args.yes)
    sys.exit(0 if success else 1)

