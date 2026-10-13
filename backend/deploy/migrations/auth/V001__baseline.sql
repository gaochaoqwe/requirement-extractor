-- =============================================================================
-- auth 库 · V001 基线
-- =============================================================================
-- 来源：backend/app/auth/db/init_postgresql.py（create_users_table）
-- 说明：auth 库表结构为手写 SQL（非 ORM），此处作为权威基线。
--       字段与 init_postgresql.py 完全一致，保持幂等。
-- =============================================================================

CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    username      VARCHAR(50)  UNIQUE NOT NULL,
    password_hash VARCHAR(64)  NOT NULL,
    display_name  VARCHAR(100) NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login    TIMESTAMP,
    is_active     BOOLEAN DEFAULT TRUE
);
