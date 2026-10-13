# 链路审查进度UI优化指南

## 🎯 优化目标

改进链路审查进度页面的显示方式：
1. ✅ **横向显示**：Round 1-3 横向排列，不纵向堆叠
2. ✅ **分段显示**：前50%显示Round状态，后50%显示功能审查进度
3. ✅ **精确同步**：确保显示与后端真实活动一致
4. ✅ **状态切换**：Round 3 完成后立即切换到功能审查显示

---

## 📊 新增API返回字段

### 后端API：`GET /api/code-review/business/progress?task_id={task_id}`

**新增字段**：

```json
{
  "status": "reviewing",
  "overall_progress": 75.0,
  "discovery_progress": 50.0,
  "review_progress": 75.0,
  
  // ✅ 新增：结构化的Round信息（用于前半段横向显示）
  "rounds_info": [
    {
      "round": 1,
      "title": "目录结构分析",
      "description": "基于目录结构的粗粒度划分",
      "status": "completed",  // completed | in_progress | pending
      "timestamp": "2025/10/26 21:30:23"
    },
    {
      "round": 2,
      "title": "函数签名分析",
      "description": "分批分析（多个模块）+ 最终汇总",
      "status": "completed",
      "timestamp": "2025/10/26 21:31:10"
    },
    {
      "round": 3,
      "title": "main函数验证",
      "description": "功能发现完成",
      "status": "completed",
      "timestamp": "2025/10/26 21:31:31"
    }
  ],
  
  // ✅ 新增：当前审查的功能点名称（用于后半段显示）
  "current_reviewing_feature": "信号采集与处理",
  
  "features_count": 7,
  "reviewed_features": 3,
  "discovery_status": "completed",
  "current_round": 3
}
```

---

## 🎨 前端UI设计

### 布局结构

```
┌────────────────────────────────────────────────────────────┐
│                    链路审查 - 实时进度                        │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│  进度条 [████████████████████████░░░░░░░░░░░░] 75%         │
│         ↑前50%（Round 1-3）     ↑后50%（功能审查）          │
└────────────────────────────────────────────────────────────┘

【前50%区域：Round状态横向显示】
┌─────────────┬─────────────┬─────────────┐
│ Round 1: ✅ │ Round 2: ✅ │ Round 3: ✅ │
│ 目录结构分析│ 函数签名分析│ main函数验证│
│ 基于目录... │ 分批分析... │ 功能发现完成│
│ 21:30:23   │ 21:31:10   │ 21:31:31   │
└─────────────┴─────────────┴─────────────┘

【后50%区域：功能审查状态】
┌────────────────────────────────────────┐
│ 🔍 正在审查：信号采集与处理 (3/7)      │
└────────────────────────────────────────┘
```

---

## 💻 前端实现代码

### Vue 3 实现示例

```vue
<template>
  <div class="chain-review-progress">
    <!-- 标题 -->
    <div class="header">
      <h2>链路审查 - 实时进度</h2>
      <button @click="goBack">返回</button>
    </div>

    <!-- 进度条 -->
    <div class="progress-section">
      <div class="progress-bar-wrapper">
        <div class="progress-bar">
          <div 
            class="progress-fill" 
            :style="{ width: progress.overall_progress + '%' }"
          />
          <!-- 中点标记（50%处） -->
          <div class="midpoint-marker"></div>
        </div>
        <div class="progress-text">{{ progress.overall_progress.toFixed(0) }}%</div>
      </div>
      
      <!-- 进度条下方的区域标签 -->
      <div class="progress-labels">
        <span class="label label-discovery">功能发现（Round 1-3）</span>
        <span class="label label-review">功能审查</span>
      </div>
    </div>

    <!-- Round 状态横向显示（前50%） -->
    <div v-if="progress.discovery_progress < 50 || progress.overall_progress <= 50" class="rounds-section">
      <h3>分析轮次</h3>
      <div class="rounds-horizontal">
        <div 
          v-for="round in progress.rounds_info" 
          :key="round.round"
          class="round-card"
          :class="'round-' + round.status"
        >
          <div class="round-header">
            <span class="round-icon">{{ getRoundIcon(round.status) }}</span>
            <span class="round-title">Round {{ round.round }}: {{ round.title }}</span>
          </div>
          <div class="round-description">{{ round.description }}</div>
          <div v-if="round.timestamp" class="round-timestamp">
            {{ round.timestamp }}
          </div>
        </div>
      </div>
    </div>

    <!-- 功能审查状态（后50%） -->
    <div v-else-if="progress.status === 'reviewing'" class="review-section">
      <h3>功能审查进度</h3>
      <div class="current-feature">
        <span class="feature-icon">🔍</span>
        <span class="feature-text">
          正在审查：<strong>{{ progress.current_reviewing_feature }}</strong>
          ({{ progress.reviewed_features }}/{{ progress.features_count }})
        </span>
      </div>
    </div>

    <!-- 完成状态 -->
    <div v-else-if="progress.status === 'completed'" class="completed-section">
      <div class="completed-message">
        <span class="completed-icon">✅</span>
        <span class="completed-text">
          审查完成！共发现 {{ progress.features_count }} 个功能模块
        </span>
      </div>
      
      <!-- 操作按钮 -->
      <div v-if="progress.show_action_buttons" class="action-buttons">
        <button 
          v-for="action in progress.actions" 
          :key="action.type"
          @click="handleAction(action)"
          class="action-button"
        >
          {{ action.label }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const props = defineProps({
  taskId: {
    type: Number,
    required: true
  }
});

const progress = ref({
  status: 'discovering',
  overall_progress: 0,
  discovery_progress: 0,
  review_progress: 0,
  rounds_info: [],
  current_reviewing_feature: null,
  features_count: 0,
  reviewed_features: 0,
  show_action_buttons: false,
  actions: []
});

let progressTimer = null;

const fetchProgress = async () => {
  try {
    const response = await fetch(`/api/code-review/business/progress?task_id=${props.taskId}`);
    const data = await response.json();
    progress.value = data;
  } catch (error) {
    console.error('获取进度失败:', error);
  }
};

const getRoundIcon = (status) => {
  switch (status) {
    case 'completed': return '✅';
    case 'in_progress': return '🔄';
    case 'pending': return '⏳';
    default: return '⚪';
  }
};

const handleAction = (action) => {
  if (action.type === 'download') {
    window.open(action.url, '_blank');
  } else if (action.type === 'view_code') {
    router.push(`/codemap/${props.taskId}`);
  }
};

const goBack = () => {
  router.back();
};

onMounted(() => {
  fetchProgress();
  // 轮询进度（每2秒）
  progressTimer = setInterval(fetchProgress, 2000);
});

onUnmounted(() => {
  if (progressTimer) {
    clearInterval(progressTimer);
  }
});
</script>

<style scoped>
.chain-review-progress {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

/* 进度条样式 */
.progress-section {
  margin-bottom: 40px;
}

.progress-bar-wrapper {
  position: relative;
  margin-bottom: 10px;
}

.progress-bar {
  position: relative;
  width: 100%;
  height: 24px;
  background: #e0e0e0;
  border-radius: 12px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4CAF50 0%, #2196F3 50%, #FF9800 100%);
  transition: width 0.5s ease;
}

/* 中点标记（50%处） */
.midpoint-marker {
  position: absolute;
  left: 50%;
  top: 0;
  width: 2px;
  height: 100%;
  background: rgba(0, 0, 0, 0.3);
  transform: translateX(-50%);
}

.progress-text {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  font-weight: bold;
  color: white;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
}

.progress-labels {
  display: flex;
  justify-content: space-between;
  padding: 0 10px;
}

.label {
  font-size: 12px;
  color: #666;
}

.label-discovery {
  flex: 0 0 50%;
}

.label-review {
  flex: 0 0 50%;
  text-align: right;
}

/* Round 状态横向显示 */
.rounds-section {
  margin-bottom: 30px;
}

.rounds-horizontal {
  display: flex;
  gap: 20px;
  justify-content: space-between;
}

.round-card {
  flex: 1;
  padding: 16px;
  border-radius: 8px;
  border: 2px solid #e0e0e0;
  background: white;
  transition: all 0.3s ease;
}

.round-card.round-completed {
  border-color: #4CAF50;
  background: #f1f8f4;
}

.round-card.round-in_progress {
  border-color: #2196F3;
  background: #e3f2fd;
  animation: pulse 2s infinite;
}

.round-card.round-pending {
  border-color: #e0e0e0;
  background: #fafafa;
  opacity: 0.6;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.02); }
}

.round-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  font-weight: bold;
}

.round-icon {
  font-size: 20px;
  margin-right: 8px;
}

.round-description {
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}

.round-timestamp {
  font-size: 12px;
  color: #999;
}

/* 功能审查状态 */
.review-section {
  margin-bottom: 30px;
}

.current-feature {
  display: flex;
  align-items: center;
  padding: 20px;
  background: #e3f2fd;
  border-radius: 8px;
  border-left: 4px solid #2196F3;
}

.feature-icon {
  font-size: 24px;
  margin-right: 12px;
}

.feature-text {
  font-size: 16px;
}

/* 完成状态 */
.completed-section {
  text-align: center;
}

.completed-message {
  padding: 30px;
  background: #f1f8f4;
  border-radius: 8px;
  margin-bottom: 20px;
}

.completed-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 16px;
}

.completed-text {
  font-size: 18px;
  color: #4CAF50;
  font-weight: bold;
}

.action-buttons {
  display: flex;
  gap: 16px;
  justify-content: center;
}

.action-button {
  padding: 12px 24px;
  font-size: 16px;
  border: none;
  border-radius: 4px;
  background: #2196F3;
  color: white;
  cursor: pointer;
  transition: background 0.3s;
}

.action-button:hover {
  background: #1976D2;
}
</style>
```

---

## 🔄 状态切换逻辑

### 关键判断条件

```javascript
// 1. 判断当前应该显示哪个区域
const shouldShowRounds = computed(() => {
  // 功能发现阶段（前50%）或刚完成
  return progress.value.discovery_progress < 50 || 
         progress.value.overall_progress <= 50;
});

const shouldShowReview = computed(() => {
  // 功能审查阶段（后50%）
  return progress.value.status === 'reviewing' && 
         !shouldShowRounds.value;
});

// 2. Round 3 完成后的切换
// 后端会确保：
// - discovery_status === "completed"
// - discovery_progress === 50.0
// - 所有 rounds_info[x].status === "completed"
// - status 切换为 "reviewing"
// - current_reviewing_feature 有值

// 前端根据这些状态自动切换显示
```

---

## 📱 响应式设计

```css
/* 移动端适配 */
@media (max-width: 768px) {
  .rounds-horizontal {
    flex-direction: column;
    gap: 16px;
  }
  
  .round-card {
    width: 100%;
  }
  
  .progress-labels {
    font-size: 10px;
  }
}
```

---

## 🎯 测试验证清单

### 1️⃣ Round 1-3 阶段测试

- [ ] Round 1 进行中：只有Round 1显示🔄，其他显示⏳
- [ ] Round 2 进行中：Round 1显示✅，Round 2显示🔄，Round 3显示⏳
- [ ] Round 3 进行中：Round 1-2显示✅，Round 3显示🔄
- [ ] 每个Round完成后立即显示时间戳

### 2️⃣ 状态切换测试

- [ ] Round 3 完成瞬间：所有Round显示✅
- [ ] 进入审查阶段：Round区域消失，显示功能审查区域
- [ ] 功能审查区域正确显示当前审查的功能点名称

### 3️⃣ 进度条同步测试

- [ ] Round 1-3：进度在0-50%之间
- [ ] 功能审查：进度在50-100%之间
- [ ] 进度条颜色渐变正确（前半段绿→蓝，后半段蓝→橙）

### 4️⃣ 完成状态测试

- [ ] 审查完成后显示完成消息
- [ ] 显示"下载审查结果"按钮
- [ ] 显示"代码视图"按钮
- [ ] 按钮点击正确响应

---

## 🆕 API返回数据示例

### 示例1：Round 2 进行中

```json
{
  "status": "discovering",
  "overall_progress": 33.34,
  "discovery_progress": 33.34,
  "rounds_info": [
    {
      "round": 1,
      "title": "目录结构分析",
      "description": "基于目录结构的粗粒度划分",
      "status": "completed",
      "timestamp": "2025/10/26 21:30:23"
    },
    {
      "round": 2,
      "title": "函数签名分析",
      "description": "分批分析（多个模块）+ 最终汇总",
      "status": "in_progress",
      "timestamp": ""
    },
    {
      "round": 3,
      "title": "main函数验证",
      "description": "功能发现完成",
      "status": "pending",
      "timestamp": ""
    }
  ],
  "current_reviewing_feature": null,
  "discovery_status": "in_progress",
  "current_round": 2
}
```

### 示例2：功能审查进行中

```json
{
  "status": "reviewing",
  "overall_progress": 71.43,
  "discovery_progress": 50.0,
  "review_progress": 71.43,
  "rounds_info": [
    {
      "round": 1,
      "title": "目录结构分析",
      "status": "completed",
      "timestamp": "2025/10/26 21:30:23"
    },
    {
      "round": 2,
      "title": "函数签名分析",
      "status": "completed",
      "timestamp": "2025/10/26 21:31:10"
    },
    {
      "round": 3,
      "title": "main函数验证",
      "status": "completed",
      "timestamp": "2025/10/26 21:31:31"
    }
  ],
  "current_reviewing_feature": "信号采集与处理",
  "features_count": 7,
  "reviewed_features": 3,
  "discovery_status": "completed"
}
```

---

## 🎊 总结

**后端改进**：
1. ✅ 新增 `rounds_info` 字段：结构化的Round状态数组
2. ✅ 新增 `current_reviewing_feature` 字段：当前审查的功能点名称
3. ✅ 确保状态切换准确：Round 3 完成后立即切换为 "reviewing"

**前端改进**：
1. ✅ Round 1-3 横向排列显示
2. ✅ 状态图标清晰：✅完成 🔄进行中 ⏳待开始
3. ✅ 分段显示：前50%显示Round，后50%显示功能审查
4. ✅ 进度条带中点标记（50%处）
5. ✅ 响应式设计：支持移动端

**效果**：进度显示清晰、直观、与后端活动完全同步！🎉

---

**修复日期**：2025-10-26  
**影响范围**：链路审查进度显示页面

**立即使用新的进度API和UI设计！** ✨

