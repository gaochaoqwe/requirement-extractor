-- =============================================================================
-- static_analysis_filter 库 · V002 自动修复功能表（C 语言 / GJB8114）
-- =============================================================================
-- 来源：
--   * app/staticAnalysis/filter/database/fix_migration.py :: ensure_fix_schema()
--   * app/staticAnalysis/filter/database/数据库迁移.md
--   * ORM 模型：app/staticAnalysis/filter/models/models.py
--                （StaticAnalysisFixTask / StaticAnalysisFix）
--
-- 说明：static_analysis_fix_tasks / static_analysis_fixes 由 ORM create_all 建立；
--       本迁移主要补 static_analysis_issues 的两个新列（create_all 不会给老表补列）。
--       三张表的 DDL 一并写出，保证未启动过后端的环境也能就绪。幂等。
-- =============================================================================

CREATE TABLE IF NOT EXISTS static_analysis_fix_tasks (
    id           SERIAL PRIMARY KEY,
    task_id      INTEGER NOT NULL,
    rule_type    VARCHAR(20),
    scope_type   VARCHAR(20),          -- single / file / rule
    scope_value  TEXT,                 -- problem_id / file_path / rule_code
    user_prompt  TEXT,
    options_json TEXT,
    status       VARCHAR(20) DEFAULT 'pending',
    total        INTEGER DEFAULT 0,
    succeeded    INTEGER DEFAULT 0,
    failed       INTEGER DEFAULT 0,
    conflicted   INTEGER DEFAULT 0,
    created_by   VARCHAR(100),
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_fix_tasks_task_id ON static_analysis_fix_tasks(task_id);

CREATE TABLE IF NOT EXISTS static_analysis_fixes (
    id               SERIAL PRIMARY KEY,
    fix_task_id      INTEGER NOT NULL,
    problem_id       INTEGER,
    file_path        VARCHAR(512),
    line_no          INTEGER,
    rule_code        VARCHAR(50),
    rule_type        VARCHAR(20),
    original_snippet TEXT,
    fixed_snippet    TEXT,
    diff_text        TEXT,
    ai_explanation   TEXT,
    can_fix          BOOLEAN DEFAULT FALSE,
    confidence       DOUBLE PRECISION,
    status           VARCHAR(20) DEFAULT 'generated',  -- generated/applied/conflict/failed/rolled_back
    error_message    TEXT,
    raw_response     TEXT,
    backup_path      VARCHAR(512),
    applied_at       TIMESTAMP,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_fixes_task_id ON static_analysis_fixes(fix_task_id);
CREATE INDEX IF NOT EXISTS idx_fixes_problem_id ON static_analysis_fixes(problem_id);

ALTER TABLE static_analysis_issues ADD COLUMN IF NOT EXISTS fix_status INTEGER DEFAULT 0;
ALTER TABLE static_analysis_issues ADD COLUMN IF NOT EXISTS fix_id INTEGER;
CREATE INDEX IF NOT EXISTS idx_issues_fix_status ON static_analysis_issues(fix_status);
