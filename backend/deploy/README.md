# deploy —— 统一数据库部署与迁移

本目录把原先散落在 **7 套 `init_postgresql.py` + 若干 `数据库迁移.md` + `部署方案.md` 手工 SQL**
里的数据库变更，收敛为**一个入口 + 版本化迁移文件 + 一张版本记录表**。

目标：部署从"换文件夹 → 跑 N 个脚本 → 在 Navicat 里手工粘贴 SQL"变成**一条命令**，且可重复执行、跑不坏。

---

## 一、为什么需要它（现状问题）

| 问题 | 具体表现 |
|---|---|
| 没有迁移机制 | schema 变更靠手工在 Navicat 执行 `ALTER ... ADD COLUMN IF NOT EXISTS`，只把 SQL 记在 md 里 |
| 7 个库 7 套入口 | 每模块一个 `init_postgresql.py`，跑没跑、跑到哪一步无从判断 |
| 同一变更抄三处 | 代码 `migrate_database()`、`数据库迁移.md`、`部署方案.md` 各一份，已出现不一致 |
| 新老环境对不齐 | 新库靠 `create_all` 建"最初的表"，老库靠历史 ALTER，二者结构可能不同 |

已发现的具体不一致（本目录已修正/记录）：
- `code_review_tasks.has_marked_problems / marked_problem_count / marked_problems_exported`
  只在 md 与 ORM 模型里，代码 `migrate_database()` 无对应 ALTER → 老库不补列。**已在 V001 补上。**
- `code_review_regression` 的链路审查补列被误写成 `chain_review_problems`（那是 code_review 库的表）→
  在回归库静默失败。**已在 V001 修正为 `regression_test_chain_problems`。**
- `feature_repo.py` 用 SQLite 语法 `PRAGMA table_info` 做 PG 迁移 → 在 PostgreSQL 上永不生效（**已知问题，未动代码**）。
- `normalModeC/数据库迁移.md` 要求建 `fk_nm_problems_function` 外键，代码却刻意注释掉 → **以代码为准，不建**。
- `filterFpga/数据库迁移.md` 提前包含了 FPGA 代码里尚不存在的 fix 表 → 归入 V002，标注为"结构对齐"。

---

## 二、目录结构

```
backend/deploy/
├── db_config.py          # 7 个库的声明（库名/用户/密码/迁移目录/原有初始化脚本）
├── migration_runner.py   # 迁移引擎：schema_migrations 版本表 + 幂等按序执行
├── deploy_db.py          # ← 统一入口
├── snapshot_schema.py    # pg_dump 导出各库真实结构（用于核对/归档）
├── snapshots/            # 结构快照输出目录
└── migrations/
    ├── auth/                          V001
    ├── code_review/                   V001, V002
    ├── code_review_regression/        V001, V002
    ├── static_analysis_filter/        V001, V002
    ├── fpga_static_analysis_filter/   V001, V002
    ├── opto_knowledge/                （纯 ORM，无迁移）
    └── maintenance/                   V001
```

---

## 三、常用命令

> 用后端运行时的同一个 Python 环境执行（即 `start5002.bat` 里那个 `aiTest_new` 环境）。

```bash
cd backend

# 1) 查看受管数据库与迁移清单
python deploy/deploy_db.py --list

# 2) 只读校验：各库当前处于哪个版本、还差几个迁移
python deploy/deploy_db.py --verify

# 3) 演练：不实际改动，只打印将要做什么
python deploy/deploy_db.py --dry-run

# 4) 一键部署：建库/建用户/授权 + 应用全部迁移（幂等，可反复跑）
python deploy/deploy_db.py --yes

# 5) 只建库与用户
python deploy/deploy_db.py --create-only --yes

# 6) 只跑迁移（库已存在）
python deploy/deploy_db.py --migrate-only --yes

# 7) 全新环境：先复用各模块原有 init_postgresql.py 建基础表，再补迁移
python deploy/deploy_db.py --bootstrap --yes

# 8) 只处理某几个库
python deploy/deploy_db.py --targets code_review,static_analysis_filter --yes

# 9) 导出各库真实结构快照（只读，需本机有 pg_dump）
python deploy/snapshot_schema.py
```

---

## 四、日常工作流（以后改 schema 怎么做）

1. 在 `migrations/<库>/` 下新建 `V003__本次变更描述.sql`，**写成幂等语句**：

   ```sql
   -- 新功能：xxx
   ALTER TABLE code_review_tasks ADD COLUMN IF NOT EXISTS new_field VARCHAR(50);
   CREATE INDEX IF NOT EXISTS idx_xxx ON code_review_tasks(new_field);
   ```

2. 本地跑 `python deploy/deploy_db.py --migrate-only --yes` 生效；
3. 用 `--verify` 确认状态为 `applied`；
4. 迁移文件一并入库（git），下次部署直接 `python deploy/deploy_db.py --yes`。

> 版本号只增不改。**已应用的迁移文件不要再改内容**（改了 `--verify` 会报 `changed`），
> 需要修正就新增一个 `Vxxx`。

---

## 五、设计要点

- **幂等**：所有语句都用 `... IF NOT EXISTS`，重复执行安全，首次纳管已有环境不破坏数据。
- **失败可控**：单条语句失败会记录原因并继续（`--strict` 可改为立即中止），结束时汇总。
- **基础表归属**：ORM 表（`code_review_*` / `static_analysis_*` / `regression_test_*` / `opto_knowledge_*`）
  仍由 SQLAlchemy `create_all` 建立；`create_all` 只建表不补列，**所有"加列"都在本目录迁移文件里**。
  手写 SQL 表（`users`、`maintenance_*`、`nm_*` / `nm_fpga_*`）的基线也写进了对应 V001。
- **只读校验**：`--verify` 不创建任何表；若 `schema_migrations` 不存在，则全部视为 pending。
- **加库即纳入**：新增一个数据库，只要在 `db_config.py` 的 `TARGETS` 加一条，并建同名迁移目录即可。

---

## 六、与旧流程的对应关系

| 旧做法 | 新做法 |
|---|---|
| 编辑 `start5002.bat` 挂的 `init_static_analysis_db.bat` | `python deploy/deploy_db.py --yes` |
| 在 Navicat 里粘贴 `部署方案.md` 的 ALTER | 迁移文件已内置，自动执行并记录版本 |
| 每模块单独跑 `init_postgresql.py` | `--create-only` 统一建库；`--bootstrap` 兜底建基础表 |
| 无法判断某环境跑到哪一版 | `python deploy/deploy_db.py --verify` 一目了然 |
