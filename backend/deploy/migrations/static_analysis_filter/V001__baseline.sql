-- =============================================================================
-- static_analysis_filter 库 · V001 基线（C 语言静态分析）
-- =============================================================================
-- 本库存放两套表：
--   A. 工具模式（filter）：static_analysis_* / gjb8114_* / cwe_*  —— 由 ORM create_all 建立
--   B. 普通模式（normalModeC）：nm_*  —— 手写 SQL，此处作为权威基线
--
-- 合并来源：
--   * app/staticAnalysis/normalModeC/database/init_postgresql.py（nm_* 建表）
--   * app/staticAnalysis/filter/database/postgresql_database.py :: migrate_database()
--   * app/staticAnalysis/filter/database/migrate_accuracy_feedback.py
--   * app/staticAnalysis/filter/database/数据库迁移.md
--
-- 本文件所有语句均幂等。
-- =============================================================================

-- =========================== A. 工具模式增量 ===========================

ALTER TABLE static_analysis_issues ADD COLUMN IF NOT EXISTS problem_status INTEGER DEFAULT 1 NOT NULL;
CREATE INDEX IF NOT EXISTS idx_static_analysis_issues_status ON static_analysis_issues(problem_status);

ALTER TABLE static_analysis_sessions ADD COLUMN IF NOT EXISTS operator_name VARCHAR(100) NULL;
ALTER TABLE static_analysis_sessions ADD COLUMN IF NOT EXISTS problem_sheet_accuracy_rate VARCHAR(50);
ALTER TABLE static_analysis_sessions ADD COLUMN IF NOT EXISTS problem_sheet_feedback_at TIMESTAMP;
ALTER TABLE static_analysis_sessions ADD COLUMN IF NOT EXISTS marked_problems_exported BOOLEAN DEFAULT FALSE;

ALTER TABLE gjb8114_rules ADD COLUMN IF NOT EXISTS is_selected BOOLEAN DEFAULT TRUE;
CREATE INDEX IF NOT EXISTS idx_gjb_rules_is_selected ON gjb8114_rules(is_selected);
UPDATE gjb8114_rules SET is_selected = TRUE WHERE is_selected IS NULL;

ALTER TABLE cwe_rules ADD COLUMN IF NOT EXISTS is_selected BOOLEAN DEFAULT TRUE;
CREATE INDEX IF NOT EXISTS idx_cwe_rules_is_selected ON cwe_rules(is_selected);
UPDATE cwe_rules SET is_selected = TRUE WHERE is_selected IS NULL;

-- =========================== B. 普通模式 nm_* 建表 ===========================

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

CREATE TABLE IF NOT EXISTS nm_analysis_files (
    id              SERIAL PRIMARY KEY,
    task_id         INTEGER REFERENCES nm_analysis_tasks(id) ON DELETE CASCADE,
    file_path       VARCHAR(512) NOT NULL,
    extract_path    VARCHAR(512),
    file_name       VARCHAR(255) NOT NULL,
    file_size       INTEGER,
    file_type       VARCHAR(50),
    status          VARCHAR(50)  NOT NULL DEFAULT 'uploaded',
    functions_count INTEGER      NOT NULL DEFAULT 0,
    file_count      INTEGER      NOT NULL DEFAULT 0,
    upload_time     TIMESTAMP    NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_nm_files_task_id ON nm_analysis_files(task_id);

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
CREATE INDEX IF NOT EXISTS idx_nm_problems_task_id ON nm_analysis_problems(task_id);
CREATE INDEX IF NOT EXISTS idx_nm_problems_file_id ON nm_analysis_problems(file_id);

-- 说明：普通模式刻意不为 nm_analysis_problems.function_id 建外键
-- （function_id=0 表示 FPGA 模式占位行，加约束会插入失败）。
-- 原 init_postgresql.py 中该外键被注释掉，normalModeC/数据库迁移.md 却要求建，
-- 属文档与代码不一致，此处以代码为准：不建。
