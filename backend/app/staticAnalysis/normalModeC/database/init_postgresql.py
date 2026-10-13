"""
普通模式静态分析 PostgreSQL 表初始化脚本

在 static_analysis_filter 数据库中创建普通模式所需的四张 nm_ 表。
不会创建新的数据库或用户，直接复用工具模式的 PostgreSQL 实例。

使用方法：
1. 确保 PostgreSQL 已启动，且 static_analysis_filter 数据库已存在
2. 确保 backend/.env 文件已配置（会自动加载）
3. 运行: python init_postgresql.py
4. 或自动确认: python init_postgresql.py --yes

功能：
- 在 static_analysis_filter 库中创建 nm_analysis_tasks 表
- 在 static_analysis_filter 库中创建 nm_analysis_files 表
- 在 static_analysis_filter 库中创建 nm_analysis_functions 表
- 在 static_analysis_filter 库中创建 nm_analysis_problems 表
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
POSTGRES_ADMIN_USER    = os.getenv("POSTGRES_ADMIN_USER",      "postgres")
POSTGRES_ADMIN_PASSWORD= os.getenv("POSTGRES_ADMIN_PASSWORD",  "123456")
DB_USER                = os.getenv("STATIC_POSTGRES_USER",     "static_analysis")
DB_PASSWORD            = os.getenv("STATIC_POSTGRES_PASSWORD", "123456")
DB_NAME                = os.getenv("STATIC_POSTGRES_DB",       "static_analysis_filter")

print(f"[配置] 目标数据库: {DB_NAME}  主机: {POSTGRES_HOST}:{POSTGRES_PORT}  用户: {DB_USER}")

# -------- 建表 DDL --------
CREATE_TABLES_SQL = """
-- 普通模式任务表
CREATE TABLE IF NOT EXISTS nm_analysis_tasks (
    id               SERIAL PRIMARY KEY,
    task_name        VARCHAR(255) NOT NULL,
    task_description TEXT,
    status           VARCHAR(50)  NOT NULL DEFAULT 'pending',
    progress         INTEGER      NOT NULL DEFAULT 0,
    total_files      INTEGER      NOT NULL DEFAULT 0,
    processed_files  INTEGER      NOT NULL DEFAULT 0,
    total_problems   INTEGER      NOT NULL DEFAULT 0,
    code_file_id     INTEGER,
    domain           VARCHAR(50)  NOT NULL DEFAULT 'normalModeC',
    created_at       TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMP    NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_nm_tasks_status ON nm_analysis_tasks(status);
CREATE INDEX IF NOT EXISTS idx_nm_tasks_domain ON nm_analysis_tasks(domain);

-- 普通模式文件表
CREATE TABLE IF NOT EXISTS nm_analysis_files (
    id           SERIAL PRIMARY KEY,
    task_id      INTEGER REFERENCES nm_analysis_tasks(id) ON DELETE CASCADE,
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
CREATE INDEX IF NOT EXISTS idx_nm_files_task_id ON nm_analysis_files(task_id);

-- 普通模式函数表（C 模式按函数扫描，FPGA 可存占位行）
CREATE TABLE IF NOT EXISTS nm_analysis_functions (
    id                   SERIAL PRIMARY KEY,
    file_id              INTEGER NOT NULL REFERENCES nm_analysis_files(id) ON DELETE CASCADE,
    function_name        VARCHAR(255) NOT NULL,
    start_line           INTEGER NOT NULL,
    end_line             INTEGER NOT NULL,
    source_code          TEXT    NOT NULL,
    analyzed             BOOLEAN NOT NULL DEFAULT FALSE,
    file_path            VARCHAR(512),
    function_description TEXT,
    commented_code       TEXT
);
CREATE INDEX IF NOT EXISTS idx_nm_functions_file_id ON nm_analysis_functions(file_id);

-- 普通模式问题表
CREATE TABLE IF NOT EXISTS nm_analysis_problems (
    id                      SERIAL PRIMARY KEY,
    task_id                 INTEGER NOT NULL REFERENCES nm_analysis_tasks(id) ON DELETE CASCADE,
    file_id                 INTEGER NOT NULL REFERENCES nm_analysis_files(id) ON DELETE CASCADE,
    function_id             INTEGER NOT NULL DEFAULT 0,
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
CREATE INDEX IF NOT EXISTS idx_nm_problems_task_id  ON nm_analysis_problems(task_id);
CREATE INDEX IF NOT EXISTS idx_nm_problems_file_id  ON nm_analysis_problems(file_id);

-- 补充外键：问题 -> 函数（function_id=0 表示 FPGA 模式占位，跳过约束检查）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_nm_problems_function'
    ) THEN
        -- 只在 function_id != 0 时实际引用，此处仅记录注释，不强制外键
        -- 如需严格约束可取消下面注释
        -- ALTER TABLE nm_analysis_problems
        --     ADD CONSTRAINT fk_nm_problems_function
        --     FOREIGN KEY (function_id) REFERENCES nm_analysis_functions(id) ON DELETE CASCADE;
        RAISE NOTICE 'fk_nm_problems_function 未添加（FPGA 兼容模式）';
    END IF;
END$$;
"""


def print_banner():
    print("=" * 70)
    print("  普通模式静态分析 PostgreSQL 表初始化脚本".center(70))
    print(f"  目标数据库: {DB_NAME}".center(70))
    print("=" * 70)
    print()


def check_database_exists(cursor):
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
    return cursor.fetchone() is not None


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
        print("    请确认 static_analysis_filter 数据库已存在，且用户密码正确")
        return False

    print("[2/2] 创建 nm_ 表...")
    try:
        cursor.execute(CREATE_TABLES_SQL)
        print("    OK nm_analysis_tasks       创建/已存在")
        print("    OK nm_analysis_files       创建/已存在")
        print("    OK nm_analysis_functions   创建/已存在")
        print("    OK nm_analysis_problems    创建/已存在")
        print()

        # 授予用户权限（防止用 postgres 超级用户建表后 static_analysis 无权访问）
        grant_sql = f"""
            GRANT ALL PRIVILEGES ON TABLE nm_analysis_tasks     TO {DB_USER};
            GRANT ALL PRIVILEGES ON TABLE nm_analysis_files     TO {DB_USER};
            GRANT ALL PRIVILEGES ON TABLE nm_analysis_functions TO {DB_USER};
            GRANT ALL PRIVILEGES ON TABLE nm_analysis_problems  TO {DB_USER};
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
            WHERE schemaname = 'public' AND tablename LIKE 'nm_%'
            ORDER BY tablename
        """)
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()

        expected = {
            "nm_analysis_tasks",
            "nm_analysis_files",
            "nm_analysis_functions",
            "nm_analysis_problems",
        }
        missing = expected - set(tables)
        if missing:
            print(f"    WARNING 以下表未找到: {missing}")
            return False

        print("  验证结果（数据库中的 nm_ 表）：")
        for t in sorted(tables):
            print(f"    ✓ {t}")
        return True

    except Exception as e:
        print(f"    ERROR 验证失败: {e}")
        return False


def print_success():
    print("=" * 70)
    print("  OK 普通模式数据库表初始化完成".center(70))
    print("=" * 70)
    print()
    print("连接信息：")
    print(f"  主机:     {POSTGRES_HOST}:{POSTGRES_PORT}")
    print(f"  数据库:   {DB_NAME}")
    print(f"  用户:     {DB_USER}")
    print()
    print("已就绪的表：")
    print("  nm_analysis_tasks       普通模式任务（含 domain 字段区分 C/FPGA）")
    print("  nm_analysis_files       上传的代码压缩包记录")
    print("  nm_analysis_functions   C 模式函数扫描单元（FPGA 使用占位行）")
    print("  nm_analysis_problems    扫描出的问题详情")
    print()
    print("后续步骤：重启后端服务即可，普通模式将自动写入以上四张表。")
    print()


def main():
    parser = argparse.ArgumentParser(description="普通模式静态分析 PostgreSQL 表初始化")
    parser.add_argument("--yes", "-y", action="store_true", help="自动确认，跳过交互提示")
    args = parser.parse_args()

    print_banner()

    print(f"即将在数据库 '{DB_NAME}' 中创建以下四张表（已存在则跳过）：")
    print("  nm_analysis_tasks / nm_analysis_files / nm_analysis_functions / nm_analysis_problems")
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
