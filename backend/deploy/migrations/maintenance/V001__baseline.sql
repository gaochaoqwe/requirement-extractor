-- =============================================================================
-- maintenance 库 · V001 基线
-- =============================================================================
-- 来源：app/maintenance/db/database.py :: create_tables()
-- 说明：本库表结构为手写 SQL（非 ORM），此处作为权威基线。全部幂等。
-- =============================================================================

CREATE TABLE IF NOT EXISTS maintenance_announcement_snooze (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL,
    announcement_id VARCHAR(64) NOT NULL,
    snooze_until    TIMESTAMP NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, announcement_id)
);

CREATE TABLE IF NOT EXISTS maintenance_feedback (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL,
    type        VARCHAR(32) NOT NULL,
    module      VARCHAR(128),
    content     TEXT NOT NULL,
    page_url    TEXT,
    status      VARCHAR(32) NOT NULL DEFAULT 'open',
    admin_reply TEXT,
    replied_by  INTEGER,
    replied_at  TIMESTAMP,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 兼容旧库补列
ALTER TABLE maintenance_feedback ADD COLUMN IF NOT EXISTS module VARCHAR(128);
ALTER TABLE maintenance_feedback ADD COLUMN IF NOT EXISTS admin_reply TEXT;
ALTER TABLE maintenance_feedback ADD COLUMN IF NOT EXISTS replied_by INTEGER;
ALTER TABLE maintenance_feedback ADD COLUMN IF NOT EXISTS replied_at TIMESTAMP;

-- 索引
CREATE INDEX IF NOT EXISTS idx_maintenance_feedback_user_id_created_at
    ON maintenance_feedback(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_maintenance_feedback_replied_by
    ON maintenance_feedback(replied_by);
CREATE INDEX IF NOT EXISTS idx_maintenance_announcement_snooze_user_id
    ON maintenance_announcement_snooze(user_id);
