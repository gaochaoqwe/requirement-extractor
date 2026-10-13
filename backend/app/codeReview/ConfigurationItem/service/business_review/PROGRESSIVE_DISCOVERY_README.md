# 渐进式功能发现 - 链路审查优化方案

## 🎯 核心理念

传统的链路审查面临一个核心挑战：**如何在有限的上下文窗口内理解整个代码库？**

渐进式功能发现采用**由粗到细、迭代精化**的策略，让AI像人类工程师一样理解代码：

1. **第一步**：看目录结构，了解整体架构
2. **第二步**：看函数签名，理解模块功能
3. **第三步**：看main函数，验证执行流程
4. **第N步**：深入细化（可选）

每一轮都可以**修正之前的判断**，通过**外部记忆文件**实现轮次间的信息传递。

---

## 📊 架构设计

### 整体流程

```
┌─────────────────────────────────────────────────────────────┐
│                    渐进式功能发现                             │
│                                                               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  Round 1    │───▶│  Round 2    │───▶│  Round 3    │     │
│  │ 目录结构分析 │    │ 函数签名分析 │    │ main函数验证│     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                   │                   │            │
│         ▼                   ▼                   ▼            │
│  ┌──────────────────────────────────────────────────┐       │
│  │           记忆文件 (Memory File)                  │       │
│  │  - 功能列表 (features)                            │       │
│  │  - 调用图 (call_graph)                            │       │
│  │  - 轮次历史 (rounds_history)                      │       │
│  └──────────────────────────────────────────────────┘       │
│                           │                                  │
│                           ▼                                  │
│                  ┌─────────────────┐                        │
│                  │  功能审查阶段    │                        │
│                  │  (基于记忆文件)  │                        │
│                  └─────────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 核心模块

### 1. 记忆管理器 (`memory_manager.py`)

**职责**：存储、加载、更新功能划分记忆

**核心功能**：
- `create_initial_memory()`: 创建初始记忆结构
- `save_round()`: 保存某一轮的分析结果
- `load_round()`: 加载指定轮次的记忆
- `get_visualization_data()`: 导出前端可视化数据

**记忆文件结构**：
```json
{
  "version": "1.0",
  "task_id": 123,
  "project": {
    "name": "my_project",
    "root_path": "/path/to/project",
    "language": "c"
  },
  "discovery": {
    "status": "in_progress",
    "current_round": 2,
    "total_rounds": 3
  },
  "features": [
    {
      "id": "feature_1",
      "name": "数据采集模块",
      "description": "负责从传感器采集数据",
      "confidence": "high",
      "evidence": "基于data_acquisition/目录和collect_*函数",
      "related_files": ["data_acquisition/collector.c"],
      "key_functions": ["collect_data", "init_sensor"],
      "sub_features": [...]
    }
  ],
  "metadata": {
    "created_at": "2025-10-23T10:00:00",
    "rounds_history": [
      {
        "round": 1,
        "method": "directory_analysis",
        "summary": "识别了5个顶层功能模块",
        "ai_decisions": [...]
      }
    ]
  }
}
```

---

### 2. 代码提取器 (`code_extractor.py`)

**职责**：提取代码库的结构化信息

**核心功能**：
- `extract_directory_tree()`: 提取目录树（可控深度）
- `extract_function_signatures()`: 提取所有函数签名
- `find_main_function()`: 定位main函数
- `get_compact_overview()`: 生成紧凑的项目概览

**示例输出**（目录树）：
```
📁 my_project/
  📁 src/
    📁 data_acquisition/
      📄 collector.c
      📄 sensor.c
    📁 processing/
      📄 filter.c
      📄 transform.c
  📄 main.c
```

**示例输出**（函数签名）：
```json
[
  {
    "name": "collect_data",
    "signature": "int collect_data(sensor_t *sensor, data_buffer_t *buffer)",
    "file": "src/data_acquisition/collector.c",
    "line": 45
  }
]
```

---

### 3. 渐进式发现器 (`progressive_discovery.py`)

**职责**：协调多轮渐进式分析流程

**核心流程**：

#### Round 1: 目录结构分析
- **输入**：目录树 + 项目概览
- **AI任务**：给出粗粒度的顶层功能模块划分
- **输出**：顶层功能列表（含证据和置信度）

#### Round 2: 函数签名分析
- **输入**：上一轮记忆 + 所有函数签名（按文件分组）
- **AI任务**：
  1. 审视上一轮的划分，指出不合理的地方
  2. 基于函数签名，细化功能模块
  3. 添加子功能（sub_features）
- **输出**：细化的功能层次结构 + 修正说明

#### Round 3: main函数验证
- **输入**：上一轮记忆 + main函数实现代码
- **AI任务**：
  1. 分析main函数的执行流程
  2. 验证功能划分是否合理
  3. 调整功能优先级和依赖关系
- **输出**：最终功能划分 + 调用依赖图

---

## 🚀 使用方法

### 启用渐进式发现

**方式1：环境变量**
```bash
export ENABLE_PROGRESSIVE_DISCOVERY=true
```

**方式2：配置文件**
```python
# backend/app/codeReview/ConfigurationItem/config.py
ENABLE_PROGRESSIVE_DISCOVERY = True
```

### 编程接口

```python
from backend.app.codeReview.ConfigurationItem.service.business_review.planner.progressive_discovery import ProgressiveDiscovery

# 创建发现器
progressive = ProgressiveDiscovery(
    task_id=123,
    project_root="/path/to/project",
    language='c'
)

# 运行完整的发现流程
result = progressive.run_discovery()

# 查看结果
print(f"总轮次: {result['total_rounds']}")
print(f"记忆文件: {result['memory_path']}")

# 获取可视化数据
viz_data = result['visualization_data']
```

### 主流程集成

渐进式发现已集成到智能链路审查主流程中：

```python
# backend/app/codeReview/ConfigurationItem/service/business_review/chain_review_smart.py

def run_smart_chain_review(...):
    # 自动检测是否启用渐进式发现
    if ENABLE_PROGRESSIVE_DISCOVERY:
        # 使用渐进式多轮发现
        progressive = ProgressiveDiscovery(...)
        result = progressive.run_discovery()
        features = result['features']
    else:
        # 使用传统的一次性发现
        features = discover_features_for_task(...)
    
    # 后续审查流程保持不变
    ...
```

---

## 🌐 前端API接口

### 1. 获取最新记忆
```
GET /code_review/progressive/memory/{task_id}
```

**响应**：
```json
{
  "status": "success",
  "task_id": 123,
  "memory": { ... },
  "visualization": {
    "tree": { ... },
    "statistics": {
      "total_features": 15,
      "total_rounds": 3,
      "status": "completed"
    }
  }
}
```

### 2. 获取指定轮次记忆
```
GET /code_review/progressive/memory/{task_id}/round/{round_num}
```

### 3. 获取可视化数据（树形结构）
```
GET /code_review/progressive/visualization/{task_id}
```

**响应**：
```json
{
  "status": "success",
  "task_id": 123,
  "tree": {
    "name": "my_project",
    "type": "project",
    "children": [
      {
        "id": "feature_1",
        "name": "数据采集模块",
        "confidence": "high",
        "status": "pending",
        "issues_count": 0,
        "children": [...]
      }
    ]
  },
  "statistics": { ... }
}
```

### 4. 获取功能详情
```
GET /code_review/progressive/feature/{task_id}/{feature_id}
```

### 5. 获取轮次历史
```
GET /code_review/progressive/rounds/{task_id}
```

---

## 📈 优势对比

| 特性 | 传统一次性发现 | 渐进式发现 |
|------|---------------|-----------|
| **上下文利用** | 单次，易超限 | 多轮，每轮专注 |
| **准确性** | 一次机会 | 可迭代修正 |
| **可解释性** | 黑盒 | 每轮有理由 |
| **灵活性** | 固定流程 | 可扩展轮次 |
| **调试性** | 困难 | 可回溯每轮 |
| **AI自主性** | 低 | 高（AI可修正） |

---

## 🔍 示例场景

假设有一个C项目：
```
my_control_system/
├── src/
│   ├── sensor/          # 传感器相关
│   │   ├── init.c
│   │   └── read.c
│   ├── controller/      # 控制逻辑
│   │   ├── pid.c
│   │   └── state.c
│   └── actuator/        # 执行器
│       └── motor.c
└── main.c
```

### Round 1 输出（目录结构分析）
```json
{
  "features": [
    {
      "id": "f1",
      "name": "传感器管理",
      "confidence": "high",
      "related_directories": ["src/sensor/"]
    },
    {
      "id": "f2",
      "name": "控制算法",
      "confidence": "high",
      "related_directories": ["src/controller/"]
    },
    {
      "id": "f3",
      "name": "执行器驱动",
      "confidence": "medium",
      "related_directories": ["src/actuator/"]
    }
  ]
}
```

### Round 2 输出（函数签名分析）
```json
{
  "corrections": [
    {
      "previous_feature_id": "f2",
      "issue": "控制算法应该拆分为PID控制和状态管理",
      "action": "split"
    }
  ],
  "features": [
    {
      "id": "f1",
      "name": "传感器管理",
      "sub_features": [
        {
          "id": "f1_1",
          "name": "传感器初始化",
          "related_functions": ["sensor_init", "sensor_calibrate"]
        },
        {
          "id": "f1_2",
          "name": "数据读取",
          "related_functions": ["sensor_read", "sensor_filter"]
        }
      ]
    },
    {
      "id": "f2",
      "name": "PID控制",
      "key_functions": ["pid_compute", "pid_update"]
    },
    {
      "id": "f2_new",
      "name": "状态管理",
      "key_functions": ["state_transition", "state_check"]
    }
  ]
}
```

### Round 3 输出（main函数验证）
```json
{
  "main_flow_analysis": "main函数先初始化传感器，然后进入循环：读取->PID计算->执行器输出",
  "features": [
    {
      "id": "f1",
      "name": "传感器管理",
      "priority": 1,
      "depends_on": []
    },
    {
      "id": "f2",
      "name": "PID控制",
      "priority": 2,
      "depends_on": ["f1"]
    },
    {
      "id": "f3",
      "name": "执行器驱动",
      "priority": 3,
      "depends_on": ["f2"]
    }
  ]
}
```

---

## 🛠️ 扩展性

### 添加新的轮次

可以轻松添加 Round 4、Round 5...

```python
# 在 ProgressiveDiscovery.run_discovery() 中添加
def run_discovery(self):
    # ... Round 1, 2, 3 ...
    
    # Round 4: 数据流分析（可选）
    if self.should_do_round_4():
        round4_result = self._round_4_data_flow_analysis()
        self.memory.save_round(4, round4_result)
```

### 自定义轮次策略

```python
# 子类化 ProgressiveDiscovery
class CustomProgressiveDiscovery(ProgressiveDiscovery):
    def _round_4_security_analysis(self):
        # 自定义的安全分析轮次
        ...
```

---

## 📝 最佳实践

1. **合理控制轮次数量**：通常3-5轮足够，过多轮次会增加时间成本
2. **每轮明确目标**：避免重复分析同样的内容
3. **利用置信度**：低置信度的功能可以在后续轮次重点验证
4. **记录AI决策**：每轮都记录AI的修正理由，便于调试
5. **前端可视化**：展示每轮的演变过程，增强可解释性

---

## 🐛 故障排查

### 问题：记忆文件未生成

**检查**：
- 任务ID是否正确
- 项目路径是否可访问
- 日志目录权限

### 问题：某轮分析失败

**检查**：
- 查看该轮的AI提示词（日志中）
- 检查代码提取器输出是否正常
- 验证AI响应格式是否符合预期

### 问题：功能划分不准确

**优化**：
- 调整AI提示词，提供更多上下文
- 增加更多轮次进行细化
- 手动修正记忆文件后继续

---

## 📚 相关文档

- [智能链路审查总览](./SMART_CHAIN_REVIEW_README.md)
- [功能审查Agent](../../ai/FUNCTION_REVIEW_AGENT_README.md)
- [代码审查模式对比](../../CODE_REVIEW_MODES.md)

---

## 🎓 理论支撑

本方案基于以下软件工程理论：

1. **增量式程序分析**：分阶段理解程序，每阶段聚焦不同抽象层次
2. **记忆增强AI**：使用外部记忆突破上下文限制
3. **层次化抽象**：从系统级到模块级再到函数级
4. **自我修正机制**：允许AI在后续轮次修正之前的判断
5. **知识图谱构建**：渐进式构建代码的功能关系图

---

## 🔬 实验结果（预期）

| 项目规模 | 传统模式耗时 | 渐进式模式耗时 | 功能发现准确率提升 |
|---------|-------------|---------------|------------------|
| 小型（<50文件） | 30s | 45s | +10% |
| 中型（50-200文件） | 2min | 3min | +25% |
| 大型（>200文件） | 失败（上下文溢出） | 8min | +40% |

**结论**：对于大型项目，渐进式发现是**唯一可行**的方案。

---

## 📞 反馈与改进

如有问题或建议，请通过以下方式反馈：
- Issue Tracker
- 邮件联系项目维护者

---

**最后更新**: 2025-10-23
**版本**: v1.0

