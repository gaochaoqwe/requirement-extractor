-- ========================================================
-- 在 Navicat 中执行的 SQL 脚本
-- 为 fpga_rules 表添加 is_selected 字段
-- ========================================================

-- 1. 添加 is_selected 字段（默认值为 TRUE，表示默认勾选）
ALTER TABLE fpga_rules 
ADD COLUMN IF NOT EXISTS is_selected BOOLEAN DEFAULT TRUE;

-- 2. 创建索引（提高查询性能）
CREATE INDEX IF NOT EXISTS idx_fpga_rules_is_selected ON fpga_rules(is_selected);

-- 3. 初始化所有现有规则的 is_selected 为 TRUE
UPDATE fpga_rules 
SET is_selected = TRUE 
WHERE is_selected IS NULL;

-- 4. 查看更新后的统计信息
SELECT 
    COUNT(*) as total_rules,
    COUNT(*) FILTER (WHERE is_selected = TRUE) as selected_rules,
    COUNT(*) FILTER (WHERE is_selected = FALSE) as unselected_rules
FROM fpga_rules;
