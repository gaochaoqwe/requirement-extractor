"""
PostgreSQL用户认证数据库一键初始化脚本（auth）

运行此脚本将：
- 自动创建1个数据库（auth）
- 自动创建数据库用户（auth）
- 自动创建用户认证相关表（users）
- 插入默认用户数据

使用方法：
1. 确保PostgreSQL已安装并启动
2. 如有需要修改下面的配置参数（管理员密码等）
3. 运行: python init_postgresql.py
4. 或自动确认: python init_postgresql.py --yes
"""
import argparse
import hashlib
import sys

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# ==================== 配置参数 ====================
# PostgreSQL管理员配置
POSTGRES_HOST = "localhost"
POSTGRES_PORT = 5432
POSTGRES_ADMIN_USER = "postgres"
POSTGRES_ADMIN_PASSWORD = "123456"

# 要创建的数据库和用户
DB_NAME = "auth"
DB_USER = "auth"
DB_PASSWORD = "123456"
DB_DESCRIPTION = "用户认证数据库（auth 模块独立使用）"
# ================================================

def hash_password(password):
    """使用SHA256哈希密码"""
    return hashlib.sha256(password.encode()).hexdigest()

def print_banner():
    """打印欢迎横幅"""
    print("="*70)
    print("  用户认证表初始化脚本".center(70))
    print("  User Authentication Table Initialization".center(70))
    print("="*70)
    print()

def check_config():
    """检查配置"""
    print(f"配置信息：")
    print(f"  管理员用户: {POSTGRES_ADMIN_USER}")
    print(f"  管理员密码: {'*' * len(POSTGRES_ADMIN_PASSWORD)}")
    print(f"  数据库主机: {POSTGRES_HOST}")
    print(f"  数据库端口: {POSTGRES_PORT}")
    print(f"  数据库名称: {DB_NAME}")
    print(f"  数据库用户: {DB_USER}")
    print(f"  数据库密码: {'*' * len(DB_PASSWORD)}")
    print()

def create_user_and_database():
    """创建数据库用户和数据库"""
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
        print(f"\nERROR 数据库错误: {e}")
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

def grant_schema_privileges():
    """授予schema权限"""
    print("[4/6] 授予Schema权限...")

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

def create_users_table():
    """创建用户表"""
    try:
        print(f"正在连接到PostgreSQL数据库 {DB_NAME}...")
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        print("OK 连接成功\n")

        # 创建用户表
        print(f"[5/6] 创建用户表 'users'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(64) NOT NULL,
                display_name VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        print("    OK 用户表创建成功")
        print()

        # 插入默认用户
        print(f"[6/6] 插入默认用户...")
        default_password_hash = hash_password("123456")

        default_users = [
            ("gaochao", "高超"),
            ("lilingzi", "李玲子"),
            ("wangkaixuan", "王凯旋"),
            ("laikunyu", "莱琨钰"),
            ("hanyunlong", "韩蕴龙"),
            ("jiarui", "贾瑞"),
            ("yusufen", "于素芬"),
            ("guoshiqing", "郭士清"),
            ("wangyue", "王悦"),
            ("zhululu", "朱璐璐"),
            ("zhanggang", "张刚"),
            ("wanghao", "王浩"),
            ("sunhaoqiang", "孙浩强"),
            ("lijiazhen", "李佳真"),
            ("renqiuwen", "任秋稳"),
            ("panshuai", "潘帅"),
            ("zhaohanbing", "赵寒冰"),
            ("lixinrui", "李新瑞"),
            ("zhangxuanguang", "张悬光"),
            ("doujihuan", "窦纪欢"),
            ("wuhuiying", "武慧莹"),
            ("zhanghaoran", "张浩冉"),
            ("zhangshaofei", "张少飞"),
            ("wangliuzhu", "汪刘柱"),
            ("zhairuoyan", "翟若岩"),
            ("guoxiaojv", "郭晓菊"),
            ("chengdong", "程栋"),
            ("zhangminghao", "张铭昊"),
            ("liudingxiang", "刘丁翔"),
            ("fushoujia", "付首嘉"),
            ("zhanjunwen", "战俊文"),
            ("dangqian", "党倩"),
            ("zhanglong", "张龙"),
            ("yangmeng", "杨猛"),
            ("liyanyan", "李岩岩"),
            ("chenxinyu", "陈歆宇"),
            ("wangshaozhe", "王绍哲"),
            ("gaosujie", "高素杰"),
            ("liangxiaomiao", "梁小苗"),
            ("fengjingjing", "冯璟璟"),
            ("niutingting", "牛婷婷"),
            ("zhanggeng", "张耕"),
        ]

        inserted = 0
        skipped = 0
        for username, display_name in default_users:
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, display_name)
                VALUES (%s, %s, %s)
                ON CONFLICT (username) DO NOTHING
                """,
                (username, default_password_hash, display_name),
            )
            if cursor.rowcount and cursor.rowcount > 0:
                inserted += 1
            else:
                skipped += 1

        print(f"    OK 默认用户插入完成: 新增 {inserted} 个，已存在跳过 {skipped} 个")
        print(f"       初始密码: 123456")
        print()

        cursor.close()
        conn.close()

        return True

    except psycopg2.Error as e:
        print(f"\nERROR 数据库错误: {e}")
        print("\n请检查：")
        print("1. PostgreSQL服务是否已启动")
        print("2. auth数据库是否已创建")
        print("3. 数据库用户名和密码是否正确")
        return False
    except Exception as e:
        print(f"\nERROR 未知错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def print_success_info():
    """打印成功信息"""
    print("="*70)
    print("  OK 用户认证数据库初始化完成！".center(70))
    print("="*70)
    print()
    print("已创建的数据库：")
    print(f"  - {DB_NAME}")
    print()
    print("已创建的用户：")
    print(f"  - {DB_USER}")
    print()
    print("默认用户信息：")
    print("  用户名: gaochao")
    print("  密码: 123456")
    print("  显示名: 高超")
    print()

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='用户认证表初始化脚本')
    parser.add_argument('--yes', '-y', action='store_true', help='自动确认，跳过交互式提示')
    args = parser.parse_args()

    print_banner()
    check_config()

    print("准备初始化用户认证数据库...")
    print()

    if not args.yes:
        response = input("是否继续？(yes/no): ").strip().lower()

        if response not in ['yes', 'y']:
            print("\n已取消初始化")
            sys.exit(0)
    else:
        print("自动确认模式：继续执行...")

    print()

    if not create_user_and_database():
        sys.exit(1)

    if not grant_schema_privileges():
        print("\nWARNING  Schema权限配置失败，请手动配置")

    # 创建用户表
    if not create_users_table():
        sys.exit(1)

    # 打印成功信息
    print_success_info()

if __name__ == "__main__":
    main()
