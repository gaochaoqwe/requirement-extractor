<template>
  <el-dialog :model-value="visible" @update:modelValue="onUpdateVisible" title="智能表单导入" width="70%">
    <div class="upload-area">
      <el-upload
        class="upload-intelligent"
        :before-upload="beforeUpload"
        :http-request="doNothing"
        :show-file-list="false"
        accept=".xlsx,.xls"
      >
        <el-button type="primary" :loading="loading">选择Excel并预览建议</el-button>
      </el-upload>
      <span class="tip">支持四列表头：软件类别、测试项名称、测试项描述、测试方法</span>
    </div>

    <el-table v-loading="loading" :data="suggestions" height="420" stripe>
      <el-table-column prop="index" label="#" width="70" />
      <el-table-column prop="incoming.software_category" label="软件类别" width="140" />
      <el-table-column prop="incoming.test_item_name" label="测试项名称" width="200" />
      <el-table-column prop="suggestion_type" label="建议" width="140">
        <template #default="{ row }">
          <el-tag :type="row.suggestion_type === 'append_columns' ? 'success' : 'warning'">
            {{ row.suggestion_type === 'append_columns' ? '仅追加后两列' : '新建记录' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="confidence" label="置信度" width="100">
        <template #default="{ row }">
          {{ (row.confidence * 100).toFixed(0) }}%
        </template>
      </el-table-column>
      <el-table-column prop="matched_name" label="匹配到的现有项" />
      <el-table-column label="操作" width="160">
        <template #default="{ row, $index }">
          <el-select v-model="decisions[$index].suggestion_type" size="small" style="width: 130px">
            <el-option label="仅追加后两列" value="append_columns" />
            <el-option label="新建记录" value="create_new" />
          </el-select>
        </template>
      </el-table-column>
    </el-table>

    <template #footer>
      <el-button @click="close">取消</el-button>
      <el-button type="primary" :disabled="!suggestions.length" :loading="submitting" @click="submit">确认提交</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { previewIntelligentImport, commitIntelligentImport } from '@/api/requirements'

const props = defineProps({
  visible: { type: Boolean, default: false },
})
const emit = defineEmits(['update:visible'])

const loading = ref(false)
const submitting = ref(false)
const suggestions = ref([])
const rawFile = ref(null)
const decisions = ref([])

function doNothing() {}

function onUpdateVisible(val) {
  emit('update:visible', val)
}

function reset() {
  suggestions.value = []
  decisions.value = []
  rawFile.value = null
}

function beforeUpload(file) {
  loading.value = true
  rawFile.value = file
  const form = new FormData()
  form.append('file', file)
  previewIntelligentImport(form)
    .then((res) => {
      suggestions.value = Array.isArray(res) ? res : []
      decisions.value = suggestions.value.map((s) => ({
        suggestion_type: s.suggestion_type,
        matched_id: s.matched_id || null,
        incoming: s.incoming,
      }))
    })
    .catch((err) => {
      ElMessage.error(err.message || '预览失败')
    })
    .finally(() => {
      loading.value = false
    })
  return false
}

function submit() {
  if (!decisions.value.length) {
    ElMessage.warning('没有可提交的数据')
    return
  }
  submitting.value = true
  commitIntelligentImport(decisions.value)
    .then((res) => {
      ElMessage.success(`新建 ${res.created || 0} 条，更新 ${res.updated || 0} 条`)
      close()
    })
    .catch((err) => {
      ElMessage.error(err.message || '提交失败')
    })
    .finally(() => {
      submitting.value = false
    })
}

function close() {
  emit('update:visible', false)
  reset()
}
</script>

<style scoped>
.upload-area {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}
.tip { color: #909399; font-size: 12px; }
</style>
