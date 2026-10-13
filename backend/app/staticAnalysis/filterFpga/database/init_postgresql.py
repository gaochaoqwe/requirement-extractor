"""
PostgreSQL数据库一键初始化脚本

在新电脑安装PostgreSQL后，运行此脚本即可完成所有数据库和表的创建，
并从SQLite迁移规则数据

使用方法：
1. 确保PostgreSQL已安装并启动
2. 确保 backend/.env 文件已配置（会自动加载）
3. 运行: python init_postgresql.py
4. 或自动确认: python init_postgresql.py --yes

功能：
- 自动创建数据库（static_analysis_filter）
- 自动创建数据库用户（static_analysis）
- 自动创建所有需要的数据表
- 自动从SQLite迁移规则数据（GJB8114和CWE规则）
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys
import os
from pathlib import Path
import argparse

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

# ==================== 配置参数 ====================
# 从环境变量读取配置（如果存在），否则使用默认值

# PostgreSQL管理员配置
POSTGRES_HOST = os.getenv("FPGA_POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("FPGA_POSTGRES_PORT", "5432"))
POSTGRES_ADMIN_USER = os.getenv("POSTGRES_ADMIN_USER", "postgres")
POSTGRES_ADMIN_PASSWORD = os.getenv("POSTGRES_ADMIN_PASSWORD", "123456")

# 要创建的数据库用户
DB_USER = os.getenv("FPGA_POSTGRES_USER", "fpga_analysis")
DB_PASSWORD = os.getenv("FPGA_POSTGRES_PASSWORD", "123456")

# 要创建的数据库
DB_NAME = os.getenv("FPGA_POSTGRES_DB", "fpga_static_analysis_filter")
DB_DESCRIPTION = "FPGA静态分析过滤工具数据库（包含会话、问题、FPGA规则的所有表）"

print(f"[配置] 从环境变量读取配置")
print(f"  数据库主机: {POSTGRES_HOST}")
print(f"  数据库端口: {POSTGRES_PORT}")
print(f"  数据库名称: {DB_NAME}")
print(f"  数据库用户: {DB_USER}")
# ================================================

def print_banner():
    """打印欢迎横幅"""
    print("="*70)
    print("  PostgreSQL数据库一键初始化脚本".center(70))
    print("  静态分析过滤工具数据库初始化".center(70))
    print("="*70)
    print()

def check_config():
    """检查配置"""
    print(f"配置信息：")
    print(f"  管理员用户: {POSTGRES_ADMIN_USER}")
    print(f"  管理员密码: {'*' * len(POSTGRES_ADMIN_PASSWORD)}")
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
            database="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("OK 连接成功\n")
        
        # 1. 创建用户
        print(f"[1/3] 检查并创建数据库用户 '{DB_USER}'...")
        cursor.execute(f"SELECT 1 FROM pg_roles WHERE rolname = '{DB_USER}'")
        if cursor.fetchone():
            print(f"    WARNING  用户 '{DB_USER}' 已存在，跳过创建")
        else:
            cursor.execute(f"CREATE USER {DB_USER} WITH PASSWORD '{DB_PASSWORD}'")
            print(f"    OK 用户 '{DB_USER}' 创建成功")
        print()
        
        # 2. 创建数据库
        print(f"[2/3] 检查并创建数据库 '{DB_NAME}'...")
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
        if cursor.fetchone():
            print(f"    WARNING  数据库 '{DB_NAME}' 已存在，跳过创建")
        else:
            cursor.execute(f"CREATE DATABASE {DB_NAME} ENCODING 'UTF8'")
            print(f"    OK 数据库 '{DB_NAME}' 创建成功")
        print(f"    说明: {DB_DESCRIPTION}")
        print()
        
        # 3. 授予权限
        print(f"[3/3] 授予用户权限...")
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

def grant_schema_privileges():
    """授予schema权限"""
    print("[4/6] 授予Schema权限...")
    
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_ADMIN_USER,
            password=POSTGRES_ADMIN_PASSWORD,
            database=DB_NAME
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # 授予public schema的所有权限
        cursor.execute(f"GRANT ALL ON SCHEMA public TO {DB_USER}")
        # 授予该schema下所有表的权限（如果表已存在）
        cursor.execute(f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {DB_USER}")
        # 授予该schema下所有序列的权限
        cursor.execute(f"GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO {DB_USER}")
        # 设置默认权限（对未来创建的对象）
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

def create_tables():
    """创建所有数据表"""
    print("[5/6] 创建数据表...")
    
    # 设置环境变量，确保使用PostgreSQL
    os.environ["STATIC_POSTGRES_HOST"] = POSTGRES_HOST
    os.environ["STATIC_POSTGRES_PORT"] = str(POSTGRES_PORT)
    os.environ["STATIC_POSTGRES_USER"] = DB_USER
    os.environ["STATIC_POSTGRES_PASSWORD"] = DB_PASSWORD
    os.environ["STATIC_POSTGRES_DB"] = DB_NAME
    
    try:
        # 添加项目根目录到路径
        import sys
        from pathlib import Path as PathLib
        
        # 找到项目根目录（包含backend文件夹的目录）
        current_file = PathLib(__file__).resolve()
        db_dir = current_file.parent
        filter_dir = db_dir.parent
        static_analysis_dir = filter_dir.parent
        app_dir = static_analysis_dir.parent
        backend_dir = app_dir.parent
        project_root = backend_dir.parent
        
        # 添加到 Python 路径
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        
        print(f"    项目根目录: {project_root}")
        print(f"    后端目录: {backend_dir}")
        
        # 导入并初始化数据库（会创建所有表）
        print("    正在初始化FPGA静态分析过滤工具表...")
        from backend.app.staticAnalysis.filterFpga.database.postgresql_database import init_database
        init_database()
        print("    OK 所有表创建完成")
        print("       - static_analysis_sessions (会话表)")
        print("       - static_analysis_issues (问题表)")
        print("       - static_analysis_marked_problems (标记问题表)")
        print("       - fpga_rules (FPGA规则表)")
        
        # 创建表后，再次授予所有表的权限
        print("    正在授予表权限...")
        grant_table_privileges()
        
        print()
        return True
        
    except Exception as e:
        print(f"\nERROR 创建数据表失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def grant_table_privileges():
    """在创建表后授予所有表的权限"""
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_ADMIN_USER,
            password=POSTGRES_ADMIN_PASSWORD,
            database=DB_NAME
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # 1. 确保用户有schema的USAGE权限
        cursor.execute(f"GRANT USAGE ON SCHEMA public TO {DB_USER}")
        
        # 2. 授予所有表的权限（包括SELECT, INSERT, UPDATE, DELETE等）
        cursor.execute(f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {DB_USER}")
        
        # 3. 授予所有序列的权限
        cursor.execute(f"GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO {DB_USER}")
        
        # 4. 授予所有函数的权限（如果有）
        cursor.execute(f"GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO {DB_USER}")
        
        # 5. 设置默认权限（对未来创建的对象）
        cursor.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {DB_USER}")
        cursor.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO {DB_USER}")
        cursor.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO {DB_USER}")
        
        # 6. 确保用户是schema的所有者（可选，但有助于权限管理）
        # 注意：这需要先撤销当前所有者，可能不必要
        
        # 7. 查询并显示所有表的所有者
        cursor.execute("""
            SELECT tablename, tableowner 
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        tables = cursor.fetchall()
        if tables:
            print(f"    表列表和所有者：")
            for table_name, owner in tables:
                print(f"      - {table_name} (所有者: {owner})")
                # 如果表的所有者不是目标用户，需要更改所有者或授予权限
                if owner != DB_USER:
                    try:
                        cursor.execute(f'ALTER TABLE "{table_name}" OWNER TO {DB_USER}')
                        print(f"        已将 {table_name} 的所有者改为 {DB_USER}")
                    except Exception as e:
                        print(f"        警告：无法更改 {table_name} 的所有者: {e}")
        
        cursor.close()
        conn.close()
        
        print(f"    OK 已授予 '{DB_USER}' 对所有表的权限")
        return True
        
    except Exception as e:
        print(f"    WARNING 授予表权限时出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def migrate_rules_data():
    """导入FPGA规则数据"""
    print("[6/6] 导入FPGA规则数据...")
    
    try:
        # 添加项目根目录到路径
        import sys
        from pathlib import Path as PathLib
        
        current_file = PathLib(__file__).resolve()
        db_dir = current_file.parent
        filter_dir = db_dir.parent
        static_analysis_dir = filter_dir.parent
        app_dir = static_analysis_dir.parent
        backend_dir = app_dir.parent
        project_root = backend_dir.parent
        
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        
        print("    正在导入FPGA规则数据...")
        from backend.app.staticAnalysis.filterFpga.database.migrate_fpga_rules import migrate_fpga_rules
        fpga_count = migrate_fpga_rules()
        print(f"    OK FPGA规则导入完成，共 {fpga_count} 条规则")
        
        print()
        return True
        
    except Exception as e:
        print(f"\nERROR 导入FPGA规则数据失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def print_success_info():
    """打印成功信息和后续步骤"""
    print("="*70)
    print("  OK PostgreSQL数据库初始化完成！".center(70))
    print("="*70)
    print()
    print("数据库连接信息：")
    print(f"  主机: {POSTGRES_HOST}")
    print(f"  端口: {POSTGRES_PORT}")
    print(f"  用户: {DB_USER}")
    print(f"  密码: {DB_PASSWORD}")
    print(f"  数据库: {DB_NAME}")
    print()
    print("已创建的数据表：")
    print("  会话和问题表:")
    print("    - static_analysis_sessions       (过滤会话)")
    print("    - static_analysis_issues         (分析问题)")
    print("    - static_analysis_marked_problems (标记问题)")
    print()
    print("  规则表:")
    print("    - fpga_rules                     (FPGA Verilog和VHDL编码规则)")
    print()
    print("后续步骤：")
    print()
    print("1. 设置环境变量（Windows CMD）：")
    print(f"   set STATIC_POSTGRES_HOST={POSTGRES_HOST}")
    print(f"   set STATIC_POSTGRES_PORT={POSTGRES_PORT}")
    print(f"   set STATIC_POSTGRES_DB={DB_NAME}")
    print(f"   set STATIC_POSTGRES_USER={DB_USER}")
    print(f"   set STATIC_POSTGRES_PASSWORD={DB_PASSWORD}")
    print()
    print("2. 或者在backend目录创建 .env 文件：")
    print(f"   STATIC_POSTGRES_HOST={POSTGRES_HOST}")
    print(f"   STATIC_POSTGRES_PORT={POSTGRES_PORT}")
    print(f"   STATIC_POSTGRES_DB={DB_NAME}")
    print(f"   STATIC_POSTGRES_USER={DB_USER}")
    print(f"   STATIC_POSTGRES_PASSWORD={DB_PASSWORD}")
    print()
    print("3. 启动后端服务：")
    print("   python run_fastapi.py")
    print()

def print_manual_sql():
    """打印手动执行的SQL命令"""
    print("\n" + "="*70)
    print("如果自动初始化失败，可以手动执行以下SQL命令：")
    print("="*70)
    print(f"""
-- 连接到PostgreSQL
psql -U {POSTGRES_ADMIN_USER} -h {POSTGRES_HOST} -p {POSTGRES_PORT}

-- 创建用户
CREATE USER {DB_USER} WITH PASSWORD '{DB_PASSWORD}';

-- 创建数据库
CREATE DATABASE {DB_NAME} ENCODING 'UTF8';

-- 授予权限
GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO {DB_USER};

-- 连接到新数据库并授予schema权限
\\c {DB_NAME}
GRANT ALL ON SCHEMA public TO {DB_USER};
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {DB_USER};
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO {DB_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {DB_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO {DB_USER};
""")

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='PostgreSQL数据库初始化脚本')
    parser.add_argument('--yes', '-y', action='store_true', help='自动确认，跳过交互式提示')
    args = parser.parse_args()
    
    print_banner()
    check_config()
    
    print("准备初始化PostgreSQL数据库...")
    print(f"将创建数据库: {DB_NAME}")
    print(f"数据库用户: {DB_USER}")
    print()
    
    if not args.yes:
        response = input("是否继续？(yes/no): ").strip().lower()
        
        if response not in ['yes', 'y']:
            print("\n已取消初始化")
            print_manual_sql()
            sys.exit(0)
    else:
        print("自动确认模式：继续执行...")
    
    print()
    
    # 步骤1-3: 创建用户和数据库
    if not create_user_and_database():
        print_manual_sql()
        sys.exit(1)
    
    # 步骤4: 授予schema权限
    if not grant_schema_privileges():
        print("\nWARNING  Schema权限配置失败，请手动配置")
    
    # 步骤5: 创建表
    if not create_tables():
        print("\nWARNING  数据库和用户创建成功，但表创建失败")
        print("   你可以稍后手动运行以下命令创建表：")
        print("   python -m backend.app.staticAnalysis.filter.database.postgresql_database")
        sys.exit(1)
    
    # 步骤6: 迁移规则数据
    if not migrate_rules_data():
        print("\nWARNING  数据库和表创建成功，但规则数据迁移失败")
        print("   你可以稍后手动运行以下命令迁移数据：")
        print("   python -m backend.app.staticAnalysis.filter.database.migrate_rules")
    
    # 打印成功信息
    print_success_info()

if __name__ == "__main__":
    main()

