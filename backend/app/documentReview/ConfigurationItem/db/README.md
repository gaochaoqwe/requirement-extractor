# 文档审查配置项数据库模块

此模块为文档审查配置项测试提供数据库管理功能，支持问题等级分类。

## 功能特性

- **问题等级分类**：支持三种问题等级
  - 建议改进：优化、改进相关问题
  - 一般问题：常规问题（默认）
  - 重要问题：安全、性能、关键错误等

- **数据迁移**：从原有 `test_management.db` 迁移数据并添加问题等级字段

- **Excel导出**：支持按问题等级导出审查结果

## 数据库结构

### review_sessions 表
| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | INTEGER | 主键 |
| project_id | INTEGER | 项目ID |
| created_at | DATETIME | 创建时间 |

### review_results 表
| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | INTEGER | 主键 |
| session_id | INTEGER | 会话ID（外键） |
| doc_type | VARCHAR(32) | 文档类型 |
| doc_name | VARCHAR(128) | 文档名称 |
| requirement_content | TEXT | 原始需求内容 |
| violation_rules | VARCHAR(256) | 违反规则 |
| **issue_level** | **VARCHAR(32)** | **问题等级（新增）** |
| issue_name | VARCHAR(256) | 问题名称 |
| issue_location | VARCHAR(256) | 问题位置 |
| description_requirement | TEXT | 需求描述 |
| description_issue | TEXT | 问题描述 |
| description_location | TEXT | 问题定位 |
| description_impact | TEXT | 影响分析 |

## 使用方法

### 1. 初始化数据库

```python
# 运行初始化脚本
python backend/app/documentReview/ConfigurationItem/db/init_database.py
```

### 2. 在代码中使用

```python
from backend.app.documentReview.ConfigurationItem.db import get_db, ReviewSession, ReviewResult
from sqlalchemy.orm import Session

# 使用依赖注入
@router.get("/api/sessions")
async def get_sessions(db: Session = Depends(get_db)):
    sessions = db.query(ReviewSession).all()
    return [s.to_dict() for s in sessions]

# 查询带问题等级的结果
@router.get("/api/results/{session_id}")
async def get_results(session_id: int, db: Session = Depends(get_db)):
    results = db.query(ReviewResult).filter(
        ReviewResult.session_id == session_id
    ).all()
    return [r.to_dict() for r in results]
```

### 3. 下载功能

下载功能已更新为包含问题等级列：
- Excel表头增加"问题等级"列
- 支持按文档类型分sheet导出
- 自动设置列宽和文本换行

## 文件结构

```
db/
├── __init__.py          # 模块导出
├── database.py          # 数据库连接配置
├── deps.py             # 依赖注入
├── init_database.py    # 数据库初始化脚本
├── migrate_data.py     # 数据迁移脚本
├── documentReview.db   # SQLite数据库文件
└── models/
    ├── __init__.py
    ├── review_session.py
    └── review_result.py
```

## 问题等级分配规则

系统自动根据问题名称和违反规则中的关键词分配问题等级：

- **重要问题**：包含"安全"、"性能"、"关键"、"严重"、"错误"、"失败"等关键词
- **建议改进**：包含"建议"、"优化"、"改进"、"完善"、"增强"等关键词  
- **一般问题**：其他情况（默认等级）

## 注意事项

1. 数据库文件位置：`backend/app/documentReview/ConfigurationItem/db/documentReview.db`
2. 原数据库备份：建议在迁移前备份原有的 `test_management.db`
3. 问题等级可通过SQL直接修改：
   ```sql
   UPDATE review_results SET issue_level = '重要问题' WHERE id = 1;
   ``` 