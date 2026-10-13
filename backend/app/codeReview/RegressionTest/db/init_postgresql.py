"""
PostgreSQL数据库一键初始化脚本

在新电脑安装PostgreSQL后，运行此脚本即可完成所有数据库和表的创建

使用方法：
1. 确保PostgreSQL已安装并启动
2. 修改下面的配置参数（管理员密码等）
3. 运行: python init_postgresql.py
4. 或自动确认: python init_postgresql.py --yes

功能：
- 自动创建1个独立的回归测试数据库（code_review_regression）
- 自动创建数据库用户（code_review）
- 自动创建所有需要的数据表（回归测试专用表）
- 自动执行数据库迁移
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys
import os
from pathlib import Path
import argparse

# ==================== 配置参数 ====================
# PostgreSQL管理员配置
POSTGRES_HOST = "localhost"
POSTGRES_PORT = 5432
POSTGRES_ADMIN_USER = "postgres"  # PostgreSQL默认管理员用户
POSTGRES_ADMIN_PASSWORD = "123456"  # 管理员密码

# 要创建的数据库用户
DB_USER = "code_review"
DB_PASSWORD = "123456"  # 数据库用户密码

# 要创建的数据库（回归测试独立数据库）
DB_NAME = "code_review_regression"
DB_DESCRIPTION = "回归测试专用数据库（独立于配置项测试）"
# ================================================

def print_banner():
    """打印欢迎横幅"""
    print("="*70)
    print("  PostgreSQL数据库一键初始化脚本".center(70))
    print("  Code Review Module Database Initialization".center(70))
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
    print("[4/5] 授予Schema权限...")
    
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
    print("[5/5] 创建数据表...")
    
    # 设置环境变量，确保使用PostgreSQL（回归测试专用数据库）
    os.environ["POSTGRES_HOST"] = POSTGRES_HOST
    os.environ["POSTGRES_PORT"] = str(POSTGRES_PORT)
    os.environ["POSTGRES_USER"] = DB_USER
    os.environ["POSTGRES_PASSWORD"] = DB_PASSWORD
    os.environ["POSTGRES_DB_REGRESSION"] = DB_NAME
    
    try:
        # 添加项目根目录到路径
        import sys
        from pathlib import Path as PathLib
        
        # 找到项目根目录（包含backend文件夹的目录）
        current_file = PathLib(__file__).resolve()
        db_dir = current_file.parent
        config_item_dir = db_dir.parent
        code_review_dir = config_item_dir.parent
        app_dir = code_review_dir.parent
        backend_dir = app_dir.parent
        project_root = backend_dir.parent
        
        # 添加到 Python 路径
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        
        print(f"    项目根目录: {project_root}")
        print(f"    后端目录: {backend_dir}")
        
        # 导入并初始化回归测试数据库（会创建所有表）
        print("    正在初始化回归测试相关表...")
        from backend.app.codeReview.RegressionTest.db.database import init_database
        init_database()
        print("    OK 回归测试表创建完成（regression_test_tasks, regression_test_files, regression_test_functions, regression_test_problems, regression_test_problem_filters, regression_test_function_pairs）")
        
        print("    正在初始化回归测试链路审查相关表...")
        from backend.app.codeReview.RegressionTest.db.database_chain import init_chain_database
        init_chain_database()
        print("    OK 回归测试链路审查表创建完成（regression_test_chain_problems）")
        
        print("    正在初始化回归测试功能审查相关表...")
        from backend.app.codeReview.RegressionTest.db.database_feature import init_feature_database
        init_feature_database()
        print("    OK 回归测试功能审查表创建完成（regression_test_features, regression_test_feature_problems）")
        
        # 初始化系统过滤规则模板
        print("\n    正在初始化系统过滤规则模板...")
        from backend.app.codeReview.RegressionTest.db.init_filter_templates import init_system_filter_templates
        init_system_filter_templates()
        print("    OK 系统过滤规则模板初始化完成")
        
        print()
        return True
        
    except Exception as e:
        print(f"\nERROR 创建数据表失败: {e}")
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
    print("已创建的数据表（回归测试专用）：")
    print("  基础表:")
    print("    - regression_test_tasks              (回归测试任务)")
    print("    - regression_test_files              (上传的代码文件)")
    print("    - regression_test_functions          (提取的函数)")
    print("    - regression_test_function_pairs     (函数配对关系：旧版↔新版)")
    print("    - regression_test_problems           (审查问题)")
    print("    - regression_test_problem_filters    (问题过滤规则)")
    print()
    print("  链路审查表:")
    print("    - regression_test_chain_problems         (链路审查问题)")
    print("    - regression_test_file_problems          (文件级审查问题)")
    print()
    print("  功能审查表:")
    print("    - regression_test_features               (功能点定义)")
    print("    - regression_test_feature_problems        (功能审查问题)")
    print()
    print("后续步骤：")
    print()
    print("1. 设置环境变量（Windows PowerShell）：")
    print(f"   $env:POSTGRES_HOST='{POSTGRES_HOST}'")
    print(f"   $env:POSTGRES_PORT='{POSTGRES_PORT}'")
    print(f"   $env:POSTGRES_DB_REGRESSION='{DB_NAME}'  # 回归测试专用")
    print(f"   $env:POSTGRES_USER='{DB_USER}'")
    print(f"   $env:POSTGRES_PASSWORD='{DB_PASSWORD}'")
    print()
    print("2. 或者设置环境变量（Windows CMD）：")
    print(f"   set POSTGRES_HOST={POSTGRES_HOST}")
    print(f"   set POSTGRES_PORT={POSTGRES_PORT}")
    print(f"   set POSTGRES_DB_REGRESSION={DB_NAME}")
    print(f"   set POSTGRES_USER={DB_USER}")
    print(f"   set POSTGRES_PASSWORD={DB_PASSWORD}")
    print()
    print("3. 或者创建 .env 文件：")
    print(f"   POSTGRES_HOST={POSTGRES_HOST}")
    print(f"   POSTGRES_PORT={POSTGRES_PORT}")
    print(f"   POSTGRES_DB_REGRESSION={DB_NAME}  # 回归测试专用")
    print(f"   POSTGRES_USER={DB_USER}")
    print(f"   POSTGRES_PASSWORD={DB_PASSWORD}")
    print()
    print("4. 启动后端服务：")
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
        print("   python -m backend.app.codeReview.RegressionTest.db.database")
        sys.exit(1)
    
    # 打印成功信息
    print_success_info()

if __name__ == "__main__":
    main()
