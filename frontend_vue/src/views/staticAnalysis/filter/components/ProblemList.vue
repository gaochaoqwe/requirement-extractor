<template>
  <div class="problem-list">
    <div class="problem-header">
      <div class="header-title">
        <el-icon class="warning-icon"><WarningFilled /></el-icon>
        <h3>发现的问题</h3>
        <el-tag v-if="problems.length > 0" type="danger" size="small">{{ problems.length }} 个问题</el-tag>
      </div>
      <div class="header-actions">
        <el-dropdown
          v-if="selectedNode && problems.length > 0"
          trigger="click"
          @command="handleBatchFixCommand"
        >
          <el-button type="warning" size="small" plain>
            <el-icon><MagicStick /></el-icon>
            批量修复
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="file">
                修复本文件全部问题 ({{ problems.length }})
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button 
          v-if="hasMarkedProblems"
          type="success"
          size="small"
          @click="$emit('viewMarkedProblems')"
        >
          查看已标记 ({{ markedProblemsCount }})
        </el-button>
        <el-button 
          v-if="hasMarkedProblems"
          type="primary" 
          size="small"
          @click="exportMarkedProblems"
          :loading="exporting"
        >
          <el-icon><Download /></el-icon>
          导出已标记问题 ({{ markedProblemsCount }})
        </el-button>
      </div>
    </div>

    <div class="problem-content">
      <div v-if="!selectedNode" class="empty-state">
        <el-empty description="请先选择文件" />
      </div>
      <div v-else-if="problems.length === 0" class="empty-state">
        <el-empty description="该文件没有问题" />
      </div>
      <div v-else class="problems-container">
        <div 
          v-for="(problem, index) in displayedProblems" 
          :key="index" 
          class="problem-block"
          :class="[getProblemStatusClass(problem), problem.fix_status === 2 ? 'problem-fixed' : '']"
        >
          <div class="problem-title" @click="toggleProblem(problem, index)">
            <div class="problem-title-left">
              <div class="problem-status-indicator" :class="getProblemStatusIndicatorClass(problem)"></div>
              <el-icon><Warning /></el-icon>
              <span>问题 {{ index + 1 }}</span>
              <el-tag 
                v-if="problem.rule_accuracy_type"
                :type="getIssueLevelTagType(getProblemSeverity(problem))" 
                size="small"
                class="problem-level-tag"
              >
                {{ getProblemSeverity(problem) }}
              </el-tag>
              <el-tag 
                v-if="getProblemStatusLabel(problem)"
                :type="getProblemStatusTagType(problem)" 
                size="small"
                class="problem-status-tag"
              >
                {{ getProblemStatusLabel(problem) }}
              </el-tag>
              <!-- [NEW] 自动修复状态 -->
              <el-tag
                v-if="problem.fix_status === 2"
                type="success"
                size="small"
                effect="dark"
                class="problem-status-tag"
              >
                <el-icon><CircleCheck /></el-icon>已修复
              </el-tag>
              <el-tag
                v-else-if="problem.fix_status === 1"
                type="warning"
                size="small"
                class="problem-status-tag"
              >
                待应用修复
              </el-tag>
            </div>
            <div class="problem-title-right">
              <!-- [NEW] AI 自动修复入口 -->
              <el-button
                type="warning"
                size="small"
                text
                @click.stop="requestFix(problem)"
                :title="problem.fix_status === 2 ? '重新生成修复方案' : 'AI 生成修复方案'"
              >
                <el-icon><MagicStick /></el-icon>
                {{ problem.fix_status === 2 ? '重新修复' : 'AI 修复' }}
              </el-button>
              <el-button
                v-if="problem.fix_status === 2 && problem.fix_id"
                type="danger"
                size="small"
                text
                @click.stop="rollbackFix(problem)"
                title="撤销该修复（还原代码）"
              >
                <el-icon><RefreshLeft /></el-icon>
                撤销
              </el-button>
              <!-- 自动状态：移除手动状态选择，下方仅保留标记与定位按钮 -->
              <el-button 
                :type="isProblemMarked(problem) ? 'success' : 'info'" 
                size="small" 
                text
                @click.stop="toggleProblemMark(problem)"
                :title="isProblemMarked(problem) ? '取消标记' : '标记为已确认'"
              >
                <el-icon><Check v-if="isProblemMarked(problem)" /><Flag v-else /></el-icon>
                {{ isProblemMarked(problem) ? '已标记' : '标记' }}
              </el-button>
              <el-button 
                type="primary" 
                size="small" 
                text
                @click.stop="locateProblem(problem, index)"
                title="在代码中高亮显示此问题"
              >
                <el-icon><Edit /></el-icon>
                定位
              </el-button>
              <el-icon 
                class="collapse-icon"
                :class="{ 'collapsed': collapsedProblems.has(index) }"
              >
                <ArrowDown />
              </el-icon>
            </div>
          </div>

          <el-collapse-transition>
            <div 
              v-show="!collapsedProblems.has(index)"
              class="problem-content"
            >
              <!-- 问题单格式显示 -->
              <template v-if="problem.problem_sheet">
                <div class="problem-sheet-compact">
                  <!-- 问题名称 - 突出显示 -->
                  <div class="problem-sheet-name-highlight">
                    <span class="name-label">问题名称：</span>
                    <span class="name-value">{{ problem.problem_sheet.issue_name }}</span>
                  </div>

                  <!-- 四段式描述 -->
                  <div class="problem-sheet-section four-part-section">
                    <div class="section-content">
                      <div class="four-part-text">{{ formatProblemSheetText(problem.problem_sheet.four_part_description) }}</div>
                      <pre v-if="extractProblemSheetSource(problem.problem_sheet.four_part_description)" class="problem-source-code"><code>{{ formatProblemSheetSource(problem.problem_sheet.four_part_description) }}</code></pre>
                      <div v-if="formatProblemSheetTail(problem.problem_sheet.four_part_description)" class="four-part-text source-tail-text">{{ formatProblemSheetTail(problem.problem_sheet.four_part_description) }}</div>
                    </div>
                  </div>

                  <!-- 测评单位意见 -->
                  <div class="problem-sheet-section opinion-section">
                    <div class="section-content">
                      <pre>{{ problem.problem_sheet.test_unit_opinion }}</pre>
                    </div>
                  </div>
                </div>
              </template>
              
              <!-- 后备显示：如果没有问题单数据 -->
              <template v-else>
                <!-- 问题名称 -->
                <div v-if="problem.issue_name" class="problem-field">
                  <div class="field-label">问题名称</div>
                  <div class="field-value">{{ problem.issue_name }}</div>
                </div>

                <!-- 问题位置 -->
                <div class="problem-field">
                  <div class="field-label">问题位置</div>
                  <div class="field-value">{{ problem.issue_file || '未知文件' }}:{{ problem.issue_line || '?' }}</div>
                </div>

                <!-- 规则编号 -->
                <div v-if="problem.rule_code" class="problem-field">
                  <div class="field-label">规则编号</div>
                  <div class="field-value">
                    <el-tag :type="getRuleTypeTag(problem.rule_type)" size="small">
                      {{ problem.rule_code }}
                    </el-tag>
                    <el-tag 
                      v-if="problem.rule_accuracy_type"
                      :type="problem.rule_accuracy_type === 'accurate' ? 'success' : 'warning'" 
                      size="small"
                      style="margin-left: 8px;"
                    >
                      {{ problem.rule_accuracy_type === 'accurate' ? '确定规则' : '不确定规则' }}
                    </el-tag>
                  </div>
                </div>

                <!-- 问题描述 -->
                <div v-if="problem.issue_description" class="problem-field">
                  <div class="field-label">问题描述</div>
                  <div class="field-value">{{ problem.issue_description }}</div>
                </div>

                <!-- AI分析结果（如果有） -->
                <div v-if="problem.ai_analyzed" class="problem-field">
                  <div class="field-label">AI分析结果</div>
                  <div class="field-value">
                    <el-tag 
                      :type="problem.ai_is_real_issue ? 'danger' : 'success'" 
                      size="small"
                    >
                      {{ problem.ai_is_real_issue ? '确认为真实问题' : '误报' }}
                    </el-tag>
                    <span v-if="problem.ai_confidence" class="confidence">
                      (置信度: {{ (problem.ai_confidence * 100).toFixed(0) }}%)
                    </span>
                  </div>
                  <div v-if="problem.ai_analysis_result" class="ai-result">
                    {{ problem.ai_analysis_result }}
                  </div>
                </div>
              </template>
            </div>
          </el-collapse-transition>
        </div>
      </div>
    </div>

    <!-- 问题单准确率反馈弹窗 -->
    <ProblemSheetAccuracyFeedback
      v-model:visible="showFeedbackDialog"
      :task-id="props.taskId"
      :viewed-count="props.visitedRulesCount"
      :total-problems="props.totalRulesCount"
      :trigger-point="feedbackStatus.delayedCount === 0 ? '1/3' : feedbackStatus.delayedCount === 1 ? '2/3' : '3/3'"
      :delayed-count="feedbackStatus.delayedCount"
      rule-type="gjb"
      @submitted="handleFeedbackSubmitted"
      @delayed="handleFeedbackDelayed"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { WarningFilled, Warning, Location, ArrowDown, Download, Check, Flag, Edit, MagicStick, RefreshLeft, CircleCheck } from '@element-plus/icons-vue'
import axios from 'axios'
import { buildProblemKey } from '../shared/problemMarking'
import ProblemSheetAccuracyFeedback from './ProblemSheetAccuracyFeedback.vue'
import staticAnalysisFixService from '@/services/staticAnalysisFixService'

// Props
const props = defineProps({
  problems: {
    type: Array,
    default: () => []
  },
  selectedNode: {
    type: Object,
    default: null
  },
  taskId: {
    type: String,
    required: true
  },
  ruleType: {
    type: String,
    required: true
  },
  // [NEW] 任务级别总问题数（用于准确率反馈计算）
  totalTaskProblems: {
    type: Number,
    default: 0
  },
  // 已访问规则数（用于反馈触发）
  visitedRulesCount: {
    type: Number,
    default: 0
  },
  // 过滤后规则总数（反馈触发分母）
  totalRulesCount: {
    type: Number,
    default: 0
  }
})

// Emits
const emit = defineEmits(['highlightProblem', 'problemStatusChanged', 'viewMarkedProblems', 'requestFix', 'requestBatchFix', 'fixApplied'])

// 响应式数据
const collapsedProblems = ref(new Set())
const markedProblems = ref(new Set()) // 存储已标记的问题键
// 保留：如果后续需要只展示右侧已标记问题，可复用
const showOnlyMarked = ref(false)
const exporting = ref(false)

// 问题单准确率反馈相关
const showFeedbackDialog = ref(false)
const viewedProblemIds = ref(new Set()) // [FIX] 用问题ID而不是index来记录，避免不同文件index重复
const feedbackStatus = ref({
  hasFeedback: false,
  delayedCount: 0,
  alreadyShown: false
})

// 计算属性：判断当前问题是否来自单一标准
const singleRuleType = computed(() => {
  const types = Array.from(new Set(props.problems.map(p => p.rule_type).filter(Boolean)))
  return types.length === 1 ? types[0] : null
})

// 计算属性：统计所有已标记的问题数（跨标准）
const markedProblemsCount = computed(() => {
  return markedProblems.value.size
})

// 计算属性：是否有已标记的问题且来自单一标准
const hasMarkedProblems = computed(() => markedProblems.value.size > 0)

// 基于开关过滤的展示列表
const displayedProblems = computed(() => {
  if (!showOnlyMarked.value) return props.problems
  return props.problems.filter(p => isProblemMarked(p))
})

// 方法
function toggleProblem(problem, index) {
  console.log(`[问题单准确率反馈] toggleProblem被调用: index=${index}, problem.id=${problem?.id}`)
  const isExpanding = !collapsedProblems.value.has(index)
  console.log(`[问题单准确率反馈] isExpanding=${isExpanding}, collapsedProblems.has(${index})=${collapsedProblems.value.has(index)}`)
  if (collapsedProblems.value.has(index)) {
    collapsedProblems.value.delete(index)
  } else {
    collapsedProblems.value.add(index)
  }
  
  // 记录查看的问题（仅在展开时）- [FIX] 使用problem.id而不是index
  const problemId = problem?.id || `idx_${index}`
  
  // 当用户展开问题时，如果是“新发现(1)”且未标记，则自动置为“已查看(2)”
  if (problem && problem.id && (problem.problem_status === 1 || !problem.problem_status)) {
    // 已标记的保持为标记状态
    if (!isProblemMarked(problem)) {
      updateProblemStatus(problem, 2)
    }
  }
}

// 检查并触发反馈
function checkAndTriggerFeedback() {
  if (feedbackStatus.value.hasFeedback) return

  const total = props.totalRulesCount
  const visited = props.visitedRulesCount
  if (total === 0 || visited === 0) return

  const percentage = (visited / total) * 100
  const delayedCount = feedbackStatus.value.delayedCount

  let shouldTrigger = false
  let triggerPoint = ''

  if (delayedCount === 0 && percentage >= 33.4) {
    shouldTrigger = true
    triggerPoint = '1/3'
  } else if (delayedCount === 1 && percentage >= 66.7) {
    shouldTrigger = true
    triggerPoint = '2/3'
  } else if (delayedCount === 2 && percentage >= 100) {
    shouldTrigger = true
    triggerPoint = '3/3'
  }

  if (!shouldTrigger) return

  const shownKey = `feedback_shown_${props.taskId}_${triggerPoint}`
  if (!localStorage.getItem(shownKey)) {
    showFeedbackDialog.value = true
    localStorage.setItem(shownKey, 'true')
  }
}

// 处理反馈提交
function handleFeedbackSubmitted(rate) {
  feedbackStatus.value.hasFeedback = true
  showFeedbackDialog.value = false
  ElMessage.success('感谢您的反馈！')
  // 清除localStorage中的延迟记录
  localStorage.removeItem(`problem_sheet_feedback_delayed_${props.taskId}`)
}

// 处理延迟反馈
function handleFeedbackDelayed(data) {
  feedbackStatus.value.delayedCount = data.delayedCount
  showFeedbackDialog.value = false
}

// 页面加载时检查反馈状态
onMounted(async () => {
  console.log(`[问题单准确率反馈] ==================== 组件挂载 ====================`)
  console.log(`[问题单准确率反馈] taskId=${props.taskId}, ruleType=${props.ruleType}`)
  console.log(`[问题单准确率反馈] localStorage内容:`)
  console.log(`[问题单准确率反馈]   delayed=${localStorage.getItem(`problem_sheet_feedback_delayed_${props.taskId}`)}`)
  console.log(`[问题单准确率反馈]   shown_50%=${localStorage.getItem(`feedback_shown_${props.taskId}_50%`)}`)
  console.log(`[问题单准确率反馈]   shown_80%=${localStorage.getItem(`feedback_shown_${props.taskId}_80%`)}`)
  console.log(`[问题单准确率反馈]   shown_100%=${localStorage.getItem(`feedback_shown_${props.taskId}_100%`)}`)
  
  try {
    const response = await axios.get(`/api/staticAnalysis/filter/${props.taskId}/problem_sheet_accuracy_status`)
    console.log(`[问题单准确率反馈] API响应:`, response.data)
    if (response.data.success) {
      feedbackStatus.value.hasFeedback = response.data.data.has_feedback
      // 从localStorage读取延迟次数
      const delayedCount = parseInt(localStorage.getItem(`problem_sheet_feedback_delayed_${props.taskId}`) || '0')
      feedbackStatus.value.delayedCount = delayedCount
      console.log(`[问题单准确率反馈] 初始化状态: hasFeedback=${feedbackStatus.value.hasFeedback}, delayedCount=${feedbackStatus.value.delayedCount}`)
    }
  } catch (error) {
    console.log('[问题单准确率反馈] 获取反馈状态失败:', error)
  }
  console.log(`[问题单准确率反馈] ==================== 挂载完成 ====================`)
})

function splitSourceSection(value) {
  const text = String(value || '')
  const markers = ['源代码为：', '源程序为：', '源代码为:', '源程序为:']
  const marker = markers.find(item => text.includes(item))

  if (!marker) {
    return { text, source: '' }
  }

  const [prefix, ...rest] = text.split(marker)
  const sourceAndTail = rest.join(marker)
  const impactIndex = sourceAndTail.indexOf('\n影响分析：')

  if (impactIndex >= 0) {
    const source = sourceAndTail.slice(0, impactIndex).trim()
    const tail = sourceAndTail.slice(impactIndex + 1).trim()
    return {
      text: `${prefix.trim()}${marker}`,
      source,
      tail
    }
  }

  return {
    text: `${prefix.trim()}${marker}`,
    source: sourceAndTail.trim()
  }
}

function formatProblemSheetText(value) {
  return splitSourceSection(value).text
}

function extractProblemSheetSource(value) {
  return splitSourceSection(value).source
}

function formatProblemSheetTail(value) {
  return splitSourceSection(value).tail || ''
}

function formatProblemSheetSource(value) {
  const source = extractProblemSheetSource(value)
  if (!source) return ''
  if (source.includes('\n')) return source

  return source
    .replace(/}\s*else\s*{/g, '} else {')
    .replace(/([;{}])\s*/g, '$1\n')
    .replace(/\n{2,}/g, '\n')
    .trim()
}

function locateProblem(problem, index) {
  emit('highlightProblem', {
    problem,
    problemIndex: index,
    nodeInfo: props.selectedNode
  })
  // 定位查看时自动置为已查看
  if (problem && problem.id && (problem.problem_status === 1 || !problem.problem_status)) {
    if (!isProblemMarked(problem)) {
      updateProblemStatus(problem, 2)
    }
  }
}

function getRuleTypeTag(ruleType) {
  if (ruleType === 'gjb') return 'primary'
  if (ruleType === 'cwe') return 'success'
  return 'info'
}

function getProblemSeverity(problem) {
  // 根据问题类型和准确性判断严重程度
  if (problem.rule_accuracy_type === 'accurate') {
    return '重要问题'
  } else if (problem.ai_analyzed && problem.ai_is_real_issue) {
    return '重要问题'
  }
  return '一般问题'
}

function getIssueLevelTagType(level) {
  switch (level) {
    case '重要问题': return 'danger'
    case '一般问题': return 'warning'
    case '建议改进': return 'info'
    default: return 'info'
  }
}

// 问题状态管理（自动）

function getProblemStatusClass(problem) {
  const status = problem.problem_status || 1
  switch (status) {
    case 1: return 'problem-status-new'
    case 2: return 'problem-status-viewed'
    case 3: return 'problem-status-filtered'
    case 4: return 'problem-status-marked'
    default: return 'problem-status-new'
  }
}

function getProblemStatusIndicatorClass(problem) {
  const status = problem.problem_status || 1
  switch (status) {
    case 1: return 'status-indicator-new'
    case 2: return 'status-indicator-viewed'
    case 3: return 'status-indicator-filtered'
    case 4: return 'status-indicator-marked'
    default: return 'status-indicator-new'
  }
}

function getProblemStatusLabel(problem) {
  const status = problem.problem_status || 1
  // 只有已标记显示标签，其他状态不显示（与函数审查保持一致）
  if (status === 4) return '已标记'
  return null
}

function getProblemStatusTagType(problem) {
  const status = problem.problem_status || 1
  // 只有已标记状态会显示标签，使用success类型（绿色勾）
  if (status === 4) return 'success'
  return ''
}

function getProblemStatusButtonType(problem) {
  const status = problem.problem_status || 1
  switch (status) {
    case 1: return 'success'
    case 2: return 'info'
    case 3: return 'info'
    case 4: return 'primary'
    default: return 'info'
  }
}

// 标记功能相关（使用数据库API）
function isProblemMarked(problem) {
  const problemKey = buildProblemKey(problem)
  return markedProblems.value.has(problemKey)
}

async function toggleProblemMark(problem) {
  const problemKey = buildProblemKey(problem)
  const ruleType = problem.rule_type || props.ruleType
  
  try {
    if (isProblemMarked(problem)) {
      // 调用API移除标记
      await axios.delete(`/api/staticAnalysis/filter/${props.taskId}/marked-problems`, {
        data: {
          rule_type: ruleType,
          problem_key: problemKey
        }
      })
      ElMessage.success('已取消标记')
      
      // 如果问题有ID且状态是4（已标记），改为已查看
      if (problem.id && problem.problem_status === 4) {
        await updateProblemStatus(problem, 2)
      }
    } else {
      // 调用API保存标记
      await axios.post(`/api/staticAnalysis/filter/${props.taskId}/marked-problems`, {
        rule_type: ruleType,
        problem_key: problemKey,
        problem_data: problem
      })
      ElMessage.success('已标记问题')
      
      // 如果问题有ID，同时更新状态为4（已标记）
      if (problem.id) {
        await updateProblemStatus(problem, 4)
      }
    }
    
    // 重新加载标记状态
    await loadMarkedProblems()
  } catch (error) {
    console.error('[标记] 操作失败:', error)
    ElMessage.error('操作失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 加载已标记的问题（从数据库API）
async function loadMarkedProblems() {
  try {
    const allMarked = new Set()
    const ruleTypes = ['gjb', 'cwe']

    await Promise.all(
      ruleTypes.map(ruleType =>
        axios
          .get(`/api/staticAnalysis/filter/${props.taskId}/marked-problems`, {
            params: { rule_type: ruleType }
          })
          .then(res => {
            const markedData = res.data?.data || []
            markedData.forEach(item => {
              if (item?.problem_key) {
                allMarked.add(item.problem_key)
              }
            })
          })
          .catch(() => {
            // 忽略单个规则类型的错误，继续处理其他类型
          })
      )
    )

    markedProblems.value = allMarked
  } catch (error) {
    console.error('[标记] 加载失败:', error)
    // 失败时使用空集合
    markedProblems.value = new Set()
  }
}

// 更新问题状态
async function updateProblemStatus(problem, newStatus) {
  if (!problem.id) return
  
  try {
    await axios.patch(
      `/api/staticAnalysis/filter/${props.taskId}/problems/${problem.id}/status`,
      null,
      { params: { status: newStatus } }
    )
    problem.problem_status = newStatus
    emit('problemStatusChanged')
  } catch (error) {
    console.error('[状态] 更新失败:', error)
  }
}

// ========== [NEW] AI 自动修复 ==========

// 单问题修复：交给父组件打开 FixDialog
function requestFix(problem) {
  emit('requestFix', { problem })
}

// 头部「批量修复 ▾」
function handleBatchFixCommand(command) {
  if (command === 'file') {
    emit('requestBatchFix', {
      type: 'file',
      value: selectedNode.value?.file_path || selectedNode.value?.name,
      label: `文件 ${selectedNode.value?.name || ''}`,
      candidates: props.problems
    })
  }
}

// 撤销已应用的修复
async function rollbackFix(problem) {
  if (!problem.fix_id) return
  try {
    await staticAnalysisFixService.rollback(props.taskId, [problem.fix_id])
    problem.fix_status = 0
    problem.fix_id = null
    ElMessage.success('已撤销修复，代码已还原')
    emit('fixApplied', { rolledBack: true, problemId: problem.id })
  } catch (error) {
    ElMessage.error('撤销失败: ' + (error.message || ''))
  }
}

// 导出已标记的问题
async function exportMarkedProblems() {
  if (markedProblems.value.size === 0) {
    ElMessage.warning('没有已标记的问题')
    return
  }
  
  exporting.value = true
  
  try {
    const ruleTypes = ['gjb', 'cwe']
    const combinedMap = new Map()

    const responses = await Promise.all(
      ruleTypes.map(ruleType =>
        axios
          .get(`/api/staticAnalysis/filter/${props.taskId}/marked-problems`, {
            params: { rule_type: ruleType }
          })
          .catch(() => ({ data: { data: [] } }))
      )
    )

    responses.forEach((response, index) => {
      const ruleType = ruleTypes[index]
      const markedData = response.data?.data || []
      markedData.forEach(item => {
        if (!item?.problem_key) return
        const uniqueKey = `${ruleType}::${item.problem_key}`
        if (!combinedMap.has(uniqueKey)) {
          combinedMap.set(uniqueKey, item.problem_data)
        }
      })
    })

    if (combinedMap.size === 0) {
      ElMessage.warning('未找到已标记问题的详情')
      exporting.value = false
      return
    }

    const markedProblemsArray = Array.from(combinedMap.values())

    const response = await axios.post(
      `/api/staticAnalysis/filter/export-marked-problems/${props.taskId}`,
      {
        rule_type: 'all',
        problems: markedProblemsArray
      },
      { responseType: 'blob' }
    )
    
    // 创建下载链接
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `static_analysis_marked_problems_${props.taskId}_all_${new Date().getTime()}.xlsx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('已标记问题导出成功')
  } catch (error) {
    console.error('[导出] 导出失败:', error)
    ElMessage.error('导出失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    exporting.value = false
  }
}

// 监听taskId和problems变化，重新加载标记状态；切换规则/文件节点时同步重置查看记录和折叠状态
watch(
  () => [props.taskId, props.problems],
  () => {
    if (!props.taskId) return
    loadMarkedProblems()
    // 切换规则或文件节点时，重置查看记录，避免跨规则累加导致反馈提前触发

    collapsedProblems.value = new Set()
  },
  { immediate: true, deep: true }
)

// 每次父组件传入新的已访问规则数时检查是否触发反馈
watch(
  () => props.visitedRulesCount,
  () => {
    checkAndTriggerFeedback()
  }
)
</script>

<style scoped>
.problem-list {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
}

.problem-header {
  padding: 20px;
  border-bottom: 1px solid rgba(230, 230, 230, 0.8);
  background: rgba(255, 255, 255, 0.98);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.warning-icon {
  color: #f56c6c;
  font-size: 18px;
}

.problem-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.problem-content {
  flex: 1;
  overflow: auto;
  padding: 20px;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.problems-container {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.problem-block {
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
}

/* 问题状态颜色（与函数审查保持一致） */
.problem-status-new {
  /* 新问题：绿色主题 */
  border-left: 4px solid #22c55e;
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.1) 0%, rgba(16, 185, 129, 0.05) 100%);
  box-shadow: 0 2px 8px rgba(34, 197, 94, 0.15);
}

.problem-status-viewed,
.problem-status-filtered {
  /* 已查看/已过滤：灰色背景，降低透明度 */
  border-left: 4px solid #9ca3af;
  background: #f5f5f5;
  box-shadow: none;
  opacity: 0.9;
}

.problem-status-marked {
  /* 已标记：蓝色边框和背景 */
  border-left: 4px solid #3b82f6;
  background: #eff6ff;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.15);
}

/* [NEW] 已修复：翠绿色主题 */
.problem-fixed {
  border-left: 4px solid #10b981;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(5, 150, 105, 0.06) 100%);
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.18);
}

.problem-block:hover {
  box-shadow: 0 4px 12px rgba(245, 108, 108, 0.2);
  transform: translateY(-2px);
}

.problem-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  cursor: pointer;
  transition: background-color 0.2s ease;
  background: rgba(255, 255, 255, 0.8);
}

.problem-title:hover {
  background: rgba(255, 255, 255, 0.95);
}

.problem-title-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.problem-title-left > span {
  font-weight: 600;
  font-size: 15px;
  color: #303133;
}

.problem-level-tag {
  margin-left: 8px;
}

.problem-status-tag {
  margin-left: 8px;
}

/* 状态指示器（与函数审查保持一致） */
.problem-status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-indicator-new {
  background-color: #22c55e;  /* 绿色 */
  box-shadow: 0 0 6px rgba(34, 197, 94, 0.5);
}

.status-indicator-viewed,
.status-indicator-filtered {
  background-color: #9ca3af;  /* 灰色 */
}

.status-indicator-marked {
  background-color: #3b82f6;  /* 蓝色 */
  box-shadow: 0 0 6px rgba(59, 130, 246, 0.5);
}

/* 下拉菜单中的状态指示器（与函数审查保持一致） */
.status-indicator {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 8px;
  vertical-align: middle;
}

.status-indicator.status-new {
  background-color: #22c55e;
}

.status-indicator.status-viewed,
.status-indicator.status-filtered {
  background-color: #9ca3af;
}

.status-indicator.status-marked {
  background-color: #3b82f6;
}

.problem-title-right {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.problem-title-right .el-button + .el-button {
  margin-left: 0;
}

.collapse-icon {
  transition: transform 0.3s ease;
  cursor: pointer;
  color: #909399;
  font-size: 14px;
  margin-left: 8px;
}

.collapse-icon.collapsed {
  transform: rotate(-90deg);
}

.problem-content {
  padding: 15px 20px 20px 20px;
  display: flex;
  flex-direction: column;
  gap: 15px;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(5px);
}

.problem-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-label {
  font-size: 12px;
  color: #909399;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.field-value {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  word-break: break-word;
}

.confidence {
  margin-left: 8px;
  font-size: 13px;
  color: #909399;
}

.ai-result {
  margin-top: 8px;
  font-size: 13px;
  color: #606266;
  line-height: 1.7;
  padding: 12px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 8px;
  border: 1px solid rgba(230, 230, 230, 0.5);
}

/* 滚动条样式 */
.problem-content::-webkit-scrollbar {
  width: 6px;
}

.problem-content::-webkit-scrollbar-track {
  background: #f5f5f5;
}

.problem-content::-webkit-scrollbar-thumb {
  background: #d9d9d9;
  border-radius: 3px;
}

.problem-content::-webkit-scrollbar-thumb:hover {
  background: #bfbfbf;
}

/* ========== 问题单紧凑样式 ========== */

/* 问题单紧凑容器 */
.problem-sheet-compact {
  padding: 12px 0;
}

/* 问题名称 - 突出显示 */
.problem-sheet-name-highlight {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  border-left: 4px solid #2563eb;
  padding: 10px 14px;
  margin-bottom: 12px;
  border-radius: 6px;
  font-size: 14px;
  line-height: 1.6;
}

.problem-sheet-name-highlight .name-label {
  font-weight: 700;
  color: #1e40af;
  margin-right: 4px;
}

.problem-sheet-name-highlight .name-value {
  font-weight: 600;
  color: #1e3a8a;
}

/* 问题单区块 */
.problem-sheet-section {
  margin-bottom: 10px;
  border-radius: 6px;
  overflow: hidden;
}

/* 四段式描述区块 */
.four-part-section {
  background: #fafafa;
  border-left: 3px solid #8b5cf6;
}

/* 测评单位意见区块 */
.opinion-section {
  background: #fafafa;
  border-left: 3px solid #f59e0b;
}

/* 区块内容 */
.section-content {
  padding: 12px 14px;
}

.section-content pre {
  font-family: inherit;
  font-size: 13px;
  color: #374151;
  line-height: 1.7;
  white-space: pre-wrap;
  word-wrap: break-word;
  word-break: break-word;
  margin: 0;
  padding: 0;
}

.four-part-text {
  font-family: inherit;
  font-size: 13px;
  color: #374151;
  line-height: 1.7;
  white-space: pre-wrap;
  word-wrap: break-word;
  word-break: break-word;
  margin: 0;
  padding: 0;
}

.problem-source-code {
  margin: 10px 0 0 0;
  padding: 12px 14px;
  max-height: 260px;
  overflow: auto;
  border-radius: 6px;
  border: 1px solid #c7d2fe;
  background: #f8fafc;
  color: #111827;
  font-size: 12px;
  line-height: 1.6;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  white-space: pre;
  word-break: normal;
}

.problem-source-code code {
  font-family: inherit;
  color: inherit;
}

.source-tail-text {
  margin-top: 10px;
}

/* 旧版兼容样式 - 确保内容自动换行 */
.field-value pre {
  font-family: inherit;
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
  word-break: break-word;
  overflow-wrap: break-word;
  margin: 0;
  padding: 0;
  max-width: 100%;
  overflow-x: hidden;
}

.field-value.problem-sheet-name,
.field-value.four-part-description,
.field-value.impact-analysis,
.field-value.test-unit-opinion {
  max-width: 100%;
  overflow: visible;
  white-space: pre-wrap;
  word-wrap: break-word;
  word-break: break-word;
}
</style>
