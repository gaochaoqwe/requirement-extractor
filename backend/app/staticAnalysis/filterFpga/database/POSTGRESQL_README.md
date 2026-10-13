# 静态分析过滤工具 PostgreSQL 数据库说明

## 📋 概述

静态分析过滤工具现在支持PostgreSQL数据库，提供更强大的并发性能和数据管理能力。

### 数据库结构

PostgreSQL数据库 `static_analysis_filter` 包含以下表：

**会话和问题表：**
- `static_analysis_sessions` - 过滤会话
- `static_analysis_issues` - 分析问题
- `static_analysis_marked_problems` - 用户标记的问题

**规则表：**
- `gjb8114_rules` - GJB8114规则（来自 gjb8114_rules.db）
- `gjb8114_rule_keywords` - GJB8114关键字映射
- `cwe_rules` - CWE规则（来自 cwe_rules.db）

## 🚀 快速开始

### 1. 配置环境变量（推荐方式）

在 `backend/.env` 文件中添加以下配置（会在启动时自动加载）：

```env
# 启用PostgreSQL
USE_STATIC_POSTGRESQL=true

# 静态分析过滤工具 PostgreSQL 配置
STATIC_POSTGRES_HOST=localhost
STATIC_POSTGRES_PORT=5432
STATIC_POSTGRES_DB=static_analysis_filter
STATIC_POSTGRES_USER=static_analysis
STATIC_POSTGRES_PASSWORD=123456

# PostgreSQL 管理员配置（用于初始化数据库）
POSTGRES_ADMIN_USER=postgres
POSTGRES_ADMIN_PASSWORD=123456
```

**注意：** 如果 `backend/.env` 文件不存在，请手动创建。参考 `backend/ENV_CONFIG_README.md`。

### 2. 删除旧数据库（可选）

如果需要重新创建数据库：

```cmd
cd backend/app/staticAnalysis/filter/database
python drop_database.py --yes
```

### 3. 初始化PostgreSQL数据库

运行初始化脚本（会自动从 `.env` 读取配置）：

```cmd
cd backend/app/staticAnalysis/filter/database
python init_postgresql.py --yes
```

**该脚本会完成：**
1. 从 `backend/.env` 文件读取配置
2. 创建数据库用户 `static_analysis`
3. 创建数据库 `static_analysis_filter`
4. 授予必要权限
5. 创建所有数据表
6. 从SQLite迁移GJB8114规则数据
7. 从SQLite迁移CWE规则数据

### 4. 启动后端服务

```cmd
cd backend
python run_fastapi.py
```

服务启动时会自动从 `backend/.env` 加载环境变量。

## 📝 管理脚本

### 删除数据库

⚠️ **警告：会删除所有数据！**

```cmd
python drop_database.py --yes
```

### 初始化数据库

```cmd
python init_postgresql.py --yes
```

### 迁移规则数据

如果只需要重新迁移规则数据：

```cmd
python migrate_rules.py
```

## 🔧 配置说明

### 环境变量配置（推荐）

**优先级：** `.env` 文件 > 系统环境变量 > 默认值

#### 方式1：使用 .env 文件（推荐）

在 `backend/.env` 文件中配置（程序启动时自动加载）：

```env
USE_STATIC_POSTGRESQL=true
STATIC_POSTGRES_HOST=localhost
STATIC_POSTGRES_PORT=5432
STATIC_POSTGRES_DB=static_analysis_filter
STATIC_POSTGRES_USER=static_analysis
STATIC_POSTGRES_PASSWORD=123456
POSTGRES_ADMIN_USER=postgres
POSTGRES_ADMIN_PASSWORD=123456
```

#### 方式2：使用系统环境变量

**Windows CMD：**
```cmd
set USE_STATIC_POSTGRESQL=true
set STATIC_POSTGRES_HOST=localhost
...
```

**Windows PowerShell：**
```powershell
$env:USE_STATIC_POSTGRESQL="true"
$env:STATIC_POSTGRES_HOST="localhost"
...
```

### 数据库配置

数据库配置在 `postgresql_config.py` 中定义，通过环境变量读取：

| 环境变量 | 默认值 | 说明 |
|---------|-------|------|
| `USE_STATIC_POSTGRESQL` | false | 是否使用PostgreSQL |
| `STATIC_POSTGRES_HOST` | localhost | PostgreSQL主机 |
| `STATIC_POSTGRES_PORT` | 5432 | PostgreSQL端口 |
| `STATIC_POSTGRES_DB` | static_analysis_filter | 数据库名 |
| `STATIC_POSTGRES_USER` | static_analysis | 数据库用户 |
| `STATIC_POSTGRES_PASSWORD` | 123456 | 数据库密码 |

### 管理员配置

用于创建和删除数据库的管理员配置：

- 用户名: `postgres`
- 密码: `123456`

## 💡 使用说明

### 切换数据库类型

在 `backend/.env` 文件中设置：

**使用PostgreSQL：**
```env
USE_STATIC_POSTGRESQL=true
```

**使用SQLite（默认）：**
```env
USE_STATIC_POSTGRESQL=false
```

或者不设置该环境变量（默认使用SQLite）。

### 数据库连接测试

```python
cd backend/app/staticAnalysis/filter/database
python postgresql_database.py
```

## 📊 数据迁移

### 从SQLite迁移规则数据

初始化脚本会自动迁移以下规则数据：

1. **GJB8114规则** - 从 `gjb8114_rules.db` 迁移
   - `gjb8114_rules` 表
   - `rule_keywords` 表

2. **CWE规则** - 从 `cwe_rules.db` 迁移
   - `cwe_rules` 表

**注意：** 会话数据（`static_analysis_filter.db`）不会被迁移，这是预期行为。

## ⚙️ 技术细节

### 连接池配置

- 连接池大小: 10
- 最大溢出连接数: 20
- 连接回收时间: 3600秒（1小时）
- 连接预测试: 启用

### 索引优化

PostgreSQL版本添加了多个复合索引以优化查询性能：

- `idx_task_rule_type` - (task_id, rule_type)
- `idx_task_accuracy` - (task_id, rule_accuracy_type)
- `idx_task_status` - (task_id, problem_status)
- `idx_session_rule_type` - (session_id, rule_type)
- `idx_session_problem_key` - (session_id, problem_key)

## 🔍 故障排查

### 连接失败

1. 确认PostgreSQL服务已启动
2. 确认防火墙允许5432端口
3. 确认管理员密码正确
4. 检查环境变量是否正确设置

### 初始化失败

1. 检查是否有足够的权限
2. 确认PostgreSQL版本 >= 12
3. 查看详细错误信息

### 规则迁移失败

1. 确认SQLite数据库文件存在：
   - `gjb8114_rules.db`
   - `cwe_rules.db`
2. 检查数据库文件是否完整
3. 查看迁移日志

## 📦 依赖项

确保已安装以下Python包：

```bash
pip install psycopg2-binary
pip install sqlalchemy
```

## 🆘 支持

如遇问题，请检查：

1. PostgreSQL服务状态
2. 环境变量设置
3. 数据库日志
4. Python日志文件

## 📚 相关文件

- `drop_database.py` - 删除数据库脚本
- `init_postgresql.py` - 初始化数据库脚本
- `migrate_rules.py` - 规则数据迁移脚本
- `postgresql_config.py` - PostgreSQL配置
- `postgresql_models.py` - 数据库模型
- `postgresql_database.py` - 数据库连接
- `postgresql_rules_database.py` - 规则数据库访问类
- `rules_database_factory.py` - 规则数据库工厂
- `set_postgresql_env.bat` - CMD环境变量设置
- `set_postgresql_env.ps1` - PowerShell环境变量设置

