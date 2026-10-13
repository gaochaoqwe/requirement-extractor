<template>
  <el-dialog
    v-model="visible"
    title="动态测试问题单生成"
    width="640px"
    :close-on-click-modal="false"
    destroy-on-close
    @closed="onClosed"
  >
    <div class="dir-desc">
      <p>
        上传包含「测试用例单」工作表的 Excel，系统将筛选 AA 列「测试结论」为“不通过”的用例，
        按 G 列「测试项名称」分组，逐测试项结合 P 列输入条件、Q 列预期结果、Z 列测试结果用 AI 生成问题单，
        并汇总导出为 Excel 问题单。
      </p>
    </div>

    <el-upload
      class="dir-upload"
      drag
      :auto-upload="false"
      :show-file-list="true"
      :limit="1"
      accept=".xlsx,.xlsm"
      :file-list="fileList"
      :on-change="onFileChange"
      :on-remove="onFileRemove"
      :on-exceed="onExceed"
    >
      <div class="dir-upload-hint">点击或拖拽 Excel 文件到此处</div>
    </el-upload>

    <el-alert
      v-if="result"
      class="dir-result"
      :type="resultType"
      :closable="false"
      show-icon
    >
      <template #title>{{ resultTitle }}</template>
      <div class="dir-result-body">
        <p>工作表：{{ result.sheet_name || '-' }}</p>
        <p>涉及测试项 {{ result.test_item_count }} 个，生成问题单 {{ result.issue_count }} 条</p>
        <p v-if="errorCount > 0">
          其中 {{ errorCount }} 个测试项 AI 生成失败，已使用回退问题单
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

const GENERATE_URL = '/test-tools/test-case-assistant/dynamic-issue-report/generate'

const visible = ref(false)
const selectedFile = ref(null)
const fileList = ref([])
const processing = ref(false)
const result = ref(null)

const errorCount = computed(() => (Array.isArray(result.value?.errors) ? result.value.errors.length : 0))
const resultType = computed(() => (errorCount.value > 0 ? 'warning' : 'success'))
const resultTitle = computed(() => (errorCount.value > 0 ? '生成完成（部分测试项使用回退问题单）' : '生成完成'))

const open = () => {
  visible.value = true
}

const resetState = () => {
  selectedFile.value = null
  fileList.value = []
  processing.value = false
  result.value = null
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

  const formData = new FormData()
  formData.append('file', selectedFile.value)

  processing.value = true
  result.value = null
  try {
    const resp = await request.post(GENERATE_URL, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })

    if (!resp?.success) {
      ElMessage.error(resp?.error || '生成失败')
      return
    }

    result.value = resp

    if (resp.issue_count > 0 && resp.download_url) {
      await downloadBlob(resp.download_url, resp.download_filename || '问题单.xlsx')
      ElMessage.success(`生成完成，共 ${resp.issue_count} 条问题单`)
    } else {
      ElMessage.warning('未生成任何问题单')
    }
  } catch (e) {
    ElMessage.error(e?.message || '生成失败')
  } finally {
    processing.value = false
  }
}

defineExpose({ open })
</script>

<style scoped>
.dir-desc {
  color: #4b5563;
  font-size: 13px;
  line-height: 1.7;
  margin-bottom: 12px;
}

.dir-upload :deep(.el-upload-dragger) {
  padding: 28px 16px;
}

.dir-upload-hint {
  color: #6b7280;
  font-size: 14px;
}

.dir-result {
  margin-top: 16px;
}

.dir-result-body {
  font-size: 13px;
  line-height: 1.7;
}

.dir-result-body p {
  margin: 2px 0;
}
</style>
