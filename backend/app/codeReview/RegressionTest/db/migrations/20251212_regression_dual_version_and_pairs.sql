-- RegressionTest schema upgrade: dual version upload & function pairing

-- 1) regression_test_files: add version info
ALTER TABLE regression_test_files
  ADD COLUMN IF NOT EXISTS version VARCHAR(20);

ALTER TABLE regression_test_files
  ADD COLUMN IF NOT EXISTS task_upload_order INTEGER;


-- 2) regression_test_functions: add diff/pairing info
ALTER TABLE regression_test_functions
  ADD COLUMN IF NOT EXISTS version VARCHAR(20);

ALTER TABLE regression_test_functions
  ADD COLUMN IF NOT EXISTS change_type VARCHAR(20);

ALTER TABLE regression_test_functions
  ADD COLUMN IF NOT EXISTS paired_function_id INTEGER;

ALTER TABLE regression_test_functions
  ADD COLUMN IF NOT EXISTS code_diff TEXT;


-- 3) new table: regression_test_function_pairs
CREATE TABLE IF NOT EXISTS regression_test_function_pairs (
  id SERIAL PRIMARY KEY,
  task_id INTEGER NOT NULL REFERENCES regression_test_tasks(id) ON DELETE CASCADE,
  old_function_id INTEGER NULL REFERENCES regression_test_functions(id) ON DELETE SET NULL,
  new_function_id INTEGER NULL REFERENCES regression_test_functions(id) ON DELETE SET NULL,
  change_type VARCHAR(20) NOT NULL,
  similarity_score DOUBLE PRECISION NULL,
  should_review BOOLEAN NOT NULL DEFAULT TRUE,
  diff_summary TEXT NULL,
  created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_regression_test_function_pairs_task_id
  ON regression_test_function_pairs(task_id);

CREATE INDEX IF NOT EXISTS idx_regression_test_function_pairs_old_function_id
  ON regression_test_function_pairs(old_function_id);

CREATE INDEX IF NOT EXISTS idx_regression_test_function_pairs_new_function_id
  ON regression_test_function_pairs(new_function_id);
