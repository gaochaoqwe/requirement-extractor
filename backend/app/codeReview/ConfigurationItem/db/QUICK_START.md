# 数据库快速上手指南

## 📌 新电脑首次部署（3步完成）

### 步骤1：初始化数据库
```bash
cd backend/app/codeReview/ConfigurationItem/db
python init_postgresql.py --yes
```

自动完成：
- ✅ 创建数据库用户 `code_review`
- ✅ 创建数据库 `code_review`
- ✅ 授予所有权限
- ✅ 创建所有9个数据表

### 步骤2：配置环境变量
```bash
python setup_env.py --force
```

自动完成：
- ✅ 创建 `backend/.env` 文件
- ✅ 配置数据库连接信息
- ✅ `run_fastapi.py` 会自动读取

### 步骤3：启动服务
```bash
cd backend
python run_fastapi.py
```

✅ 完成！应用会自动读取 `.env` 文件中的配置

---

## 🔄 完全重置数据库

如果需要清空所有数据并重建：

### 步骤1：删除数据库
```bash
cd backend/app/codeReview/ConfigurationItem/db
python drop_database.py
```
输入 `yes` 确认删除

### 步骤2：重新创建
```bash
python init_postgresql.py
```

---

## 📂 核心脚本说明

### 1. `init_postgresql.py` - 初始化数据库
- **用途：** 创建数据库、用户和所有表
- **场景：** 新电脑部署 / 完全重建数据库

### 2. `drop_database.py` - 删除数据库
- **用途：** 删除整个数据库和用户
- **场景：** 清空数据，准备重新部署
- **警告：** ⚠️ 会删除所有数据！

---

## 📊 已创建的数据表

运行 `init_postgresql.py` 后会创建以下9个表：

**共享表（2个）：**
- `code_review_tasks` - 分析任务
- `code_review_files` - 上传的代码文件

**函数审查表（2个）：**
- `code_review_functions` - 提取的函数
- `code_review_problems` - 函数审查问题

**链路审查表（1个）：**
- `chain_review_problems` - 链路审查问题

**功能审查表（2个）：**
- `features` - 功能点定义
- `feature_review_problems` - 功能审查问题

**问题标记表（1个）：**
- `code_review_marked_problems` - 标记的问题

**文件问题表（1个）：**
- `file_review_problems` - 文件级审查问题

---

## ❓ 常见问题

### 问题1：连接被拒绝
**解决：** 检查PostgreSQL服务是否启动
```bash
net start postgresql-x64-16  # 版本号根据实际安装的版本
```

### 问题2：认证失败
**解决：** 检查 `init_postgresql.py` 中的管理员密码是否正确

### 问题3：数据库已存在
**解决：** 先运行 `drop_database.py` 删除，再运行 `init_postgresql.py`

### 问题4：表不存在
**解决：** 运行 `init_postgresql.py` 重新创建表

---

## 💡 提示

1. **密码安全：** 生产环境请使用强密码
2. **数据备份：** 重要数据请定期备份
3. **环境变量：** 建议创建 `.env` 文件管理配置
4. **权限问题：** 如遇权限错误，参考 `README_POSTGRESQL.md` 手动授权

---

## 📖 更多信息

详细文档请查看：`README_POSTGRESQL.md`

