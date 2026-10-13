# 函数审查报告 — tiny_test / math_utils.c

- 模式：function（函数审查）
- 索引 taskId：`mv0qr73np7saf6`（9 个函数，13 条调用边，均由 code-review-index 生成）
- 范围：`math_utils.c`（`math_utils.h` 仅声明，无函数体）
- 问题类型目录：function-review `check-catalog.json`（11 类，未发明新类型）
- 说明：仅给出问题、位置与建议方向，是否采纳、反馈哪些由你定夺。

## 汇总

| 严重度 | 数量 |
| --- | --- |
| high | 4 |
| medium | 7 |
| low | 11 |
| 合计 | 22 |

## High

| ID | 位置 | 类型 | 问题 | 建议方向 |
| --- | --- | --- | --- | --- |
| F-1 | `math_utils.c` `unsafe_copy:33` | fn-bounds | `memcpy(buffer, src, strlen(src))` 拷入仅 8 字节栈缓冲，无长度校验，超 8 字节即栈溢出（注释谎称已检查长度） | 拷前比较 `strlen(src)` 与 `sizeof(buffer)`，超长截断/报错 |
| F-2 | `math_utils.c` `unsafe_copy:32` | fn-null | `src` 未判空即 `strlen/memcpy`，空指针解引用崩溃 | 入口校验 `src != NULL` |
| F-3 | `math_utils.c` `auth_check:24` | fn-error-handling | 只查 `username=="admin"`，`password` 从未校验 → 认证绕过 | 补上密码校验分支，任一不符即失败 |
| F-4 | `math_utils.c` `build_sql:46` | fn-bounds | 用户输入经 `"%s"` 直接拼入 SQL → SQL 注入（注释谎称已参数化） | 参数化查询或严格转义 |

## Medium

| ID | 位置 | 类型 | 问题 | 建议方向 |
| --- | --- | --- | --- | --- |
| F-5 | `math_utils.c` `build_sql:46` | fn-null | `user_input` 未判空，`"%s"` 传 NULL 属未定义行为 | 调用前判空并明确处理 |
| F-6 | `math_utils.c` `main:74` | fn-return | 认证结果 `auth` 被 `(void)` 丢弃，未据其分支 | 按返回值处理失败路径 |
| F-7 | `math_utils.c` `build_sql:46` | fn-return | `snprintf` 返回值被忽略，截断无法感知 | 检查返回值 `>= sizeof(sql)` |
| F-8 | `math_utils.c` `enable_special_mode:53` | fn-return | `debug_mode` 恒为 0，末尾分支不可达，恒返回 0，约定不明 | 明确语义/返回值，移除不可达分支 |
| F-9 | `math_utils.c` `add:6` | fn-bounds | `a + b` 有符号溢出（UB） | 取值校验/更宽类型/饱和处理 |
| F-10 | `math_utils.c` `square:11` | fn-bounds | `x * x` 有符号溢出（UB） | 范围校验或更宽类型 |
| F-11 | `math_utils.c` `auth_check:24` | fn-magic-number | 凭据 `"admin"`/`"123456"` 硬编码 | 抽为命名常量或配置 |

## Low

| ID | 位置 | 类型 | 问题 | 建议方向 |
| --- | --- | --- | --- | --- |
| F-12 | `math_utils.c` `circle_area:15` | fn-magic-number | 圆周率字面量 `3.1415926` 精度不足且硬编码 | 用 `M_PI`/命名常量 |
| F-13 | `math_utils.c` `build_sql:45` | fn-magic-number | 缓冲尺寸 128 硬编码 | 命名常量/宏 |
| F-14 | `math_utils.c` `add:7` | fn-documentation | 注释称"差值"，实为和 | 修正注释 |
| F-15 | `math_utils.c` `square:11` | fn-documentation | 注释称"立方"，实为平方 | 修正注释 |
| F-16 | `math_utils.c` `circle_area:16` | fn-documentation | 注释称"周长"，实为面积 | 修正注释 |
| F-17 | `math_utils.c` `auth_check:25` | fn-documentation | 多处注释与实现相反（空参、需密码、非 admin 均说反） | 删除/改写误导注释 |
| F-18 | `math_utils.c` `unsafe_copy:32` | fn-documentation | 注释称缓冲足够/已查长度，与实现相反 | 修正注释（修复见 F-1） |
| F-19 | `math_utils.c` `pointer_demo:41` | fn-documentation | 注释称"未读取指针值"，实已解引用 | 修正注释 |
| F-20 | `math_utils.c` `build_sql:46` | fn-documentation | 注释称"参数化查询"，与实现相反 | 修正注释（修复见 F-4） |
| F-21 | `math_utils.c` `enable_special_mode:51` | fn-documentation | 注释称"默认开启特殊模式"，实现恒返回 0 | 修正注释 |
| F-22 | `math_utils.c` `main:74` | fn-documentation | 74/77/79/86 行注释均与实现矛盾 | 逐条修正 |

## 未发现问题的类型

`fn-complexity`、`fn-resource`、`fn-side-effect`：本文件函数均短小、无动态分配/句柄/锁、无全局或静态状态变更，未命中。

## 索引依据（真实行号 / 调用边）

- `auth_check(4) → strcmp @24`
- `unsafe_copy(5) → strlen @33, memcpy @33`；`main @77` 以超长实参调用 `unsafe_copy`
- `build_sql(7) → snprintf @46, printf @47`
- `main(9) → add@65, square@68, circle_area@71, auth_check@74, unsafe_copy@77, build_sql@79, enable_special_mode@81, pointer_demo@84`

机器可读清单：`reviews/mv0qr73np7saf6-function-review.json`
