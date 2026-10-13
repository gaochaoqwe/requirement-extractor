<template>
  <div class="problem-list">
    <div class="problem-header">
      <div class="header-title">
        <el-icon class="warning-icon"><WarningFilled /></el-icon>
        <h3>发现的问题</h3>
        <el-tag v-if="problems.length > 0" type="danger" size="small">{{ problems.length }} 个问题</el-tag>
      </div>
      <div class="header-actions">
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
    
    <!-- 图例说明 -->
    <div v-if="problems.length > 0" class="problem-legend">
      <div class="legend-item">
        <div class="legend-dot legend-important"></div>
        <span>重要问题（确定规则或AI确认）</span>
      </div>
      <div class="legend-item">
        <div class="legend-dot legend-ai-filtered"></div>
        <span>AI过滤的问题（AI判定为误报）</span>
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
          v-for="(problem, index) in problems" 
          :key="index" 
          class="problem-block"
          :class="getProblemStatusClass(problem)"
        >
          <div class="problem-title" @click="toggleProblem(index)">
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
                v-if="isAIFiltered(problem)"
                type="info" 
                size="small"
                class="ai-filtered-tag"
                effect="plain"
              >
                🤖 AI已过滤
              </el-tag>
              <el-tag 
                v-if="getProblemStatusLabel(problem)"
                :type="getProblemStatusTagType(problem)" 
                size="small"
                class="problem-status-tag"
              >
                {{ getProblemStatusLabel(problem) }}
              </el-tag>
            </div>
            <div class="problem-title-right">
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
                    <span class="name-value">{{ problem.problem_sheet.issue_name || problem.issue_name || problem.rule_code || '—' }}</span>
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
      :viewed-count="viewedProblemIds.size"
      :total-problems="props.totalTaskProblems"
      :trigger-point="feedbackStatus.delayedCount === 0 ? '50%' : feedbackStatus.delayedCount === 1 ? '80%' : '100%'"
      :delayed-count="feedbackStatus.delayedCount"
      @submitted="handleFeedbackSubmitted"
      @delayed="handleFeedbackDelayed"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { WarningFilled, Warning, Location, ArrowDown, Download, Check, Flag, Edit } from '@element-plus/icons-vue'
import axios from 'axios'
import {
  buildProblemKey,
  saveMarkedProblem,
  removeMarkedProblem,
  getMarkedProblemSet,
  getMarkedProblems
} from '../shared/problemMarking'
import ProblemSheetAccuracyFeedback from './ProblemSheetAccuracyFeedback.vue'

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
  mode: {
    type: String,
    default: 'normal'
  },
  // [NEW] 任务级别总问题数（用于准确率反馈计算）
  totalTaskProblems: {
    type: Number,
    default: 0
  }
})

const isNormalMode = computed(() => props.mode === 'normal')

// Emits
const emit = defineEmits(['highlightProblem', 'problemStatusChanged'])

// 响应式数据
const collapsedProblems = ref(new Set())
const markedProblems = ref(new Set()) // 存储已标记的问题键
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
const hasMarkedProblems = computed(() => {
  return markedProblems.value.size > 0 && singleRuleType.value !== null
})

// 方法
function toggleProblem(index) {
  const isExpanding = !collapsedProblems.value.has(index)
  if (collapsedProblems.value.has(index)) {
    collapsedProblems.value.delete(index)
  } else {
    collapsedProblems.value.add(index)
  }
  
  // 先获取problem对象
  const problem = props.problems[index]
  
  // 记录查看的问题（仅在展开时）- [FIX] 使用problem.id而不是index
  const problemId = problem?.id || `idx_${index}`
  if (isExpanding && !viewedProblemIds.value.has(problemId)) {
    viewedProblemIds.value.add(problemId)
    console.log(`[FPGA问题单准确率反馈] ✅ 记录查看问题: problemId=${problemId}`)
    console.log(`[FPGA问题单准确率反馈] 统计: 总计查看=${viewedProblemIds.value.size}, 过滤后总问题数=${props.totalTaskProblems}`)
    // 检查是否触发反馈
    checkAndTriggerFeedback()
  }
  
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
  console.log(`[FPGA问题单准确率反馈] 检查触发条件...`)
  
  // 如果已经提交过反馈，不再触发
  if (feedbackStatus.value.hasFeedback) {
    console.log(`[FPGA问题单准确率反馈] 已有反馈，跳过触发`)
    return
  }
  
  const total = props.totalTaskProblems || props.problems.length  // 优先使用任务总问题数
  if (total === 0) {
    console.log(`[FPGA问题单准确率反馈] 总问题数为0，跳过触发`)
    return
  }
  
  const viewed = viewedProblemIds.value.size
  const percentage = (viewed / total) * 100
  const delayedCount = feedbackStatus.value.delayedCount
  
  console.log(`[FPGA问题单准确率反馈] 状态检查: viewed=${viewed}, total=${total}, percentage=${percentage.toFixed(2)}%, delayedCount=${delayedCount}`)
  
  // 根据延迟次数设置触发点
  let shouldTrigger = false
  let triggerPoint = ''
  
  if (delayedCount === 0) {
    // 第一次：50%时触发
    if (percentage >= 50) {
      shouldTrigger = true
      triggerPoint = '50%'
    }
  } else if (delayedCount === 1) {
    // 第二次：80%时触发
    if (percentage >= 80) {
      shouldTrigger = true
      triggerPoint = '80%'
    }
  } else if (delayedCount === 2) {
    // 第三次：100%时触发
    if (percentage >= 100) {
      shouldTrigger = true
      triggerPoint = '100%'
    }
  }
  
  console.log(`[FPGA问题单准确率反馈] 触发判断: shouldTrigger=${shouldTrigger}, triggerPoint=${triggerPoint}`)
  
  // 确保每个触发点只触发一次
  const shownKey = `feedback_shown_${props.taskId}_${triggerPoint}`
  const alreadyShown = localStorage.getItem(shownKey)
  console.log(`[FPGA问题单准确率反馈] localStorage检查: shownKey=${shownKey}, alreadyShown=${alreadyShown}`)
  
  if (shouldTrigger && !alreadyShown) {
    console.log(`[FPGA问题单准确率反馈] 触发弹窗显示！`)
    showFeedbackDialog.value = true
    localStorage.setItem(shownKey, 'true')
  } else if (shouldTrigger && alreadyShown) {
    console.log(`[FPGA问题单准确率反馈] 该触发点已显示过，不再触发`)
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

// 页面加载时检查反馈状态（普通模式跳过科代反馈接口）
onMounted(async () => {
  if (isNormalMode.value) {
    feedbackStatus.value.hasFeedback = true
    return
  }
  try {
    const response = await axios.get(`/api/staticAnalysis/filterFpga/${props.taskId}/problem_sheet_accuracy_status`)
    if (response.data.success) {
      feedbackStatus.value.hasFeedback = response.data.data.has_feedback
      const delayedCount = parseInt(localStorage.getItem(`problem_sheet_feedback_delayed_${props.taskId}`) || '0')
      feedbackStatus.value.delayedCount = delayedCount
    }
  } catch (error) {
    console.log('[FPGA问题单准确率反馈] 获取反馈状态失败:', error)
  }
})

function splitSourceSection(value) {
  const text = String(value || '')
  const markers = ['源代码为：', '源程序为：', '源代码为:', '源程序为:']
  const marker = markers.find(item => text.includes(item))
  if (!marker) return { text, source: '' }
  const [prefix, ...rest] = text.split(marker)
  const sourceAndTail = rest.join(marker)
  const impactIndex = sourceAndTail.indexOf('\n影响分析：')
  if (impactIndex >= 0) {
    return {
      text: `${prefix.trim()}${marker}`,
      source: sourceAndTail.slice(0, impactIndex).trim(),
      tail: sourceAndTail.slice(impactIndex + 1).trim()
    }
  }
  return { text: `${prefix.trim()}${marker}`, source: sourceAndTail.trim() }
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
  
  // 记录查看的问题（点击定位时也记录）- [FIX] 使用problem.id而不是index
  const problemId = problem?.id || `idx_${index}`
  if (!viewedProblemIds.value.has(problemId)) {
    viewedProblemIds.value.add(problemId)
    console.log(`[FPGA问题单准确率反馈] ✅ 定位记录查看问题: problemId=${problemId}`)
    console.log(`[FPGA问题单准确率反馈] 统计: 总计查看=${viewedProblemIds.value.size}, 过滤后总问题数=${props.totalTaskProblems}`)
    // 检查是否触发反馈
    checkAndTriggerFeedback()
  }
  
  // 用户定位查看问题时，同步自动置为“已查看(2)”（若当前为新发现且未标记）
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

// 判断问题是否被AI过滤
function isAIFiltered(problem) {
  return problem.rule_accuracy_type === 'uncertain' && 
         problem.ai_analyzed === true && 
         problem.ai_is_real_issue === false
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
  // AI过滤的问题优先级最高，使用特殊样式
  if (isAIFiltered(problem)) {
    return 'problem-ai-filtered'
  }
  
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
  const ruleType = problem.rule_type || props.ruleType || 'fpga'

  try {
    if (isNormalMode.value) {
      if (isProblemMarked(problem)) {
        removeMarkedProblem(String(props.taskId), ruleType, problemKey)
        ElMessage.success('已取消标记')
      } else {
        saveMarkedProblem(String(props.taskId), ruleType, {
          key: problemKey,
          problem
        })
        ElMessage.success('已标记问题')
      }
      await loadMarkedProblems()
      return
    }

    if (isProblemMarked(problem)) {
      await axios.delete(`/api/staticAnalysis/filter/${props.taskId}/marked-problems`, {
        data: { rule_type: ruleType, problem_key: problemKey }
      })
      ElMessage.success('已取消标记')
      if (problem.id && problem.problem_status === 4) {
        await updateProblemStatus(problem, 2)
      }
    } else {
      await axios.post(`/api/staticAnalysis/filter/${props.taskId}/marked-problems`, {
        rule_type: ruleType,
        problem_key: problemKey,
        problem_data: problem
      })
      ElMessage.success('已标记问题')
      if (problem.id) {
        await updateProblemStatus(problem, 4)
      }
    }
    await loadMarkedProblems()
  } catch (error) {
    console.error('[标记] 操作失败:', error)
    ElMessage.error('操作失败: ' + (error.response?.data?.detail || error.message))
  }
}

async function loadMarkedProblems() {
  try {
    if (isNormalMode.value) {
      const allMarked = new Set()
      ;['fpga', 'mixed', 'gjb', 'cwe'].forEach(ruleType => {
        getMarkedProblemSet(String(props.taskId), ruleType).forEach(key => allMarked.add(key))
      })
      markedProblems.value = allMarked
      return
    }

    const allMarked = new Set()
    if (singleRuleType.value) {
      const response = await axios.get(
        `/api/staticAnalysis/filter/${props.taskId}/marked-problems`,
        { params: { rule_type: singleRuleType.value } }
      )
      ;(response.data.data || []).forEach(m => allMarked.add(m.problem_key))
    } else {
      const [gjbResponse, cweResponse] = await Promise.all([
        axios.get(`/api/staticAnalysis/filter/${props.taskId}/marked-problems`, {
          params: { rule_type: 'gjb' }
        }).catch(() => ({ data: { data: [] } })),
        axios.get(`/api/staticAnalysis/filter/${props.taskId}/marked-problems`, {
          params: { rule_type: 'cwe' }
        }).catch(() => ({ data: { data: [] } }))
      ])
      ;(gjbResponse.data.data || []).forEach(m => allMarked.add(m.problem_key))
      ;(cweResponse.data.data || []).forEach(m => allMarked.add(m.problem_key))
    }
    markedProblems.value = allMarked
  } catch (error) {
    console.error('[标记] 加载失败:', error)
    markedProblems.value = new Set()
  }
}

async function updateProblemStatus(problem, newStatus) {
  if (!problem.id || isNormalMode.value) return
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

async function exportMarkedProblems() {
  if (markedProblems.value.size === 0) {
    ElMessage.warning('没有已标记的问题')
    return
  }

  if (isNormalMode.value) {
    exporting.value = true
    try {
      const problems = []
      ;['fpga', 'mixed', 'gjb', 'cwe'].forEach(ruleType => {
        problems.push(...getMarkedProblems(String(props.taskId), ruleType))
      })
      if (!problems.length) {
        ElMessage.warning('未找到已标记问题的详情')
        return
      }
      const blob = new Blob([JSON.stringify(problems, null, 2)], { type: 'application/json' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `normal_mode_fpga_marked_problems_${props.taskId}_${Date.now()}.json`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      ElMessage.success('已标记问题导出成功')
    } catch (error) {
      console.error('[导出] 导出失败:', error)
      ElMessage.error('导出失败: ' + (error.message || error))
    } finally {
      exporting.value = false
    }
    return
  }

  if (!singleRuleType.value) {
    ElMessage.warning('混合视图下无法导出，请切换到单一标准视图')
    return
  }

  exporting.value = true
  try {
    const markedResponse = await axios.get(
      `/api/staticAnalysis/filter/${props.taskId}/marked-problems`,
      { params: { rule_type: singleRuleType.value } }
    )
    const markedData = markedResponse.data.data || []
    if (markedData.length === 0) {
      ElMessage.warning('未找到已标记问题的详情')
      return
    }
    const markedProblemsArray = markedData.map(m => m.problem_data)
    const response = await axios.post(
      `/api/staticAnalysis/filter/export-marked-problems/${props.taskId}`,
      { rule_type: singleRuleType.value, problems: markedProblemsArray },
      { responseType: 'blob' }
    )
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `static_analysis_marked_problems_${props.taskId}_${singleRuleType.value}_${new Date().getTime()}.xlsx`
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

// 监听taskId和problems变化，重新加载标记状态
watch(
  () => [props.taskId, props.problems],
  () => {
    if (!props.taskId) return
    loadMarkedProblems()
  },
  { immediate: true, deep: true }
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

/* 图例样式 */
.problem-legend {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 12px 20px;
  background: #fafafa;
  border-bottom: 1px solid #e8e8e8;
  font-size: 13px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  flex-shrink: 0;
}

.legend-important {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.8) 0%, rgba(16, 185, 129, 0.6) 100%);
  border: 2px solid #22c55e;
}

.legend-ai-filtered {
  background: linear-gradient(135deg, rgba(243, 244, 246, 0.9) 0%, rgba(249, 250, 251, 0.8) 100%);
  border: 2px dashed #d1d5db;
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

/* AI过滤的问题：淡灰色背景，虚线边框 */
.problem-ai-filtered {
  border-left: 4px dashed #d1d5db;
  background: linear-gradient(135deg, rgba(243, 244, 246, 0.9) 0%, rgba(249, 250, 251, 0.8) 100%);
  box-shadow: none;
  opacity: 0.85;
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

.ai-filtered-tag {
  margin-left: 8px;
  font-weight: 500;
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

/* 区块标题标签 */
.section-header-label {
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  padding: 6px 14px 0 14px;
  letter-spacing: 0.3px;
}

/* 规则要求区块 */
.requirement-section {
  background: #f0fdf4;
  border-left: 3px solid #22c55e;
}

/* 问题描述区块 */
.four-part-section {
  background: #fafafa;
  border-left: 3px solid #8b5cf6;
}

/* 问题位置区块 */
.location-section {
  background: #fefce8;
  border-left: 3px solid #eab308;
}

/* 影响分析区块 */
.opinion-section {
  background: #fafafa;
  border-left: 3px solid #f59e0b;
}

/* 区块内容 */
.section-content {
  padding: 10px 12px;
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
  font-size: 13px;
  color: #374151;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

.source-tail-text {
  font-size: 13px;
  color: #374151;
  line-height: 1.7;
  margin-top: 6px;
}

.problem-source-code {
  background: #1e1e2e !important;
  color: #cdd6f4 !important;
  border-radius: 6px;
  padding: 10px 14px;
  font-size: 12px;
  line-height: 1.6;
  overflow-x: auto;
  margin: 8px 0;
  white-space: pre-wrap;
  word-break: break-word;
}

.problem-source-code code {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  color: #cdd6f4 !important;
  background: none !important;
}

.section-header-label {
  font-size: 12px;
  font-weight: 600;
  color: #4b5563;
  padding: 6px 14px 0;
  letter-spacing: 0.3px;
}
</style>

