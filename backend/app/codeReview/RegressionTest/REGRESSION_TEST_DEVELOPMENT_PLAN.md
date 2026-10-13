# 回归测试功能开发计划

## 项目概述

将当前的代码审查模块改造为真正的回归测试模块，支持两个版本代码的对比审查。

## 需求分析

### 1. 核心功能需求

#### 1.1 双版本上传
- 上传旧版本代码（ZIP）
- 上传新版本代码（ZIP）
- 一个任务包含两个版本的代码

#### 1.2 变更检测
- 扫描两个版本的所有函数
- 识别变更类型：
  - 新增函数（new）
  - 删除函数（deleted）
  - 修改函数（modified）
  - 未变更函数（unchanged）
- 生成变更函数对列表（旧函数 ↔ 新函数）

#### 1.3 AI审查逻辑
- 只审查**新增函数**和**修改函数**
- 审查时提供：
  - 旧版本函数代码（如果存在）
  - 新版本函数代码
  - 明确标识哪个是旧版、哪个是新版
- 保持智能体功能（工具调用）
- 注释只针对新版本代码
- AI对新版本函数提出问题

#### 1.4 前端视图增强
- **目录树**：左右双栏显示旧版本和新版本
- **代码视图**：对比显示两个版本
- **变更大纲**：列出所有变更函数
- **变更详情**：高亮显示具体变更

### 2. 存储结构设计

```
E:\code\requirement_extractor1\backend\app\uploads\codeReviewRegression\
├── zip\
│   └── task_{task_id}\
│       ├── old_version_{uuid}.zip      # 旧版本ZIP
│       └── new_version_{uuid}.zip      # 新版本ZIP
└── folders\
    └── task_{task_id}\
        ├── old_version\                # 旧版本代码
        │   └── [解压的代码文件]
        └── new_version\                # 新版本代码
            └── [解压的代码文件]
```

### 3. 数据库设计

#### 3.1 需要修改的表

**`regression_test_tasks` 表**：
- 保持现有字段
- 无需修改

**`regression_test_files` 表**：
```sql
-- 添加新字段
ALTER TABLE regression_test_files ADD COLUMN version VARCHAR(20);  -- 'old' 或 'new'
ALTER TABLE regression_test_files ADD COLUMN task_upload_order INT;  -- 上传顺序，1=旧版本，2=新版本
```

**`regression_test_functions` 表**：
```sql
-- 添加新字段
ALTER TABLE regression_test_functions ADD COLUMN version VARCHAR(20);  -- 'old' 或 'new'
ALTER TABLE regression_test_functions ADD COLUMN change_type VARCHAR(20);  -- 'new', 'modified', 'deleted', 'unchanged'
ALTER TABLE regression_test_functions ADD COLUMN paired_function_id INT;  -- 配对的函数ID（旧版本 ↔ 新版本）
ALTER TABLE regression_test_functions ADD COLUMN code_diff TEXT;  -- 代码差异（可选）
```

**新增表：`regression_test_function_pairs`**：
```sql
CREATE TABLE regression_test_function_pairs (
    id SERIAL PRIMARY KEY,
    task_id INT NOT NULL,
    old_function_id INT,  -- 旧版本函数ID（可为NULL，表示新增函数）
    new_function_id INT,  -- 新版本函数ID（可为NULL，表示删除函数）
    change_type VARCHAR(20),  -- 'new', 'modified', 'deleted'
    similarity_score FLOAT,  -- 相似度得分（0-1）
    should_review BOOLEAN DEFAULT TRUE,  -- 是否需要审查
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 开发阶段划分

---

## 📦 阶段1：数据库结构升级（预计2小时）

### 1.1 任务清单
- [ ] 创建数据库迁移脚本
- [ ] 修改 `database.py` 中的表结构
- [ ] 创建新表 `regression_test_function_pairs`
- [ ] 编写数据库升级文档
- [ ] 测试数据库迁移

### 1.2 交付物
- `db/migrations/add_regression_fields.sql`
- `db/database.py`（更新后的表定义）
- `db/init_regression_upgrade.py`（升级脚本）
- `DATABASE_UPGRADE_GUIDE.md`

### 1.3 测试要点
✅ 可以执行升级脚本
✅ 新字段和新表创建成功
✅ 现有数据不受影响
✅ 可以回滚（如果需要）

---

## 📤 阶段2：双版本上传功能（预计4小时）

### 2.1 任务清单
- [ ] 修改上传API支持版本标识
- [ ] 修改存储路径结构（task_id分组）
- [ ] 创建双版本上传逻辑
- [ ] 验证两个版本都上传成功
- [ ] 更新文件仓储层

### 2.2 交付物
- `api/endpoints/upload_file.py`（支持版本参数）
- `service/upload_service.py`（新建）
- `config.py`（更新存储路径逻辑）
- `UPLOAD_API_DOC.md`

### 2.3 API设计
```python
POST /api/codeReview/regressionTest/upload_old_version
POST /api/codeReview/regressionTest/upload_new_version
POST /api/codeReview/regressionTest/upload_both_versions  # 一次上传两个版本
```

### 2.3.1 实际实现（方案1：单接口 + version/task_id）

接口：

```python
POST /upload_file
```

请求类型：`multipart/form-data`

表单字段：
- `file`: ZIP文件
- `version`: `old` 或 `new`（默认 `new`）
- `task_id`: 可选；不传则自动创建任务并返回
- `task_name`: 可选；仅当自动创建任务时生效

存储结构：

```
uploads/codeReviewRegression/
├── zip/
│   └── task_{task_id}/
│       ├── old_version_{uuid}.zip
│       └── new_version_{uuid}.zip
└── folders/
    └── task_{task_id}/
        ├── old_version/
        └── new_version/
```

数据库写入：
- `regression_test_files.task_id = task_id`
- `regression_test_files.version = old/new`
- `regression_test_files.task_upload_order = 1(旧) / 2(新)`

### 2.4 测试要点
✅ 可以上传旧版本代码
✅ 可以上传新版本代码
✅ 两个版本存储在正确的目录结构
✅ 数据库正确记录版本信息
✅ 文件解压正确

#### 2.4.1 最小可测步骤

1. 上传旧版本：
   - 调用 `POST /upload_file`
   - `version=old`
   - 不传 `task_id`
   - 响应中获取 `task_id` 与 `file_id`

2. 上传新版本：
   - 调用 `POST /upload_file`
   - `version=new`
   - 传入上一步返回的 `task_id`
   - 响应中获取新的 `file_id`

3. 检查磁盘目录：
   - `uploads/codeReviewRegression/folders/task_{task_id}/old_version/`
   - `uploads/codeReviewRegression/folders/task_{task_id}/new_version/`

4. 检查数据库（可选）：
   - `regression_test_files` 中应有两条记录
   - `task_id` 相同
   - `version` 分别为 `old` 与 `new`

---

## 🔍 阶段3：函数变更检测引擎（预计6小时）

### 3.1 任务清单
- [ ] 创建函数扫描器（支持版本）
- [ ] 实现函数匹配算法
- [ ] 识别变更类型（new/modified/deleted）
- [ ] 生成函数配对关系
- [ ] 计算相似度得分
- [ ] 保存配对结果到数据库

### 3.2 交付物
- `service/diff/function_matcher.py`（函数匹配器）
- `service/diff/change_detector.py`（变更检测器）
- `service/diff/similarity_calculator.py`（相似度计算）
- `db/repository_function_pairs.py`（配对仓储）

### 3.3 匹配算法
```python
# 1. 精确匹配：函数名 + 文件路径
# 2. 模糊匹配：函数名相同，路径相似
# 3. 相似度计算：基于代码内容（使用difflib）
# 4. 智能推断：基于函数签名和注释
```

### 3.4 测试要点
✅ 能识别新增函数
✅ 能识别删除函数
✅ 能识别修改函数
✅ 匹配准确率高（>90%）
✅ 相似度计算合理
✅ 配对关系正确保存

---

## 🤖 阶段4：AI审查逻辑改造（预计8小时）

### 4.1 任务清单
- [ ] 修改分析启动逻辑（支持双版本）
- [ ] 创建回归测试专用提示词
- [ ] 修改函数审查Agent（传入旧版本+新版本）
- [ ] 更新工具调用逻辑（只查询新版本）
- [ ] 只对新版本函数进行注释
- [ ] 问题记录关联到新版本函数

### 4.2 交付物
- `service/ai/regression_analysis_runner.py`（回归测试启动器）
- `service/ai/regression_review_agent.py`（回归测试Agent）
- `service/ai/prompt/regression_prompt.py`（回归测试提示词）
- `api/endpoints/start_regression_analysis.py`

### 4.3 提示词设计
```
系统角色：你是一个专业的代码回归测试审查专家。

当前任务：审查函数从旧版本到新版本的变更。

提供信息：
1. 旧版本函数代码（如果存在）
2. 新版本函数代码
3. 代码变更摘要

审查重点：
1. 变更是否引入新问题
2. 变更是否影响原有功能
3. 是否有潜在的回归风险
4. 新版本代码的质量问题

注意：
- 只对新版本函数提出问题
- 注释只针对新版本代码
- 可以调用工具查询新版本的上下文
```

### 4.4 测试要点
✅ AI能理解变更上下文
✅ AI只对新版本提问题
✅ 注释正确添加到新版本
✅ 工具调用正确（查询新版本）
✅ 问题记录正确
✅ 智能体功能正常

---

## 🖥️ 阶段5：前端视图改造（预计10小时）

### 5.1 任务清单
- [ ] 双版本目录树组件
- [ ] 代码对比视图组件
- [ ] 变更大纲组件
- [ ] 变更详情高亮显示
- [ ] 函数导航（变更函数列表）
- [ ] API接口调整
- [ ] 状态管理更新

### 5.2 交付物
- `frontend_vue/src/views/codeReview/regression/`（所有组件）
- `frontend_vue/src/components/CodeDiff.vue`（代码对比组件）
- `frontend_vue/src/components/ChangeOutline.vue`（变更大纲）

### 5.3 页面布局
```
┌─────────────────────────────────────────────────────────────┐
│  任务信息 | 上传旧版本 | 上传新版本 | 开始分析              │
├──────────┬──────────┬──────────┬──────────────────────────┤
│          │          │          │  变更大纲                │
│  旧版本  │  新版本  │  变更    │  ├─ 新增函数 (10)       │
│  目录树  │  目录树  │  详情    │  ├─ 修改函数 (25)       │
│          │          │          │  └─ 删除函数 (5)        │
│  (左栏)  │  (左中)  │  (右中)  │                          │
│          │          │          │  问题列表                │
│          │          │          │  (审查结果)              │
│          │          │          │  (右栏)                  │
└──────────┴──────────┴──────────┴──────────────────────────┘
```

### 5.4 测试要点
✅ 双版本目录树正确显示
✅ 代码对比高亮正确
✅ 变更大纲准确
✅ 可以快速导航到变更函数
✅ 问题列表正确显示
✅ 交互流畅

---

## 🔧 阶段6：API接口完善（预计4小时）

### 6.1 任务清单
- [ ] 创建变更列表API
- [ ] 创建函数对比API
- [ ] 创建代码diff API
- [ ] 创建变更统计API
- [ ] 更新现有API支持双版本

### 6.2 交付物
- `api/endpoints/regression_diff.py`
- `api/endpoints/regression_stats.py`
- API文档更新

### 6.3 新增API列表
```python
GET /api/codeReview/regressionTest/changes/{task_id}  # 获取变更列表
GET /api/codeReview/regressionTest/function_pair/{pair_id}  # 获取函数对比
GET /api/codeReview/regressionTest/code_diff/{pair_id}  # 获取代码diff
GET /api/codeReview/regressionTest/stats/{task_id}  # 获取变更统计
```

### 6.4 测试要点
✅ API返回正确的变更数据
✅ 函数对比数据完整
✅ 代码diff格式正确
✅ 统计数据准确

---

## 🧪 阶段7：集成测试与优化（预计6小时）

### 7.1 任务清单
- [ ] 端到端测试（上传→分析→查看）
- [ ] 性能优化（大项目支持）
- [ ] 错误处理完善
- [ ] 日志系统调整
- [ ] 用户文档编写

### 7.2 交付物
- `tests/test_regression_workflow.py`
- `REGRESSION_TEST_USER_GUIDE.md`
- `PERFORMANCE_OPTIMIZATION.md`

### 7.3 测试场景
✅ 小项目（<100个函数）
✅ 中等项目（100-500个函数）
✅ 大项目（>500个函数）
✅ 边界情况（全新增/全删除/无变更）
✅ 错误处理（文件损坏、网络中断）

---

## 📊 总体时间估算

| 阶段 | 工作量 | 依赖关系 |
|------|--------|---------|
| 阶段1：数据库升级 | 2小时 | 无 |
| 阶段2：双版本上传 | 4小时 | 阶段1 |
| 阶段3：变更检测 | 6小时 | 阶段2 |
| 阶段4：AI审查改造 | 8小时 | 阶段3 |
| 阶段5：前端视图 | 10小时 | 阶段4 |
| 阶段6：API完善 | 4小时 | 阶段4 |
| 阶段7：集成测试 | 6小时 | 阶段5,6 |
| **总计** | **40小时** | - |

## 🎯 里程碑

### 里程碑1：后端基础完成（阶段1-3）
- 数据库结构就绪
- 双版本上传可用
- 变更检测正常工作
- **可测试点**：上传两个版本，查看变更列表

### 里程碑2：AI审查可用（阶段4）
- AI能审查变更函数
- 问题记录正确
- **可测试点**：完整的审查流程

### 里程碑3：前端完整（阶段5-6）
- 用户界面完整
- 所有功能可用
- **可测试点**：端到端用户体验

### 里程碑4：生产就绪（阶段7）
- 性能优化
- 文档完整
- **可测试点**：真实项目测试

## 📝 开发原则

1. **向后兼容**：尽量不影响现有配置项测试功能
2. **增量开发**：每个阶段都可独立测试
3. **数据安全**：提供数据库备份和回滚方案
4. **性能优先**：考虑大型项目的处理能力
5. **用户体验**：界面清晰，操作流畅

## 🚀 开始开发

确认开发计划后，我们将按照以下顺序执行：

1. **准备工作**：备份数据库，创建开发分支
2. **阶段1**：数据库升级（提供测试指南）
3. **阶段2**：双版本上传（提供测试API）
4. **阶段3-7**：逐步开发，每阶段提供测试点

## 📞 反馈与调整

每完成一个阶段后：
- 提供测试指南
- 收集反馈
- 调整后续计划（如需要）

---

**准备好开始了吗？请确认计划，然后我们从阶段1开始！** 🎉
