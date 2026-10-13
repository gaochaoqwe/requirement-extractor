<template>
  <div class="test-case-reverse-container">
    <div class="header">
      <h1>测试用例反向推导工具</h1>
      <p class="description">根据测试用例反向推导测试内容和测试方法</p>
    </div>

    <div class="main-content">
      <!-- 模式切换区域 -->
      <div class="mode-switch-section" v-if="!sessionId">
        <div class="mode-switch-card">
          <h3>选择处理模式</h3>
          <div class="mode-options">
            <div 
              class="mode-option" 
              :class="{ active: processingMode === 'normal' }"
              @click="processingMode = 'normal'"
            >
              <div class="mode-icon">📝</div>
              <div class="mode-info">
                <h4>普通模式</h4>
                <p>生成测试内容和测试方法</p>
              </div>
            </div>
            <div 
              class="mode-option" 
              :class="{ active: processingMode === 'template' }"
              @click="processingMode = 'template'"
            >
              <div class="mode-icon">📋</div>
              <div class="mode-info">
                <h4>用例模板模式</h4>
                <p>生成测试内容、测试方法和用例模板</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 上传区域 -->
      <div class="upload-section" v-if="!sessionId">
        <div class="upload-card">
          <div class="upload-header">
            <h3>上传测试用例Excel文件</h3>
            <p>支持格式：.xlsx, .xls</p>
            <div class="current-mode">
              当前模式: <span class="mode-badge" :class="processingMode">
                {{ processingMode === 'normal' ? '普通模式' : '用例模板模式' }}
              </span>
            </div>
          </div>
          
          <div class="upload-area" @click="triggerFileInput" @dragover.prevent @drop.prevent="handleDrop">
            <input 
              ref="fileInput" 
              type="file" 
              accept=".xlsx,.xls" 
              @change="handleFileSelect" 
              style="display: none"
            >
            <div class="upload-icon">📄</div>
            <p>点击选择文件或拖拽文件到此处</p>
            <p class="upload-hint">请确保Excel文件包含"测试用例单"工作表</p>
            <p v-if="selectedFile" class="selected-file">已选择: {{ selectedFile.name }}</p>
          </div>
          
          <button 
            class="upload-btn" 
            @click="uploadFile" 
            :disabled="!selectedFile || uploading"
          >
            {{ uploading ? '上传中...' : '开始处理' }}
          </button>
        </div>
      </div>

      <!-- 处理状态区域 -->
      <div class="processing-section" v-if="sessionId">
        <div class="status-card">
          <div class="status-header">
            <h3>处理状态</h3>
            <div class="status-info">
              <div class="status-badge" :class="statusClass">{{ statusText }}</div>
              <div class="mode-badge" :class="currentProcessingMode" v-if="currentProcessingMode">
                {{ currentProcessingMode === 'normal' ? '普通模式' : '用例模板模式' }}
              </div>
            </div>
          </div>
          
          <div class="progress-info">
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: progress + '%' }"></div>
            </div>
            <p class="progress-text">{{ progressText }}</p>
            <div class="retry-info" v-if="retryCount > 0">
              <p class="retry-text">⚠️ 部分项目已重试 {{ retryCount }} 次</p>
            </div>
          </div>
          
          <div class="file-info">
            <p><strong>文件名：</strong>{{ originalFilename }}</p>
          </div>
          
          <!-- 下载按钮 -->
          <div class="download-section" v-if="status === 'completed'">
            <div class="completion-info">
              <p v-if="completedItems > 0" class="success-info">
                ✅ 成功处理 {{ completedItems }} 个测试项
              </p>
              <p v-if="errorItems > 0" class="error-info">
                ❌ {{ errorItems }} 个测试项处理失败（不影响文件下载）
              </p>
            </div>
            <button class="download-btn" @click="downloadResult">
              <span class="download-icon">⬇️</span>
              下载结果文件
            </button>
          </div>
        </div>
      </div>

      <!-- 错误信息 -->
      <div class="error-section" v-if="error">
        <div class="error-card">
          <h3>❌ 处理失败</h3>
          <p>{{ error }}</p>
          <div class="error-actions">
            <button class="retry-btn" @click="restart">重新开始</button>
            <button class="change-mode-btn" @click="changeMode">切换模式重试</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import testCaseReverseService from '@/services/testCaseReverseService'
import { performanceMonitor } from '@/utils/performance'

export default {
  name: 'TestCaseReverse',
  setup() {
    // 响应式数据
    const selectedFile = ref(null)
    const uploading = ref(false)
    const sessionId = ref('')
    const status = ref('')
    const progress = ref(0)
    const originalFilename = ref('')
    const error = ref('')
    const pollingInterval = ref(null)
    const fileInput = ref(null)
    const processingMode = ref('normal') // 处理模式
    const currentProcessingMode = ref('') // 当前会话的处理模式
    const retryCount = ref(0)
    const completedItems = ref(0)
    const errorItems = ref(0)

    // 计算属性
    const statusClass = computed(() => {
      switch (status.value) {
        case 'processing': return 'status-processing'
        case 'completed': return 'status-completed'
        case 'error': return 'status-error'
        default: return 'status-pending'
      }
    })

    const statusText = computed(() => {
      switch (status.value) {
        case 'processing': return '处理中'
        case 'completed': return '已完成'
        case 'error': return '处理失败'
        default: return '等待处理'
      }
    })

    const progressText = computed(() => {
      if (status.value === 'completed') {
        return `反向推导完成 - 成功: ${completedItems.value}, 失败: ${errorItems.value}`
      } else if (status.value === 'processing') {
        return `正在进行反向推导... ${progress.value.toFixed(1)}%`
      } else {
        return '等待开始处理'
      }
    })

    // 文件选择相关方法
    const triggerFileInput = () => {
      console.log('触发文件选择')
      if (fileInput.value) {
        fileInput.value.click()
      } else {
        console.error('fileInput ref 未找到')
      }
    }

    const handleFileSelect = (event) => {
      console.log('文件选择事件触发')
      const file = event.target.files[0]
      if (file) {
        console.log('选择的文件:', file.name)
        selectedFile.value = file
        error.value = '' // 清除之前的错误
      }
    }

    const handleDrop = (event) => {
      console.log('拖拽文件事件触发')
      const files = event.dataTransfer.files
      if (files.length > 0) {
        console.log('拖拽的文件:', files[0].name)
        selectedFile.value = files[0]
        error.value = '' // 清除之前的错误
      }
    }

    // 上传文件
    const uploadFile = async () => {
      console.log('开始上传文件')
      
      if (!selectedFile.value) {
        error.value = '请选择文件'
        console.error('没有选择文件')
        return
      }

      try {
        uploading.value = true
        error.value = ''
        
        // 开始性能监控
        performanceMonitor.mark('testCaseReverse-upload')
        
        console.log('调用上传服务，文件:', selectedFile.value.name, '模式:', processingMode.value)
        const response = await testCaseReverseService.uploadFile(selectedFile.value, processingMode.value)
        console.log('上传响应:', response)
        
        if (response.success) {
          sessionId.value = response.session_id
          status.value = 'processing'
          originalFilename.value = selectedFile.value.name
          currentProcessingMode.value = response.processing_mode || processingMode.value
          
          console.log('上传成功，会话ID:', response.session_id, '处理模式:', currentProcessingMode.value)
          
          // 开始轮询状态
          startStatusPolling()
          
          // 结束性能监控
          performanceMonitor.measure('testCaseReverse-upload')
        } else {
          error.value = response.error || '上传失败'
          console.error('上传失败:', response.error)
        }
      } catch (err) {
        error.value = '上传文件时出错: ' + err.message
        console.error('上传异常:', err)
      } finally {
        uploading.value = false
      }
    }

    // 状态轮询
    const startStatusPolling = () => {
      if (pollingInterval.value) {
        clearInterval(pollingInterval.value)
      }
      
      pollingInterval.value = setInterval(async () => {
        try {
          const response = await testCaseReverseService.getSessionStatus(sessionId.value)
          
          if (response.success) {
            status.value = response.status
            progress.value = response.progress || 0
            completedItems.value = response.completed_items || 0
            errorItems.value = response.error_items || 0
            
            // 更新当前处理模式
            if (response.processing_mode) {
              currentProcessingMode.value = response.processing_mode
            }
            
            // 更新重试信息
            if (response.total_items && response.completed_items) {
              const totalRetries = response.total_items * 3 - response.completed_items * 3
              retryCount.value = Math.max(0, totalRetries)
            }
            
            if (response.status === 'completed' || response.status === 'error') {
              clearInterval(pollingInterval.value)
              pollingInterval.value = null
              
              if (response.status === 'error') {
                error.value = response.error_message || '处理失败'
              }
            }
          } else {
            console.error('获取状态失败:', response.error)
          }
        } catch (err) {
          console.error('轮询状态时出错:', err)
        }
      }, 2000) // 每2秒轮询一次
    }

    // 下载结果
    const downloadResult = async () => {
      try {
        const url = `${window.location.origin}/api/test-tools/test-case-reverse/download/${sessionId.value}`
        
        // 创建一个临时的a标签来触发下载
        const link = document.createElement('a')
        link.href = url
        link.download = `test_case_reverse_result_${sessionId.value}.xlsx`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
      } catch (err) {
        error.value = '下载失败: ' + err.message
      }
    }

    // 重新开始
    const restart = () => {
      selectedFile.value = null
      sessionId.value = ''
      status.value = ''
      progress.value = 0
      originalFilename.value = ''
      error.value = ''
      uploading.value = false
      currentProcessingMode.value = ''
      retryCount.value = 0
      completedItems.value = 0
      errorItems.value = 0
      
      if (pollingInterval.value) {
        clearInterval(pollingInterval.value)
        pollingInterval.value = null
      }
    }

    // 切换模式重试
    const changeMode = () => {
      processingMode.value = processingMode.value === 'normal' ? 'template' : 'normal'
      restart()
    }

    // 生命周期
    onMounted(() => {
      console.log('TestCaseReverse 组件已挂载')
    })

    onUnmounted(() => {
      if (pollingInterval.value) {
        clearInterval(pollingInterval.value)
      }
    })

    return {
      selectedFile,
      uploading,
      sessionId,
      status,
      progress,
      originalFilename,
      error,
      fileInput,
      processingMode,
      currentProcessingMode,
      retryCount,
      completedItems,
      errorItems,
      statusClass,
      statusText,
      progressText,
      triggerFileInput,
      handleFileSelect,
      handleDrop,
      uploadFile,
      downloadResult,
      restart,
      changeMode
    }
  }
}
</script>

<style scoped>
.test-case-reverse-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.header {
  text-align: center;
  margin-bottom: 32px;
}

.header h1 {
  font-size: 2rem;
  color: #1f2937;
  margin-bottom: 8px;
}

.description {
  color: #6b7280;
  font-size: 1.1rem;
}

.main-content {
  width: 100%;
  max-width: 600px;
}

.mode-switch-section, .upload-section, .processing-section, .error-section {
  margin-bottom: 24px;
}

.mode-switch-card, .upload-card, .status-card, .error-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
}

.mode-switch-card h3 {
  font-size: 1.25rem;
  color: #1f2937;
  margin-bottom: 16px;
  text-align: center;
}

.mode-options {
  display: flex;
  gap: 16px;
}

.mode-option {
  flex: 1;
  padding: 16px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: center;
}

.mode-option:hover {
  border-color: #8b5cf6;
  background-color: #f9fafb;
}

.mode-option.active {
  border-color: #8b5cf6;
  background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
}

.mode-icon {
  font-size: 2rem;
  margin-bottom: 8px;
}

.mode-info h4 {
  font-size: 1rem;
  color: #1f2937;
  margin-bottom: 4px;
}

.mode-info p {
  font-size: 0.875rem;
  color: #6b7280;
}

.upload-header {
  text-align: center;
  margin-bottom: 24px;
}

.upload-header h3 {
  font-size: 1.25rem;
  color: #1f2937;
  margin-bottom: 8px;
}

.current-mode {
  margin-top: 12px;
  font-size: 0.875rem;
  color: #6b7280;
}

.mode-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 600;
  font-size: 0.75rem;
}

.mode-badge.normal {
  background: #dbeafe;
  color: #1e40af;
}

.mode-badge.template {
  background: #fef3c7;
  color: #92400e;
}

.upload-area {
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  padding: 48px 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 24px;
}

.upload-area:hover {
  border-color: #8b5cf6;
  background-color: #f9fafb;
}

.upload-icon {
  font-size: 3rem;
  margin-bottom: 16px;
}

.upload-hint {
  color: #6b7280;
  font-size: 0.875rem;
  margin-top: 8px;
}

.selected-file {
  color: #059669;
  font-weight: 600;
  margin-top: 12px;
}

.upload-btn {
  width: 100%;
  background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 12px 24px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.upload-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px -3px rgba(139, 92, 246, 0.3);
}

.upload-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.status-header h3 {
  font-size: 1.25rem;
  color: #1f2937;
}

.status-info {
  display: flex;
  gap: 8px;
  align-items: center;
}

.status-badge {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: 600;
}

.status-processing {
  background: #fef3c7;
  color: #92400e;
}

.status-completed {
  background: #d1fae5;
  color: #065f46;
}

.status-error {
  background: #fee2e2;
  color: #991b1b;
}

.status-pending {
  background: #f3f4f6;
  color: #374151;
}

.progress-info {
  margin-bottom: 24px;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #f3f4f6;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%);
  transition: width 0.3s ease;
}

.progress-text {
  color: #6b7280;
  font-size: 0.875rem;
}

.retry-info {
  margin-top: 8px;
}

.retry-text {
  color: #f59e0b;
  font-size: 0.875rem;
  font-weight: 500;
}

.file-info {
  margin-bottom: 24px;
}

.file-info p {
  margin: 8px 0;
  color: #374151;
}

.download-section {
  margin-bottom: 16px;
}

.completion-info {
  margin-bottom: 16px;
}

.success-info {
  color: #065f46;
  font-weight: 500;
  margin-bottom: 4px;
}

.error-info {
  color: #dc2626;
  font-weight: 500;
}

.download-btn {
  background: #10b981;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 12px 24px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  justify-content: center;
}

.download-btn:hover {
  background: #059669;
  transform: translateY(-2px);
}

.download-icon {
  font-size: 1.2rem;
}

.error-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.retry-btn, .change-mode-btn {
  background: #6b7280;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 10px 20px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.3s ease;
  flex: 1;
}

.retry-btn:hover, .change-mode-btn:hover {
  background: #4b5563;
}

.change-mode-btn {
  background: #8b5cf6;
}

.change-mode-btn:hover {
  background: #7c3aed;
}

.error-card {
  border-left: 4px solid #ef4444;
}

.error-card h3 {
  color: #dc2626;
  margin-bottom: 12px;
}

.error-card p {
  color: #374151;
  margin-bottom: 16px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .test-case-reverse-container {
    padding: 16px;
  }
  
  .mode-switch-card, .upload-card, .status-card, .error-card {
    padding: 16px;
  }
  
  .mode-options {
    flex-direction: column;
  }
  
  .upload-area {
    padding: 32px 16px;
  }
  
  .status-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .status-info {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .error-actions {
    flex-direction: column;
  }
}
</style> 