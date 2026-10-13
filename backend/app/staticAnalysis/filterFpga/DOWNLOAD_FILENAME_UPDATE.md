# FPGA下载文件名优化说明

## 问题描述

FPGA工具的两个下载按钮生成的Excel文件名不够明确，无法清晰区分是否经过AI过滤：
- **原文件名1**：`FPGA_确定规则.xlsx`（AI过滤后）
- **原文件名2**：`FPGA_完整问题单.xlsx`（未经AI过滤）

**问题**：用户无法从文件名直观判断文件内容的区别。

## 解决方案

### 修改后的文件名

在文件名中添加括号说明，明确标识是否经过AI过滤：

| 按钮 | 原文件名 | 新文件名 | 说明 |
|------|---------|---------|------|
| 下载FPGA准确问题单 | `FPGA_确定规则.xlsx` | `FPGA_准确问题单（AI过滤后）.xlsx` | 只包含确定规则的问题，经过AI审查 |
| 下载FPGA全部问题单 | `FPGA_完整问题单.xlsx` | `FPGA_全部问题单（未经AI过滤）.xlsx` | 包含所有问题，未经AI审查 |

### 优势

1. ✅ **清晰明确**：从文件名就能看出是否经过AI过滤
2. ✅ **命名统一**：与GJB/CWE工具的文件命名保持一致
3. ✅ **易于管理**：用户下载多个文件时，能快速识别每个文件的用途

## 修改内容

### 文件：`fpga_processing_api.py`

**修改位置1**：`download_fpga_accurate_issues` 函数

**修改前**：
```python
output_filename = "FPGA_确定规则.xlsx"
```

**修改后**：
```python
output_filename = "FPGA_准确问题单（AI过滤后）.xlsx"
```

---

**修改位置2**：`download_fpga_full_issues` 函数

**修改前**：
```python
output_filename = "FPGA_完整问题单.xlsx"
```

**修改后**：
```python
output_filename = "FPGA_全部问题单（未经AI过滤）.xlsx"
```

## 与GJB/CWE工具的命名对照

| 工具类型 | AI过滤后 | 未经AI过滤 |
|---------|---------|-----------|
| **GJB8114** | `8114_全部问题单（AI过滤后）.xlsx` | `8114_全部问题单（未经AI过滤）.xlsx` |
| **CWE** | `CWE_全部问题单（AI过滤后）.xlsx` | `CWE_全部问题单（未经AI过滤）.xlsx` |
| **FPGA** | `FPGA_准确问题单（AI过滤后）.xlsx` | `FPGA_全部问题单（未经AI过滤）.xlsx` |

### 命名模式

所有工具都遵循统一的命名模式：
```
{工具名称}_{问题范围}（{是否AI过滤}）.xlsx
```

## 文件内容说明

### 1. `FPGA_准确问题单（AI过滤后）.xlsx`

**生成参数**：
- `rule_type="fpga"`
- `accuracy="accurate"`

**包含内容**：
- 只包含 **确定规则**（`rule_accuracy_type='accurate'`）的问题
- 这些问题规则明确，不需要AI审查

**用途**：
- 提供给开发人员的高置信度问题清单
- 建议优先修复这些问题

### 2. `FPGA_全部问题单（未经AI过滤）.xlsx`

**生成参数**：
- `rule_type="fpga"`
- `accuracy="all"`

**包含内容**：
- **确定规则**的问题
- **不确定规则**的问题（未经AI审查）

**用途**：
- 完整的问题清单
- 包含所有可能的问题，用于全面审查

## API端点

| 端点 | 方法 | 文件名 |
|------|------|--------|
| `/api/staticAnalysis/fpga/download-accurate/{session_id}` | GET | `FPGA_准确问题单（AI过滤后）.xlsx` |
| `/api/staticAnalysis/fpga/download-full/{session_id}` | GET | `FPGA_全部问题单（未经AI过滤）.xlsx` |
| `/api/staticAnalysis/fpga/download-split/{session_id}` | GET | `FPGA_四分类问题单.xlsx` |

## 用户界面

### 按钮文本

| 按钮文本 | 下载的文件 |
|---------|-----------|
| 下载FPGA准确问题单（AI过滤后） | `FPGA_准确问题单（AI过滤后）.xlsx` |
| 下载FPGA全部问题单（未经AI过滤） | `FPGA_全部问题单（未经AI过滤）.xlsx` |
| 下载FPGA四分类问题单 | `FPGA_四分类问题单.xlsx` |

### 按钮说明

1. **准确问题单（AI过滤后）**
   - 只包含确定规则的问题
   - 推荐优先下载和修复

2. **全部问题单（未经AI过滤）**
   - 包含所有检测到的问题
   - 用于全面审查

3. **四分类问题单**
   - 包含4个sheet：确定勾选、确定未勾选、不确定勾选、不确定未勾选
   - 用于详细分析和筛选

## 兼容性

- ✅ **向后兼容**：只修改文件名，不影响文件内容
- ✅ **不需要前端修改**：前端使用后端返回的文件名，自动生效
- ✅ **不影响其他功能**：只修改下载文件名，不影响分析流程

## 测试建议

1. **测试下载准确问题单**
   - 点击"下载FPGA准确问题单（AI过滤后）"按钮
   - 验证下载的文件名为 `FPGA_准确问题单（AI过滤后）.xlsx`
   - 验证文件内容只包含确定规则的问题

2. **测试下载全部问题单**
   - 点击"下载FPGA全部问题单（未经AI过滤）"按钮
   - 验证下载的文件名为 `FPGA_全部问题单（未经AI过滤）.xlsx`
   - 验证文件内容包含所有问题

3. **对比文件内容**
   - 下载两个文件
   - 对比确认"准确问题单"是"全部问题单"的子集
   - 验证"全部问题单"包含更多不确定规则的问题

## 修改文件清单

### 后端
- `backend/app/staticAnalysis/filterFpga/api/fpga_processing_api.py`

### 文档
- `backend/app/staticAnalysis/filterFpga/DOWNLOAD_FILENAME_UPDATE.md` - 本文档

## 修改日期

2025年12月3日

## 相关文档

- `backend/app/staticAnalysis/FILENAME_SIMPLIFICATION.md` - GJB/CWE工具的文件名简化说明
- `backend/app/staticAnalysis/filterFpga/FIX_DOWNLOAD_RACE_CONDITION.md` - FPGA下载问题修复说明
