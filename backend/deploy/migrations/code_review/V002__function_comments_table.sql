-- =============================================================================
-- code_review 库 · V002 链路审查函数注释表
-- =============================================================================
-- 来源：app/codeReview/ConfigurationItem/db/数据库迁移.md（2026-06-02）
--       ORM 模型定义：db/models_chain.py → FunctionComment
-- 说明：依赖 code_review_tasks 已存在（由 create_all 或 --bootstrap 建立）。
-- =============================================================================

CREATE TABLE IF NOT EXISTS function_comments (
    id                   SERIAL PRIMARY KEY,
    task_id              INTEGER NOT NULL,
    file_path            VARCHAR(512) NOT NULL,
    function_name        VARCHAR(255) NOT NULL,
    function_description TEXT,
    commented_code       TEXT,
    status               VARCHAR(50) DEFAULT 'pending',
    created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_function_comments_task
        FOREIGN KEY (task_id) REFERENCES code_review_tasks(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_function_comments_task_id ON function_comments(task_id);
