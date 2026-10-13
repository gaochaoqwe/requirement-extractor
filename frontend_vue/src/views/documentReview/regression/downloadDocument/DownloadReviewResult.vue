<template>
  <div class="download-btn-container">
    <el-button type="primary" @click="downloadResult" :loading="downloading">
      <el-icon><Download /></el-icon>
      下载审查结果（Excel）
    </el-button>
    <el-button type="success" @click="downloadImpactReport" :loading="downloadingImpactReport">
      <el-icon><Document /></el-icon>
      下载批注版影响域分析报告
    </el-button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, Document } from '@element-plus/icons-vue'

const props = defineProps({
  sessionId: {
    type: [String, Number],
    required: true,
  }
});

const downloading = ref(false)
const downloadingImpactReport = ref(false)

async function downloadResult() {
  downloading.value = true
  try {
    const url = `/api/documentReview/Regression/download?session_id=${props.sessionId}`
    window.open(url, '_blank')
    ElMessage.success('审查结果下载成功')
  } catch (e) {
    console.error('下载审查结果失败:', e)
    ElMessage.error('下载审查结果失败')
  } finally {
    downloading.value = false
  }
}

async function downloadImpactReport() {
  downloadingImpactReport.value = true
  try {
    const url = `/api/documentReview/Regression/download/annotated/impactreport?session_id=${props.sessionId}`
    window.open(url, '_blank')
    ElMessage.success('影响域分析报告批注版下载成功')
  } catch (e) {
    console.error('下载影响域分析报告批注版失败:', e)
    ElMessage.error('下载影响域分析报告批注版失败')
  } finally {
    downloadingImpactReport.value = false
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
