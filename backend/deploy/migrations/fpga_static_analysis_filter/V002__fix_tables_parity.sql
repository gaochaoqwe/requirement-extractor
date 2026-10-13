-- =============================================================================
-- fpga_static_analysis_filter 库 · V002 自动修复功能表（结构对齐）
-- =============================================================================
-- 来源：app/staticAnalysis/filterFpga/database/数据库迁移.md
--
-- 说明：自动修复功能当前仅 C 语言模块（static_analysis_filter）投入使用，
--       FPGA 代码里没有 fix 相关模型。此处建表仅为「保持两库结构一致」
--       （全部 IF NOT EXISTS，幂等，无副作用）。
--       若确认 FPGA 永不使用该功能，可删除本文件。
-- =============================================================================

CREATE TABLE IF NOT EXISTS static_analysis_fix_tasks (
    id           SERIAL PRIMARY KEY,
    task_id      INTEGER NOT NULL,
    rule_type    VARCHAR(20),
    scope_type   VARCHAR(20),
    scope_value  TEXT,
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
    status           VARCHAR(20) DEFAULT 'generated',
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
