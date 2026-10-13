# FPGA过滤项目Excel列映射修复

## 修复日期
2024年11月11日

## 问题描述
原代码中的Excel列映射与实际的"结果1" sheet结构不匹配。

## 实际Excel结构（"结果1" sheet）
根据用户提供的真实表单截图：

| 列 | 字段名 | 说明 |
|---|--------|------|
| A | 序号 | 问题序号 |
| B | 规则编号 | 格式如 "5.1.1.5 建议准则A-1-5" |
| C | 规则描述 | 规则的详细描述 |
| D | 文件 | 文件路径，如 "E:/xx/xx/xx/new/top.v" |
| E | 行 | 行号 |
| F | 告警类型 | 告警的类型分类 |
| G | 确认状态 | 问题的确认状态 |
| H | 备注 | 备注信息 |

## 原代码的错误映射
在 `fpga_excel_processor.py` 中：
- F列被错误地认为是"列"（column number）
- G列被错误地认为是"严重程度"（severity）

## 修复内容

### 1. 更新了 `fpga_excel_processor.py`

**文件路径**: `D:\code\requirement_extractor\backend\app\staticAnalysis\filterFpga\services\fpga_excel_processor.py`

**修改位置**: 
- 第97-110行：更新了 `_read_excel_data` 方法的文档字符串
- 第124-132行：更新了列数据提取逻辑
- 第145-158行：更新了问题字典的字段名

**具体变更**:
```python
# 修改前
column = str(row[5]) if row[5] is not None and len(row) > 5 else ""  # F列：列
severity = str(row[6]) if row[6] is not None and len(row) > 6 else ""  # G列：严重程度

# 修改后
alert_type = str(row[5]) if row[5] is not None and len(row) > 5 else ""  # F列：告警类型
confirm_status = str(row[6]) if row[6] is not None and len(row) > 6 else ""  # G列：确认状态
```

**字段名变更**:
- `description` → `rule_description` (C列：规则描述)
- `column` → `alert_type` (F列：告警类型)
- `severity` → `confirm_status` (G列：确认状态)

### 2. 数据库模型验证
检查了以下文件，确认它们使用通用字段，无需修改：
- `models/models.py` - 使用 `issue_name`, `issue_description` 等通用字段
- `database/postgresql_models.py` - 同样使用通用字段

### 3. 前端代码验证
检查了前端组件 `ProblemList.vue`，确认它使用的是通用字段：
- `issue_name` - 问题名称
- `issue_file` - 文件路径
- `issue_line` - 行号
- `issue_description` - 问题描述
- `rule_code` - 规则编号

前端无需修改，因为后端会将提取的数据映射到这些通用字段。

## 影响范围
- ✅ Excel文件解析现在能正确读取F列（告警类型）和G列（确认状态）
- ✅ 数据结构更准确地反映实际Excel内容
- ✅ 前端显示不受影响，因为使用的是通用字段映射

## 测试建议
1. 使用真实的FPGA静态分析Excel文件进行测试
2. 验证"结果1" sheet的所有列都能正确解析
3. 检查告警类型和确认状态字段是否正确提取
4. 确认前端能正常显示所有问题信息

## 注意事项
- 如果后续需要使用 `alert_type` 和 `confirm_status` 字段，需要在数据库模型中添加相应的列
- 当前这些字段存储在问题数据的JSON中，可以通过 `issue_description` 或其他文本字段访问
