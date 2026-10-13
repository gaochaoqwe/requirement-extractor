-- =============================================================================
-- code_review_regression 库 · V002 函数配对表
-- =============================================================================
-- 来源：app/codeReview/RegressionTest/db/migrations/20251212_regression_dual_version_and_pairs.sql
--       （原文件被 database.py::migrate_database() 读取执行，此处纳入统一迁移）
-- =============================================================================

CREATE TABLE IF NOT EXISTS regression_test_function_pairs (
    id               SERIAL PRIMARY KEY,
    task_id          INTEGER NOT NULL REFERENCES regression_test_tasks(id) ON DELETE CASCADE,
    old_function_id  INTEGER NULL REFERENCES regression_test_functions(id) ON DELETE SET NULL,
    new_function_id  INTEGER NULL REFERENCES regression_test_functions(id) ON DELETE SET NULL,
    change_type      VARCHAR(20) NOT NULL,
    similarity_score DOUBLE PRECISION NULL,
    should_review    BOOLEAN NOT NULL DEFAULT TRUE,
    diff_summary     TEXT NULL,
    created_at       TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_regression_test_function_pairs_task_id
    ON regression_test_function_pairs(task_id);
CREATE INDEX IF NOT EXISTS idx_regression_test_function_pairs_old_function_id
    ON regression_test_function_pairs(old_function_id);
CREATE INDEX IF NOT EXISTS idx_regression_test_function_pairs_new_function_id
    ON regression_test_function_pairs(new_function_id);
