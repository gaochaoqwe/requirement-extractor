<template>
  <div class="excel-workspace">
    <!-- Excel风格的功能区 -->
    <div class="excel-ribbon">
      <!-- 主功能区 -->
      <div class="ribbon-tabs">
        <div class="ribbon-tab active">
          <span>开始</span>
        </div>
      </div>
      
      <!-- 功能区内容 - 统一的上图标下文字格式 -->
      <div class="ribbon-content">
        <!-- 普通导入：点击后显示 全量/增量 两个选项 -->
        <el-popover
          placement="bottom"
          width="auto"
          trigger="click"
          popper-class="import-popover"
          :popper-style="{ minWidth: 'unset', width: 'auto', maxWidth: 'none', padding: '2px', background: 'transparent', border: 'none', boxShadow: 'none' }"
          :show-arrow="false"
          :offset="4"
          :popper-options="popperOptions"
          @show="updateImportOptionsWidth"
        >
          <template #reference>
            <button ref="importMainBtn" class="ribbon-button success import-main-btn" title="导入包含四个Sheet的Excel文件" :disabled="importingMultiSheet">
              <img src="./assets/import.svg" class="button-icon" alt="普通导入" />
              <span class="button-text" ref="importMainText">普通导入</span>
            </button>
          </template>
          <div class="import-options" :style="{ width: importOptionsWidth + 'px' }">
            <el-upload
              :auto-upload="false"
              :show-file-list="false"
              accept=".xlsx"
              :on-change="(f)=>handleMultiSheetImportFileSelectWithMode(f, 'full')"
            >
              <button class="option-btn option-full" title="清空现有数据，导入新数据">全量导入</button>
            </el-upload>
            <el-upload
              :auto-upload="false"
              :show-file-list="false"
              accept=".xlsx"
              :on-change="(f)=>handleMultiSheetImportFileSelectWithMode(f, 'incremental')"
            >
              <button class="option-btn option-incr" title="保留现有数据，追加新数据">增量导入</button>
            </el-upload>
          </div>
        </el-popover>

        <div class="separator"></div>

        <!-- 导出 -->
        <button class="ribbon-button" @click="exportData" title="导出Excel">
          <img src="./assets/export.svg" class="button-icon" alt="导出" />
          <span class="button-text">导出</span>
        </button>

        <!-- 智能导出 -->
        <button class="ribbon-button intelligent-export-btn" @click="showIntelligentExportDialog" title="智能导出功能">
          <img src="./assets/export.svg" class="button-icon blue-icon" alt="智能导出" />
          <span class="button-text blue-text">智能导出</span>
        </button>

        <div class="separator"></div>

        <!-- 开发工具 -->
        <button class="ribbon-button danger" @click="clearDatabase" title="清空数据库中的所有数据">
          <img src="./assets/refresh.svg" class="button-icon" alt="清空" />
          <span class="button-text">清空数据库</span>
        </button>
      </div>
    </div>

    <!-- Tab页区域 -->
    <div class="tab-container">
      <el-tabs v-model="activeTab" type="card" class="database-tabs">
        <el-tab-pane label="转塔" name="转塔">
          <SevenColsPane :key="`转塔-${refreshKey}`" table="转塔" />
        </el-tab-pane>
        <el-tab-pane label="对抗告警" name="对抗告警">
          <SevenColsPane :key="`对抗告警-${refreshKey}`" table="对抗告警" />
        </el-tab-pane>
        <el-tab-pane label="光雷" name="光雷">
          <SevenColsPane :key="`光雷-${refreshKey}`" table="光雷" />
        </el-tab-pane>
        <el-tab-pane label="吊舱" name="吊舱">
          <SevenColsPane :key="`吊舱-${refreshKey}`" table="吊舱" />
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 导入结果对话框 -->
    <el-dialog
      v-model="importResultDialog.visible"
      title="导入结果"
      width="600px"
      class="import-result-dialog"
      :close-on-click-modal="false"
    >
      <div class="import-result">
        <div class="result-header">
          <el-icon size="24" :color="importResultDialog.success ? '#10b981' : '#ef4444'">
            <Check v-if="importResultDialog.success" />
            <Close v-else />
          </el-icon>
          <h3>{{ importResultDialog.success ? '导入成功' : '导入失败' }}</h3>
        </div>
        
        <div class="result-message">
          {{ importResultDialog.message }}
        </div>
        
        <div class="import-stats" v-if="importResultDialog.sheetsResult">
          <h4 class="sheets-title">各Sheet导入详情</h4>
          <div class="sheets-grid">
            <div 
              v-for="(result, sheetName) in importResultDialog.sheetsResult" 
              :key="sheetName" 
              class="sheet-item"
            >
              <div class="sheet-name">{{ sheetName }}</div>
              <div class="sheet-stats">
                <div class="sheet-stat success" v-if="result.created > 0">
                  <span class="stat-number">{{ result.created }}</span>
                  <span class="stat-label">新增</span>
                </div>
                <div class="sheet-stat warning" v-if="result.deleted > 0">
                  <span class="stat-number">{{ result.deleted }}</span>
                  <span class="stat-label">删除</span>
                </div>
                <div class="sheet-stat info" v-if="result.skipped > 0">
                  <span class="stat-number">{{ result.skipped }}</span>
                  <span class="stat-label">跳过</span>
                </div>
              </div>
            </div>
          </div>
          
          <div class="error-details" v-if="importResultDialog.errorDetails && importResultDialog.errorDetails.length > 0">
            <h4>错误详情：</h4>
            <div class="error-list">
              <div 
                v-for="(error, index) in importResultDialog.errorDetails" 
                :key="index" 
                class="error-item"
              >
                <el-icon color="#ef4444"><Warning /></el-icon>
                <span>{{ error }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="importResultDialog.visible = false">关闭</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 智能导出对话框 -->
    <el-dialog
      v-model="intelligentExportDialog.visible"
      title="智能导出"
      width="500px"
      class="intelligent-export-dialog"
      :close-on-click-modal="false"
    >
      <div class="intelligent-export-form">
        <!-- 类型选择 -->
        <div class="form-item">
          <label class="form-label">选择产品类型：</label>
          <el-select 
            v-model="intelligentExportDialog.selectedType" 
            placeholder="请选择产品类型"
            style="width: 100%"
          >
            <el-option label="转塔" value="转塔" />
            <el-option label="对抗告警" value="对抗告警" />
            <el-option label="光雷" value="光雷" />
            <el-option label="吊舱" value="吊舱" />
          </el-select>
        </div>

        <!-- 软件类型选择 -->
        <div class="form-item" v-if="intelligentExportDialog.availableSoftwareTypes.length > 0">
          <label class="form-label">选择软件类型：</label>
          <el-select 
            v-model="intelligentExportDialog.selectedSoftwareType" 
            placeholder="请选择软件类型"
            style="width: 100%"
          >
            <el-option 
              v-for="softwareType in intelligentExportDialog.availableSoftwareTypes" 
              :key="softwareType"
              :label="softwareType" 
              :value="softwareType" 
            />
          </el-select>
        </div>

        <!-- 文件上传 -->
        <div class="form-item">
          <label class="form-label">上传Excel文档：</label>
          <el-upload
            ref="intelligentExportUpload"
            :auto-upload="false"
            :show-file-list="true"
            :limit="1"
            accept=".xlsx,.xls"
            :on-change="handleIntelligentExportFileChange"
            :on-remove="handleIntelligentExportFileRemove"
            class="upload-area"
          >
            <el-button type="primary" :icon="Upload">选择文件</el-button>
            <template #tip>
              <div class="el-upload__tip">
                只能上传 xlsx/xls 文件，且文档应包含6个sheet，其中第4个sheet为需求分析表，第5个sheet为测试用例单
              </div>
            </template>
          </el-upload>
        </div>

        <!-- 处理说明 -->
        <div class="form-item">
          <div class="process-description">
            <h4>处理说明：</h4>
            <ul>
              <li>系统将根据您选择的产品类型和软件类型，从对应的组织资产库中匹配数据</li>
              <li>首先匹配您表单中需求分析表的"测试项名称"列</li>
              <li>然后匹配组织资产库中的"软件类别"列与您选择的软件类型</li>
              <li><strong>注意：</strong>组织资产库中标记为"通用"的测试项将匹配任何软件类型</li>
              <li>将匹配到的"测试内容"合并填充到"测试项描述"列</li>
              <li>将匹配到的"测试方法"合并填充到"测试方法"列</li>
              <li>在测试用例单中，为每个匹配项创建对应的用例行</li>
            </ul>
          </div>
        </div>

        <!-- 进度显示 -->
        <div class="form-item" v-if="intelligentExportDialog.processing">
          <div class="progress-container">
            <div class="progress-header">
              <span class="progress-text">{{ intelligentExportDialog.progressText }}</span>
              <span class="progress-percentage">{{ intelligentExportDialog.progressPercentage }}%</span>
            </div>
            <el-progress 
              :percentage="intelligentExportDialog.progressPercentage" 
              :stroke-width="12"
              :show-text="false"
              :color="progressColor"
              class="smooth-progress"
            />
          </div>
        </div>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="intelligentExportDialog.visible = false">
            {{ intelligentExportDialog.canDownload ? '关闭' : '取消' }}
          </el-button>
          
          <!-- 处理按钮 -->
          <el-button 
            v-if="!intelligentExportDialog.canDownload"
            type="primary" 
            @click="processIntelligentExport"
            :loading="intelligentExportDialog.processing"
            :disabled="!intelligentExportDialog.selectedType || !intelligentExportDialog.selectedSoftwareType || !intelligentExportDialog.selectedFile"
          >
            {{ intelligentExportDialog.processing ? '处理中...' : '开始处理' }}
          </el-button>
          
          <!-- 下载按钮 -->
          <el-button 
            v-if="intelligentExportDialog.canDownload"
            type="success" 
            :icon="Download"
            @click="downloadExportResult"
          >
            下载文件
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Check, Close, Warning, Upload, Download } from '@element-plus/icons-vue'
import SevenColsPane from './components/SevenColsPane.vue'
import { databaseManageService } from '@/services/databaseManageService'

// 当前活跃的tab
const activeTab = ref('转塔')

// 刷新key，用于强制重新渲染组件
const refreshKey = ref(0)

// 导入相关状态
const importingMultiSheet = ref(false)
const importOptionsWidth = ref(120)
const importMainText = ref(null)
const importMainBtn = ref(null)
const popperOptions = ref({
  modifiers: [
    { name: 'offset', options: { offset: [0, 4] } }
  ]
})

// 导入结果对话框
const importResultDialog = reactive({
  visible: false,
  success: false,
  message: '',
  stats: null,
  errorDetails: [],
  sheetsResult: null
})

// 智能导出对话框
const intelligentExportDialog = reactive({
  visible: false,
  selectedType: '',
  selectedSoftwareType: '',
  selectedFile: null,
  processing: false,
  progressText: '准备处理...',
  progressPercentage: 0,
  canDownload: false,
  taskId: null,
  filename: null,
  availableSoftwareTypes: []
})

// 产品与软件类型的映射关系
const productSoftwareMapping = {
  '转塔': ['主控', '随动', '图像', '红外', '激光'],
  '对抗告警': ['告警主控', '告警红外', '分色滤光', '目标检测', '拼接', '干扰主控', '伺服', '干扰红外', '干扰图像', '干扰激光'],
  '光雷': ['主控', '随动', '红外', '图像', '激光'],
  '吊舱': ['主控', '随动', '图像', '红外', '激光']
}

// 进度条颜色计算
const progressColor = computed(() => {
  const percentage = intelligentExportDialog.progressPercentage
  if (percentage < 30) return '#f56c6c' // 红色 - 开始阶段
  if (percentage < 60) return '#e6a23c' // 橙色 - 处理阶段
  if (percentage < 90) return '#409eff' // 蓝色 - 接近完成
  return '#67c23a' // 绿色 - 完成
})

// 更新导入选项宽度并根据“普通导入”文字水平居中气泡
const updateImportOptionsWidth = async () => {
  await nextTick()
  const textEl = importMainText.value
  const btnEl = importMainBtn.value
  if (!textEl || !btnEl) return

  const textRect = textEl.getBoundingClientRect()
  const btnRect = btnEl.getBoundingClientRect()

  // 文案宽度 + 适当余量，避免换行或裁切
  const padding = 12 // 左右各6px
  importOptionsWidth.value = Math.ceil(textRect.width) + padding

  // 计算水平偏移（skidding）：让气泡中心对准文字中心
  const textCenterX = textRect.left + textRect.width / 2
  const btnCenterX = btnRect.left + btnRect.width / 2
  const skidding = Math.round(textCenterX - btnCenterX)

  popperOptions.value = {
    modifiers: [
      { name: 'offset', options: { offset: [skidding, 4] } }
    ]
  }
}

// 处理多Sheet导入文件选择
const handleMultiSheetImportFileSelectWithMode = async (fileObj, mode) => {
  if (!fileObj || !fileObj.raw) {
    ElMessage.error('请选择有效的Excel文件')
    return
  }
  
  try {
    importingMultiSheet.value = true
    
  const formData = new FormData()
    formData.append('file', fileObj.raw)
    
    const response = await databaseManageService.importMultiSheet7Cols(formData, mode)

    // 显示导入结果
    importResultDialog.visible = true
    importResultDialog.success = true
    importResultDialog.message = response.message || '文件导入成功'
    importResultDialog.stats = response.stats || null
    importResultDialog.errorDetails = response.errors || []
    importResultDialog.sheetsResult = response.sheets || null
    
    ElMessage.success('导入成功')
    
    // 触发当前tab页的数据刷新
    refreshCurrentTabData()
    
  } catch (error) {
    console.error('导入失败:', error)
    
    // 显示错误结果
    importResultDialog.visible = true
    importResultDialog.success = false
    importResultDialog.message = error.response?.data?.detail || error.message || '导入失败'
    importResultDialog.stats = error.response?.data?.stats || null
    importResultDialog.errorDetails = error.response?.data?.errors || []
    
    ElMessage.error('导入失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    importingMultiSheet.value = false
  }
}

// 导出数据
const exportData = async () => {
  try {
    const response = await databaseManageService.exportSevenCols({
      table: activeTab.value
    })
    
    // 创建下载链接
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${activeTab.value}_数据库导出.xlsx`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 刷新当前tab页数据
const refreshCurrentTabData = () => {
  // 使用key强制重新渲染SevenColsPane组件
  refreshKey.value++
}

// 清空数据库
const clearDatabase = async () => {
  try {
    await ElMessageBox.confirm('此操作将清空数据库中的所有数据（保留表结构），是否继续？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const res = await databaseManageService.resetDatabase()
    ElMessage.success(res.message || '数据库清空成功')
    
    // 清空数据库后刷新当前tab数据
    refreshCurrentTabData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清空数据库失败:', error)
      ElMessage.error('清空失败: ' + (error.response?.data?.detail || error.message))
    }
  }
}

// 监听产品类型变化，更新软件类型列表
watch(() => intelligentExportDialog.selectedType, (newType) => {
  // 清空之前的软件类型选择
  intelligentExportDialog.selectedSoftwareType = ''
  
  // 根据产品类型更新可用的软件类型列表
  if (newType && productSoftwareMapping[newType]) {
    intelligentExportDialog.availableSoftwareTypes = productSoftwareMapping[newType]
  } else {
    intelligentExportDialog.availableSoftwareTypes = []
  }
})

// 显示智能导出对话框
const showIntelligentExportDialog = () => {
  intelligentExportDialog.visible = true
  intelligentExportDialog.selectedType = ''
  intelligentExportDialog.selectedSoftwareType = ''
  intelligentExportDialog.selectedFile = null
  intelligentExportDialog.processing = false
  intelligentExportDialog.progressPercentage = 0
  intelligentExportDialog.progressText = '准备处理...'
  intelligentExportDialog.canDownload = false
  intelligentExportDialog.taskId = null
  intelligentExportDialog.filename = null
  intelligentExportDialog.availableSoftwareTypes = []
}

// 处理智能导出文件选择
const handleIntelligentExportFileChange = (file) => {
  intelligentExportDialog.selectedFile = file
}

// 处理智能导出文件移除
const handleIntelligentExportFileRemove = () => {
  intelligentExportDialog.selectedFile = null
}

// 手动下载导出结果
const downloadExportResult = async () => {
  if (!intelligentExportDialog.taskId) {
    ElMessage.error('无法获取下载信息')
    return
  }

  try {
    const downloadResponse = await databaseManageService.downloadExportResult(intelligentExportDialog.taskId)
    
    // 创建下载链接
    const blob = new Blob([downloadResponse.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = intelligentExportDialog.filename || '智能导出结果.xlsx'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('文件下载完成')
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 处理智能导出
const processIntelligentExport = async () => {
  if (!intelligentExportDialog.selectedType || !intelligentExportDialog.selectedSoftwareType || !intelligentExportDialog.selectedFile) {
    ElMessage.warning('请选择产品类型、软件类型并上传文件')
    return
  }

  intelligentExportDialog.processing = true
  intelligentExportDialog.progressPercentage = 0
  intelligentExportDialog.progressText = '准备处理...'
  
  let taskId = null
  let progressTimer = null
  
  try {
    // 更新进度函数（平滑过渡）
    const updateProgress = (incomingPercentage, text) => {
      // 单调递增：不允许回退
      const currentPercentage = intelligentExportDialog.progressPercentage
      const targetPercentage = Math.max(incomingPercentage ?? 0, currentPercentage)
      
      // 始终更新提示文本
      intelligentExportDialog.progressText = text
      
      if (targetPercentage === currentPercentage) {
        console.log(`🎯 进度保持: ${currentPercentage}% - ${text}`)
        return
      }
      
      // 平滑更新进度条
      const step = (targetPercentage - currentPercentage) / 10
      
      if (Math.abs(targetPercentage - currentPercentage) > 5) {
        // 如果差距较大，使用动画过渡
        let current = currentPercentage
        const animate = () => {
          current += step
          if (current < targetPercentage) {
            intelligentExportDialog.progressPercentage = Math.round(current)
            setTimeout(animate, 50) // 每50ms更新一次
          } else {
            intelligentExportDialog.progressPercentage = targetPercentage
          }
        }
        animate()
      } else {
        // 差距较小，直接更新
        intelligentExportDialog.progressPercentage = targetPercentage
      }
      
      console.log(`🎯 进度更新: ${targetPercentage}% - ${text}`)
    }

    updateProgress(5, '正在上传文件并启动任务...')
    
    const formData = new FormData()
    formData.append('file', intelligentExportDialog.selectedFile.raw)
    formData.append('selected_type', intelligentExportDialog.selectedType)
    formData.append('selected_software_type', intelligentExportDialog.selectedSoftwareType)

    // 启动异步任务
    const taskResponse = await databaseManageService.intelligentExportAsync(formData)
    taskId = taskResponse.data.task_id
    
    updateProgress(10, '任务已启动，正在处理...')
    
    // 延迟开始查询，让用户看到初始进度
    setTimeout(() => {
      // 定期查询进度
      progressTimer = setInterval(async () => {
      try {
        const progressResponse = await databaseManageService.getExportProgress(taskId)
        const progressData = progressResponse.data
        
        console.log('📊 进度查询响应:', progressData)
        
        updateProgress(progressData.progress, progressData.message)
        
        if (progressData.status === 'completed') {
          // 任务完成，清除定时器
          clearInterval(progressTimer)
          progressTimer = null
          
          updateProgress(100, '处理完成！可以下载文件')
          
          // 设置下载状态
          intelligentExportDialog.canDownload = true
          intelligentExportDialog.taskId = taskId
          intelligentExportDialog.filename = progressData.filename || `智能导出_${intelligentExportDialog.selectedType}_${String(taskId).slice(0, 8)}.xlsx`
          intelligentExportDialog.processing = false
          
          ElMessage.success('智能导出完成，可以下载文件')
          
        } else if (progressData.status === 'error') {
          // 任务失败
          clearInterval(progressTimer)
          progressTimer = null
          throw new Error(progressData.message || '导出任务失败')
        }
        
      } catch (progressError) {
        console.error('查询进度失败:', progressError)
        // 如果是网络错误或服务器错误，继续尝试（给后台处理一些时间）
        if (progressError.message.includes('Network Error') || 
            progressError.message.includes('Request failed with status code 500') ||
            progressError.message.includes('Request failed with status code 404')) {
          console.log('服务器错误，继续尝试查询进度...')
          // 可能是任务还没开始或者服务器正在处理，继续等待
        } else {
          // 其他严重错误，停止查询
          clearInterval(progressTimer)
          progressTimer = null
          throw progressError
        }
      }
        }, 5000) // 每5秒查询一次进度（适合大量用例处理）
      
      // 注意：定时器在finally中会被清理
    }, 500) // 首次延迟0.5秒再开始查询
    
    } catch (error) {
    console.error('智能导出失败:', error)
    ElMessage.error('智能导出失败: ' + (error.response?.data?.detail || error.message))
    
    // 清除定时器
    if (progressTimer) {
      clearInterval(progressTimer)
      progressTimer = null
    }
    // 保持进度条停留片刻再重置
    setTimeout(() => {
      intelligentExportDialog.processing = false
      intelligentExportDialog.canDownload = false
      intelligentExportDialog.taskId = null
      intelligentExportDialog.filename = null
      setTimeout(() => {
        intelligentExportDialog.progressPercentage = 0
        intelligentExportDialog.progressText = '准备处理...'
      }, 300)
    }, 1500)
  } finally {
    // 不在finally里立刻清空，等待完成/失败分支自行处理
  }
}

onMounted(() => {
  // 窗口尺寸变化时重算，保持对齐
  window.addEventListener('resize', updateImportOptionsWidth)
})

import { onBeforeUnmount } from 'vue'
onBeforeUnmount(() => {
  window.removeEventListener('resize', updateImportOptionsWidth)
})
</script>

<style scoped>
.excel-workspace {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f0f0f0;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* 图标样式 */
.icon {
  width: 16px;
  height: 16px;
  filter: brightness(0) saturate(100%);
}

.menu-icon {
  width: 14px;
  height: 14px;
  filter: brightness(0) saturate(100%);
}

.result-icon {
  width: 32px;
  height: 32px;
}

.result-icon.success {
  filter: brightness(0) saturate(100%) invert(48%) sepia(79%) saturate(2476%) hue-rotate(86deg) brightness(118%) contrast(119%);
}

.result-icon.error {
  filter: brightness(0) saturate(100%) invert(17%) sepia(90%) saturate(7471%) hue-rotate(3deg) brightness(97%) contrast(118%);
}

.error-icon {
  width: 16px;
  height: 16px;
  filter: brightness(0) saturate(100%) invert(64%) sepia(98%) saturate(1204%) hue-rotate(5deg) brightness(101%) contrast(101%);
}

/* Excel功能区样式 */
.excel-ribbon {
  background: #f8f9fa;
  border-bottom: 1px solid #d1d5db;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.ribbon-tabs {
  display: flex;
  background: #e5e7eb;
  border-bottom: 1px solid #d1d5db;
}

.ribbon-tab {
  padding: 8px 20px;
  cursor: pointer;
  border-right: 1px solid #d1d5db;
  font-size: 13px;
  font-weight: 500;
}

.ribbon-tab.active {
  background: #f8f9fa;
  border-bottom: 2px solid #3b82f6;
  color: #3b82f6;
}

.ribbon-content {
  display: flex;
  padding: 8px 16px;
  gap: 8px;
  align-items: center;
  min-height: 80px;
}

/* Tab页容器样式 */
.tab-container {
  flex: 1;
  padding: 16px;
  background: white;
  overflow: visible; /* 🚀 修复：改为visible，确保分页组件完全可见 */
  min-height: 0; /* 🚀 允许flex子项收缩 */
}

.database-tabs {
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0; /* 🚀 允许flex子项收缩 */
}

.database-tabs .el-tabs__content {
  flex: 1;
  overflow: visible; /* 🚀 修复：改为visible，避免分页组件被裁剪 */
  height: calc(100vh - 200px); /* 🚀 调整高度计算，为分页组件预留空间 */
  position: relative; /* 🚀 确保正确的定位上下文 */
}

.database-tabs .el-tab-pane {
  height: 100%;
  overflow: visible; /* 🚀 修复：允许内容可见，避免分页组件被裁剪 */
  display: flex;
  flex-direction: column; /* 🚀 使用flex布局确保分页组件显示 */
}

.database-tabs .el-tabs__header {
  margin: 0 0 16px 0;
}

.database-tabs .el-tabs__nav-wrap {
  background: #f8f9fa;
  border-radius: 8px 8px 0 0;
}

.database-tabs .el-tabs__item {
  font-weight: 500;
  font-size: 14px;
  padding: 0 24px;
  height: 40px;
  line-height: 40px;
}

.database-tabs .el-tabs__item.is-active {
  background: white;
  border-bottom: 2px solid #409eff;
}

/* 统一的按钮样式 - 上图标下文字 */
.ribbon-button {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 6px 8px;
  border: 1px solid transparent;
  border-radius: 4px;
  background: transparent;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 60px;
  min-height: 60px;
  font-size: 11px;
  color: #374151;
}

.ribbon-button:hover:not(:disabled) {
  background: #e5e7eb;
  border-color: #d1d5db;
}

.ribbon-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 大按钮样式 */
.ribbon-button.large {
  min-width: 80px;
  min-height: 70px;
  padding: 8px 12px;
}

/* 按钮状态样式 */
.ribbon-button.success {
  color: #059669;
}

.ribbon-button.success:hover:not(:disabled) {
  background: #f0fdf4;
  border-color: #bbf7d0;
}

.ribbon-button.primary {
  color: #3b82f6;
}

.ribbon-button.primary:hover:not(:disabled) {
  background: #eff6ff;
  border-color: #bfdbfe;
}

.ribbon-button.danger {
  color: #dc2626;
}

.ribbon-button.danger:hover:not(:disabled) {
  background: #fef2f2;
  border-color: #fecaca;
}

.ribbon-button.highlight {
  background: #fef3c7;
  border-color: #fbbf24;
  color: #92400e;
}

.ribbon-button.active {
  background: #dbeafe;
  border-color: #3b82f6;
  color: #1d4ed8;
}

/* 图标样式 */
.button-icon {
  width: 24px;
  height: 24px;
  margin-bottom: 4px;
  filter: brightness(0) saturate(100%);
}

.large-icon {
  width: 32px;
  height: 32px;
}

/* 根据按钮状态调整图标颜色 */
.ribbon-button.success .button-icon {
  filter: brightness(0) saturate(100%) invert(48%) sepia(79%) saturate(2476%) hue-rotate(86deg) brightness(118%) contrast(119%);
}

.ribbon-button.primary .button-icon {
  filter: brightness(0) saturate(100%) invert(37%) sepia(99%) saturate(1798%) hue-rotate(213deg) brightness(97%) contrast(94%);
}

.ribbon-button.danger .button-icon {
  filter: brightness(0) saturate(100%) invert(17%) sepia(90%) saturate(7471%) hue-rotate(3deg) brightness(97%) contrast(118%);
}

/* 普通导入弹出层及选项按钮可视样式 */
/* 覆盖 Element Plus 默认最小宽度，避免右侧空白 */
.el-popover.import-popover {
  min-width: unset !important;
  width: fit-content !important;
  max-width: none !important;
  padding: 2px !important;
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}

.import-popover {
  padding: 4px !important;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  background: rgba(255, 255, 255, 0.95) !important;
  backdrop-filter: blur(8px);
  border: 1px solid rgba(0, 0, 0, 0.1) !important;
}

.import-popover .import-options {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: stretch;
  margin: 0 auto;
  padding: 0;
}

.import-popover .option-btn {
  width: 100%;
  max-width: 100%;
  height: 24px;
  padding: 0 8px;
  font-size: 11px;
  font-weight: 500;
  line-height: 24px;
  white-space: nowrap;
  color: #374151;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  background: rgba(248, 250, 252, 0.8);
  cursor: pointer;
  text-align: center;
  transition: all .15s ease;
}

.import-popover .option-btn:hover {
  background: rgba(238, 242, 255, 0.9);
  border-color: rgba(199, 210, 254, 0.8);
  color: #1e40af;
  transform: translateY(-1px);
}

/* 语义配色：在悬浮/聚焦时区分全量与增量 */
.import-popover .option-full:hover,
.import-popover .option-full:focus-visible {
  background: rgba(236, 253, 245, 0.9);
  border-color: rgba(167, 243, 208, 0.8);
  color: #065f46;
  transform: translateY(-1px);
}

.import-popover .option-incr:hover,
.import-popover .option-incr:focus-visible {
  background: rgba(255, 251, 235, 0.9);
  border-color: rgba(253, 230, 138, 0.8);
  color: #92400e;
  transform: translateY(-1px);
}

/* 可访问焦点态 */
.import-popover .option-btn:focus-visible {
  outline: 2px solid rgba(59, 130, 246, 0.5); /* 蓝色可视焦点 */
  outline-offset: 1px;
}

.ribbon-button.highlight .button-icon {
  filter: brightness(0) saturate(100%) invert(64%) sepia(98%) saturate(1204%) hue-rotate(5deg) brightness(101%) contrast(101%);
}

.ribbon-button.active .button-icon {
  filter: brightness(0) saturate(100%) invert(20%) sepia(95%) saturate(2893%) hue-rotate(214deg) brightness(99%) contrast(94%);
}

/* 按钮文字 */
.button-text {
  font-size: 11px;
  line-height: 1.2;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

/* 分隔线 */
.separator {
  width: 1px;
  height: 50px;
  background: #d1d5db;
  margin: 0 4px;
}

/* 上传组件包装 */
.upload-wrapper {
  display: contents;
}

.upload-wrapper :deep(.el-upload) {
  display: contents;
}

/* 搜索对话框样式 */
.search-dialog {
  font-family: inherit;
}

.search-dialog :deep(.el-dialog__body) {
  padding: 20px 24px 0;
}

.search-dialog :deep(.el-dialog__footer) {
  padding: 16px 24px 20px;
  border-top: 1px solid #e5e7eb;
}

.search-form {
  padding: 0;
}

.search-field {
  margin-bottom: 20px;
}

.search-label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.search-input {
  width: 100%;
}

.search-options {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.search-checkbox {
  font-size: 14px;
}

.search-results {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
  border: 1px solid #86efac;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.result-icon.success {
  color: #16a34a;
  font-size: 16px;
}

.result-info {
  font-size: 14px;
  color: #16a34a;
  font-weight: 600;
}

.result-current {
  font-weight: 500;
  color: #059669;
}

.search-no-results {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #fef2f2 0%, #fef7f7 100%);
  border: 1px solid #fca5a5;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.result-icon.error {
  color: #dc2626;
  font-size: 16px;
}

.no-result-info {
  font-size: 14px;
  color: #dc2626;
  font-weight: 600;
}

.search-action-buttons {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.search-btn.primary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 20px;
  font-weight: 600;
  border-radius: 8px;
}

.nav-buttons {
  display: flex;
  gap: 4px;
}

.search-btn.nav {
  width: 40px;
  height: 36px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
}

.search-dialog-footer {
  display: flex;
  justify-content: flex-end;
  margin: 0;
}

.close-btn {
  padding: 8px 20px;
  border-radius: 6px;
}

/* 名称框和公式栏 */
.formula-bar {
  display: flex;
  background: white;
  border-bottom: 1px solid #d1d5db;
  height: 32px;
}

.name-box {
  width: 80px;
  border-right: 1px solid #d1d5db;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  background: #f8f9fa;
}

.formula-input {
  flex: 1;
  display: flex;
  align-items: center;
}

.formula-input .el-input {
  border: none;
  border-radius: 0;
}

/* 表格样式 */
.excel-table-wrapper {
  flex: 1;
  overflow: hidden;
  background: white;
  margin: 0;
}

.table-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.column-headers {
  display: flex;
  background: #f8f9fa;
  border-bottom: 2px solid #d1d5db;
  position: sticky;
  top: 0;
  z-index: 10;
}

.corner-cell {
  width: 50px;
  height: 32px;
  border-right: 1px solid #d1d5db;
  background: #e5e7eb;
}

.column-header {
  height: 32px;
  border-right: 1px solid #d1d5db;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 12px;
  position: relative;
  cursor: pointer;
  user-select: none;
  background: #f8f9fa;
  transition: background-color 0.2s;
}

.column-header:hover {
  background: #e5e7eb;
}

.column-header.selected {
  background: #dbeafe;
  color: #3b82f6;
}

.column-resizer {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  cursor: col-resize;
  background: transparent;
}

.column-resizer:hover {
  background: #3b82f6;
}

.table-body {
  flex: 1;
  overflow: auto;
}

.table-row {
  display: flex;
  border-bottom: 1px solid #e5e7eb;
  transition: background-color 0.2s;
}

.table-row:hover {
  background: #f8f9fa;
}

.table-row.selected {
  background: #dbeafe;
}

.table-row.search-highlight {
  background: #fef3c7;
}

.row-number {
  width: 50px;
  height: 32px;
  border-right: 1px solid #d1d5db;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  color: #6b7280;
  background: #f8f9fa;
  cursor: pointer;
  user-select: none;
}

.row-number.selected {
  background: #dbeafe;
  color: #3b82f6;
  font-weight: 600;
}

.row-number:hover {
  background: #e5e7eb;
}

.row-number.selected:hover {
  background: #bfdbfe;
}

.table-cell {
  height: 32px;
  border-right: 1px solid #e5e7eb;
  position: relative;
  cursor: cell;
  display: flex;
  align-items: stretch;
}

.table-cell.selected {
  background: #dbeafe;
  outline: 2px solid #3b82f6;
  z-index: 5;
}

.table-cell.editing {
  background: white;
  outline: 2px solid #10b981;
  z-index: 10;
}

.table-cell.search-match {
  background: #fbbf24;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.cell-content {
  padding: 4px 8px;
  width: 100%;
  display: flex;
  align-items: flex-start;
  font-size: 12px;
  line-height: 1.4;
  overflow: hidden;
  word-wrap: break-word;
  word-break: break-all;
}

.cell-content.auto-wrap {
  white-space: normal;
  overflow-wrap: break-word;
}

.wrapped-text {
  white-space: normal;
  word-wrap: break-word;
  word-break: break-all;
  overflow-wrap: break-word;
}

.multiline-content {
  width: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 2px;
}

.text-line {
  font-size: 12px;
  line-height: 1.3;
  padding: 1px 0;
  border-left: 2px solid transparent;
  padding-left: 4px;
}

.text-line:not(:last-child) {
  border-bottom: 1px solid #f3f4f6;
}

.cell-editor {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 15;
}

.cell-editor .el-textarea {
  height: 100%;
}

.cell-editor .el-textarea__inner {
  border: none;
  border-radius: 0;
  box-shadow: 0 0 0 2px #10b981;
  resize: none;
  font-size: 12px;
  line-height: 1.4;
}

/* 右键菜单 */
.context-menu {
  position: fixed;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  min-width: 180px;
  padding: 4px 0;
  font-size: 13px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  cursor: pointer;
  transition: background-color 0.2s;
  position: relative;
}

.menu-item:hover:not(.disabled) {
  background: #f3f4f6;
}

.menu-item.disabled {
  color: #9ca3af;
  cursor: not-allowed;
}

.menu-item.danger {
  color: #dc2626;
}

.menu-item.danger:hover {
  background: #fef2f2;
}

.shortcut {
  margin-left: auto;
  font-size: 11px;
  color: #6b7280;
}

.menu-separator {
  height: 1px;
  background: #e5e7eb;
  margin: 4px 0;
}

/* 状态栏 */
.status-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 16px;
  background: #f8f9fa;
  border-top: 1px solid #d1d5db;
  font-size: 12px;
  color: #6b7280;
  height: 28px;
}

/* 导入结果对话框 */
.import-result-dialog {
  font-family: inherit;
}

.import-result {
  padding: 16px 0;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.result-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.result-message {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 20px;
}

.import-stats {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.stat-item {
  text-align: center;
  padding: 12px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.stat-item.success {
  border-color: #10b981;
  background: #f0fdf4;
}

.stat-item.primary {
  border-color: #3b82f6;
  background: #eff6ff;
}

.stat-item.danger {
  border-color: #ef4444;
  background: #fef2f2;
}

.stat-number {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 4px;
}

.stat-item.success .stat-number {
  color: #10b981;
}

.stat-item.primary .stat-number {
  color: #3b82f6;
}

.stat-item.danger .stat-number {
  color: #ef4444;
}

.stat-label {
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
}

/* Sheet详情样式 */
.sheets-title {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #374151;
}

.sheets-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.sheet-item {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 12px;
  border: 1px solid #e5e7eb;
}

.sheet-name {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
  text-align: center;
}

.sheet-stats {
  display: flex;
  justify-content: center;
  gap: 8px;
  flex-wrap: wrap;
}

.sheet-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 4px 8px;
  border-radius: 4px;
  min-width: 40px;
}

.sheet-stat.success {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
}

.sheet-stat.warning {
  background: #fffbeb;
  border: 1px solid #fde68a;
}

.sheet-stat.info {
  background: #eff6ff;
  border: 1px solid #bfdbfe;
}

.sheet-stat .stat-number {
  font-size: 16px;
  font-weight: 700;
  line-height: 1;
}

.sheet-stat.success .stat-number {
  color: #16a34a;
}

.sheet-stat.warning .stat-number {
  color: #d97706;
}

.sheet-stat.info .stat-number {
  color: #2563eb;
}

.sheet-stat .stat-label {
  font-size: 10px;
  color: #6b7280;
  font-weight: 500;
  margin-top: 2px;
}

.error-details h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.error-list {
  max-height: 200px;
  overflow-y: auto;
  background: white;
  border-radius: 4px;
  border: 1px solid #e5e7eb;
}

.error-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-bottom: 1px solid #f3f4f6;
  font-size: 12px;
}

.error-item:last-child {
  border-bottom: none;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 滚动条样式 */
.table-body::-webkit-scrollbar,
.error-list::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.table-body::-webkit-scrollbar-track,
.error-list::-webkit-scrollbar-track {
  background: #f3f4f6;
}

.table-body::-webkit-scrollbar-thumb,
.error-list::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 4px;
}

.table-body::-webkit-scrollbar-thumb:hover,
.error-list::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .ribbon-content {
    gap: 16px;
  }
  
  .ribbon-group {
    padding-right: 16px;
  }
}

@media (max-width: 768px) {
  .ribbon-content {
    flex-wrap: wrap;
    gap: 12px;
  }
  
  .search-box {
    width: 150px;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* 智能导出对话框样式 */
.intelligent-export-dialog .intelligent-export-form {
  padding: 20px 0;
}

.intelligent-export-dialog .form-item {
  margin-bottom: 24px;
}

.intelligent-export-dialog .form-label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #374151;
  font-size: 14px;
}

.intelligent-export-dialog .upload-area {
  width: 100%;
}

.intelligent-export-dialog .upload-area .el-upload {
  width: 100%;
}

.intelligent-export-dialog .upload-area .el-upload-dragger {
  width: 100%;
  height: auto;
  padding: 20px;
  border: 2px dashed #d1d5db;
  border-radius: 6px;
  background: #f9fafb;
  transition: all 0.3s ease;
}

.intelligent-export-dialog .upload-area .el-upload-dragger:hover {
  border-color: #3b82f6;
  background: #eff6ff;
}

.intelligent-export-dialog .process-description {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 16px;
}

.intelligent-export-dialog .process-description h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.intelligent-export-dialog .process-description ul {
  margin: 0;
  padding-left: 20px;
  color: #64748b;
  font-size: 13px;
  line-height: 1.5;
}

.intelligent-export-dialog .process-description li {
  margin-bottom: 4px;
}

.intelligent-export-dialog .dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 智能导出按钮样式 */
.ribbon-button.intelligent-export-btn {
  background: white;
  color: #374151;
  border: 1px solid #d1d5db;
}

.ribbon-button.intelligent-export-btn:hover {
  background: #f9fafb;
  border-color: #3b82f6;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
}

.ribbon-button.intelligent-export-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.1);
}

/* 蓝色图标和文字 */
.blue-icon {
  filter: hue-rotate(200deg) saturate(2) brightness(0.8);
}

/* 智能导出进度条样式 */
.progress-container {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 20px;
  margin: 16px 0;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.progress-text {
  font-size: 14px;
  color: #374151;
  font-weight: 500;
}

.progress-percentage {
  font-size: 16px;
  color: #1f2937;
  font-weight: 600;
}

.smooth-progress {
  transition: all 0.3s ease-in-out;
}

/* Element Plus 进度条样式覆盖 */
.smooth-progress :deep(.el-progress-bar__outer) {
  background-color: #e5e7eb;
  border-radius: 10px;
  overflow: hidden;
}

.smooth-progress :deep(.el-progress-bar__inner) {
  border-radius: 10px;
  transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  background: linear-gradient(90deg, var(--el-color-primary) 0%, var(--el-color-primary-light-3) 100%);
  position: relative;
  overflow: hidden;
}

.smooth-progress :deep(.el-progress-bar__inner)::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(
    90deg, 
    transparent 0%, 
    rgba(255, 255, 255, 0.3) 50%, 
    transparent 100%
  );
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

.blue-text {
  color: #3b82f6 !important;
  font-weight: 500;
}

/* 进度显示样式 */
.progress-container {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 16px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.progress-text {
  font-size: 14px;
  color: #475569;
  font-weight: 500;
}

.progress-percentage {
  font-size: 14px;
  color: #3b82f6;
  font-weight: 600;
}
</style>