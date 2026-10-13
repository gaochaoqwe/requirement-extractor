<template>
  <div class="test-case-summary-container">
    <div class="header">
      <h2>功能性能指标符合性表生成工具</h2>
      <p class="description">上传测试用例表，AI自动生成功能性能指标符合性分析表</p>
    </div>

    <!-- 文件上传区域 -->
    <div class="upload-section" v-if="!isProcessing && !isCompleted">
      <div 
        class="upload-area"
        :class="{ 'drag-over': isDragOver }"
        @drop="handleDrop"
        @dragover.prevent="isDragOver = true"
        @dragleave.prevent="isDragOver = false"
        @click="triggerFileInput"
      >
        <div class="upload-content">
          <i class="upload-icon">📄</i>
          <h3>选择或拖拽测试用例Excel文件</h3>
          <p>支持 .xlsx, .xls 格式</p>
          <p class="file-hint">请确保Excel文件包含"测试用例单"工作表</p>
          <el-button type="primary" size="large">选择文件</el-button>
        </div>
      </div>
      
      <input 
        ref="fileInput"
        type="file"
        accept=".xlsx,.xls"
        @change="handleFileSelect"
        style="display: none"
      />
      
      <!-- 选中的文件信息 -->
      <div v-if="selectedFile" class="file-info">
        <div class="file-details">
          <i class="file-icon">📋</i>
          <div class="file-text">
            <span class="file-name">{{ selectedFile.name }}</span>
            <span class="file-size">{{ formatFileSize(selectedFile.size) }}</span>
          </div>
          <el-button @click="clearFile" type="text" class="remove-btn">移除</el-button>
        </div>
        
        <div class="upload-actions">
          <el-button 
            type="primary" 
            size="large"
            @click="uploadFile"
            :loading="uploading"
          >
            {{ uploading ? '上传中...' : '开始处理' }}
          </el-button>
        </div>
      </div>
    </div>

    <!-- 处理进度区域 -->
    <div class="progress-section" v-if="isProcessing">
      <div class="progress-header">
        <h3>正在处理测试用例...</h3>
        <p>AI正在分析和总结您的测试用例，请稍候</p>
      </div>
      
      <div class="progress-content">
        <el-progress 
          :percentage="Math.round(progressPercentage)" 
          :stroke-width="8"
        />
        
        <div class="progress-stats">
          <div class="stat-item">
            <span class="stat-label">总测试项:</span>
            <span class="stat-value">{{ sessionStatus.total_test_items || 0 }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">已处理:</span>
            <span class="stat-value">{{ sessionStatus.processed_test_items || 0 }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">已完成:</span>
            <span class="stat-value">{{ sessionStatus.completed_items || 0 }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">处理失败:</span>
            <span class="stat-value">{{ sessionStatus.error_items || 0 }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 完成结果区域 -->
    <div class="result-section" v-if="isCompleted">
      <div class="result-header">
        <i class="success-icon">✅</i>
        <h3>处理完成！</h3>
        <p>测试用例总结已生成完成</p>
      </div>
      
      <div class="result-stats">
        <div class="stat-card">
          <div class="stat-number">{{ sessionStatus.total_test_items || 0 }}</div>
          <div class="stat-label">总测试项</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">{{ sessionStatus.completed_items || 0 }}</div>
          <div class="stat-label">成功处理</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">{{ sessionStatus.error_items || 0 }}</div>
          <div class="stat-label">处理失败</div>
        </div>
      </div>
      
      <div class="result-actions">
        <el-button 
          type="primary" 
          size="large"
          @click="downloadResult"
          :loading="downloading"
        >
          <i class="download-icon">⬇️</i>
          {{ downloading ? '准备下载...' : '下载用例总结结果' }}
        </el-button>
        
        <el-button 
          size="large"
          @click="resetTool"
        >
          重新开始
        </el-button>
      </div>
    </div>

    <div v-if="retrySuccessItems.length > 0" class="success-section">
      <div class="failed-header">
        <h3>重试成功测试项</h3>
      </div>
      <div v-for="item in retrySuccessItems" :key="item.item_id" class="success-item-card">
        <div class="failed-item-top">
          <div class="failed-item-name">{{ item.test_item_name }}</div>
          <el-tag type="success">重试成功</el-tag>
        </div>
        <div class="success-item-message">该测试项已重新生成成功，并已合并到最终下载表单中。</div>
      </div>
    </div>

    <div v-if="failedItems.length > 0" class="failed-section">
      <div class="failed-header">
        <h3>失败需求列表</h3>
        <el-button text type="primary" @click="refreshFailedItems">刷新</el-button>
      </div>

      <div v-for="item in failedItems" :key="item.item_id" class="failed-item-card">
        <div class="failed-item-top">
          <div class="failed-item-name">{{ item.test_item_name }}</div>
          <el-tag type="danger">失败</el-tag>
        </div>
        <div class="failed-item-error">失败原因：{{ item.error_message || '未知错误' }}</div>

        <div v-if="item.retry_history && item.retry_history.length" class="retry-history">
          <div class="retry-history-title">自动重试记录</div>
          <div
            v-for="history in item.retry_history"
            :key="`${item.item_id}-${history.attempt}`"
            class="retry-history-line"
          >
            第{{ history.attempt }}次：{{ history.error }}
          </div>
        </div>

        <div class="failed-item-actions">
          <el-button
            type="primary"
            :loading="retryingItemId === item.item_id"
            @click="retryItem(item)"
          >
            重试此测试项
          </el-button>
        </div>
      </div>
    </div>

    <!-- 错误提示 -->
    <div class="error-section" v-if="errorMessage">
      <el-alert
        :title="errorMessage"
        type="error"
        :closable="false"
        show-icon
      />
      <div class="error-actions">
        <el-button @click="resetTool">重新开始</el-button>
      </div>
    </div>

    <el-dialog v-model="rawDialogVisible" :title="rawDialogTitle" width="70%" top="5vh">
      <div class="raw-dialog-content">
        <div class="raw-block">
          <div class="raw-block-title">发送给模型的原始信息</div>
          <pre>{{ rawRequestText }}</pre>
        </div>
        <div class="raw-block">
          <div class="raw-block-title">AI返回的原始信息</div>
          <pre>{{ rawResponseText }}</pre>
        </div>
      </div>
      <template #footer>
        <el-button type="primary" @click="rawDialogVisible = false">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import testCaseSummaryService from '@/services/testCaseSummaryService'

export default {
  name: 'TestCaseSummary',
  setup() {
    // 响应式数据
    const selectedFile = ref(null)
    const isDragOver = ref(false)
    const uploading = ref(false)
    const downloading = ref(false)
    const isProcessing = ref(false)
    const isCompleted = ref(false)
    const errorMessage = ref('')
    const sessionId = ref('')
    const progressPercentage = ref(0)
    const fileInput = ref(null)
    const failedItems = ref([])
    const retrySuccessItems = ref([])
    const retryingItemId = ref(null)
    const rawDialogVisible = ref(false)
    const rawDialogTitle = ref('')
    const rawRequestText = ref('')
    const rawResponseText = ref('')
    
    const sessionStatus = reactive({
      total_test_items: 0,
      processed_test_items: 0,
      completed_items: 0,
      error_items: 0,
      processing_items: 0,
      status: '',
      original_filename: '',
      output_filename: '',
      failed_items: []
    })

    let statusPollingInterval = null

    // 文件处理方法
    const triggerFileInput = () => {
      fileInput.value?.click()
    }

    const handleFileSelect = (event) => {
      const file = event.target.files[0]
      if (file) {
        validateAndSetFile(file)
      }
    }

    const handleDrop = (event) => {
      event.preventDefault()
      isDragOver.value = false
      
      const files = event.dataTransfer.files
      if (files.length > 0) {
        validateAndSetFile(files[0])
      }
    }

    const validateAndSetFile = (file) => {
      // 验证文件类型
      const allowedTypes = [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-excel'
      ]
      
      if (!allowedTypes.includes(file.type) && !file.name.match(/\.(xlsx|xls)$/i)) {
        ElMessage.error('请选择Excel文件 (.xlsx 或 .xls)')
        return
      }

      // 验证文件大小 (50MB)
      const maxSize = 50 * 1024 * 1024
      if (file.size > maxSize) {
        ElMessage.error('文件大小不能超过50MB')
        return
      }

      selectedFile.value = file
      errorMessage.value = ''
    }

    const clearFile = () => {
      selectedFile.value = null
      if (fileInput.value) {
        fileInput.value.value = ''
      }
    }

    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }

    const syncStatus = (status) => {
      Object.assign(sessionStatus, status)
      failedItems.value = status.failed_items || []
    }

    const refreshFailedItems = async () => {
      if (!sessionId.value) return
      try {
        const response = await testCaseSummaryService.getFailedItems(sessionId.value)
        if (response?.success) {
          failedItems.value = response.failed_items || []
        }
      } catch (error) {
        console.error('获取失败项失败:', error)
      }
    }

    const openRawDialog = (title, rawRequest, rawResponse) => {
      rawDialogTitle.value = title
      rawRequestText.value = typeof rawRequest === 'string' ? rawRequest : JSON.stringify(rawRequest || {}, null, 2)
      rawResponseText.value = typeof rawResponse === 'string' ? rawResponse : JSON.stringify(rawResponse || {}, null, 2)
      rawDialogVisible.value = true
    }

    const retryItem = async (item) => {
      retryingItemId.value = item.item_id
      try {
        const response = await testCaseSummaryService.retrySingleItem(sessionId.value, item.item_id)
        openRawDialog(`测试项重试详情：${item.test_item_name}`, response?.raw_request, response?.raw_response)
        if (response?.success) {
          ElMessage.success(response.message || '重试成功')
          failedItems.value = failedItems.value.filter(failed => failed.item_id !== item.item_id)
          retrySuccessItems.value = [
            { item_id: item.item_id, test_item_name: item.test_item_name },
            ...retrySuccessItems.value.filter(success => success.item_id !== item.item_id)
          ]
        } else {
          ElMessage.error(response?.error || '重试失败')
        }
        await checkStatus({ silent: true })
        await refreshFailedItems()
      } catch (error) {
        ElMessage.error(error.message || '重试失败')
      } finally {
        retryingItemId.value = null
      }
    }

    // 上传和处理方法
    const uploadFile = async () => {
      if (!selectedFile.value) {
        ElMessage.error('请先选择文件')
        return
      }

      uploading.value = true
      errorMessage.value = ''

      try {
        const response = await testCaseSummaryService.uploadFile(selectedFile.value)
        
        console.log('上传响应:', response) // 调试日志
        console.log('响应类型:', typeof response) // 调试响应类型
        
        if (response && response.success) {
          sessionId.value = response.session_id
          isProcessing.value = true
          
          ElMessage.success('文件上传成功，开始处理...')
          
          // 开始轮询状态
          startStatusPolling()
        } else {
          throw new Error(response?.error || response?.message || '上传失败')
        }
      } catch (error) {
        console.error('上传失败:', error)
        console.error('错误详情:', error.response || error) // 更详细的错误日志
        errorMessage.value = error.message || '上传文件失败，请重试'
        ElMessage.error(errorMessage.value)
      } finally {
        uploading.value = false
      }
    }

    const checkStatus = async ({ silent = false } = {}) => {
      try {
        const status = await testCaseSummaryService.getSessionStatus(sessionId.value)
        if (!status.success) return

        syncStatus(status)

        if (status.total_test_items > 0) {
          progressPercentage.value = (status.processed_test_items / status.total_test_items) * 100
        }

        if (status.error_items > 0) {
          await refreshFailedItems()
        } else {
          failedItems.value = []
        }

        if (status.status === 'completed') {
          isProcessing.value = false
          isCompleted.value = true
          stopStatusPolling()
          if (!silent) {
            ElMessage.success('测试用例总结处理完成！')
          }
        } else if (status.status === 'error') {
          isProcessing.value = false
          errorMessage.value = status.error_message || '处理过程中发生错误'
          stopStatusPolling()
          ElMessage.error('处理失败: ' + errorMessage.value)
        }
      } catch (error) {
        console.error('获取状态失败:', error)
      }
    }

    // 状态轮询
    const startStatusPolling = () => {
      if (statusPollingInterval) {
        clearInterval(statusPollingInterval)
      }
      checkStatus({ silent: true })
      statusPollingInterval = setInterval(() => checkStatus(), 3000)
    }

    const stopStatusPolling = () => {
      if (statusPollingInterval) {
        clearInterval(statusPollingInterval)
        statusPollingInterval = null
      }
    }

    // 下载结果
    const downloadResult = async () => {
      downloading.value = true
      
      try {
        const downloadUrl = await testCaseSummaryService.getDownloadUrl(sessionId.value)
        
        // 创建下载链接
        const link = document.createElement('a')
        link.href = downloadUrl
        link.download = sessionStatus.output_filename || 'test_case_summary.xlsx'
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        
        ElMessage.success('文件下载成功！')
      } catch (error) {
        console.error('下载失败:', error)
        ElMessage.error('下载失败: ' + (error.message || '未知错误'))
      } finally {
        downloading.value = false
      }
    }

    // 重置工具
    const resetTool = () => {
      selectedFile.value = null
      isDragOver.value = false
      uploading.value = false
      downloading.value = false
      isProcessing.value = false
      isCompleted.value = false
      errorMessage.value = ''
      sessionId.value = ''
      progressPercentage.value = 0
      failedItems.value = []
      retrySuccessItems.value = []
      retryingItemId.value = null
      rawDialogVisible.value = false
      rawDialogTitle.value = ''
      rawRequestText.value = ''
      rawResponseText.value = ''
      
      Object.assign(sessionStatus, {
        total_test_items: 0,
        processed_test_items: 0,
        completed_items: 0,
        error_items: 0,
        processing_items: 0,
        status: '',
        original_filename: '',
        output_filename: '',
        failed_items: []
      })
      
      stopStatusPolling()
      
      if (fileInput.value) {
        fileInput.value.value = ''
      }
    }

    // 生命周期
    onMounted(() => {
      // 组件挂载时的初始化逻辑
    })

    onUnmounted(() => {
      stopStatusPolling()
    })

    return {
      // 数据
      selectedFile,
      isDragOver,
      uploading,
      downloading,
      isProcessing,
      isCompleted,
      errorMessage,
      sessionId,
      progressPercentage,
      sessionStatus,
      fileInput,
      failedItems,
      retrySuccessItems,
      retryingItemId,
      rawDialogVisible,
      rawDialogTitle,
      rawRequestText,
      rawResponseText,
      
      // 方法
      triggerFileInput,
      handleFileSelect,
      handleDrop,
      clearFile,
      formatFileSize,
      uploadFile,
      refreshFailedItems,
      retryItem,
      downloadResult,
      resetTool
    }
  }
}
</script>

<style scoped>
.test-case-summary-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.header {
  text-align: center;
  margin-bottom: 30px;
}

.header h2 {
  color: #2c3e50;
  margin-bottom: 10px;
}

.description {
  color: #7f8c8d;
  font-size: 16px;
}

/* 上传区域样式 */
.upload-section {
  margin-bottom: 30px;
}

.upload-area {
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background-color: #fafafa;
}

.upload-area:hover,
.upload-area.drag-over {
  border-color: #409eff;
  background-color: #f0f9ff;
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
}

.upload-icon {
  font-size: 48px;
}

.upload-content h3 {
  margin: 0;
  color: #2c3e50;
}

.upload-content p {
  margin: 0;
  color: #7f8c8d;
}

.file-hint {
  font-size: 14px;
  color: #e67e22 !important;
}

/* 文件信息样式 */
.file-info {
  margin-top: 20px;
  padding: 20px;
  border: 1px solid #e1e8ed;
  border-radius: 8px;
  background-color: #f8f9fa;
}

.file-details {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
}

.file-icon {
  font-size: 24px;
}

.file-text {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.file-name {
  font-weight: 500;
  color: #2c3e50;
}

.file-size {
  font-size: 14px;
  color: #7f8c8d;
}


.remove-btn {
  color: #e74c3c;
}

.upload-actions {
  text-align: center;
}

/* 进度区域样式 */
.progress-section {
  text-align: center;
  padding: 40px 20px;
}

.progress-header h3 {
  color: #2c3e50;
  margin-bottom: 10px;
}

.progress-header p {
  color: #7f8c8d;
  margin-bottom: 30px;
}

.progress-content {
  max-width: 500px;
  margin: 0 auto;
}

.progress-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 20px;
  margin-top: 30px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
}

.stat-label {
  font-size: 14px;
  color: #7f8c8d;
}

.stat-value {
  font-size: 20px;
  font-weight: bold;
  color: #2c3e50;
}

/* 结果区域样式 */
.result-section {
  text-align: center;
  padding: 40px 20px;
}

.result-header {
  margin-bottom: 30px;
}

.success-icon {
  font-size: 48px;
  margin-bottom: 15px;
  display: block;
}

.result-header h3 {
  color: #27ae60;
  margin-bottom: 10px;
}

.result-header p {
  color: #7f8c8d;
}

.result-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
  max-width: 500px;
  margin-left: auto;
  margin-right: auto;
}

.stat-card {
  padding: 20px;
  border-radius: 8px;
  background-color: #f8f9fa;
  border: 1px solid #e1e8ed;
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  color: #2c3e50;
  margin-bottom: 5px;
}

.stat-card .stat-label {
  font-size: 14px;
  color: #7f8c8d;
}

.result-actions {
  display: flex;
  justify-content: center;
  gap: 15px;
  flex-wrap: wrap;
}

.download-icon {
  margin-right: 5px;
}

/* 错误区域样式 */
.error-section {
  margin: 30px 0;
}

.error-actions {
  text-align: center;
  margin-top: 20px;
}


.failed-section,
.success-section {
  margin: 30px 0;
}

.success-item-card {
  border: 1px solid #b7eb8f;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  background: #f6ffed;
}

.success-item-message {
  color: #2e7d32;
  line-height: 1.7;
}

.failed-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.failed-item-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  background: #fff;
}

.failed-item-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.failed-item-name {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

.failed-item-error {
  color: #c0392b;
  line-height: 1.7;
}

.retry-history {
  margin-top: 12px;
  padding: 12px;
  background: #fafafa;
  border-radius: 6px;
}

.retry-history-title,
.raw-block-title {
  font-weight: 600;
  margin-bottom: 8px;
}

.retry-history-line {
  color: #606266;
  line-height: 1.7;
}

.failed-item-actions {
  margin-top: 14px;
  display: flex;
  justify-content: flex-end;
}

.raw-dialog-content {
  display: grid;
  gap: 16px;
}

.raw-block pre {
  margin: 0;
  max-height: 260px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
  background: #fafafa;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 12px;
  font-size: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .test-case-summary-container {
    padding: 15px;
  }
  
  .upload-area {
    padding: 30px 15px;
  }
  
  .progress-stats {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .result-stats {
    grid-template-columns: 1fr;
  }
  
  .result-actions {
    flex-direction: column;
    align-items: center;
  }
}
</style> 