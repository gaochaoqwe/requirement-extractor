<template>
  <el-dialog
    v-model="visible"
    title="问题报告单归零说明生成"
    width="640px"
    :close-on-click-modal="false"
    destroy-on-close
    @closed="onClosed"
  >
    <div class="ir-desc">
      <p>
        上传包含「问题报告单」工作表的 Excel，系统将读取 T 列「研制单位意见」，
        用 AI 生成「问题确认意见/归零说明」，写入同一行 AA 列（内容为修改说明 + 换行 + “问题已归零”）。
      </p>
    </div>

    <el-upload
      class="ir-upload"
      drag
      :auto-upload="false"
      :show-file-list="true"
      :limit="1"
      accept=".xlsx,.xlsm"
      :file-list="fileList"
      :disabled="processing"
      :on-change="onFileChange"
      :on-remove="onFileRemove"
      :on-exceed="onExceed"
    >
      <div class="ir-upload-hint">点击或拖拽 Excel 文件到此处</div>
    </el-upload>

    <GenerationProgress
      :progress="gp.progress.value"
      :items="gp.items.value"
      :active="processing"
      :elapsed="gp.elapsedSeconds.value"
      unit="行"
      :summary="rowSummary"
    />

    <el-alert
      v-if="result"
      class="ir-result"
      :type="resultType"
      :closable="false"
      show-icon
    >
      <template #title>{{ resultTitle }}</template>
      <div class="ir-result-body">
        <p>工作表：{{ result.sheet_name || '-' }}</p>
        <p>已生成 {{ result.updated_rows }} 行，跳过 {{ result.skipped_rows }} 行</p>
        <p v-if="errorCount > 0">
          其中 {{ errorCount }} 行 AI 生成失败，已回退为研制单位意见原文
        </p>
      </div>
    </el-alert>

    <template #footer>
      <el-button @click="visible = false">关闭</el-button>
      <el-button
        type="primary"
        :loading="processing"
        :disabled="!selectedFile || processing"
        @click="handleGenerate"
      >
        {{ processing ? '正在生成...' : '生成并下载' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'

import GenerationProgress from './GenerationProgress.vue'
import { useGenerationProgress } from '../composables/useGenerationProgress'

const GENERATE_URL = '/test-tools/test-case-assistant/issue-report/generate-opinions'
const PROGRESS_URL = '/test-tools/test-case-assistant/issue-report/progress'

const visible = ref(false)
const selectedFile = ref(null)
const fileList = ref([])
const processing = ref(false)
const result = ref(null)

const gp = useGenerationProgress(PROGRESS_URL, { startMessage: '正在上传 Excel 文件…' })

const errorCount = computed(() => (Array.isArray(result.value?.errors) ? result.value.errors.length : 0))
const resultType = computed(() => (errorCount.value > 0 ? 'warning' : 'success'))
const resultTitle = computed(() => (errorCount.value > 0 ? '生成完成（部分行使用原文回退）' : '生成完成'))
const rowSummary = computed(() => {
  const count = Number(gp.progress.value?.updated_rows) || 0
  return count > 0 ? `已生成 ${count} 行归零说明` : ''
})

const open = () => {
  visible.value = true
}

const resetState = () => {
  processing.value = false
  selectedFile.value = null
  fileList.value = []
  result.value = null
  gp.reset()
}

const onClosed = () => {
  resetState()
}

const onFileChange = (uploadFile) => {
  selectedFile.value = uploadFile?.raw || null
  fileList.value = uploadFile ? [uploadFile] : []
  result.value = null
}

const onFileRemove = () => {
  selectedFile.value = null
  fileList.value = []
}

const onExceed = () => {
  ElMessage.warning('一次只能上传一个文件，请先移除已选文件')
}

const downloadBlob = async (url, filename) => {
  const blob = await request.get(url, { responseType: 'blob' })
  const data = blob instanceof Blob ? blob : new Blob([blob])
  const objectUrl = URL.createObjectURL(data)
  const link = document.createElement('a')
  link.href = objectUrl
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(objectUrl)
}

const handleGenerate = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择 Excel 文件')
    return
  }

  const sid = gp.start()

  const formData = new FormData()
  formData.append('file', selectedFile.value)
  formData.append('session_id', sid)

  processing.value = true
  result.value = null

  try {
    const resp = await request.post(GENERATE_URL, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })

    // 收尾拉一次最终进度（失败原因也会体现在进度文案里）
    await gp.poll()

    if (!resp?.success) {
      ElMessage.error(resp?.error || '生成失败')
      return
    }

    result.value = resp
    const updatedRows = Number(resp.updated_rows) || 0
    const skippedRows = Number(resp.skipped_rows) || 0
    gp.markDone({
      current: updatedRows,
      total: updatedRows,
      updated_rows: updatedRows,
      message: `生成完成：已生成 ${updatedRows} 行归零说明，跳过 ${skippedRows} 行`,
    })

    if (updatedRows > 0 && resp.download_url) {
      await downloadBlob(resp.download_url, resp.download_filename || '问题报告单_归零说明.xlsx')
      ElMessage.success(`生成完成，共处理 ${updatedRows} 行`)
    } else {
      ElMessage.warning('未找到可生成的行（T列研制单位意见为空）')
    }
  } catch (e) {
    await gp.poll()
    ElMessage.error(e?.message || '生成失败')
  } finally {
    processing.value = false
    gp.stop()
  }
}

defineExpose({ open })
</script>

<style scoped>
.ir-desc {
  color: #4b5563;
  font-size: 13px;
  line-height: 1.7;
  margin-bottom: 12px;
}

.ir-upload :deep(.el-upload-dragger) {
  padding: 28px 16px;
}

.ir-upload-hint {
  color: #6b7280;
  font-size: 14px;
}

.ir-result {
  margin-top: 16px;
}

.ir-result-body {
  font-size: 13px;
  line-height: 1.7;
}

.ir-result-body p {
  margin: 2px 0;
}
</style>
