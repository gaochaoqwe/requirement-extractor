# 智能链路审查 - 使用指南

## 📋 概述

智能链路审查是对原有固定链路审查的升级，核心区别：

| 特性 | 旧版链路审查 | 新版智能链路审查 |
|------|-------------|----------------|
| 功能划分 | 基于固定调用图算法 | **AI自主发现和理解** |
| 审查方式 | 固定模板 | **AI ReAct模式探索** |
| 上下文控制 | 可能超token | **智能分批，严格控制** |
| 灵活性 | 受限于预设规则 | **AI自适应** |
| 工具使用 | 无 | **7个代码分析工具** |

## 🎯 核心优势

### 1. AI自主功能发现
- **输入**：仅需入口函数（如`main`）
- **AI做什么**：
  - 阅读入口函数代码
  - 分析项目结构
  - 根据代码语义和文件名推断功能模块
  - 自动划分功能边界

### 2. 智能上下文管理
- **Token限制**：60000 tokens总限制
- **策略**：
  - 每个功能模块<15000 tokens
  - 分批审查，逐个击破
  - 自动检测是否需要细分

### 3. ReAct探索模式
AI在审查每个功能时：
```
第1轮：使用 get_file_outline 快速浏览文件结构
  ↓
第2轮：使用 read_file_range 读取关键函数代码
  ↓
第3轮：使用 search_function_by_name 追踪调用关系
  ↓
第4轮：使用 get_function_context 深入理解上下文
  ↓
第N轮：输出最终问题单
```

## 🔧 启用方法

### 方法1：环境变量（推荐）

```bash
# Windows PowerShell
$env:ENABLE_SMART_CHAIN_REVIEW = "true"

# Linux/Mac
export ENABLE_SMART_CHAIN_REVIEW=true

# 禁用（回退到旧版）
export ENABLE_SMART_CHAIN_REVIEW=false
```

### 方法2：代码集成

在 `business_runner.py` 中：

```python
from .chain_review_smart import run_smart_chain_review, enable_smart_chain_review

# 在链路审查部分
if enable_smart_chain_review():
    # 使用新的智能链路审查
    result = run_smart_chain_review(
        task_id=task_id,
        project_root=project_root,
        software_type=software_type,
        entry_function=entry_function,
        kb=kb
    )
else:
    # 使用旧的固定链路审查
    chains = plan_chains(...)
```

## 📊 工作流程

```
┌─────────────────────────────────────────────────┐
│  阶段1: AI功能发现（Smart Discovery）           │
│  ───────────────────────────────────────────    │
│  输入：入口函数（如main）                       │
│  处理：                                         │
│    1. 获取项目结构                             │
│    2. 分析入口函数                             │
│    3. AI推断功能模块                           │
│    4. Token估算和细分                          │
│  输出：功能列表                                │
│    [                                           │
│      {                                         │
│        "name": "系统初始化",                   │
│        "description": "...",                   │
│        "estimated_files": [...],               │
│        "estimated_tokens": 8000,               │
│        "priority": "高"                        │
│      },                                        │
│      ...                                       │
│    ]                                           │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  阶段2: 分批审查（Batch Review）                │
│  ───────────────────────────────────────────    │
│  对每个功能模块：                               │
│    1. 初始化Agent（ReAct模式）                 │
│    2. AI使用工具探索代码：                     │
│       - get_file_outline                       │
│       - read_file_range                        │
│       - get_function_context                   │
│       - search_function_by_name                │
│       - ...                                    │
│    3. AI理解业务逻辑                           │
│    4. 识别业务问题                             │
│    5. 输出问题单                               │
│  保存到数据库                                  │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  阶段3: 结果汇总                                │
│  ───────────────────────────────────────────    │
│  统计：                                         │
│    - 审查功能数                                │
│    - 发现问题数                                │
│    - 每个功能的问题分布                        │
│  返回给前端                                    │
└─────────────────────────────────────────────────┘
```

## 🛠️ 可用工具

AI在审查时可以调用的7个工具：

| 工具名 | 用途 | 示例 |
|-------|------|------|
| `get_file_outline` | 快速浏览文件结构 | 获取函数列表、宏定义、include |
| `read_file_range` | 读取指定行范围 | 读取第100-150行 |
| `get_function_context` | 获取函数完整代码 | 获取第120行所在函数 |
| `search_function_by_name` | 搜索函数定义 | 搜索`process_data`函数 |
| `search_function_in_file` | 在文件中搜索函数 | 在main.c中搜索`init` |
| `read_file` | 读取整个文件 | 读取小文件（<500行） |
| `list_directory` | 列出目录内容 | 浏览项目结构 |

## 📝 示例：AI审查过程

假设审查"数据处理"功能模块：

```
【AI思考】
这个功能模块涉及data_process.c文件，我先看看文件结构。

【AI行动】
调用工具：get_file_outline("data_process.c")

【工具返回】
{
  "functions": ["init_buffer", "process_data", "validate_input"],
  "macros": ["MAX_SIZE", "BUFFER_LEN"],
  "total_lines": 320
}

【AI思考】
看到了process_data函数，这应该是核心函数，我需要读取它的代码。

【AI行动】
调用工具：search_function_by_name("process_data")

【工具返回】
{
  "locations": [
    {"file": "data_process.c", "line": 45}
  ]
}

【AI行动】
调用工具：get_function_context("data_process.c", 45)

【工具返回】
{
  "code": "void process_data(int *buf, int size) {\n  for(int i=0; i<=size; i++) {\n    buf[i] = ...\n  }\n}"
}

【AI思考】
发现问题！循环条件是i<=size，这会导致数组越界！

【最终问题单】
{
  "problems": [
    {
      "issue_name": "数组越界风险",
      "issue_level": "严重",
      "issue_location": "data_process.c:46",
      "description_issue": "循环条件使用i<=size会导致访问buf[size]，超出数组边界",
      ...
    }
  ]
}
```

## ⚙️ 配置参数

在 `smart_feature_discovery.py` 中可调整：

```python
class SmartFeatureDiscovery:
    def __init__(...):
        # Token限制
        self.MAX_TOKENS_PER_FEATURE = 15000  # 每个功能模块
        self.MAX_TOTAL_CONTEXT = 60000       # 模型总上下文
```

在 `smart_chain_executor.py` 中可调整：

```python
class SmartChainExecutor:
    def __init__(...):
        self.max_iterations = 8              # 最多8轮推理
        self.max_tool_calls_per_iteration = 3  # 每轮最多3个工具
```

## 🔍 对比示例

### 旧版链路审查
```
输入：main函数
处理：
  1. 构建完整调用图（可能很大）
  2. 按固定算法划分链路
  3. 批量生成提示词
  4. AI直接输出问题（没有探索过程）
问题：
  - 调用图可能不准确
  - 划分可能不合理
  - AI缺乏灵活性
  - 容易超token
```

### 新版智能链路审查
```
输入：main函数
处理：
  1. AI阅读main函数代码
  2. AI推断有哪些功能模块
  3. 对每个功能模块：
     a. AI选择使用哪个工具
     b. AI读取必要的代码
     c. AI理解业务逻辑
     d. AI识别问题
  4. 输出问题单
优势：
  ✅ AI自主理解
  ✅ 灵活探索
  ✅ 严格控制token
  ✅ 更准确的功能划分
```

## 🚀 下一步

1. **测试新功能**：
   ```bash
   cd backend
   python -m app.codeReview.ConfigurationItem.service.business_review.test_smart_chain
   ```

2. **监控日志**：
   - 查看 `logs/bg_debug.txt`
   - 搜索 `[智能链路审查]` 标签

3. **对比结果**：
   - 先用旧版审查一次
   - 再用新版审查一次
   - 对比问题单质量

## ❓ 常见问题

### Q1: 新版会更慢吗？
**A**: 可能会稍慢，因为AI需要多轮推理。但质量更高，且避免了token超限的失败。

### Q2: 如何回退到旧版？
**A**: 设置环境变量 `ENABLE_SMART_CHAIN_REVIEW=false`

### Q3: 能否同时使用两种方式？
**A**: 可以。保留文件审查和函数审查，链路审查使用智能版本。

### Q4: AI如何知道何时停止探索？
**A**: 
- 达到最大迭代次数（8轮）
- AI判断已理解代码并输出问题单
- 遇到工具调用错误

### Q5: 如果功能太多怎么办？
**A**: AI会自动估算token并细分功能，确保每个功能<15000 tokens。

## 📚 相关文件

- `smart_feature_discovery.py` - AI功能发现器
- `smart_chain_executor.py` - 智能审查执行器
- `chain_review_smart.py` - 主入口和集成
- `planner/chain_planner.py` - 旧版链路规划（仍保留）

