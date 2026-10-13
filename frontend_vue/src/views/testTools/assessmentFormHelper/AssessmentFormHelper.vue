<template>
  <div class="assessment-form-helper">
    <div class="tool-header">
      <h1>充分性要求、通过准则列生成工具</h1>
      <p>根据表单中已有的内容，自动生成充分性要求列和通过准则列</p>
    </div>

    <!-- 上传区域 -->
    <div v-if="!processing && !completed" class="upload-section">
      <el-upload
        ref="uploadRef"
        class="upload-demo"
        drag
        :auto-upload="false"
        :on-change="handleFileChange"
        :before-upload="beforeUpload"
        accept=".xls,.xlsx"
        :limit="1"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          将Excel文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            只能上传 .xls/.xlsx 文件，且不超过 50MB
          </div>
        </template>
      </el-upload>

      <div class="upload-actions">
        <el-button 
          type="primary" 
          :disabled="!selectedFile" 
          @click="uploadFile"
        >
          开始处理
        </el-button>
      </div>
    </div>

    <!-- 进度显示区域 -->
    <div v-if="processing" class="progress-section">
      <h3>AI正在处理中...</h3>
      <el-progress 
        :percentage="progressPercentage" 
        :stroke-width="8"
      >
        <span>{{ completedItems }}/{{ totalItems }}</span>
      </el-progress>
    </div>

    <!-- 结果区域 -->
    <div v-if="completed" class="result-section">
      <div class="success-message">
        <el-icon class="success-icon"><Check /></el-icon>
        <h3>处理完成！</h3>
        <p>AI已成功生成充分性要求和通过准则</p>
      </div>
      
      <div class="download-section">
        <el-button 
          type="primary" 
          size="large"
          :loading="downloading"
          @click="downloadResult"
        >
          <el-icon><Download /></el-icon>
          下载结果
        </el-button>
      </div>
      
      <div class="restart-section">
        <el-button @click="resetForm">重新开始</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, Check, Download } from '@element-plus/icons-vue'
import assessmentFormService from '../../../services/assessmentFormService'

// 响应式数据
const uploadRef = ref()
const selectedFile = ref(null)
const processing = ref(false)
const completed = ref(false)
const downloading = ref(false)
const sessionId = ref('')
const totalItems = ref(0)
const completedItems = ref(0)

let pollInterval = null

// 计算属性
const progressPercentage = computed(() => {
  if (totalItems.value === 0) return 0
  return Math.round((completedItems.value / totalItems.value) * 100)
})

// 方法
const handleFileChange = (file) => {
  selectedFile.value = file
}

const beforeUpload = (file) => {
  const isExcel = file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' || 
                  file.type === 'application/vnd.ms-excel'
  const isLt50M = file.size / 1024 / 1024 < 50

  if (!isExcel) {
    ElMessage.error('只能上传 Excel 文件!')
    return false
  }
  if (!isLt50M) {
    ElMessage.error('文件大小不能超过 50MB!')
    return false
  }
  return false // 阻止自动上传
}

const uploadFile = async () => {
  if (!selectedFile.value) {
    ElMessage.error('请先选择文件')
    return
  }

  try {
    processing.value = true
    
    const response = await assessmentFormService.uploadFile(selectedFile.value.raw)
    
    if (!response) {
      throw new Error('服务器无响应')
    }
    
    if (response.success) {
      sessionId.value = response.session_id
      ElMessage.success('文件上传成功，正在处理中...')
      
      // 立即检查一次状态
      try {
        const statusResponse = await assessmentFormService.getSessionStatus(sessionId.value)
        
        if (statusResponse && statusResponse.success) {
          totalItems.value = statusResponse.total_items || 0
          completedItems.value = statusResponse.completed_items || 0
          
          if (statusResponse.status === 'completed') {
            processing.value = false
            completed.value = true
            ElMessage.success('处理完成！')
            return
          }
        }
      } catch (error) {
        // 初始状态检查失败，继续轮询
      }
      
      // 开始轮询状态
      startStatusPolling()
    } else {
      throw new Error(response.error || response.message || '上传失败')
    }
  } catch (error) {
    console.error('上传失败:', error)
    
    let errorMessage = '上传失败'
    if (error.message) {
      errorMessage += ': ' + error.message
    }
    
    ElMessage.error(errorMessage)
    processing.value = false
  }
}

const startStatusPolling = () => {
  // 立即查询一次
  checkStatus()
  
  // 设置定时器，每5秒查询一次
  pollInterval = setInterval(() => {
    // 检查是否已经完成，如果完成则停止轮询
    if (completed.value || !processing.value) {
      clearInterval(pollInterval)
      pollInterval = null
      return
    }
    
    checkStatus()
  }, 5000) // 每5秒轮询一次
}

const checkStatus = async () => {
  if (!sessionId.value) {
    return
  }

  try {
    const response = await assessmentFormService.getSessionStatus(sessionId.value)
    
    if (!response) {
      return
    }
    
    if (response.success) {
      // 更新状态
      totalItems.value = response.total_items || 0
      completedItems.value = response.completed_items || 0
      
      // 检查是否完成
      if (response.status === 'completed') {
        processing.value = false
        completed.value = true
        
        // 停止轮询
        if (pollInterval) {
          clearInterval(pollInterval)
          pollInterval = null
        }
        
        ElMessage.success('处理完成！')
      }
    }
  } catch (error) {
    // 单次查询失败不影响轮询继续
  }
}

const downloadResult = async () => {
  try {
    downloading.value = true
    
    // 生成文件
    const generateResponse = await assessmentFormService.generateOutputFile(sessionId.value)
    
    if (!generateResponse.success) {
      throw new Error(generateResponse.error || '生成文件失败')
    }
    
    // 下载文件
    await assessmentFormService.downloadFile(sessionId.value, generateResponse.filename)
    
    ElMessage.success('文件已下载')
    
  } catch (error) {
    ElMessage.error('下载失败: ' + error.message)
  } finally {
    downloading.value = false
  }
}

const resetForm = () => {
  // 清理状态
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
  
  selectedFile.value = null
  processing.value = false
  completed.value = false
  downloading.value = false
  sessionId.value = ''
  totalItems.value = 0
  completedItems.value = 0
  
  // 清理上传组件
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

// 组件卸载时清理
onUnmounted(() => {
  if (pollInterval) {
    clearInterval(pollInterval)
  }
})
</script>

<style scoped>
.assessment-form-helper {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

.tool-header {
  text-align: center;
  margin-bottom: 30px;
}

.tool-header h1 {
  color: #2c3e50;
  margin-bottom: 10px;
}

.tool-header p {
  color: #7f8c8d;
  font-size: 14px;
}

.upload-section {
  margin-bottom: 30px;
}

.upload-actions {
  text-align: center;
  margin-top: 20px;
}

.progress-section {
  text-align: center;
  padding: 40px 20px;
}

.progress-section h3 {
  color: #2c3e50;
  margin-bottom: 20px;
}

.result-section {
  margin-top: 30px;
}

.success-message {
  text-align: center;
  padding: 40px 20px;
  background-color: #e8f5e9; /* Light green background */
  border-radius: 8px;
  margin-bottom: 20px;
}

.success-message h3 {
  color: #2e7d32; /* Dark green text */
  margin-bottom: 10px;
}

.success-message p {
  color: #616161;
  font-size: 14px;
}

.success-icon {
  font-size: 60px;
  color: #4caf50; /* Green color for icon */
  margin-bottom: 15px;
}

.download-section {
  text-align: center;
  margin-bottom: 20px;
}

.restart-section {
  text-align: center;
}
</style> 