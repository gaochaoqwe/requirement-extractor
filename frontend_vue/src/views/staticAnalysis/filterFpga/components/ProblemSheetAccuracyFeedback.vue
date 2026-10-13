<template>
  <el-dialog
    v-model="dialogVisible"
    title="问题单准确率反馈"
    width="500px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :show-close="false"
    center
    class="problem-sheet-accuracy-dialog"
  >
    <div class="feedback-content">
      <div class="feedback-icon">
        <el-icon :size="60" color="#409EFF">
          <ChatDotRound />
        </el-icon>
      </div>
      
      <div class="feedback-title">
        您已查看超过{{ triggerPoint }}的问题
      </div>
      
      <div class="feedback-description">
        请问生成的问题单准确率如何？您的反馈将帮助我们改进服务质量
        <span v-if="delayedCount > 0" class="delayed-hint">
          （第{{ delayedCount + 1 }}次提醒）
        </span>
      </div>
      
      <div class="feedback-options">
        <el-radio-group v-model="selectedRate" size="large">
          <el-radio-button 
            v-for="option in rateOptions" 
            :key="option.value" 
            :label="option.value"
            class="rate-option"
          >
            <div class="option-content">
              <span class="option-label">{{ option.label }}</span>
              <el-icon class="option-icon" :color="option.color">
                <component :is="option.icon" />
              </el-icon>
            </div>
          </el-radio-button>
        </el-radio-group>
      </div>
      
      <div class="feedback-stats">
        <el-text type="info" size="small">
          已查看 {{ viewedCount }} / {{ totalProblems }} 个问题 ({{ viewPercentage }}%)
        </el-text>
      </div>
    </div>
    
    <template #footer>
      <div class="dialog-footer">
        <el-button 
          v-if="canDelay"
          @click="handleDelay" 
          size="large"
          :loading="delaying"
        >
          稍后反馈
        </el-button>
        <el-button 
          type="primary" 
          @click="handleSubmit" 
          :loading="submitting"
          :disabled="!selectedRate"
          size="large"
        >
          提交反馈
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ChatDotRound, CircleCheck, WarningFilled, CircleClose } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

// Props
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  taskId: {
    type: [Number, String],
    required: true
  },
  viewedCount: {
    type: Number,
    default: 0
  },
  totalProblems: {
    type: Number,
    default: 0
  },
  triggerPoint: {
    type: String,
    default: '50%'
  },
  delayedCount: {
    type: Number,
    default: 0
  }
})

// Emits
const emit = defineEmits(['update:visible', 'submitted', 'delayed'])

// 响应式数据
const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

const selectedRate = ref('')
const submitting = ref(false)
const delaying = ref(false)

// 准确率选项
const rateOptions = [
  { 
    value: '50%以下', 
    label: '50%以下', 
    icon: CircleClose,
    color: '#F56C6C'
  },
  { 
    value: '50%-70%', 
    label: '50%-70%', 
    icon: WarningFilled,
    color: '#E6A23C'
  },
  { 
    value: '70%-85%', 
    label: '70%-85%', 
    icon: WarningFilled,
    color: '#E6A23C'
  },
  { 
    value: '85%-95%', 
    label: '85%-95%', 
    icon: CircleCheck,
    color: '#67C23A'
  },
  { 
    value: '95%-100%', 
    label: '95%-100%', 
    icon: CircleCheck,
    color: '#67C23A'
  }
]

// 计算查看百分比
const viewPercentage = computed(() => {
  if (props.totalProblems === 0) return 0
  return Math.round((props.viewedCount / props.totalProblems) * 100)
})

// 是否可以延迟（最多延迟2次）
const canDelay = computed(() => {
  return props.delayedCount < 2
})

// 提交反馈
async function handleSubmit() {
  if (!selectedRate.value) {
    ElMessage.warning('请选择准确率区间')
    return
  }
  
  submitting.value = true
  
  try {
    const response = await axios.post(
      `/api/staticAnalysis/filterFpga/${props.taskId}/problem_sheet_accuracy_feedback`,
      {
        accuracy_rate: selectedRate.value
      }
    )
    
    if (response.data.success) {
      ElMessage.success(response.data.message || '感谢您的反馈！')
      emit('submitted', selectedRate.value)
      dialogVisible.value = false
    } else {
      ElMessage.error(response.data.message || '提交失败')
    }
  } catch (error) {
    console.error('提交反馈失败:', error)
    ElMessage.error('提交失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    submitting.value = false
  }
}

// 延迟反馈 - 使用本地存储记录
async function handleDelay() {
  delaying.value = true
  
  try {
    // 记录延迟次数到localStorage
    const key = `problem_sheet_feedback_delayed_${props.taskId}`
    const currentDelayed = parseInt(localStorage.getItem(key) || '0')
    localStorage.setItem(key, String(currentDelayed + 1))
    
    const nextTrigger = props.delayedCount === 0 ? '80%' : '100%'
    ElMessage.info(`已延迟反馈，将在查看${nextTrigger}问题时再次提醒`)
    
    emit('delayed', { delayedCount: currentDelayed + 1 })
    dialogVisible.value = false
  } catch (error) {
    console.error('延迟反馈失败:', error)
    ElMessage.error('操作失败')
  } finally {
    delaying.value = false
  }
}
</script>

<style scoped>
.problem-sheet-accuracy-dialog {
  border-radius: 16px;
}

.problem-sheet-accuracy-dialog :deep(.el-dialog__header) {
  padding: 24px 24px 16px;
  text-align: center;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.problem-sheet-accuracy-dialog :deep(.el-dialog__body) {
  padding: 16px 24px 24px;
}

.feedback-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.feedback-icon {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
}

.feedback-icon .el-icon {
  color: white !important;
}

.feedback-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  text-align: center;
}

.feedback-description {
  font-size: 14px;
  color: #606266;
  text-align: center;
  line-height: 1.6;
  max-width: 400px;
}

.delayed-hint {
  color: #E6A23C;
  font-weight: 500;
}

.feedback-options {
  width: 100%;
  margin-top: 10px;
}

.feedback-options :deep(.el-radio-group) {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

.feedback-options :deep(.el-radio-button) {
  width: 100%;
}

.feedback-options :deep(.el-radio-button__inner) {
  width: 100%;
  padding: 16px 20px;
  border-radius: 12px;
  border: 2px solid #DCDFE6;
  background: #fff;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.feedback-options :deep(.el-radio-button__inner:hover) {
  border-color: #409EFF;
  background: #f0f7ff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.2);
}

.feedback-options :deep(.el-radio-button.is-active .el-radio-button__inner) {
  border-color: #409EFF;
  background: linear-gradient(135deg, #e6f4ff 0%, #f0f7ff 100%);
  color: #409EFF;
  font-weight: 600;
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.3);
}

.option-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.option-label {
  font-size: 15px;
  font-weight: 500;
}

.option-icon {
  font-size: 20px;
  transition: transform 0.3s ease;
}

.feedback-options :deep(.el-radio-button.is-active) .option-icon {
  transform: scale(1.2);
}

.feedback-stats {
  margin-top: 10px;
  padding: 12px 20px;
  background: #f5f7fa;
  border-radius: 8px;
  width: 100%;
  text-align: center;
}

.dialog-footer {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding-top: 8px;
}

.dialog-footer .el-button {
  min-width: 120px;
  border-radius: 8px;
  font-weight: 500;
}

/* 动画效果 */
.problem-sheet-accuracy-dialog :deep(.el-dialog) {
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
