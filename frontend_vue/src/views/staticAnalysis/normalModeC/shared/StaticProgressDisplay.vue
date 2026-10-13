<template>
  <!-- 折叠状态：圆形悬浮球 -->
  <div
    v-if="showProgress && isMinimized"
    class="progress-ball"
    :class="{ 'is-completed': isCompleted }"
    @click="handleBallClick"
    :title="ballTitle"
  >
    <!-- 进行中：水波上涨效果 -->
    <template v-if="!isCompleted">
      <div class="water-wave" :style="{ height: overallProgress + '%' }">
        <div class="wave"></div>
        <div class="wave wave-2"></div>
      </div>
      <!-- 进度数字 -->
      <div class="progress-number">
        <div class="number">{{ overallProgress }}</div>
        <div class="percent">%</div>
      </div>
    </template>
    
    <!-- 完成后：下载图标 -->
    <template v-else>
      <div class="download-icon">
        <el-icon><Download /></el-icon>
      </div>
      <div class="download-text">下载</div>
    </template>
    
    <!-- 关闭按钮 -->
    <div class="ball-close" @click.stop="closeProgress">
      <el-icon><Close /></el-icon>
    </div>
  </div>

  <!-- 展开状态：完整进度面板 -->
  <div class="progress-display" v-if="showProgress && !isMinimized">
    <div class="progress-header">
      <h3>
        <el-icon><TrendCharts /></el-icon>
        静态分析进度
      </h3>
      <div class="header-actions">
        <el-button @click="toggleMinimize" link :icon="Minus" title="最小化">最小化</el-button>
        <el-button @click="closeProgress" link :icon="Close" title="关闭">关闭</el-button>
      </div>
    </div>

    <!-- GJB进度 (仅在gjb或mixed视图显示) -->
    <div class="progress-section" v-if="ruleType === 'gjb' || ruleType === 'mixed'">
      <div class="section-header">
        <span class="section-title">
          <el-icon><Document /></el-icon>
          GJB8114规则
        </span>
        <span class="section-percentage">{{ gjbData.percentage }}%</span>
      </div>
      <el-progress 
        :percentage="gjbData.percentage" 
        :status="gjbData.status"
        :stroke-width="12"
      >
        <span class="progress-text">{{ gjbData.statusText }}</span>
      </el-progress>
      <div class="section-details" v-if="gjbData.current > 0">
        <span>已分析: {{ gjbData.current }} / {{ gjbData.total }}</span>
      </div>
    </div>

    <!-- CWE进度 (仅在cwe或mixed视图显示) -->
    <div class="progress-section" v-if="ruleType === 'cwe' || ruleType === 'mixed'">
      <div class="section-header">
        <span class="section-title">
          <el-icon><Document /></el-icon>
          CWE规则
        </span>
        <span class="section-percentage">{{ cweData.percentage }}%</span>
      </div>
      <el-progress 
        :percentage="cweData.percentage" 
        :status="cweData.status"
        :stroke-width="12"
      >
        <span class="progress-text">{{ cweData.statusText }}</span>
      </el-progress>
      <div class="section-details" v-if="cweData.current > 0">
        <span>已分析: {{ cweData.current }} / {{ cweData.total }}</span>
      </div>
    </div>

    <!-- 综合进度 (仅在mixed视图显示，单一视图直接显示当前规则进度) -->
    <div class="overall-section" v-if="ruleType === 'mixed'">
      <div class="overall-header">
        <span class="overall-title">综合进度</span>
        <span class="overall-percentage">{{ overallProgress }}%</span>
      </div>
      <el-progress 
        :percentage="overallProgress" 
        :status="overallStatus"
        :stroke-width="14"
        color="#667eea"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Close, Minus, TrendCharts, Document, Download } from '@element-plus/icons-vue'

const props = defineProps({
  gjbData: {
    type: Object,
    required: true
  },
  cweData: {
    type: Object,
    required: true
  },
  visible: {
    type: Boolean,
    default: false
  },
  ruleType: {
    type: String,
    default: 'mixed' // 'gjb', 'cwe', 'mixed'
  }
})

const emit = defineEmits(['close', 'download'])

const showProgress = ref(props.visible)
const isMinimized = ref(false)

// 监听 visible 变化
watch(() => props.visible, (newVal) => {
  console.log('[进度组件] visible 变化:', newVal)
  showProgress.value = newVal
  if (newVal) {
    // 进度显示时默认最小化为悬浮球
    isMinimized.value = true
    console.log('[进度组件] 显示为悬浮球')
  }
}, { immediate: true })

// 监听数据变化
watch(() => [props.gjbData, props.cweData], ([gjb, cwe]) => {
  console.log('[进度组件] 数据变化 - GJB:', gjb, 'CWE:', cwe)
}, { deep: true })

// 综合进度计算（根据规则类型）
const overallProgress = computed(() => {
  // 如果是GJB视图，只显示GJB进度
  if (props.ruleType === 'gjb') {
    return props.gjbData.percentage || 0
  }
  
  // 如果是CWE视图，只显示CWE进度
  if (props.ruleType === 'cwe') {
    return props.cweData.percentage || 0
  }
  
  // 混合视图，按实际问题数量加权平均
  const gjbWeight = props.gjbData.total || 0
  const cweWeight = props.cweData.total || 0
  const totalWeight = gjbWeight + cweWeight
  
  if (totalWeight === 0) {
    // 如果没有总数，按50:50权重
    return Math.round((props.gjbData.percentage + props.cweData.percentage) / 2)
  }
  
  // 按实际问题数量加权平均
  const gjbPortion = (props.gjbData.percentage * gjbWeight) / totalWeight
  const cwePortion = (props.cweData.percentage * cweWeight) / totalWeight
  
  return Math.round(gjbPortion + cwePortion)
})

// 综合状态
const overallStatus = computed(() => {
  if (overallProgress.value === 100) {
    return 'success'
  }
  return ''
})

// 是否完成
const isCompleted = computed(() => {
  return overallProgress.value === 100
})

// 悬浮球标题
const ballTitle = computed(() => {
  if (isCompleted.value) {
    return '✅ 分析完成，点击下载结果'
  }
  return `🔄 分析中... ${overallProgress.value}%，点击展开详情`
})

// 处理悬浮球点击
function handleBallClick() {
  if (isCompleted.value) {
    // 完成后点击触发下载
    emit('download')
  } else {
    // 进行中点击展开详情
    toggleMinimize()
  }
}

// 切换最小化
function toggleMinimize() {
  isMinimized.value = !isMinimized.value
}

// 关闭进度显示
function closeProgress() {
  showProgress.value = false
  emit('close')
}
</script>

<style scoped>
/* ==================== 悬浮球样式 ==================== */
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
  transform: scale(1.05);
  box-shadow: 0 12px 32px rgba(102, 126, 234, 0.5);
}

/* 完成状态的悬浮球 */
.progress-ball.is-completed {
  background: linear-gradient(135deg, #52c41a 0%, #73d13d 100%);
  box-shadow: 0 8px 24px rgba(82, 196, 26, 0.4);
  cursor: pointer;
}

.progress-ball.is-completed:hover {
  background: linear-gradient(135deg, #73d13d 0%, #95de64 100%);
  box-shadow: 0 12px 32px rgba(82, 196, 26, 0.6);
}

/* 下载图标 */
.download-icon {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -60%);
  z-index: 2;
}

.download-icon .el-icon {
  font-size: 32px;
  color: white;
  animation: downloadPulse 2s ease-in-out infinite;
}

@keyframes downloadPulse {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-5px);
  }
}

.download-text {
  position: absolute;
  bottom: 18px;
  left: 50%;
  transform: translateX(-50%);
  color: white;
  font-size: 12px;
  font-weight: 600;
  z-index: 2;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

@keyframes ballBounce {
  0% {
    transform: scale(0.3) translateY(100px);
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
  right: 0;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.3) 0%, rgba(255, 255, 255, 0.6) 100%);
  transition: height 0.6s ease;
  overflow: hidden;
}

.wave {
  position: absolute;
  top: -10px;
  left: -50%;
  width: 200%;
  height: 20px;
  background: radial-gradient(ellipse at center, rgba(255, 255, 255, 0.5) 0%, transparent 70%);
  animation: waveMove 3s linear infinite;
}

.wave-2 {
  animation-delay: -1.5s;
  animation-duration: 4s;
}

@keyframes waveMove {
  0% {
    transform: translateX(0) translateY(0);
  }
  50% {
    transform: translateX(25%) translateY(-5px);
  }
  100% {
    transform: translateX(50%) translateY(0);
  }
}

/* 进度数字 */
.progress-number {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: baseline;
  gap: 2px;
  color: white;
  font-weight: 700;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  z-index: 2;
}

.progress-number .number {
  font-size: 24px;
  line-height: 1;
}

.progress-number .percent {
  font-size: 14px;
  line-height: 1;
}

/* 球上的关闭按钮 */
.ball-close {
  position: absolute;
  top: 5px;
  right: 5px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: all 0.2s ease;
  z-index: 3;
}

.progress-ball:hover .ball-close {
  opacity: 1;
}

.ball-close:hover {
  background: rgba(255, 255, 255, 0.5);
  transform: scale(1.1);
}

.ball-close .el-icon {
  font-size: 12px;
  color: white;
}

/* ==================== 完整面板样式 ==================== */
.progress-display {
  position: fixed;
  bottom: 30px;
  right: 30px;
  width: 380px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  overflow: hidden;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.progress-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.header-actions .el-button {
  color: white;
}

.header-actions .el-button:hover {
  color: rgba(255, 255, 255, 0.8);
}

/* 进度区域 */
.progress-section {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  display: flex;
  align-items: center;
  gap: 6px;
}

.section-title .el-icon {
  color: #409EFF;
}

.section-percentage {
  font-size: 16px;
  font-weight: 700;
  color: #667eea;
}

.section-details {
  margin-top: 8px;
  font-size: 13px;
  color: #666;
}

.progress-text {
  font-size: 12px;
  color: #666;
  margin-left: 8px;
}

/* 综合进度区域 */
.overall-section {
  padding: 16px 20px;
  background: linear-gradient(135deg, #f8fafc 0%, #e8f0fe 100%);
}

.overall-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.overall-title {
  font-size: 15px;
  font-weight: 700;
  color: #1a202c;
}

.overall-percentage {
  font-size: 18px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* 进度条样式优化 */
.progress-section :deep(.el-progress-bar__outer) {
  background-color: #e8e8e8;
}

.progress-section :deep(.el-progress-bar__inner) {
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
}

.overall-section :deep(.el-progress-bar__outer) {
  background-color: #e0e7ff;
}

.overall-section :deep(.el-progress-bar__inner) {
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
}

/* 响应式 */
@media (max-width: 768px) {
  .progress-display {
    width: calc(100% - 40px);
    right: 20px;
    bottom: 20px;
  }
  
  .progress-ball {
    right: 20px;
    bottom: 100px;
  }
}
</style>

