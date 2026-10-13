# 链路审查当前功能显示修复

## 问题描述

用户报告在链路审查进度页面，"功能审查"阶段一直显示"等待开始..."，而不是显示当前正在审查的功能名称。

### 前端表现
```
功能审查
  🔄 等待开始...          ❌ 错误
  3 / 4 已完成
```

### 预期表现
```
功能审查
  🔄 加法操作             ✓ 正确
  3 / 4 已完成
```

## 根本原因

### 数据结构不匹配

**审查时的功能列表**（`run_smart_chain_review` 函数）：
```python
# 扁平化功能列表（包括所有子功能）
all_features = flatten_features(features)
# 示例：[
#   {name: "数学工具模块"},
#   {name: "加法操作"},        ← 子功能
#   {name: "平方操作"},        ← 子功能
#   {name: "条件判断操作"}    ← 子功能
# ]
# 总共 4 个功能
```

**获取进度时的功能列表**（`get_chain_review_progress` 函数 - 修复前）：
```python
features = memory.get("features", [])
# 示例：[
#   {
#     name: "数学工具模块",
#     sub_features: [
#       {name: "加法操作"},
#       {name: "平方操作"},
#       {name: "条件判断操作"}
#     ]
#   }
# ]
# 顶层只有 1 个功能（嵌套结构）
```

### 索引越界导致返回None

当审查进度更新时：
```python
# 审查第2个功能（扁平化列表的索引1）
reviewed_features = 1

# 尝试获取当前功能名称（修复前的代码）
features = memory.get("features", [])  # 顶层列表，长度 = 1
if reviewed_features < len(features):  # 1 < 1 = False ❌
    current_reviewing_feature = features[1].get('name')  # 不执行！

# 结果
current_reviewing_feature = None
# 前端显示："等待开始..."
```

### 代码流程对比

| 步骤 | 审查时 (`run_smart_chain_review`) | 获取进度时（修复前） | 获取进度时（修复后） |
|------|-----------------------------------|---------------------|---------------------|
| 1. 获取features | `features = memory.get("features")` | 同左 | 同左 |
| 2. 扁平化 | `all_features = flatten_features(features)` | ❌ **未扁平化** | ✓ **已扁平化** |
| 3. 更新进度 | `update_review_progress(i)` 使用扁平化索引 | - | - |
| 4. 获取当前功能 | - | `features[reviewed_features]` ❌ 索引越界 | `all_features[reviewed_features]` ✓ 正确 |

## 修复方案

### 修改文件
`backend/app/codeReview/ConfigurationItem/service/business_review/chain_review_smart.py`

### 修复前（第351-356行）
```python
# 获取当前正在审查的功能点名称（用于审查阶段显示）
current_reviewing_feature = None
if overall_status == "reviewing" and reviewed_features < total_features:
    features = memory.get("features", [])
    if reviewed_features < len(features):  # ❌ 使用顶层列表长度判断
        current_reviewing_feature = features[reviewed_features].get('name', f'功能{reviewed_features + 1}')
```

### 修复后（第351-372行）
```python
# 获取当前正在审查的功能点名称（用于审查阶段显示）
# 注意：需要使用扁平化后的功能列表，因为审查时是对扁平化列表进行的
current_reviewing_feature = None
if overall_status == "reviewing" and reviewed_features < total_features:
    features = memory.get("features", [])
    
    # 扁平化功能列表（与审查时保持一致）
    def flatten_features(features_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """递归扁平化功能列表，包括所有子功能"""
        flattened = []
        for feature in features_list:
            flattened.append(feature)
            sub_features = feature.get('sub_features', []) or []
            if sub_features:
                flattened.extend(flatten_features(sub_features))
        return flattened
    
    all_features = flatten_features(features)
    
    # 从扁平化列表中获取当前正在审查的功能
    if reviewed_features < len(all_features):  # ✓ 使用扁平化列表长度判断
        current_reviewing_feature = all_features[reviewed_features].get('name', f'功能{reviewed_features + 1}')
```

## 修复效果

### 场景示例

**功能结构**：
```
数学工具模块 (顶层)
├── 加法操作 (子功能)
├── 平方操作 (子功能)
└── 条件判断操作 (子功能)
```

**审查进度显示**（修复后）：

| reviewed_features | 当前显示 | 说明 |
|------------------|---------|------|
| 0 | 🔄 数学工具模块 | 正在审查顶层功能 |
| 1 | 🔄 加法操作 | 正在审查第1个子功能 |
| 2 | 🔄 平方操作 | 正在审查第2个子功能 |
| 3 | 🔄 条件判断操作 | 正在审查第3个子功能 |
| 4 | ✓ 审查完成 | 所有功能已审查 |

### API返回示例

**修复后的 `/api/codeReview/progressive/progress/{task_id}` 响应**：
```json
{
  "status": "reviewing",
  "discovery_status": "completed",
  "review_progress": 87.5,
  "overall_progress": 87.5,
  "features_count": 4,
  "reviewed_features": 3,
  "current_feature": "条件判断操作",           ← ✓ 正确显示
  "current_reviewing_feature": "条件判断操作", ← ✓ 正确显示
  "current_activity": "🔍 正在审查功能模块 (3/4)"
}
```

## 技术细节

### 扁平化算法

```python
def flatten_features(features_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    递归扁平化功能列表
    
    输入（嵌套结构）:
    [
      {
        "name": "A",
        "sub_features": [
          {"name": "A1", "sub_features": []},
          {"name": "A2", "sub_features": []}
        ]
      }
    ]
    
    输出（扁平结构）:
    [
      {"name": "A", ...},
      {"name": "A1", ...},
      {"name": "A2", ...}
    ]
    
    顺序：深度优先遍历（DFS）
    """
    flattened = []
    for feature in features_list:
        flattened.append(feature)  # 先添加父功能
        sub_features = feature.get('sub_features', []) or []
        if sub_features:
            flattened.extend(flatten_features(sub_features))  # 递归添加子功能
    return flattened
```

### 为什么需要扁平化？

**审查逻辑**：
- AI审查时，会逐个审查每个功能，**不区分**顶层功能和子功能
- 因此审查进度（`reviewed_features`）是基于扁平化列表计数的

**进度显示**：
- 前端需要知道"当前正在审查哪个功能"
- 必须使用与审查时**相同的扁平化列表**来索引当前功能
- 否则会出现索引不匹配的问题

## 数据一致性保证

| 操作 | 位置 | 使用的列表 | 说明 |
|------|------|-----------|------|
| 审查功能 | `run_smart_chain_review` | `all_features = flatten_features(features)` | 扁平化后审查 |
| 更新进度 | `update_review_progress(i)` | `i` 是扁平化列表的索引 | 保存扁平化索引 |
| 获取当前功能 | `get_chain_review_progress` | `all_features = flatten_features(features)` | ✓ 使用相同扁平化逻辑 |

## 测试验证

### 测试步骤
1. 启动一个新的链路审查任务
2. 等待功能划分阶段完成
3. 观察"功能审查"阶段的显示

### 预期结果
- ✓ 显示当前正在审查的具体功能名称（如"加法操作"）
- ✓ 功能名称随着审查进度动态更新
- ✓ 不再显示"等待开始..."（除非审查尚未开始）

### 测试场景

**场景1：单层功能**
```json
{
  "features": [
    {"name": "功能A"},
    {"name": "功能B"},
    {"name": "功能C"}
  ]
}
```
- 扁平化后：3个功能
- 显示：功能A → 功能B → 功能C

**场景2：嵌套功能（本次修复的场景）**
```json
{
  "features": [
    {
      "name": "功能A",
      "sub_features": [
        {"name": "功能A1"},
        {"name": "功能A2"}
      ]
    }
  ]
}
```
- 扁平化后：3个功能
- 显示：功能A → 功能A1 → 功能A2

## 部署说明

修改了后端代码，需要重启服务：

```powershell
# 停止当前服务（Ctrl+C）

# 重新启动
cd E:\code\requirement_extractor\backend
python run_fastapi.py

# 或使用批处理脚本
start_unified.bat
```

## 相关文档

- [链路审查进度追踪系统](./CHAIN_REVIEW_PROGRESS_UI_GUIDE.md)
- [渐进式功能发现](./planner/PROGRESSIVE_DISCOVERY.md)
- [智能链路审查执行器](./executor/SMART_CHAIN_EXECUTOR.md)

---

**修复时间**: 2025-11-02 21:00  
**问题ID**: CHAIN_REVIEW_CURRENT_FEATURE_DISPLAY  
**状态**: ✅ 已修复  
**需要重启**: ✅ 是

