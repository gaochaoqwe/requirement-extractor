-- =============================================================================
-- code_review 库 · V001 基线（历史增量合并）
-- =============================================================================
-- 合并来源（原先分散在代码 / md 文档 / Navicat 手工执行三处）：
--   * app/codeReview/ConfigurationItem/db/database.py      :: migrate_database()
--   * app/codeReview/ConfigurationItem/db/database_chain.py
--   * app/codeReview/ConfigurationItem/db/数据库迁移.md
--   * 部署方案.md（2026-5-12 注释准确率反馈）
--
-- 注意：
--   1) 基础表（code_review_tasks/files/functions/problems/features/... ）
--      由 SQLAlchemy Base.metadata.create_all 建立，create_all 只建表不补列，
--      所以「加列」必须走这里。
--   2) 本文件所有语句均幂等，重复执行安全。
--   3) 【补齐】has_marked_problems / marked_problem_count / marked_problems_exported
--      原仅存在于 数据库迁移.md 与 ORM 模型，代码 migrate_database() 里没有对应
--      ALTER，导致老库升级不补列。本迁移补上，消除该不一致。
-- =============================================================================

-- ---- code_review_functions ----
ALTER TABLE code_review_functions ADD COLUMN IF NOT EXISTS function_description TEXT;
ALTER TABLE code_review_functions ADD COLUMN IF NOT EXISTS commented_code TEXT;

-- ---- code_review_files ----
ALTER TABLE code_review_files ADD COLUMN IF NOT EXISTS file_function_summary TEXT;

-- ---- code_review_problems ----
ALTER TABLE code_review_problems ADD COLUMN IF NOT EXISTS problem_status INTEGER DEFAULT 1 NOT NULL;
CREATE INDEX IF NOT EXISTS idx_code_review_problems_status ON code_review_problems(problem_status);

ALTER TABLE code_review_problems ADD COLUMN IF NOT EXISTS problem_source VARCHAR(64) DEFAULT 'main_review';
CREATE INDEX IF NOT EXISTS idx_code_review_problems_source ON code_review_problems(problem_source);
UPDATE code_review_problems
   SET problem_source = 'main_review'
 WHERE problem_source IS NULL OR problem_source = '';

-- ---- code_review_tasks：任务恢复 / 测试人员 / 标记问题统计 / 注释准确率反馈 ----
ALTER TABLE code_review_tasks ADD COLUMN IF NOT EXISTS paused_at TIMESTAMP NULL;
ALTER TABLE code_review_tasks ADD COLUMN IF NOT EXISTS execution_context TEXT NULL;
ALTER TABLE code_review_tasks ADD COLUMN IF NOT EXISTS tester_name VARCHAR(100) NULL;

ALTER TABLE code_review_tasks ADD COLUMN IF NOT EXISTS has_marked_problems BOOLEAN DEFAULT FALSE;
ALTER TABLE code_review_tasks ADD COLUMN IF NOT EXISTS marked_problem_count INTEGER DEFAULT 0;
ALTER TABLE code_review_tasks ADD COLUMN IF NOT EXISTS marked_problems_exported BOOLEAN DEFAULT FALSE;

ALTER TABLE code_review_tasks ADD COLUMN IF NOT EXISTS comment_accuracy_rate VARCHAR(50) NULL;
ALTER TABLE code_review_tasks ADD COLUMN IF NOT EXISTS comment_accuracy_feedback_at TIMESTAMP NULL;
ALTER TABLE code_review_tasks ADD COLUMN IF NOT EXISTS clicked_function_count INTEGER DEFAULT 0;
ALTER TABLE code_review_tasks ADD COLUMN IF NOT EXISTS feedback_delayed_count INTEGER DEFAULT 0;

-- ---- 链路审查 ----
ALTER TABLE chain_review_problems ADD COLUMN IF NOT EXISTS chain_function_description TEXT;
