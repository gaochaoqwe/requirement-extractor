# RegressionTest 数据库升级指南（阶段1）

## 目标

为回归测试支持“旧版/新版双版本上传”和“函数配对（旧↔新）”做数据库结构准备。

## 变更点

- `regression_test_files`
  - 新增字段：`version`（old/new）
  - 新增字段：`task_upload_order`

- `regression_test_functions`
  - 新增字段：`version`（old/new）
  - 新增字段：`change_type`（new/modified/deleted/unchanged）
  - 新增字段：`paired_function_id`
  - 新增字段：`code_diff`

- 新增表：`regression_test_function_pairs`

## 升级方式（推荐）

运行升级脚本：

```powershell
conda activate aiTest_new
python -m backend.app.codeReview.RegressionTest.db.upgrade_regression_schema
```

该脚本会调用 `migrate_database()`，并自动执行：

- `db/migrations/20251212_regression_dual_version_and_pairs.sql`

## 验证方式

1. 运行 `verify_database.py` 或启动后端服务后，确认表存在。
2. 在数据库中执行：

```sql
\d regression_test_files
\d regression_test_functions
\d regression_test_function_pairs
```

确认新增字段存在。

## 回滚说明

本阶段仅新增字段/新增表，不删除任何旧字段，通常不需要回滚。
如需回滚，可手动删除新增表/字段（不建议在已有数据时执行）。
