-- ========================================================
-- FPGA规则表添加 is_selected 字段的 SQL 脚本
-- 用于在 Navicat 或 PostgreSQL 中手动执行
-- ========================================================

-- 1. 添加 is_selected 字段到 fpga_rules 表（如果不存在）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'fpga_rules' AND column_name = 'is_selected'
    ) THEN
        ALTER TABLE fpga_rules 
        ADD COLUMN is_selected BOOLEAN DEFAULT TRUE;
        
        RAISE NOTICE '已添加 is_selected 字段到 fpga_rules 表';
    ELSE
        RAISE NOTICE 'is_selected 字段已存在，跳过添加';
    END IF;
END $$;

-- 2. 创建索引（如果不存在）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'idx_fpga_rules_is_selected'
    ) THEN
        CREATE INDEX idx_fpga_rules_is_selected ON fpga_rules(is_selected);
        RAISE NOTICE '已创建 idx_fpga_rules_is_selected 索引';
    ELSE
        RAISE NOTICE '索引 idx_fpga_rules_is_selected 已存在，跳过创建';
    END IF;
END $$;

-- 3. 初始化所有现有规则的 is_selected 为 TRUE（默认勾选）
UPDATE fpga_rules 
SET is_selected = TRUE 
WHERE is_selected IS NULL;

-- 4. 查看更新后的统计信息
SELECT 
    COUNT(*) as total_rules,
    COUNT(*) FILTER (WHERE is_selected = TRUE) as selected_rules,
    COUNT(*) FILTER (WHERE is_selected = FALSE) as unselected_rules
FROM fpga_rules;

-- ========================================================
-- 可选：根据当前配置文件更新 is_selected 状态
-- 如果你希望将当前配置文件中勾选的规则同步到数据库，
-- 请先查看配置文件中的规则列表，然后执行以下 UPDATE 语句：
-- ========================================================

/*
-- 步骤 1：先将所有规则设为未勾选
UPDATE fpga_rules SET is_selected = FALSE;

-- 步骤 2：将配置文件中勾选的规则设为已勾选
-- 请从 default_selected_rules.json 文件中复制 gjb_rules 数组内容
-- 替换下面的规则代码列表
UPDATE fpga_rules 
SET is_selected = TRUE 
WHERE rule_code IN (
    'A-1-2', 'A-1-3', 'A-1-4', 'A-2-1', 'A-2-2', ... -- 粘贴配置文件中的规则代码
);
*/
