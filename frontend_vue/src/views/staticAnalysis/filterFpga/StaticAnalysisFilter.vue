<template>
  <div class="static-analysis-filter">
    <div class="header">
      <h2>🚀 FPGA静态分析问题智能过滤工具</h2>
      <p class="description">上传FPGA静态分析结果和代码库，基于Verilog/VHDL编码规则智能过滤并生成格式化问题单</p>
    </div>

    <!-- 文件上传和规则选择区域 -->
    <div v-if="!processing && !completed" class="main-content">
      <!-- 文件上传区域 -->
      <div class="upload-container">
        <!-- Excel文件上传 -->
        <div class="upload-item">
          <div class="upload-header">
            <h3>📊 静态分析结果文件</h3>
            <el-tag :type="selectedExcelFile ? 'success' : 'info'" size="small">
              {{ selectedExcelFile ? '已选择' : '必需' }}
            </el-tag>
          </div>
          <el-upload
            ref="excelUploadRef"
            class="upload-dragger compact"
            drag
            :auto-upload="false"
            :limit="1"
            accept=".xlsx"
            :on-change="handleExcelFileChange"
            :file-list="excelFileList"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              拖拽或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 .xlsx 格式
              </div>
            </template>
          </el-upload>
        </div>

        <!-- 代码库上传 -->
        <div class="upload-item">
          <div class="upload-header">
            <h3>📁 代码库文件</h3>
            <el-tag :type="selectedCodebaseFile ? 'success' : 'warning'" size="small">
              {{ selectedCodebaseFile ? '已选择' : '必需' }}
            </el-tag>
          </div>
          <el-upload
            ref="codebaseUploadRef"
            class="upload-dragger compact"
            drag
            :auto-upload="false"
            :limit="1"
            accept=".zip"
            :on-change="handleCodebaseFileChange"
            :file-list="codebaseFileList"
          >
            <el-icon class="el-icon--upload"><folder-add /></el-icon>
            <div class="el-upload__text">
              拖拽或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 .zip 格式
              </div>
            </template>
          </el-upload>
        </div>
      </div>

      <!-- 规则选择区域 -->
      <div class="rules-section">
            <div class="rules-header">
              <div class="rules-title">
                <h3>🎯 选择要应用的FPGA规则</h3>
                <div class="rules-summary">
                  <span class="selected-count">已选择 {{ selectedRules.length }}/{{ totalRulesCount }} 规则</span>
                </div>
              </div>
              <div class="rules-actions">
                <el-button size="small" @click="selectAllRules">全选</el-button>
                <el-button size="small" @click="deselectAllRules">全不选</el-button>
                <el-button size="small" @click="selectAccurateOnly">仅选确定规则</el-button>
                <el-button size="small" @click="selectUncertainOnly">仅选不确定规则</el-button>
                <el-button size="small" type="warning" @click="showSaveConfigDialog">
                  <el-icon><Lock /></el-icon>保存为默认配置
                </el-button>
              </div>
            </div>
            <el-tabs v-model="activeFpgaLangTab" class="fpga-lang-tabs">
              <el-tab-pane name="verilog">
                <template #label>
                  <span>🟢 Verilog <el-badge :value="selectedVerilogCount" :hidden="selectedVerilogCount===0" type="primary" class="tab-badge" /></span>
                </template>
                <div class="rules-container">
                  <div class="rules-column accurate-column">
                    <div class="column-header">
                      <div class="header-content"><h4>✅ 确定规则</h4><div class="rule-count">{{ accurateVerilogRules.length }} 条</div></div>
                      <p class="header-desc">语法分析即可准确识别</p>
                    </div>
                    <div class="rules-list">
                      <el-checkbox-group v-model="selectedRules">
                        <div v-for="rule in accurateVerilogRules" :key="rule.rule_code" class="rule-item" :class="{'rule-modified': isRuleModified('fpga', rule.rule_code)}">
                          <el-checkbox :value="rule.rule_code" :label="rule.rule_code" class="rule-checkbox">
                            <div class="rule-content">
                              <div class="rule-name">{{ rule.rule_code }}</div>
                              <div class="rule-description">{{ rule.rule_content }}</div>
                              <div class="rule-meta"><el-tag size="small" type="success">Verilog</el-tag><el-tag size="small" plain>{{ rule.rule_type }}</el-tag></div>
                            </div>
                          </el-checkbox>
                          <el-button size="small" type="warning" plain @click="moveRuleToUncertain('fpga', rule.rule_code)" class="move-rule-btn"><el-icon><Bottom /></el-icon>移至不确定</el-button>
                        </div>
                      </el-checkbox-group>
                    </div>
                  </div>
                  <div class="rules-column uncertain-column">
                    <div class="column-header">
                      <div class="header-content"><h4>⚠️ 不确定规则</h4><div class="rule-count">{{ uncertainVerilogRules.length }} 条</div></div>
                      <p class="header-desc">需AI分析代码上下文</p>
                    </div>
                    <div class="rules-list">
                      <el-checkbox-group v-model="selectedRules">
                        <div v-for="rule in uncertainVerilogRules" :key="rule.rule_code" class="rule-item" :class="{'rule-modified': isRuleModified('fpga', rule.rule_code)}">
                          <el-checkbox :value="rule.rule_code" :label="rule.rule_code" class="rule-checkbox">
                            <div class="rule-content">
                              <div class="rule-name">{{ rule.rule_code }}</div>
                              <div class="rule-description">{{ rule.rule_content }}</div>
                              <div class="rule-meta"><el-tag size="small" type="warning">Verilog</el-tag><el-tag size="small" plain>{{ rule.rule_type }}</el-tag></div>
                            </div>
                          </el-checkbox>
                          <el-button size="small" type="success" plain @click="moveRuleToAccurate('fpga', rule.rule_code)" class="move-rule-btn"><el-icon><Top /></el-icon>移至确定</el-button>
                        </div>
                      </el-checkbox-group>
                    </div>
                  </div>
                </div>
              </el-tab-pane>
              <el-tab-pane name="vhdl">
                <template #label>
                  <span>🔵 VHDL <el-badge :value="selectedVhdlCount" :hidden="selectedVhdlCount===0" type="info" class="tab-badge" /></span>
                </template>
                <div class="rules-container">
                  <div class="rules-column accurate-column">
                    <div class="column-header">
                      <div class="header-content"><h4>✅ 确定规则</h4><div class="rule-count">{{ accurateVhdlRules.length }} 条</div></div>
                      <p class="header-desc">语法分析即可准确识别</p>
                    </div>
                    <div class="rules-list">
                      <el-checkbox-group v-model="selectedRules">
                        <div v-for="rule in accurateVhdlRules" :key="rule.rule_code" class="rule-item" :class="{'rule-modified': isRuleModified('fpga', rule.rule_code)}">
                          <el-checkbox :value="rule.rule_code" :label="rule.rule_code" class="rule-checkbox">
                            <div class="rule-content">
                              <div class="rule-name">{{ rule.rule_code }}</div>
                              <div class="rule-description">{{ rule.rule_content }}</div>
                              <div class="rule-meta"><el-tag size="small" type="info">VHDL</el-tag><el-tag size="small" plain>{{ rule.rule_type }}</el-tag></div>
                            </div>
                          </el-checkbox>
                          <el-button size="small" type="warning" plain @click="moveRuleToUncertain('fpga', rule.rule_code)" class="move-rule-btn"><el-icon><Bottom /></el-icon>移至不确定</el-button>
                        </div>
                      </el-checkbox-group>
                    </div>
                  </div>
                  <div class="rules-column uncertain-column">
                    <div class="column-header">
                      <div class="header-content"><h4>⚠️ 不确定规则</h4><div class="rule-count">{{ uncertainVhdlRules.length }} 条</div></div>
                      <p class="header-desc">需AI分析代码上下文</p>
                    </div>
                    <div class="rules-list">
                      <el-checkbox-group v-model="selectedRules">
                        <div v-for="rule in uncertainVhdlRules" :key="rule.rule_code" class="rule-item" :class="{'rule-modified': isRuleModified('fpga', rule.rule_code)}">
                          <el-checkbox :value="rule.rule_code" :label="rule.rule_code" class="rule-checkbox">
                            <div class="rule-content">
                              <div class="rule-name">{{ rule.rule_code }}</div>
                              <div class="rule-description">{{ rule.rule_content }}</div>
                              <div class="rule-meta"><el-tag size="small" type="danger">VHDL</el-tag><el-tag size="small" plain>{{ rule.rule_type }}</el-tag></div>
                            </div>
                          </el-checkbox>
                          <el-button size="small" type="success" plain @click="moveRuleToAccurate('fpga', rule.rule_code)" class="move-rule-btn"><el-icon><Top /></el-icon>移至确定</el-button>
                        </div>
                      </el-checkbox-group>
                    </div>
                  </div>
                </div>
              </el-tab-pane>
            </el-tabs>
      </div>


      <!-- 开始处理按钮 -->
      <div class="start-processing">
        <div class="processing-info">
          <div class="info-item">
            <el-icon><document /></el-icon>
            <span>Excel文件: {{ selectedExcelFile ? '✅' : '❌' }}</span>
          </div>
          <div class="info-item">
            <el-icon><folder /></el-icon>
            <span>代码库: {{ selectedCodebaseFile ? '✅' : '❌' }}</span>
          </div>
          <div class="info-item">
            <el-icon><check /></el-icon>
            <span>规则: {{ selectedRules.length }} 条</span>
          </div>
        </div>
        <el-button 
          type="primary" 
          size="large"
          :disabled="!canStartProcessing"
          @click="startProcessing"
          class="start-btn"
        >
          <el-icon><caret-right /></el-icon>
          开始智能过滤处理
        </el-button>
      </div>
    </div>

    <!-- FPGA规则审查进度 -->
    <div v-if="processing || completed" class="single-progress-container">
      <!-- FPGA规则进度卡片 -->
      <div class="progress-card fpga-progress-card">
        <div class="card-header-banner fpga-banner">
          <h3>🔍 FPGA规则审查进度</h3>
          <el-tag :type="getStatusTagType(fpgaProgress.status)" size="large">
            {{ getStatusText(fpgaProgress.status) }}
          </el-tag>
        </div>
        
        <div class="card-content">
          <el-progress 
            :percentage="fpgaProgress.progress" 
            :stroke-width="12"
            :status="getProgressStatusByState(fpgaProgress.status)"
            class="main-progress"
          >
            <span class="progress-text">{{ fpgaProgress.aiProcessedIssues }}/{{ fpgaProgress.aiProcessingTotal }}</span>
          </el-progress>

          <!-- 当前分析信息 -->
          <div v-if="fpgaProgress.status === 'processing' && fpgaProgress.currentAnalyzingIssue" class="current-analysis-info fpga-analysis">
            <div class="analysis-header">
              <span class="analysis-icon">🔬</span>
              <span class="analysis-title">正在分析</span>
            </div>
            <div class="analysis-content">
              <div class="issue-name">{{ fpgaProgress.currentAnalyzingIssue }}</div>
              <div class="tool-calls">已调用工具 {{ fpgaProgress.toolCallsCount }} 次</div>
            </div>
          </div>

          <!-- 详细统计信息 -->
          <div class="detailed-stats">
            <div class="stats-row">
              <div class="stat-item-detail">
                <span class="stat-label">📊 总问题数</span>
                <span class="stat-value primary">{{ fpgaProgress.totalIssues }}</span>
              </div>
              <div class="stat-item-detail">
                <span class="stat-label">✅ 确定规则</span>
                <span class="stat-value success">{{ fpgaProgress.accurateIssues }}</span>
              </div>
              <div class="stat-item-detail">
                <span class="stat-label">⚠️ 不确定规则</span>
                <span class="stat-value warning">{{ fpgaProgress.uncertainIssues }}</span>
              </div>
            </div>
            <div class="stats-row">
              <div class="stat-item-detail">
                <span class="stat-label">🔬 不确定（已勾选）</span>
                <span class="stat-value info">{{ fpgaProgress.aiProcessedIssues }}/{{ fpgaProgress.aiProcessingTotal }}</span>
              </div>
              <div class="stat-item-detail">
                <span class="stat-label">🗑️ 过滤掉</span>
                <span class="stat-value danger">{{ fpgaProgress.filteredIssues }}</span>
              </div>
              <div class="stat-item-detail">
                <span class="stat-label">✨ 最终保留</span>
                <span class="stat-value primary-bold">{{ fpgaProgress.retainedIssues }}</span>
              </div>
            </div>
          </div>

          <!-- 后台整理提示 -->
          <div v-if="processing && !fpgaProgress.accurate_ready" class="preparing-hint preparing-hint-fpga">
            <div class="preparing-hint-icon preparing-hint-spinner-wrap">
              <el-icon class="preparing-hint-spinner"><Loading /></el-icon>
            </div>
            <div class="preparing-hint-content">
              <div class="preparing-hint-title">后台正在整理数据</div>
              <div class="preparing-hint-text">系统正在汇总问题并生成“未经AI过滤”问题单，请稍候，按钮将在文件准备完成后自动出现。</div>
            </div>
          </div>

          <!-- 下载按钮区域（四分分类 + 代码视图同排） -->
          <div v-if="fpgaProgress.accurate_ready || fpgaProgress.status === 'completed'" class="download-buttons">
            <!-- 全部问题单（未经AI过滤） - accurate_ready 显示 -->
            <el-button 
              v-if="fpgaProgress.accurate_ready"
              type="primary" 
              size="default"
              :loading="downloadingFpgaAllSplit"
              @click="downloadFpgaAllSplit"
              class="download-btn-compact download-btn-wide"
            >
              <el-icon><download /></el-icon>
              下载FPGA全部问题单（未经AI过滤）
            </el-button>
            <!-- 完整问题单（AI过滤后，高亮AI确认） - 完成后显示 -->
            <el-button 
              v-if="fpgaProgress.status === 'completed' && fpgaProgress.aiProcessingTotal > 0"
              type="primary" 
              size="default"
              :loading="downloadingFpgaFullSplit"
              @click="downloadFpgaFullSplit"
              class="download-btn-compact download-btn-wide"
            >
              <el-icon><download /></el-icon>
              下载FPGA完整问题单（AI过滤后）
            </el-button>
            <!-- 完成后显示代码视图，与上面同排 -->
            <el-button 
              v-if="fpgaProgress.status === 'completed'"
              type="success"
              size="default"
              @click="openCodeView('fpga')"
              class="download-btn-compact download-btn-medium"
            >
              <el-icon><View /></el-icon>
              打开代码视图
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 重新开始按钮（完成后显示） -->
    <div v-if="completed" class="restart-section-bottom">
      <el-button @click="resetForm" size="large" plain>
        <el-icon><refresh /></el-icon>
        重新开始
      </el-button>
    </div>

    <!-- 保存配置对话框 -->
    <el-dialog
      v-model="saveConfigDialogVisible"
      title="保存默认规则配置"
      width="450px"
      :close-on-click-modal="false"
    >
      <el-form :model="saveConfigForm" label-width="110px">
        <el-collapse v-model="activeCollapseItems" style="margin-bottom: 15px;">
          <el-collapse-item title="🎯 高级过滤配置（可选）" name="customFilters">
            <el-alert type="info" :closable="false" style="margin-bottom: 15px;">
              <p style="margin: 0;">为特定规则配置关键词过滤：问题描述需<strong>同时包含所有关键词</strong>才会被过滤</p>
            </el-alert>
            
            <div v-for="(filter, index) in customFilterList" :key="index" class="filter-item">
              <el-select 
                v-model="filter.ruleCode" 
                placeholder="选择规则"
                filterable
                style="width: 200px;"
              >
                <el-option-group label="GJB8114规则">
                  <el-option 
                    v-for="rule in selectedRules" 
                    :key="rule" 
                    :label="rule" 
                    :value="rule"
                  />
                </el-option-group>
                <el-option-group label="CWE规则">
                  <el-option 
                    v-for="rule in [...selectedCweAccurateRules, ...selectedCweUncertainRules]" 
                    :key="rule" 
                    :label="rule" 
                    :value="rule"
                  />
                </el-option-group>
              </el-select>
              
              <el-input
                v-model="filter.keywords"
                placeholder="输入关键词，多个用逗号分隔"
                style="width: 300px; margin: 0 10px;"
              />
              
              <el-button 
                type="danger" 
                size="small" 
                plain
                @click="removeCustomFilter(index)"
              >
                删除
              </el-button>
            </div>
            
            <el-button 
              type="primary" 
              size="small" 
              plain
              @click="addCustomFilter"
              style="margin-top: 10px;"
            >
              <el-icon><Plus /></el-icon>
              添加过滤规则
            </el-button>
          </el-collapse-item>
          
          <el-collapse-item title="⚙️ 问题数量限制（可选）" name="maxIssues">
            <el-alert type="info" :closable="false" style="margin-bottom: 15px;">
              <p style="margin: 0;">为每个规则设置最多保留的问题数量，超出部分将通过<strong>均匀分布采样</strong>删除</p>
              <p style="margin: 5px 0 0 0; font-size: 12px; color: #909399;">设置为 0 表示不限制问题数量</p>
            </el-alert>
            
            <el-input-number
              v-model="saveConfigForm.maxIssuesPerRule"
              :min="0"
              :max="1000"
              :step="10"
              controls-position="right"
              style="width: 100%;"
            />
          </el-collapse-item>
        </el-collapse>
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

    <!-- 导入配置对话框 -->
    <el-dialog
      v-model="importConfigDialogVisible"
      title="导入规则配置"
      width="450px"
      :close-on-click-modal="false"
    >
      <el-form :model="importConfigForm" label-width="110px">
        <el-form-item label="配置文件">
          <el-upload
            ref="configUploadRef"
            :auto-upload="false"
            :limit="1"
            accept=".json"
            :on-change="handleConfigFileChange"
            :on-remove="handleConfigFileRemove"
          >
            <template #trigger>
              <el-button type="primary" plain>
                <el-icon><Upload /></el-icon>
                选择配置文件
              </el-button>
            </template>
            <template #tip>
              <div class="el-upload__tip">
                请选择之前导出的 JSON 格式配置文件
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="importConfigDialogVisible = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="confirmImportConfig" 
            :loading="importingConfig"
            :disabled="!selectedConfigFile"
          >
            确认导入
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox, ElNotification, ElUpload } from 'element-plus'
import { 
  UploadFilled, 
  FolderAdd, 
  Check, 
  Download, 
  Loading, 
  Clock,
  Document,
  Folder,
  CaretRight,
  CircleCheck,
  Refresh,
  Lock,
  View,
  Top,
  Bottom,
  Upload,
  Warning,
  Plus
} from '@element-plus/icons-vue'
import axios from 'axios'
import staticAnalysisFilterFpgaService from '@/services/staticAnalysisFilterFpgaService'

// 确保FPGA相关请求也携带cookie，以便后端获取登录session
axios.defaults.withCredentials = true

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
const downloadingFirst = ref(false)
const downloadingFinal = ref(false)
const downloadingFpgaAccurate = ref(false)
const downloadingFpgaFull = ref(false)
// 规则相关 - FPGA
const accurateRules = ref([])
const uncertainRules = ref([])
const selectedRules = ref([])
const rulesLoaded = ref(false)

// Language-grouped computed (injected)
const activeFpgaLangTab    = ref('verilog')
const accurateVerilogRules  = computed(() => accurateRules.value.filter(r => (r.language || '').toLowerCase() === 'verilog'))
const uncertainVerilogRules = computed(() => uncertainRules.value.filter(r => (r.language || '').toLowerCase() === 'verilog'))
const accurateVhdlRules     = computed(() => accurateRules.value.filter(r => (r.language || '').toLowerCase() === 'vhdl'))
const uncertainVhdlRules    = computed(() => uncertainRules.value.filter(r => (r.language || '').toLowerCase() === 'vhdl'))
const verilogRulesAll       = computed(() => [...accurateVerilogRules.value, ...uncertainVerilogRules.value])
const vhdlRulesAll          = computed(() => [...accurateVhdlRules.value, ...uncertainVhdlRules.value])
const selectedVerilogCount  = computed(() => selectedRules.value.filter(c => verilogRulesAll.value.some(r => r.rule_code === c)).length)
const selectedVhdlCount     = computed(() => selectedRules.value.filter(c => vhdlRulesAll.value.some(r => r.rule_code === c)).length)


// CWE 相关（本页主要管理FPGA，但保存/导入配置复用通用结构，需提供占位）
const cweAccurateRules = ref([])
const cweUncertainRules = ref([])
const selectedCweAccurateRules = ref([])
const selectedCweUncertainRules = ref([])

// 规则分类覆盖（用于移动规则）
const ruleOverrides = ref({
  fpga: {}, // { "A-4-3": "uncertain" }
  cwe: {}   // { "S_01_01": "accurate" }
})

// 规则类型切换

// 保存配置相关
const saveConfigDialogVisible = ref(false)
const savingConfig = ref(false)
const saveConfigForm = reactive({
})

// 导入配置相关
const importConfigDialogVisible = ref(false)
const importingConfig = ref(false)
const configUploadRef = ref()
const selectedConfigFile = ref(null)
const configFileList = ref([])
const importPreview = ref(null)
const importConfigForm = reactive({
})

// 自定义过滤配置
const activeCollapseItems = ref([])
const customFilterList = ref([])  // [{ruleCode: 'GJB_R_01_01_01', keywords: 'kw1,kw2'}]

// 问题数量限制配置
const maxIssuesPerRule = ref(0) // 0表示不限制

// 进度数据
const totalIssues = ref(0)
const processedIssues = ref(0)
const filteredIssues = ref(0)
const aiAnalyzedIssues = ref(0)
const accurateIssues = ref(0)
const uncertainIssues = ref(0)
const currentStatus = ref('pending')
const showFirstDownload = ref(false)

// AI分析进度详情
const currentAnalyzingIssue = ref('')
const currentIssueIndex = ref(0)
const totalUncertainIssues = ref(0)
const toolCallsCount = ref(0)

// 双进度跟踪（GJB和CWE）
const fpgaProgress = reactive({
  totalIssues: 0,
  accurateIssues: 0,
  uncertainIssues: 0,
  filteredIssues: 0,
  retainedIssues: 0,
  aiProcessingTotal: 0,
  aiProcessedIssues: 0,
  processedIssues: 0,
  currentAnalyzingIssue: '',
  toolCallsCount: 0,
  progress: 0,
  status: 'pending',
  accurate_ready: false  // 新增：确定规则是否已就绪
})

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

const canStartProcessing = computed(() => {
  return selectedExcelFile.value && 
         selectedCodebaseFile.value && 
         selectedRules.value.length > 0
})

// 轮询相关
let pollInterval = null

// 组件挂载时加载规则
onMounted(async () => {
  await loadRules()
})

// 加载FPGA规则列表
const loadRules = async () => {
  try {
    const [accurateResponse, uncertainResponse] = await Promise.all([
      axios.get('/api/staticAnalysis/filterFpga/rules', { params: { accuracy: 'accurate' } }),
      axios.get('/api/staticAnalysis/filterFpga/rules', { params: { accuracy: 'uncertain' } })
    ])

    if (accurateResponse.data && accurateResponse.data.items) {
      accurateRules.value = accurateResponse.data.items
    }

    if (uncertainResponse.data && uncertainResponse.data.items) {
      uncertainRules.value = uncertainResponse.data.items
    }

    // 尝试加载默认配置
    try {
      const defaultConfig = await staticAnalysisFilterFpgaService.loadDefaultRulesConfig()
      if (defaultConfig.success && defaultConfig.has_config && defaultConfig.gjb_rules.length > 0) {
        // 使用默认配置
        const allFpgaRules = [
          ...accurateRules.value.map(r => r.rule_code),
          ...uncertainRules.value.map(r => r.rule_code)
        ]
        
        // 只选择配置中存在且在规则列表中的规则
        const validFpgaRules = defaultConfig.gjb_rules.filter(code => allFpgaRules.includes(code))
        selectedRules.value = validFpgaRules
        
        // 加载自定义过滤规则
        if (defaultConfig.custom_filters) {
          loadCustomFilters(defaultConfig.custom_filters)
          console.log('[DEBUG] 已加载自定义过滤规则:', Object.keys(defaultConfig.custom_filters).length, '条')
        }
        
        // 加载问题数量限制配置
        if (defaultConfig.max_issues_per_rule !== undefined) {
          maxIssuesPerRule.value = defaultConfig.max_issues_per_rule
          console.log('[DEBUG] 已加载问题数量限制配置:', defaultConfig.max_issues_per_rule)
        }
        
        console.log('[DEBUG] 已加载FPGA默认配置(来自gjb_rules):', validFpgaRules.length, '个规则')
      } else {
        // 没有默认配置，全选所有规则
        selectedRules.value = [
          ...accurateRules.value.map(rule => rule.rule_code),
          ...uncertainRules.value.map(rule => rule.rule_code)
        ]
      }
    } catch (configError) {
      // 加载默认配置失败，全选所有规则
      selectedRules.value = [
        ...accurateRules.value.map(rule => rule.rule_code),
        ...uncertainRules.value.map(rule => rule.rule_code)
      ]
    }

    rulesLoaded.value = true
  } catch (error) {
    ElMessage.error('加载FPGA规则列表失败: ' + error.message)
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

// 规则选择操作
const selectAllRules = () => {
  selectedRules.value = [
    ...accurateRules.value.map(rule => rule.rule_code),
    ...uncertainRules.value.map(rule => rule.rule_code)
  ]
}

const deselectAllRules = () => {
  selectedRules.value = []
}

const selectAccurateOnly = () => {
  selectedRules.value = accurateRules.value.map(rule => rule.rule_code)
}

const selectUncertainOnly = () => {
  selectedRules.value = uncertainRules.value.map(rule => rule.rule_code)
}

function selectAllVerilogRules()   { const s = new Set(verilogRulesAll.value.map(r => r.rule_code)); selectedRules.value = [...new Set([...selectedRules.value, ...s])] }
function deselectAllVerilogRules() { const s = new Set(verilogRulesAll.value.map(r => r.rule_code)); selectedRules.value = selectedRules.value.filter(c => !s.has(c)) }
function selectAllVhdlRules()      { const s = new Set(vhdlRulesAll.value.map(r => r.rule_code)); selectedRules.value = [...new Set([...selectedRules.value, ...s])] }
function deselectAllVhdlRules()    { const s = new Set(vhdlRulesAll.value.map(r => r.rule_code)); selectedRules.value = selectedRules.value.filter(c => !s.has(c)) }

// 移动规则到不确定
const moveRuleToUncertain = (ruleType, ruleCode) => {
  const before = ruleOverrides.value
  const nextForType = { ...(before[ruleType] || {}), [ruleCode]: 'uncertain' }
  ruleOverrides.value = { ...before, [ruleType]: nextForType }
  
  ElMessage.success(`规则 ${ruleCode} 已标记为"不确定"，点击"保存为默认配置"以永久生效`)
  try {
    console.log('[FPGA][MOVE] to uncertain:', ruleCode, {
      after_fpga_count: Object.keys(ruleOverrides.value.fpga || {}).length,
      snapshot: ruleOverrides.value
    })
  } catch (e) {}
}

// 移动规则到确定
const moveRuleToAccurate = (ruleType, ruleCode) => {
  const before = ruleOverrides.value
  const nextForType = { ...(before[ruleType] || {}), [ruleCode]: 'accurate' }
  ruleOverrides.value = { ...before, [ruleType]: nextForType }
  
  ElMessage.success(`规则 ${ruleCode} 已标记为"确定"，点击"保存为默认配置"以永久生效`)
  try {
    console.log('[FPGA][MOVE] to accurate:', ruleCode, {
      after_fpga_count: Object.keys(ruleOverrides.value.fpga || {}).length,
      snapshot: ruleOverrides.value
    })
  } catch (e) {}
}

// 判断规则是否被修改
const isRuleModified = (ruleType, ruleCode) => {
  return ruleOverrides.value[ruleType] && ruleOverrides.value[ruleType][ruleCode]
}

// 添加自定义过滤
const addCustomFilter = () => {
  customFilterList.value.push({
    ruleCode: '',
    keywords: ''
  })
}

// 删除自定义过滤
const removeCustomFilter = (index) => {
  customFilterList.value.splice(index, 1)
}

// 将customFilterList转换为对象格式
const getCustomFiltersObject = () => {
  const filters = {}
  customFilterList.value.forEach(filter => {
    if (filter.ruleCode && filter.keywords) {
      const keywords = filter.keywords.split(',').map(k => k.trim()).filter(k => k)
      if (keywords.length > 0) {
        filters[filter.ruleCode] = keywords
      }
    }
  })
  return filters
}

// 从对象格式加载到customFilterList
const loadCustomFilters = (customFilters) => {
  customFilterList.value = Object.entries(customFilters || {}).map(([ruleCode, keywords]) => ({
    ruleCode,
    keywords: Array.isArray(keywords) ? keywords.join(',') : keywords
  }))
}

// 显示保存配置对话框
const showSaveConfigDialog = () => {
  saveConfigDialogVisible.value = true
}

// 导出配置
const exportConfig = () => {
  try {
    // 构建配置对象
    const config = {
      fpga_rules: selectedRules.value,
      cwe_rules: [...selectedCweAccurateRules.value, ...selectedCweUncertainRules.value],
      rule_overrides: ruleOverrides.value,
      custom_filters: getCustomFiltersObject(),
      max_issues_per_rule: maxIssuesPerRule.value,
      version: "1.0",
      exported_at: new Date().toISOString(),
      exported_by: "静态分析过滤工具"
    }
    
    // 转换为JSON字符串
    const jsonStr = JSON.stringify(config, null, 2)
    
    // 创建Blob对象
    const blob = new Blob([jsonStr], { type: 'application/json' })
    
    // 创建下载链接
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    
    // 生成文件名（包含时间戳）
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5)
    link.download = `rules_config_${timestamp}.json`
    
    // 触发下载
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    // 释放URL对象
    URL.revokeObjectURL(url)
    
    ElMessage.success({
      message: `配置已导出：${link.download}`,
      duration: 3000
    })
    
  } catch (error) {
    ElMessage.error('导出配置失败: ' + error.message)
  }
}

// 显示导入配置对话框
const showImportConfigDialog = () => {
  importConfigForm.password = ''
  selectedConfigFile.value = null
  configFileList.value = []
  importPreview.value = null
  importConfigDialogVisible.value = true
}

// 处理配置文件选择
const handleConfigFileChange = (file) => {
  selectedConfigFile.value = file.raw
  configFileList.value = [file]
  
  // 读取文件内容并预览
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const config = JSON.parse(e.target.result)
      
      // 验证配置格式
      if (!config.fpga_rules || !config.cwe_rules) {
        throw new Error('配置文件格式不正确，缺少必要字段')
      }
      
      // 生成预览信息
      const gjbOverrides = config.rule_overrides?.gjb || {}
      const cweOverrides = config.rule_overrides?.cwe || {}
      const overrideCount = Object.keys(gjbOverrides).length + Object.keys(cweOverrides).length
      
      importPreview.value = {
        gjb_count: config.fpga_rules.length,
        cwe_count: config.cwe_rules.length,
        has_overrides: overrideCount > 0,
        override_count: overrideCount,
        max_issues_per_rule: config.max_issues_per_rule || 0,
        config: config
      }
      
    } catch (error) {
      ElMessage.error('解析配置文件失败: ' + error.message)
      selectedConfigFile.value = null
      configFileList.value = []
      importPreview.value = null
    }
  }
  reader.readAsText(file.raw)
}

// 确认导入配置
const confirmImportConfig = async () => {
  if (!importConfigForm.password) {
    ElMessage.error('请输入管理员密码')
    return
  }
  
  if (!importPreview.value) {
    ElMessage.error('请先选择配置文件')
    return
  }
  
  try {
    importingConfig.value = true
    
    const config = importPreview.value.config
    
    // 调用保存配置API
    const response = await staticAnalysisFilterFpgaService.saveDefaultRulesConfig(
      importConfigForm.password,
      config.fpga_rules,
      config.cwe_rules,
      config.rule_overrides || { gjb: {}, cwe: {} },
      config.custom_filters || {},
      config.max_issues_per_rule || 0
    )
    
    if (response.success) {
      ElMessage.success('配置导入成功！')
      importConfigDialogVisible.value = false
      
      // 应用导入的配置到前端
      selectedRules.value = config.fpga_rules.filter(code => {
        const allFpgaRules = [
          ...accurateRules.value.map(r => r.rule_code),
          ...uncertainRules.value.map(r => r.rule_code)
        ]
        return allFpgaRules.includes(code)
      })
      
      selectedCweAccurateRules.value = config.cwe_rules.filter(code => {
        return cweAccurateRules.value.some(r => r.rule_code === code)
      })
      
      selectedCweUncertainRules.value = config.cwe_rules.filter(code => {
        return cweUncertainRules.value.some(r => r.rule_code === code)
      })
      
      // 如果有规则覆盖，更新ruleOverrides
      if (config.rule_overrides) {
        ruleOverrides.value = config.rule_overrides
      }
      
      // 加载自定义过滤规则
      if (config.custom_filters) {
        loadCustomFilters(config.custom_filters)
      }
      
      // 加载问题数量限制配置
      maxIssuesPerRule.value = config.max_issues_per_rule || 0
      
      // 重新加载规则（因为可能有规则分类变更）
      await loadRules()
      // 清空规则覆盖（因为已经应用到数据库了）
      ruleOverrides.value = { gjb: {}, cwe: {} }
      
      ElMessage.success({
        message: `已导入 ${config.gjb_rules.length} 条GJB规则和 ${config.cwe_rules.length} 条CWE规则`,
        duration: 3000
      })
    }
  } catch (error) {
    if (error.response && error.response.status === 403) {
      ElMessage.error('管理员密码错误')
    } else {
      ElMessage.error('导入配置失败: ' + error.message)
    }
  } finally {
    importingConfig.value = false
  }
}

// 确认保存配置
const confirmSaveConfig = async () => {
  try {
    savingConfig.value = true

    // 收集所有选中的规则
    const gjbRules = selectedRules.value
    const cweRules = [...selectedCweAccurateRules.value, ...selectedCweUncertainRules.value]

    // 统计规则覆盖信息
    const fpgaOverrideCount = Object.keys(ruleOverrides.value.fpga || {}).length
    const cweOverrideCount = Object.keys(ruleOverrides.value.cwe || {}).length
    const hasOverrides = fpgaOverrideCount > 0 || cweOverrideCount > 0

    // 获取自定义过滤规则
    const customFilters = getCustomFiltersObject()

    const response = await staticAnalysisFilterFpgaService.saveDefaultRulesConfig(
      gjbRules,
      cweRules,
      ruleOverrides.value,
      customFilters,
      maxIssuesPerRule.value
    )
    try {
      console.log('[FPGA][SAVE] sending overrides:', {
        fpga: Object.keys(ruleOverrides.value.fpga || {}).length,
        cwe: Object.keys(ruleOverrides.value.cwe || {}).length,
      })
    } catch (e) {}

    if (response.success) {
      let message = '默认规则配置已保存！'
      if (hasOverrides) {
        message += `\n已将 ${fpgaOverrideCount} 条FPGA规则和 ${cweOverrideCount} 条CWE规则的分类永久更新到数据库`
      }
      ElMessage.success(message)
      saveConfigDialogVisible.value = false
      
      // 清空规则覆盖记录
      ruleOverrides.value = { fpga: {}, cwe: {} }
      
      // 重新加载规则（从数据库获取最新分类）
      await loadRules()
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
  console.log('[DEBUG] startProcessing 被调用')
  if (!canStartProcessing.value) {
    console.log('[DEBUG] 检查失败，缺少必需文件或规则')
    ElMessage.error('请确保已上传所有必需文件并选择至少一个FPGA规则')
    return
  }

  try {
    console.log('[DEBUG] 开始上传FPGA文件...')
    processing.value = true
    
    // 使用FPGA规则
    console.log('[DEBUG] 选中的FPGA规则数:', selectedRules.value.length)
    
    // 准备FormData
    const formData = new FormData()
    formData.append('excel_file', selectedExcelFile.value.raw)
    formData.append('codebase_file', selectedCodebaseFile.value.raw)
    formData.append('selected_rules', JSON.stringify(selectedRules.value))
    
    // 调用FPGA专用API
    const response = await axios.post(
      '/api/staticAnalysis/filterFpga/start-processing',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    )
    console.log('[DEBUG] FPGA上传响应:', response.data)
    
    if (!response || !response.data) {
      throw new Error('服务器无响应')
    }
    
    if (response.data.success) {
      // 优先使用task_id，如果没有则使用session_id（向后兼容）
      sessionId.value = response.data.task_id || response.data.session_id
      console.log('[DEBUG] FPGA上传成功! taskId/sessionId:', sessionId.value)
      
      // 检查是否因并发限制而跳过AI审查
      if (response.data.ai_disabled) {
        console.log('[DEBUG] 检测到ai_disabled标志，显示并发限制警告')
        // 并发过高：关闭AI审查，仅提供"未经AI过滤"下载
        ElMessageBox.alert(
          '当前使用人数过多，无法进行AI审查，请下载未经AI过滤的问题单',
          '⚠️ 受模型并发限制',
          {
            confirmButtonText: '我知道了',
            type: 'warning',
            center: true,
            showClose: false
          }
        )
        
        // 等待后端处理完成，然后获取统计数据
        try {
          console.log('[DEBUG] 等待后端处理统计数据...')
          await new Promise(resolve => setTimeout(resolve, 2000))
          
          // 获取统计数据
          const progressResponse = await axios.get(`/api/staticAnalysis/filterFpga/progress/${sessionId.value}`)
          console.log('[DEBUG] 获取到统计数据:', progressResponse.data)
          
          if (progressResponse.data && progressResponse.data.success) {
            const progress = progressResponse.data.progress
            // 更新FPGA进度统计
            fpgaProgress.totalIssues = progress.total_issues || 0
            fpgaProgress.accurateIssues = progress.accurate_issues || 0
            fpgaProgress.uncertainIssues = progress.uncertain_issues || 0
            fpgaProgress.filteredIssues = progress.filtered_issues || 0
            fpgaProgress.retainedIssues = (progress.total_issues || 0) - (progress.filtered_issues || 0)
            fpgaProgress.aiProcessingTotal = 0  // 跳过AI审查
            fpgaProgress.aiProcessedIssues = 0
            fpgaProgress.progress = 100
          }
        } catch (error) {
          console.error('[DEBUG] 获取统计数据失败:', error)
        }
        
        // 立即显示下载按钮，允许用户下载未经AI过滤的问题单
        fpgaProgress.accurate_ready = true
        fpgaProgress.status = 'completed'
        // 不启动轮询，停在当前页，等待用户手动下载
        return
      } else {
        ElMessage.success('FPGA文件上传成功，正在智能过滤处理中...')
      }
      
      // 获取task_id并显示FPGA代码视图地址通知
      try {
        // 等待一下让后台处理创建数据库记录
        await new Promise(resolve => setTimeout(resolve, 2000))
        
        const taskIdResponse = await staticAnalysisFilterFpgaService.getTaskIdBySession(sessionId.value)
        if (taskIdResponse && taskIdResponse.success && taskIdResponse.task_id) {
          const taskId = taskIdResponse.task_id
          const fpgaCodeViewUrl = `http://172.16.32.81:8085/static-analysis/fpga-code-view/${taskId}`
          
          // 显示FPGA代码视图通知
          ElNotification({
            title: '✅ FPGA代码视图已就绪',
            message: `
              <div style="margin-top: 12px;">
                <div style="background: #f0f9ff; padding: 12px; border-radius: 6px; border-left: 3px solid #409EFF; margin-bottom: 12px;">
                  <div style="color: #606266; font-size: 13px; margin-bottom: 6px;">📍 FPGA代码视图地址：</div>
                  <div style="color: #303133; font-size: 14px; font-family: monospace; word-break: break-all;">${fpgaCodeViewUrl}</div>
                  <div style="color: #718096; font-size: 12px; margin-top: 4px;">任务ID: ${taskId}</div>
                </div>
                <a href="${fpgaCodeViewUrl}" target="_blank" 
                   style="display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; 
                          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          color: white; text-decoration: none; border-radius: 6px; 
                          font-weight: 500; font-size: 14px; transition: all 0.3s; 
                          box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);"
                   onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(102, 126, 234, 0.4)';"
                   onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 8px rgba(102, 126, 234, 0.3)';">
                  🔗 查看FPGA代码视图
                </a>
              </div>
            `,
            dangerouslyUseHTMLString: true,
            type: 'success',
            duration: 0,  // 不自动关闭
            position: 'top-right',
            showClose: true,
            offset: 80
          })
          
          // 下载包含代码视图地址的txt文件
          const txtContent = `FPGA 静态分析代码视图地址
===========================================

任务ID: ${taskId}
生成时间: ${new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })}

FPGA 代码视图:
${fpgaCodeViewUrl}

===========================================
说明: 请使用浏览器打开以上链接查看静态分析结果
`
          const blob = new Blob([txtContent], { type: 'text/plain;charset=utf-8' })
          const url = window.URL.createObjectURL(blob)
          const link = document.createElement('a')
          link.href = url
          link.download = `FPGA代码视图地址_${taskId}_${new Date().getTime()}.txt`
          document.body.appendChild(link)
          link.click()
          document.body.removeChild(link)
          window.URL.revokeObjectURL(url)
          
          ElMessage.success('FPGA代码视图地址已下载到txt文件')
        } else {
          // 如果获取task_id失败，使用session_id作为后备
          const fpgaCodeViewUrl = `http://172.16.32.81:8085/static-analysis/fpga-code-view/${sessionId.value}`
          
          ElNotification({
            title: '✅ FPGA代码视图已就绪',
            message: `
              <div style="margin-top: 8px;">
                <p>代码视图: <a href="${fpgaCodeViewUrl}" target="_blank" style="color: #409EFF;">${fpgaCodeViewUrl}</a></p>
              </div>
            `,
            dangerouslyUseHTMLString: true,
            type: 'success',
            duration: 0,
            position: 'top-right',
            showClose: true,
            offset: 80
          })
        }
      } catch (error) {
        console.error('[DEBUG] 获取task_id失败:', error)
        // 使用session_id作为后备
        const fpgaCodeViewUrl = `http://172.16.32.81:8085/static-analysis/fpga-code-view/${sessionId.value}`
        ElNotification({
          title: '✅ FPGA智能过滤任务已启动',
          message: `代码视图: ${fpgaCodeViewUrl}`,
          type: 'success',
          duration: 8000,
          position: 'top-right'
        })
      }
      
      // 开始轮询FPGA处理进度
      startStatusPolling()
    } else {
      throw new Error(response.error || response.message || '上传失败')
    }
  } catch (error) {
    console.log('[DEBUG] 上传过程发生错误:', error)
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
      (currentStatus.value === 'completed')) {
    showFirstDownload.value = true
  }
}

// 开始状态轮询
const startStatusPolling = () => {
  console.log('[DEBUG] startStatusPolling 被调用')
  console.log('[DEBUG] totalIssues:', totalIssues.value)
  
  checkStatus()
  
  // 根据问题数量调整轮询间隔
  let pollIntervalTime = 5000 // 默认5秒
  if (totalIssues.value > 3000) {
    pollIntervalTime = 10000 // 大于3000个问题时，改为10秒轮询
  } else if (totalIssues.value > 1000) {
    pollIntervalTime = 8000 // 大于1000个问题时，改为8秒轮询
  }
  
  console.log('[DEBUG] 轮询间隔:', pollIntervalTime, 'ms')
  
  pollInterval = setInterval(() => {
    console.log('[DEBUG] 轮询回调触发 - processing:', processing.value, 'completed:', completed.value)
    if (completed.value || !processing.value) {
      clearInterval(pollInterval)
      pollInterval = null
      return
    }
    checkStatus()
  }, pollIntervalTime)
  
  console.log('[DEBUG] setInterval 已设置, pollInterval:', pollInterval)
}

// 检查FPGA处理状态
const checkStatus = async () => {
  console.log('[DEBUG] checkStatus 被调用, sessionId:', sessionId.value)
  if (!sessionId.value) {
    console.log('[DEBUG] sessionId 为空，跳过检查')
    return
  }

  try {
    console.log('[DEBUG] 开始请求FPGA进度:', sessionId.value)
    const response = await axios.get(`/api/staticAnalysis/filterFpga/progress/${sessionId.value}`)
    console.log('[DEBUG] FPGA进度响应:', response.data)
    
    if (!response.data || !response.data.success) {
      return
    }
    
    // 如果响应中有task_id且当前是session_id，更新为task_id
    if (response.data.task_id && response.data.task_id !== sessionId.value) {
      console.log('[DEBUG] 更新sessionId为task_id:', response.data.task_id)
      sessionId.value = response.data.task_id
    }
    
    const progress = response.data.progress
    
    // 更新FPGA进度
    fpgaProgress.totalIssues = progress.total_issues || 0
    fpgaProgress.accurateIssues = progress.accurate_issues || 0
    fpgaProgress.uncertainIssues = progress.uncertain_issues || 0
    fpgaProgress.filteredIssues = progress.filtered_issues || 0
    fpgaProgress.retainedIssues = (progress.total_issues || 0) - (progress.filtered_issues || 0)
    // 使用后端提供的仅“不确定且勾选”的总量
    fpgaProgress.aiProcessingTotal = progress.ai_processing_total || progress.uncertain_selected_issues || progress.uncertain_issues || 0
    // 仅统计不确定规则的已处理数量：processed_issues - accurate_issues
    const uncertainProcessed = Math.max((progress.processed_issues || 0) - (progress.accurate_issues || 0), 0)
    fpgaProgress.aiProcessedIssues = Math.min(uncertainProcessed, fpgaProgress.aiProcessingTotal)
    fpgaProgress.processedIssues = progress.processed_issues || 0
    fpgaProgress.currentAnalyzingIssue = progress.current_analyzing_issue || ''
    fpgaProgress.toolCallsCount = progress.tool_calls_count || 0
    // 进度条显示AI审查进度（仅不确定且勾选）
    if (fpgaProgress.status === 'completed') {
      fpgaProgress.progress = 100
    } else {
      fpgaProgress.progress = fpgaProgress.aiProcessingTotal > 0
        ? Math.round((fpgaProgress.aiProcessedIssues / fpgaProgress.aiProcessingTotal) * 100)
        : 0
    }
    fpgaProgress.status = progress.status || 'pending'
    fpgaProgress.accurate_ready = progress.accurate_ready || false
    
    console.log('[DEBUG] FPGA状态更新:', {
      status: fpgaProgress.status,
      progress: fpgaProgress.progress,
      aiProcessed: fpgaProgress.aiProcessedIssues,
      aiTotal: fpgaProgress.aiProcessingTotal,
      accurate_ready: fpgaProgress.accurate_ready
    })
    
    // 判断是否完成
    if (fpgaProgress.status === 'completed') {
      console.log('[DEBUG] ✅ FPGA任务已完成，停止轮询')
      processing.value = false
      completed.value = true
      
      if (pollInterval) {
        clearInterval(pollInterval)
        pollInterval = null
      }
      
      ElMessage.success('FPGA静态分析处理完成！')
    }
  } catch (error) {
    console.error('[ERROR] 获取详细状态失败:', error)
    // 单次查询失败不停止轮询
  }
}

// 进度相关方法
const getProgressTitle = () => {
  switch (currentStatus.value) {
    case 'processing':
      return '🔍 正在分析确定规则的问题...'
    case 'ai_analyzing':
      return '🤖 AI正在深度分析不确定规则的问题...'
    case 'completed':
      return '✅ 智能过滤处理完成！'
    default:
      return '⚡ 正在处理中...'
  }
}

const getStatusText = (status) => {
  // 如果没传status，使用currentStatus
  const statusToCheck = status || currentStatus.value
  switch (statusToCheck) {
    case 'processing':
      return 'AI分析中'
    case 'completed':
      return '已完成'
    case 'pending':
      return '等待中'
    case 'error':
      return '错误'
    default:
      return '处理中'
  }
}

const getProgressStatusByState = (status) => {
  if (status === 'completed') {
    return 'success'
  } else if (status === 'error') {
    return 'exception'
  }
  return undefined
}

const getStatusTagType = (status) => {
  // 如果没传status，使用currentStatus
  const statusToCheck = status || currentStatus.value
  switch (statusToCheck) {
    case 'processing':
      return 'primary'
    case 'ai_analyzing':
      return 'warning'
    case 'completed':
      return 'success'
    case 'error':
      return 'danger'
    default:
      return 'info'
  }
}

const getProgressStatus = () => {
  if (currentStatus.value === 'completed') {
    return 'success'
  } else {
    return 'active'
  }
}

const getPhaseClass = (phase) => {
  if (phase === 'processing') {
    if (currentStatus.value === 'processing') return 'active'
    if (currentStatus.value === 'ai_analyzing' || currentStatus.value === 'completed') return 'completed'
    return 'pending'
  } else if (phase === 'ai_analyzing') {
    if (currentStatus.value === 'ai_analyzing') return 'active'
    if (currentStatus.value === 'completed') return 'completed'
    return 'pending'
  }
  return 'pending'
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

// 下载FPGA确定规则问题单
const downloadFpgaAccurate = async () => {
  if (!sessionId.value) {
    ElMessage.error('会话ID不存在')
    return
  }

  try {
    downloadingFpgaAccurate.value = true
    
    const url = `/api/staticAnalysis/filterFpga/download-accurate/${sessionId.value}`
    const response = await fetch(url)
    
    if (!response.ok) {
      throw new Error(`下载失败: ${response.statusText}`)
    }
    
    const contentDisposition = response.headers.get('Content-Disposition')
    let filename = 'FPGA确定规则问题单.xlsx'
    if (contentDisposition) {
      const matches = contentDisposition.match(/filename="?(.+?)"?$/)
      if (matches && matches[1]) {
        filename = decodeURIComponent(matches[1])
      }
    }
    
    const blob = await response.blob()
    const blobUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = blobUrl
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(blobUrl)
    
    ElMessage.success('FPGA确定规则问题单下载成功')
    
  } catch (error) {
    ElMessage.error('下载失败: ' + error.message)
  } finally {
    downloadingFpgaAccurate.value = false
  }
}

// 下载FPGA完整问题单
const downloadFpgaFull = async () => {
  if (!sessionId.value) {
    ElMessage.error('会话ID不存在')
    return
  }

  try {
    downloadingFpgaFull.value = true
    
    const url = `/api/staticAnalysis/filterFpga/download-full/${sessionId.value}`
    const response = await fetch(url)
    
    if (!response.ok) {
      throw new Error(`下载失败: ${response.statusText}`)
    }
    
    const contentDisposition = response.headers.get('Content-Disposition')
    let filename = 'FPGA完整问题单.xlsx'
    if (contentDisposition) {
      const matches = contentDisposition.match(/filename="?(.+?)"?$/)
      if (matches && matches[1]) {
        filename = decodeURIComponent(matches[1])
      }
    }
    
    const blob = await response.blob()
    const blobUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = blobUrl
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(blobUrl)
    
    ElMessage.success('FPGA完整问题单下载成功')
    
  } catch (error) {
    ElMessage.error('下载失败: ' + error.message)
  } finally {
    downloadingFpgaFull.value = false
  }
}

// 新增：FPGA 四分分类下载 loading
const downloadingFpgaAllSplit = ref(false)
const downloadingFpgaFullSplit = ref(false)

// 下载FPGA全部问题单（未经AI过滤，四分分类）
const downloadFpgaAllSplit = async () => {
  if (!sessionId.value) {
    ElMessage.error('会话ID不存在')
    return
  }
  try {
    downloadingFpgaAllSplit.value = true
    const url = `/api/staticAnalysis/filterFpga/download-split/${sessionId.value}?highlight_ai=false`
    const response = await fetch(url)
    if (!response.ok) throw new Error(`下载失败: ${response.statusText}`)
    const contentDisposition = response.headers.get('Content-Disposition')
    let filename = 'FPGA_四分类问题单（未经AI过滤）.xlsx'
    if (contentDisposition) {
      const matches = contentDisposition.match(/filename="?(.+?)"?$/)
      if (matches && matches[1]) filename = decodeURIComponent(matches[1])
    }
    const blob = await response.blob()
    const blobUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = blobUrl
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(blobUrl)
    ElMessage.success('FPGA全部问题单（四个Sheet）下载成功')
  } catch (error) {
    ElMessage.error('下载失败: ' + error.message)
  } finally {
    downloadingFpgaAllSplit.value = false
  }
}

// 下载FPGA完整问题单（AI过滤后，四分分类+AI高亮）
const downloadFpgaFullSplit = async () => {
  if (!sessionId.value) {
    ElMessage.error('会话ID不存在')
    return
  }

  let cancelled = false
  let boxVisible = false

  try {
    downloadingFpgaFullSplit.value = true

    ElMessageBox.confirm(
      'FPGA完整问题单正在后台整理并生成 Excel，请稍候…（生成完成后会自动开始下载）',
      '正在生成 FPGA 完整问题单',
      {
        confirmButtonText: '继续等待',
        cancelButtonText: '取消',
        showCancelButton: true,
        closeOnClickModal: false,
        closeOnPressEscape: false,
        type: 'info'
      }
    ).catch(() => {
      cancelled = true
    })
    boxVisible = true

    const maxWaitMs = 10 * 60 * 1000
    const intervalMs = 2000
    const start = Date.now()
    let lastError = null

    while (!cancelled && Date.now() - start < maxWaitMs) {
      try {
    const url = `/api/staticAnalysis/filterFpga/download-split/${sessionId.value}?highlight_ai=true`
    const response = await fetch(url)
        if (!response.ok) {
          throw new Error(`下载失败: ${response.statusText}`)
        }

    const contentDisposition = response.headers.get('Content-Disposition')
        let filename = 'FPGA_四分类问题单（AI过滤后）.xlsx'
    if (contentDisposition) {
      const matches = contentDisposition.match(/filename="?(.+?)"?$/)
      if (matches && matches[1]) filename = decodeURIComponent(matches[1])
    }

    const blob = await response.blob()
    const blobUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = blobUrl
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(blobUrl)

        if (boxVisible) {
          ElMessageBox.close()
          boxVisible = false
        }
    ElMessage.success('FPGA完整问题单（四个Sheet，含AI确认高亮）下载成功')
        return
      } catch (error) {
        lastError = error
      }

      await new Promise(resolve => setTimeout(resolve, intervalMs))
    }

    if (cancelled) {
      throw new Error('已取消等待生成')
    }
    throw lastError || new Error('生成超时，请稍后再试')
  } catch (error) {
    ElMessage.error('下载失败: ' + error.message)
  } finally {
    if (boxVisible) {
      ElMessageBox.close()
    }
    downloadingFpgaFullSplit.value = false
  }
}

// 打开代码视图（FPGA使用task_id）
const openCodeView = async (ruleType) => {
  if (!sessionId.value) {
    ElMessage.error('会话ID不存在')
    return
  }

  try {
    if (ruleType === 'fpga') {
      // 先通过session_id换取task_id
      const resp = await staticAnalysisFilterFpgaService.getTaskIdBySession(sessionId.value)
      if (!resp || !resp.success || !resp.task_id) {
        throw new Error('无法获取任务ID')
      }
      const taskId = resp.task_id
      window.open(`/static-analysis/fpga-code-view/${taskId}`, '_blank')
    } else {
      window.open(`/static-analysis/code-view/${sessionId.value}?type=${ruleType}`, '_blank')
    }
  } catch (e) {
    ElMessage.error('打开代码视图失败：' + (e.message || '未知错误'))
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
.static-analysis-filter {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
  background: #f8fafc;
  min-height: 100vh;
}

/* 头部样式 */
.header {
  text-align: center;
  /* 统一与下方内容的左右边界，对齐为同一内宽 */
  width: 100%;
  max-width: 1320px; /* 内容内宽：确保与下方模块保持完全一致 */
  margin: 0 auto 40px auto;
  padding: 30px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  color: white;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
}

.header h2 {
  margin: 0 0 10px 0;
  font-size: 28px;
  font-weight: bold;
}

.description {
  margin: 0;
  font-size: 16px;
  opacity: 0.9;
}

/* 主要内容区域 */
.main-content {
  display: flex;
  flex-direction: column;
  gap: 30px;
  /* 与头部保持相同的内宽，左右边界严格对齐 */
  width: 100%;
  max-width: 1320px;
  margin: 0 auto;
}

/* 文件上传容器 */
.upload-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.upload-item {
  background: white;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: none;
  transition: all 0.3s ease;
  min-height: 200px;
  display: flex;
  flex-direction: column;
}

.upload-item:hover {
  box-shadow: 0 8px 30px rgba(64, 158, 255, 0.15);
  transform: translateY(-2px);
}

.upload-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.upload-header h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.upload-dragger.compact {
  width: 100%;
}

.upload-dragger.compact :deep(.el-upload-dragger) {
  height: 140px; /* 增加高度让组件更饱满 */
  border-radius: 8px;
  border: 2px dashed #d9d9d9;
  background: #fafafa;
  transition: all 0.3s ease;
}

.upload-dragger.compact :deep(.el-icon--upload) {
  font-size: 32px;
  margin-bottom: 8px;
}

.upload-dragger.compact :deep(.el-upload__text) {
  font-size: 14px;
}

.upload-dragger.compact :deep(.el-upload__tip) {
  font-size: 12px;
  margin-top: 8px;
}

/* 规则选择区域 */
.rules-section {
  background: white;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.rules-header {
  margin-bottom: 20px;
}

.rules-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.rules-title h3 {
  margin: 0;
  color: #303133;
  font-size: 18px;
}

.selected-count {
  font-size: 14px;
  color: #409eff;
  font-weight: bold;
}

.rules-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.rules-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.rules-column {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  background: #fafafa;
}

.column-header {
  padding: 15px 20px;
  color: white;
  font-weight: bold;
}

.accurate-column .column-header {
  background: linear-gradient(135deg, #67c23a, #85ce61);
}

.uncertain-column .column-header {
  background: linear-gradient(135deg, #e6a23c, #f0a020);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
}

.header-content h4 {
  margin: 0;
  font-size: 16px;
}

.rule-count {
  background: rgba(255, 255, 255, 0.2);
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
}

.header-desc {
  margin: 0;
  font-size: 12px;
  opacity: 0.9;
}

.rules-list {
  max-height: 350px;
  overflow-y: auto;
  padding: 15px;
  background: white;
}

.rule-item {
  margin-bottom: 12px;
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  background: #fafafa;
  transition: all 0.3s;
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  /* 预留右侧空间给悬浮操作按钮，避免长文本覆盖 */
  padding-right: 140px;
}

.rule-item:hover {
  border-color: #409eff;
  background: #f0f9ff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

/* 被修改的规则高亮 */
.rule-item.rule-modified {
  border: 2px solid #f56c6c;
  background: #fff5f5;
}

.rule-item.rule-modified::before {
  content: '●';
  color: #f56c6c;
  position: absolute;
  left: -10px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 20px;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.rule-checkbox {
  flex: 1;
}

.rule-content {
  margin-left: 24px;
}

/* 移动规则按钮 */
.move-rule-btn {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  min-width: 100px;
  font-size: 12px;
  opacity: 0;
  transition: opacity 0.3s;
  z-index: 2; /* 提高层级，确保不被文字覆盖 */
}

.rule-item:hover .move-rule-btn {
  opacity: 1;
}

.rule-item.rule-modified .move-rule-btn {
  opacity: 1;
}

/* 限制复选框内容最大宽度，避免与按钮重叠 */
.rule-checkbox {
  flex: 1;
  max-width: calc(100% - 120px);
}

.rule-name {
  font-weight: bold;
  color: #303133;
  margin-bottom: 6px;
  font-size: 13px;
  line-height: 1.4;
  white-space: normal;
  word-wrap: break-word;
  overflow-wrap: break-word;
  max-width: 100%;
}

.rule-description {
  color: #606266;
  font-size: 12px;
  margin-bottom: 8px;
  line-height: 1.4;
}

.rule-meta {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

/* 开始处理区域 */
.start-processing {
  background: white;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  text-align: center;
}

.processing-info {
  display: flex;
  justify-content: center;
  gap: 30px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #606266;
}

.start-btn {
  font-size: 16px;
  padding: 12px 30px;
  border-radius: 8px;
}

/* 双进度区域样式 */
.dual-progress-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 1320px;
  margin: 0 auto;
}

.progress-card {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.progress-card:hover {
  box-shadow: 0 6px 25px rgba(0, 0, 0, 0.12);
}

.fpga-progress-card {
  border-left: 4px solid #409EFF;
}

.cwe-progress-card {
  border-left: 4px solid #67C23A;
}

.card-header-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 30px;
  color: white;
}

.fpga-banner {
  background: linear-gradient(135deg, #409EFF 0%, #3a8ee6 100%);
}

.cwe-banner {
  background: linear-gradient(135deg, #67C23A 0%, #5daf34 100%);
}

.card-header-banner h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.card-content {
  padding: 25px 30px;
}

.stat-grid-compact {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
  margin-top: 20px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
}

.stat-item .stat-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.stat-item .stat-value {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.fpga-analysis {
  background: linear-gradient(135deg, #e6f7ff 0%, #bae7ff 100%);
  border-left: 3px solid #409EFF;
}

.cwe-analysis {
  background: linear-gradient(135deg, #f6ffed 0%, #d9f7be 100%);
  border-left: 3px solid #67C23A;
}

/* 旧的进度区域样式（保留向后兼容） */
.progress-section {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
}

.progress-header h3 {
  margin: 0;
  color: #303133;
  font-size: 20px;
}

.main-progress {
  margin-bottom: 30px;
}

.main-progress :deep(.el-progress-bar__outer) {
  border-radius: 8px;
}

.main-progress :deep(.el-progress-bar__inner) {
  border-radius: 8px;
}

.progress-text {
  font-size: 14px;
  font-weight: bold;
}

.current-analysis-info {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  color: white;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.analysis-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  font-size: 16px;
  font-weight: 600;
}

.analysis-icon {
  font-size: 24px;
}

.analysis-title {
  flex: 1;
}

.analysis-progress {
  background: rgba(255, 255, 255, 0.2);
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 14px;
}

.analysis-content {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 12px 16px;
}

.issue-name {
  font-size: 15px;
  font-weight: 500;
  margin-bottom: 8px;
  line-height: 1.5;
}

.tool-calls {
  font-size: 13px;
  opacity: 0.9;
}

/* 后台整理提示 */
.preparing-hint {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  margin: 18px 0 22px;
  padding: 16px 18px;
  border-radius: 12px;
  border: 1px solid rgba(64, 158, 255, 0.18);
  box-shadow: 0 8px 20px rgba(64, 158, 255, 0.08);
}

.preparing-hint-fpga {
  background: linear-gradient(135deg, rgba(230, 247, 255, 0.95) 0%, rgba(243, 249, 255, 0.98) 100%);
}

.preparing-hint-icon {
  flex-shrink: 0;
  width: 38px;
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(64, 158, 255, 0.14);
  font-size: 18px;
}

.preparing-hint-spinner-wrap {
  background: rgba(64, 158, 255, 0.12);
}

.preparing-hint-spinner {
  font-size: 18px;
  color: #409eff;
  animation: preparing-spin 1s linear infinite;
}

.preparing-hint-content {
  min-width: 0;
}

.preparing-hint-title {
  margin-bottom: 6px;
  color: #1f2d3d;
  font-size: 15px;
  font-weight: 700;
}

.preparing-hint-text {
  color: #5c6b77;
  font-size: 13px;
  line-height: 1.7;
}

@keyframes preparing-spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 15px;
  margin-bottom: 30px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  background: #fafafa;
}

.stat-card.primary { border-left: 4px solid #409eff; }
.stat-card.success { border-left: 4px solid #67c23a; }
.stat-card.warning { border-left: 4px solid #e6a23c; }
.stat-card.info { border-left: 4px solid #909399; }
.stat-card.danger { border-left: 4px solid #f56c6c; }
.stat-card.purple { border-left: 4px solid #9c27b0; }

.stat-icon {
  font-size: 20px;
}

.stat-value {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
  line-height: 1;
}

.stat-label {
  font-size: 12px;
  color: #606266;
  margin-top: 2px;
}

/* 阶段指示器 */
.phase-indicators {
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 30px 0;
  gap: 20px;
}

.phase-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px 20px;
  border-radius: 8px;
  border: 2px solid #e4e7ed;
  background: #fafafa;
  transition: all 0.3s;
}

.phase-item.active {
  border-color: #409eff;
  background: #e6f7ff;
  color: #1890ff;
}

.phase-item.completed {
  border-color: #67c23a;
  background: #f6ffed;
  color: #52c41a;
}

.phase-item.pending {
  border-color: #d9d9d9;
  background: #f5f5f5;
  color: #8c8c8c;
}

.phase-icon {
  font-size: 18px;
}

.phase-title {
  font-weight: bold;
  font-size: 14px;
}

.phase-desc {
  font-size: 12px;
  opacity: 0.8;
}

.phase-divider {
  width: 30px;
  height: 2px;
  background: #e4e7ed;
  border-radius: 1px;
}

/* 第一阶段下载 */
.first-download {
  text-align: center;
  margin-top: 25px;
}

.download-alert {
  margin-bottom: 15px;
}

.download-btn-wide {
  min-width: 266px; /* 380px 缩短 3/10 ≈ 266px */
  padding: 10px 20px;
}

/* 结果区域样式 */
.result-section {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  text-align: center;
}

.success-header {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-bottom: 30px;
}

.success-icon {
  font-size: 48px;
  color: #67c23a;
}

.success-content h3 {
  margin: 0 0 8px 0;
  color: #67c23a;
  font-size: 24px;
}

.success-content p {
  margin: 0;
  color: #606266;
  font-size: 16px;
}

.result-summary {
  display: flex;
  justify-content: center;
  gap: 40px;
  margin: 30px 0;
  flex-wrap: wrap;
}

.summary-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.summary-item.highlight {
  padding: 15px 20px;
  background: linear-gradient(135deg, #f0f9ff, #e6f7ff);
  border-radius: 8px;
  border: 2px solid #409eff;
}

.summary-label {
  font-size: 14px;
  color: #606266;
}

.summary-item.highlight .summary-label {
  font-weight: bold;
  color: #409eff;
}

.summary-value {
  font-size: 28px;
  font-weight: bold;
}

.summary-value.primary { color: #409eff; }
.summary-value.success { color: #67c23a; }
.summary-value.info { color: #409eff; }
.summary-value.warning { color: #e6a23c; }
.summary-value.purple { color: #9c27b0; }

/* 详细统计信息样式 */
.detailed-stats {
  margin-top: 20px;
  background: #f8fafc;
  border-radius: 8px;
  padding: 15px;
}

/* 下载按钮区域 */
./* 后台整理提示 */
.preparing-hint {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  margin: 18px 0 22px;
  padding: 16px 18px;
  border-radius: 12px;
  border: 1px solid rgba(64, 158, 255, 0.18);
  box-shadow: 0 8px 20px rgba(64, 158, 255, 0.08);
}

.preparing-hint-fpga {
  background: linear-gradient(135deg, rgba(230, 247, 255, 0.95) 0%, rgba(243, 249, 255, 0.98) 100%);
}

.preparing-hint-icon {
  flex-shrink: 0;
  width: 38px;
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(64, 158, 255, 0.14);
  font-size: 18px;
}

.preparing-hint-content {
  min-width: 0;
}

.preparing-hint-title {
  margin-bottom: 6px;
  color: #1f2d3d;
  font-size: 15px;
  font-weight: 700;
}

.preparing-hint-text {
  color: #5c6b77;
  font-size: 13px;
  line-height: 1.7;
}

.download-buttons {
  margin-top: 20px;
  display: flex;
  gap: 12px;
  justify-content: center;
}

.download-btn-compact {
  flex: 0 0 auto;
  max-width: none;
  font-size: 14px;
  padding: 12px 20px;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
  margin-bottom: 12px;
}

.stats-row:last-child {
  margin-bottom: 0;
}

.stat-item-detail {
  background: white;
  border-radius: 8px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.stat-item-detail:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.stat-item-detail .stat-label {
  font-size: 13px;
  color: #606266;
  font-weight: 500;
  text-align: center;
}

.stat-item-detail .stat-value {
  font-size: 22px;
  font-weight: bold;
  text-align: center;
}

.stat-item-detail .stat-value.primary { color: #409eff; }
.stat-item-detail .stat-value.primary-bold { color: #1890ff; font-size: 24px; }
.stat-item-detail .stat-value.success { color: #67c23a; }
.stat-item-detail .stat-value.info { color: #e6a23c; }
.stat-item-detail .stat-value.warning { color: #909399; }
.stat-item-detail .stat-value.danger { color: #f56c6c; }

.download-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin: 30px 0;
}

.download-card {
  border: 1px solid #e4e7ed;
  border-radius: 12px;
  padding: 20px;
  background: #fafafa;
  transition: all 0.3s;
}

.download-card:hover {
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.download-card.featured {
  border-color: #409eff;
  background: linear-gradient(135deg, #f0f9ff, #e6f7ff);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 15px;
}

.card-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: white;
}

.card-icon.success { background: #67c23a; }
.card-icon.primary { background: #409eff; }

.card-title h4 {
  margin: 0 0 4px 0;
  font-size: 16px;
  color: #303133;
}

.card-title p {
  margin: 0;
  font-size: 12px;
  color: #606266;
}

.card-btn {
  width: 100%;
  font-size: 14px;
}

.restart-section {
  margin-top: 30px;
}

.restart-section-bottom {
  margin-top: 30px;
  text-align: center;
  padding: 20px;
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

/* 响应式设计 */
@media (max-width: 1200px) {
  .upload-container {
    grid-template-columns: 1fr;
  }
  
  .rules-container {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .static-analysis-filter {
    padding: 15px;
  }
  
  .header {
    padding: 20px;
  }
  
  .header h2 {
    font-size: 22px;
  }
  
  .stat-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .phase-indicators {
    flex-direction: column;
    gap: 15px;
  }
  
  .phase-divider {
    width: 2px;
    height: 20px;
  }
  
  .processing-info {
    flex-direction: column;
    gap: 15px;
  }
  
  .result-summary {
    flex-direction: column;
    gap: 20px;
  }
  
  .download-cards {
    grid-template-columns: 1fr;
  }
}

/* 配置对话框样式 */
.config-summary {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 6px;
  font-size: 14px;
}

.config-summary p {
  margin: 8px 0;
}

.dialog-footer-with-extra {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.extra-actions {
  display: flex;
  gap: 8px;
}

.main-actions {
  display: flex;
  gap: 10px;
}

/* 导入预览样式 */
.import-preview {
  background: #f0f9ff;
  padding: 12px;
  border-radius: 6px;
  border: 1px solid #d9ecff;
}

.import-preview p {
  margin: 6px 0;
  font-size: 14px;
}

/* 自定义过滤配置样式 */
.filter-item {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.el-collapse {
  border: none;
}

.el-collapse-item {
  border-bottom: 1px solid #ebeef5;
}
</style>