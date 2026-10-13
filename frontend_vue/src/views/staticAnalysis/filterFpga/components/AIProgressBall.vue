<template>
  <div class="ai-progress-ball" v-if="visible">
    <div class="ball-content" :class="{ expanded: isExpanded, completed: isCompleted }" @click="handleClick">
      <div class="ball-header">
        <span class="ball-title">{{ isCompleted ? '✅ 审查完成' : '🔍 AI审查进度' }}</span>
        <div class="header-icons">
          <el-icon v-if="!isExpanded && !isCompleted" class="expand-icon"><DArrowRight /></el-icon>
          <el-icon v-else-if="!isCompleted" class="expand-icon"><DArrowLeft /></el-icon>
          <el-icon class="close-icon" @click.stop="handleClose"><Close /></el-icon>
        </div>
      </div>
      
      <div v-if="isExpanded && !isCompleted" class="ball-details">
        <!-- 圆形进度指示器 -->
        <div class="progress-circle">
          <svg width="60" height="60">
            <circle
              cx="30"
              cy="30"
              r="25"
              fill="none"
              stroke="#e6e6e6"
              stroke-width="4"
            />
            <circle
              cx="30"
              cy="30"
              r="25"
              fill="none"
              :stroke="progressColor"
              stroke-width="4"
              stroke-linecap="round"
              :stroke-dasharray="circumference"
              :stroke-dashoffset="strokeDashoffset"
              transform="rotate(-90 30 30)"
              class="progress-ring"
            />
          </svg>
          <div class="progress-text">
            <div class="percentage">{{ percentage }}%</div>
            <div class="count">{{ current }}/{{ total }}</div>
          </div>
        </div>
        
        <!-- 状态文字 -->
        <div class="status-text" :style="{ color: progressColor }">
          {{ statusText }}
        </div>
      </div>
      
      <!-- 折叠状态只显示百分比 -->
      <div v-else-if="!isCompleted" class="ball-mini">
        <div class="mini-percentage" :style="{ color: progressColor }">{{ percentage }}%</div>
      </div>
      
      <!-- 审查完成状态 -->
      <div v-if="isCompleted" class="ball-completed">
        <div class="download-icon">
          <el-icon :size="16"><Download /></el-icon>
        </div>
        <div class="download-text">点击下载</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { DArrowRight, DArrowLeft, Download, Close } from '@element-plus/icons-vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: true
  },
  current: {
    type: Number,
    default: 0
  },
  total: {
    type: Number,
    default: 0
  },
  status: {
    type: String,
    default: 'pending'
  }
})

const emit = defineEmits(['download', 'close'])

const isExpanded = ref(true)

// 是否审查完成
const isCompleted = computed(() => props.status === 'completed')

const handleClick = () => {
  if (isCompleted.value) {
    // 审查完成时，点击触发下载
    emit('download')
  } else {
    // 审查中时，点击切换展开/折叠
    isExpanded.value = !isExpanded.value
  }
}

const handleClose = () => {
  emit('close')
}

// 计算百分比
const percentage = computed(() => {
  if (props.total === 0) return 0
  return Math.round((props.current / props.total) * 100)
})

// 进度条颜色
const progressColor = computed(() => {
  if (props.status === 'completed') return '#67C23A'
  if (props.status === 'error') return '#F56C6C'
  if (percentage.value < 30) return '#E6A23C'
  if (percentage.value < 70) return '#409EFF'
  return '#67C23A'
})

// 状态文字
const statusText = computed(() => {
  if (props.status === 'completed') return '✅ 审查完成'
  if (props.status === 'error') return '❌ 审查失败'
  if (props.status === 'ai_analyzing') return '🔄 AI审查中...'
  if (props.status === 'processing') return '⚙️ 处理中...'
  return '⏳ 等待中...'
})

// 圆形进度条相关计算
const radius = 25
const circumference = 2 * Math.PI * radius

const strokeDashoffset = computed(() => {
  return circumference - (percentage.value / 100) * circumference
})
</script>

<style scoped>
.ai-progress-ball {
  position: fixed;
  bottom: 80px;
  right: 30px;
  z-index: 999;
  cursor: pointer;
  user-select: none;
}

.ball-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 8px;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  transition: all 0.3s ease;
  min-width: 60px;
}

.ball-content:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.5);
}

.ball-content.expanded {
  min-width: 120px;
}

.ball-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: white;
  font-weight: 600;
  margin-bottom: 0;
}

.ball-content.expanded .ball-header {
  margin-bottom: 12px;
}

.ball-title {
  font-size: 11px;
  flex: 1;
}

.header-icons {
  display: flex;
  align-items: center;
  gap: 8px;
}

.expand-icon {
  font-size: 12px;
  transition: transform 0.3s;
}

.close-icon {
  font-size: 11px;
  opacity: 0.7;
  transition: all 0.2s;
  cursor: pointer;
}

.close-icon:hover {
  opacity: 1;
  transform: scale(1.2);
}

.ball-details {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.progress-circle {
  position: relative;
  width: 60px;
  height: 60px;
}

.progress-ring {
  transition: stroke-dashoffset 0.5s ease;
}

.progress-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: white;
}

.percentage {
  font-size: 14px;
  font-weight: bold;
  margin-bottom: 2px;
}

.count {
  font-size: 9px;
  opacity: 0.9;
}

.status-text {
  font-size: 10px;
  font-weight: 500;
  color: white;
  text-align: center;
}

.ball-mini {
  display: flex;
  align-items: center;
  justify-content: center;
}

.mini-percentage {
  font-size: 12px;
  font-weight: bold;
  color: white;
}

/* 审查完成状态样式 */
.ball-content.completed {
  background: linear-gradient(135deg, #67C23A 0%, #85ce61 100%);
  min-width: 110px;
  cursor: pointer;
}

.ball-content.completed:hover {
  background: linear-gradient(135deg, #85ce61 0%, #95d475 100%);
  transform: translateY(-4px) scale(1.02);
  box-shadow: 0 12px 32px rgba(103, 194, 58, 0.5);
}

.ball-completed {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 4px 0;
}

.download-icon {
  color: white;
  animation: bounce 2s infinite;
}

.download-text {
  color: white;
  font-size: 11px;
  font-weight: bold;
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-8px);
  }
}
</style>
