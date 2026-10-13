# FPGA代码视图过滤器优化说明

## 修改目的

优化FPGA静态分析代码视图的过滤器，与GJB/CWE工具保持一致：
1. 删除"确定规则"和"不确定规则"的开关
2. 新增四个按钮对应Excel输出的四个sheet，精确控制显示哪些问题

## 修改内容

### 1. 前端过滤器UI调整

**文件**: `frontend_vue/src/views/staticAnalysis/filterFpga/StaticAnalysisCodeView.vue`

#### 删除的开关：
- ❌ **标准**: FPGA标签（改为隐藏，因为已经明确是FPGA）
- ❌ **规则类型**: 确定规则 / 不确定规则

#### 新增的四个按钮：
- ✅ **确定勾选**（accurate + selected）
- ✅ **确定非勾选**（accurate + not selected）
- ✅ **不确定勾选**（uncertain + selected）
- ✅ **不确定非勾选**（uncertain + not selected）

### 2. 过滤逻辑优化

#### 原来的逻辑：
```javascript
// 两个开关控制
const showAccurate = ref(true)
const showUncertain = ref(true)

// 过滤逻辑
if (p.rule_accuracy_type === 'accurate') {
  return showAccurate.value
} else if (p.rule_accuracy_type === 'uncertain') {
  return showUncertain.value && p.ai_analyzed === true && p.ai_is_real_issue === true
}
```

#### 新的逻辑：
```javascript
// 四个开关对应四个sheet
const showAccurateSelected = ref(true)      // 确定规则（勾选）
const showAccurateUnselected = ref(true)    // 确定规则（未勾选）
const showUncertainSelected = ref(true)     // 不确定规则（勾选）
const showUncertainUnselected = ref(true)   // 不确定规则（未勾选）

// 用户选中的规则列表（从FPGA后端获取）
const selectedRulesSet = ref(new Set())

// 过滤逻辑
const isSelected = isProblemSelected(p)  // 判断问题是否被勾选
const accuracyType = p.rule_accuracy_type

if (accuracyType === 'accurate') {
  if (isSelected) return showAccurateSelected.value
  else return showAccurateUnselected.value
}

if (accuracyType === 'uncertain') {
  if (isSelected) return showUncertainSelected.value
  else return showUncertainUnselected.value
}
```

### 3. 后端API增强

**文件**: `backend/app/staticAnalysis/filterFpga/api/api.py`

在 `code-view/{task_id}` API中新增返回字段：

```python
# 获取用户选中的规则列表（通过查询is_filtered=False的问题来推断）
selected_rules = set()
all_issues = db.query(StaticAnalysisIssue).filter(
    StaticAnalysisIssue.task_id == db_task_id
).all()

for issue in all_issues:
    if issue.rule_code and not issue.is_filtered:
        selected_rules.add(issue.rule_code)

return {
    "success": True,
    "data": {
        "files": files_data,
        "problems": problems_data,
        "selected_rules": list(selected_rules)  # 新增：用户勾选的规则列表
    }
}
```

### 4. 数据加载逻辑

```javascript
// 加载FPGA代码视图数据
async function loadCodeViewData() {
  const fpgaRes = await axios.get(`/api/staticAnalysis/fpga/code-view/${taskId.value}`)
  const fpgaData = fpgaRes.data.success ? fpgaRes.data.data : { files: [], problems: [], selected_rules: [] }
  
  // 加载用户勾选的规则列表
  selectedRulesSet.value = new Set(fpgaData.selected_rules || [])
  console.log('[FPGA代码视图] 用户勾选的规则数量:', selectedRulesSet.value.size)
  
  allFiles.value = dedupeFiles([...(fpgaData.files || [])])
  allProblems.value = [...(fpgaData.problems || []).map(p => ({ ...p, rule_type: p.rule_type || 'fpga' }))]
}
```

## 使用场景

### 场景1：查看FPGA确定勾选问题

1. 从主界面点击"FPGA问题"按钮进入代码视图
2. 默认显示所有四种分类的问题
3. 关闭"确定非勾选"、"不确定勾选"、"不确定非勾选"三个开关
4. 只显示"确定规则（勾选）"的问题

### 场景2：查看FPGA AI审查后保留问题

1. 进入FPGA代码视图
2. 关闭"确定非勾选"、"不确定非勾选"两个开关
3. 只显示被勾选的问题（包括确定和不确定）

### 场景3：对比不同分类的问题

1. 打开所有四个开关，查看所有问题
2. 逐个关闭开关，对比不同分类的问题数量和分布
3. 帮助理解AI过滤的效果

## 对应关系

### 与Excel四个sheet的对应：

| 前端开关 | Excel Sheet名称 | 数据特征 |
|---------|----------------|---------|
| 确定勾选 | 确定规则（勾选） | rule_accuracy_type='accurate' + 用户勾选的规则 |
| 确定非勾选 | 确定规则（未勾选） | rule_accuracy_type='accurate' + 用户未勾选的规则 |
| 不确定勾选 | 不确定规则（勾选） | rule_accuracy_type='uncertain' + 用户勾选的规则 |
| 不确定非勾选 | 不确定规则（未勾选） | rule_accuracy_type='uncertain' + 用户未勾选的规则 |

### 勾选判断逻辑：

**前端判断**（在代码视图中）：
```javascript
const isProblemSelected = (problem) => {
  if (!problem.rule_code) return false
  return selectedRulesSet.value.has(problem.rule_code)
}
```

**API推断**（从数据库查询）：
```python
# 用户勾选的规则 = 未被is_filtered标记的规则
selected_rules = set()
for issue in all_issues:
    if issue.rule_code and not issue.is_filtered:
        selected_rules.add(issue.rule_code)
```

## FPGA特殊性

### 代码库格式
- FPGA使用ZIP格式上传代码库
- 支持的文件类型：`.v`, `.sv`, `.vh`, `.svh`, `.vhd`, `.vhdl`
- 代码库扫描从ZIP文件中读取

### 规则体系
- FPGA复用GJB8114规则体系
- 问题的 `rule_type` 可能是 'gjb' 或 'fpga'
- 统一按FPGA处理

## 优势

1. **更直观**：四个按钮直接对应Excel的四个sheet，用户容易理解
2. **更精确**：可以精确控制显示哪一类问题，方便对比分析
3. **更简洁**：删除了冗余开关，界面更清爽
4. **更一致**：与GJB/CWE工具的代码视图保持一致的交互方式

## 兼容性

- ✅ **完全向后兼容**：不影响现有的数据和流程
- ✅ **不需要数据迁移**：使用现有的数据库字段（rule_accuracy_type, rule_code, is_filtered）
- ✅ **不影响其他功能**：只修改了代码视图的过滤器，不影响上传、分析、下载等其他功能

## 测试建议

### 1. 基本功能测试

1. 上传FPGA Excel和代码库，完成AI分析
2. 点击"FPGA问题"进入代码视图
3. 验证四个开关都能正常工作
4. 切换开关，验证问题列表和代码树正确更新

### 2. 对比测试

1. 下载FPGA四分类Excel文件
2. 查看每个sheet的问题数量
3. 在代码视图中，只打开对应的一个开关
4. 验证显示的问题数量与Excel sheet一致

### 3. 边界测试

1. 测试没有勾选任何规则的情况
2. 测试只有确定规则没有不确定规则的情况
3. 测试全部问题都被过滤的情况

## 修改文件清单

### 前端
- `frontend_vue/src/views/staticAnalysis/filterFpga/StaticAnalysisCodeView.vue`

### 后端
- `backend/app/staticAnalysis/filterFpga/api/api.py`

### 文档
- `frontend_vue/src/views/staticAnalysis/filterFpga/CODE_VIEW_FILTER_UPDATE.md`（本文档）

## 与GJB/CWE工具的区别

| 特性 | GJB/CWE工具 | FPGA工具 |
|-----|-----------|---------|
| 规则类型 | GJB8114 和 CWE | FPGA（复用GJB规则） |
| 代码库格式 | 文件夹 | ZIP压缩包 |
| 文件类型 | C/C++（.c, .cpp, .h等） | Verilog/VHDL（.v, .vhd等） |
| 路由参数 | `?type=gjb` 或 `?type=cwe` | 无（固定为FPGA） |
| 过滤逻辑 | 完全相同 | 完全相同 |
| UI布局 | 完全相同 | 完全相同 |

## 修改日期

2025年12月3日
