<template>
  <div class="enhanced-static-analysis-filter">
    <div class="header">
      <h2>静态分析问题过滤工具 - 增强版</h2>
      <p class="description">上传静态分析工具扫描结果和代码库，智能过滤并生成格式化的问题单</p>
    </div>

    <!-- 文件上传区域 -->
    <div v-if="!processing && !completed && !showRulesSelection" class="upload-section">
      <!-- Excel文件上传 -->
      <div class="upload-group">
        <h3>📊 静态分析结果文件</h3>
        <el-upload
          ref="excelUploadRef"
          class="upload-dragger"
          drag
          :auto-upload="false"
          :limit="1"
          accept=".xlsx,.xls"
          :on-change="handleExcelFileChange"
          :file-list="excelFileList"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将静态分析结果文件拖到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持 .xlsx/.xls 格式，文件大小不超过50MB
            </div>
          </template>
        </el-upload>
      </div>

      <!-- 代码库上传 -->
      <div class="upload-group">
        <h3>📁 代码库文件（可选）</h3>
        <el-upload
          ref="codebaseUploadRef"
          class="upload-dragger"
          drag
          :auto-upload="false"
          :limit="1"
          accept=".zip,.rar,.7z"
          :on-change="handleCodebaseFileChange"
          :file-list="codebaseFileList"
        >
          <el-icon class="el-icon--upload"><folder-add /></el-icon>
          <div class="el-upload__text">
            将代码库压缩文件拖到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持 .zip/.rar/.7z 格式，用于AI智能分析不确定规则的问题
            </div>
          </template>
        </el-upload>
        <div class="codebase-notice">
          <el-alert
            title="代码库说明"
            type="info"
            description="上传代码库后，AI将对不确定规则的问题进行深度分析，提高过滤准确性"
            :closable="false"
            show-icon
          />
        </div>
      </div>

      <!-- 过滤关键字配置 -->
      <div class="filter-config">
        <el-form :model="filterForm" label-width="120px">
          <el-form-item label="过滤关键字">
            <el-input
              v-model="filterForm.keywords"
              type="textarea"
              :rows="3"
              placeholder="输入需要包含的关键字，用逗号分隔。如：不规范,错误,缺失"
            />
            <div class="form-tip">
              只有包含这些关键字的问题才会被保留，留空则使用默认关键字
            </div>
          </el-form-item>
        </el-form>
      </div>

      <div class="upload-actions">
        <el-button 
          type="primary" 
          size="large"
          :disabled="!selectedExcelFile"
          @click="proceedToRulesSelection"
        >
          下一步：选择规则
        </el-button>
      </div>
    </div>

    <!-- 规则选择区域 -->
    <div v-if="showRulesSelection && !processing && !completed" class="rules-selection-section">
      <div class="rules-header">
        <h3>🎯 选择要应用的规则</h3>
        <p>请选择要应用的GJB8114和CWE规则，未选中的规则对应的问题将不会出现在最终问题单中</p>
        <div class="rules-actions">
          <el-button @click="selectAllRules">全选</el-button>
          <el-button @click="deselectAllRules">全不选</el-button>
          <el-button type="warning" @click="showSaveConfigDialog">
            <el-icon><Lock /></el-icon>
            保存为默认配置
          </el-button>
          <el-button type="primary" @click="startProcessing" :disabled="selectedRules.length === 0">
            开始过滤处理 ({{ selectedRules.length }}/{{ totalRulesCount }} 规则)
          </el-button>
        </div>
      </div>

      <div class="rules-container">
        <!-- 确定规则列表 -->
        <div class="rules-column">
          <div class="column-header accurate">
            <h4>✅ 确定规则 ({{ accurateRules.length }})</h4>
            <p>这些规则的问题可以准确识别，无需AI分析</p>
          </div>
          <div class="rules-list">
            <el-checkbox-group v-model="selectedRules">
              <div v-for="rule in accurateRules" :key="rule.rule_code" class="rule-item">
                <el-checkbox :label="rule.rule_code" class="rule-checkbox">
                  <div class="rule-content">
                    <div class="rule-name">{{ rule.rule_name }}</div>
                    <div class="rule-description">{{ rule.rule_description }}</div>
                    <div class="rule-meta">
                      <el-tag size="small" type="success">{{ rule.category }}</el-tag>
                      <el-tag size="small">{{ rule.detection_method }}</el-tag>
                    </div>
                  </div>
                </el-checkbox>
              </div>
            </el-checkbox-group>
          </div>
        </div>

        <!-- 不确定规则列表 -->
        <div class="rules-column">
          <div class="column-header uncertain">
            <h4>⚠️ 不确定规则 ({{ uncertainRules.length }})</h4>
            <p>这些规则的问题需要AI分析代码上下文才能准确判断</p>
          </div>
          <div class="rules-list">
            <el-checkbox-group v-model="selectedRules">
              <div v-for="rule in uncertainRules" :key="rule.rule_code" class="rule-item">
                <el-checkbox :label="rule.rule_code" class="rule-checkbox">
                  <div class="rule-content">
                    <div class="rule-name">{{ rule.rule_name }}</div>
                    <div class="rule-description">{{ rule.rule_description }}</div>
                    <div class="rule-meta">
                      <el-tag size="small" type="warning">{{ rule.category }}</el-tag>
                      <el-tag size="small">{{ rule.analysis_complexity }}</el-tag>
                    </div>
                  </div>
                </el-checkbox>
              </div>
            </el-checkbox-group>
          </div>
        </div>
      </div>

      <div class="rules-actions-bottom">
        <el-button @click="backToUpload">返回上传</el-button>
        <el-button type="primary" @click="startProcessing" :disabled="selectedRules.length === 0">
          开始过滤处理 ({{ selectedRules.length }} 规则)
        </el-button>
      </div>
    </div>

    <!-- 保存配置对话框 -->
    <el-dialog
      v-model="saveConfigDialogVisible"
      title="保存默认规则配置"
      width="400px"
      :close-on-click-modal="false"
    >
      <el-form :model="saveConfigForm" label-width="100px">
        <el-alert
          title="管理员权限"
          type="warning"
          description="保存默认配置需要管理员密码验证，保存后所有用户将使用此配置"
          show-icon
          :closable="false"
          style="margin-bottom: 20px;"
        />
        <el-form-item label="管理员密码" required>
          <el-input
            v-model="saveConfigForm.password"
            type="password"
            placeholder="请输入管理员密码"
            show-password
            @keyup.enter="confirmSaveConfig"
          />
        </el-form-item>
        <el-form-item>
          <div class="config-summary">
            <p><strong>当前选择：</strong></p>
            <p>GJB8114规则：{{ gjbSelectedCount }} / {{ accurateRules.length + uncertainRules.length }}</p>
            <p>CWE规则：{{ cweSelectedCount }} / {{ cweRulesTotal }}</p>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="saveConfigDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmSaveConfig" :loading="savingConfig">
            确认保存
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 进度显示区域 -->
    <div v-if="processing" class="progress-section">
      <div class="progress-header">
        <h3>{{ getProgressTitle() }}</h3>
        <div class="progress-status">
          <el-tag :type="getStatusTagType()">{{ getStatusText() }}</el-tag>
        </div>
      </div>

      <el-progress 
        :percentage="progressPercentage" 
        :stroke-width="8"
        :status="getProgressStatus()"
      >
        <span>{{ processedIssues }}/{{ totalIssues }}</span>
      </el-progress>

      <div class="progress-info">
        <div class="progress-stats">
          <div class="stat-card">
            <div class="stat-label">总问题数</div>
            <div class="stat-value">{{ totalIssues }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">已处理</div>
            <div class="stat-value">{{ processedIssues }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">已过滤</div>
            <div class="stat-value">{{ filteredIssues }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">确定规则</div>
            <div class="stat-value">{{ accurateIssues }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">不确定规则</div>
            <div class="stat-value">{{ uncertainIssues }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">AI已分析</div>
            <div class="stat-value">{{ aiAnalyzedIssues }}</div>
          </div>
        </div>

        <!-- 阶段说明 -->
        <div class="phase-info">
          <div v-if="currentStatus === 'processing'" class="phase-item active">
            <el-icon><loading /></el-icon>
            <span>正在分析确定规则的问题...</span>
          </div>
          <div v-else class="phase-item completed">
            <el-icon><check /></el-icon>
            <span>确定规则问题分析完成</span>
          </div>

          <div v-if="currentStatus === 'ai_analyzing'" class="phase-item active">
            <el-icon><loading /></el-icon>
            <span>AI正在深度分析不确定规则的问题...</span>
          </div>
          <div v-else-if="hasCodebase && (currentStatus === 'completed' || showFirstDownload)" class="phase-item completed">
            <el-icon><check /></el-icon>
            <span>AI分析完成</span>
          </div>
          <div v-else-if="hasCodebase" class="phase-item pending">
            <el-icon><clock /></el-icon>
            <span>等待AI分析...</span>
          </div>
        </div>

        <!-- 第一阶段下载按钮 -->
        <div v-if="showFirstDownload" class="first-download-section">
          <el-alert
            title="确定规则问题单已生成"
            type="success"
            description="确定规则的问题已处理完成，您可以先下载这部分问题单。AI仍在分析不确定规则的问题..."
            show-icon
            :closable="false"
          />
          <el-button 
            type="success" 
            size="large"
            :loading="downloadingFirst"
            @click="downloadFirstResult"
          >
            <el-icon><download /></el-icon>
            下载确定规则问题单
          </el-button>
        </div>

        <div v-if="totalIssues > 3000" class="large-file-notice">
          <el-alert
            title="处理大文件中"
            type="info"
            description="您的文件包含大量问题，处理需要较长时间，请耐心等待..."
            :closable="false"
          />
        </div>
      </div>
    </div>

    <!-- 结果区域 -->
    <div v-if="completed" class="result-section">
      <div class="success-message">
        <el-icon class="success-icon"><Check /></el-icon>
        <h3>智能过滤处理完成！</h3>
        <p>已成功过滤静态分析问题，生成格式化问题单</p>
      </div>
      
      <div class="result-stats">
        <div class="stat-item">
          <span class="stat-label">总问题数：</span>
          <span class="stat-value">{{ totalIssues }}</span>
        </div>
        <div class="stat-item highlight">
          <span class="stat-label">确定规则对应：</span>
          <span class="stat-value success">{{ accurateIssues }}个（全部保留）</span>
        </div>
        <div class="stat-item highlight">
          <span class="stat-label">不确定规则对应：</span>
          <span class="stat-value info">{{ uncertainIssues }}个</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">过滤掉：</span>
          <span class="stat-value warning">{{ filteredIssues }}个</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">保留问题：</span>
          <span class="stat-value success">{{ retainedIssues }}个</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">AI分析：</span>
          <span class="stat-value">{{ aiAnalyzedIssues }}个</span>
        </div>
      </div>
      
      <div class="download-section">
        <!-- 第一个下载按钮：确定规则问题单 -->
        <div class="download-group">
          <h4>📋 确定规则问题单</h4>
          <el-button 
            type="success" 
            size="large"
            :loading="downloadingFirst"
            @click="downloadFirstResult"
          >
            <el-icon><download /></el-icon>
            下载确定规则问题单
          </el-button>
        </div>

        <!-- 第二个下载按钮：完整问题单 -->
        <div class="download-group">
          <h4>🎯 完整智能过滤问题单</h4>
          <el-button 
            type="primary" 
            size="large"
            :loading="downloadingFinal"
            @click="downloadFinalResult"
          >
            <el-icon><download /></el-icon>
            下载完整问题单
          </el-button>
        </div>
      </div>
      
      <div class="restart-section">
        <el-button @click="resetForm">重新开始</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElUpload } from 'element-plus'
import { 
  UploadFilled, 
  FolderAdd, 
  Check, 
  Download, 
  Loading, 
  Clock,
  Lock
} from '@element-plus/icons-vue'
import staticAnalysisFilterService from '@/services/staticAnalysisFilterService'

// 响应式数据
const excelUploadRef = ref()
const codebaseUploadRef = ref()
const selectedExcelFile = ref(null)
const selectedCodebaseFile = ref(null)
const excelFileList = ref([])
const codebaseFileList = ref([])
const sessionId = ref('')
const processing = ref(false)
const completed = ref(false)
const showRulesSelection = ref(false)
const downloadingFirst = ref(false)
const downloadingFinal = ref(false)

// 过滤配置
const filterForm = reactive({
  keywords: ''
})

// 规则相关
const accurateRules = ref([])
const uncertainRules = ref([])
const selectedRules = ref([])
const rulesLoaded = ref(false)

// CWE规则（需要单独管理）
const cweAccurateRules = ref([])
const cweUncertainRules = ref([])
const cweRulesTotal = ref(0)

// 保存配置相关
const saveConfigDialogVisible = ref(false)
const savingConfig = ref(false)
const saveConfigForm = reactive({
  password: ''
})

// 计算选中的GJB和CWE规则数量
const gjbSelectedCount = computed(() => {
  const gjbRuleCodes = [
    ...accurateRules.value.map(r => r.rule_code),
    ...uncertainRules.value.map(r => r.rule_code)
  ]
  return selectedRules.value.filter(code => gjbRuleCodes.includes(code)).length
})

const cweSelectedCount = computed(() => {
  const cweRuleCodes = [
    ...cweAccurateRules.value.map(r => r.rule_code),
    ...cweUncertainRules.value.map(r => r.rule_code)
  ]
  return selectedRules.value.filter(code => cweRuleCodes.includes(code)).length
})

// 进度数据
const totalIssues = ref(0)
const processedIssues = ref(0)
const filteredIssues = ref(0)
const aiAnalyzedIssues = ref(0)
const accurateIssues = ref(0)
const uncertainIssues = ref(0)
const currentStatus = ref('pending')
const hasCodebase = ref(false)
const showFirstDownload = ref(false)

// 计算属性
const progressPercentage = computed(() => {
  if (totalIssues.value === 0) return 0
  return Math.round((processedIssues.value / totalIssues.value) * 100)
})

const retainedIssues = computed(() => {
  return processedIssues.value - filteredIssues.value
})

const totalRulesCount = computed(() => {
  return accurateRules.value.length + uncertainRules.value.length
})

// 轮询相关
let pollInterval = null

// 组件挂载时加载规则
onMounted(async () => {
  await loadRules()
})

// 加载规则列表
const loadRules = async () => {
  try {
    // 加载GJB8114规则
    const [accurateResponse, uncertainResponse, cweAccurateResponse, cweUncertainResponse] = await Promise.all([
      staticAnalysisFilterService.getRulesByType('accurate'),
      staticAnalysisFilterService.getRulesByType('uncertain'),
      staticAnalysisFilterService.getCWERulesByType('accurate'),
      staticAnalysisFilterService.getCWERulesByType('uncertain')
    ])

    if (accurateResponse.success) {
      accurateRules.value = accurateResponse.rules
    }

    if (uncertainResponse.success) {
      uncertainRules.value = uncertainResponse.rules
    }

    // 加载CWE规则
    if (cweAccurateResponse.success) {
      cweAccurateRules.value = cweAccurateResponse.rules
    }

    if (cweUncertainResponse.success) {
      cweUncertainRules.value = cweUncertainResponse.rules
    }

    cweRulesTotal.value = cweAccurateRules.value.length + cweUncertainRules.value.length

    // 尝试加载默认配置
    try {
      const defaultConfig = await staticAnalysisFilterService.loadDefaultRulesConfig()
      if (defaultConfig.success && defaultConfig.has_config) {
        // 使用默认配置
        const allGjbRules = [...accurateRules.value.map(r => r.rule_code), ...uncertainRules.value.map(r => r.rule_code)]
        const allCweRules = [...cweAccurateRules.value.map(r => r.rule_code), ...cweUncertainRules.value.map(r => r.rule_code)]
        
        // 只选择配置中存在且在规则列表中的规则
        const validGjbRules = defaultConfig.gjb_rules.filter(code => allGjbRules.includes(code))
        const validCweRules = defaultConfig.cwe_rules.filter(code => allCweRules.includes(code))
        
        selectedRules.value = [...validGjbRules, ...validCweRules]
        
        ElMessage.success(`已加载默认配置：GJB ${validGjbRules.length} 个，CWE ${validCweRules.length} 个`)
      } else {
        // 没有默认配置，全选所有规则
        selectedRules.value = [
          ...accurateRules.value.map(rule => rule.rule_code),
          ...uncertainRules.value.map(rule => rule.rule_code),
          ...cweAccurateRules.value.map(rule => rule.rule_code),
          ...cweUncertainRules.value.map(rule => rule.rule_code)
        ]
      }
    } catch (configError) {
      // 加载默认配置失败，全选所有规则
      selectedRules.value = [
        ...accurateRules.value.map(rule => rule.rule_code),
        ...uncertainRules.value.map(rule => rule.rule_code),
        ...cweAccurateRules.value.map(rule => rule.rule_code),
        ...cweUncertainRules.value.map(rule => rule.rule_code)
      ]
    }

    rulesLoaded.value = true
  } catch (error) {
    ElMessage.error('加载规则列表失败: ' + error.message)
  }
}

// 文件选择处理
const handleExcelFileChange = (file) => {
  selectedExcelFile.value = file
  excelFileList.value = [file]
}

const handleCodebaseFileChange = (file) => {
  selectedCodebaseFile.value = file
  codebaseFileList.value = [file]
}

// 进入规则选择阶段
const proceedToRulesSelection = () => {
  if (!selectedExcelFile.value) {
    ElMessage.error('请先选择Excel文件')
    return
  }

  if (!rulesLoaded.value) {
    ElMessage.error('规则列表还未加载完成，请稍候')
    return
  }

  showRulesSelection.value = true
}

// 返回上传阶段
const backToUpload = () => {
  showRulesSelection.value = false
}

// 规则选择操作
const selectAllRules = () => {
  selectedRules.value = [
    ...accurateRules.value.map(rule => rule.rule_code),
    ...uncertainRules.value.map(rule => rule.rule_code),
    ...cweAccurateRules.value.map(rule => rule.rule_code),
    ...cweUncertainRules.value.map(rule => rule.rule_code)
  ]
}

const deselectAllRules = () => {
  selectedRules.value = []
}

// 显示保存配置对话框
const showSaveConfigDialog = () => {
  saveConfigForm.password = ''
  saveConfigDialogVisible.value = true
}

// 确认保存配置
const confirmSaveConfig = async () => {
  if (!saveConfigForm.password) {
    ElMessage.error('请输入管理员密码')
    return
  }

  try {
    savingConfig.value = true

    // 分离GJB和CWE规则
    const allGjbRules = [
      ...accurateRules.value.map(r => r.rule_code),
      ...uncertainRules.value.map(r => r.rule_code)
    ]
    const allCweRules = [
      ...cweAccurateRules.value.map(r => r.rule_code),
      ...cweUncertainRules.value.map(r => r.rule_code)
    ]

    const gjbRules = selectedRules.value.filter(code => allGjbRules.includes(code))
    const cweRules = selectedRules.value.filter(code => allCweRules.includes(code))

    const response = await staticAnalysisFilterService.saveDefaultRulesConfig(
      saveConfigForm.password,
      gjbRules,
      cweRules
    )

    if (response.success) {
      ElMessage.success('默认规则配置已保存！')
      saveConfigDialogVisible.value = false
    }
  } catch (error) {
    if (error.response && error.response.status === 403) {
      ElMessage.error('管理员密码错误')
    } else {
      ElMessage.error('保存配置失败: ' + error.message)
    }
  } finally {
    savingConfig.value = false
  }
}

// 开始处理
const startProcessing = async () => {
  if (!selectedExcelFile.value) {
    ElMessage.error('请先选择Excel文件')
    return
  }

  if (selectedRules.value.length === 0) {
    ElMessage.error('请至少选择一个规则')
    return
  }

  try {
    processing.value = true
    showRulesSelection.value = false
    hasCodebase.value = !!selectedCodebaseFile.value
    
    const response = await staticAnalysisFilterService.uploadEnhancedFiles(
      selectedExcelFile.value.raw,
      selectedCodebaseFile.value?.raw,
      filterForm.keywords,
      selectedRules.value
    )
    
    if (!response) {
      throw new Error('服务器无响应')
    }
    
    if (response.success) {
      sessionId.value = response.session_id
      hasCodebase.value = response.has_codebase
      ElMessage.success('文件上传成功，正在智能过滤处理中...')
      
      // 立即检查一次状态
      try {
        const statusResponse = await staticAnalysisFilterService.getEnhancedSessionStatus(sessionId.value)
        
        if (statusResponse && statusResponse.success) {
          updateProgressData(statusResponse)
          
          if (statusResponse.status === 'completed') {
            processing.value = false
            completed.value = true
            ElMessage.success('智能过滤处理完成！')
            return
          }
        }
      } catch (error) {
        // 初始状态检查失败，继续轮询
      }
      
      // 开始轮询状态
      startStatusPolling()
    } else {
      throw new Error(response.error || response.message || '上传失败')
    }
  } catch (error) {
    let errorMessage = '上传失败'
    if (error.message) {
      errorMessage += ': ' + error.message
    }
    ElMessage.error(errorMessage)
    processing.value = false
  }
}

// 更新进度数据
const updateProgressData = (statusData) => {
  totalIssues.value = statusData.total_issues || 0
  processedIssues.value = statusData.processed_issues || 0
  filteredIssues.value = statusData.filtered_issues || 0
  aiAnalyzedIssues.value = statusData.ai_analyzed_issues || 0
  accurateIssues.value = statusData.accurate_issues || 0
  uncertainIssues.value = statusData.uncertain_issues || 0
  currentStatus.value = statusData.status || 'pending'

  // 判断是否显示第一阶段下载按钮
  if (currentStatus.value === 'ai_analyzing' || 
      (currentStatus.value === 'completed' && hasCodebase.value)) {
    showFirstDownload.value = true
  }
}

// 开始状态轮询
const startStatusPolling = () => {
  checkStatus()
  
  // 根据问题数量调整轮询间隔
  let pollIntervalTime = 5000 // 默认5秒
  if (totalIssues.value > 3000) {
    pollIntervalTime = 10000 // 大于3000个问题时，改为10秒轮询
  } else if (totalIssues.value > 1000) {
    pollIntervalTime = 8000 // 大于1000个问题时，改为8秒轮询
  }
  
  pollInterval = setInterval(() => {
    if (completed.value || !processing.value) {
      clearInterval(pollInterval)
      pollInterval = null
      return
    }
    checkStatus()
  }, pollIntervalTime)
}

// 检查状态
const checkStatus = async () => {
  if (!sessionId.value) {
    return
  }

  try {
    const response = await staticAnalysisFilterService.getEnhancedSessionStatus(sessionId.value)
    
    if (!response) {
      return
    }
    
    if (response.success) {
      updateProgressData(response)
      
      if (response.status === 'completed') {
        processing.value = false
        completed.value = true
        
        if (pollInterval) {
          clearInterval(pollInterval)
          pollInterval = null
        }
        
        ElMessage.success('智能过滤处理完成！')
      }
    }
  } catch (error) {
    // 单次查询失败不停止轮询
  }
}

// 进度相关方法
const getProgressTitle = () => {
  switch (currentStatus.value) {
    case 'processing':
      return '正在分析确定规则的问题...'
    case 'ai_analyzing':
      return 'AI正在深度分析不确定规则的问题...'
    case 'completed':
      return '智能过滤处理完成！'
    default:
      return '正在处理中...'
  }
}

const getStatusText = () => {
  switch (currentStatus.value) {
    case 'processing':
      return '规则分析中'
    case 'ai_analyzing':
      return 'AI分析中'
    case 'completed':
      return '处理完成'
    default:
      return '处理中'
  }
}

const getStatusTagType = () => {
  switch (currentStatus.value) {
    case 'processing':
      return 'primary'
    case 'ai_analyzing':
      return 'warning'
    case 'completed':
      return 'success'
    default:
      return 'info'
  }
}

const getProgressStatus = () => {
  if (currentStatus.value === 'completed') {
    return 'success'
  } else if (currentStatus.value === 'ai_analyzing') {
    return 'active'
  } else {
    return 'active'
  }
}

// 下载第一阶段结果（确定规则问题单）
const downloadFirstResult = async () => {
  if (!sessionId.value) {
    ElMessage.error('会话ID不存在')
    return
  }

  try {
    downloadingFirst.value = true
    
    // 先确保文件已生成
    const generateResponse = await staticAnalysisFilterService.generateOutputFile(sessionId.value)
    
    if (!generateResponse.success) {
      throw new Error(generateResponse.error || '生成文件失败')
    }
    
    // 下载文件
    const downloadUrl = staticAnalysisFilterService.getDownloadUrl(sessionId.value, generateResponse.filename)
    
    // 创建下载链接
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = `确定规则问题单_${generateResponse.filename}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    ElMessage.success('确定规则问题单下载成功')
    
  } catch (error) {
    ElMessage.error('下载失败: ' + error.message)
  } finally {
    downloadingFirst.value = false
  }
}

// 下载最终结果（完整问题单）
const downloadFinalResult = async () => {
  if (!sessionId.value) {
    ElMessage.error('会话ID不存在')
    return
  }

  try {
    downloadingFinal.value = true
    
    // 先确保文件已生成
    const generateResponse = await staticAnalysisFilterService.generateOutputFile(sessionId.value)
    
    if (!generateResponse.success) {
      throw new Error(generateResponse.error || '生成文件失败')
    }
    
    // 下载文件
    const downloadUrl = staticAnalysisFilterService.getDownloadUrl(sessionId.value, generateResponse.filename)
    
    // 创建下载链接
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = `智能过滤问题单_${generateResponse.filename}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    ElMessage.success('完整问题单下载成功')
    
  } catch (error) {
    ElMessage.error('下载失败: ' + error.message)
  } finally {
    downloadingFinal.value = false
  }
}

// 重置表单
const resetForm = () => {
  selectedExcelFile.value = null
  selectedCodebaseFile.value = null
  excelFileList.value = []
  codebaseFileList.value = []
  sessionId.value = ''
  processing.value = false
  completed.value = false
  showRulesSelection.value = false
  downloadingFirst.value = false
  downloadingFinal.value = false
  showFirstDownload.value = false
  
  totalIssues.value = 0
  processedIssues.value = 0
  filteredIssues.value = 0
  aiAnalyzedIssues.value = 0
  accurateIssues.value = 0
  uncertainIssues.value = 0
  currentStatus.value = 'pending'
  hasCodebase.value = false
  
  filterForm.keywords = ''
  
  // 重新选择所有规则
  selectedRules.value = [
    ...accurateRules.value.map(rule => rule.rule_code),
    ...uncertainRules.value.map(rule => rule.rule_code)
  ]
  
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
  
  // 清空上传组件
  if (excelUploadRef.value) {
    excelUploadRef.value.clearFiles()
  }
  if (codebaseUploadRef.value) {
    codebaseUploadRef.value.clearFiles()
  }
}

// 组件卸载时清理
onUnmounted(() => {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
})
</script>

<style scoped>
.enhanced-static-analysis-filter {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.header {
  text-align: center;
  /* 统一与下方内容的左右边界，对齐为同一内宽 */
  width: 100%;
  max-width: 1320px;
  margin: 0 auto 30px auto;
}

.header h2 {
  color: #303133;
  margin-bottom: 10px;
}

.description {
  color: #606266;
  font-size: 14px;
}

/* 上传区域样式 */
.upload-section {
  margin-bottom: 30px;
}

.upload-group {
  margin-bottom: 30px;
  padding: 25px;
  border: 1px solid #e4e7ed;
  border-radius: 12px;
  background: white;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  min-height: 180px;
}

.upload-group h3 {
  margin: 0 0 15px 0;
  color: #303133;
  font-size: 16px;
}

.upload-dragger {
  width: 100%;
}

.codebase-notice {
  margin-top: 15px;
}

.filter-config {
  margin: 20px 0;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.upload-actions {
  text-align: center;
  margin-top: 20px;
}

/* 规则选择区域样式 */
.rules-selection-section {
  margin-bottom: 30px;
}

.rules-header {
  text-align: center;
  margin-bottom: 20px;
  padding: 20px;
  background: #f0f9ff;
  border-radius: 8px;
}

.rules-header h3 {
  margin: 0 0 10px 0;
  color: #303133;
}

.rules-actions {
  margin-top: 15px;
}

.rules-actions button {
  margin: 0 5px;
}

.rules-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.rules-column {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
}

.column-header {
  padding: 15px 20px;
  color: white;
  font-weight: bold;
}

.column-header.accurate {
  background: linear-gradient(135deg, #67c23a, #85ce61);
}

.column-header.uncertain {
  background: linear-gradient(135deg, #e6a23c, #f0a020);
}

.column-header h4 {
  margin: 0 0 5px 0;
  font-size: 16px;
}

.column-header p {
  margin: 0;
  font-size: 12px;
  opacity: 0.9;
}

.rules-list {
  max-height: 400px;
  overflow-y: auto;
  padding: 10px;
}

.rule-item {
  margin-bottom: 10px;
  padding: 10px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  background: white;
  transition: all 0.3s;
}

.rule-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.rule-checkbox {
  width: 100%;
}

.rule-content {
  margin-left: 24px;
}

.rule-name {
  font-weight: bold;
  color: #303133;
  margin-bottom: 5px;
  white-space: normal;
  word-wrap: break-word;
  overflow-wrap: break-word;
  max-width: 100%;
  font-size: 13px;
  line-height: 1.4;
}

.rule-description {
  color: #606266;
  font-size: 12px;
  margin-bottom: 8px;
  line-height: 1.4;
}

.rule-meta {
  display: flex;
  gap: 5px;
}

.rules-actions-bottom {
  text-align: center;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

/* 进度区域样式 */
.progress-section {
  text-align: center;
  padding: 40px 20px;
}

.progress-header {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
}

.progress-header h3 {
  color: #409EFF;
  margin: 0;
}

.progress-status {
  margin: 0;
}

.progress-info {
  margin-top: 30px;
}

.progress-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 15px;
  max-width: 800px;
  margin: 0 auto 30px;
}

.stat-card {
  padding: 15px;
  background: #f0f9ff;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.stat-card .stat-label {
  display: block;
  font-size: 12px;
  color: #606266;
  margin-bottom: 5px;
}

.stat-card .stat-value {
  display: block;
  font-size: 20px;
  font-weight: bold;
  color: #409EFF;
}

.phase-info {
  margin: 20px 0;
  text-align: left;
  max-width: 400px;
  margin-left: auto;
  margin-right: auto;
}

.phase-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 15px;
  margin-bottom: 10px;
  border-radius: 6px;
  font-size: 14px;
}

.phase-item.active {
  background: #e6f7ff;
  border: 1px solid #91d5ff;
  color: #1890ff;
}

.phase-item.completed {
  background: #f6ffed;
  border: 1px solid #b7eb8f;
  color: #52c41a;
}

.phase-item.pending {
  background: #f5f5f5;
  border: 1px solid #d9d9d9;
  color: #8c8c8c;
}

.first-download-section {
  margin: 30px 0;
  padding: 20px;
  background: #f6ffed;
  border-radius: 8px;
  border: 1px solid #b7eb8f;
}

.first-download-section .el-alert {
  margin-bottom: 15px;
}

.large-file-notice {
  margin-top: 20px;
}

/* 配置对话框样式 */
.config-summary {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  margin: 10px 0;
}

.config-summary p {
  margin: 5px 0;
  color: #606266;
}

.config-summary strong {
  color: #303133;
}

/* 结果区域样式 */
.result-section {
  text-align: center;
  padding: 40px 20px;
}

.success-message {
  margin-bottom: 30px;
}

.success-icon {
  font-size: 48px;
  color: #67C23A;
  margin-bottom: 15px;
}

.success-message h3 {
  color: #67C23A;
  margin-bottom: 10px;
}

.result-stats {
  display: flex;
  justify-content: center;
  gap: 30px;
  margin: 30px 0;
  flex-wrap: wrap;
}

.stat-item {
  padding: 15px 20px;
  background: #f0f9ff;
  border-radius: 8px;
  min-width: 120px;
}

.stat-item.highlight {
  background: linear-gradient(135deg, #f0f9ff, #e6f7ff);
  border: 2px solid #409eff;
}

.stat-label {
  display: block;
  font-size: 14px;
  color: #606266;
  margin-bottom: 5px;
}

.stat-item.highlight .stat-label {
  font-weight: bold;
  color: #409eff;
}

.stat-value {
  display: block;
  font-size: 24px;
  font-weight: bold;
  color: #409EFF;
}

.stat-value.success {
  color: #67c23a;
}

.stat-value.info {
  color: #409eff;
}

.stat-value.warning {
  color: #e6a23c;
}

.download-section {
  margin: 30px 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 30px;
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
}

.download-group {
  padding: 20px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #fafafa;
}

.download-group h4 {
  margin: 0 0 15px 0;
  color: #303133;
}

.restart-section {
  margin-top: 30px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .rules-container {
    grid-template-columns: 1fr;
  }
  
  .progress-stats {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .result-stats {
    flex-direction: column;
    align-items: center;
  }
  
  .download-section {
    grid-template-columns: 1fr;
  }
}
</style>
