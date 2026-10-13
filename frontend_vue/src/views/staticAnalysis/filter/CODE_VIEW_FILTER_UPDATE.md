# 代码视图过滤器优化说明

## 修改目的

优化AI分析结果代码视图的过滤器，使其更符合实际使用场景：
1. 删除GJB8114和CWE的开关（因为从哪个按钮进入已经确定了规则类型）
2. 新增四个按钮对应Excel输出的四个sheet，精确控制显示哪些问题

## 修改内容

### 1. 前端过滤器UI调整

**文件**: `frontend_vue/src/views/staticAnalysis/filter/StaticAnalysisCodeView.vue`

#### 删除的开关：
- ❌ **标准**: GJB8114 / CWE
- ❌ **规则类型**: 确定规则 / 不确定规则

#### 新增的四个按钮：
- ✅ **确定勾选**（accurate + selected）
- ✅ **确定非勾选**（accurate + not selected）
- ✅ **不确定勾选**（uncertain + selected）
- ✅ **不确定非勾选**（uncertain + not selected）

### 2. 过滤逻辑优化

#### 原来的逻辑：
```javascript
// 四个开关控制
const showGJB = ref(true)
const showCWE = ref(true)
const showAccurate = ref(true)
const showUncertain = ref(true)

// 过滤逻辑
if (p.rule_type === 'gjb' && showGJB.value) || (p.rule_type === 'cwe' && showCWE.value) {
  if (p.rule_accuracy_type === 'accurate') return showAccurate.value
  if (p.rule_accuracy_type === 'uncertain') return showUncertain.value
}
```

#### 新的逻辑：
```javascript
// 四个开关对应四个sheet
const showAccurateSelected = ref(true)      // 确定规则（勾选）
const showAccurateUnselected = ref(true)    // 确定规则（未勾选）
const showUncertainSelected = ref(true)     // 不确定规则（勾选）
const showUncertainUnselected = ref(true)   // 不确定规则（未勾选）

// 用户选中的规则列表（从后端获取）
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

**文件**: `backend/app/staticAnalysis/filter/api/api.py`

在 `code-view/{task_id}` API中新增返回字段：

```python
# 获取用户选中的规则列表（通过查询is_filtered=False的问题来推断）
selected_rules = set()
all_issues = db.query(StaticAnalysisIssue).filter(
    StaticAnalysisIssue.task_id == db_task_id,
    StaticAnalysisIssue.rule_type == rule_type
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

### 4. 规则类型判断逻辑

#### 原来的逻辑：
- 从开关状态推断规则类型
- 如果GJB=true, CWE=false → 'gjb'
- 如果GJB=false, CWE=true → 'cwe'
- 如果两者都true → 'mixed'

#### 新的逻辑：
- 从路由参数直接获取规则类型
- `route.query.type === 'gjb'` → 'gjb'
- `route.query.type === 'cwe'` → 'cwe'
- 其他情况 → 'mixed'

## 使用场景

### 场景1：查看GJB规则的确定勾选问题

1. 从主界面点击"GJB8114问题"按钮进入代码视图
2. 路由参数：`?type=gjb`
3. 默认显示所有四种分类的问题
4. 关闭"确定非勾选"、"不确定勾选"、"不确定非勾选"三个开关
5. 只显示"确定规则（勾选）"的问题

### 场景2：查看CWE规则的AI审查后保留问题

1. 从主界面点击"CWE问题"按钮进入代码视图
2. 路由参数：`?type=cwe`
3. 关闭"确定非勾选"、"不确定非勾选"两个开关
4. 只显示被勾选的问题（包括确定和不确定）

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

**后端判断**（在`enhanced_service.py`生成Excel时）：
```python
selected = set(self.selected_rules or [])

def issue_selected(issue):
    return (issue.rule_code or '') in selected if selected else False

accurate_selected = [i for i in selected_issues 
                    if (i.rule_accuracy_type == 'accurate' and issue_selected(i))]
```

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

## 优势

1. **更直观**：四个按钮直接对应Excel的四个sheet，用户容易理解
2. **更精确**：可以精确控制显示哪一类问题，方便对比分析
3. **更简洁**：删除了冗余的GJB/CWE开关，因为规则类型已经由路由确定
4. **更一致**：前端显示逻辑与Excel生成逻辑完全一致

## 兼容性

- ✅ **完全向后兼容**：不影响现有的数据和流程
- ✅ **不需要数据迁移**：使用现有的数据库字段（rule_accuracy_type, rule_code, is_filtered）
- ✅ **不影响其他功能**：只修改了代码视图的过滤器，不影响上传、分析、下载等其他功能

## 测试建议

### 1. 基本功能测试

1. 上传Excel和代码库，完成AI分析
2. 点击"GJB8114问题"进入代码视图
3. 验证四个开关都能正常工作
4. 切换开关，验证问题列表和代码树正确更新

### 2. 对比测试

1. 下载四分类Excel文件
2. 查看每个sheet的问题数量
3. 在代码视图中，只打开对应的一个开关
4. 验证显示的问题数量与Excel sheet一致

### 3. 边界测试

1. 测试没有勾选任何规则的情况
2. 测试只有确定规则没有不确定规则的情况
3. 测试全部问题都被过滤的情况

## 修改文件清单

### 前端
- `frontend_vue/src/views/staticAnalysis/filter/StaticAnalysisCodeView.vue`

### 后端
- `backend/app/staticAnalysis/filter/api/api.py`

### 文档
- `frontend_vue/src/views/staticAnalysis/filter/CODE_VIEW_FILTER_UPDATE.md`（本文档）

## 修改日期

2025年12月3日
