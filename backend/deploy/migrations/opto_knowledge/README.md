# opto_knowledge · 迁移说明

本库目前**没有任何手写 SQL 迁移**，不需要迁移文件。

原因：
- 全部表（`opto_knowledge_node`、`opto_knowledge_edge`、`opto_knowledge_asset`）由
  SQLAlchemy ORM 模型定义，见 `app/databaseManage/optoKnowledge/db/models.py`；
- 基础表由 `Base.metadata.create_all()` 建立，默认节点数据由 `seed_database()` 插入；
- `app/databaseManage/optoKnowledge/db/database.py::migrate_database()` 为空实现。

因此 `deploy_db.py` 只需为本库完成「建库 / 建用户 / 授权」，schema 交由后端启动时创建。

> 将来若新增手写补列/补表，在此目录放 `V001__xxx.sql`（幂等）即可自动被纳入统一迁移。
