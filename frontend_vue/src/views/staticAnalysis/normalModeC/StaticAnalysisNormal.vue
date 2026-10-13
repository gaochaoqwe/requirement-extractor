<template>
  <div class="static-analysis-normal">
    <div class="analysis-hero">
      <div class="analysis-hero-inner">
        <h2>🚀 纯AI模式静态分析工具</h2>
        <p>上传代码压缩包，按勾选的 C/C++ 规则执行文件级静态分析（确定类直调 AI，不确定类走智能体）。</p>
      </div>
    </div>

    <!-- 上传与规则配置区（处理中/完成后隐藏） -->
    <div v-if="!processing && !completed" class="analysis-main-content">
      <div class="normal-upload-panel">
        <div class="upload-item upload-item--single">
          <div class="upload-header-row">
            <div class="upload-header-title">
              <el-icon><Document /></el-icon>
              <h3>代码文件</h3>
            </div>
            <el-tag :type="fileId ? 'success' : 'warning'" size="small">
              {{ fileId ? '已上传' : '必需' }}
            </el-tag>
          </div>
          <UploadCodeFile
            mode="c"
            :upload-url="staticAnalysisNormalModeCService.getUploadUrl()"
            @upload-success="setFileId($event)"
          />
          <div class="upload-tip-row">
            <span>支持 C/C++ 代码压缩包</span>
          </div>
        </div>
      </div>

      <div class="rules-section normal-rules-section">
        <el-tabs v-model="activeCRuleTab" class="normal-rule-tabs">
          <el-tab-pane label="GJB8114规则" name="gjb">
            <div class="rules-header compact-rules-header">
              <div class="rules-title">
                <h3>🎯 选择要应用的GJB8114规则</h3>
                <div class="rules-summary">
                  <span class="selected-count">已选择 {{ selectedGjbRules.length }}/{{ gjbTotalRulesCount }} 规则</span>
                </div>
              </div>
              <div class="rules-actions">
                <el-button size="small" @click="selectAllGjbRules">全选</el-button>
                <el-button size="small" @click="deselectAllGjbRules">全不选</el-button>
                <el-button size="small" @click="selectAccurateGjbOnly">仅选确定规则</el-button>
                <el-button size="small" @click="selectUncertainGjbOnly">仅选不确定规则</el-button>
                <el-button size="small" type="warning" @click="showSaveConfigDialog">
                  <el-icon><Lock /></el-icon>
                  保存为默认配置
                </el-button>
              </div>
            </div>

            <div class="rules-container compact-rules-container">
              <div class="rules-column accurate-column">
                <div class="column-header">
                  <div class="header-content">
                    <h4>✅ 确定规则</h4>
                    <div class="rule-count">{{ accurateGjbRules.length }} 条</div>
                  </div>
                  <p class="header-desc">语法分析即可准确识别（不走智能体）</p>
                </div>
                <div class="rules-list compact-rules-list">
                  <el-checkbox-group v-model="selectedGjbRules">
                    <div v-for="rule in accurateGjbRules" :key="rule.rule_code" class="rule-item compact-rule-item hoverable-rule-item">
                      <el-checkbox :label="rule.rule_code" class="rule-checkbox">
                        <div class="rule-content compact-rule-content">
                          <div class="rule-name">{{ rule.rule_code }}</div>
                          <div class="rule-description">{{ rule.rule_name }}</div>
                          <div class="rule-meta compact-rule-meta">
                            <el-tag size="small" type="success">{{ rule.meta_label || 'GJB' }}</el-tag>
                          </div>
                        </div>
                      </el-checkbox>
                      <el-button class="move-btn" size="small" type="warning" plain
                        @click.stop="moveGjbRule(rule.rule_code, 'uncertain')">
                        移到不确定 →
                      </el-button>
                    </div>
                  </el-checkbox-group>
                </div>
              </div>

              <div class="rules-column uncertain-column">
                <div class="column-header">
                  <div class="header-content">
                    <h4>⚠️ 不确定规则</h4>
                    <div class="rule-count">{{ uncertainGjbRules.length }} 条</div>
                  </div>
                  <p class="header-desc">需结合代码上下文分析（走智能体）</p>
                </div>
                <div class="rules-list compact-rules-list">
                  <el-checkbox-group v-model="selectedGjbRules">
                    <div v-for="rule in uncertainGjbRules" :key="rule.rule_code" class="rule-item compact-rule-item hoverable-rule-item">
                      <el-checkbox :label="rule.rule_code" class="rule-checkbox">
                        <div class="rule-content compact-rule-content">
                          <div class="rule-name">{{ rule.rule_code }}</div>
                          <div class="rule-description">{{ rule.rule_name }}</div>
                          <div class="rule-meta compact-rule-meta">
                            <el-tag size="small" type="warning">{{ rule.meta_label || 'GJB' }}</el-tag>
                          </div>
                        </div>
                      </el-checkbox>
                      <el-button class="move-btn" size="small" type="success" plain
                        @click.stop="moveGjbRule(rule.rule_code, 'accurate')">
                        ← 移到确定
                      </el-button>
                    </div>
                  </el-checkbox-group>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="CWE规则" name="cwe">
            <div class="rules-header compact-rules-header">
              <div class="rules-title">
                <h3>🛡️ 选择要应用的CWE规则</h3>
                <div class="rules-summary">
                  <span class="selected-count">已选择 {{ selectedCweRules.length }}/{{ cweTotalRulesCount }} 规则</span>
                </div>
              </div>
              <div class="rules-actions">
                <el-button size="small" @click="selectAllCweRules">全选</el-button>
                <el-button size="small" @click="deselectAllCweRules">全不选</el-button>
                <el-button size="small" @click="selectAccurateCweOnly">仅选确定规则</el-button>
                <el-button size="small" @click="selectUncertainCweOnly">仅选不确定规则</el-button>
                <el-button size="small" type="warning" @click="showSaveConfigDialog">
                  <el-icon><Lock /></el-icon>保存为默认配置
                </el-button>
              </div>
            </div>

            <div class="rules-container compact-rules-container">
              <div class="rules-column accurate-column">
                <div class="column-header">
                  <div class="header-content">
                    <h4>✅ 确定规则</h4>
                    <div class="rule-count">{{ accurateCweRules.length }} 条</div>
                  </div>
                  <p class="header-desc">语法分析即可准确识别（不走智能体）</p>
                </div>
                <div class="rules-list compact-rules-list">
                  <el-checkbox-group v-model="selectedCweRules">
                    <div v-for="rule in accurateCweRules" :key="rule.rule_code" class="rule-item compact-rule-item hoverable-rule-item">
                      <el-checkbox :label="rule.rule_code" class="rule-checkbox">
                        <div class="rule-content compact-rule-content">
                          <div class="rule-name">{{ rule.rule_code }}</div>
                          <div class="rule-description">{{ rule.rule_name }}</div>
                          <div v-if="rule.rule_description" class="rule-extra-description compact-rule-extra-description">{{ rule.rule_description }}</div>
                          <div class="rule-meta compact-rule-meta">
                            <el-tag size="small" type="success">CWE</el-tag>
                          </div>
                        </div>
                      </el-checkbox>
                      <el-button class="move-btn" size="small" type="warning" plain
                        @click.stop="moveCweRule(rule.rule_code, 'uncertain')">
                        移到不确定 →
                      </el-button>
                    </div>
                  </el-checkbox-group>
                </div>
              </div>

              <div class="rules-column uncertain-column">
                <div class="column-header">
                  <div class="header-content">
                    <h4>⚠️ 不确定规则</h4>
                    <div class="rule-count">{{ uncertainCweRules.length }} 条</div>
                  </div>
                  <p class="header-desc">需结合代码上下文分析（走智能体）</p>
                </div>
                <div class="rules-list compact-rules-list">
                  <el-checkbox-group v-model="selectedCweRules">
                    <div v-for="rule in uncertainCweRules" :key="rule.rule_code" class="rule-item compact-rule-item hoverable-rule-item">
                      <el-checkbox :label="rule.rule_code" class="rule-checkbox">
                        <div class="rule-content compact-rule-content">
                          <div class="rule-name">{{ rule.rule_code }}</div>
                          <div class="rule-description">{{ rule.rule_name }}</div>
                          <div v-if="rule.rule_description" class="rule-extra-description compact-rule-extra-description">{{ rule.rule_description }}</div>
                          <div class="rule-meta compact-rule-meta">
                            <el-tag size="small" type="warning">CWE</el-tag>
                          </div>
                        </div>
                      </el-checkbox>
                      <el-button class="move-btn" size="small" type="success" plain
                        @click.stop="moveCweRule(rule.rule_code, 'accurate')">
                        ← 移到确定
                      </el-button>
                    </div>
                  </el-checkbox-group>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>

      <div class="start-processing normal-start-processing">
        <div class="processing-info">
          <div class="info-item">
            <el-icon><Document /></el-icon>
            <span>代码文件: {{ fileId ? '✅' : '❌' }}</span>
          </div>
          <div class="info-item">
            <el-icon><Check /></el-icon>
            <span>规则: {{ selectedRules.length }} 条</span>
          </div>
          <div class="info-item">
            <el-icon><CircleCheck /></el-icon>
            <span>模式: C语言</span>
          </div>
        </div>

        <el-button
          type="primary"
          size="large"
          :disabled="!canStartAnalysis"
          :loading="analyzing"
          class="start-btn"
          @click="startAnalysis"
        >
          <el-icon><CaretRight /></el-icon>
          开始静态分析处理
        </el-button>
      </div>

      <el-alert
        v-if="message"
        :title="message"
        :type="messageType"
        show-icon
        :closable="false"
        class="analysis-message"
      />
    </div>

    <!-- 进度中间页（处理中 / 完成） -->
    <div v-if="processing || completed" class="normal-progress-page">
      <!-- GJB 进度卡片 -->
      <div class="progress-card gjb-progress-card">
        <div class="card-header-banner gjb-banner">
          <h3>🔍 GJB8114 规则分析进度</h3>
          <el-tag :type="sectionTagType(gjbSection.status)" size="large">{{ sectionText(gjbSection.status) }}</el-tag>
        </div>
        <div class="card-content">
          <el-progress
            :percentage="gjbSection.progress"
            :status="sectionProgressStatus(gjbSection.status)"
            :stroke-width="12"
            class="main-progress"
          >
            <span class="progress-text">{{ gjbSection.processed_units }}/{{ gjbSection.total_units }}</span>
          </el-progress>

          <div v-if="gjbSection.current_analyzing_issue" class="current-analysis-info gjb-analysis">
            <div class="analysis-header">
              <span class="analysis-icon">🔬</span>
              <span class="analysis-title">正在分析</span>
            </div>
            <div class="analysis-content">
              <div class="issue-name">{{ gjbSection.current_analyzing_issue }}</div>
              <div class="tool-calls">已调用工具 {{ gjbSection.tool_calls_count }} 次</div>
            </div>
          </div>

          <div class="detailed-stats">
            <div class="stats-row">
              <div class="stat-item-detail">
                <span class="stat-label">📁 扫描文件</span>
                <span class="stat-value primary">{{ progressBase.processed_files }}/{{ progressBase.total_files }}</span>
              </div>
              <div class="stat-item-detail">
                <span class="stat-label">📊 GJB问题数</span>
                <span class="stat-value success">{{ gjbSection.total_issues }}</span>
              </div>
              <div class="stat-item-detail">
                <span class="stat-label">⚙️ 处理单元</span>
                <span class="stat-value info">{{ gjbSection.processed_units }}/{{ gjbSection.total_units }}</span>
              </div>
            </div>
            <div class="stats-row">
              <div class="stat-item-detail">
                <span class="stat-label">✅ 确定规则数</span>
                <span class="stat-value success">{{ progressBase.accurate_rules }}</span>
              </div>
              <div class="stat-item-detail">
                <span class="stat-label">⚠️ 不确定规则数</span>
                <span class="stat-value warning">{{ progressBase.uncertain_rules }}</span>
              </div>
              <div class="stat-item-detail">
                <span class="stat-label">📋 当前规则</span>
                <span class="stat-value" style="font-size:13px;">{{ progressBase.current_rule_code || '—' }}</span>
              </div>
            </div>
          </div>

          <div v-if="completed" class="download-buttons">
            <el-button
              type="primary"
              size="default"
              :loading="downloading"
              @click="downloadResult"
              class="download-btn-compact"
            >
              <el-icon><Download /></el-icon>
              下载分析结果（Excel）
            </el-button>
            <el-button
              type="success"
              size="default"
              @click="openCodeView('gjb')"
              class="download-btn-compact"
            >
              <el-icon><View /></el-icon>
              查看GJB代码视图
            </el-button>
          </div>
        </div>
      </div>

      <!-- CWE 进度卡片 -->
      <div class="progress-card cwe-progress-card">
        <div class="card-header-banner cwe-banner">
          <h3>🛡️ CWE 规则分析进度</h3>
          <el-tag :type="sectionTagType(cweSection.status)" size="large">{{ sectionText(cweSection.status) }}</el-tag>
        </div>
        <div class="card-content">
          <el-progress
            :percentage="cweSection.progress"
            :status="sectionProgressStatus(cweSection.status)"
            :stroke-width="12"
            class="main-progress"
          >
            <span class="progress-text">{{ cweSection.processed_units }}/{{ cweSection.total_units }}</span>
          </el-progress>

          <div v-if="cweSection.current_analyzing_issue" class="current-analysis-info cwe-analysis">
            <div class="analysis-header">
              <span class="analysis-icon">🔬</span>
              <span class="analysis-title">正在分析</span>
            </div>
            <div class="analysis-content">
              <div class="issue-name">{{ cweSection.current_analyzing_issue }}</div>
              <div class="tool-calls">已调用工具 {{ cweSection.tool_calls_count }} 次</div>
            </div>
          </div>

          <div class="detailed-stats">
            <div class="stats-row">
              <div class="stat-item-detail">
                <span class="stat-label">📊 总问题数</span>
                <span class="stat-value primary">{{ progressBase.total_problems }}</span>
              </div>
              <div class="stat-item-detail">
                <span class="stat-label">🛡️ CWE问题数</span>
                <span class="stat-value success">{{ cweSection.total_issues }}</span>
              </div>
              <div class="stat-item-detail">
                <span class="stat-label">⚙️ 处理单元</span>
                <span class="stat-value info">{{ cweSection.processed_units }}/{{ cweSection.total_units }}</span>
              </div>
            </div>
            <div class="stats-row">
              <div class="stat-item-detail">
                <span class="stat-label">✅ 确定规则数</span>
                <span class="stat-value success">{{ cweSection.accurate_rules }}</span>
              </div>
              <div class="stat-item-detail">
                <span class="stat-label">⚠️ 不确定规则数</span>
                <span class="stat-value warning">{{ cweSection.uncertain_rules }}</span>
              </div>
              <div class="stat-item-detail">
                <span class="stat-label">📌 当前规则</span>
                <span class="stat-value" style="font-size:13px;">{{ cweSection.current_rule_code || '—' }}</span>
              </div>
            </div>
          </div>
          <div v-if="completed" class="download-buttons">
            <el-button
              type="success"
              size="default"
              @click="openCodeView('cwe')"
              class="download-btn-compact"
            >
              <el-icon><View /></el-icon>
              查看CWE代码视图
            </el-button>
          </div>
        </div>
      </div>

      <!-- 重新开始 -->
      <div v-if="completed" class="restart-section-bottom">
        <el-button @click="resetForm" size="large" plain>
          <el-icon><Refresh /></el-icon>
          重新开始
        </el-button>
      </div>

      <el-alert
        v-if="message"
        :title="message"
        :type="messageType"
        show-icon
        :closable="false"
        class="analysis-message"
      />
    </div>
  </div>

  <!-- 保存默认配置弹窗 -->
  <el-dialog v-model="saveConfigVisible" title="保存默认规则配置" width="420px" :close-on-click-modal="false">
    <el-alert type="warning" :closable="false" style="margin-bottom:16px;">
      保存后，所有用户下次打开时将默认使用当前勾选的规则配置。
    </el-alert>
    <div class="config-summary">
      <p>GJB8114 规则：已选 <strong>{{ selectedGjbRules.length }}</strong> / {{ gjbTotalRulesCount }} 条</p>
      <p>CWE 规则：已选 <strong>{{ selectedCweRules.length }}</strong> / {{ cweTotalRulesCount }} 条</p>
      <p>共 <strong>{{ selectedRules.length }}</strong> 条规则将保存为默认配置</p>
    </div>
    <template #footer>
      <el-button @click="saveConfigVisible = false">取消</el-button>
      <el-button type="primary" :loading="savingConfig" @click="confirmSaveConfig">确认保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { ElNotification, ElMessage } from 'element-plus'
import UploadCodeFile from '../upload/UploadCodeFile.vue'
import { Document, Check, CircleCheck, CaretRight, Download, View, Refresh, Lock } from '@element-plus/icons-vue'
import staticAnalysisNormalModeCService from '@/services/staticAnalysisNormalModeCService'

const codeFileId = ref('')
const taskId = ref('')
const processing = ref(false)
const completed = ref(false)
const downloading = ref(false)
const message = ref('')
const messageType = ref('success')
const cRules = ref([])
const selectedGjbRules = ref([])
const selectedCweRules = ref([])
const activeCRuleTab = ref('gjb')
const isSubmitting = ref(false)
let pollTimer = null

// 保存配置弹窗
const saveConfigVisible = ref(false)
const saveConfigPassword = ref('')
const savingConfig = ref(false)

const progressBase = reactive({
  status: 'pending', progress: 0,
  total_files: 0, processed_files: 0,
  total_rules: 0, accurate_rules: 0, uncertain_rules: 0,
  total_units: 0, processed_units: 0, total_problems: 0,
  current_rule_code: '', current_analyzing_issue: '', tool_calls_count: 0,
})
const gjbSection = reactive({
  status: 'pending', progress: 0, total_issues: 0,
  processed_units: 0, total_units: 0,
  current_analyzing_issue: '', tool_calls_count: 0,
  accurate_rules: 0, uncertain_rules: 0, current_rule_code: '',
})
const cweSection = reactive({
  status: 'pending', progress: 0, total_issues: 0,
  processed_units: 0, total_units: 0,
  current_analyzing_issue: '', tool_calls_count: 0,
  accurate_rules: 0, uncertain_rules: 0, current_rule_code: '',
})

const fileId = computed(() => codeFileId.value)
const gjbRules = computed(() => cRules.value.filter(r => r.rule_type === 'GJB'))
const cweRules = computed(() => cRules.value.filter(r => r.rule_type === 'CWE'))
const accurateGjbRules = computed(() => gjbRules.value.filter(r => r.accuracy_type === 'accurate'))
const uncertainGjbRules = computed(() => gjbRules.value.filter(r => r.accuracy_type !== 'accurate'))
const accurateCweRules = computed(() => cweRules.value.filter(r => r.accuracy_type === 'accurate'))
const uncertainCweRules = computed(() => cweRules.value.filter(r => r.accuracy_type !== 'accurate'))
const gjbTotalRulesCount = computed(() => gjbRules.value.length)
const cweTotalRulesCount = computed(() => cweRules.value.length)
const selectedRules = computed(() => [...selectedGjbRules.value, ...selectedCweRules.value])
const canStartAnalysis = computed(() => !!fileId.value && selectedRules.value.length > 0 && !processing.value)

function sectionTagType(s) {
  if (s === 'completed') return 'success'
  if (s === 'failed') return 'danger'
  if (s === 'processing') return 'primary'
  return 'warning'
}
function sectionText(s) {
  if (s === 'completed') return '已完成'
  if (s === 'failed') return '失败'
  if (s === 'processing') return '分析中'
  return '等待中'
}
function sectionProgressStatus(s) {
  if (s === 'completed') return 'success'
  if (s === 'failed') return 'exception'
  return undefined
}

function normalizeCRule(rule) {
  return {
    rule_code: rule.rule_code,
    rule_name: rule.rule_name || rule.rule_description || rule.description || rule.rule_code,
    rule_description: rule.rule_description || rule.description || '',
    rule_type: (rule.rule_type || inferCRuleType(rule.rule_code)).toUpperCase(),
    accuracy_type: rule.accuracy_type || 'uncertain',
    is_selected: false,
    meta_label: rule.detection_method || rule.category || inferCRuleType(rule.rule_code).toUpperCase()
  }
}

function inferCRuleType(ruleCode = '') {
  const upperCode = String(ruleCode).toUpperCase()
  if (upperCode.startsWith('CWE') || upperCode.startsWith('S_')) return 'cwe'
  return 'gjb'
}

async function loadRules() {
  try {
    const { gjb, cwe } = await staticAnalysisNormalModeCService.loadRules()
    cRules.value = [...gjb, ...cwe].map(normalizeCRule)
    selectedGjbRules.value = []
    selectedCweRules.value = []
  } catch (error) {
    console.error('加载普通模式C规则失败:', error)
  }
}

function showSaveConfigDialog() {
  saveConfigVisible.value = true
}

async function confirmSaveConfig() {
  savingConfig.value = true
  try {
    const res = await staticAnalysisNormalModeCService.saveConfig(selectedRules.value)
    if (res?.success) {
      ElMessage.success(`默认配置已保存，共 ${selectedRules.value.length} 条规则`)
      saveConfigVisible.value = false
    } else {
      ElMessage.error(res?.message || '保存失败')
    }
  } catch (e) {
    ElMessage.error('保存失败：' + (e?.message || e))
  } finally {
    savingConfig.value = false
  }
}

function setFileId(res) {
  if (!res || !res.file_id) return
  codeFileId.value = res.file_id
  message.value = '代码文件上传成功'
  messageType.value = 'success'
}

function selectAllGjbRules()      { selectedGjbRules.value = gjbRules.value.map(r => r.rule_code) }
function deselectAllGjbRules()    { selectedGjbRules.value = [] }
function selectAccurateGjbOnly()  { selectedGjbRules.value = accurateGjbRules.value.map(r => r.rule_code) }
function selectUncertainGjbOnly() { selectedGjbRules.value = uncertainGjbRules.value.map(r => r.rule_code) }
function selectAllCweRules()      { selectedCweRules.value = cweRules.value.map(r => r.rule_code) }
function deselectAllCweRules()    { selectedCweRules.value = [] }
function selectAccurateCweOnly()  { selectedCweRules.value = accurateCweRules.value.map(r => r.rule_code) }
function selectUncertainCweOnly() { selectedCweRules.value = uncertainCweRules.value.map(r => r.rule_code) }

function moveGjbRule(ruleCode, targetAccuracy) {
  const rule = cRules.value.find(r => r.rule_code === ruleCode)
  if (!rule) return
  rule.accuracy_type = targetAccuracy
  ElMessage.success(`${ruleCode} 已移到${targetAccuracy === 'accurate' ? '确定' : '不确定'}规则`)
}

function moveCweRule(ruleCode, targetAccuracy) {
  const rule = cRules.value.find(r => r.rule_code === ruleCode)
  if (!rule) return
  rule.accuracy_type = targetAccuracy
  ElMessage.success(`${ruleCode} 已移到${targetAccuracy === 'accurate' ? '确定' : '不确定'}规则`)
}

async function startAnalysis() {
  if (isSubmitting.value) return
  if (!codeFileId.value) {
    message.value = '错误：未获取到有效的文件ID，请重新上传文件'
    messageType.value = 'error'
    return
  }
  if (!selectedRules.value.length) {
    message.value = '请至少勾选一条规则'
    messageType.value = 'error'
    return
  }

  isSubmitting.value = true
  processing.value = true
  completed.value = false
  message.value = ''

  try {
    const response = await staticAnalysisNormalModeCService.start({
      file_id: codeFileId.value,
      language_mode: 'c',
      selected_rules: selectedRules.value
    })
    if (response && response.task_id) {
      taskId.value = response.task_id
      showCodeViewNotifications()
      schedulePoll()
    } else {
      throw new Error(response?.error || '服务端未返回task_id')
    }
  } catch (e) {
    message.value = '启动静态分析失败：' + (e.message || e)
    messageType.value = 'error'
    processing.value = false
  } finally {
    isSubmitting.value = false
  }
}

function showCodeViewNotifications() {
  const tid = taskId.value
  const base = window.location.origin
  const gjbUrl = `${base}/static-analysis/normal-c-code-view/${tid}?type=gjb`
  const cweUrl = `${base}/static-analysis/normal-c-code-view/${tid}?type=cwe`

  ElNotification({
    title: '✅ GJB8114 代码视图已就绪',
    message: `<div style="margin-top:10px;"><div style="background:#f0f9ff;padding:10px;border-radius:6px;border-left:3px solid #409EFF;margin-bottom:10px;"><div style="color:#606266;font-size:13px;margin-bottom:4px;">📍 GJB8114代码视图地址：</div><div style="color:#303133;font-size:13px;font-family:monospace;word-break:break-all;">${gjbUrl}</div><div style="color:#718096;font-size:12px;margin-top:2px;">任务ID: ${tid}</div></div><a href="${gjbUrl}" target="_blank" style="display:inline-flex;align-items:center;gap:6px;padding:7px 14px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#fff;text-decoration:none;border-radius:6px;font-size:13px;">🔗 查看GJB8114代码视图</a></div>`,
    dangerouslyUseHTMLString: true,
    type: 'success',
    duration: 0,
    position: 'top-right',
    showClose: true,
    offset: 80,
  })

  ElNotification({
    title: '✅ CWE 代码视图已就绪',
    message: `<div style="margin-top:10px;"><div style="background:#fff7e6;padding:10px;border-radius:6px;border-left:3px solid #E6A23C;margin-bottom:10px;"><div style="color:#606266;font-size:13px;margin-bottom:4px;">📍 CWE代码视图地址：</div><div style="color:#303133;font-size:13px;font-family:monospace;word-break:break-all;">${cweUrl}</div><div style="color:#718096;font-size:12px;margin-top:2px;">任务ID: ${tid}</div></div><a href="${cweUrl}" target="_blank" style="display:inline-flex;align-items:center;gap:6px;padding:7px 14px;background:linear-gradient(135deg,#f093fb 0%,#f5576c 100%);color:#fff;text-decoration:none;border-radius:6px;font-size:13px;">🔗 查看CWE代码视图</a></div>`,
    dangerouslyUseHTMLString: true,
    type: 'warning',
    duration: 0,
    position: 'top-right',
    showClose: true,
    offset: 340,
  })

  const txt = `C/C++ 普通模式静态分析代码视图地址\n===========================================\n任务ID: ${tid}\n生成时间: ${new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })}\n\nGJB8114 代码视图:\n${gjbUrl}\n\nCWE 代码视图:\n${cweUrl}\n===========================================\n`
  const blob = new Blob([txt], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `代码视图地址_${tid}_${Date.now()}.txt`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

function schedulePoll() {
  pollTimer = setTimeout(doPoll, 5000)
}

async function doPoll() {
  if (!taskId.value || !processing.value) return
  try {
    const data = await staticAnalysisNormalModeCService.getTaskProgress(taskId.value)
    if (!data) { schedulePoll(); return }

    const base = data.progress || data
    const st = base.status || data.status || 'pending'

    Object.assign(progressBase, {
      status: st,
      progress: base.progress ?? 0,
      total_files: base.total_files ?? 0,
      processed_files: base.processed_files ?? 0,
      total_rules: base.total_rules ?? 0,
      accurate_rules: base.accurate_rules ?? 0,
      uncertain_rules: base.uncertain_rules ?? 0,
      total_units: base.total_units ?? 0,
      processed_units: base.processed_units ?? 0,
      total_problems: base.total_problems ?? 0,
      current_rule_code: base.current_rule_code ?? '',
      current_analyzing_issue: base.current_analyzing_issue ?? '',
      tool_calls_count: base.tool_calls_count ?? 0,
    })

    const fillSection = (section, src) => Object.assign(section, {
      status: src.status ?? st,
      progress: src.progress ?? 0,
      total_issues: src.total_issues ?? src.total_problems ?? 0,
      processed_units: src.processed_units ?? src.ai_processed_issues ?? 0,
      total_units: src.total_units ?? src.ai_processing_total ?? 0,
      current_analyzing_issue: src.current_analyzing_issue ?? '',
      tool_calls_count: src.tool_calls_count ?? 0,
      accurate_rules: src.accurate_rules ?? 0,
      uncertain_rules: src.uncertain_rules ?? 0,
      current_rule_code: src.current_rule_code ?? '',
    })

    if (data.gjb) fillSection(gjbSection, data.gjb)
    else Object.assign(gjbSection, { status: st, progress: progressBase.progress })

    if (data.cwe) fillSection(cweSection, data.cwe)
    else Object.assign(cweSection, { status: st, progress: progressBase.progress })

    if (st === 'completed') {
      processing.value = false
      completed.value = true
      message.value = '静态分析完成，可以下载结果或查看代码视图'
      messageType.value = 'success'
    } else if (st === 'failed') {
      processing.value = false
      message.value = base.message || '静态分析失败'
      messageType.value = 'error'
    } else {
      schedulePoll()
    }
  } catch (e) {
    console.error('获取任务进度失败:', e)
    schedulePoll()
  }
}

async function downloadResult() {
  if (!taskId.value) return
  downloading.value = true
  try {
    const href = staticAnalysisNormalModeCService.getDownloadUrl(taskId.value)
    const a = document.createElement('a')
    a.href = href
    a.download = `normal_c_result_${taskId.value}.xlsx`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  } finally {
    downloading.value = false
  }
}

function openCodeView(type = 'gjb') {
  if (!taskId.value) return
  window.open(`/static-analysis/normal-c-code-view/${taskId.value}?type=${type}`, '_blank')
}

function resetForm() {
  if (pollTimer) { clearTimeout(pollTimer); pollTimer = null }
  codeFileId.value = ''
  taskId.value = ''
  processing.value = false
  completed.value = false
  message.value = ''
  Object.assign(progressBase, {
    status: 'pending', progress: 0, total_files: 0, processed_files: 0,
    total_rules: 0, accurate_rules: 0, uncertain_rules: 0,
    total_units: 0, processed_units: 0, total_problems: 0,
    current_rule_code: '', current_analyzing_issue: '', tool_calls_count: 0,
  })
  Object.assign(gjbSection, { status: 'pending', progress: 0, total_issues: 0,
    processed_units: 0, total_units: 0, current_analyzing_issue: '', tool_calls_count: 0 })
  Object.assign(cweSection, { status: 'pending', progress: 0, total_issues: 0,
    processed_units: 0, total_units: 0, current_analyzing_issue: '', tool_calls_count: 0 })
}

onMounted(loadRules)
onUnmounted(() => { if (pollTimer) clearTimeout(pollTimer) })
</script>

<style scoped>
.static-analysis-normal {
  width: 100%;
}

.analysis-hero {
  width: 100%;
  margin: 0 auto 8px;
  background: linear-gradient(135deg, #5f7ae6 0%, #7d4bb3 100%);
  border-radius: 14px;
  padding: 22px 20px;
  text-align: center;
  color: #fff;
  box-shadow: 0 14px 30px rgba(104, 88, 182, 0.22);
}

.analysis-hero-inner {
  width: min(100%, 760px);
  margin: 0 auto;
}

.analysis-hero h2 {
  margin: 0 0 10px;
  font-size: 24px;
  font-weight: 700;
}

.analysis-hero p {
  margin: 0;
  font-size: 13px;
  line-height: 1.8;
  opacity: 0.95;
  border-top: 1px solid rgba(255, 255, 255, 0.65);
  padding-top: 10px;
}

.analysis-main-content {
  display: flex;
  flex-direction: column;
  gap: 14px;
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
}

.normal-upload-panel {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}

.upload-item {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  border: 1px solid #edf2f7;
  box-shadow: 0 10px 26px rgba(50, 93, 156, 0.08);
}

.upload-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.upload-header-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.upload-header-title h3 {
  margin: 0;
  font-size: 16px;
  color: #2d3748;
}

.upload-tip-row {
  margin-top: 10px;
  font-size: 12px;
  color: #7b8794;
}

.rules-section {
  background: #fff;
  border-radius: 14px;
  padding: 10px 16px 14px;
  box-shadow: 0 10px 28px rgba(50, 93, 156, 0.08);
}

.normal-rule-tabs :deep(.el-tabs__header) {
  margin: 0 0 8px;
}

.normal-rules-section {
  border: 1px solid #edf2f7;
}

.rules-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid #edf2f7;
}

.rules-title h3 {
  margin: 0 0 4px;
  font-size: 18px;
  color: #2d3748;
}

.rules-summary {
  font-size: 13px;
  color: #409eff;
  font-weight: 600;
}

.rules-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.rules-container {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.rules-column {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #edf2f7;
}

.column-header {
  padding: 12px 14px;
  color: #fff;
}

.accurate-column .column-header {
  background: linear-gradient(135deg, #74ce45 0%, #6fc13e 100%);
}

.uncertain-column .column-header {
  background: linear-gradient(135deg, #f7ad2a 0%, #f1a11f 100%);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.header-content h4 {
  margin: 0;
  font-size: 16px;
}

.rule-count {
  background: rgba(255, 255, 255, 0.25);
  border-radius: 999px;
  padding: 2px 10px;
  font-size: 12px;
}

.header-desc {
  margin: 0;
  font-size: 12px;
  opacity: 0.92;
}

.rules-list {
  padding: 8px;
  max-height: 300px;
  overflow-y: auto;
}

.rule-item {
  background: #fff;
  border: 1px solid #d9e2ec;
  border-radius: 8px;
  margin-bottom: 8px;
  padding: 6px 10px;
}

.rule-checkbox {
  width: 100%;
}

:deep(.rule-checkbox .el-checkbox__label) {
  width: calc(100% - 24px);
  padding-left: 10px;
}

.rule-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.rule-name {
  font-weight: 700;
  color: #2d3748;
  font-size: 12px;
}

.rule-description {
  color: #2d3748;
  font-size: 12px;
  line-height: 1.35;
}

.rule-extra-description {
  color: #6b7280;
  font-size: 11px;
  line-height: 1.35;
}

.rule-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}

.start-processing {
  background: #fff;
  border-radius: 14px;
  padding: 18px 20px;
  box-shadow: 0 10px 28px rgba(50, 93, 156, 0.08);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.processing-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 22px;
  flex-wrap: wrap;
  color: #4a5568;
  font-size: 14px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.start-btn {
  min-width: 220px;
  border-radius: 8px;
}

.normal-progress-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 1280px;
  margin: 0 auto;
}

.progress-card {
  background: #fff;
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 6px 24px rgba(50, 93, 156, 0.09);
}

.gjb-progress-card { border-left: 4px solid #409EFF; }
.cwe-progress-card { border-left: 4px solid #67C23A; }

.card-header-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 24px;
  color: #fff;
}

.gjb-banner { background: linear-gradient(135deg, #409EFF 0%, #3a8ee6 100%); }
.cwe-banner { background: linear-gradient(135deg, #67C23A 0%, #5daf34 100%); }

.card-header-banner h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.card-content {
  padding: 20px 24px;
}

.main-progress { margin-bottom: 16px; }

.progress-text {
  font-size: 13px;
  font-weight: 600;
}

.current-analysis-info {
  border-radius: 10px;
  padding: 14px 16px;
  margin-bottom: 16px;
  color: #fff;
}

.gjb-analysis {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.cwe-analysis {
  background: linear-gradient(135deg, #43a047 0%, #2e7d32 100%);
}

.analysis-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
  font-size: 15px;
  font-weight: 600;
}

.analysis-icon { font-size: 20px; }

.analysis-content {
  background: rgba(255,255,255,0.15);
  border-radius: 6px;
  padding: 10px 12px;
}

.issue-name {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 6px;
  line-height: 1.5;
}

.tool-calls { font-size: 12px; opacity: 0.9; }

.detailed-stats {
  background: #f8fafc;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 16px;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 10px;
}

.stats-row:last-child { margin-bottom: 0; }

.stat-item-detail {
  background: #fff;
  border-radius: 8px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}

.stat-label { font-size: 12px; color: #606266; text-align: center; }

.stat-value {
  font-size: 18px;
  font-weight: 700;
  text-align: center;
}

.stat-value.primary { color: #409eff; }
.stat-value.success { color: #67c23a; }
.stat-value.warning { color: #e6a23c; }
.stat-value.info    { color: #909399; }

.download-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}

.download-btn-compact {
  min-width: 160px;
}

.restart-section-bottom {
  text-align: center;
  padding: 10px 0 16px;
}

.analysis-message {
  margin-top: 4px;
}

@media (max-width: 900px) {
  .rules-header { flex-direction: column; }
  .rules-actions { justify-content: flex-start; }
  .rules-container { grid-template-columns: 1fr; }
  .stats-row { grid-template-columns: 1fr 1fr; }
}

.config-summary {
  background: #f5f7fa;
  border-radius: 6px;
  padding: 12px 16px;
  font-size: 14px;
}
.config-summary p { margin: 6px 0; color: #606266; }
.config-summary strong { color: #303133; }

.hoverable-rule-item {
  position: relative;
}
.hoverable-rule-item .move-btn {
  display: none;
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 11px;
  padding: 2px 8px;
  white-space: nowrap;
}
.hoverable-rule-item:hover .move-btn {
  display: inline-flex;
}
.hoverable-rule-item:hover {
  padding-right: 110px;
}
</style>
