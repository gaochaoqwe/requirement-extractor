<template>
  <div class="download-btn-container">
    <el-button type="primary" @click="downloadResult" :loading="downloading">
      <el-icon><Download /></el-icon>
      下载审查结果（Excel）
    </el-button>
    <el-button type="success" @click="downloadTaskBook" :loading="downloadingTaskBook">
      <el-icon><Document /></el-icon>
      下载批注版研制任务书
    </el-button>
    <el-button type="warning" @click="downloadRequirementSpec" :loading="downloadingRequirementSpec">
      <el-icon><Tickets /></el-icon>
      下载批注版需求规格说明
    </el-button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, Document, Tickets } from '@element-plus/icons-vue'

const props = defineProps({
  sessionId: {
    type: [String, Number],
    required: true,
  },
  apiService: Object,
});

const downloading = ref(false)
const downloadingTaskBook = ref(false)
const downloadingRequirementSpec = ref(false)

async function downloadResult() {
  downloading.value = true
  try {
    await props.apiService.downloadReviewResult(props.sessionId);
    ElMessage.success('审查结果下载成功')
  } catch (e) {
    console.error('下载审查结果失败:', e)
    ElMessage.error('下载审查结果失败')
  } finally {
    downloading.value = false
  }
}

async function downloadTaskBook() {
  downloadingTaskBook.value = true
  try {
    const url = `/api/documentReview/ConfigurationItem/download/api/download/annotated/taskbook?session_id=${props.sessionId}`
    window.open(url, '_blank')
    ElMessage.success('研制任务书批注版下载成功')
  } catch (e) {
    console.error('下载研制任务书批注版失败:', e)
    ElMessage.error('下载研制任务书批注版失败')
  } finally {
    downloadingTaskBook.value = false
  }
}

async function downloadRequirementSpec() {
  downloadingRequirementSpec.value = true
  try {
    const url = `/api/documentReview/ConfigurationItem/download/api/download/annotated/requirementspec?session_id=${props.sessionId}`
    window.open(url, '_blank')
    ElMessage.success('需求规格说明批注版下载成功')
  } catch (e) {
    console.error('下载需求规格说明批注版失败:', e)
    ElMessage.error('下载需求规格说明批注版失败')
  } finally {
    downloadingRequirementSpec.value = false
  }
}
</script>

<style scoped>
.download-btn-container {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 16px;
}

.download-btn-container .el-button {
  min-width: 180px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.download-btn-container .el-button .el-icon {
  font-size: 16px;
}
</style>
