-- =============================================================================
-- code_review_regression 库 · V001 基线（历史增量合并）
-- =============================================================================
-- 合并来源：
--   * app/codeReview/RegressionTest/db/database.py :: migrate_database()
--   * app/codeReview/RegressionTest/db/database_chain.py
--   * app/codeReview/RegressionTest/db/migrations/20251212_regression_dual_version_and_pairs.sql
--   * app/codeReview/RegressionTest/REGRESSION_TEST_DEVELOPMENT_PLAN.md
--
-- 本库与 code_review 表结构同构但库独立（用户同为 code_review）。
--
-- 注意：
--   1) 基础表 regression_test_* 由 create_all 建立。
--   2) 【修正】原 database_chain.py 把链路审查补列写成了 chain_review_problems
--      （那是 code_review 库的表名），在本库不存在、迁移静默失败。此处更正为
--      regression_test_chain_problems。
--   3) 本文件所有语句均幂等。
-- =============================================================================

-- ---- 函数 / 文件 / 问题 / 任务 补列 ----
ALTER TABLE regression_test_functions ADD COLUMN IF NOT EXISTS function_description TEXT;
ALTER TABLE regression_test_functions ADD COLUMN IF NOT EXISTS commented_code TEXT;

ALTER TABLE regression_test_files ADD COLUMN IF NOT EXISTS file_function_summary TEXT;

ALTER TABLE regression_test_problems ADD COLUMN IF NOT EXISTS problem_status INTEGER DEFAULT 1 NOT NULL;
CREATE INDEX IF NOT EXISTS idx_regression_test_problems_status ON regression_test_problems(problem_status);

ALTER TABLE regression_test_tasks ADD COLUMN IF NOT EXISTS paused_at TIMESTAMP NULL;
ALTER TABLE regression_test_tasks ADD COLUMN IF NOT EXISTS execution_context TEXT NULL;
ALTER TABLE regression_test_tasks ADD COLUMN IF NOT EXISTS tester_name VARCHAR(100) NULL;

-- ---- 双版本上传与函数配对（2025-12-12）----
ALTER TABLE regression_test_files ADD COLUMN IF NOT EXISTS version VARCHAR(20);
ALTER TABLE regression_test_files ADD COLUMN IF NOT EXISTS task_upload_order INTEGER;

ALTER TABLE regression_test_functions ADD COLUMN IF NOT EXISTS version VARCHAR(20);
ALTER TABLE regression_test_functions ADD COLUMN IF NOT EXISTS change_type VARCHAR(20);
ALTER TABLE regression_test_functions ADD COLUMN IF NOT EXISTS paired_function_id INTEGER;
ALTER TABLE regression_test_functions ADD COLUMN IF NOT EXISTS code_diff TEXT;

-- ---- 链路审查（表名修正）----
ALTER TABLE regression_test_chain_problems ADD COLUMN IF NOT EXISTS chain_function_description TEXT;
