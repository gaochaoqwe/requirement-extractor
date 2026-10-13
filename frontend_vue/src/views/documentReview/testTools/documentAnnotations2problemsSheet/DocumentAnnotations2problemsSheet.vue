<template>
  <div class="document-annotations-container">
    <div class="header">
      <h1>文档批注转问题报告单工具</h1>
      <p class="description">根据需求规格说明中的批注自动生成问题报告单</p>
    </div>

    <div class="main-content">
      <!-- 上传区域 -->
      <div class="upload-section" v-if="!sessionId">
        <div class="upload-card">
          <div class="upload-header">
            <h3>上传Word文档</h3>
            <p>支持格式：.docx</p>
          </div>
          
          <div class="upload-area" @click="triggerFileInput" @dragover.prevent @drop.prevent="handleDrop">
            <input 
              ref="fileInput" 
              type="file" 
              accept=".docx" 
              @change="handleFileSelect" 
              style="display: none"
            >
            <div class="upload-content">
              <div class="upload-icon">📄</div>
              <p class="upload-prompt">点击选择文件或拖拽文件到此处</p>
              <div class="upload-hint">
                <div class="upload-hint-row upload-hint-row-first">
                  <span class="upload-hint-label">文档批注格式：</span>
                  <span class="upload-hint-value"></span>
                </div>
                <div class="upload-hint-row">
                  <span class="upload-hint-label">位置：</span>
                  <span class="upload-hint-value">填写问题所在章节号和章节名称</span>
                </div>
                <div class="upload-hint-row">
                  <span class="upload-hint-label">说明：</span>
                  <span class="upload-hint-value">问题进一步解释说明</span>
                </div>
              </div>
              <p class="upload-note">问题名称、需求描述和测评意见将由AI自动生成</p>
              <p v-if="selectedFile" class="selected-file">已选择: {{ selectedFile.name }}</p>
            </div>
          </div>
          <button 
            class="upload-btn" 
            @click="uploadFile" 
            :disabled="!selectedFile || uploading"
          >
            {{ uploading ? '处理中...' : '开始处理' }}
          </button>
        </div>
      </div>

      <!-- 处理状态区域 -->
      <div class="processing-section" v-if="sessionId">
        <div class="status-card">
          <div class="status-header">
            <h3>处理状态</h3>
            <div class="status-badge" :class="statusClass">{{ statusText }}</div>
          </div>
          
          <div class="progress-info">
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: progress + '%' }"></div>
            </div>
            <p class="progress-text">{{ progressText }}</p>
          </div>
          
          <div class="file-info">
            <p><strong>文件名：</strong>{{ originalFilename }}</p>
            <p v-if="totalAnnotations > 0"><strong>批注总数：</strong>{{ totalAnnotations }}</p>
          </div>
          
          <!-- 下载按钮 -->
          <div class="download-section" v-if="status === 'completed'">
            <button class="download-btn" @click="downloadResult">
              <span class="download-icon">⬇️</span>
              下载问题报告单
            </button>
          </div>
        </div>
      </div>

      <!-- 错误信息 -->
      <div class="error-section" v-if="error">
        <div class="error-card">
          <h3>❌ 处理失败</h3>
          <p>{{ error }}</p>
          <button class="retry-btn" @click="restart">重试</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'

export default {
  name: 'DocumentAnnotations2problemsSheet',
  setup() {
    // API基础路径
    const BASE_URL = '/api/documentReview/testTools/document-annotations-to-problems'
    
    // 响应式数据
    const selectedFile = ref(null)
    const uploading = ref(false)
    const sessionId = ref('')
    const status = ref('')
    const progress = ref(0)
    const originalFilename = ref('')
    const totalAnnotations = ref(0)
    const processedAnnotations = ref(0)
    const error = ref('')
    const pollingInterval = ref(null)
    const fileInput = ref(null)

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
        return '批注处理完成，问题报告单已生成'
      } else if (status.value === 'processing') {
        if (totalAnnotations.value > 0) {
          return `正在处理批注 ${processedAnnotations.value} / ${totalAnnotations.value}（${progress.value.toFixed(1)}%）`
        }
        return `正在处理文档批注... ${progress.value.toFixed(1)}%`
      } else {
        return '等待开始处理'
      }
    })

    // 文件选择相关方法
    const triggerFileInput = () => {
      if (fileInput.value) {
        fileInput.value.click()
      }
    }

    const handleFileSelect = (event) => {
      const file = event.target.files[0]
      if (file) {
        selectedFile.value = file
        error.value = ''
      }
    }

    const handleDrop = (event) => {
      const files = event.dataTransfer.files
      if (files.length > 0) {
        selectedFile.value = files[0]
        error.value = ''
      }
    }

    // 上传文件
    const uploadFile = async () => {
      if (!selectedFile.value) {
        error.value = '请选择文件'
        return
      }

      try {
        uploading.value = true
        error.value = ''
        
        const formData = new FormData()
        formData.append('file', selectedFile.value)
        
        const response = await axios.post(`${BASE_URL}/upload`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        
        if (response.data.success) {
          sessionId.value = response.data.session_id
          status.value = 'processing'
          originalFilename.value = selectedFile.value.name
          
          // 开始轮询状态
          startStatusPolling()
        } else {
          error.value = response.data.error || '上传失败'
        }
      } catch (err) {
        error.value = '上传文件时出错: ' + (err.response?.data?.detail || err.message)
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
          const response = await axios.get(`${BASE_URL}/status/${sessionId.value}`)
          
          if (response.data.success) {
            status.value = response.data.status
            progress.value = response.data.progress || 0
            totalAnnotations.value = response.data.total_annotations || 0
            processedAnnotations.value = response.data.processed_annotations || 0
            
            if (response.data.status === 'completed' || response.data.status === 'error') {
              clearInterval(pollingInterval.value)
              pollingInterval.value = null
              
              if (response.data.status === 'error') {
                error.value = response.data.error_message || '处理失败'
              }
            }
          } else {
            console.error('获取状态失败:', response.data.error)
          }
        } catch (err) {
          console.error('轮询状态时出错:', err)
        }
      }, 2000) // 每2秒轮询一次
    }

    // 下载结果
    const downloadResult = async () => {
      try {
        const url = `${window.location.origin}/api/documentReview/testTools/document-annotations-to-problems/download/${sessionId.value}`
        
        // 创建一个临时的a标签来触发下载
        const link = document.createElement('a')
        link.href = url
        link.download = `问题报告单_${sessionId.value}.xlsx`
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
      totalAnnotations.value = 0
      error.value = ''
      uploading.value = false
      
      if (pollingInterval.value) {
        clearInterval(pollingInterval.value)
        pollingInterval.value = null
      }
    }

    // 生命周期
    onMounted(() => {
      console.log('DocumentAnnotations2problemsSheet 组件已挂载')
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
      totalAnnotations,
      processedAnnotations,
      error,
      fileInput,
      statusClass,
      statusText,
      progressText,
      triggerFileInput,
      handleFileSelect,
      handleDrop,
      uploadFile,
      downloadResult,
      restart
    }
  }
}
</script>

<style scoped>
.document-annotations-container {
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

.upload-section, .processing-section, .error-section {
  margin-bottom: 24px;
}

.upload-card, .status-card, .error-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
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

.upload-content {
  display: inline-block;
  text-align: left;
  max-width: 100%;
  /* 与“位置/说明”等提示行共享同一套标签列宽，用于对齐 */
  --hint-label-width: 8em;
}

.upload-icon {
  font-size: 3rem;
  margin-bottom: 16px;
  width: 100%;
  text-align: center;
}

.upload-prompt {
  margin: 0;
  padding: 0;
}

.upload-hint {
  color: #6b7280;
  font-size: 0.875rem;
  margin-top: 8px;
  margin-left: 0;
  margin-right: 0;
  padding: 0;
  white-space: pre-line;
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 0.25em;
}

.upload-hint-row {
  display: grid;
  /* 标签列要能容纳"文档批注格式："避免断行，同时保持冒号对齐 */
  grid-template-columns: var(--hint-label-width) 1fr;
  align-items: start;
  margin: 0;
  padding: 0;
}

/* 第一行（文档批注格式）的标签左对齐，与"点击选择文件"对齐 */
.upload-hint-row-first .upload-hint-label {
  justify-self: start;
  text-align: left;
}

.upload-hint-label {
  font-weight: 700;
  white-space: nowrap;
  /* 让冒号贴近内容列，减少"标签-内容"之间的空白 */
  justify-self: end;
  text-align: right;
  margin: 0;
  padding: 0;
}

.upload-hint-value {
  white-space: pre-line;
  margin: 0;
  padding: 0;
}

.upload-note {
  color: #8b5cf6;
  font-size: 0.875rem;
  margin-top: 4px;
  font-weight: 500;
  /* 与“位置/说明”同一左对齐基线（标签列起点），避免看起来跟上方图标对齐 */
  padding-left: 0;
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

.retry-btn {
  background: #6b7280;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 10px 20px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.retry-btn:hover {
  background: #4b5563;
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
  .document-annotations-container {
    padding: 16px;
  }
  
  .upload-card, .status-card, .error-card {
    padding: 16px;
  }
  
  .upload-area {
    padding: 32px 16px;
  }
  
  .status-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style> 