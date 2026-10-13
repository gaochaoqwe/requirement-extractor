<template>
  <el-dialog
    v-model="dialogVisible"
    title="导入Excel文件"
    width="80%"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    @close="handleClose"
  >
    <div class="import-dialog-content">
      <!-- 步骤指示器 -->
      <el-steps :active="currentStep" finish-status="success" align-center>
        <el-step title="选择文件" description="上传Excel文件" />
        <el-step title="数据预览" description="检查导入数据" />
        <el-step title="导入完成" description="确认导入结果" />
      </el-steps>

      <!-- 步骤1：文件选择 -->
      <div v-if="currentStep === 0" class="step-content">
        <div class="file-upload-area">
          <el-upload
            ref="uploadRef"
            class="excel-upload"
            drag
            :auto-upload="false"
            :show-file-list="false"
            accept=".xlsx,.xls"
            :on-change="handleFileChange"
            :before-upload="beforeUpload"
          >
            <div class="upload-content">
              <el-icon class="upload-icon" size="48" color="#409EFF">
                <Upload />
              </el-icon>
              <div class="upload-text">
                <div class="upload-title">点击或拖拽Excel文件到此处</div>
                <div class="upload-hint">支持 .xlsx 和 .xls 格式</div>
              </div>
            </div>
          </el-upload>
          
          <div v-if="selectedFile" class="file-info">
            <div class="file-item">
              <el-icon class="file-icon"><Document /></el-icon>
              <span class="file-name">{{ selectedFile.name }}</span>
              <span class="file-size">({{ formatFileSize(selectedFile.size) }})</span>
              <el-button
                type="danger"
                size="small"
                text
                @click="removeFile"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>
        </div>

        <!-- 导入选项 -->
        <div class="import-options">
          <h4>导入选项</h4>
          <el-form :model="importOptions" label-width="120px">
            <el-form-item label="工作表名称">
              <el-input
                v-model="importOptions.sheetName"
                placeholder="光电需求分析表"
                style="width: 200px;"
              />
              <el-tooltip content="Excel文件中要导入的工作表名称" placement="top">
                <el-icon class="help-icon"><QuestionFilled /></el-icon>
              </el-tooltip>
            </el-form-item>
            <el-form-item label="清空现有数据">
              <el-switch
                v-model="importOptions.clearExisting"
                active-text="是"
                inactive-text="否"
              />
              <el-tooltip content="导入前是否清空数据库中的现有数据" placement="top">
                <el-icon class="help-icon"><QuestionFilled /></el-icon>
              </el-tooltip>
            </el-form-item>
            <el-form-item label="跳过空行">
              <el-switch
                v-model="importOptions.skipEmptyRows"
                active-text="是"
                inactive-text="否"
              />
            </el-form-item>
          </el-form>
        </div>
      </div>

      <!-- 步骤2：数据预览 -->
      <div v-if="currentStep === 1" class="step-content">
        <div class="preview-header">
          <h4>数据预览</h4>
          <div class="preview-stats">
            <el-tag type="info">共 {{ previewData.length }} 行数据</el-tag>
            <el-tag type="success" v-if="validRows > 0">有效: {{ validRows }}</el-tag>
            <el-tag type="warning" v-if="invalidRows > 0">无效: {{ invalidRows }}</el-tag>
          </div>
        </div>

        <!-- 预览表格 -->
        <div class="preview-table-container">
          <el-table
            :data="previewData.slice(0, 20)"
            border
            stripe
            height="400"
            style="width: 100%"
          >
            <el-table-column type="index" label="行号" width="60" />
            <el-table-column
              prop="software_category"
              label="软件类别"
              width="120"
              :class-name="getColumnClass"
            >
              <template #default="{ row }">
                <div :class="getCellClass(row, 'software_category')">
                  {{ row.software_category }}
                </div>
              </template>
            </el-table-column>
            <el-table-column
              prop="test_item_name"
              label="测试项名称"
              width="200"
              :class-name="getColumnClass"
            >
              <template #default="{ row }">
                <div :class="getCellClass(row, 'test_item_name')">
                  {{ row.test_item_name }}
                </div>
              </template>
            </el-table-column>
            <el-table-column
              prop="test_item_description"
              label="测试项描述"
              min-width="250"
              show-overflow-tooltip
            >
              <template #default="{ row }">
                <div :class="getCellClass(row, 'test_item_description')">
                  {{ row.test_item_description }}
                </div>
              </template>
            </el-table-column>
            <el-table-column
              prop="test_method"
              label="测试方法"
              min-width="250"
              show-overflow-tooltip
            >
              <template #default="{ row }">
                <div :class="getCellClass(row, 'test_method')">
                  {{ row.test_method }}
                </div>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="80">
              <template #default="{ row }">
                <el-tag
                  :type="row._valid ? 'success' : 'danger'"
                  size="small"
                >
                  {{ row._valid ? '有效' : '无效' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>

          <div v-if="previewData.length > 20" class="preview-more">
            <el-alert
              :title="`显示前20行，共${previewData.length}行数据`"
              type="info"
              :closable="false"
            />
          </div>
        </div>

        <!-- 错误信息 -->
        <div v-if="validationErrors.length > 0" class="validation-errors">
          <h5>数据验证问题：</h5>
          <el-scrollbar height="120px">
            <div
              v-for="(error, index) in validationErrors.slice(0, 10)"
              :key="index"
              class="error-item"
            >
              <el-tag type="warning" size="small">行{{ error.row }}</el-tag>
              <span>{{ error.message }}</span>
            </div>
          </el-scrollbar>
          <div v-if="validationErrors.length > 10" class="error-more">
            还有 {{ validationErrors.length - 10 }} 个问题...
          </div>
        </div>
      </div>

      <!-- 步骤3：导入结果 -->
      <div v-if="currentStep === 2" class="step-content">
        <div class="result-content">
          <div class="result-icon">
            <el-icon
              size="64"
              :color="importResult.success ? '#67C23A' : '#F56C6C'"
            >
              <component :is="importResult.success ? 'SuccessFilled' : 'CircleCloseFilled'" />
            </el-icon>
          </div>
          
          <div class="result-text">
            <h3>{{ importResult.success ? '导入成功！' : '导入失败！' }}</h3>
            <p>{{ importResult.message }}</p>
          </div>

          <div v-if="importResult.success" class="result-stats">
            <el-descriptions border :column="2">
              <el-descriptions-item label="成功导入">
                <el-tag type="success">{{ importResult.imported || 0 }} 条</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="跳过记录">
                <el-tag type="info">{{ importResult.skipped || 0 }} 条</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="清除原有">
                <el-tag type="warning">{{ importResult.cleared || 0 }} 条</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="总用时">
                <el-tag>{{ importResult.duration || 0 }}ms</el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button
          v-if="currentStep > 0"
          @click="previousStep"
          :disabled="importing"
        >
          上一步
        </el-button>
        
        <el-button @click="handleClose" :disabled="importing">
          {{ currentStep === 2 ? '关闭' : '取消' }}
        </el-button>
        
        <el-button
          v-if="currentStep === 0"
          type="primary"
          @click="nextStep"
          :disabled="!selectedFile"
        >
          下一步
        </el-button>
        
        <el-button
          v-if="currentStep === 1"
          type="primary"
          @click="startImport"
          :loading="importing"
          :disabled="validRows === 0"
        >
          {{ importing ? '导入中...' : '开始导入' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Upload,
  Document,
  Delete,
  QuestionFilled,
  SuccessFilled,
  CircleCloseFilled
} from '@element-plus/icons-vue'
import { databaseManageService } from '@/services/databaseManageService'

// Props
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  file: {
    type: File,
    default: null
  }
})

// Emits
const emit = defineEmits(['update:visible', 'import-success', 'import-error'])

// 响应式数据
const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

const currentStep = ref(0)
const importing = ref(false)
const selectedFile = ref(null)
const uploadRef = ref(null)

// 导入选项
const importOptions = reactive({
  sheetName: '光电需求分析表',
  clearExisting: false,
  skipEmptyRows: true
})

// 预览数据
const previewData = ref([])
const validationErrors = ref([])

// 导入结果
const importResult = reactive({
  success: false,
  message: '',
  imported: 0,
  skipped: 0,
  cleared: 0,
  duration: 0
})

// 计算属性
const validRows = computed(() => {
  return previewData.value.filter(row => row._valid).length
})

const invalidRows = computed(() => {
  return previewData.value.length - validRows.value
})

// 监听props变化
watch(() => props.file, (newFile) => {
  if (newFile) {
    selectedFile.value = newFile
    currentStep.value = 0
  }
}, { immediate: true })

watch(() => props.visible, (visible) => {
  if (visible) {
    resetDialog()
  }
})

// 方法
const resetDialog = () => {
  currentStep.value = 0
  importing.value = false
  selectedFile.value = props.file
  previewData.value = []
  validationErrors.value = []
  importResult.success = false
  importResult.message = ''
  importResult.imported = 0
  importResult.skipped = 0
  importResult.cleared = 0
  importResult.duration = 0
}

const handleFileChange = (file) => {
  selectedFile.value = file.raw
}

const beforeUpload = () => {
  return false // 阻止自动上传
}

const removeFile = () => {
  selectedFile.value = null
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const nextStep = async () => {
  if (currentStep.value === 0) {
    // 验证和预览数据
    await validateAndPreview()
  }
  currentStep.value++
}

const previousStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const validateAndPreview = async () => {
  if (!selectedFile.value) return

  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    if (importOptions.sheetName) {
      formData.append('sheet_name', importOptions.sheetName)
    }

    const response = await databaseManageService.validateExcelImport(formData)
    
    if (response.data.valid) {
      // 解析Excel文件获取预览数据
      const parseResponse = await parseExcelFile(selectedFile.value)
      previewData.value = parseResponse.data
      validationErrors.value = parseResponse.errors || []
      
      // 验证每行数据
      previewData.value.forEach((row, index) => {
        row._valid = validateRow(row, index + 1)
      })
    } else {
      throw new Error(response.data.message)
    }
  } catch (error) {
    ElMessage.error('文件验证失败: ' + error.message)
    throw error
  }
}

const parseExcelFile = async (file) => {
  // 这里应该调用后端API来解析Excel文件
  // 为了演示，我们模拟一些数据
  return {
    data: [
      {
        software_category: '通用',
        test_item_name: '软件初始化测试',
        test_item_description: '测试软件是否能正常初始化',
        test_method: '通过断点调试验证初始化过程'
      },
      {
        software_category: 'CAM',
        test_item_name: '相机驱动测试',
        test_item_description: '测试相机驱动程序功能',
        test_method: '运行相机驱动并检查输出'
      }
    ],
    errors: []
  }
}

const validateRow = (row, rowNumber) => {
  const errors = []
  
  // 必填字段验证
  if (!row.software_category || !row.software_category.trim()) {
    errors.push('软件类别不能为空')
  }
  
  if (!row.test_item_name || !row.test_item_name.trim()) {
    errors.push('测试项名称不能为空')
  }
  
  if (errors.length > 0) {
    validationErrors.value.push({
      row: rowNumber,
      message: errors.join(', ')
    })
    return false
  }
  
  return true
}

const getCellClass = (row, field) => {
  if (!row._valid) {
    if (field === 'software_category' || field === 'test_item_name') {
      if (!row[field] || !row[field].trim()) {
        return 'invalid-cell'
      }
    }
  }
  return ''
}

const getColumnClass = () => {
  return 'preview-column'
}

const startImport = async () => {
  if (!selectedFile.value || validRows.value === 0) return

  importing.value = true
  const startTime = Date.now()

  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    if (importOptions.clearExisting) {
      formData.append('clear_existing', 'true')
    }
    if (importOptions.sheetName) {
      formData.append('sheet_name', importOptions.sheetName)
    }

    const response = await databaseManageService.importExcelRequirements(formData)
    
    // 设置成功结果
    importResult.success = true
    importResult.message = '数据导入成功！'
    importResult.imported = response.data.length || validRows.value
    importResult.skipped = previewData.value.length - validRows.value
    importResult.cleared = importOptions.clearExisting ? response.data.cleared || 0 : 0
    importResult.duration = Date.now() - startTime

    // 发送成功事件
    emit('import-success', response.data)
    
    currentStep.value = 2
    
  } catch (error) {
    // 设置失败结果
    importResult.success = false
    importResult.message = error.message || '导入过程中发生错误'
    importResult.duration = Date.now() - startTime
    
    currentStep.value = 2
    
    emit('import-error', error.message)
  } finally {
    importing.value = false
  }
}

const handleClose = () => {
  if (!importing.value) {
    dialogVisible.value = false
  }
}
</script>

<style scoped>
.import-dialog-content {
  padding: 20px 0;
}

.step-content {
  margin-top: 30px;
  min-height: 400px;
}

.file-upload-area {
  margin-bottom: 30px;
}

.excel-upload {
  width: 100%;
}

.upload-content {
  padding: 60px 0;
  text-align: center;
}

.upload-icon {
  margin-bottom: 20px;
}

.upload-title {
  font-size: 16px;
  color: #303133;
  margin-bottom: 8px;
}

.upload-hint {
  font-size: 14px;
  color: #909399;
}

.file-info {
  margin-top: 20px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-icon {
  color: #409EFF;
}

.file-name {
  flex: 1;
  font-weight: 500;
}

.file-size {
  color: #909399;
  font-size: 12px;
}

.import-options {
  border-top: 1px solid #ebeef5;
  padding-top: 20px;
}

.import-options h4 {
  margin: 0 0 20px 0;
  color: #303133;
}

.help-icon {
  margin-left: 8px;
  color: #909399;
  cursor: help;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.preview-header h4 {
  margin: 0;
  color: #303133;
}

.preview-stats {
  display: flex;
  gap: 8px;
}

.preview-table-container {
  margin-bottom: 20px;
}

.preview-more {
  margin-top: 10px;
}

.validation-errors {
  margin-top: 20px;
  padding: 15px;
  background: #fdf6ec;
  border: 1px solid #fcdcb4;
  border-radius: 4px;
}

.validation-errors h5 {
  margin: 0 0 10px 0;
  color: #e6a23c;
}

.error-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 12px;
}

.error-more {
  margin-top: 10px;
  font-size: 12px;
  color: #909399;
  text-align: center;
}

.invalid-cell {
  color: #f56c6c;
  background: #fef0f0;
  padding: 2px 4px;
  border-radius: 2px;
}

.result-content {
  text-align: center;
  padding: 40px 0;
}

.result-icon {
  margin-bottom: 20px;
}

.result-text h3 {
  margin: 0 0 10px 0;
  font-size: 20px;
}

.result-text p {
  margin: 0 0 30px 0;
  color: #606266;
}

.result-stats {
  max-width: 400px;
  margin: 0 auto;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* 响应式 */
@media (max-width: 768px) {
  .preview-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .preview-stats {
    flex-wrap: wrap;
  }
  
  .result-stats {
    max-width: 100%;
  }
}
</style> 