-- =============================================================================
-- fpga_static_analysis_filter 库 · V001 基线（FPGA 静态分析）
-- =============================================================================
-- 本库与 static_analysis_filter 表名同构但库独立（用户 fpga_analysis）。
--
-- 合并来源：
--   * app/staticAnalysis/normalModeFpga/database/init_postgresql.py（nm_fpga_* 建表）
--   * app/staticAnalysis/filterFpga/database/postgresql_database.py :: migrate_database()
--   * app/staticAnalysis/filterFpga/database/migrate_accuracy_feedback.py
--   * app/staticAnalysis/filterFpga/database/数据库迁移.md
--   * app/staticAnalysis/filterFpga/database/navicat_add_field.sql
--   * app/staticAnalysis/filterFpga/database/add_is_selected_field.sql
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

ALTER TABLE fpga_rules ADD COLUMN IF NOT EXISTS accuracy_type VARCHAR(20) NOT NULL DEFAULT 'accurate';
CREATE INDEX IF NOT EXISTS idx_fpga_rules_accuracy ON fpga_rules(accuracy_type);

ALTER TABLE fpga_rules ADD COLUMN IF NOT EXISTS is_selected BOOLEAN DEFAULT TRUE;
CREATE INDEX IF NOT EXISTS idx_fpga_rules_is_selected ON fpga_rules(is_selected);
UPDATE fpga_rules SET is_selected = TRUE WHERE is_selected IS NULL;

-- =========================== B. 普通模式 nm_fpga_* 建表 ===========================

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

CREATE TABLE IF NOT EXISTS nm_fpga_analysis_files (
    id              SERIAL PRIMARY KEY,
    task_id         INTEGER REFERENCES nm_fpga_analysis_tasks(id) ON DELETE CASCADE,
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
CREATE INDEX IF NOT EXISTS idx_nm_fpga_files_task_id ON nm_fpga_analysis_files(task_id);

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
CREATE INDEX IF NOT EXISTS idx_nm_fpga_problems_task_id ON nm_fpga_analysis_problems(task_id);
CREATE INDEX IF NOT EXISTS idx_nm_fpga_problems_file_id ON nm_fpga_analysis_problems(file_id);
CREATE INDEX IF NOT EXISTS idx_nm_fpga_problems_func_id ON nm_fpga_analysis_problems(function_id);
