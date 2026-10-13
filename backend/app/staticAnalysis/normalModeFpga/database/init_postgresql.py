"""
普通模式 FPGA PostgreSQL 表初始化脚本

在 fpga_static_analysis_filter 数据库中创建普通模式FPGA所需的四张 nm_fpga_ 表。
与工具模式FPGA共用数据库实例，但使用独立的表。

使用方法：
1. 确保 PostgreSQL 已启动，且 fpga_static_analysis_filter 数据库已存在
2. 确保 backend/.env 文件已配置（会自动加载）
3. 运行: python init_postgresql.py
4. 或自动确认: python init_postgresql.py --yes

功能：
- 在 fpga_static_analysis_filter 库中创建 nm_fpga_analysis_tasks 表
- 在 fpga_static_analysis_filter 库中创建 nm_fpga_analysis_files 表
- 在 fpga_static_analysis_filter 库中创建 nm_fpga_analysis_functions 表
- 在 fpga_static_analysis_filter 库中创建 nm_fpga_analysis_problems 表
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

POSTGRES_HOST          = os.getenv("FPGA_POSTGRES_HOST",     "localhost")
POSTGRES_PORT          = int(os.getenv("FPGA_POSTGRES_PORT", "5432"))
POSTGRES_ADMIN_USER    = os.getenv("POSTGRES_ADMIN_USER",    "postgres")
POSTGRES_ADMIN_PASSWORD= os.getenv("POSTGRES_ADMIN_PASSWORD","123456")
DB_USER                = os.getenv("FPGA_POSTGRES_USER",     "fpga_analysis")
DB_PASSWORD            = os.getenv("FPGA_POSTGRES_PASSWORD", "123456")
DB_NAME                = os.getenv("FPGA_POSTGRES_DB",       "fpga_static_analysis_filter")

print(f"[配置] 目标数据库: {DB_NAME}  主机: {POSTGRES_HOST}:{POSTGRES_PORT}  用户: {DB_USER}")

# -------- 建表 DDL --------
CREATE_TABLES_SQL = """
-- 普通模式FPGA任务表
CREATE TABLE IF NOT EXISTS nm_fpga_analysis_tasks (
    id               SERIAL PRIMARY KEY,
    task_name        VARCHAR(255) NOT NULL,
    task_description TEXT,
    status           VARCHAR(50)  NOT NULL DEFAULT 'pending',
    progress         INTEGER      NOT NULL DEFAULT 0,
    total_files      INTEGER      NOT NULL DEFAULT 0,
    processed_files  INTEGER      NOT NULL DEFAULT 0,
    total_problems   INTEGER      NOT NULL DEFAULT 0,
    code_file_id     INTEGER,
    domain           VARCHAR(50)  NOT NULL DEFAULT 'normalModeFpga',
    created_at       TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMP    NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_nm_fpga_tasks_status ON nm_fpga_analysis_tasks(status);
CREATE INDEX IF NOT EXISTS idx_nm_fpga_tasks_domain ON nm_fpga_analysis_tasks(domain);

-- 普通模式FPGA文件表
CREATE TABLE IF NOT EXISTS nm_fpga_analysis_files (
    id           SERIAL PRIMARY KEY,
    task_id      INTEGER REFERENCES nm_fpga_analysis_tasks(id) ON DELETE CASCADE,
    file_path    VARCHAR(512) NOT NULL,
    extract_path VARCHAR(512),
    file_name    VARCHAR(255) NOT NULL,
    file_size    INTEGER,
    file_type    VARCHAR(50),
    status       VARCHAR(50)  NOT NULL DEFAULT 'uploaded',
    functions_count INTEGER   NOT NULL DEFAULT 0,
    file_count   INTEGER      NOT NULL DEFAULT 0,
    upload_time  TIMESTAMP    NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_nm_fpga_files_task_id ON nm_fpga_analysis_files(task_id);

-- 普通模式FPGA函数/文件单元表（FPGA按文件扫描，占位行）
CREATE TABLE IF NOT EXISTS nm_fpga_analysis_functions (
    id                   SERIAL PRIMARY KEY,
    file_id              INTEGER NOT NULL REFERENCES nm_fpga_analysis_files(id) ON DELETE CASCADE,
    function_name        VARCHAR(255) NOT NULL,
    start_line           INTEGER NOT NULL,
    end_line             INTEGER NOT NULL,
    source_code          TEXT    NOT NULL,
    analyzed             BOOLEAN NOT NULL DEFAULT FALSE,
    file_path            VARCHAR(512),
    function_description TEXT,
    commented_code       TEXT
);
CREATE INDEX IF NOT EXISTS idx_nm_fpga_functions_file_id ON nm_fpga_analysis_functions(file_id);

-- 普通模式FPGA问题表
CREATE TABLE IF NOT EXISTS nm_fpga_analysis_problems (
    id                      SERIAL PRIMARY KEY,
    task_id                 INTEGER NOT NULL REFERENCES nm_fpga_analysis_tasks(id) ON DELETE CASCADE,
    file_id                 INTEGER NOT NULL REFERENCES nm_fpga_analysis_files(id) ON DELETE CASCADE,
    function_id             INTEGER NOT NULL REFERENCES nm_fpga_analysis_functions(id) ON DELETE CASCADE,
    file_name               VARCHAR(255) NOT NULL,
    source_code             TEXT    NOT NULL,
    violation_rules         VARCHAR(255),
    issue_level             VARCHAR(50),
    issue_name              VARCHAR(255),
    issue_location          VARCHAR(255),
    description_requirement TEXT,
    description_issue       TEXT,
    description_location    TEXT,
    description_impact      TEXT,
    created_at              TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_nm_fpga_problems_task_id  ON nm_fpga_analysis_problems(task_id);
CREATE INDEX IF NOT EXISTS idx_nm_fpga_problems_file_id  ON nm_fpga_analysis_problems(file_id);
CREATE INDEX IF NOT EXISTS idx_nm_fpga_problems_func_id  ON nm_fpga_analysis_problems(function_id);
"""


def print_banner():
    print("=" * 70)
    print("  普通模式FPGA PostgreSQL 表初始化脚本".center(70))
    print(f"  目标数据库: {DB_NAME}".center(70))
    print("=" * 70)
    print()


def create_tables():
    print("[1/2] 连接到数据库...")
    try:
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
        print("    请确认 fpga_static_analysis_filter 数据库已存在，且用户密码正确")
        return False

    print("[2/2] 创建 nm_fpga_ 表...")
    try:
        cursor.execute(CREATE_TABLES_SQL)
        print("    OK nm_fpga_analysis_tasks       创建/已存在")
        print("    OK nm_fpga_analysis_files       创建/已存在")
        print("    OK nm_fpga_analysis_functions   创建/已存在")
        print("    OK nm_fpga_analysis_problems    创建/已存在")
        print()

        grant_sql = f"""
            GRANT ALL PRIVILEGES ON TABLE nm_fpga_analysis_tasks     TO {DB_USER};
            GRANT ALL PRIVILEGES ON TABLE nm_fpga_analysis_files     TO {DB_USER};
            GRANT ALL PRIVILEGES ON TABLE nm_fpga_analysis_functions TO {DB_USER};
            GRANT ALL PRIVILEGES ON TABLE nm_fpga_analysis_problems  TO {DB_USER};
            GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {DB_USER};
        """
        cursor.execute(grant_sql)
        print(f"    OK 已授予 '{DB_USER}' 对四张表的全部权限")
        print()

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"    ERROR 建表失败: {e}")
        import traceback
        traceback.print_exc()
        cursor.close()
        conn.close()
        return False


def verify_tables():
    """验证四张表是否存在"""
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
        )
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public' AND tablename LIKE 'nm_fpga_%'
            ORDER BY tablename
        """)
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()

        expected = {
            "nm_fpga_analysis_tasks",
            "nm_fpga_analysis_files",
            "nm_fpga_analysis_functions",
            "nm_fpga_analysis_problems",
        }
        missing = expected - set(tables)
        if missing:
            print(f"    WARNING 以下表未找到: {missing}")
            return False

        print("  验证结果（数据库中的 nm_fpga_ 表）：")
        for t in sorted(tables):
            print(f"    ✓ {t}")
        return True

    except Exception as e:
        print(f"    ERROR 验证失败: {e}")
        return False


def print_success():
    print("=" * 70)
    print("  OK 普通模式FPGA数据库表初始化完成".center(70))
    print("=" * 70)
    print()
    print("连接信息：")
    print(f"  主机:     {POSTGRES_HOST}:{POSTGRES_PORT}")
    print(f"  数据库:   {DB_NAME}")
    print(f"  用户:     {DB_USER}")
    print()
    print("已就绪的表：")
    print("  nm_fpga_analysis_tasks       普通模式FPGA任务")
    print("  nm_fpga_analysis_files       上传的FPGA代码压缩包记录")
    print("  nm_fpga_analysis_functions   FPGA文件扫描单元（占位行）")
    print("  nm_fpga_analysis_problems    FPGA扫描出的问题详情")
    print()
    print("后续步骤：重启后端服务即可，普通模式FPGA将自动写入以上四张表。")
    print()


def main():
    parser = argparse.ArgumentParser(description="普通模式FPGA PostgreSQL 表初始化")
    parser.add_argument("--yes", "-y", action="store_true", help="自动确认，跳过交互提示")
    args = parser.parse_args()

    print_banner()

    print(f"即将在数据库 '{DB_NAME}' 中创建以下四张表（已存在则跳过）：")
    print("  nm_fpga_analysis_tasks / nm_fpga_analysis_files / nm_fpga_analysis_functions / nm_fpga_analysis_problems")
    print()

    if not args.yes:
        resp = input("是否继续？(yes/no): ").strip().lower()
        if resp not in ("yes", "y"):
            print("\n已取消")
            sys.exit(0)
    else:
        print("自动确认模式：继续执行...")
    print()

    if not create_tables():
        sys.exit(1)

    print("正在验证表...")
    verify_tables()
    print()
    print_success()


if __name__ == "__main__":
    main()
