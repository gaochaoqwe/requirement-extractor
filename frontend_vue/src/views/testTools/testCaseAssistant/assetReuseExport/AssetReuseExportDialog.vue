<template>
  <el-dialog
    v-model="visibleProxy"
    title="组织资产复用"
    width="500px"
    :close-on-click-modal="false"
  >
    <div class="asset-reuse-export-form">
      <div class="form-item">
        <label class="form-label">选择产品类型：</label>
        <el-select v-model="state.selectedType" placeholder="请选择产品类型" style="width: 100%">
          <el-option label="转塔" value="转塔" />
          <el-option label="对抗告警" value="对抗告警" />
          <el-option label="光雷" value="光雷" />
          <el-option label="吊舱" value="吊舱" />
        </el-select>
      </div>

      <div class="form-item" v-if="state.availableSoftwareTypes.length > 0">
        <label class="form-label">选择软件类型：</label>
        <el-select v-model="state.selectedSoftwareType" placeholder="请选择软件类型" style="width: 100%">
          <el-option
            v-for="softwareType in state.availableSoftwareTypes"
            :key="softwareType"
            :label="softwareType"
            :value="softwareType"
          />
        </el-select>
      </div>

      <div class="form-item">
        <label class="form-label">上传Excel文档：</label>
        <el-upload
          :auto-upload="false"
          :show-file-list="true"
          :limit="1"
          accept=".xlsx,.xls"
          :on-change="handleFileChange"
          :on-remove="handleFileRemove"
        >
          <el-button type="primary" :icon="Upload">选择文件</el-button>
          <template #tip>
            <div class="el-upload__tip">
              只能上传 xlsx/xls 文件，且文档应包含名为“需求分析表”和“测试用例单”的sheet
            </div>
          </template>
        </el-upload>
      </div>

      <div class="form-item">
        <div class="process-description">
          <h4>处理说明：</h4>
          <ul>
            <li>根据产品类型+软件类型，从组织资产库匹配数据并回填</li>
            <li>需求分析表：按测试项名称匹配，填充测试项描述/测试方法</li>
            <li>测试用例单：按测试项匹配，用例行插入并填充用例模板字段</li>
          </ul>
        </div>
      </div>

      <div class="form-item" v-if="state.processing">
        <div class="progress-container">
          <div class="progress-header">
            <span class="progress-text">{{ state.progressText }}</span>
            <span class="progress-percentage">{{ state.progressPercentage }}%</span>
          </div>
          <el-progress
            :percentage="state.progressPercentage"
            :stroke-width="12"
            :show-text="false"
            :color="progressColor"
          />
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="visibleProxy = false">
          {{ state.canDownload ? '关闭' : '取消' }}
        </el-button>

        <el-button
          v-if="!state.canDownload"
          type="primary"
          @click="startProcess"
          :loading="state.processing"
          :disabled="!state.selectedType || !state.selectedSoftwareType || !state.selectedFile"
        >
          {{ state.processing ? '处理中...' : '开始处理' }}
        </el-button>

        <el-button v-if="state.canDownload" type="success" :icon="Download" @click="downloadResult">
          下载文件
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload, Download } from '@element-plus/icons-vue'
import { assetReuseExportService } from './assetReuseExportService'
import request from '@/api/request'

const props = defineProps({
  visible: { type: Boolean, default: false },
  taskId: { type: String, default: '' },
})

const emit = defineEmits(['update:visible'])

const visibleProxy = computed({
  get: () => props.visible,
  set: (v) => emit('update:visible', v),
})

const state = reactive({
  selectedType: '',
  selectedSoftwareType: '',
  availableSoftwareTypes: [],
  selectedFile: null,

  processing: false,
  progressText: '准备处理...',
  progressPercentage: 0,

  canDownload: false,
  taskId: null,
  filename: null,
})

const productSoftwareMapping = {
  转塔: ['主控', '随动', '图像', '红外', '激光'],
  对抗告警: ['告警主控', '告警红外', '分色滤光', '目标检测', '拼接', '干扰主控', '伺服', '干扰红外', '干扰图像', '干扰激光'],
  光雷: ['主控', '随动', '红外', '图像', '激光'],
  吊舱: ['主控', '随动', '图像', '红外', '激光'],
}

watch(
  () => state.selectedType,
  (newType) => {
    state.selectedSoftwareType = ''
    state.availableSoftwareTypes = newType && productSoftwareMapping[newType] ? productSoftwareMapping[newType] : []
  }
)

watch(
  () => props.visible,
  (v) => {
    if (v) {
      reset()
      hydrateFromTask()
    }
  }
)

async function hydrateFromTask() {
  const tid = props.taskId
  if (!tid) return
  try {
    const resp = await request.get(`/test-tools/test-case-assistant/tasks/${tid}`)
    const productType = resp?.product_type
    const softwareType = resp?.software_type

    if (productType) {
      state.selectedType = productType
    }
    if (softwareType) {
      state.selectedSoftwareType = softwareType
    }
  } catch (_) {
    // ignore
  }
}

const progressColor = computed(() => {
  const p = state.progressPercentage
  if (p < 30) return '#f56c6c'
  if (p < 60) return '#e6a23c'
  if (p < 90) return '#409eff'
  return '#67c23a'
})

function reset() {
  state.selectedType = ''
  state.selectedSoftwareType = ''
  state.availableSoftwareTypes = []
  state.selectedFile = null

  state.processing = false
  state.progressText = '准备处理...'
  state.progressPercentage = 0

  state.canDownload = false
  state.taskId = null
  state.filename = null
}

function handleFileChange(file) {
  state.selectedFile = file
}

function handleFileRemove() {
  state.selectedFile = null
}

async function downloadResult() {
  if (!state.taskId) {
    ElMessage.error('无法获取下载信息')
    return
  }

  try {
    const resp = await assetReuseExportService.download(state.taskId)
    const blob = new Blob([resp.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = state.filename || '组织资产复用.xlsx'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('文件下载完成')
  } catch (e) {
    ElMessage.error('下载失败: ' + (e?.message || '未知错误'))
  }
}

async function startProcess() {
  if (!state.selectedType || !state.selectedSoftwareType || !state.selectedFile?.raw) {
    ElMessage.warning('请选择产品类型、软件类型并上传文件')
    return
  }

  const tid = props.taskId
  if (tid) {
    try {
      await request.patch(`/test-tools/test-case-assistant/tasks/${tid}`, {
        product_type: state.selectedType,
        software_type: state.selectedSoftwareType,
      })
    } catch (e) {
      ElMessage.warning('保存产品/软件类型失败：' + (e?.message || '未知错误'))
    }
  }

  state.processing = true
  state.progressPercentage = 0
  state.progressText = '正在上传文件并启动任务...'

  let timer = null

  try {
    const fd = new FormData()
    fd.append('file', state.selectedFile.raw)
    fd.append('selected_type', state.selectedType)
    fd.append('selected_software_type', state.selectedSoftwareType)

    const startResp = await assetReuseExportService.start(fd)
    const taskId = startResp.data?.task_id
    if (!taskId) throw new Error('启动任务失败：未返回task_id')

    state.taskId = taskId
    state.progressPercentage = 10
    state.progressText = '任务已启动，正在处理...'

    timer = window.setInterval(async () => {
      try {
        const progResp = await assetReuseExportService.progress(taskId)
        const d = progResp.data

        if (typeof d?.progress === 'number') state.progressPercentage = Math.max(state.progressPercentage, d.progress)
        if (d?.message) state.progressText = d.message

        if (d?.status === 'completed') {
          if (timer) window.clearInterval(timer)
          timer = null

          state.progressPercentage = 100
          state.progressText = '处理完成！可以下载文件'
          state.canDownload = true
          state.processing = false
          state.filename = d.filename || `组织资产复用_${state.selectedType}_${String(taskId).slice(0, 8)}.xlsx`
          ElMessage.success('处理完成，可以下载文件')
        } else if (d?.status === 'error') {
          if (timer) window.clearInterval(timer)
          timer = null
          throw new Error(d?.message || d?.error || '处理失败')
        }
      } catch (pollErr) {
        // 网络/偶发错误先继续轮询
        console.error(pollErr)
      }
    }, 5000)
  } catch (e) {
    console.error(e)
    ElMessage.error('组织资产复用失败: ' + (e?.message || '未知错误'))
    state.processing = false
    state.canDownload = false
    state.taskId = null
  }
}
</script>

<style scoped>
.asset-reuse-export-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 13px;
  color: #374151;
}

.process-description {
  padding: 10px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f9fafb;
}

.process-description h4 {
  margin: 0 0 6px;
  font-size: 13px;
}

.process-description ul {
  margin: 0;
  padding-left: 18px;
  font-size: 12px;
  color: #4b5563;
}

.progress-container {
  padding: 10px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
  font-size: 12px;
  color: #374151;
}
</style>
