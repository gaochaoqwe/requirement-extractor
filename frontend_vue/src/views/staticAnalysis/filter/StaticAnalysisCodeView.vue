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
        <el-dropdown trigger="click" @command="handleExportCommand">
          <el-button type="success" plain :loading="exporting">
            <el-icon><Download /></el-icon>
            导出修复结果
            <el-tag v-if="appliedFixCount > 0" type="success" size="small" effect="dark" class="export-count">
              {{ appliedFixCount }}
            </el-tag>
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="current" :disabled="!selectedNode">
                导出当前文件{{ selectedNode ? ` (${selectedNode.name})` : '（未选中文件）' }}
              </el-dropdown-item>
              <el-dropdown-item command="package" divided>
                导出修复后的代码库 (.zip)
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
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
          :rules="filteredRules"
          :show-accurate-selected="showAccurateSelected"
          :show-accurate-unselected="showAccurateUnselected"
          :show-uncertain-selected="showUncertainSelected"
          :show-uncertain-unselected="showUncertainUnselected"
          :selected-rules-set="selectedRulesSet"
          :checked-rules-set="checkedRulesSet"
          @rule-check-change="handleRuleCheckChange"
          @request-batch-fix="handleRequestBatchFix"
        />
      </div>

      <!-- 左侧：代码树 -->
      <div class="left-panel">
        <CodeTree 
          :tree-data="treeData"
          :selected-node="selectedNode"
          @node-click="handleNodeClick"
          @request-batch-fix="handleRequestBatchFix"
        />
      </div>

      <!-- 中间：源代码视图 -->
      <div class="center-panel">
        <SourceView 
          :selected-node="selectedNode"
          :highlighted-problem="highlightedProblem"
          :fixed-lines="fixedLinesForSelected"
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
          :visited-rules-count="visitedRulesSet.size"
          :total-rules-count="filteredRules.length"
          @highlight-problem="handleHighlightProblem"
          @problemStatusChanged="handleProblemStatusChanged"
          @viewMarkedProblems="handleViewMarkedProblems"
          @request-fix="handleRequestFix"
          @request-batch-fix="handleRequestBatchFix"
          @fix-applied="handleFixApplied"
        />
      </div>
    </div>

    <!-- AI 单问题修复弹窗 -->
    <FixDialog
      v-model:visible="fixDialogVisible"
      :problem="fixProblem"
      :task-id="taskId"
      :rule-type="ruleType === 'mixed' ? 'gjb' : ruleType"
      @applied="handleFixApplied"
    />

    <!-- 批量修复面板（文件级 / 规则级） -->
    <BatchFixPanel
      v-model:visible="batchPanelVisible"
      :task-id="taskId"
      :scope="batchScope"
      :candidates="batchCandidates"
      @applied="handleFixApplied"
    />

    <!-- 悬浮进度显示 -->
    <StaticProgressDisplay 
      :gjb-data="gjbProgressData"
      :cwe-data="cweProgressData"
      :visible="showProgress"
      :rule-type="ruleType"
      @close="handleProgressClose"
      @download="handleDownload"
    />
    
    <!-- AI审查进度悬浮球已移除，只保留进度界面的大进度框 -->
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Back, Loading, Download, ArrowDown } from '@element-plus/icons-vue'
import axios from 'axios'
import CodeTree from './components/CodeTree.vue'
import SourceView from './components/SourceView.vue'
import ProblemList from './components/ProblemList.vue'
import RuleList from './components/RuleList.vue'
import FixDialog from './components/FixDialog.vue'
import BatchFixPanel from './components/BatchFixPanel.vue'
import StaticProgressDisplay from './shared/StaticProgressDisplay.vue'
// import AIProgressBall from './components/AIProgressBall.vue' // 已移除悬浮球
import staticAnalysisFilterService from '@/services/staticAnalysisFilterService'
import staticAnalysisFixService from '@/services/staticAnalysisFixService'

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
const markedFilesSet = ref(new Set())
const markedFileProblemMap = ref({})
const markedViewLoading = ref(false)

// ========== [NEW] 自动修复相关状态 ==========
const fixDialogVisible = ref(false)
const fixProblem = ref(null)
const batchPanelVisible = ref(false)
const batchScope = ref(null)
const batchCandidates = ref([])
const exporting = ref(false)
const fixedFiles = ref([])                     // 已应用修复的文件列表
const fixedLinesByFile = ref({})               // { 'src/main.c': [12, 13] }

const appliedFixCount = computed(() =>
  fixedFiles.value.reduce((sum, item) => sum + (item.fixed_count || 0), 0)
)

const fixedLinesForSelected = computed(() => {
  if (!selectedNode.value) return []
  const keys = [
    selectedNode.value.file_path,
    selectedNode.value.name,
    selectedNode.value.id
  ].filter(Boolean)
  for (const key of keys) {
    const lines = fixedLinesByFile.value[key]
    if (lines && lines.length) return lines
  }
  return []
})

// 四个开关状态（对应Excel四个sheet，默认全部开启）
const showAccurateSelected = ref(true)      // 确定规则（勾选）
const showAccurateUnselected = ref(true)    // 确定规则（未勾选）
const showUncertainSelected = ref(true)     // 不确定规则（勾选）
const showUncertainUnselected = ref(true)   // 不确定规则（未勾选）

// 用户选中的规则列表（从后端获取）
const selectedRulesSet = ref(new Set())
// 用户访问过的规则（点击即算，用于准确率反馈触发）
const visitedRulesSet = ref(new Set())

// 当前视图对应的规则类型（从路由参数获取）
const ruleType = computed(() => {
  if (isNormalMode.value) {
    return 'mixed'
  }
  const routeType = route.query.type
  if (routeType === 'gjb') return 'gjb'
  if (routeType === 'cwe') return 'cwe'
  return 'mixed'
})

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

// 进度轮询定时器
let progressPollInterval = null

// 判断问题是否被用户勾选
const isProblemSelected = (problem) => {
  if (!problem.rule_code) return false
  return selectedRulesSet.value.has(problem.rule_code)
}

// 过滤后的规则列表（根据当前视图类型）
const filteredRules = computed(() => {
  const currentRuleType = ruleType.value
  const filtered = allRules.value.filter(rule => {
    // 只显示当前规则类型的规则
    if (currentRuleType !== 'mixed' && rule.rule_type !== currentRuleType) {
      return false
    }
    return true
  })
  
  console.log('[规则过滤]', {
    当前视图类型: currentRuleType,
    全部规则数: allRules.value.length,
    过滤后规则数: filtered.length,
    规则类型分布: {
      gjb: allRules.value.filter(r => r.rule_type === 'gjb').length,
      cwe: allRules.value.filter(r => r.rule_type === 'cwe').length
    }
  })
  
  return filtered
})

// 过滤后的问题列表（根据四个开关 + 复选框选中状态）
const filteredProblems = computed(() => {
  const filtered = allProblems.value.filter(p => {
    // 只显示当前规则类型的问题
    const currentRuleType = ruleType.value
    if (currentRuleType !== 'mixed' && p.rule_type !== currentRuleType) {
      return false
    }

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
  
  console.log('[问题过滤]', {
    总问题数: allProblems.value.length,
    已选规则数: checkedRulesSet.value.size,
    过滤后问题数: filtered.length,
    四个开关: {
      确定勾选: showAccurateSelected.value,
      确定非勾选: showAccurateUnselected.value,
      不确定勾选: showUncertainSelected.value,
      不确定非勾选: showUncertainUnselected.value
    }
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
    // 尝试多种匹配方式：
    // 1. 精确匹配文件名
    if (p.issue_file === fileName) return true
    // 2. 精确匹配文件路径
    if (p.issue_file === filePath) return true
    // 3. issue_file以fileName结尾（处理路径情况）
    if (p.issue_file && p.issue_file.endsWith(fileName)) return true
    // 4. 提取issue_file的basename进行比较
    const issueFileBasename = p.issue_file ? p.issue_file.split(/[/\\]/).pop() : ''
    if (issueFileBasename === fileName) return true
    
    return false
  })
})

// [NEW] 过滤后的问题数（确定勾选+AI确认的问题，用于问题单准确率反馈）
const currentRuleTypeTotalProblems = computed(() => {
  // 使用filteredProblems的长度（已经过四分类过滤和规则复选框过滤）
  const count = filteredProblems.value.length
  console.log(`[父组件] 过滤后问题数: ${count}, ruleType=${ruleType.value}`)
  return count
})

// 初始化规则复选框状态（默认全部不勾选，用户需手动选择）
function initializeCheckedRules() {
  // 默认空集合，不勾选任何规则
  checkedRulesSet.value = new Set()
  console.log('[规则选择] 初始化复选框，默认不勾选任何规则，共', filteredRules.value.length, '条规则可选')
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
  // 记录"访问过"的规则（点击即算，不论勾选还是取消）
  visitedRulesSet.value = new Set([...visitedRulesSet.value, ruleCode])
  console.log('[规则选择]', ruleCode, checked ? '选中' : '取消选中', '，当前选中:', checkedRulesSet.value.size, '条，已访问:', visitedRulesSet.value.size, '条')
}

// 组件挂载时加载数据
onMounted(async () => {
  console.log('[代码视图] 组件挂载, taskId:', taskId.value)
  // 立即启动进度轮询
  startProgressPolling()
  // 加载数据
  await loadCodeViewData()
  // 初始化规则复选框状态
  initializeCheckedRules()
  // 加载已应用修复的文件列表（用于导出下拉）
  loadFixedFiles()
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
    ensureSelectedNode()
  } else {
    treeData.value = []
    selectedNode.value = null
  }
  // 当开关变化时，重新初始化规则复选框状态
  if (filteredRules.value.length > 0) {
    initializeCheckedRules()
  }
})

// 监听规则复选框变化，重建代码树（更新问题数量）
watch(checkedRulesSet, () => {
  if (allFiles.value.length > 0) {
    console.log('[代码树] 规则复选框变化，重建代码树，当前选中规则数:', checkedRulesSet.value.size)
    treeData.value = buildTreeData(allFiles.value)
    ensureSelectedNode()
  }
})

watch(
  () => markedFilesSet.value,
  () => {
    if (allFiles.value.length === 0) {
      return
    }
    // 仅刷新节点标记标签，不改变当前过滤状态
    const preferred = selectedNode.value
      ? [{ name: selectedNode.value.name, file_path: selectedNode.value.file_path }]
      : []
    treeData.value = buildTreeData(allFiles.value)
    ensureSelectedNode(preferred)
  }
)

// 加载代码视图数据（普通模式直接读codemap，工具模式并行加载GJB和CWE）
async function loadCodeViewData() {
  try {
    loading.value = true
    error.value = ''
    markedFilesSet.value = new Set()
    markedFileProblemMap.value = {}
    previousSelectedNode.value = null

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

    console.log('[代码视图] 开始并行加载GJB和CWE数据:', taskId.value)
    const [gjbRes, cweRes] = await Promise.all([
      axios.get(`/api/staticAnalysis/filter/code-view/${taskId.value}`, {
        params: { rule_type: 'gjb' }
      }).catch(err => {
        console.warn('[代码视图] GJB数据加载失败:', err)
        return { data: { success: false, data: { files: [], problems: [] } } }
      }),
      axios.get(`/api/staticAnalysis/filter/code-view/${taskId.value}`, {
        params: { rule_type: 'cwe' }
      }).catch(err => {
        console.warn('[代码视图] CWE数据加载失败:', err)
        return { data: { success: false, data: { files: [], problems: [] } } }
      })
    ])
    const gjbData = gjbRes.data.success ? gjbRes.data.data : { files: [], problems: [], selected_rules: [] }
    const cweData = cweRes.data.success ? cweRes.data.data : { files: [], problems: [], selected_rules: [] }
    
    const allSelectedRules = [
      ...(gjbData.selected_rules || []),
      ...(cweData.selected_rules || [])
    ]
    selectedRulesSet.value = new Set(allSelectedRules)
    console.log('[代码视图] 用户勾选的规则数量:', selectedRulesSet.value.size)
    
    allFiles.value = dedupeFiles([...(gjbData.files || []), ...(cweData.files || [])])
    allProblems.value = [
      ...(gjbData.problems || []).map(p => ({ ...p, rule_type: p.rule_type || 'gjb' })),
      ...(cweData.problems || []).map(p => ({ ...p, rule_type: p.rule_type || 'cwe' }))
    ]
    allRules.value = [
      ...(gjbData.rules || []),
      ...(cweData.rules || [])
    ]
    
    console.log('[代码视图] 合并后数据:', {
      文件数: allFiles.value.length,
      总问题数: allProblems.value.length,
      规则数: allRules.value.length,
      GJB规则数: (gjbData.rules || []).length,
      CWE规则数: (cweData.rules || []).length,
      当前视图类型: ruleType.value
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
  } catch (err) {
    console.error('[代码视图] 加载数据失败:', err)
    error.value = '加载代码视图数据失败: ' + (err.response?.data?.detail || err.message)
    ElMessage.error(error.value)
  } finally {
    loading.value = false
  }
}

function handleNodeClick(node) {
  if (!node) {
    return
  }
  previousSelectedNode.value = createDescriptorFromNode(node)
  selectedNode.value = node
  highlightedProblem.value = null
  markProblemsAsViewedForNode(node)
}

function handleHighlightProblem(payload) {
  if (!payload || !payload.problem) {
    highlightedProblem.value = null
    return
  }

  const { problem, nodeInfo } = payload

  let targetNode = null
  if (nodeInfo) {
    targetNode = findNodeByFileInfo(nodeInfo.name, nodeInfo.file_path)
  }
  if (!targetNode) {
    targetNode = findNodeByProblem(problem)
  }

  if (targetNode) {
    previousSelectedNode.value = createDescriptorFromNode(targetNode)
    selectedNode.value = targetNode
  }

  highlightedProblem.value = {
    ...payload,
    nodeInfo: targetNode || nodeInfo || null
  }
}

async function handleViewMarkedProblems() {
  if (markedViewLoading.value) {
    return
  }
  if (!taskId.value) {
    ElMessage.warning('当前任务ID不存在，无法查看已标记问题')
    return
  }

  // 根据当前路由类型确定要获取哪个规则类型的已标记问题
  const ruleTypesToFetch = []
  const currentRuleType = ruleType.value
  if (currentRuleType === 'mixed') {
    ruleTypesToFetch.push('gjb', 'cwe')
  } else {
    ruleTypesToFetch.push(currentRuleType)
  }

  markedViewLoading.value = true
  try {
    for (let i = 0; i < ruleTypesToFetch.length; i++) {
      await refreshMarkedFiles(ruleTypesToFetch[i], {
        preserveView: true,
        merge: i > 0
      })
    }

    treeData.value = buildTreeData(allFiles.value)
    ensureSelectedNode()

    if (markedFilesSet.value.size === 0) {
      ElMessage.info('暂无已标记问题')
    } else {
      ElMessage.success('已更新已标记问题标记')
    }
  } catch (error) {
    console.error('[代码视图] 查看已标记问题失败:', error)
    ElMessage.error('获取已标记问题失败')
  } finally {
    markedViewLoading.value = false
  }
}

async function refreshMarkedFiles(ruleTypeToFetch, options = {}) {
  const { showToast = false, preserveView = true, merge = false } = options
  if (!taskId.value || !ruleTypeToFetch) {
    return
  }

  try {
    const response = await axios.get(
      `/api/staticAnalysis/filter/${taskId.value}/marked-problems/files`,
      { params: { rule_type: ruleTypeToFetch } }
    )

    if (response.data?.success) {
      updateMarkedFileMetadata(response.data.data || {}, merge)

      if (preserveView) {
        const preferred = selectedNode.value ? [createDescriptorFromNode(selectedNode.value)] : []
        treeData.value = buildTreeData(allFiles.value)
        ensureSelectedNode(preferred)
      }

      if (showToast) {
        const fileCount = response.data.data?.files?.length || 0
        ElMessage.success(`已刷新标记信息（${fileCount} 个文件）`)
      }
    }
  } catch (error) {
    console.error('[代码视图] 刷新标记信息失败:', error)
    if (showToast) {
      ElMessage.error('刷新标记信息失败')
    }
  }
}

function updateMarkedFileMetadata(info, merge = false) {
  const newSet = merge ? new Set(markedFilesSet.value) : new Set()
  const newMap = merge ? { ...markedFileProblemMap.value } : {}

  const addKey = (rawKey, countValue = 1) => {
    if (!rawKey) return
    const normalized = normalizeFileKey(rawKey)
    if (!normalized) return
    newSet.add(normalized)
    if (merge) {
      newMap[normalized] = (newMap[normalized] ?? 0) + countValue
    } else {
      newMap[normalized] = Math.max(newMap[normalized] ?? 0, countValue)
    }
  }

  const fileProblems = info?.file_problems || {}
  Object.entries(fileProblems).forEach(([key, count]) => {
    if (!key) return
    const value = Math.max(Number(count) || 0, 1)
    addKey(key, value)
    const base = key.split(/[/\\]/).pop()
    if (base && base !== key) {
      addKey(base, value)
    }
  })

  const files = info?.files || []
  files.forEach(fileStr => {
    if (!fileStr) return
    addKey(fileStr, 1)
    const base = fileStr.split(/[/\\]/).pop()
    if (base && base !== fileStr) {
      addKey(base, 1)
    }
  })

  markedFilesSet.value = newSet
  markedFileProblemMap.value = newMap
}

function normalizeFileKey(value) {
  if (!value) return ''
  return String(value).replace(/\\/g, '/').toLowerCase()
}

function assembleFileKeys(fileLike) {
  if (!fileLike) return []
  const keys = new Set()
  const name = fileLike.file_name || fileLike.name || ''
  const path = fileLike.file_path || ''

  if (name) {
    keys.add(name)
  }
  if (path) {
    keys.add(path)
    const baseFromPath = path.split(/[/\\]/).pop()
    if (baseFromPath) {
      keys.add(baseFromPath)
    }
  }
  if (name && (name.includes('/') || name.includes('\\'))) {
    const baseFromName = name.split(/[/\\]/).pop()
    if (baseFromName) {
      keys.add(baseFromName)
    }
  }
  return Array.from(keys)
}

function getMarkedProblemCountForFile(fileLike) {
  const candidates = assembleFileKeys(fileLike)
  let maxCount = 0
  for (const candidate of candidates) {
    const normalized = normalizeFileKey(candidate)
    const count = markedFileProblemMap.value[normalized]
    if (count && count > maxCount) {
      maxCount = count
    }
  }
  return maxCount
}

function findNodeByFileInfo(name, path) {
  if (!treeData.value || treeData.value.length === 0) {
    return null
  }
  const targetKeys = assembleFileKeys({ name, file_path: path })
  if (targetKeys.length === 0) {
    return null
  }
  const normalizedTargets = targetKeys.map(normalizeFileKey)
  return (
    treeData.value.find(node => {
      const nodeKeys = assembleFileKeys(node)
      return nodeKeys.some(key => normalizedTargets.includes(normalizeFileKey(key)))
    }) || null
  )
}

function findNodeByProblem(problem) {
  if (!problem) {
    return null
  }
  const issueFile = problem.issue_file || ''
  const descriptor = {
    name: issueFile,
    file_path: issueFile
  }
  return findNodeByFileInfo(descriptor.name, descriptor.file_path)
}

function ensureSelectedNode(preferredTargets = []) {
  if (!treeData.value || treeData.value.length === 0) {
    selectedNode.value = null
    return
  }

  const descriptors = []

  if (selectedNode.value) {
    descriptors.push(createDescriptorFromNode(selectedNode.value))
  }

  preferredTargets.forEach(target => {
    if (target && (target.name || target.file_path)) {
      descriptors.push(target)
    }
  })

  for (const descriptor of descriptors) {
    if (!descriptor) continue
    const match = findNodeByFileInfo(descriptor.name, descriptor.file_path)
    if (match) {
      selectedNode.value = match
      return
    }
  }

  const fallback = treeData.value.find(node => node.isMarked) || treeData.value[0]
  selectedNode.value = fallback
}

function createDescriptorFromNode(node) {
  if (!node) return null
  return {
    name: node.file_name || node.name || '',
    file_path: node.file_path || ''
  }
}

async function markProblemsAsViewedForNode(node) {
  if (!node || !taskId.value) {
    return
  }

  const ids = getNewProblemIdsForNode(node)
  if (ids.length === 0) {
    return
  }

  try {
    await axios.patch(`/api/staticAnalysis/filter/${taskId.value}/problems/status`, {
      problem_ids: ids,
      status: 2
    })

    allProblems.value = allProblems.value.map(problem => {
      if (ids.includes(problem.id)) {
        return { ...problem, problem_status: 2 }
      }
      return problem
    })

    node.problems = node.problems.map(problem => {
      if (ids.includes(problem.id)) {
        return { ...problem, problem_status: 2 }
      }
      return problem
    })

    treeData.value = buildTreeData(allFiles.value)
  } catch (error) {
    console.warn('[代码视图] 自动更新问题状态失败:', error)
  }
}

async function handleProblemStatusChanged() {
  treeData.value = buildTreeData(allFiles.value)
  ensureSelectedNode()

  // 根据当前路由类型确定要刷新哪个规则类型的已标记问题
  const typesToRefresh = []
  const currentRuleType = ruleType.value
  if (currentRuleType === 'mixed') {
    typesToRefresh.push('gjb', 'cwe')
  } else {
    typesToRefresh.push(currentRuleType)
  }

  for (let i = 0; i < typesToRefresh.length; i++) {
    await refreshMarkedFiles(typesToRefresh[i], { preserveView: true, merge: i > 0 })
  }

  treeData.value = buildTreeData(allFiles.value)
  ensureSelectedNode()
}

// 启动进度轮询
function startProgressPolling() {
  // 立即检查一次
  checkProgress()
  
  // 每5秒轮询一次
  progressPollInterval = setInterval(() => {
    checkProgress()
  }, 5000)
}

// 检查进度
async function checkProgress() {
  try {
    console.log('[代码视图] 检查进度, taskId:', taskId.value)
    const response = await axios.get(`/api/staticAnalysis/filter/status/${taskId.value}/detailed`)
    
    console.log('[代码视图] 进度API响应:', response.data)
    
    if (response.data && response.data.success) {
      updateProgressDisplay(response.data)
    } else {
      console.warn('[代码视图] 进度API返回失败:', response.data)
    }
  } catch (error) {
    console.error('[代码视图] 获取进度失败:', error)
  }
}

// 更新进度显示
function updateProgressDisplay(statusData) {
  console.log('[代码视图] 更新进度显示:', statusData)
  
  let hasActiveTask = false // 标记是否有正在进行的任务
  
  // 更新GJB进度
  if (statusData.gjb) {
    const gjb = statusData.gjb
    const gjbStatus = gjb.status
    console.log('[代码视图] GJB状态:', gjbStatus, '完整数据:', gjb)
    
    if (gjbStatus === 'completed') {
      gjbProgressData.value = {
        percentage: 100,
        status: 'success',
        statusText: '✅ 过滤完成',
        current: gjb.ai_analyzed_issues || 0,
        total: gjb.total_issues || 0
      }
    } else if (gjbStatus === 'processing' || gjbStatus === 'ai_analyzing') {
      // processing 是静态分析的状态，ai_analyzing 是函数审查的状态
      // 使用后端已经计算好的 progress 字段，或者用 ai_processed_issues / ai_processing_total
      const percentage = gjb.progress ?? 
        (gjb.ai_processing_total > 0 
          ? Math.round((gjb.ai_processed_issues / gjb.ai_processing_total) * 100) 
          : 0)
      
      gjbProgressData.value = {
        percentage,
        status: '',
        statusText: '🔄 AI智能分析中...',
        current: gjb.ai_processed_issues || 0,
        total: gjb.ai_processing_total || gjb.uncertain_issues || 0
      }
      hasActiveTask = true
    } else if (gjbStatus === 'filtering') {
      gjbProgressData.value = {
        percentage: 30,
        status: '',
        statusText: '🔍 关键词过滤中...',
        current: 0,
        total: gjb.total_issues || 0
      }
      hasActiveTask = true
    } else if (gjbStatus === 'pending' || gjbStatus === 'uploading') {
      gjbProgressData.value = {
        percentage: 10,
        status: '',
        statusText: '⏳ 准备中...',
        current: 0,
        total: 0
      }
      hasActiveTask = true
    }
  }
  
  // 更新CWE进度
  if (statusData.cwe) {
    const cwe = statusData.cwe
    const cweStatus = cwe.status
    console.log('[代码视图] CWE状态:', cweStatus, '完整数据:', cwe)
    
    if (cweStatus === 'completed') {
      cweProgressData.value = {
        percentage: 100,
        status: 'success',
        statusText: '✅ 过滤完成',
        current: cwe.ai_analyzed_issues || 0,
        total: cwe.total_issues || 0
      }
    } else if (cweStatus === 'processing' || cweStatus === 'ai_analyzing') {
      // processing 是静态分析的状态，ai_analyzing 是函数审查的状态
      // 使用后端已经计算好的 progress 字段，或者用 ai_processed_issues / ai_processing_total
      const percentage = cwe.progress ?? 
        (cwe.ai_processing_total > 0 
          ? Math.round((cwe.ai_processed_issues / cwe.ai_processing_total) * 100) 
          : 0)
      
      cweProgressData.value = {
        percentage,
        status: '',
        statusText: '🔄 AI智能分析中...',
        current: cwe.ai_processed_issues || 0,
        total: cwe.ai_processing_total || cwe.uncertain_issues || 0
      }
      hasActiveTask = true
    } else if (cweStatus === 'filtering') {
      cweProgressData.value = {
        percentage: 30,
        status: '',
        statusText: '🔍 关键词过滤中...',
        current: 0,
        total: cwe.total_issues || 0
      }
      hasActiveTask = true
    } else if (cweStatus === 'pending' || cweStatus === 'uploading') {
      cweProgressData.value = {
        percentage: 10,
        status: '',
        statusText: '⏳ 准备中...',
        current: 0,
        total: 0
      }
      hasActiveTask = true
    }
  }
  
  console.log('[代码视图] hasActiveTask:', hasActiveTask, 'showProgress.value:', showProgress.value)
  
  // 检查是否有任何任务数据（有total就说明有数据）
  const hasAnyTaskData = (gjbProgressData.value.total > 0) || (cweProgressData.value.total > 0)
  
  // 在代码视图中，只要有任务数据就显示进度框（无论是否完成）
  if (hasAnyTaskData) {
    showProgress.value = true
    console.log('[代码视图] 有任务数据，显示进度组件')
  }
  
  // 如果两个都完成了（状态都是completed），停止轮询
  const gjbCompleted = statusData.gjb?.status === 'completed'
  const cweCompleted = statusData.cwe?.status === 'completed'
  
  if (gjbCompleted && cweCompleted) {
    console.log('[代码视图] 两个任务都已完成，停止轮询')
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
    if (!file) return
    const key = file.file_path || file.file_name
    if (!key) return
    if (fileMap.has(key)) {
      const existing = fileMap.get(key)
      fileMap.set(key, {
        ...existing,
        ...file,
        source_code: file.source_code || existing.source_code
      })
    } else {
      fileMap.set(key, { ...file })
    }
  })
  return Array.from(fileMap.values())
}

function buildTreeData(files) {
  const sourceFiles = files

  const treeNodes = sourceFiles.map((file, index) => {
    const fileProblems = filteredProblems.value.filter(p => {
      if (p.issue_file === file.file_name) return true
      if (p.issue_file === file.file_path) return true
      if (p.issue_file && p.issue_file.endsWith(file.file_name)) return true

      const issueFileBasename = p.issue_file ? p.issue_file.split(/[/\\]/).pop() : ''
      if (issueFileBasename === file.file_name) return true

      return false
    })

    const storedMarkedCount = getMarkedProblemCountForFile(file)
    const problemMarkedCount = fileProblems.filter(p => p.problem_status === 4).length
    const markedCount = Math.max(storedMarkedCount, problemMarkedCount)

    const node = {
      id: file.file_path || file.file_name || `file_${index}`,
      name: file.file_name,
      type: 'file',
      file_path: file.file_path,
      source_code: file.source_code,
      problems: fileProblems,
      problemCount: fileProblems.length,
      markedProblemCount: markedCount,
      isMarked: markedCount > 0
    }

    return node
  })

  console.log('[代码树] 构建完成，节点数:', treeNodes.length)

  return treeNodes
}

function isFileInMarkedSet(file) {
  if (!file) return false
  const candidates = assembleFileKeys(file)
  for (const candidate of candidates) {
    if (!candidate) continue
    const normalized = normalizeFileKey(candidate)
    if (markedFilesSet.value.has(normalized)) {
      return true
    }
  }
  return false
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
    const currentRuleType = ruleType.value
    
    console.log('[代码视图] 下载完整问题单:', { taskId: taskId.value, ruleType: currentRuleType })
    
    // 直接使用taskId（后端支持数字ID和UUID两种格式）
    const generateResponse = await staticAnalysisFilterService.generateOutputFile(
      taskId.value,
      currentRuleType,
      'all',
      false,
      true,
      true
    )
    
    if (!generateResponse.success) {
      throw new Error(generateResponse.error || '生成文件失败')
    }
    
    // 使用后端返回的真实session_id构建下载URL
    const sessionIdForDownload = generateResponse.session_id || taskId.value
    const downloadUrl = staticAnalysisFilterService.getDownloadUrl(sessionIdForDownload, generateResponse.filename)
    
    // 创建下载链接
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = `${currentRuleType.toUpperCase()}完整问题单_${generateResponse.filename}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    ElMessage.success(`${currentRuleType.toUpperCase()}完整问题单下载成功（四个Sheet，含AI确认高亮）`)
  } catch (error) {
    console.error('[代码视图] 下载失败:', error)
    ElMessage.error('下载失败: ' + error.message)
  }
}

// ========== [NEW] 自动修复：入口与导出 ==========

// 单问题修复入口
function handleRequestFix(payload) {
  fixProblem.value = payload?.problem || null
  if (!fixProblem.value) return
  fixDialogVisible.value = true
}

// 批量修复入口（文件级 / 规则级）
function handleRequestBatchFix(payload) {
  if (!payload) return
  batchScope.value = {
    type: payload.type,
    value: payload.value,
    label: payload.label || ''
  }

  let candidates = payload.candidates || []
  if (!candidates.length && payload.type === 'rule') {
    // 规则级：从全量问题中筛出该规则的问题
    candidates = allProblems.value.filter(p => p.rule_code === payload.value)
  }
  if (!candidates.length && payload.type === 'file') {
    const target = payload.value
    candidates = allProblems.value.filter(p => {
      if (!p.issue_file) return false
      const issueFile = String(p.issue_file).replace(/\\/g, '/')
      const value = String(target || '').replace(/\\/g, '/')
      return issueFile === value || issueFile.endsWith(value) || issueFile.split('/').pop() === value.split('/').pop()
    })
  }

  if (!candidates.length) {
    ElMessage.warning('该范围内没有问题可修复')
    return
  }
  batchCandidates.value = candidates
  batchPanelVisible.value = true
}

// 修复应用后：刷新代码库数据 + 更新变更行高亮
async function handleFixApplied(payload) {
  if (payload?.applied?.length) {
    const map = { ...fixedLinesByFile.value }
    payload.applied.forEach(entry => {
      if (!entry?.file_path) return
      const key = entry.file_path
      const set = new Set(map[key] || [])
      ;(entry.applied_lines || []).forEach(line => set.add(line))
      map[key] = Array.from(set).sort((a, b) => a - b)
    })
    fixedLinesByFile.value = map
  }
  if (payload?.rolledBack) {
    // 回滚时无法精确知道行号，清空该文件的变更行高亮
    const node = selectedNode.value
    if (node) {
      const map = { ...fixedLinesByFile.value }
      delete map[node.file_path]
      delete map[node.name]
      fixedLinesByFile.value = map
    }
  }
  await reloadAfterFix()
}

// 重新拉取代码视图数据（源码已变更）
async function reloadAfterFix() {
  try {
    const [gjbRes, cweRes] = await Promise.all([
      axios.get(`/api/staticAnalysis/filter/code-view/${taskId.value}`, { params: { rule_type: 'gjb' } })
        .catch(() => ({ data: { success: false, data: { files: [], problems: [] } } })),
      axios.get(`/api/staticAnalysis/filter/code-view/${taskId.value}`, { params: { rule_type: 'cwe' } })
        .catch(() => ({ data: { success: false, data: { files: [], problems: [] } } }))
    ])
    const gjbData = gjbRes.data.success ? gjbRes.data.data : { files: [], problems: [] }
    const cweData = cweRes.data.success ? cweRes.data.data : { files: [], problems: [] }

    allFiles.value = dedupeFiles([...(gjbData.files || []), ...(cweData.files || [])])
    allProblems.value = [
      ...(gjbData.problems || []).map(p => ({ ...p, rule_type: p.rule_type || 'gjb' })),
      ...(cweData.problems || []).map(p => ({ ...p, rule_type: p.rule_type || 'cwe' }))
    ]
    treeData.value = buildTreeData(allFiles.value)
    ensureSelectedNode()
    await loadFixedFiles()
  } catch (error) {
    console.error('[代码视图] 修复后刷新失败:', error)
  }
}

async function loadFixedFiles() {
  try {
    const res = await staticAnalysisFixService.getFixedFiles(taskId.value)
    if (res?.success) {
      fixedFiles.value = res.data?.files || []
    }
  } catch (error) {
    // 无代码库 / 尚无修复时不打扰用户
    fixedFiles.value = []
  }
}

// 导出修复结果（两种模式）
async function handleExportCommand(command) {
  if (exporting.value) return
  exporting.value = true
  try {
    if (command === 'current') {
      const node = selectedNode.value
      if (!node) {
        ElMessage.warning('请先在代码树中选择一个文件')
        return
      }
      const filePath = node.file_path || node.name
      const res = await staticAnalysisFixService.exportCurrentFile(taskId.value, filePath)
      ElMessage.success(`已导出文件 ${res.filename}`)
    } else if (command === 'package') {
      const res = await staticAnalysisFixService.exportPackage(taskId.value)
      ElMessage.success(`已导出代码包 ${res.filename}`)
    }
  } catch (error) {
    ElMessage.error(error.message || '导出失败')
  } finally {
    exporting.value = false
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

/* 防止进度条元素意外渲染到代码视图主容器中 */
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
  align-items: center;
}

.export-count {
  margin-left: 6px;
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

