-- 新增 Verilog 一般准则（默认标记为不确定）
-- 使用方式：在 Navicat 连接对应 PostgreSQL 数据库后直接执行
-- 说明：
-- 1. 这些规则编码采用 Excel 中的实际格式，如 5.9.1.a
-- 2. 全部 language = 'Verilog'
-- 3. 全部默认 accuracy_type = 'uncertain'
-- 4. 使用 ON CONFLICT(rule_code) DO UPDATE，重复执行也安全

INSERT INTO fpga_rules (
    rule_code,
    rule_content,
    language,
    rule_type,
    category,
    chapter,
    sequence,
    accuracy_type,
    issue_title,
    impact_analysis,
    fix_suggestion,
    created_at,
    updated_at
)
VALUES
    ('5.9.1.a', '不应存在冗余代码，提高代码的可读性和可维护性。', 'Verilog', 'advisory', 'Verilog一般准则', '5.9.1', 1, 'uncertain', NULL, NULL, NULL, NOW(), NOW()),
    ('5.9.1.b', '宜采用层次化设计方式开展逻辑软件设计，结构的层次不宜太深，不宜超过5层。较为合理的顶层模块由输入输出管脚声明、模块的调用和实例化、全局时钟资源、全局置位／复位、三态缓冲和一些简单的组合逻辑构成，不允许建立子模块间跨层次的接口。', 'Verilog', 'advisory', 'Verilog一般准则', '5.9.1', 2, 'uncertain', NULL, NULL, NULL, NOW(), NOW()),
    ('5.9.1.c', '组合逻辑模块的输出信号不应直接通过层次关系间接连接到同一模块的输入端口。', 'Verilog', 'advisory', 'Verilog一般准则', '5.9.1', 3, 'uncertain', NULL, NULL, NULL, NOW(), NOW()),

    ('5.9.2.a', '不宜在时钟路径上插入反相器或缓冲器，在时钟路径上插入反相器或缓存器会增加时钟信号的偏移，引起时序错误。', 'Verilog', 'advisory', 'Verilog一般准则', '5.9.2', 4, 'uncertain', NULL, NULL, NULL, NOW(), NOW()),
    ('5.9.2.b', '时钟信号不应再汇聚，再汇聚路径将导致时钟路径上发生时序冲突。', 'Verilog', 'advisory', 'Verilog一般准则', '5.9.2', 5, 'uncertain', NULL, NULL, NULL, NOW(), NOW()),
    ('5.9.2.c', '不宜使用行波时钟，行波时钟在行波链上各触发器时钟之间会产生较大的时钟偏移，降低系统的实际速度，并且有可能超出最坏情况下的建立时间、保持时间。', 'Verilog', 'advisory', 'Verilog一般准则', '5.9.2', 6, 'uncertain', NULL, NULL, NULL, NOW(), NOW()),

    ('5.9.3.a', '异步复位建议采用同步释放的方式，可避免异步复位释放时的亚稳态。', 'Verilog', 'advisory', 'Verilog一般准则', '5.9.3', 7, 'uncertain', NULL, NULL, NULL, NOW(), NOW()),
    ('5.9.3.b', '设计中建议使用同一复位域，存在多个复位域可能影响设计的初始状态，引起信号的冲突。', 'Verilog', 'advisory', 'Verilog一般准则', '5.9.3', 8, 'uncertain', NULL, NULL, NULL, NOW(), NOW()),
    ('5.9.3.c', '同一复位信号应使用唯一的有效电平，保证系统模块同时复位。', 'Verilog', 'advisory', 'Verilog一般准则', '5.9.3', 9, 'uncertain', NULL, NULL, NULL, NOW(), NOW()),
    ('5.9.3.d', '应保证一定长度的复位有效时间，确保复位信号能被正确采样。', 'Verilog', 'advisory', 'Verilog一般准则', '5.9.3', 10, 'uncertain', NULL, NULL, NULL, NOW(), NOW()),

    ('5.9.4.a', '状态机的跳转不应依赖外部信号。', 'Verilog', 'advisory', 'Verilog一般准则', '5.9.4', 11, 'uncertain', NULL, NULL, NULL, NOW(), NOW()),
    ('5.9.4.b', '根据状态机对速度、资源占用量等方面的要求，合理使用状态及编码。', 'Verilog', 'advisory', 'Verilog一般准则', '5.9.4', 12, 'uncertain', NULL, NULL, NULL, NOW(), NOW()),

    ('5.9.5.a', '决定重用某逻辑软件或使用 IP 核来完成安全关键功能之前，应确定其适用性，并充分分析其安全性影响。', 'Verilog', 'advisory', 'Verilog一般准则', '5.9.5', 13, 'uncertain', NULL, NULL, NULL, NOW(), NOW()),
    ('5.9.5.b', '应对 IP 核使用进行版本控制，在 IP 核的调用语句后添加版本号注释。', 'Verilog', 'advisory', 'Verilog一般准则', '5.9.5', 14, 'uncertain', NULL, NULL, NULL, NOW(), NOW())
ON CONFLICT (rule_code) DO UPDATE SET
    rule_content = EXCLUDED.rule_content,
    language = EXCLUDED.language,
    rule_type = EXCLUDED.rule_type,
    category = EXCLUDED.category,
    chapter = EXCLUDED.chapter,
    sequence = EXCLUDED.sequence,
    accuracy_type = EXCLUDED.accuracy_type,
    updated_at = NOW();

