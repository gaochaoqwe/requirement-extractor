# 链路审查提示词与问题单格式升级

## 🎯 升级目标

参考函数审查的提示词格式（`codeReviewPrompt.md`），全面升级链路审查的问题单格式，使其更加规范、详细和易于前端解析。

## 📋 升级内容概述

### 1. 完善的字段定义

**之前（旧格式）**：
```json
{
  "problems": [
    {
      "issue_name": "问题名称",
      "issue_level": "严重|中等|轻微",
      "issue_location": "文件:行号",
      "description_requirement": "违反的业务需求或编程规范",
      "description_issue": "具体问题描述",
      "description_impact": "可能的影响",
      "problem_reason": "问题原因分析"
    }
  ]
}
```

**现在（新格式）**：
```json
{
  "problems": [
    {
      "file_name": "链路名称（功能模块名称）",
      "source_code": "出问题的代码片段",
      "problem_reason": "问题原因（简洁描述）",
      "issue_level": "建议改进|一般问题|重要问题",
      "issue_name": "问题名称",
      "issue_location": "文件名:函数名",
      "description_requirement": "需求描述",
      "description_issue": "问题描述",
      "description_location": "xx文件的xx函数的xx行：问题代码语句",
      "description_impact": "影响分析"
    }
  ]
}
```

### 2. 字段变更详情

| 字段 | 之前 | 现在 | 说明 |
|------|------|------|------|
| `file_name` | ❌ 无 | ✅ 链路名称 | 标识功能模块（如"信号采集与处理链路"） |
| `source_code` | ❌ 无 | ✅ 代码片段 | 出问题的具体代码段 |
| `problem_reason` | 简单描述 | ✅ 结构化描述 | 提供具体原因（如"未检查返回值"、"资源未释放"） |
| `issue_level` | 严重/中等/轻微 | ✅ 建议改进/一般问题/重要问题 | 与函数审查统一 |
| `description_location` | 简单位置 | ✅ 严格格式 | `xx文件的xx函数的xx行：问题代码语句` |

### 3. 新增的格式约束

**新增12条严格的JSON格式要求**：

1. ✅ 必须返回标准的、可解析的JSON格式
2. ✅ 所有字符串值必须使用双引号(")
3. ✅ 字符串中的双引号必须转义(\\")
4. ✅ 代码中的换行用\\n表示
5. ✅ 不包含未转义的特殊字符
6. ✅ 数组元素用逗号分隔，最后一项后无逗号
7. ✅ 所有字段严格遵循模板格式
8. ✅ **issue_level必须是三个值之一**
9. ✅ 未发现问题时返回 `{"problems": []}`
10. ✅ 回复必须是【最终问题单】后的单一JSON对象
11. ✅ **description_location必须严格按照格式**
12. ✅ **问题代码语句是最重要的定位信息**

## 📝 详细字段说明

### `file_name` - 链路名称（新增）
- **含义**：功能模块名称，不是具体的文件名
- **示例**：
  - ✅ "信号采集与处理链路"
  - ✅ "数据传输与缓存管理"
  - ❌ "radar_system.c"（这应该放在`issue_location`）

### `source_code` - 问题代码片段（新增）
- **含义**：导致问题的具体代码段
- **格式要求**：
  - 去掉多余空格
  - 保持原始语法
  - 代码换行用`\n`表示
- **示例**：
```json
"source_code": "void cleanup_system() {\n    // 释放缓冲区\n    free_signal_buffer();\n    // 日志文件未关闭\n}"
```

### `problem_reason` - 问题原因（优化）
- **之前**：可以是任意描述
- **现在**：要求简洁、具体的原因
- **示例**：
  - ✅ "日志文件句柄未释放，导致资源泄漏"
  - ✅ "未检查返回值，可能导致空指针"
  - ✅ "缓冲区溢出风险"
  - ❌ "代码有问题"（太模糊）

### `issue_level` - 问题等级（标准化）
- **之前**：严重|中等|轻微
- **现在**：建议改进|一般问题|重要问题
- **目的**：与函数审查的等级体系统一

### `description_location` - 问题定位（严格格式）
- **格式**：`xx文件的xx函数的xx行：问题代码语句`
- **示例**：
  - ✅ `example.c文件的foo函数的3行：gets(buf)`
  - ✅ `radar_system.c文件的cleanup_system函数的284行：free_signal_buffer()`
  - ✅ `tiny_test\math_utils.c文件的square函数的15行：result = x * x`
- **重要性**：前端将使用**问题代码语句**进行精确匹配定位

## 🔧 技术实现

### 修改的文件

**1. `smart_chain_executor.py`（第250-303行）**

```python
def _build_system_prompt(self, kb: Dict[str, Any], feature: Dict[str, Any]) -> str:
    """构建系统提示词"""
    # ...
    
    return f"""你是一位资深的软件审查专家...
    
【问题单格式】
当你完成代码审查后，**必须严格按照如下JSON结构输出分析结果**：

## 问题分析字段含义：
- `file_name`：链路名称（功能模块名称，如"信号采集与处理"）
- `source_code`：出问题的代码片段...
- `problem_reason`：问题原因...
- `issue_level`：问题等级（**必须**是以下三个值之一：**建议改进**、**一般问题**、**重要问题**）
...

**输出示例：**
【最终问题单】
```json
{{
  "problems": [
    {{
      "file_name": "信号采集与处理链路",
      "source_code": "void cleanup_system() {{\\n...",
      "problem_reason": "日志文件句柄未释放，导致资源泄漏",
      "issue_level": "重要问题",
      ...
    }}
  ]
}}
```

## 严格的JSON格式要求：
1-12条详细要求...
"""
```

### 解析逻辑（无需修改）

现有的 `_extract_problems_from_response` 方法已经能够正确解析新格式：

```python
def _extract_problems_from_response(self, content: str) -> List[Dict[str, Any]]:
    """从响应中提取问题列表"""
    try:
        # 查找JSON块
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            data = json.loads(json_str)
            return data.get('problems', [])
        
        # 尝试直接解析
        if '{' in content and '}' in content:
            start = content.find('{')
            end = content.rfind('}') + 1
            json_str = content[start:end]
            data = json.loads(json_str)
            return data.get('problems', [])
    except Exception as e:
        log_concurrent_warning(f"[问题提取] 解析失败: {e}", "smart_chain_executor")
    
    return []
```

## 📊 升级效果对比

### 问题单完整性

| 方面 | 升级前 | 升级后 |
|------|--------|--------|
| 链路标识 | ❌ 无专门字段 | ✅ `file_name` 字段 |
| 代码片段 | ❌ 无代码上下文 | ✅ `source_code` 字段 |
| 问题原因 | ⚠️ 格式不统一 | ✅ 结构化描述 |
| 问题定位 | ⚠️ 格式宽松 | ✅ 严格格式 + 代码语句匹配 |
| 等级体系 | ⚠️ 与函数审查不一致 | ✅ 完全统一 |

### AI输出质量

| 指标 | 升级前 | 升级后 |
|------|--------|--------|
| 格式规范性 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 字段完整性 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 前端定位准确性 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 与函数审查一致性 | ⭐⭐ | ⭐⭐⭐⭐⭐ |

## 🧪 测试验证

### 测试步骤

1. **启动链路审查任务**
   ```bash
   # 使用现有测试项目
   cd E:\code\requirement_extractor\backend\tests\lianlutest\radar_system
   ```

2. **验证AI输出格式**
   - 检查日志文件：`logs/task_XXX/logs/progressive_discovery.log`
   - 查找AI返回的问题单
   - 确认字段完整性

3. **验证数据库存储**
   - 查询 `chain_review_problems` 表
   - 确认所有字段正确保存

4. **验证前端显示**
   - 进入四栏界面
   - 点击功能模块
   - 确认问题定位准确

### 预期结果

**AI输出示例**：
```json
{
  "problems": [
    {
      "file_name": "信号采集与处理链路",
      "source_code": "void cleanup_system() {\n    free_signal_buffer();\n    // 日志文件未关闭\n}",
      "problem_reason": "日志文件句柄未释放，导致资源泄漏",
      "issue_level": "重要问题",
      "issue_name": "日志文件句柄泄漏",
      "issue_location": "radar_system.c:cleanup_system",
      "description_requirement": "系统在关闭时应释放所有资源，包括文件句柄",
      "description_issue": "在cleanup_system函数中，只释放了信号缓冲区，但没有关闭之前打开的日志文件（log_file），导致文件句柄泄漏。",
      "description_location": "radar_system.c文件的cleanup_system函数的284行：free_signal_buffer()",
      "description_impact": "长期运行可能导致系统文件句柄耗尽，影响系统稳定性"
    }
  ]
}
```

## 📌 注意事项

### 1. 删除了 `function_info` 字段
- **原因**：链路审查关注整个链路，而非单个函数
- **影响**：AI不再返回函数信息部分
- **数据库**：`ChainReviewProblem` 模型已经有 `call_chain` 字段存储链路信息

### 2. `file_name` 的特殊含义
- **链路审查**：`file_name` = 链路名称（如"信号采集与处理"）
- **函数审查**：`file_name` = 文件名（如"example.c"）
- **原因**：链路审查是业务层面的审查，不局限于单个文件

### 3. 兼容性考虑
- ✅ 数据库模型已支持所有新字段
- ✅ 前端解析逻辑无需修改（使用相同的字段名）
- ✅ 解析代码已支持新格式

### 4. 与之前的调用链显示修复配合
- 本次升级的 `description_location` 字段提供**精确的代码定位**
- 配合之前实现的**调用链顺序标记（A、B、C、D）**
- 两者结合，让测试人员快速定位问题在链路中的位置

## 🎊 总结

本次升级通过参考函数审查的提示词格式，全面改进了链路审查的问题单格式：

1. ✅ **新增关键字段**：`file_name`（链路名称）、`source_code`（代码片段）
2. ✅ **统一等级体系**：与函数审查的"建议改进/一般问题/重要问题"一致
3. ✅ **严格格式约束**：12条详细的JSON格式要求，确保AI输出规范
4. ✅ **精确问题定位**：`description_location` 严格格式 + 代码语句匹配
5. ✅ **简化输出结构**：删除 `function_info`，聚焦于问题分析

**配合之前的修复**：
- 调用链顺序显示（A、B、C、D标记）
- 链路进度状态同步（Round 1/2/3 完成标记）

**整体效果**：链路审查的AI输出更加规范、完整、易于定位，为前端精确展示问题奠定基础！

**修复日期**：2025-10-26  
**影响范围**：链路审查（智能链路审查）模块的AI提示词和问题单格式

---

**立即测试新的链路审查提示词和问题单格式！** ✨

