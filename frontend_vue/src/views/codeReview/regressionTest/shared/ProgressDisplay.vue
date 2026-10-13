<template>
  <!-- 折叠状态：圆形悬浮球 -->
  <div 
    v-if="showProgress && isMinimized" 
    class="progress-ball" 
    @click="toggleMinimize"
    :title="statusMessage"
  >
    <!-- 水波上涨效果 -->
    <div class="water-wave" :style="{ height: overallProgress + '%' }">
      <div class="wave"></div>
      <div class="wave wave-2"></div>
    </div>
    <!-- 进度数字 -->
    <div class="progress-number">
      <div class="number">{{ overallProgress }}</div>
      <div class="percent">%</div>
    </div>
    <!-- 关闭按钮 -->
    <div class="ball-close" @click.stop="closeProgress">
      <el-icon><Close /></el-icon>
    </div>
  </div>

  <!-- 展开状态：完整进度面板 -->
  <div class="progress-display" v-if="showProgress && !isMinimized">
    <div class="progress-header">
      <div class="progress-title">
        <el-icon><Loading /></el-icon>
        <span>{{ progressTitle }}</span>
      </div>
      <div class="progress-actions">
        <el-button 
          link
          size="small" 
          @click="toggleMinimize"
          class="minimize-btn"
        >
          <el-icon><Minus /></el-icon>
        </el-button>
        <el-button 
          link
          size="small" 
          @click="closeProgress"
          class="close-btn"
        >
          <el-icon><Close /></el-icon>
        </el-button>
      </div>
    </div>
    
    <div class="progress-content">
      <!-- 总体进度条 -->
      <div class="overall-progress">
        <div class="progress-info">
          <span class="progress-label">总体进度</span>
          <span class="progress-percentage">{{ overallProgress }}%</span>
        </div>
        <el-progress 
          :percentage="overallProgress" 
          :status="progressStatus"
          :stroke-width="8"
          :show-text="false"
        />
      </div>
      
      <!-- 详细进度信息 -->
      <div v-if="progressDetails" class="progress-details">
        <!-- 函数审查进度 -->
        <div v-if="progressDetails.function_progress !== undefined" class="detail-item">
          <div class="detail-info">
            <span class="detail-label">函数审查</span>
            <span class="detail-percentage">{{ progressDetails.function_progress }}%</span>
          </div>
          <el-progress 
            :percentage="progressDetails.function_progress" 
            :stroke-width="6"
            :show-text="false"
            color="#409EFF"
          />
        </div>
        
        <!-- 业务审查进度 -->
        <div v-if="progressDetails.business_progress !== undefined" class="detail-item">
          <div class="detail-info">
            <span class="detail-label">业务审查</span>
            <span class="detail-percentage">{{ progressDetails.business_progress }}%</span>
          </div>
          <el-progress 
            :percentage="progressDetails.business_progress" 
            :stroke-width="6"
            :show-text="false"
            color="#67C23A"
          />
        </div>
        
        <!-- 链路审查发现进度 -->
        <div v-if="progressDetails.discovery_progress !== undefined" class="detail-item">
          <div class="detail-info">
            <span class="detail-label">功能发现</span>
            <span class="detail-percentage">{{ progressDetails.discovery_progress }}%</span>
          </div>
          <el-progress 
            :percentage="progressDetails.discovery_progress" 
            :stroke-width="6"
            :show-text="false"
            color="#E6A23C"
          />
        </div>
        
        <!-- 链路审查审查进度 -->
        <div v-if="progressDetails.review_progress !== undefined" class="detail-item">
          <div class="detail-info">
            <span class="detail-label">链路审查</span>
            <span class="detail-percentage">{{ progressDetails.review_progress }}%</span>
          </div>
          <el-progress 
            :percentage="progressDetails.review_progress" 
            :stroke-width="6"
            :show-text="false"
            color="#67C23A"
          />
        </div>
      </div>
      
      <!-- 当前状态信息 -->
      <div class="status-info">
        <div class="status-message">
          <el-icon><InfoFilled /></el-icon>
          <span>{{ statusMessage }}</span>
        </div>
        <div v-if="lastUpdateTime" class="last-update">
          最后更新: {{ formatTime(lastUpdateTime) }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading, Minus, Plus, Close, InfoFilled } from '@element-plus/icons-vue'
import axios from 'axios'

// Props
const props = defineProps({
  taskId: {
    type: [String, Number],
    required: true
  },
  autoStart: {
    type: Boolean,
    default: true
  },
  pollInterval: {
    type: Number,
    default: 3000 // 3秒轮询间隔
  },
  reviewType: {
    type: String,
    default: 'function' // function, chain, feature
  }
})

// Emits
const emit = defineEmits(['progress-updated', 'task-completed', 'task-failed'])

// 响应式数据
const showProgress = ref(false)
const isMinimized = ref(true)  // 默认为最小化状态（悬浮球）
const overallProgress = ref(0)
const progressStatus = ref('')
const statusMessage = ref('正在获取进度信息...')
const progressDetails = ref(null)
const lastUpdateTime = ref(null)
const isPolling = ref(false)
let pollTimer = null

// 计算属性
const progressTitle = computed(() => {
  if (progressStatus.value === 'completed') return '审查已完成'
  if (progressStatus.value === 'failed') return '审查失败'
  return '代码审查进行中'
})

// 生命周期
onMounted(() => {
  if (props.autoStart) {
    startProgressTracking()
  }
})

onBeforeUnmount(() => {
  stopProgressTracking()
})

// 方法
function startProgressTracking() {
  if (!props.taskId) {
    console.warn('TaskId is required for progress tracking')
    return
  }
  
  showProgress.value = true
  isPolling.value = true
  pollProgress()
}

function stopProgressTracking() {
  isPolling.value = false
  if (pollTimer) {
    clearTimeout(pollTimer)
    pollTimer = null
  }
}

async function pollProgress() {
  if (!isPolling.value || !props.taskId) return
  
  try {
    let response
    
    // 根据审查类型选择不同的API端点
    if (props.reviewType === 'chain') {
      // 链路审查使用专用的进度API
      response = await axios.get(`/api/codeReview/regressionTest/progressive/progress/${props.taskId}`)
    } else {
      // 函数审查和其他类型使用通用进度API
      response = await axios.get(`/api/codeReview/regressionTest/task/${props.taskId}/progress`)
    }
    
    if (response.data) {
      const data = response.data
      
      // 更新进度数据
      if (props.reviewType === 'chain') {
        // 链路审查的进度格式
        overallProgress.value = data.overall_progress || 0
        progressStatus.value = getProgressStatus(data.status)
        statusMessage.value = data.message || getDefaultStatusMessage(data.status)
        
        // 构建详细进度信息
        progressDetails.value = {
          discovery_progress: data.discovery_progress,
          review_progress: data.review_progress
        }
      } else {
        // 函数审查的进度格式
        overallProgress.value = data.progress || 0
        progressStatus.value = getProgressStatus(data.status)
        statusMessage.value = data.message || getDefaultStatusMessage(data.status)
        progressDetails.value = data.details || null
      }
      
      lastUpdateTime.value = new Date()
      
      // 发出进度更新事件
      emit('progress-updated', data)
      
      // 检查任务状态
      if (data.status === 'completed') {
        isPolling.value = false
        emit('task-completed', data)
        ElMessage.success('代码审查已完成')
      } else if (data.status === 'failed') {
        isPolling.value = false
        emit('task-failed', data)
        ElMessage.error('代码审查失败')
      } else {
        // 继续轮询
        pollTimer = setTimeout(pollProgress, props.pollInterval)
      }
    }
  } catch (error) {
    console.error('获取进度失败:', error)
    
    // 如果是网络错误，继续轮询
    if (error.code === 'NETWORK_ERROR' || error.response?.status >= 500) {
      statusMessage.value = '网络连接异常，正在重试...'
      pollTimer = setTimeout(pollProgress, props.pollInterval * 2) // 延长间隔
    } else {
      // 其他错误停止轮询
      isPolling.value = false
      statusMessage.value = '获取进度失败: ' + (error.response?.data?.detail || error.message)
    }
  }
}

function getProgressStatus(status) {
  switch (status) {
    case 'completed':
      return 'success'
    case 'failed':
      return 'exception'
    case 'processing':
    case 'idle':
      return ''
    default:
      return ''
  }
}

function getDefaultStatusMessage(status) {
  switch (status) {
    case 'pending':
      return '任务准备中...'
    case 'processing':
      return '正在执行代码审查...'
    case 'idle':
      return '任务暂停中...'
    case 'completed':
      return '代码审查已完成'
    case 'failed':
      return '代码审查失败'
    default:
      return '状态未知'
  }
}

function toggleMinimize() {
  isMinimized.value = !isMinimized.value
}

function closeProgress() {
  showProgress.value = false
  stopProgressTracking()
}

function formatTime(time) {
  if (!time) return ''
  return new Date(time).toLocaleTimeString()
}

// 暴露方法给父组件
defineExpose({
  startProgressTracking,
  stopProgressTracking,
  show: () => { showProgress.value = true },
  hide: () => { showProgress.value = false },
  isTracking: () => isPolling.value
})
</script>

<style scoped>
.progress-display {
  position: fixed;
  top: 20px;
  right: 20px;
  width: 320px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  z-index: 1000;
  overflow: hidden;
  transition: all 0.3s ease;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.progress-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 14px;
}

.progress-actions {
  display: flex;
  gap: 4px;
}

.minimize-btn,
.expand-btn,
.close-btn {
  color: white !important;
  padding: 4px !important;
  min-height: auto !important;
}

.minimize-btn:hover,
.expand-btn:hover,
.close-btn:hover {
  background: rgba(255, 255, 255, 0.2) !important;
}

.progress-content {
  padding: 20px;
}

.overall-progress {
  margin-bottom: 20px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.progress-label {
  font-weight: 600;
  color: #303133;
  font-size: 14px;
}

.progress-percentage {
  font-weight: 600;
  color: #409EFF;
  font-size: 14px;
}

.progress-details {
  margin-bottom: 20px;
}

.detail-item {
  margin-bottom: 16px;
}

.detail-item:last-child {
  margin-bottom: 0;
}

.detail-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.detail-label {
  font-size: 13px;
  color: #606266;
}

.detail-percentage {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
}

.status-info {
  border-top: 1px solid #ebeef5;
  padding-top: 16px;
}

.status-message {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 13px;
  color: #606266;
}

.last-update {
  font-size: 12px;
  color: #909399;
  text-align: right;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .progress-display {
    width: 280px;
    right: 10px;
    top: 10px;
  }
  
  .progress-content {
    padding: 16px;
  }
}

/* 动画效果 */
.progress-display {
  animation: slideInRight 0.3s ease-out;
}

@keyframes slideInRight {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* 进度条自定义样式 */
:deep(.el-progress-bar__outer) {
  background-color: #f0f2f5;
  border-radius: 4px;
}

:deep(.el-progress-bar__inner) {
  border-radius: 4px;
  transition: width 0.6s ease;
}

/* 加载图标旋转动画 */
.progress-title .el-icon {
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* ============ 悬浮球样式 ============ */
.progress-ball {
  position: fixed;
  bottom: 120px;
  right: 30px;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
  cursor: pointer;
  z-index: 1000;
  overflow: hidden;
  transition: all 0.3s ease;
  animation: ballBounce 0.5s ease-out;
}

.progress-ball:hover {
  transform: scale(1.1);
  box-shadow: 0 12px 32px rgba(102, 126, 234, 0.6);
}

@keyframes ballBounce {
  0% {
    transform: scale(0);
    opacity: 0;
  }
  50% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

/* 水波效果 */
.water-wave {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  background: linear-gradient(180deg, 
    rgba(255, 255, 255, 0.3) 0%, 
    rgba(255, 255, 255, 0.5) 50%,
    rgba(255, 255, 255, 0.7) 100%
  );
  transition: height 0.6s ease;
  overflow: hidden;
}

/* 波浪动画 */
.wave {
  position: absolute;
  top: -20px;
  left: -50%;
  width: 200%;
  height: 40px;
  background: rgba(255, 255, 255, 0.4);
  border-radius: 45%;
  animation: waveMove 3s linear infinite;
}

.wave-2 {
  animation: waveMove 4s linear infinite;
  opacity: 0.6;
}

@keyframes waveMove {
  0% {
    transform: translateX(0) translateZ(0) scaleY(1);
  }
  50% {
    transform: translateX(-25%) translateZ(0) scaleY(0.8);
  }
  100% {
    transform: translateX(-50%) translateZ(0) scaleY(1);
  }
}

/* 进度数字 */
.progress-number {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 10;
  color: white;
  text-align: center;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  font-weight: bold;
}

.progress-number .number {
  font-size: 28px;
  line-height: 1;
  font-weight: 700;
}

.progress-number .percent {
  font-size: 14px;
  margin-top: -4px;
  font-weight: 600;
  opacity: 0.9;
}

/* 悬浮球关闭按钮 */
.ball-close {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 50%;
  color: white;
  font-size: 12px;
  opacity: 0;
  transition: all 0.2s ease;
  z-index: 20;
}

.progress-ball:hover .ball-close {
  opacity: 1;
}

.ball-close:hover {
  background: rgba(0, 0, 0, 0.4);
  transform: scale(1.1);
}

/* 响应式 - 悬浮球 */
@media (max-width: 768px) {
  .progress-ball {
    width: 70px;
    height: 70px;
    bottom: 100px;
    right: 20px;
  }
  
  .progress-number .number {
    font-size: 24px;
  }
  
  .progress-number .percent {
    font-size: 12px;
  }
}
</style>
