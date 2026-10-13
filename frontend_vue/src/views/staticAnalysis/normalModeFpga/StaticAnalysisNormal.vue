<template>
  <div class="static-analysis-normal">
    <div class="analysis-hero">
      <div class="analysis-hero-inner">
        <h2>🚀 纯AI模式 FPGA 静态分析工具</h2>
        <p>上传代码压缩包，按勾选的 FPGA 规则执行文件级静态分析（确定类直调 AI，不确定类走智能体）。</p>
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
            mode="fpga"
            :upload-url="staticAnalysisNormalModeFpgaService.getUploadUrl()"
            @upload-success="setFileId($event)"
          />
          <div class="upload-tip-row">
            <span>支持 Verilog / VHDL / IP 文件压缩包</span>
          </div>
        </div>
      </div>

      <div class="rules-section normal-rules-section">
        <el-tabs v-model="activeFpgaLangTab" class="fpga-lang-tabs">

          <!-- ═══ Verilog tab ═══ -->
          <el-tab-pane name="verilog">
            <template #label>
              <span>🟢 Verilog
                <el-badge :value="selectedVerilogCount" :hidden="selectedVerilogCount === 0"
                  type="primary" class="tab-badge" />
              </span>
            </template>

            <div class="rules-header compact-rules-header">
              <div class="rules-title">
                <h3>🎯 选择要应用的普通模式 FPGA 规则（Verilog）</h3>
                <div class="rules-summary">
                  <span class="selected-count">已选 {{ selectedVerilogCount }}/{{ verilogRules.length }} 条</span>
                </div>
              </div>
              <div class="rules-actions">
                <el-button size="small" @click="selectCurrentTabAll">全选</el-button>
                <el-button size="small" @click="deselectCurrentTabAll">全不选</el-button>
                <el-button size="small" @click="selectAccurateFpgaOnly">仅选确定规则</el-button>
                <el-button size="small" @click="selectUncertainFpgaOnly">仅选不确定规则</el-button>
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
                    <div class="rule-count">{{ accurateVerilogRules.length }} 条</div>
                  </div>
                  <p class="header-desc">语法分析即可准确识别（不走智能体）</p>
                </div>
                <div class="rules-list compact-rules-list">
                  <el-checkbox-group v-model="selectedFpgaRules">
                    <div v-for="rule in accurateVerilogRules" :key="rule.rule_code"
                      class="rule-item compact-rule-item hoverable-rule-item">
                      <el-checkbox :label="rule.rule_code" class="rule-checkbox">
                        <div class="rule-content compact-rule-content">
                          <div class="rule-name">{{ rule.rule_code }}</div>
                          <div class="rule-description">{{ rule.rule_name }}</div>
                          <div class="rule-meta compact-rule-meta">
                            <el-tag size="small" type="success">Verilog</el-tag>
                            <el-tag v-if="rule.meta_label" size="small" plain>{{ rule.meta_label }}</el-tag>
                          </div>
                        </div>
                      </el-checkbox>
                      <el-button class="move-btn" size="small" type="warning" plain
                        @click.stop="moveFpgaRule(rule.rule_code, 'uncertain')">移到不确定 →</el-button>
                    </div>
                  </el-checkbox-group>
                </div>
              </div>
              <div class="rules-column uncertain-column">
                <div class="column-header">
                  <div class="header-content">
                    <h4>⚠️ 不确定规则</h4>
                    <div class="rule-count">{{ uncertainVerilogRules.length }} 条</div>
                  </div>
                  <p class="header-desc">需结合代码上下文分析（走智能体）</p>
                </div>
                <div class="rules-list compact-rules-list">
                  <el-checkbox-group v-model="selectedFpgaRules">
                    <div v-for="rule in uncertainVerilogRules" :key="rule.rule_code"
                      class="rule-item compact-rule-item hoverable-rule-item">
                      <el-checkbox :label="rule.rule_code" class="rule-checkbox">
                        <div class="rule-content compact-rule-content">
                          <div class="rule-name">{{ rule.rule_code }}</div>
                          <div class="rule-description">{{ rule.rule_name }}</div>
                          <div class="rule-meta compact-rule-meta">
                            <el-tag size="small" type="warning">Verilog</el-tag>
                            <el-tag v-if="rule.meta_label" size="small" plain>{{ rule.meta_label }}</el-tag>
                          </div>
                        </div>
                      </el-checkbox>
                      <el-button class="move-btn" size="small" type="success" plain
                        @click.stop="moveFpgaRule(rule.rule_code, 'accurate')">← 移到确定</el-button>
                    </div>
                  </el-checkbox-group>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <!-- ═══ VHDL tab ═══ -->
          <el-tab-pane name="vhdl">
            <template #label>
              <span>🔵 VHDL
                <el-badge :value="selectedVhdlCount" :hidden="selectedVhdlCount === 0"
                  type="info" class="tab-badge" />
              </span>
            </template>

            <div class="rules-header compact-rules-header">
              <div class="rules-title">
                <h3>🎯 选择要应用的普通模式 FPGA 规则（VHDL）</h3>
                <div class="rules-summary">
                  <span class="selected-count">已选 {{ selectedVhdlCount }}/{{ vhdlRules.length }} 条</span>
                </div>
              </div>
              <div class="rules-actions">
                <el-button size="small" @click="selectCurrentTabAll">全选</el-button>
                <el-button size="small" @click="deselectCurrentTabAll">全不选</el-button>
                <el-button size="small" @click="selectAccurateFpgaOnly">仅选确定规则</el-button>
                <el-button size="small" @click="selectUncertainFpgaOnly">仅选不确定规则</el-button>
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
                    <div class="rule-count">{{ accurateVhdlRules.length }} 条</div>
                  </div>
                  <p class="header-desc">语法分析即可准确识别（不走智能体）</p>
                </div>
                <div class="rules-list compact-rules-list">
                  <el-checkbox-group v-model="selectedFpgaRules">
                    <div v-for="rule in accurateVhdlRules" :key="rule.rule_code"
                      class="rule-item compact-rule-item hoverable-rule-item">
                      <el-checkbox :label="rule.rule_code" class="rule-checkbox">
                        <div class="rule-content compact-rule-content">
                          <div class="rule-name">{{ rule.rule_code }}</div>
                          <div class="rule-description">{{ rule.rule_name }}</div>
                          <div class="rule-meta compact-rule-meta">
                            <el-tag size="small" type="info">VHDL</el-tag>
                            <el-tag v-if="rule.meta_label" size="small" plain>{{ rule.meta_label }}</el-tag>
                          </div>
                        </div>
                      </el-checkbox>
                      <el-button class="move-btn" size="small" type="warning" plain
                        @click.stop="moveFpgaRule(rule.rule_code, 'uncertain')">移到不确定 →</el-button>
                    </div>
                  </el-checkbox-group>
                </div>
              </div>
              <div class="rules-column uncertain-column">
                <div class="column-header">
                  <div class="header-content">
                    <h4>⚠️ 不确定规则</h4>
                    <div class="rule-count">{{ uncertainVhdlRules.length }} 条</div>
                  </div>
                  <p class="header-desc">需结合代码上下文分析（走智能体）</p>
                </div>
                <div class="rules-list compact-rules-list">
                  <el-checkbox-group v-model="selectedFpgaRules">
                    <div v-for="rule in uncertainVhdlRules" :key="rule.rule_code"
                      class="rule-item compact-rule-item hoverable-rule-item">
                      <el-checkbox :label="rule.rule_code" class="rule-checkbox">
                        <div class="rule-content compact-rule-content">
                          <div class="rule-name">{{ rule.rule_code }}</div>
                          <div class="rule-description">{{ rule.rule_name }}</div>
                          <div class="rule-meta compact-rule-meta">
                            <el-tag size="small" type="danger">VHDL</el-tag>
                            <el-tag v-if="rule.meta_label" size="small" plain>{{ rule.meta_label }}</el-tag>
                          </div>
                        </div>
                      </el-checkbox>
                      <el-button class="move-btn" size="small" type="success" plain
                        @click.stop="moveFpgaRule(rule.rule_code, 'accurate')">← 移到确定</el-button>
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
            <span>规则: {{ selectedFpgaRules.length }} 条</span>
          </div>
          <div class="info-item">
            <el-icon><CircleCheck /></el-icon>
            <span>模式: FPGA</span>
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

    <!-- 进度中间页 -->
    <div v-if="processing || completed" class="normal-progress-page">
      <div class="progress-card fpga-progress-card">
        <div class="card-header-banner fpga-banner">
          <h3>🔍 FPGA 规则分析进度</h3>
          <el-tag :type="sectionTagType(fpgaSection.status)" size="large">{{ sectionText(fpgaSection.status) }}</el-tag>
        </div>
        <div class="card-content">
          <el-progress
            :percentage="fpgaSection.progress"
            :status="sectionProgressStatus(fpgaSection.status)"
            :stroke-width="12"
            class="main-progress"
          >
            <span class="progress-text">{{ fpgaSection.processed_units }}/{{ fpgaSection.total_units }}</span>
          </el-progress>

          <div v-if="fpgaSection.current_analyzing_issue" class="current-analysis-info fpga-analysis">
            <div class="analysis-header">
              <span class="analysis-icon">🔬</span>
              <span class="analysis-title">正在分析</span>
            </div>
            <div class="analysis-content">
              <div class="issue-name">{{ fpgaSection.current_analyzing_issue }}</div>
              <div class="tool-calls">已调用工具 {{ fpgaSection.tool_calls_count }} 次</div>
            </div>
          </div>

          <div class="detailed-stats">
            <div class="stats-row">
              <div class="stat-item-detail">
                <span class="stat-label">📁 扫描文件</span>
                <span class="stat-value primary">{{ progressBase.processed_files }}/{{ progressBase.total_files }}</span>
              </div>
              <div class="stat-item-detail">
                <span class="stat-label">📊 FPGA 问题数</span>
                <span class="stat-value success">{{ fpgaSection.total_issues }}</span>
              </div>
              <div class="stat-item-detail">
                <span class="stat-label">⚙️ 处理单元</span>
                <span class="stat-value info">{{ fpgaSection.processed_units }}/{{ fpgaSection.total_units }}</span>
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
              @click="openCodeView"
              class="download-btn-compact"
            >
              <el-icon><View /></el-icon>
              查看代码视图
            </el-button>
          </div>
        </div>
      </div>

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
      保存后，所有用户下次打开时将默认使用当前勾选的 FPGA 规则配置。
    </el-alert>
    <div class="config-summary">
      <p>FPGA 规则：已选 <strong>{{ selectedFpgaRules.length }}</strong> / {{ fpgaTotalRulesCount }} 条</p>
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
import staticAnalysisNormalModeFpgaService from '@/services/staticAnalysisNormalModeFpgaService'

const codeFileId = ref('')
const taskId = ref('')
const processing = ref(false)
const completed = ref(false)
const downloading = ref(false)
const message = ref('')
const messageType = ref('success')
const fpgaRules = ref([])
const selectedFpgaRules = ref([])
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
const fpgaSection = reactive({
  status: 'pending', progress: 0, total_issues: 0,
  processed_units: 0, total_units: 0,
  current_analyzing_issue: '', tool_calls_count: 0,
})
const fileId = computed(() => codeFileId.value)
const accurateFpgaRules = computed(() => fpgaRules.value.filter(r => r.accuracy_type === 'accurate'))
const uncertainFpgaRules = computed(() => fpgaRules.value.filter(r => r.accuracy_type !== 'accurate'))
const fpgaTotalRulesCount = computed(() => fpgaRules.value.length)

const verilogRules          = computed(() => fpgaRules.value.filter(r => (r.language || '').toLowerCase() === 'verilog'))
const vhdlRules             = computed(() => fpgaRules.value.filter(r => (r.language || '').toLowerCase() === 'vhdl'))
const accurateVerilogRules  = computed(() => verilogRules.value.filter(r => r.accuracy_type === 'accurate'))
const uncertainVerilogRules = computed(() => verilogRules.value.filter(r => r.accuracy_type !== 'accurate'))
const accurateVhdlRules     = computed(() => vhdlRules.value.filter(r => r.accuracy_type === 'accurate'))
const uncertainVhdlRules    = computed(() => vhdlRules.value.filter(r => r.accuracy_type !== 'accurate'))
const activeFpgaLangTab   = ref('verilog')
const selectedVerilogCount = computed(() => selectedFpgaRules.value.filter(
  c => verilogRules.value.some(r => r.rule_code === c)).length)
const selectedVhdlCount    = computed(() => selectedFpgaRules.value.filter(
  c => vhdlRules.value.some(r => r.rule_code === c)).length)


const canStartAnalysis = computed(() => !!fileId.value && selectedFpgaRules.value.length > 0 && !processing.value)

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

function normalizeFpgaRule(rule) {
  return {
    rule_code: rule.rule_code,
    rule_name: rule.rule_content || rule.rule_name || rule.rule_code,
    rule_description: rule.rule_content || rule.rule_description || '',
    rule_type: rule.rule_type,
    language: rule.language,
    accuracy_type: rule.accuracy_type || 'uncertain',
    is_selected: rule.is_selected !== undefined ? rule.is_selected : true,
    meta_label: rule.rule_type || ''
  }
}

async function loadRules() {
  try {
    const items = await staticAnalysisNormalModeFpgaService.loadRules()
    fpgaRules.value = (items || []).map(normalizeFpgaRule)
    // 根据规则的 is_selected 字段初始化勾选状态
    selectedFpgaRules.value = fpgaRules.value
      .filter(r => r.is_selected !== false)
      .map(r => r.rule_code)
  } catch (error) {
    console.error('加载普通模式FPGA规则失败:', error)
  }
}

function showSaveConfigDialog() {
  saveConfigVisible.value = true
}

async function confirmSaveConfig() {
  savingConfig.value = true
  try {
    const res = await staticAnalysisNormalModeFpgaService.saveConfig(selectedFpgaRules.value)
    if (res?.success) {
      ElMessage.success(`默认配置已保存，共 ${selectedFpgaRules.value.length} 条规则`)
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

function selectCurrentTabAll() {
  const rules = activeFpgaLangTab.value === 'verilog' ? verilogRules.value : vhdlRules.value
  const codes = new Set(rules.map(r => r.rule_code))
  selectedFpgaRules.value = [...new Set([...selectedFpgaRules.value, ...codes])]
}
function deselectCurrentTabAll() {
  const rules = activeFpgaLangTab.value === 'verilog' ? verilogRules.value : vhdlRules.value
  const codes = new Set(rules.map(r => r.rule_code))
  selectedFpgaRules.value = selectedFpgaRules.value.filter(c => !codes.has(c))
}

function selectAllFpgaRules()      { selectedFpgaRules.value = fpgaRules.value.map(r => r.rule_code) }
function deselectAllFpgaRules()    { selectedFpgaRules.value = [] }
function selectAccurateFpgaOnly()  { selectedFpgaRules.value = accurateFpgaRules.value.map(r => r.rule_code) }
function selectUncertainFpgaOnly() { selectedFpgaRules.value = uncertainFpgaRules.value.map(r => r.rule_code) }
function selectAllVerilogRules()    { const codes = new Set(verilogRules.value.map(r => r.rule_code)); selectedFpgaRules.value = [...new Set([...selectedFpgaRules.value, ...codes])] }
function deselectAllVerilogRules()  { const codes = new Set(verilogRules.value.map(r => r.rule_code)); selectedFpgaRules.value = selectedFpgaRules.value.filter(c => !codes.has(c)) }
function selectAllVhdlRules()       { const codes = new Set(vhdlRules.value.map(r => r.rule_code)); selectedFpgaRules.value = [...new Set([...selectedFpgaRules.value, ...codes])] }
function deselectAllVhdlRules()     { const codes = new Set(vhdlRules.value.map(r => r.rule_code)); selectedFpgaRules.value = selectedFpgaRules.value.filter(c => !codes.has(c)) }

function moveFpgaRule(ruleCode, targetAccuracy) {
  const rule = fpgaRules.value.find(r => r.rule_code === ruleCode)
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
  if (!selectedFpgaRules.value.length) {
    message.value = '请至少勾选一条规则'
    messageType.value = 'error'
    return
  }

  isSubmitting.value = true
  processing.value = true
  completed.value = false
  message.value = ''

  try {
    const response = await staticAnalysisNormalModeFpgaService.start({
      file_id: codeFileId.value,
      language_mode: 'fpga',
      selected_rules: selectedFpgaRules.value
    })
    if (response && response.task_id) {
      taskId.value = response.task_id
      showCodeViewNotification()
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

function showCodeViewNotification() {
  const tid = taskId.value
  const base = window.location.origin
  const fpgaUrl = `${base}/static-analysis/normal-fpga-code-view/${tid}?type=fpga`

  ElNotification({
    title: '✅ FPGA 代码视图已就绪',
    message: `<div style="margin-top:10px;"><div style="background:#f0f9ff;padding:10px;border-radius:6px;border-left:3px solid #409EFF;margin-bottom:10px;"><div style="color:#606266;font-size:13px;margin-bottom:4px;">📍 FPGA代码视图地址：</div><div style="color:#303133;font-size:13px;font-family:monospace;word-break:break-all;">${fpgaUrl}</div><div style="color:#718096;font-size:12px;margin-top:2px;">任务ID: ${tid}</div></div><a href="${fpgaUrl}" target="_blank" style="display:inline-flex;align-items:center;gap:6px;padding:7px 14px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#fff;text-decoration:none;border-radius:6px;font-size:13px;">🔗 查看FPGA代码视图</a></div>`,
    dangerouslyUseHTMLString: true,
    type: 'success',
    duration: 0,
    position: 'top-right',
    showClose: true,
    offset: 80,
  })

  const txt = `FPGA 普通模式静态分析代码视图地址\n===========================================\n任务ID: ${tid}\n生成时间: ${new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })}\n\nFPGA 代码视图:\n${fpgaUrl}\n===========================================\n`
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
    const data = await staticAnalysisNormalModeFpgaService.getTaskProgress(taskId.value)
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

    const fpgaSrc = data.progress || data
    Object.assign(fpgaSection, {
      status: fpgaSrc.status ?? st,
      progress: fpgaSrc.progress ?? 0,
      total_issues: fpgaSrc.fpga_problems ?? fpgaSrc.total_problems ?? 0,
      processed_units: fpgaSrc.processed_units ?? 0,
      total_units: fpgaSrc.total_units ?? 0,
      current_analyzing_issue: fpgaSrc.current_analyzing_issue ?? '',
      tool_calls_count: fpgaSrc.tool_calls_count ?? 0,
    })

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
    const href = staticAnalysisNormalModeFpgaService.getDownloadUrl(taskId.value)
    const a = document.createElement('a')
    a.href = href
    a.download = `normal_fpga_result_${taskId.value}.xlsx`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  } finally {
    downloading.value = false
  }
}

function openCodeView() {
  if (!taskId.value) return
  window.open(`/static-analysis/normal-fpga-code-view/${taskId.value}?type=fpga`, '_blank')
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
  Object.assign(fpgaSection, { status: 'pending', progress: 0, total_issues: 0,
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

.fpga-progress-card { border-left: 4px solid #9c27b0; }

.card-header-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 24px;
  color: #fff;
}

.fpga-banner { background: linear-gradient(135deg, #9c27b0 0%, #7b1fa2 100%); }

.card-header-banner h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.card-content { padding: 20px 24px; }

.main-progress { margin-bottom: 16px; }

.progress-text { font-size: 13px; font-weight: 600; }

.current-analysis-info {
  border-radius: 10px;
  padding: 14px 16px;
  margin-bottom: 16px;
  color: #fff;
}

.fpga-analysis { background: linear-gradient(135deg, #9c27b0 0%, #6a1b9a 100%); }

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

.issue-name { font-size: 14px; font-weight: 500; margin-bottom: 6px; line-height: 1.5; }
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

.stat-value { font-size: 18px; font-weight: 700; text-align: center; }
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

.download-btn-compact { min-width: 160px; }

.restart-section-bottom { text-align: center; padding: 10px 0 16px; }

.analysis-message { margin-top: 4px; }

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
