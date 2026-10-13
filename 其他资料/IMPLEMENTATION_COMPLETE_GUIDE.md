# 静态分析过滤工具功能增强 - 完整实施指南

## ✅ 已完成的功能

### 1. 四开关代码视图
- GJB8114 / CWE 标准切换
- 确定规则 / 不确定规则 切换
- 并行加载数据，前端合并
- 实时过滤和更新

### 2. 数据库支持的标记功能
- 标记问题到数据库（替代localStorage）
- 跨会话持久化
- 支持导出已标记问题

### 3. 问题状态管理
- 4种状态：新发现（绿色）、已查看（灰色）、已过滤（灰色）、已标记（蓝色）
- 状态下拉菜单（UI）
- 状态变更API

### 4. 颜色显示系统
- 问题卡片根据状态显示不同颜色
- 状态指示器（圆点）
- 状态标签

## 📋 实施步骤

### 步骤 1：升级数据库 ⚠️ **必须执行**

```bash
# 1. 停止后端服务（如果正在运行）
# Ctrl+C 停止 FastAPI 服务

# 2. 备份数据库（可选，如需保留旧数据）
cd backend/app/staticAnalysis/filter/database
copy static_analysis_filter.db static_analysis_filter.db.backup

# 3. 运行重建脚本
cd ..  # 回到 filter 目录
python utils/rebuild_db.py

# 提示时输入：yes

# 4. 验证数据库
sqlite3 database/static_analysis_filter.db
.tables
# 应该看到：static_analysis_marked_problems 表
.schema static_analysis_issues
# 应该看到：problem_status 字段
.quit
```

### 步骤 2：启动后端服务

```bash
# 在 backend 目录下
python run_fastapi.py
```

检查启动日志，确认没有错误。

### 步骤 3：启动前端服务

```bash
# 在 frontend_vue 目录下
npm run dev
```

### 步骤 4：功能测试

#### 测试 1：四开关功能
1. 上传一个Excel文件（包含GJB和CWE问题）
2. 点击"代码视图"按钮
3. 测试开关：
   - 默认应该全部打开（GJB+CWE+确定+不确定）
   - 关闭GJB，只显示CWE问题
   - 关闭确定规则，只显示不确定规则
   - 各种组合切换，观察问题列表和代码树是否正确更新

#### 测试 2：标记功能（数据库支持）
1. 选择一个文件，查看问题列表
2. 点击"标记"按钮标记几个问题
   - 观察按钮变为"已标记"
   - 问题状态应自动变为"已标记"（蓝色）
3. 刷新浏览器页面
   - 标记应该保持（从数据库加载）
4. 点击"导出已标记"按钮
   - 应该下载Excel文件
   - 打开Excel验证问题是否正确

#### 测试 3：问题状态管理
1. 在问题卡片上找到"状态"下拉菜单
2. 点击下拉菜单，选择不同状态：
   - 新发现（绿色）
   - 已查看（灰色）
   - 已过滤（灰色）
   - 已标记（蓝色）
3. 观察问题卡片颜色是否变化：
   - 新发现：绿色边框，绿色指示器
   - 已查看：灰色边框，灰色指示器
   - 已过滤：浅灰边框，浅灰指示器，半透明
   - 已标记：蓝色边框，蓝色指示器
4. 刷新页面，状态应该保持

#### 测试 4：混合视图导出限制
1. 同时打开GJB和CWE开关
2. 标记一些问题
3. 点击"导出已标记"按钮
   - 应该提示："混合视图下无法导出，请切换到单一标准视图"
4. 关闭CWE或GJB其中一个
5. 再次点击导出
   - 应该成功导出

#### 测试 5：状态与标记联动
1. 标记一个问题
   - 状态应自动变为"已标记"（4）
2. 取消标记
   - 状态应变为"已查看"（2）

## 🔍 验证清单

- [ ] 数据库重建成功，包含新表和字段
- [ ] 后端服务启动无错误
- [ ] 前端服务启动无错误
- [ ] 四开关正常工作，问题列表正确过滤
- [ ] 标记功能使用数据库，刷新后保持
- [ ] 导出已标记问题成功
- [ ] 状态下拉菜单显示并可选择
- [ ] 问题颜色根据状态正确显示
- [ ] 混合视图时导出被正确限制
- [ ] 标记时自动更新状态为"已标记"

## 🐛 常见问题排查

### 问题 1：数据库错误

**症状**：后端启动时报数据库错误

**解决**：
```bash
# 1. 确认数据库文件未被占用
# 2. 删除所有数据库相关文件
cd backend/app/staticAnalysis/filter/database
del static_analysis_filter.db*
# 3. 重启后端（会自动创建）
```

### 问题 2：标记功能不工作

**症状**：点击标记按钮无反应或报错

**解决**：
1. 打开浏览器开发者工具（F12）
2. 查看Console和Network标签
3. 检查API请求是否成功
4. 验证数据库表是否存在：
   ```sql
   sqlite3 backend/app/staticAnalysis/filter/database/static_analysis_filter.db
   SELECT * FROM static_analysis_marked_problems LIMIT 5;
   ```

### 问题 3：状态不保存

**症状**：更改状态后刷新页面，状态丢失

**可能原因**：
1. 问题没有ID（从数据库加载的问题才有ID）
2. API调用失败

**解决**：
1. 确认问题来自数据库（有id字段）
2. 检查浏览器Console是否有错误
3. 检查后端日志

### 问题 4：颜色不显示

**症状**：问题卡片颜色不随状态变化

**解决**：
1. 清除浏览器缓存（Ctrl+Shift+R强制刷新）
2. 检查问题对象是否有`problem_status`字段
3. 打开开发者工具，检查CSS类是否正确应用

### 问题 5：混合视图问题

**症状**：同时开启GJB和CWE时问题显示不正确

**解决**：
1. 检查问题是否有`rule_type`字段
2. 查看浏览器Console，确认两个API都成功返回
3. 检查数据合并逻辑（应该给每个问题添加rule_type）

## 📊 API端点参考

### 标记问题管理

```http
# 保存标记
POST /api/staticAnalysis/filter/{session_id}/marked-problems
Content-Type: application/json
{
  "rule_type": "gjb",
  "problem_key": "...",
  "problem_data": { ... }
}

# 移除标记
DELETE /api/staticAnalysis/filter/{session_id}/marked-problems
Content-Type: application/json
{
  "rule_type": "gjb",
  "problem_key": "..."
}

# 获取标记列表
GET /api/staticAnalysis/filter/{session_id}/marked-problems?rule_type=gjb

# 获取标记数量
GET /api/staticAnalysis/filter/{session_id}/marked-problems/count?rule_type=gjb
```

### 问题状态管理

```http
# 更新单个问题状态
PATCH /api/staticAnalysis/filter/{session_id}/problems/{problem_id}/status?status=2

# 批量更新问题状态
PATCH /api/staticAnalysis/filter/{session_id}/problems/status
Content-Type: application/json
{
  "problem_ids": [1, 2, 3],
  "status": 2
}

# 获取状态统计
GET /api/staticAnalysis/filter/{session_id}/problems/status/statistics
```

## 🎯 性能优化建议

1. **数据库索引**：已在`problem_status`和标记表上添加索引
2. **API缓存**：考虑为标记列表添加前端缓存
3. **批量操作**：标记多个问题时可考虑批量API
4. **懒加载**：代码树大时考虑虚拟滚动

## 📚 相关文档

- [数据库升级指南](backend/app/staticAnalysis/filter/DATABASE_UPGRADE_GUIDE.md)
- [功能增强总结](STATIC_ANALYSIS_FILTER_ENHANCEMENT_SUMMARY.md)
- [API文档](http://localhost:8000/docs) - 启动后端后访问

## 🎉 验收标准

当以下所有条件满足时，功能实施完成：

✅ 数据库成功升级，包含新表和字段
✅ 四个开关正常工作，默认全部开启
✅ 标记功能使用数据库存储，刷新后保持
✅ 状态管理UI正常显示，可以更改状态
✅ 问题颜色根据状态正确显示（绿/灰/浅灰/蓝）
✅ 混合视图时导出功能正确限制
✅ 导出的Excel文件包含正确的已标记问题
✅ 无明显的UI bug或性能问题

## 🚀 下一步优化建议

1. **批量操作**：支持批量标记/取消标记
2. **过滤器增强**：根据状态过滤问题列表
3. **统计面板**：显示各状态的问题数量
4. **代码树颜色**：在代码树上显示文件的问题状态颜色
5. **快捷键**：支持键盘快捷键操作（标记、切换状态等）

---

**最后更新**：2025年11月7日
**版本**：v1.0

