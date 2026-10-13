# 渐进式功能发现 - 使用示例

## 快速开始

### 1. 启用渐进式发现

在启动FastAPI服务前，设置环境变量：

```bash
# Windows (PowerShell)
$env:ENABLE_PROGRESSIVE_DISCOVERY="true"

# Windows (CMD)
set ENABLE_PROGRESSIVE_DISCOVERY=true

# Linux/Mac
export ENABLE_PROGRESSIVE_DISCOVERY=true
```

或者在代码中直接修改配置：

```python
# backend/app/codeReview/ConfigurationItem/config.py
ENABLE_PROGRESSIVE_DISCOVERY = True
```

### 2. 后端使用示例

#### 方式A：通过链路审查主流程（推荐）

```python
from backend.app.codeReview.ConfigurationItem.service.business_review.chain_review_smart import run_smart_chain_review

# 自动使用渐进式发现（如果环境变量已启用）
result = run_smart_chain_review(
    task_id=123,
    project_root="/path/to/your/project",
    software_type="嵌入式控制系统",
    entry_function="main",
    kb={"rules": [...]}
)

print(f"发现了 {result['features_count']} 个功能模块")
print(f"发现了 {result['problems_count']} 个问题")
```

#### 方式B：直接使用渐进式发现

```python
from backend.app.codeReview.ConfigurationItem.service.business_review.planner.progressive_discovery import ProgressiveDiscovery

# 创建发现器
progressive = ProgressiveDiscovery(
    task_id=123,
    project_root="/path/to/your/project",
    language='c'  # 或 'cpp', 'python' 等
)

# 运行发现流程
discovery_result = progressive.run_discovery()

# 查看结果
print(f"✅ 发现完成！")
print(f"   总轮次: {discovery_result['total_rounds']}")
print(f"   记忆文件: {discovery_result['memory_path']}")

# 获取发现的功能列表
memory = progressive.memory.load_latest()
features = memory.get("features", [])

for feature in features:
    print(f"\n📦 功能: {feature['name']}")
    print(f"   描述: {feature['description']}")
    print(f"   置信度: {feature['confidence']}")
    print(f"   相关文件: {', '.join(feature.get('related_files', []))}")
```

### 3. 前端API调用示例

#### 获取可视化数据

```javascript
// 获取任务的功能发现可视化数据
async function getProgressiveVisualization(taskId) {
  const response = await fetch(`/api/code_review/progressive/visualization/${taskId}`);
  const data = await response.json();
  
  if (data.status === 'success') {
    console.log('功能树:', data.tree);
    console.log('统计信息:', data.statistics);
    
    // 渲染树形结构
    renderFeatureTree(data.tree);
  } else {
    console.log('暂无渐进式发现数据');
  }
}

// 树形渲染示例（使用 Element Plus 的 Tree 组件）
function renderFeatureTree(treeData) {
  // data.tree 格式：
  // {
  //   "name": "my_project",
  //   "type": "project",
  //   "children": [
  //     {
  //       "id": "feature_1",
  //       "name": "数据采集模块",
  //       "confidence": "high",
  //       "status": "pending",
  //       "issues_count": 0,
  //       "children": [...]
  //     }
  //   ]
  // }
  
  // 使用 el-tree 渲染
  return treeData;
}
```

#### 查看轮次历史

```javascript
// 获取所有轮次的历史
async function getRoundsHistory(taskId) {
  const response = await fetch(`/api/code_review/progressive/rounds/${taskId}`);
  const data = await response.json();
  
  if (data.status === 'success') {
    console.log(`总轮次: ${data.total_rounds}`);
    console.log(`当前状态: ${data.discovery_status}`);
    
    // 遍历每轮历史
    data.rounds.forEach(round => {
      console.log(`\nRound ${round.round}: ${round.method}`);
      console.log(`  摘要: ${round.summary}`);
      console.log(`  时间: ${round.timestamp}`);
    });
  }
}
```

#### 获取功能详情

```javascript
// 获取指定功能的详细信息
async function getFeatureDetail(taskId, featureId) {
  const response = await fetch(`/api/code_review/progressive/feature/${taskId}/${featureId}`);
  const data = await response.json();
  
  if (data.status === 'success') {
    const feature = data.feature;
    console.log('功能名称:', feature.name);
    console.log('功能描述:', feature.description);
    console.log('置信度:', feature.confidence);
    console.log('相关文件:', feature.related_files);
    console.log('关键函数:', feature.key_functions);
    console.log('子功能:', feature.sub_features);
  }
}
```

### 4. Vue 前端组件示例

```vue
<template>
  <div class="progressive-discovery">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>渐进式功能发现</span>
          <el-tag v-if="discoveryData.statistics" :type="statusTagType">
            {{ discoveryData.statistics.status }}
          </el-tag>
        </div>
      </template>
      
      <!-- 统计信息 -->
      <el-row :gutter="20" v-if="discoveryData.statistics">
        <el-col :span="8">
          <el-statistic title="发现功能数" :value="discoveryData.statistics.total_features" />
        </el-col>
        <el-col :span="8">
          <el-statistic title="分析轮次" :value="discoveryData.statistics.total_rounds" />
        </el-col>
        <el-col :span="8">
          <el-statistic title="当前状态" :value="discoveryData.statistics.status" />
        </el-col>
      </el-row>
      
      <!-- 功能树 -->
      <el-divider />
      
      <el-tree
        :data="treeData"
        :props="treeProps"
        default-expand-all
        @node-click="handleNodeClick"
      >
        <template #default="{ node, data }">
          <span class="custom-tree-node">
            <span>{{ node.label }}</span>
            <span class="node-meta">
              <el-tag size="small" :type="getConfidenceType(data.confidence)">
                {{ data.confidence }}
              </el-tag>
              <el-tag size="small" v-if="data.issues_count > 0" type="danger">
                {{ data.issues_count }} 问题
              </el-tag>
            </span>
          </span>
        </template>
      </el-tree>
    </el-card>
    
    <!-- 轮次历史 -->
    <el-card style="margin-top: 20px;">
      <template #header>
        <span>分析历史</span>
      </template>
      
      <el-timeline>
        <el-timeline-item
          v-for="round in roundsHistory"
          :key="round.round"
          :timestamp="round.timestamp"
        >
          <el-card>
            <h4>Round {{ round.round }}: {{ round.method }}</h4>
            <p>{{ round.summary }}</p>
          </el-card>
        </el-timeline-item>
      </el-timeline>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { ElMessage } from 'element-plus';

const props = defineProps({
  taskId: {
    type: Number,
    required: true
  }
});

const discoveryData = ref({});
const roundsHistory = ref([]);

const treeData = computed(() => {
  if (!discoveryData.value.tree) return [];
  return [discoveryData.value.tree];
});

const treeProps = {
  children: 'children',
  label: 'name'
};

const statusTagType = computed(() => {
  const status = discoveryData.value.statistics?.status;
  return status === 'completed' ? 'success' : 'warning';
});

// 加载数据
const loadData = async () => {
  try {
    // 加载可视化数据
    const vizResponse = await fetch(`/api/code_review/progressive/visualization/${props.taskId}`);
    const vizData = await vizResponse.json();
    
    if (vizData.status === 'success') {
      discoveryData.value = vizData;
    }
    
    // 加载轮次历史
    const roundsResponse = await fetch(`/api/code_review/progressive/rounds/${props.taskId}`);
    const roundsData = await roundsResponse.json();
    
    if (roundsData.status === 'success') {
      roundsHistory.value = roundsData.rounds;
    }
    
  } catch (error) {
    ElMessage.error('加载渐进式发现数据失败');
    console.error(error);
  }
};

const handleNodeClick = async (data) => {
  if (data.id) {
    // 加载功能详情
    try {
      const response = await fetch(`/api/code_review/progressive/feature/${props.taskId}/${data.id}`);
      const result = await response.json();
      
      if (result.status === 'success') {
        console.log('功能详情:', result.feature);
        // 在这里可以打开详情对话框
      }
    } catch (error) {
      console.error('加载功能详情失败:', error);
    }
  }
};

const getConfidenceType = (confidence) => {
  const map = {
    'high': 'success',
    'medium': 'warning',
    'low': 'info'
  };
  return map[confidence] || 'info';
};

onMounted(() => {
  loadData();
});
</script>

<style scoped>
.progressive-discovery {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.custom-tree-node {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  padding-right: 8px;
}

.node-meta {
  display: flex;
  gap: 8px;
}
</style>
```

### 5. 测试示例

```python
# test_progressive_discovery.py

import pytest
from pathlib import Path
from backend.app.codeReview.ConfigurationItem.service.business_review.planner.progressive_discovery import ProgressiveDiscovery

def test_progressive_discovery():
    # 准备测试项目
    test_project = Path(__file__).parent / "test_data" / "sample_c_project"
    
    # 创建发现器
    progressive = ProgressiveDiscovery(
        task_id=999,
        project_root=str(test_project),
        language='c'
    )
    
    # 运行发现
    result = progressive.run_discovery()
    
    # 断言
    assert result['status'] == 'completed'
    assert result['total_rounds'] >= 3
    assert Path(result['memory_path']).exists()
    
    # 检查功能列表
    memory = progressive.memory.load_latest()
    features = memory.get('features', [])
    
    assert len(features) > 0
    
    for feature in features:
        assert 'id' in feature
        assert 'name' in feature
        assert 'confidence' in feature
        assert feature['confidence'] in ['high', 'medium', 'low']

def test_memory_manager():
    from backend.app.codeReview.ConfigurationItem.service.business_review.memory.memory_manager import MemoryManager
    
    test_project = Path(__file__).parent / "test_data" / "sample_c_project"
    
    memory = MemoryManager(task_id=999, project_root=str(test_project))
    
    # 创建初始记忆
    initial = memory.create_initial_memory({"name": "test_project", "language": "c"})
    
    assert initial['task_id'] == 999
    assert initial['project']['name'] == "test_project"
    
    # 保存一轮
    round_data = {
        "method": "test_round",
        "summary": "测试轮次",
        "features": [
            {
                "id": "test_feature",
                "name": "测试功能",
                "confidence": "high"
            }
        ]
    }
    
    filepath = memory.save_round(1, round_data)
    assert Path(filepath).exists()
    
    # 加载
    loaded = memory.load_round(1)
    assert loaded is not None
    assert loaded['discovery']['current_round'] == 1

def test_code_extractor():
    from backend.app.codeReview.ConfigurationItem.service.business_review.tools.code_extractor import CodeExtractor
    
    test_project = Path(__file__).parent / "test_data" / "sample_c_project"
    
    extractor = CodeExtractor(str(test_project), language='c')
    
    # 测试目录树提取
    tree = extractor.extract_directory_tree(max_depth=3)
    assert tree['type'] == 'directory'
    assert 'children' in tree
    
    # 测试函数签名提取
    functions = extractor.extract_function_signatures()
    assert isinstance(functions, list)
    
    # 测试main函数查找
    main_func = extractor.find_main_function()
    # 可能找到也可能找不到，取决于测试项目
    if main_func:
        assert main_func['name'] == 'main'
        assert main_func['is_main'] == True

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
```

---

## 调试技巧

### 1. 查看记忆文件

记忆文件保存在：
```
backend/app/codeReview/ConfigurationItem/logs/task_{task_id}/memory/
```

可以直接打开JSON文件查看：
```bash
cat backend/app/codeReview/ConfigurationItem/logs/task_123/memory/latest.json
```

### 2. 查看AI提示词

在代码中添加日志：
```python
# 在 progressive_discovery.py 的 _round_1_directory_analysis 等方法中
print(f"\n=== AI提示词 ===\n{prompt}\n================\n")
```

### 3. 单步调试

```python
# 只运行特定轮次
progressive = ProgressiveDiscovery(...)

# 手动运行Round 1
round1_result = progressive._round_1_directory_analysis()
print(round1_result)

# 检查结果后，再运行Round 2
progressive.memory.save_round(1, round1_result)
round2_result = progressive._round_2_function_signature_analysis()
```

---

## 常见问题

**Q: 如何禁用渐进式发现？**

A: 设置环境变量 `ENABLE_PROGRESSIVE_DISCOVERY=false` 或在配置文件中修改。

**Q: 能否自定义轮次数量？**

A: 可以。修改 `ProgressiveDiscovery` 类的 `run_discovery` 方法，添加或移除轮次。

**Q: 记忆文件会占用多少空间？**

A: 通常每个任务的记忆文件不超过1MB。可以定期清理旧任务的记忆。

**Q: 能否在前端触发重新发现？**

A: 可以添加一个API端点来重新运行发现流程，但建议只在开发/测试时使用。

---

**提示**：完整的API文档请参考 [PROGRESSIVE_DISCOVERY_README.md](./PROGRESSIVE_DISCOVERY_README.md)

