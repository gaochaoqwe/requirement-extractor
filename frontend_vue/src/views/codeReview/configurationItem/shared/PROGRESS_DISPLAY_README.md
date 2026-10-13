# 代码审查进度显示功能

## 概述

为代码审查的函数审查和链路审查代码视图页面添加了实时进度显示功能，用户可以在查看代码地图的同时实时了解审查任务的进展情况。

## 功能特性

### 1. 实时进度显示
- 自动轮询获取任务进度
- 支持函数审查和链路审查两种模式
- 显示总体进度和详细分项进度
- 实时状态更新和消息提示

### 2. 用户界面
- 浮动式进度面板，不遮挡主要内容
- 支持最小化/展开操作
- 可手动关闭进度显示
- 响应式设计，适配不同屏幕尺寸

### 3. 进度信息
- **函数审查**: 显示函数审查进度和业务审查进度
- **链路审查**: 显示功能发现进度和链路审查进度
- 显示当前状态消息和最后更新时间

## 使用方法

### 在Vue组件中使用

```vue
<template>
  <div>
    <!-- 其他内容 -->
    
    <!-- 进度显示组件 -->
    <ProgressDisplay
      :task-id="taskId"
      :auto-start="true"
      :review-type="reviewType"
      @progress-updated="handleProgressUpdated"
      @task-completed="handleTaskCompleted"
      @task-failed="handleTaskFailed"
    />
  </div>
</template>

<script setup>
import ProgressDisplay from '../shared/ProgressDisplay.vue'

// Props
const taskId = ref(123)
const reviewType = ref('function') // 'function' 或 'chain'

// 事件处理
function handleProgressUpdated(progressData) {
  console.log('进度更新:', progressData)
}

function handleTaskCompleted(taskData) {
  console.log('任务完成:', taskData)
  // 可以在这里重新加载数据或执行其他操作
}

function handleTaskFailed(taskData) {
  console.log('任务失败:', taskData)
  // 处理任务失败的情况
}
</script>
```

### 组件属性

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `task-id` | String/Number | - | 任务ID（必需） |
| `auto-start` | Boolean | true | 是否自动开始轮询 |
| `poll-interval` | Number | 3000 | 轮询间隔（毫秒） |
| `review-type` | String | 'function' | 审查类型：'function' 或 'chain' |

### 组件事件

| 事件名 | 参数 | 说明 |
|--------|------|------|
| `progress-updated` | progressData | 进度更新时触发 |
| `task-completed` | taskData | 任务完成时触发 |
| `task-failed` | taskData | 任务失败时触发 |

### 组件方法

可以通过ref获取组件实例并调用以下方法：

```vue
<script setup>
const progressDisplayRef = ref(null)

// 手动开始进度跟踪
function startTracking() {
  progressDisplayRef.value?.startProgressTracking()
}

// 停止进度跟踪
function stopTracking() {
  progressDisplayRef.value?.stopProgressTracking()
}

// 显示/隐藏进度面板
function showProgress() {
  progressDisplayRef.value?.show()
}

function hideProgress() {
  progressDisplayRef.value?.hide()
}

// 检查是否正在跟踪
function isTracking() {
  return progressDisplayRef.value?.isTracking()
}
</script>
```

## API接口

### 函数审查进度API

**接口**: `GET /api/codeReview/task_progress/{task_id}`

**响应格式**:
```json
{
  "task_id": 123,
  "status": "processing",
  "progress": 65,
  "message": "正在执行代码审查...",
  "analysis_type": "function_review",
  "details": {
    "function_progress": 70,
    "business_progress": 60,
    "function_status": "processing",
    "business_status": "processing"
  }
}
```

### 链路审查进度API

**接口**: `GET /api/codeReview/progressive/progress/{task_id}`

**响应格式**:
```json
{
  "status": "processing",
  "overall_progress": 75,
  "discovery_progress": 100,
  "review_progress": 50,
  "message": "正在进行链路审查...",
  "discovery_status": "completed",
  "review_status": "in_progress"
}
```

## 状态说明

### 任务状态
- `pending`: 任务准备中
- `processing`: 正在处理
- `idle`: 任务暂停
- `completed`: 任务完成
- `failed`: 任务失败

### 进度状态
- `""` (空字符串): 正常进行中
- `success`: 成功完成
- `exception`: 出现异常

## 样式定制

进度显示组件使用了CSS变量，可以通过覆盖这些变量来定制样式：

```css
.progress-display {
  --progress-bg: rgba(255, 255, 255, 0.95);
  --progress-border: rgba(255, 255, 255, 0.2);
  --progress-shadow: rgba(0, 0, 0, 0.1);
  --progress-header-bg: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
```

## 测试

使用提供的测试脚本来验证进度显示功能：

```bash
# 测试函数审查进度
python backend/app/codeReview/ConfigurationItem/test_progress_display.py 123 function

# 测试链路审查进度
python backend/app/codeReview/ConfigurationItem/test_progress_display.py 456 chain
```

## 注意事项

1. **网络异常处理**: 组件会自动处理网络异常，在连接失败时会延长轮询间隔并重试
2. **内存管理**: 组件会在卸载时自动清理轮询定时器，避免内存泄漏
3. **用户体验**: 进度面板支持最小化，不会影响用户查看代码地图
4. **响应式设计**: 在小屏幕设备上会自动调整布局和尺寸

## 更新日志

### v1.0.0 (2025-11-07)
- ✅ 添加基础进度显示功能
- ✅ 支持函数审查和链路审查两种模式
- ✅ 实现实时轮询和状态更新
- ✅ 添加用户界面交互功能
- ✅ 集成到代码视图页面
- ✅ 添加错误处理和容错机制
