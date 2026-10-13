<template>
  <div class="static-analysis-code-view">
    <div class="code-view-header">
      <div class="header-left">
        <h2>静态分析代码视图</h2>
      </div>
      <div class="header-center">
        <div class="toggle-group">
          <span class="toggle-label">显示问题：</span>
          <el-switch v-model="showAccurateSelected" active-text="确定勾选" inline-prompt />
          <el-switch v-model="showAccurateUnselected" active-text="确定非勾选" inline-prompt style="margin-left: 10px;" />
          <el-switch v-model="showUncertainSelected" active-text="不确定勾选" inline-prompt style="margin-left: 10px;" />
          <el-switch v-model="showUncertainUnselected" active-text="不确定非勾选" inline-prompt style="margin-left: 10px;" />
        </div>
      </div>
      <div class="header-right">
        <el-button @click="goBack" :icon="Back">返回</el-button>
      </div>
    </div>

    <div v-if="loading" class="loading-container">
      <el-icon class="is-loading" :size="50"><Loading /></el-icon>
      <p>加载代码视图数据中...</p>
    </div>

    <div v-else-if="error" class="error-container">
      <el-alert type="error" :title="error" show-icon :closable="false" />
    </div>

    <div v-else class="code-view-container">
      <!-- 最左侧：规则列表 -->
      <div class="rules-panel">
        <RuleList
          :rules="allRules"
          :show-accurate-selected="showAccurateSelected"
          :show-accurate-unselected="showAccurateUnselected"
          :show-uncertain-selected="showUncertainSelected"
          :show-uncertain-unselected="showUncertainUnselected"
          :selected-rules-set="selectedRulesSet"
          :checked-rules-set="checkedRulesSet"
          @rule-check-change="handleRuleCheckChange"
        />
      </div>

      <!-- 左侧：代码树 -->
      <div class="left-panel">
        <CodeTree 
          :tree-data="treeData"
          :selected-node="selectedNode"
          @node-click="handleNodeClick"
        />
      </div>

      <!-- 中间：源代码视图 -->
      <div class="center-panel">
        <SourceView 
          :selected-node="selectedNode"
          :highlighted-problem="highlightedProblem"
        />
      </div>

      <!-- 右侧：问题列表 -->
      <div class="right-panel">
        <ProblemList 
          :problems="currentProblems"
          :selected-node="selectedNode"
          :task-id="taskId"
          :rule-type="ruleType"
          :total-task-problems="currentRuleTypeTotalProblems"
          @highlight-problem="handleHighlightProblem"
          @problemStatusChanged="handleProblemStatusChanged"
        />
      </div>
    </div>

    <!-- 悬浮进度显示 -->
    <StaticProgressDisplay 
      :gjb-data="gjbProgressData"
      :cwe-data="cweProgressData"
      :visible="showProgress"
      :rule-type="progressRuleType"
      @close="handleProgressClose"
      @download="handleDownload"
    />
    
    <!-- AI审查进度悬浮球已移除 -->
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Back, Loading } from '@element-plus/icons-vue'
import axios from 'axios'
import CodeTree from './components/CodeTree.vue'
import SourceView from './components/SourceView.vue'
import ProblemList from './components/ProblemList.vue'
import RuleList from './components/RuleList.vue'
import StaticProgressDisplay from './shared/StaticProgressDisplay.vue'
// import AIProgressBall from './components/AIProgressBall.vue' // 已移除悬浮球
import staticAnalysisFilterFpgaService from '@/services/staticAnalysisFilterFpgaService'

const route = useRoute()
const router = useRouter()
const isNormalMode = computed(() => route.query.mode === 'normal')

// 路由参数
const taskId = computed(() => route.params.sessionId)  // 路由参数名仍为sessionId，但内部使用taskId

// 响应式数据
const loading = ref(true)
const error = ref('')
const allFiles = ref([])
const allProblems = ref([])
const allRules = ref([])  // 所有规则列表
const checkedRulesSet = ref(new Set())  // 复选框选中的规则集合
const treeData = ref([])
const selectedNode = ref(null)
const highlightedProblem = ref(null)
const previousSelectedNode = ref(null)

// 四个开关状态（对应Excel四个sheet，默认全部开启）
const showAccurateSelected = ref(true)      // 确定规则（勾选）
const showAccurateUnselected = ref(true)    // 确定规则（未勾选）
const showUncertainSelected = ref(true)     // 不确定规则（勾选）
const showUncertainUnselected = ref(true)   // 不确定规则（未勾选）

// 用户选中的规则列表（从FPGA后端获取）
const selectedRulesSet = ref(new Set())

// 当前视图对应的规则类型（ProblemList 默认值使用）
const ruleType = computed(() => isNormalMode.value ? 'mixed' : 'fpga')

// 进度组件使用的规则类型（FPGA同时包含GJB和CWE，使用mixed）
const progressRuleType = computed(() => 'mixed')

// 进度显示相关
const showProgress = ref(false)
const gjbProgressData = ref({
  percentage: 0,
  status: '',
  statusText: '等待中',
  current: 0,
  total: 0
})
const cweProgressData = ref({
  percentage: 0,
  status: '',
  statusText: '等待中',
  current: 0,
  total: 0
})
let progressPollInterval = null

// 悬浮球相关代码已移除

// 判断问题是否被用户勾选
const isProblemSelected = (problem) => {
  if (!problem.rule_code) return false
  return selectedRulesSet.value.has(problem.rule_code)
}

// 过滤后的问题列表（根据四个开关 + 复选框选中状态）
const filteredProblems = computed(() => {
  const filtered = allProblems.value.filter(p => {
    // 关键：只显示复选框选中的规则对应的问题
    if (!checkedRulesSet.value.has(p.rule_code)) {
      return false
    }

    const isSelected = isProblemSelected(p)
    const accuracyType = p.rule_accuracy_type

    // 根据准确度和是否勾选进行过滤
    if (accuracyType === 'accurate') {
      if (isSelected) {
        return showAccurateSelected.value  // 确定规则（勾选）
      } else {
        return showAccurateUnselected.value  // 确定规则（未勾选）
      }
    }

    if (accuracyType === 'uncertain') {
      if (isSelected) {
        return showUncertainSelected.value  // 不确定规则（勾选）
      } else {
        return showUncertainUnselected.value  // 不确定规则（未勾选）
      }
    }

    return false
  })
  
  console.log('[FPGA问题过滤]', {
    总问题数: allProblems.value.length,
    已选规则数: checkedRulesSet.value.size,
    过滤后问题数: filtered.length
  })
  
  return filtered
})

// 当前选中节点的问题
const currentProblems = computed(() => {
  if (!selectedNode.value) {
    return []
  }
  
  // 根据选中的文件过滤问题（支持路径匹配）
  const fileName = selectedNode.value.name
  const filePath = selectedNode.value.file_path
  
  return filteredProblems.value.filter(p => {
    // 精确匹配文件名
    if (p.issue_file === fileName) return true
    if (p.issue_file === filePath) return true
    
    // 提取basename进行精确比较
    const issueFileBasename = p.issue_file ? p.issue_file.split(/[/\\]/).pop() : ''
    if (issueFileBasename === fileName) return true
    
    // 路径结尾匹配（必须前面有路径分隔符）
    if (p.issue_file && (p.issue_file.endsWith('/' + fileName) || p.issue_file.endsWith('\\' + fileName))) return true
    
    return false
  })
})

// [NEW] 过滤后的问题数（确定勾选+AI确认的问题，用于问题单准确率反馈）
const currentRuleTypeTotalProblems = computed(() => {
  // 使用filteredProblems的长度（已经过四分类过滤和规则复选框过滤）
  return filteredProblems.value.length
})

// 初始化规则复选框状态（默认全部不勾选，用户需手动选择）
function initializeCheckedRules() {
  // 默认空集合，不勾选任何规则
  checkedRulesSet.value = new Set()
  console.log('[FPGA规则选择] 初始化复选框，默认不勾选任何规则，共', allRules.value.length, '条规则可选')
}

// 处理规则复选框状态变化
function handleRuleCheckChange(ruleCode, checked) {
  const newSet = new Set(checkedRulesSet.value)
  if (checked) {
    newSet.add(ruleCode)
  } else {
    newSet.delete(ruleCode)
  }
  checkedRulesSet.value = newSet
  console.log('[FPGA规则选择]', ruleCode, checked ? '选中' : '取消选中', '，当前选中:', checkedRulesSet.value.size, '条')
}

// 组件挂载时加载数据
onMounted(async () => {
  console.log('[FPGA代码视图] 组件挂载, taskId:', taskId.value)
  if (!isNormalMode.value) {
    startProgressPolling()
  }
  await loadCodeViewData()
  initializeCheckedRules()
})

onUnmounted(() => {
  // 清理进度轮询
  if (progressPollInterval) {
    clearInterval(progressPollInterval)
  }
})

// 监听开关变化，重建代码树和规则复选框状态
watch([showAccurateSelected, showAccurateUnselected, showUncertainSelected, showUncertainUnselected, allFiles], () => {
  if (allFiles.value.length > 0) {
    treeData.value = buildTreeData(allFiles.value)
    // 如果当前选中的节点不在新树中，则清除选择
    if (selectedNode.value && treeData.value.length > 0) {
      const exists = treeData.value.find(node => node.id === selectedNode.value.id)
      if (!exists) {
        selectedNode.value = treeData.value[0]
      }
    }
  }
  // 当开关变化时，重新初始化规则复选框状态
  if (allRules.value.length > 0) {
    initializeCheckedRules()
  }
})

// 监听规则复选框变化，重建代码树（更新问题数量）
watch(checkedRulesSet, () => {
  if (allFiles.value.length > 0) {
    console.log('[FPGA代码树] 规则复选框变化，重建代码树，当前选中规则数:', checkedRulesSet.value.size)
    treeData.value = buildTreeData(allFiles.value)
    if (selectedNode.value && treeData.value.length > 0) {
      const exists = treeData.value.find(node => node.id === selectedNode.value.id)
      if (!exists && treeData.value[0]) {
        selectedNode.value = treeData.value[0]
      }
    }
  }
})

// 加载FPGA代码视图数据
async function loadCodeViewData() {
  try {
    loading.value = true
    error.value = ''

    if (isNormalMode.value) {
      const response = await axios.get(`/api/staticAnalysis/codemap/${taskId.value}`)
      const data = response.data?.data || {}
      selectedRulesSet.value = new Set(data.selected_rules || [])
      allFiles.value = dedupeFiles((data.files || []).map(file => ({
        file_name: file.name || file.file_name,
        file_path: file.path || file.file_path,
        source_code: file.source_code || ''
      })))
      allProblems.value = []
      allRules.value = data.rules || []
      treeData.value = buildTreeData(allFiles.value)
      if (treeData.value.length > 0) {
        selectedNode.value = treeData.value[0]
      }
      return
    }

    console.log('[FPGA代码视图] ===== 开始加载数据 =====')
    console.log('[FPGA代码视图] 请求URL:', `/api/staticAnalysis/filterFpga/code-view/${taskId.value}`)
    const fpgaRes = await axios.get(`/api/staticAnalysis/filterFpga/code-view/${taskId.value}`)
    console.log('[FPGA代码视图] API响应:', fpgaRes.data)
    const fpgaData = fpgaRes.data.success ? fpgaRes.data.data : { files: [], problems: [], selected_rules: [] }
    
    selectedRulesSet.value = new Set(fpgaData.selected_rules || [])
    console.log('[FPGA代码视图] 用户勾选的规则数量:', selectedRulesSet.value.size)
    
    allFiles.value = dedupeFiles([...(fpgaData.files || [])])
    allProblems.value = [...(fpgaData.problems || []).map(p => ({ ...p, rule_type: p.rule_type || 'fpga' }))]
    allRules.value = [...(fpgaData.rules || [])]
    
    console.log('[FPGA规则] 加载的规则数据:', allRules.value)
    console.log('[FPGA规则] 规则分类统计:', {
      accurate: allRules.value.filter(r => r.accuracy_type === 'accurate').length,
      uncertain: allRules.value.filter(r => r.accuracy_type === 'uncertain').length,
      无accuracy_type: allRules.value.filter(r => !r.accuracy_type).length
    })
    
    console.log('[代码视图] 合并后数据:', {
      文件数: allFiles.value.length,
      总问题数: allProblems.value.length,
      规则数: allRules.value.length
    })
    
    const problemStats = {
      gjb_accurate: 0,
      gjb_uncertain_ai_true: 0,
      cwe_accurate: 0,
      cwe_uncertain_ai_true: 0
    }
    
    allProblems.value.forEach(p => {
      const prefix = p.rule_type === 'gjb' ? 'gjb' : 'cwe'
      if (p.rule_accuracy_type === 'accurate') {
        problemStats[`${prefix}_accurate`]++
      } else if (p.rule_accuracy_type === 'uncertain' && p.ai_analyzed && p.ai_is_real_issue) {
        problemStats[`${prefix}_uncertain_ai_true`]++
      }
    })
    
    console.log('[代码视图] 问题统计:', problemStats)
    treeData.value = buildTreeData(allFiles.value)
    if (treeData.value.length > 0) {
      selectedNode.value = treeData.value[0]
    }
    
    const totalAccurate = problemStats.gjb_accurate + problemStats.cwe_accurate
    const totalUncertainAiTrue = problemStats.gjb_uncertain_ai_true + problemStats.cwe_uncertain_ai_true
    const totalProcessed = totalAccurate + totalUncertainAiTrue
    
    gjbProgressData.value = {
      percentage: 100,
      status: 'success',
      statusText: '✅ FPGA分析完成',
      current: totalProcessed,
      total: totalProcessed || allProblems.value.length
    }
    showProgress.value = true
    console.log('[FPGA代码视图] 设置已完成的进度显示')
    
  } catch (err) {
    console.error('[代码视图] 加载数据失败:', err)
    error.value = '加载代码视图数据失败: ' + (err.response?.data?.detail || err.message)
    ElMessage.error(error.value)
  } finally {
    loading.value = false
  }
}

// 启动进度轮询
function startProgressPolling() {
  if (isNormalMode.value) {
    return
  }
  checkProgress()
  progressPollInterval = setInterval(() => {
    checkProgress()
  }, 5000)
}

// 检查进度
async function checkProgress() {
  try {
    console.log('[DEBUG][FPGA代码视图] ===== 开始检查进度 =====')
    console.log('[DEBUG][FPGA代码视图] taskId:', taskId.value, 'taskId类型:', typeof taskId.value)
    
    // 使用和主界面相同的progress API（而不是detailed API）
    const progressUrl = `/api/staticAnalysis/filterFpga/progress/${taskId.value}`
    console.log('[DEBUG][FPGA代码视图] 请求URL:', progressUrl)
    
    const response = await axios.get(progressUrl)
    
    console.log('[DEBUG][FPGA代码视图] 响应状态:', response.status)
    console.log('[DEBUG][FPGA代码视图] 响应数据:', response.data)
    
    if (response.data && response.data.success) {
      // 将progress数据包装成和detailed API相同的格式
      const statusData = {
        success: true,
        session_id: taskId.value,
        fpga: response.data.progress
      }
      updateProgressDisplay(statusData)
    } else {
      console.warn('[代码视图] 进度API返回失败:', response.data)
    }
  } catch (error) {
    // 404错误说明会话已被清理（项目已完成），停止轮询
    if (error.response?.status === 404) {
      console.log('[FPGA代码视图] 会话不存在(项目已完成)，停止进度轮询')
      if (progressPollInterval) {
        clearInterval(progressPollInterval)
        progressPollInterval = null
      }
      return
    }
    
    console.error('[DEBUG][FPGA代码视图] ===== 获取进度失败 =====')
    console.error('[DEBUG][FPGA代码视图] 错误对象:', error)
    console.error('[DEBUG][FPGA代码视图] 错误消息:', error.message)
    console.error('[DEBUG][FPGA代码视图] 响应状态码:', error.response?.status)
    console.error('[DEBUG][FPGA代码视图] 响应数据:', error.response?.data)
    console.error('[DEBUG][FPGA代码视图] 请求配置:', error.config?.url)
  }
}

// 更新进度显示
function updateProgressDisplay(statusData) {
  console.log('[FPGA代码视图] 更新进度显示:', statusData)
  
  let hasActiveTask = false // 标记是否有正在进行的任务
  
  // FPGA只有一个进度对象
  if (statusData.fpga) {
    const fpga = statusData.fpga
    const fpgaStatus = fpga.status
    console.log('[FPGA代码视图] FPGA状态:', fpgaStatus, '完整数据:', fpga)
    
    // 使用和主界面完全一样的进度计算逻辑（见StaticAnalysisFilter.vue:1382-1395）
    const aiProcessingTotal = fpga.ai_processing_total || fpga.uncertain_selected_issues || fpga.uncertain_issues || 0
    const uncertainProcessed = Math.max((fpga.processed_issues || 0) - (fpga.accurate_issues || 0), 0)
    const aiProcessedIssues = Math.min(uncertainProcessed, aiProcessingTotal)
    
    // 计算进度百分比：直接用分数转百分比
    let progressPercentage = 0
    if (fpgaStatus === 'completed') {
      // 完成状态也用实际进度，不强制100%
      progressPercentage = aiProcessingTotal > 0
        ? Math.round((aiProcessedIssues / aiProcessingTotal) * 100)
        : 100
    } else {
      progressPercentage = aiProcessingTotal > 0
        ? Math.round((aiProcessedIssues / aiProcessingTotal) * 100)
        : 0
    }
    
    console.log('[FPGA代码视图] 进度计算（和主界面一致）:', {
      aiProcessedIssues,
      aiProcessingTotal,
      分数: `${aiProcessedIssues}/${aiProcessingTotal}`,
      progressPercentage: `${progressPercentage}%`,
      processed_issues: fpga.processed_issues,
      accurate_issues: fpga.accurate_issues
    })
    
    if (fpgaStatus === 'completed') {
      gjbProgressData.value = {
        percentage: progressPercentage,
        status: 'success',
        statusText: '✅ FPGA分析完成',
        current: aiProcessedIssues,
        total: aiProcessingTotal
      }
      // CWE数据清空（FPGA不使用）
      cweProgressData.value = {
        percentage: 0,
        status: '',
        statusText: '',
        current: 0,
        total: 0
      }
    } else if (fpgaStatus === 'processing' || fpgaStatus === 'ai_analyzing') {
      gjbProgressData.value = {
        percentage: progressPercentage,
        status: '',
        statusText: '🔄 FPGA AI智能分析中...',
        current: aiProcessedIssues,
        total: aiProcessingTotal
      }
      hasActiveTask = true
      
      // CWE数据清空
      cweProgressData.value = {
        percentage: 0,
        status: '',
        statusText: '',
        current: 0,
        total: 0
      }
    } else if (fpgaStatus === 'filtering') {
      gjbProgressData.value = {
        percentage: 30,
        status: '',
        statusText: '🔍 FPGA关键词过滤中...',
        current: 0,
        total: fpga.total_issues || 0
      }
      hasActiveTask = true
      
      cweProgressData.value = { percentage: 0, status: '', statusText: '', current: 0, total: 0 }
    } else if (fpgaStatus === 'pending' || fpgaStatus === 'uploading') {
      gjbProgressData.value = {
        percentage: 10,
        status: '',
        statusText: '⏳ FPGA准备中...',
        current: 0,
        total: 0
      }
      hasActiveTask = true
      
      cweProgressData.value = { percentage: 0, status: '', statusText: '', current: 0, total: 0 }
    }
  }
  
  console.log('[FPGA代码视图] hasActiveTask:', hasActiveTask, 'showProgress.value:', showProgress.value)
  
  // 检查是否有FPGA任务数据
  const hasAnyTaskData = gjbProgressData.value.total > 0
  
  // 在代码视图中，只要有任务数据就显示进度框（无论是否完成）
  if (hasAnyTaskData) {
    showProgress.value = true
    console.log('[FPGA代码视图] 有FPGA任务数据，显示进度组件')
  }
  
  // 如果FPGA任务完成，停止轮询
  const fpgaCompleted = statusData.fpga?.status === 'completed'
  
  if (fpgaCompleted) {
    console.log('[FPGA代码视图] FPGA任务已完成，停止轮询')
    if (progressPollInterval) {
      clearInterval(progressPollInterval)
      progressPollInterval = null
    }
  }
}

// 文件去重函数
function dedupeFiles(files) {
  const fileMap = new Map()
  files.forEach(file => {
    // 优先使用file_path作为键，回退到file_name
    const key = file.file_path || file.file_name
    if (key && !fileMap.has(key)) {
      fileMap.set(key, file)
    }
  })
  return Array.from(fileMap.values())
}

// 构建树形数据（使用过滤后的问题）
function buildTreeData(files) {
  const treeNodes = files.map((file, index) => {
    // 计算该文件的问题数（使用过滤后的问题列表）
    const fileProblems = filteredProblems.value.filter(p => {
      // 精确匹配文件名
      if (p.issue_file === file.file_name) return true
      if (p.issue_file === file.file_path) return true
      
      // 提取问题文件的basename（最后一段路径）
      const issueFileBasename = p.issue_file ? p.issue_file.split(/[/\\]/).pop() : ''
      if (issueFileBasename === file.file_name) return true
      
      // 路径结尾匹配（必须前面有路径分隔符，避免clock_divider.v匹配到divider.v）
      if (p.issue_file && (p.issue_file.endsWith('/' + file.file_name) || p.issue_file.endsWith('\\' + file.file_name))) return true
      
      return false
    })
    
    const node = {
      id: `file_${index}`,
      name: file.file_name,
      type: 'file',
      file_path: file.file_path,
      source_code: file.source_code,
      problems: fileProblems,
      problemCount: fileProblems.length
    }
    
    return node
  })
  
  console.log('[代码树] 构建完成，节点数:', treeNodes.length)
  
  return treeNodes
}

// 处理节点点击
function handleNodeClick(node) {
  console.log('[代码视图] 选中节点:', node.name)
  // 在切换到新文件前，自动将当前文件中的“新发现(1)”问题批量置为“已查看(2)”
  if (selectedNode.value) {
    markNodeProblemsViewed(selectedNode.value)
    previousSelectedNode.value = selectedNode.value
  }
  selectedNode.value = node
  highlightedProblem.value = null // 清除高亮
}

// 处理问题高亮
function handleHighlightProblem(problemInfo) {
  console.log('[代码视图] 高亮问题:', problemInfo)
  highlightedProblem.value = problemInfo
}

// 问题状态更新后，重建代码树以刷新左侧聚合状态颜色
function handleProblemStatusChanged() {
  try {
    if (allFiles.value && allFiles.value.length > 0) {
      treeData.value = buildTreeData(allFiles.value)
    }
  } catch (e) {
    // ignore
  }
}

// 批量将某个节点（文件）下的“新发现(1)”问题更新为“已查看(2)”
async function markNodeProblemsViewed(node) {
  try {
    const ids = getNewProblemIdsForNode(node)
    if (ids.length === 0) return
    await axios.patch(`/api/staticAnalysis/filter/${taskId.value}/problems/status`, {
      problem_ids: ids,
      status: 2
    })
    // 本地同步状态
    allProblems.value = allProblems.value.map(p => ids.includes(p.id) ? { ...p, problem_status: 2 } : p)
    // 刷新树颜色
    treeData.value = buildTreeData(allFiles.value)
  } catch (e) {
    console.warn('[自动置灰] 批量更新失败: ', e)
  }
}

// 取出给定节点对应文件下处于新发现(1)的问题ID
function getNewProblemIdsForNode(node) {
  const fileName = node.name
  const filePath = node.file_path
  const problemsForNode = (allProblems.value || []).filter(p => {
    if (p.issue_file === fileName) return true
    if (p.issue_file === filePath) return true
    if (p.issue_file && p.issue_file.endsWith(fileName)) return true
    const issueFileBasename = p.issue_file ? p.issue_file.split(/[\/\\]/).pop() : ''
    if (issueFileBasename === fileName) return true
    return false
  })
  return problemsForNode
    .filter(p => p && p.id && (p.problem_status === 1 || !p.problem_status))
    .map(p => p.id)
}

// 处理进度关闭
function handleProgressClose() {
  showProgress.value = false
  if (progressPollInterval) {
    clearInterval(progressPollInterval)
    progressPollInterval = null
  }
}

// 处理下载
async function handleDownload() {
  try {
    console.log('[FPGA代码视图] 下载完整问题单:', { taskId: taskId.value })
    
    // 需要先将task_id转换为session_id
    // 从数据库查询session_id
    let sessionIdForDownload = null
    try {
      // 假设taskId是数字ID，尝试从数据库获取session_id
      const response = await axios.get(`/api/staticAnalysis/filterFpga/task/${taskId.value}/session`)
      if (response.data && response.data.success) {
        sessionIdForDownload = response.data.session_id
      }
    } catch (err) {
      // 如果获取失败，可能taskId本身就是session_id，直接使用
      console.warn('[FPGA代码视图] 无法通过task_id获取session_id，尝试直接使用taskId')
      sessionIdForDownload = taskId.value
    }
    
    if (!sessionIdForDownload) {
      throw new Error('无法获取会话ID')
    }
    
    console.log('[FPGA代码视图] 使用session_id下载:', sessionIdForDownload)
    
    // 使用和进度页面相同的下载端点：/download-split/（四分分类+AI高亮）
    const url = `/api/staticAnalysis/filterFpga/download-split/${sessionIdForDownload}?highlight_ai=true`
    const downloadResponse = await fetch(url)
    
    if (!downloadResponse.ok) {
      throw new Error(`下载失败: ${downloadResponse.statusText}`)
    }
    
    // 从响应头获取文件名
    const contentDisposition = downloadResponse.headers.get('Content-Disposition')
    let filename = 'FPGA_完整问题单_四分分类.xlsx'
    if (contentDisposition) {
      const matches = contentDisposition.match(/filename="?(.+?)"?$/)
      if (matches && matches[1]) {
        filename = decodeURIComponent(matches[1])
      }
    }
    
    // 下载文件
    const blob = await downloadResponse.blob()
    const blobUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = blobUrl
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(blobUrl)
    
    ElMessage.success('FPGA完整问题单（四个Sheet，含AI确认高亮）下载成功')
  } catch (error) {
    console.error('[FPGA代码视图] 下载失败:', error)
    ElMessage.error('下载失败: ' + error.message)
  }
}

// 返回
function goBack() {
  router.back()
}
</script>

<style scoped>
.static-analysis-code-view {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #1e1e1e;
  color: #e0e0e0;
  overflow: hidden;
}

/* 防止进度条元素意外渲染到FPGA代码视图主容器中 */
.code-view-container :deep(.el-progress),
.code-view-container :deep(.el-progress-bar),
.code-view-container :deep(.el-progress-bar__outer),
.code-view-container :deep(.el-progress-bar__inner) {
  display: none !important;
}

.code-view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 30px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
  flex: 0 0 auto;
}

.header-left h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.header-center {
  display: flex;
  gap: 30px;
  align-items: center;
  flex: 1;
  justify-content: center;
}

.toggle-group {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(255, 255, 255, 0.1);
  padding: 8px 16px;
  border-radius: 8px;
  backdrop-filter: blur(10px);
}

.toggle-label {
  font-size: 14px;
  font-weight: 500;
  color: white;
  white-space: nowrap;
}

.header-right {
  display: flex;
  gap: 10px;
  flex: 0 0 auto;
}

.loading-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
  color: #666;
}

.error-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.code-view-container {
  flex: 1;
  display: grid;
  grid-template-columns: 250px 300px 1fr 500px;
  gap: 0;
  overflow: hidden;
}

.rules-panel {
  background: white;
  border-right: 1px solid #e0e0e0;
  overflow: hidden;
}

.left-panel {
  background: white;
  border-right: 1px solid #e0e0e0;
  overflow: hidden;
}

.center-panel {
  background: #1a1a1a;
  overflow: hidden;
}

.right-panel {
  background: white;
  border-left: 1px solid #e0e0e0;
  overflow: hidden;
}

/* 响应式设计 */
@media (max-width: 1600px) {
  .code-view-container {
    grid-template-columns: 220px 280px 1fr 450px;
  }
}

@media (max-width: 1400px) {
  .code-view-container {
    grid-template-columns: 200px 250px 1fr 400px;
  }
}

@media (max-width: 1200px) {
  .code-view-container {
    grid-template-columns: 180px 220px 1fr 350px;
  }
}
</style>

