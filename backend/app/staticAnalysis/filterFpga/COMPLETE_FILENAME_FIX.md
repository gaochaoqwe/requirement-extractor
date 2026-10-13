# FPGA所有下载文件名完整修复

## 问题描述

FPGA工具的三个下载按钮，文件名都没有明确标注是否经过AI过滤：
- ❌ 原文件名缺少"（未经AI过滤）"或"（AI过滤后）"标识
- ❌ 用户无法从文件名判断文件内容

## 完整解决方案

### FPGA的三个下载按钮

| 按钮 | 原文件名 | 新文件名 | 修改文件 |
|------|---------|---------|---------|
| 下载FPGA**准确**问题单 | `FPGA_确定规则.xlsx` | `FPGA_准确问题单（**AI过滤后**）.xlsx` | `fpga_processing_api.py` |
| 下载FPGA**全部**问题单 | `FPGA_完整问题单.xlsx` | `FPGA_全部问题单（**未经AI过滤**）.xlsx` | `fpga_processing_api.py` |
| 下载FPGA**四分类**问题单 | `FPGA_全部问题单_四分类.xlsx` | `FPGA_四分类问题单（**未经AI过滤**）.xlsx` | `fpga_enhanced_service.py` |

## 修改详情

### 1. 准确问题单（AI过滤后）

**文件**: `backend/app/staticAnalysis/filterFpga/api/fpga_processing_api.py`

**位置**: `download_fpga_accurate_issues` 函数，第206行

```python
# 修改前
output_filename = "FPGA_确定规则.xlsx"

# 修改后
output_filename = "FPGA_准确问题单（AI过滤后）.xlsx"
```

**说明**：只包含确定规则的问题，不需要AI审查，所以标注为"AI过滤后"

---

### 2. 全部问题单（未经AI过滤）

**文件**: `backend/app/staticAnalysis/filterFpga/api/fpga_processing_api.py`

**位置**: `download_fpga_full_issues` 函数，第303行

```python
# 修改前
output_filename = "FPGA_完整问题单.xlsx"

# 修改后
output_filename = "FPGA_全部问题单（未经AI过滤）.xlsx"
```

**说明**：包含所有问题（确定+不确定），未经AI审查，所以标注为"未经AI过滤"

---

### 3. 四分类问题单（未经AI过滤）

**文件**: `backend/app/staticAnalysis/filterFpga/services/fpga_enhanced_service.py`

**位置**: `generate_split_output_file` 方法，第687-688行

```python
# 修改前
ai_status = "AI过滤后" if highlight_ai else "未经AI过滤"
filename = f"FPGA_全部问题单（{ai_status}）.xlsx"

# 修改后
# 四分类问题单固定为"未经AI过滤"（因为包含所有问题）
filename = f"FPGA_四分类问题单（未经AI过滤）.xlsx"
```

**说明**：
- 四分类包含所有问题，分成4个sheet
- 包含确定和不确定规则的所有问题
- 统一标注为"未经AI过滤"

## 文件内容说明

### 1. FPGA_准确问题单（AI过滤后）.xlsx

**生成参数**：
- `rule_type="fpga"`
- `accuracy="accurate"`

**包含内容**：
- 只包含 **确定规则**（`rule_accuracy_type='accurate'`）
- 这些问题规则明确，不需要AI审查

**Sheet数量**：1个

**用途**：提供高置信度问题清单，建议优先修复

---

### 2. FPGA_全部问题单（未经AI过滤）.xlsx

**生成参数**：
- `rule_type="fpga"`
- `accuracy="all"`

**包含内容**：
- **确定规则** + **不确定规则**
- 包含所有检测到的问题

**Sheet数量**：1个

**用途**：完整的问题清单，用于全面审查

---

### 3. FPGA_四分类问题单（未经AI过滤）.xlsx

**生成参数**：
- 从数据库查询所有问题
- 按准确度和是否勾选分类

**包含内容**：4个Sheet
1. **确定规则（勾选）**
2. **确定规则（未勾选）**
3. **不确定规则（勾选）**
4. **不确定规则（未勾选）**

**用途**：详细分类，便于筛选和分析

## API端点

| 端点 | 文件名 |
|------|--------|
| `GET /api/staticAnalysis/fpga/download-accurate/{session_id}` | `FPGA_准确问题单（AI过滤后）.xlsx` |
| `GET /api/staticAnalysis/fpga/download-full/{session_id}` | `FPGA_全部问题单（未经AI过滤）.xlsx` |
| `GET /api/staticAnalysis/fpga/download-split/{session_id}` | `FPGA_四分类问题单（未经AI过滤）.xlsx` |

## 与GJB/CWE工具的对比

| 工具 | 准确/过滤后问题单 | 全部/未过滤问题单 | 四分类问题单 |
|------|------------------|------------------|-------------|
| **GJB8114** | `8114_全部问题单（AI过滤后）.xlsx` | `8114_全部问题单（未经AI过滤）.xlsx` | `8114_四分类问题单.xlsx` |
| **CWE** | `CWE_全部问题单（AI过滤后）.xlsx` | `CWE_全部问题单（未经AI过滤）.xlsx` | `CWE_四分类问题单.xlsx` |
| **FPGA** | `FPGA_准确问题单（AI过滤后）.xlsx` | `FPGA_全部问题单（未经AI过滤）.xlsx` | `FPGA_四分类问题单（未经AI过滤）.xlsx` |

**统一命名模式**：`{工具名称}_{问题范围}（{是否AI过滤}）.xlsx`

## 为什么四分类标注为"未经AI过滤"？

### 原因分析

1. **包含所有问题**：
   - 确定规则（不需要AI审查）
   - 不确定规则（需要AI审查，但四分类包含AI审查前的所有问题）

2. **与"全部问题单"一致**：
   - "全部问题单"标注为"未经AI过滤"
   - "四分类问题单"也包含所有问题，应保持一致

3. **避免混淆**：
   - 如果标注为"AI过滤后"，用户可能以为只包含AI确认的问题
   - 实际上包含所有问题，只是分类展示

### 对比

| 文件 | 内容 | 标注 |
|------|------|------|
| 准确问题单 | 只有确定规则 | AI过滤后 ✅ |
| 全部问题单 | 所有问题（单sheet） | 未经AI过滤 ✅ |
| 四分类问题单 | 所有问题（四sheet） | 未经AI过滤 ✅ |

## 修改文件清单

### 后端
1. `backend/app/staticAnalysis/filterFpga/api/fpga_processing_api.py`
   - 第206行：`FPGA_准确问题单（AI过滤后）.xlsx`
   - 第303行：`FPGA_全部问题单（未经AI过滤）.xlsx`

2. `backend/app/staticAnalysis/filterFpga/services/fpga_enhanced_service.py`
   - 第688行：`FPGA_四分类问题单（未经AI过滤）.xlsx`

### 文档
- `backend/app/staticAnalysis/filterFpga/COMPLETE_FILENAME_FIX.md` - 本文档

## 测试建议

1. **测试所有三个下载按钮**
2. **验证文件名**：
   - 准确问题单 → `FPGA_准确问题单（AI过滤后）.xlsx` ✅
   - 全部问题单 → `FPGA_全部问题单（未经AI过滤）.xlsx` ✅
   - 四分类问题单 → `FPGA_四分类问题单（未经AI过滤）.xlsx` ✅
3. **验证文件内容**：
   - 准确问题单：只有确定规则
   - 全部问题单：所有问题（单sheet）
   - 四分类问题单：所有问题（四sheet分类）

## 修改日期

2025年12月3日

## 相关文档

- `backend/app/staticAnalysis/filterFpga/DOWNLOAD_FILENAME_UPDATE.md` - 初次修复（不完整）
- `backend/app/staticAnalysis/FILENAME_SIMPLIFICATION.md` - GJB/CWE工具的文件名简化
