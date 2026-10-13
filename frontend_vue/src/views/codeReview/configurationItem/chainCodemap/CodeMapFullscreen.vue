<template>
  <div class="chain-codemap-fullscreen">
    <!-- 四栏布局 -->
    <div class="four-column-layout">
      <!-- 第一栏：功能模块列表（树形结构） -->
      <div class="feature-list-column" :style="columnStyle(featureListWidth)">
        <div class="column-header">
          <h3>功能模块列表</h3>
          <span class="feature-count">{{ totalFeatureCount }} 个功能</span>
        </div>
        <div class="feature-list-content">
          <el-tree
            ref="featureTreeRef"
            v-if="features.length > 0"
            :data="features"
            :props="{ label: 'name', children: 'sub_features' }"
            node-key="id"
            :highlight-current="true"
            :current-node-key="selectedFeature?.id"
            :indent="20"
            default-expand-all
            @node-click="selectFeatureNode"
            :expand-on-click-node="false"
          >
            <template #default="{ node, data }">
              <div class="feature-tree-node">
                <span class="feature-name">{{ data.section && data.name !== data.section ? data.section + ' ' + data.name : (data.section || data.name) }}</span>
                <!-- 只有叶子节点（无子章节）才显示问题数 -->
                <div v-if="!data.sub_features || data.sub_features.length === 0" class="feature-status-badges">
                  <span class="status-badge status-badge-unfiltered" :title="`未过滤问题: ${getFeatureProblemStats(data).unfiltered}`">
                    {{ getFeatureProblemStats(data).unfiltered }}
                  </span>
                  <span class="status-badge status-badge-filtered" :title="`已过滤问题: ${getFeatureProblemStats(data).filtered}`">
                    {{ getFeatureProblemStats(data).filtered }}
                  </span>
                  <span class="status-badge status-badge-marked" :title="`已标记问题: ${getFeatureProblemStats(data).marked}`">
                    {{ getFeatureProblemStats(data).marked }}
                  </span>
                </div>
              </div>
            </template>
          </el-tree>
          
          <div v-if="features.length === 0" class="empty-features">
            <i class="el-icon-info"></i>
            <p>暂无功能模块</p>
          </div>
        </div>
      </div>

      <!-- 拖拽分界线1 -->
      <div class="resize-handle" @mousedown="startResize(1, $event)"></div>

      <!-- 第二栏：代码目录树 -->
      <div class="directory-tree-column" :style="columnStyle(treeWidth)">
      <div class="column-header">
          <h3>代码目录树</h3>
        <span class="hint-text" v-if="selectedFeature">链路顺序：{{ currentChainOrderText }}</span>
      </div>
        <div class="tree-content">
          <el-tabs v-model="secondColumnTab" class="second-column-tabs" @tab-change="handleSecondColumnTabChange">
            <el-tab-pane label="目录" name="tree">
              <div class="vscode-tree-wrapper">
              <el-tree
                ref="directoryTree"
                  :data="filteredDirectoryTreeData"
                :props="{ label: 'label', children: 'children' }"
                node-key="id"
                @node-click="handleTreeNodeClick"
                default-expand-all
                :expand-on-click-node="false"
                  :indent="12"
                  class="vscode-tree"
              >
                <template #default="{ node, data }">
                    <div class="vscode-tree-node" :class="{ 'is-directory': data.type === 'directory', 'is-file': data.type === 'file', 'is-function': data.type === 'function' }">
                      <!-- 目录图标 -->
                      <span v-if="data.type === 'directory'" class="vscode-icon vscode-icon-folder">
                        <svg v-if="node.expanded" width="16" height="16" viewBox="0 0 16 16" fill="none">
                          <path d="M1 3.5A1.5 1.5 0 012.5 2H6l1 1.5H13.5A1.5 1.5 0 0115 5v7a1.5 1.5 0 01-1.5 1.5h-11A1.5 1.5 0 011 12V3.5z" fill="#DCAD78"/>
                        </svg>
                        <svg v-else width="16" height="16" viewBox="0 0 16 16" fill="none">
                          <path d="M1 3.5A1.5 1.5 0 012.5 2H6l1 1.5H13.5A1.5 1.5 0 0115 5v7a1.5 1.5 0 01-1.5 1.5h-11A1.5 1.5 0 011 12V3.5z" fill="#E8C07D" opacity="0.85"/>
                        </svg>
                    </span>
                      <!-- 函数图标 -->
                      <span v-else-if="data.type === 'function'" class="vscode-icon vscode-icon-function">
                        <span style="color:#4ec9b0;font-size:13px;font-family:'Consolas',monospace;font-weight:bold;">ƒ</span>
                    </span>
                      <!-- 文件图标 -->
                      <span v-else class="vscode-icon vscode-icon-file" :class="getVscodeFileIconClass(data.label)">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                          <path d="M4 1h5.5L13 4.5V15H4V1z" :fill="getFileIconColor(data.label)" opacity="0.9"/>
                          <path d="M9 1l4 4H9V1z" :fill="getFileIconColor(data.label)" opacity="0.5"/>
                        </svg>
                    </span>
                      <span class="vscode-node-label">{{ data.label }}</span>
                      <span v-if="data.chainOrder" class="vscode-chain-badge">{{ data.chainOrder }}</span>
                      <span v-if="data.problemCount && data.problemCount > 0" class="vscode-problem-badge">{{ data.problemCount }}</span>
                  </div>
                </template>
              </el-tree>
              </div>

              <!-- 函数列表面板（点击文件时弹出） -->
              <div v-if="showFunctionList" class="function-list-panel">
                <div class="function-list-header">
                  <span class="function-list-title">{{ selectedFileName }}</span>
                  <button class="close-btn" @click="showFunctionList = false">✕</button>
                </div>
                <div class="function-list-items">
                  <div 
                    v-for="func in currentFileFunctions"
                    :key="func.name"
                    class="function-item"
                    @click="selectFunction(func)"
                  >
                    <span class="func-icon">ƒ</span>
                    <span class="function-name">{{ func.name }}</span>
                    <span v-if="func.chainOrder" class="vscode-chain-badge">{{ func.chainOrder }}</span>
                  </div>
                </div>
              </div>
            </el-tab-pane>

            <el-tab-pane label="调用关系" name="graph">
              <div class="callgraph-panel">
                <div class="callgraph-toolbar">
                  <el-button v-if="callGraphViewMode === 'function'" size="small" @click="backToFileGraph">返回文件图</el-button>
                  <span v-if="callGraphViewMode === 'function'" class="callgraph-title">{{ selectedGraphFile?.name }}</span>
                </div>
                <div class="callgraph-content">
                  <CodeMapGraph
                    v-if="callGraphNodes.length > 0"
                    :nodes="callGraphNodes"
                    :edges="callGraphEdges"
                    @nodeSelected="handleGraphNodeSelected"
                    @nodeDeselected="handleGraphNodeDeselected"
                  />
                  <div v-else class="empty-callgraph">
                    <p>{{ selectedFeature ? '暂无调用关系数据' : '请选择功能模块后查看调用关系' }}</p>
                  </div>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>

      <!-- 拖拽分界线2 -->
      <div class="resize-handle" @mousedown="startResize(2, $event)"></div>

      <!-- 第三栏：源代码显示 -->
      <div class="source-code-column">
        <CodeMapSourceView
          :selected-node="sourceViewNode"
          :code-map-data="null"
          :highlighted-problem="highlightedProblem"
          :task-id="taskId"
        />
        </div>
        
      <!-- 拖拽分界线3 -->
      <div class="resize-handle" @mousedown="startResize(3, $event)"></div>

      <!-- 第四栏：功能介绍 + 问题列表 -->
      <div class="info-problem-column" :style="columnStyle(infoProblemWidth)">
        <!-- 上半部分：功能介绍 -->
        <div class="feature-info-section" :style="{ height: featureInfoHeight + 'px' }">
          <div class="feature-info-content">
            <div v-if="selectedFeature" class="feature-overview">
              <p class="overview-text">{{ featureDescription || '暂无功能描述（审查完成后自动生成）' }}</p>
            </div>
            <div v-else class="empty-info">
              <p>请在左侧选择功能模块</p>
            </div>
          </div>
      </div>

        <!-- 垂直拖拽分界线 -->
        <div class="vertical-resize-handle" @mousedown="startVerticalResize"></div>

        <!-- 下半部分：问题列表 -->
        <div class="problem-list-section">
          <div class="section-header">
            <h3>问题列表</h3>
            <div class="problem-list-header-actions" v-if="selectedFeature">
              <span class="problem-count">{{ featureProblems.length }} 个问题</span>
              <el-button type="primary" size="small" text @click="openFilterPanel">
                过滤设置
              </el-button>
            </div>
      </div>
          <div class="problem-list-content">
            <div v-if="featureProblems.length === 0" class="empty-problems">
              <i class="el-icon-circle-check"></i>
              <p>{{ selectedFeature ? '未发现问题' : '请选择功能模块' }}</p>
            </div>

            <div v-else class="problems-list">
            <div 
              v-for="(problem, index) in featureProblems"
                :key="problem.id || index"
                class="problem-block"
                :class="getProblemStatusClass(problem)"
              >
                <div class="problem-title" @click="handleProblemClick(problem, index)">
                  <div class="problem-title-left">
                    <div class="problem-status-indicator" :class="getProblemStatusIndicatorClass(problem)"></div>
                    <span>问题 {{ index + 1 }}</span>
                    <el-tag
                      v-if="getProblemStatusLabel(problem)"
                      :type="getProblemStatusTagType(problem)"
                      size="small"
                      class="status-tag"
                    >
                      {{ getProblemStatusLabel(problem) }}
                    </el-tag>
                    <el-tag
                      v-if="problem.issue_level"
                      :type="getIssueLevelTagType(problem.issue_level)"
                      size="small"
                      class="problem-level-tag"
                    >
                      {{ problem.issue_level }}
                    </el-tag>
              </div>
                  <div class="problem-title-right">
                    <el-button
                      :type="isProblemMarked(problem) ? 'success' : 'info'"
                      size="small"
                      text
                      @click.stop="toggleProblemMark(problem)"
                      :title="isProblemMarked(problem) ? '取消标记' : '标记问题'"
                    >
                      {{ isProblemMarked(problem) ? '已标记' : '标记' }}
                    </el-button>
                    <el-button type="primary" size="small" text @click.stop="locateProblem(problem)">
                      定位
                    </el-button>
                    <span class="collapse-icon" :class="{ collapsed: collapsedProblems.has(index) }">⌄</span>
              </div>
            </div>

                <el-collapse-transition>
                  <div v-show="!collapsedProblems.has(index)" class="problem-content">
                    <div v-if="problem.problem_reason" class="problem-field">
                      <div class="field-label">问题原因</div>
                      <div class="field-value">{{ problem.problem_reason }}</div>
          </div>

                    <div v-if="problem.issue_name" class="problem-field">
                      <div class="field-label">问题名称</div>
                      <div class="field-value">{{ problem.issue_name }}</div>
        </div>

                    <div v-if="problem.issue_location" class="problem-field">
                      <div class="field-label">问题位置</div>
                      <div class="field-value">{{ problem.issue_location }}</div>
                    </div>

                    <div v-if="problem.description_requirement" class="problem-field">
                      <div class="field-label">需求描述</div>
                      <div class="field-value">{{ problem.description_requirement }}</div>
                    </div>

                    <div v-if="problem.description_issue" class="problem-field">
                      <div class="field-label">问题描述</div>
                      <div class="field-value">{{ problem.description_issue }}</div>
                    </div>

                    <div v-if="problem.description_location" class="problem-field">
                      <div class="field-label">位置描述</div>
                      <div class="field-value location-description">
                        <div class="location-text">{{ formatLocationText(problem.description_location) }}</div>
                        <pre v-if="extractLocationSource(problem.description_location)" class="location-source-code"><code>{{ formatLocationSource(problem.description_location) }}</code></pre>
                      </div>
                    </div>

                    <div v-if="problem.description_impact" class="problem-field">
                      <div class="field-label">影响描述</div>
                      <div class="field-value">{{ problem.description_impact }}</div>
                    </div>

                    <div v-if="problem.affected_functions" class="problem-field">
                      <div class="field-label">涉及函数</div>
                      <div class="field-value">{{ problem.affected_functions }}</div>
                    </div>
                  </div>
                </el-collapse-transition>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 进度显示组件 -->
    <ProgressDisplay
      :task-id="taskId"
      :auto-start="true"
      review-type="chain"
      @progress-updated="handleProgressUpdated"
      @task-completed="handleTaskCompleted"
      @task-failed="handleTaskFailed"
    />

    <!-- 注释准确率反馈弹窗 -->
    <CommentAccuracyFeedback
      v-model:visible="showFeedbackDialog"
      :task-id="taskId"
      :clicked-count="feedbackStatus.clickedCount"
      :total-functions="feedbackStatus.totalFunctions"
      :trigger-point="feedbackTriggerPoint"
      :delayed-count="feedbackStatus.delayedCount"
      @submitted="handleFeedbackSubmitted"
      @delayed="handleFeedbackDelayed"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { buildProblemKey } from '../shared/problemMarking'
import ProgressDisplay from '../shared/ProgressDisplay.vue'
import CodeMapGraph from './CodeMapGraph.vue'
import CodeMapSourceView from './CodeMapSourceView.vue'
import CommentAccuracyFeedback from '../functionCodemap/CommentAccuracyFeedback.vue'

const route = useRoute()
const taskId = computed(() => Number(route.params.taskId))

// 功能列表
const features = ref([])
const selectedFeature = ref(null)

// 递归统计所有功能数量（包括子功能）
const totalFeatureCount = computed(() => {
  const countFeatures = (featureList) => {
    let count = 0
    for (const feature of featureList) {
      count += 1
      if (feature.sub_features && feature.sub_features.length > 0) {
        count += countFeatures(feature.sub_features)
      }
    }
    return count
  }
  return countFeatures(features.value)
})

// 统计叶子功能点数量（没有sub_features的节点）
const leafFeatureCount = computed(() => {
  const countLeaves = (featureList) => {
    let count = 0
    for (const feature of featureList) {
      if (!feature.sub_features || feature.sub_features.length === 0) {
        count += 1
      } else {
        count += countLeaves(feature.sub_features)
      }
    }
    return count
  }
  return countLeaves(features.value)
})

// 目录树
const directoryTreeData = ref([])
const directoryTree = ref(null)
const featureTreeRef = ref(null)
const projectInfo = ref(null)
const currentChainOrderLetters = ref([])

const currentChainOrderText = computed(() => {
  if (!selectedFeature.value) return ''
  if (!currentChainOrderLetters.value.length) return '（无可解析链路）'
  return currentChainOrderLetters.value.join(' → ')
})

// 第二栏 Tab
const secondColumnTab = ref('tree')

// 调用关系（两级加载）
const callGraphViewMode = ref('file') // file | function
const selectedGraphFile = ref(null)
const featureFileGraph = ref({ nodes: [], edges: [] })
const intraFileFunctionGraph = ref({ nodes: [], edges: [] })

const callGraphNodes = computed(() => {
  return callGraphViewMode.value === 'file' ? (featureFileGraph.value.nodes || []) : (intraFileFunctionGraph.value.nodes || [])
})

const callGraphEdges = computed(() => {
  return callGraphViewMode.value === 'file' ? (featureFileGraph.value.edges || []) : (intraFileFunctionGraph.value.edges || [])
})

// 函数列表面板
const showFunctionList = ref(false)
const selectedFileName = ref('')
const currentFileFunctions = ref([])

// 源代码
const currentSourceFile = ref('')
const currentSourceCode = ref('')
const highlightedProblem = ref(null)
const codeBlock = ref(null)

// 当前选中的源码节点（传给 CodeMapSourceView）
const sourceViewNode = computed(() => {
  if (!currentSourceCode.value) return null
  return {
    type: currentSelectedType.value || 'file',
    name: currentSelectedName.value || currentSourceFile.value,
    file_path: currentSourceFile.value,
    source_code: currentSourceCode.value,
    line: highlightedProblem.value?.problem?.line || highlightedProblem.value?.problem?.start_line || null,
    end_line: highlightedProblem.value?.problem?.end_line || null,
    description_location: highlightedProblem.value?.problem?.description_location || ''
  }
})
const currentSelectedType = ref('file')
const currentSelectedName = ref('')

// 问题列表
const featureProblems = ref([])
const featureDescription = ref('')  // 当前功能的AI生成描述
const markedProblemKeys = ref(new Set())
const collapsedProblems = ref(new Set())
const featureProblemStatsMap = ref({})
const filterRules = ref([])
const allFeatureProblemsMap = ref({})

// 列宽度（增大宽度，提升可读性）
const featureListWidth = ref(300)  // 从150增大到300
const treeWidth = ref(360)          // 从180增大到360
const infoProblemWidth = ref(400)   // 从200增大到400
const featureInfoHeight = ref(160)

const resizeLimits = {
  featureList: { min: 200, max: 500 },
  tree: { min: 250, max: 600 },
  infoProblem: { min: 300, max: 600 },
  sourceCode: { min: 200 }
}

function columnStyle(width) {
  return {
    width: `${width}px`,
    flex: `0 0 ${width}px`
  }
}

async function handleSecondColumnTabChange() {
  if (secondColumnTab.value === 'graph') {
    await loadFeatureFileCallGraph()
  }
}

async function loadFeatureFileCallGraph() {
  callGraphViewMode.value = 'file'
  selectedGraphFile.value = null
  intraFileFunctionGraph.value = { nodes: [], edges: [] }

  if (!selectedFeature.value?.id) {
    featureFileGraph.value = { nodes: [], edges: [] }
    return
  }

  try {
    const resp = await axios.get(`/api/codeReview/chain_callgraph/${taskId.value}/feature/${selectedFeature.value.id}/files`)
    const payload = resp.data?.data || resp.data || {}
    featureFileGraph.value = payload.graph || { nodes: [], edges: [] }
  } catch (e) {
    console.error('加载文件级调用关系失败:', e)
    featureFileGraph.value = { nodes: [], edges: [] }
    ElMessage.error('加载调用关系失败')
  }
}

async function loadIntraFileFunctionGraph(filePath) {
  if (!selectedFeature.value?.id || !filePath) return

  try {
    const resp = await axios.get(`/api/codeReview/chain_callgraph/${taskId.value}/feature/${selectedFeature.value.id}/file`, {
      params: { path: filePath }
    })
    const payload = resp.data?.data || resp.data || {}
    intraFileFunctionGraph.value = payload.graph || { nodes: [], edges: [] }
    selectedGraphFile.value = payload.file || { path: filePath, name: filePath }
    callGraphViewMode.value = 'function'
  } catch (e) {
    console.error('加载文件内函数调用关系失败:', e)
    ElMessage.error('加载文件内函数调用关系失败')
  }
}

function backToFileGraph() {
  callGraphViewMode.value = 'file'
  selectedGraphFile.value = null
  intraFileFunctionGraph.value = { nodes: [], edges: [] }
}

async function handleGraphNodeSelected(node) {
  if (callGraphViewMode.value === 'file' && node?.type === 'file') {
    await loadIntraFileFunctionGraph(node.path)
  }
}

function handleGraphNodeDeselected() {
  // no-op
}

// 拖拽状态
const isResizing = ref(false)
const resizeType = ref(0) // 1, 2, 3
const startX = ref(0)
const startY = ref(0)
const startWidth = ref(0)
const startHeight = ref(0)

// 递归复制功能树（包括子功能）
function copyFeatureWithSubFeatures(feature) {
  const copied = {
    id: feature.id,
    section: feature.section,
    name: feature.name,
    description: feature.description,
    call_chain: feature.call_chain,
    related_files: feature.related_files || [],
    related_functions: feature.related_functions || [],
    key_functions: feature.key_functions || [],
    issues_count: feature.issues_count || 0,
    problem_count: feature.issues_count || 0,
    sub_features: []
  }
  
  // 递归处理子功能
  if (feature.sub_features && feature.sub_features.length > 0) {
    copied.sub_features = feature.sub_features.map(subFeature => 
      copyFeatureWithSubFeatures(subFeature)
    )
  }
  
  return copied
}

// 加载功能列表
async function loadFeatures() {
  try {
    // 从渐进式发现API获取功能列表
    const response = await axios.get(`/api/codeReview/progressive/visualization/${taskId.value}`)
    
    if (response.data && response.data.features) {
      // 递归复制整个功能树，保留sub_features和issues_count
      features.value = response.data.features.map(f => copyFeatureWithSubFeatures(f))
      initializeFeatureProblemStats(features.value)
      await preloadFeatureProblemStats()
    }
  } catch (error) {
    console.error('加载功能列表失败:', error)
    ElMessage.error('加载功能列表失败')
  }
}

function flattenFeatures(featureList) {
  const result = []

  const walk = (items) => {
    items.forEach((item) => {
      result.push(item)
      if (item.sub_features && item.sub_features.length > 0) {
        walk(item.sub_features)
      }
    })
  }

  walk(featureList)
  return result
}

async function preloadFeatureProblemStats() {
  if (!features.value.length) return

  const allFeatures = flattenFeatures(features.value)

  await Promise.all(
    allFeatures.map(async (feature) => {
      try {
        const resp = await axios.get(`/api/codeReview/progressive/problems/${taskId.value}`, {
          params: { feature: feature.name }
        })

        const problems = (resp.data?.problems || []).map(mapChainProblem)
        const key = getFeatureStatsKey(feature)
        allFeatureProblemsMap.value[key] = problems
        updateFeatureStatsByProblems(feature, problems)
      } catch (error) {
        const key = getFeatureStatsKey(feature)
        const fallback = Number(feature.issues_count || feature.problem_count || 0)
        featureProblemStatsMap.value = {
          ...featureProblemStatsMap.value,
          [key]: {
            total: fallback,
            unfiltered: fallback,
            filtered: 0,
            marked: 0
          }
        }
      }
    })
  )
}

function updateFeatureStatsByProblems(feature, problems) {
  const total = problems.length
  let filtered = 0
  let marked = 0
  let unfiltered = 0

  problems.forEach((problem) => {
    const status = getProblemStatusForDisplay(problem)
    if (status === 4) {
      marked += 1
    } else if (status === 3) {
      filtered += 1
    } else {
      unfiltered += 1
    }
  })

  const key = getFeatureStatsKey(feature)
  featureProblemStatsMap.value = {
    ...featureProblemStatsMap.value,
    [key]: {
      total,
      unfiltered,
      filtered,
      marked
    }
  }
}

function refreshAllFeatureStatsFromCache() {
  const allFeatures = flattenFeatures(features.value)
  allFeatures.forEach((feature) => {
    const key = getFeatureStatsKey(feature)
    const problems = allFeatureProblemsMap.value[key] || []
    updateFeatureStatsByProblems(feature, problems)
  })
}

function initializeFeatureProblemStats(featureList) {
  const statsMap = {}

  const walk = (items) => {
    items.forEach((item) => {
      const key = getFeatureStatsKey(item)
      const total = Number(item.issues_count || item.problem_count || 0)
      statsMap[key] = {
        total,
        unfiltered: total,
        filtered: 0,
        marked: 0
      }

      if (item.sub_features && item.sub_features.length > 0) {
        walk(item.sub_features)
      }
    })
  }

  walk(featureList)
  featureProblemStatsMap.value = statsMap
}

function getFeatureStatsKey(feature) {
  return String(feature.id || feature.name || feature.section || '')
}

function getFeatureProblemStats(feature) {
  const key = getFeatureStatsKey(feature)
  return featureProblemStatsMap.value[key] || {
    total: Number(feature.issues_count || feature.problem_count || 0),
    unfiltered: Number(feature.issues_count || feature.problem_count || 0),
    filtered: 0,
    marked: 0
  }
}

async function loadMarkedProblems() {
  if (!taskId.value) return

  try {
    const response = await axios.get(`/api/codeReview/${taskId.value}/marked_problems`, {
      params: { analysis_type: 'chain' }
    })

    if (response.data.success) {
      const keys = response.data.data.map(item => item.problem_key)
      markedProblemKeys.value = new Set(keys)
      refreshAllFeatureStatsFromCache()
    }
  } catch (error) {
    console.error('加载已标记问题失败:', error)
  }
}

async function loadFeatureFilterRules() {
  if (!taskId.value) return

  try {
    const response = await axios.get(`/api/codeReview/${taskId.value}/problem_filters`)
    if (response.data.success) {
      filterRules.value = response.data.data.filter(rule => rule.is_enabled)
    } else {
      filterRules.value = []
    }
  } catch (error) {
    console.error('加载过滤规则失败:', error)
    filterRules.value = []
  }
}

function normalizeText(value) {
  if (value === null || value === undefined) return ''
  return String(value)
}

function isProblemFiltered(problem) {
  if (problem.problem_status === 3) return true
  if (!filterRules.value.length) return false

  const reasonText = normalizeText(problem.problem_reason)
  if (!reasonText) return false

  return filterRules.value.some((rule) => {
    const keywords = Array.isArray(rule.keywords) ? rule.keywords.filter(Boolean) : []
    if (!keywords.length) return false

    if (rule.logic_type === 'OR') {
      return keywords.some(keyword => reasonText.includes(keyword))
    }

    return keywords.every(keyword => reasonText.includes(keyword))
  })
}

function getProblemStatusForDisplay(problem) {
  if (isProblemMarked(problem)) return 4
  if (isProblemFiltered(problem)) return 3
  return problem.problem_status || 1
}

function getProblemStatusClass(problem) {
  const status = getProblemStatusForDisplay(problem)
  return {
    'status-new': status === 1,
    'status-viewed': status === 2,
    'status-filtered': status === 3,
    'status-marked': status === 4
  }
}

function getProblemStatusIndicatorClass(problem) {
  const status = getProblemStatusForDisplay(problem)
  return {
    'indicator-green': status === 1,
    'indicator-gray': status === 2 || status === 3,
    'indicator-marked': status === 4
  }
}

function getProblemStatusLabel(problem) {
  const status = getProblemStatusForDisplay(problem)
  if (status === 4) return '已标记'
  if (status === 3) return '已过滤'
  return null
}

function getProblemStatusTagType(problem) {
  const status = getProblemStatusForDisplay(problem)
  if (status === 4) return 'success'
  if (status === 3) return 'info'
  return ''
}

function getIssueLevelTagType(level) {
  switch (level) {
    case '重要问题': return 'danger'
    case '一般问题': return 'warning'
    case '建议改进': return 'info'
    default: return 'info'
  }
}

function toggleProblem(index) {
  if (collapsedProblems.value.has(index)) {
    collapsedProblems.value.delete(index)
  } else {
    collapsedProblems.value.add(index)
  }
}

function handleProblemClick(problem, index) {
  toggleProblem(index)
}

// 注释准确率反馈
const showFeedbackDialog = ref(false)
const feedbackStatus = ref({ clickedCount: 0, totalFunctions: 0, hasFeedback: false, delayedCount: 0 })
const feedbackTriggerPoint = ref('50%')

async function loadFeedbackStatus() {
  if (!taskId.value) return
  try {
    const response = await axios.get(`/api/codeReview/${taskId.value}/comment_accuracy_status`)
    if (response.data.success) {
      feedbackStatus.value = response.data.data
    }
  } catch (error) {
    console.error('加载反馈状态失败:', error)
  }
}

async function incrementClickedFunction(totalOverride = null) {
  if (!taskId.value || feedbackStatus.value.hasFeedback) return
  try {
    const body = totalOverride ? { total_override: totalOverride } : {}
    const response = await axios.post(`/api/codeReview/${taskId.value}/increment_clicked_function`, body)
    if (response.data.success) {
      const data = response.data.data
      feedbackStatus.value.clickedCount = data.clicked_count
      feedbackStatus.value.totalFunctions = data.total_functions
      feedbackStatus.value.delayedCount = data.delayed_count
      if (data.should_show_feedback && !data.already_feedback) {
        feedbackTriggerPoint.value = data.feedback_trigger_point || '50%'
        showFeedbackDialog.value = true
      }
    }
  } catch (error) {
    console.error('增加点击计数失败:', error)
  }
}

function handleFeedbackSubmitted() {
  feedbackStatus.value.hasFeedback = true
  ElMessage.success('感谢您的反馈！')
}

function handleFeedbackDelayed(data) {
  feedbackStatus.value.delayedCount = data.delayed_count
  if (data.next_trigger) {
    ElMessage.info(`已延迟反馈，将在${data.next_trigger}时再次提醒`)
  }
}

function isProblemMarked(problem) {
  return markedProblemKeys.value.has(buildProblemKey(problem))
}

function splitLocationDescription(value) {
  const text = String(value || '')
  const markers = ['源代码为：', '源程序为：', '源代码为:', '源程序为:']
  const marker = markers.find(item => text.includes(item))

  if (!marker) {
    return { text, source: '' }
  }

  const [prefix, ...rest] = text.split(marker)
  return {
    text: `${prefix.trim()}${marker}`,
    source: rest.join(marker).trim()
  }
}

function formatLocationText(value) {
  return splitLocationDescription(value).text
}

function extractLocationSource(value) {
  return splitLocationDescription(value).source
}

function formatLocationSource(value) {
  const source = extractLocationSource(value)
  if (!source) return ''
  if (source.includes('\n')) return source

  return source
    .replace(/}\s*else\s*{/g, '} else {')
    .replace(/([;{}])\s*/g, '$1\n')
    .replace(/\n{2,}/g, '\n')
    .trim()
}

function buildMarkedProblemPayload(problem) {
  const allowedFields = [
    'id',
    'issue_name',
    'issue_level',
    'issue_location',
    'file_name',
    'file',
    'function_name',
    'line',
    'end_line',
    'problem_reason',
    'description_requirement',
    'description_issue',
    'description_location',
    'description_impact',
    'affected_functions',
    'chain_name',
    'call_chain',
    'problem_status'
  ]

  const payload = {}
  allowedFields.forEach((field) => {
    if (problem[field] !== undefined && problem[field] !== null) {
      payload[field] = problem[field]
    }
  })

  return payload
}

async function toggleProblemMark(problem) {
  const problemKey = buildProblemKey(problem)
  const isMarked = markedProblemKeys.value.has(problemKey)

  try {
    if (isMarked) {
      await axios.delete(`/api/codeReview/${taskId.value}/marked_problems`, {
        data: {
          analysis_type: 'chain',
          problem_key: problemKey
        }
      })
      markedProblemKeys.value.delete(problemKey)
      problem.problem_status = problem.problem_status === 4 ? 1 : problem.problem_status
      ElMessage.success('已取消标记')
    } else {
      await axios.post(`/api/codeReview/${taskId.value}/marked_problems`, {
        analysis_type: 'chain',
        problem_key: problemKey,
        problem_data: buildMarkedProblemPayload(problem)
      })
      markedProblemKeys.value.add(problemKey)
      problem.problem_status = 4
      ElMessage.success('标记成功')
    }

    markedProblemKeys.value = new Set(markedProblemKeys.value)

    if (selectedFeature.value) {
      const key = getFeatureStatsKey(selectedFeature.value)
      allFeatureProblemsMap.value[key] = featureProblems.value.map(item => ({ ...item }))
    }

    refreshAllFeatureStatsFromCache()
  } catch (error) {
    console.error('标记操作失败:', error)
    ElMessage.error('标记操作失败')
  }
}

function updateCurrentFeatureStats() {
  if (!selectedFeature.value) return
  updateFeatureStatsByProblems(selectedFeature.value, featureProblems.value)
}


async function openFilterPanel() {
  await loadFeatureFilterRules()
  refreshAllFeatureStatsFromCache()
  ElMessage.success('已根据过滤规则刷新问题状态')
}

function mapChainProblem(problem) {
  const issueLocation = String(problem.issue_location || '')
  const locationMatch = issueLocation.match(/^(.*?):(\d+)(?::(\d+))?$/)
  const file = locationMatch?.[1] || issueLocation.split(':')[0] || ''
  const line = locationMatch?.[2] ? Number(locationMatch[2]) : (Number(problem.line) || null)
  const endLine = locationMatch?.[3] ? Number(locationMatch[3]) : (Number(problem.end_line) || null)

  const normalized = {
    ...problem,
    id: problem.id || buildProblemKey(problem),
    severity: problem.issue_level,
    title: problem.issue_name,
    description: problem.description_issue,
    impact: problem.description_impact,
    file,
    line,
    end_line: endLine
  }

  if (isProblemMarked(normalized)) {
    normalized.problem_status = 4
  }

  return normalized
}


// 加载目录树（实际的文件系统结构）
async function loadDirectoryTree() {
  try {
    const response = await axios.get(`/api/codeReview/codemap/${taskId.value}`)
    const payload = response.data?.data || response.data || {}

    projectInfo.value = payload.project || null

    if (payload.project?.tree) {
      directoryTreeData.value = formatProjectTree(payload.project.tree)
    } else {
      console.warn('未找到目录树数据，API返回:', response.data)
      directoryTreeData.value = [{
        id: 'empty',
        label: '暂无代码树数据',
        type: 'directory',
        children: []
      }]
    }
  } catch (error) {
    console.error('加载目录树失败:', error)
    ElMessage.error('加载目录树失败')
  }
}

function convertProjectNode(node, parentPath = '') {
  if (!node) return null

  const nodeName = node.name || '未命名节点'
  const nodePath = parentPath ? `${parentPath}/${nodeName}` : (node.path || nodeName)
  // 优先以 node.type 为准判断是否是目录；只有明确没有 type 时才用 children 推断
  const nodeType = (node.type || '').toLowerCase()
  const isDirectory = nodeType === 'directory' || (nodeType === '' && Array.isArray(node.children) && node.children.some(c => c.type === 'directory' || c.type === 'file'))

  const converted = {
    id: nodePath,
    label: nodeName,
    type: isDirectory ? 'directory' : 'file',
    path: node.path || nodePath,
    problemCount: node.problemCount || node.problem_count || 0,
    chainOrder: node.chainOrder || null,
    children: []
  }

  // 只有目录节点才递归处理 children（文件节点的 children 是函数列表，不应渲染为树节点）
  if (isDirectory && node.children && Array.isArray(node.children)) {
    converted.children = node.children
      .map(child => convertProjectNode(child, nodePath))
      .filter(Boolean)
  } else if (!isDirectory && node.children && Array.isArray(node.children)) {
    // 文件节点：将函数列表转为树形子节点显示
    converted.functions = node.children
    converted.children = node.children.map((func, idx) => ({
      id: `func:${nodePath}:${func.function_name || func.name || idx}`,
      label: func.function_name || func.name || '未知函数',
      name: func.function_name || func.name || '未知函数',
      type: 'function',
      path: node.path || nodePath,
      file_path: node.path || nodePath,
      source_code: func.source_code || '',
      line: func.start_line || func.line || null,
      end_line: func.end_line || null,
      problemCount: 0,
      children: []
    }))
  }

  return converted
}

function formatProjectTree(tree) {
  if (!tree) return []
  // 如果根节点 name 是 UUID（临时文件夹），直接跳过，用其子节点作为根
  const isUuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(tree.name || '')
  if (isUuid && tree.children && tree.children.length > 0) {
    // 过滤掉非用户代码目录（如 AI 生成的 call_graph），只保留用户上传的代码库目录
    const EXCLUDED_DIRS = new Set(['call_graph', 'call_graphs', '__pycache__', '.git'])
    const userDirs = tree.children.filter(child => !EXCLUDED_DIRS.has(child.name))
    return userDirs.map(child => convertProjectNode(child, '')).filter(Boolean)
  }
  const rootNode = convertProjectNode(tree)
  return rootNode ? [rootNode] : []
}

// 选择功能节点（从树形组件点击）
async function selectFeatureNode(data) {
  await selectFeature(data)
  // 只有叶子节点（没有子功能的）才触发注释准确率计数
  if (!data.sub_features || data.sub_features.length === 0) {
    incrementClickedFunction(leafFeatureCount.value)
  }
}

// 选择功能
async function selectFeature(feature) {
  if (featureProblems.value.length > 0) {
    const unmarkedGreenProblems = featureProblems.value.filter(problem => {
      const status = getProblemStatusForDisplay(problem)
      return status === 1 && !isProblemMarked(problem)
    })

    if (unmarkedGreenProblems.length > 0) {
      unmarkedGreenProblems.forEach(problem => {
        problem.problem_status = 3
      })

      if (selectedFeature.value) {
        const currentKey = getFeatureStatsKey(selectedFeature.value)
        const existingProblems = allFeatureProblemsMap.value[currentKey] || []
        allFeatureProblemsMap.value[currentKey] = existingProblems.map(item => {
          const match = unmarkedGreenProblems.find(problem => buildProblemKey(problem) === buildProblemKey(item))
          return match ? { ...item, problem_status: 3 } : item
        })
      }

      try {
        const idsToFilter = unmarkedGreenProblems
          .map(problem => problem.id)
          .filter(id => id !== undefined && id !== null)

        if (idsToFilter.length > 0) {
          await axios.patch(`/api/codeReview/${taskId.value}/problems/status`, {
            problem_ids: idsToFilter,
            status: 3
          })
        }
      } catch (error) {
        console.error('批量更新未标记问题为已过滤失败:', error)
      }

      refreshAllFeatureStatsFromCache()
    }
  }

  selectedFeature.value = feature
  highlightedProblem.value = null
  featureDescription.value = ''  // 切换功能时清空描述
  
  // 更新目录树的链路顺序标记
  updateChainOrderMarkers(feature)
  
  // 加载功能的问题列表（链路审查问题，按功能过滤）
  try {
    const key = getFeatureStatsKey(feature)
    const cachedProblems = allFeatureProblemsMap.value[key]

    if (cachedProblems) {
      const descRecord = cachedProblems.find(p => p.chain_function_description)
      if (descRecord) featureDescription.value = descRecord.chain_function_description
      featureProblems.value = cachedProblems.filter(p => p.issue_name !== '无问题').map(problem => ({ ...problem }))
    } else {
    const resp = await axios.get(`/api/codeReview/progressive/problems/${taskId.value}`, {
      params: { feature: feature.name }
    })

    if (resp.data && resp.data.problems) {
        const allMapped = resp.data.problems.map(mapChainProblem)
        // 提取功能描述（从任意一条记录取，包括占位记录）
        const descRecord = allMapped.find(p => p.chain_function_description)
        if (descRecord) featureDescription.value = descRecord.chain_function_description
        // 过滤掉占位记录（issue_name='无问题'），只显示真实问题
        const mappedProblems = allMapped.filter(p => p.issue_name !== '无问题')
        featureProblems.value = mappedProblems
        // 缓存时保存全量数据（含占位记录），供下次取描述用
        allFeatureProblemsMap.value[key] = allMapped
    } else {
      featureProblems.value = []
      }
    }
  } catch (e) {
    console.error('加载功能问题失败:', e)
    featureProblems.value = []
  }

  updateCurrentFeatureStats()

  if (secondColumnTab.value === 'graph') {
    await loadFeatureFileCallGraph()
  }
}

// 更新链路顺序标记：解析 call_chain 或 key_functions，在函数/文件节点上标记 A/B/C 顺序
function updateChainOrderMarkers(feature) {
  // 先清除所有标记
  clearChainOrderMarkers(directoryTreeData.value)
  
  // 解析调用顺序函数列表
  let orderedFunctions = []

  if (feature.call_chain && typeof feature.call_chain === 'string') {
    orderedFunctions = feature.call_chain
      .split(/→|->|,/)
      .map(s => normalizeFunctionName(s))
      .filter(Boolean)
  }

  // 如果 call_chain 没有内容，fallback 到 key_functions
  if (orderedFunctions.length === 0 && feature.key_functions && feature.key_functions.length > 0) {
    orderedFunctions = feature.key_functions
      .map(s => normalizeFunctionName(s))
      .filter(Boolean)
  }

  // 如果还是没有，fallback 到 related_functions
  if (orderedFunctions.length === 0 && feature.related_functions && feature.related_functions.length > 0) {
    try {
      const funcs = typeof feature.related_functions === 'string'
        ? JSON.parse(feature.related_functions)
        : feature.related_functions
      orderedFunctions = (Array.isArray(funcs) ? funcs : [])
        .map(s => normalizeFunctionName(s))
        .filter(Boolean)
    } catch (e) {
      orderedFunctions = []
    }
  }

  if (orderedFunctions.length === 0) {
    currentChainOrderLetters.value = []
    return
  }

  // 仅对“实际命中目录树节点”的代码单元按顺序重新编号，避免出现 A/B/D 这种跳字母
  const matchedLetters = []
  orderedFunctions.forEach((funcName) => {
    const node = findBestChainTargetNode(directoryTreeData.value, funcName)
    if (!node) return
    const label = String.fromCharCode(65 + matchedLetters.length) // A, B, C...
    node.chainOrder = label
    matchedLetters.push(label)
  })

  currentChainOrderLetters.value = matchedLetters

  // 强制触发响应式更新
  directoryTreeData.value = [...directoryTreeData.value]
}

// 清除链路顺序标记
function clearChainOrderMarkers(nodes) {
  nodes.forEach(node => {
    node.chainOrder = null
    if (node.children && node.children.length > 0) {
      clearChainOrderMarkers(node.children)
    }
  })
  currentChainOrderLetters.value = []
}

// 归一化函数名（去掉参数、注释标识、中文括号等）
function normalizeFunctionName(rawName) {
  if (!rawName || typeof rawName !== 'string') return ''
  let name = rawName.trim()

  if (name.includes('::')) {
    name = name.split('::').pop()
  }

  // 去掉“（隐含）”“(隐含)”这类注释
  name = name.replace(/[（(].*?[）)]/g, '')

  // 去掉函数参数
  name = name.replace(/\s*\(.*$/, '')

  // 去掉多余符号
  name = name.replace(/[\s`'"\[\]]+/g, '')

  return name.trim()
}

// 标记文件的链路顺序
function markFileWithChainOrder(nodes, filePath, orderLabel) {
  for (const node of nodes) {
    if (node.type === 'file' && node.path && node.path.includes(filePath)) {
      node.chainOrder = orderLabel
      return true
    }
    if (node.children && node.children.length > 0) {
      if (markFileWithChainOrder(node.children, filePath, orderLabel)) {
        return true
      }
    }
  }
  return false
}

// 在目录树中查找函数节点
function findFunctionNode(nodes, funcName) {
  const normalizedTarget = normalizeFunctionName(funcName)

  for (const node of nodes) {
    if (node.type === 'function') {
      const nodeFuncName = normalizeFunctionName(node.name || node.label || '')
      if (nodeFuncName === normalizedTarget) {
        return node
      }
    }
    if (node.children && node.children.length > 0) {
      const childNode = findFunctionNode(node.children, normalizedTarget)
      if (childNode) return childNode
    }
  }
  return null
}

// 在目录树中查找与链路代码单元最匹配的节点：优先函数，其次文件名/模块文件名
function findBestChainTargetNode(nodes, targetName) {
  const normalizedTarget = normalizeFunctionName(targetName)
  if (!normalizedTarget) return null

  const functionNode = findFunctionNode(nodes, normalizedTarget)
  if (functionNode) return functionNode

  return findFileNodeByCodeUnitName(nodes, normalizedTarget)
}

function findFileNodeByCodeUnitName(nodes, targetName) {
  for (const node of nodes) {
    if (node.type === 'file') {
      const fileLabel = String(node.label || '')
      const fileBaseName = normalizeFunctionName(fileLabel.replace(/\.[^.]+$/, ''))
      if (fileBaseName === targetName) {
        return node
      }
    }

    if (node.children && node.children.length > 0) {
      const childNode = findFileNodeByCodeUnitName(node.children, targetName)
      if (childNode) return childNode
    }
  }

  return null
}

// 加载功能的问题列表
async function loadFeatureProblems(featureId) {
  try {
    const response = await axios.get(`/api/codeReview/progressive/problems/${taskId.value}`, {
      params: { feature: featureId }
    })
    
    if (response.data && response.data.problems) {
      featureProblems.value = response.data.problems.map(mapChainProblem)
      updateCurrentFeatureStats()
    } else {
      featureProblems.value = []
      updateCurrentFeatureStats()
    }
  } catch (error) {
    console.error('加载问题列表失败:', error)
    featureProblems.value = []
    updateCurrentFeatureStats()
  }
}

// 处理树节点点击
async function handleTreeNodeClick(data) {
  highlightedProblem.value = null

  if (data.type === 'file') {
    selectedFileName.value = data.label
    currentSelectedType.value = 'file'
    currentSelectedName.value = data.label
    await loadSourceCode(data.path)
    showFunctionList.value = false
  } else if (data.type === 'function') {
    currentSelectedType.value = 'function'
    currentSelectedName.value = data.label
    if (data.source_code) {
      currentSourceCode.value = data.source_code
      currentSourceFile.value = data.file_path || data.path
    } else {
      await loadSourceCode(data.file_path || data.path, data.line)
    }
    showFunctionList.value = false
  } else if (data.type === 'directory') {
    // 点击目录：展开/折叠（由 Element Plus Tree 自动处理）
  }
}

// 加载文件的函数列表
async function loadFileFunctions(filePath) {
  try {
    const response = await axios.get(`/api/codeReview/codemap/${taskId.value}`)
    
    const payload = response.data?.data || response.data || {}
    const allFunctions = payload.functions || []
    
    // 过滤出该文件的函数（兼容不同字段名与相对路径匹配）
    const functions = allFunctions.filter(f => {
      const fpath = f.file || f.file_path || f.path || ''
      return fpath === filePath || fpath.endsWith(filePath)
    })
    
    // 如果选中了功能，添加链路顺序
    if (selectedFeature.value && selectedFeature.value.key_functions) {
      functions.forEach(func => {
        const index = selectedFeature.value.key_functions.indexOf(func.name)
        if (index !== -1) {
          func.chainOrder = String.fromCharCode(65 + index)
        }
      })
    }
    
    currentFileFunctions.value = functions
  } catch (error) {
    console.error('加载函数列表失败:', error)
    currentFileFunctions.value = []
  }
}

// 选择函数
async function selectFunction(func) {
  currentSourceFile.value = func.file || func.file_path || ''
  await loadSourceCode(currentSourceFile.value, func.line)
  showFunctionList.value = false
}

// 加载源代码
async function loadSourceCode(filePath, highlightLine = null) {
  try {
    if (!filePath) return
    const encodedPath = encodeURIComponent(filePath)
    const url = `/api/codeReview/codemap/${taskId.value}/file/${encodedPath}`
    const response = await axios.get(url)
    
    const content = response.data?.data?.source_code || response.data?.content || ''
    currentSourceCode.value = content
    currentSourceFile.value = filePath
    
    // 如果指定了行号，滚动到该行
    await nextTick()
    if (highlightLine) {
      scrollToLine(highlightLine)
    }
  } catch (error) {
    console.error('加载源代码失败:', error)
    currentSourceCode.value = '// 加载源代码失败'
  }
}

// 定位问题
async function locateProblem(problem) {
  const resolvedFilePath = resolveProblemFilePath(problem)
  const functionNode = resolveProblemFunctionNode(problem, resolvedFilePath)

  highlightedProblem.value = { problem }

  currentSelectedType.value = functionNode ? 'function' : 'file'
  currentSelectedName.value = functionNode?.name || resolvedFilePath || currentSourceFile.value
  currentSourceFile.value = resolvedFilePath

  if (functionNode?.source_code) {
    currentSourceCode.value = functionNode.source_code
    currentSourceFile.value = functionNode.file_path || functionNode.path || resolvedFilePath
    highlightedProblem.value = {
      problem: {
        ...problem,
        line: functionNode.line || functionNode.start_line || problem.line,
        end_line: functionNode.end_line || problem.end_line
      }
    }
    return
  }

  await loadSourceCode(resolvedFilePath, problem.line)
}

// 滚动到指定行
function scrollToLine(lineNumber) {
  // TODO: 实现行号高亮和滚动
  console.log('滚动到行号:', lineNumber)
}

// directoryTreeData 已在 formatProjectTree 中处理好根节点，直接透传
const filteredDirectoryTreeData = computed(() => directoryTreeData.value)

// 获取节点图标
function getNodeIcon(data) {
  if (data.type === 'directory') {
    return 'el-icon-folder'
  } else if (data.type === 'file') {
    const ext = data.label.split('.').pop()
    if (['c', 'cpp', 'cc', 'cxx'].includes(ext)) {
      return 'el-icon-document'
    } else if (['h', 'hpp'].includes(ext)) {
      return 'el-icon-tickets'
    }
    return 'el-icon-document'
  }
  return 'el-icon-document'
}

// VSCode 风格文件图标颜色
function getFileIconColor(filename) {
  if (!filename) return '#89DDFF'
  const ext = filename.split('.').pop()?.toLowerCase()
  const colorMap = {
    c: '#5C9BD6', cpp: '#5C9BD6', cc: '#5C9BD6', cxx: '#5C9BD6',
    h: '#A8C4E0', hpp: '#A8C4E0',
    v: '#E06C75', vh: '#E06C75',
    vhd: '#C678DD', vhdl: '#C678DD',
    py: '#3D9970', js: '#E5C07B', ts: '#4EC9B0',
    json: '#E5C07B', xml: '#D19A66', md: '#89DDFF',
    txt: '#ABB2BF'
  }
  return colorMap[ext] || '#ABB2BF'
}

function getVscodeFileIconClass(filename) {
  if (!filename) return ''
  const ext = filename.split('.').pop()?.toLowerCase()
  return `file-ext-${ext}`
}

function walkTree(nodes, visitor) {
  for (const node of nodes || []) {
    if (!node) continue
    visitor(node)
    if (node.children && node.children.length > 0) {
      walkTree(node.children, visitor)
    }
  }
}

function parseProblemFunctionName(problem) {
  const candidates = [
    problem?.function_name,
    problem?.issue_function,
    problem?.affected_functions,
    problem?.description_location
  ].filter(Boolean)

  for (const text of candidates) {
    const str = String(text)
    const match = str.match(/([A-Za-z_][A-Za-z0-9_]*)函数/)
    if (match?.[1]) return match[1]
  }

  return ''
}

function resolveProblemFilePath(problem) {
  const rawFile = String(problem?.file || '').trim()
  if (!rawFile) return ''

  let matchedPath = ''
  walkTree(directoryTreeData.value, (node) => {
    if (matchedPath || node.type !== 'file') return
    const nodePath = String(node.path || '')
    const nodeLabel = String(node.label || '')
    if (nodePath === rawFile || nodePath.endsWith(`/${rawFile}`) || nodeLabel === rawFile) {
      matchedPath = nodePath
    }
  })

  return matchedPath || rawFile
}

function resolveProblemFunctionNode(problem, resolvedFilePath) {
  const targetFunction = parseProblemFunctionName(problem)
  if (!targetFunction) return null

  let matchedNode = null
  walkTree(directoryTreeData.value, (node) => {
    if (matchedNode || node.type !== 'function') return
    const sameFile = !resolvedFilePath || String(node.file_path || node.path || '') === resolvedFilePath
    const sameName = String(node.name || node.label || '') === targetFunction
    if (sameFile && sameName) {
      matchedNode = node
    }
  })

  return matchedNode
}

// 拖拽相关
function startResize(type, event) {
  isResizing.value = true
  resizeType.value = type
  startX.value = event.clientX
  
  if (type === 1) {
    startWidth.value = featureListWidth.value
  } else if (type === 2) {
    startWidth.value = treeWidth.value
  } else if (type === 3) {
    startWidth.value = infoProblemWidth.value
  }
  
  document.addEventListener('mousemove', handleResize)
  document.addEventListener('mouseup', stopResize)
  event.preventDefault()
}

function handleResize(event) {
  if (!isResizing.value) return
  
  const deltaX = event.clientX - startX.value
  
  if (resizeType.value === 1) {
    featureListWidth.value = Math.max(resizeLimits.featureList.min, Math.min(resizeLimits.featureList.max, startWidth.value + deltaX))
  } else if (resizeType.value === 2) {
    treeWidth.value = Math.max(resizeLimits.tree.min, Math.min(resizeLimits.tree.max, startWidth.value + deltaX))
  } else if (resizeType.value === 3) {
    infoProblemWidth.value = Math.max(resizeLimits.infoProblem.min, Math.min(resizeLimits.infoProblem.max, startWidth.value - deltaX))
  }
}

function stopResize() {
  isResizing.value = false
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
}

// 垂直拖拽
function startVerticalResize(event) {
  isResizing.value = true
  startY.value = event.clientY
  startHeight.value = featureInfoHeight.value
  
  document.addEventListener('mousemove', handleVerticalResize)
  document.addEventListener('mouseup', stopVerticalResize)
  event.preventDefault()
}

function handleVerticalResize(event) {
  if (!isResizing.value) return
  
  const deltaY = event.clientY - startY.value
  featureInfoHeight.value = Math.max(150, Math.min(600, startHeight.value + deltaY))
}

function stopVerticalResize() {
  isResizing.value = false
  document.removeEventListener('mousemove', handleVerticalResize)
  document.removeEventListener('mouseup', stopVerticalResize)
}

// 生命周期
onMounted(async () => {
  await Promise.all([
    loadMarkedProblems(),
    loadFeatures(),
    loadDirectoryTree(),
    loadFeedbackStatus()
  ])
})

// 进度显示相关方法
function handleProgressUpdated(progressData) {
  console.log('链路审查进度更新:', progressData)
  // 可以在这里添加其他进度更新的处理逻辑
}

function handleTaskCompleted(taskData) {
  console.log('链路审查任务完成:', taskData)
  // 任务完成后重新加载代码地图以获取最新数据
  loadFeatures()
}

function handleTaskFailed(taskData) {
  console.log('链路审查任务失败:', taskData)
  ElMessage.error('链路审查任务失败')
}
</script>

<style scoped>
.chain-codemap-fullscreen {
  width: 100%;
  height: 100vh;
  background: #f5f7fa;
  overflow: hidden;
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.four-column-layout {
  display: flex;
  height: 100%;
  width: 100%;
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  overflow: hidden;
}

/* 第一栏：功能列表 */
.feature-list-column {
  background: #ffffff;
  border-right: 1px solid #dcdfe6;
  display: flex;
  flex-direction: column;
  min-width: 200px;
  max-width: 500px;
  flex-shrink: 0;
}

.column-header {
  padding: 16px;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.column-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.feature-count {
  font-size: 12px;
  color: #909399;
  background: #f4f4f5;
  padding: 2px 8px;
  border-radius: 10px;
}

.feature-list-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

/* 功能模块选中高亮（增强） */
.feature-list-content :deep(.el-tree-node__content) {
  border-radius: 8px;
  margin: 2px 4px;
  min-height: 34px;
  transition: all 0.15s ease;
}

.feature-list-content :deep(.el-tree-node__content:hover) {
  background: #eef5ff;
}

.feature-list-content :deep(.el-tree-node.is-current > .el-tree-node__content) {
  background: linear-gradient(90deg, #2f80ed 0%, #56ccf2 100%) !important;
  box-shadow: 0 0 0 1px rgba(47, 128, 237, 0.25), 0 6px 14px rgba(47, 128, 237, 0.25);
}

.feature-list-content :deep(.el-tree-node.is-current > .el-tree-node__content .feature-name) {
  color: #ffffff !important;
  font-weight: 700;
}

.feature-list-content :deep(.el-tree-node.is-current > .el-tree-node__content .feature-problem-tag) {
  border-color: rgba(255,255,255,0.45);
  background: rgba(255,255,255,0.18);
  color: #ffffff;
}

/* 功能树节点样式 */
.feature-tree-node {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding-right: 8px;
  gap: 8px;
}

.feature-tree-node .feature-name {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.feature-status-badges {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-badge {
  min-width: 18px;
  height: 18px;
  border-radius: 10px;
  padding: 0 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  color: #ffffff;
  line-height: 1;
}

.status-badge-unfiltered {
  background: #22c55e;
}

.status-badge-filtered {
  background: #9ca3af;
}

.status-badge-marked {
  background: #3b82f6;
}

.feature-list-content :deep(.el-tree-node.is-current > .el-tree-node__content .status-badge) {
  background: rgba(255, 255, 255, 0.22);
  color: #ffffff;
}

/* 旧的feature-item样式（保留以防万一） */
.feature-item {
  padding: 12px;
  margin-bottom: 8px;
  background: #f9fafc;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.feature-item:hover {
  background: #ecf5ff;
  border-color: #409eff;
}

.feature-item.active {
  background: #409eff;
  border-color: #409eff;
  color: #ffffff;
}

.feature-item.active .feature-problem-count {
  background: #ffffff;
  color: #409eff;
}

.feature-name {
  font-size: 14px;
  font-weight: 500;
  flex: 1;
}

.feature-problem-count {
  min-width: 24px;
  height: 24px;
  background: #f56c6c;
  color: #ffffff;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}

.empty-features {
  text-align: center;
  padding: 40px 20px;
  color: #909399;
}

.empty-features i {
  font-size: 48px;
  margin-bottom: 16px;
  display: block;
}

/* 第二栏：目录树 */
.directory-tree-column {
  background: #1e1e1e;
  border-right: 1px solid #3c3c3c;
  display: flex;
  flex-direction: column;
  min-width: 250px;
  max-width: 600px;
  position: relative;
  flex-shrink: 0;
}

.hint-text {
  font-size: 11px;
  color: #4ec9b0;
  font-weight: normal;
  letter-spacing: 0.3px;
}

.header-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.project-meta {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.meta-tag {
  margin-left: 4px;
}

/* 第二栏 header 深色覆盖 */
.directory-tree-column .column-header {
  background: #252526;
  border-bottom: 1px solid #3c3c3c;
  padding: 8px 12px;
}

.directory-tree-column .column-header h3 {
  color: #bbbbbb;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.tree-content {
  flex: 1;
  overflow-y: auto;
  padding: 0;
  position: relative;
  background: #1e1e1e;
}

.callgraph-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.callgraph-toolbar {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  gap: 8px;
}

.callgraph-content {
  flex: 1 1 auto;
  min-height: 600px;
  height: 100%;
}

.tree-node-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding-right: 8px;
}

.node-label {
  display: flex;
  align-items: center;
  gap: 6px;
}

.node-icon {
  color: #909399;
}

.chain-order-badge,
.vscode-chain-badge {
  background: #67c23a;
  color: #ffffff;
  padding: 1px 6px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  margin-left: 4px;
  flex-shrink: 0;
}

.problem-count-badge,
.vscode-problem-badge {
  background: #f56c6c;
  color: #ffffff;
  padding: 1px 6px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  margin-left: 4px;
  flex-shrink: 0;
}

/* ===== VSCode 风格目录树 ===== */
.vscode-tree-wrapper {
  height: 100%;
  overflow: auto;
  background: #1e1e1e;
  border-radius: 0;
}

.vscode-tree {
  background: transparent;
  --el-tree-node-hover-bg-color: #2a2d2e;
  --el-tree-node-content-height: 22px;
  --el-color-primary: #0078d4;
  padding: 4px 0;
}

.vscode-tree :deep(.el-tree-node__content) {
  height: 22px;
  padding: 0 !important;
  border-radius: 0;
  background: transparent;
  transition: background 0.1s;
}

.vscode-tree :deep(.el-tree-node__content:hover) {
  background: #2a2d2e !important;
  transform: none;
}

.vscode-tree :deep(.el-tree-node.is-current > .el-tree-node__content) {
  background: #094771 !important;
  border-left: none !important;
  padding-left: 0 !important;
  font-weight: normal;
}

.vscode-tree :deep(.el-tree-node.is-current > .el-tree-node__content:hover) {
  background: #094771 !important;
  transform: none;
}

.vscode-tree :deep(.el-tree-node__expand-icon) {
  color: #c5c5c5;
  font-size: 12px;
  padding: 0 2px;
  width: 16px;
  flex-shrink: 0;
}

.vscode-tree :deep(.el-tree-node__expand-icon.is-leaf) {
  color: transparent;
}

.vscode-tree :deep(.el-tree-node__label) {
  font-size: 13px;
  color: #cccccc;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  flex: 1;
  overflow: hidden;
}

.vscode-tree :deep(.el-tree-node) {
  margin-bottom: 0;
}

.vscode-tree :deep(.el-tree-node__children) {
  padding-left: 0;
}

.vscode-tree-node {
  display: flex;
  align-items: center;
  gap: 4px;
  width: 100%;
  height: 22px;
  padding-right: 8px;
  font-size: 13px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  overflow: hidden;
}

.vscode-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 16px;
  height: 16px;
}

.vscode-node-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #cccccc;
  font-size: 13px;
  line-height: 22px;
}

.vscode-tree-node.is-directory .vscode-node-label {
  color: #cccccc;
  font-weight: 400;
}

.vscode-tree-node.is-file .vscode-node-label {
  color: #cccccc;
  font-weight: 400;
}

.vscode-tree-node.is-function .vscode-node-label {
  color: #dcdcaa;
  font-family: 'Consolas', 'Courier New', monospace;
  font-size: 12px;
}

.vscode-icon-function {
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

/* 函数列表面板 - VSCode 风格 */
.function-list-panel {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  max-height: 50%;
  background: #252526;
  border-top: 1px solid #3c3c3c;
  box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.4);
  display: flex;
  flex-direction: column;
  z-index: 10;
}

.function-list-header {
  padding: 6px 12px;
  background: #2d2d2d;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #3c3c3c;
  flex-shrink: 0;
}

.function-list-title {
  font-size: 11px;
  font-weight: 600;
  color: #bbbbbb;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.close-btn {
  background: none;
  border: none;
  font-size: 14px;
  color: #858585;
  cursor: pointer;
  padding: 2px 4px;
  transition: color 0.15s;
  line-height: 1;
  flex-shrink: 0;
}

.close-btn:hover {
  color: #cccccc;
}

.function-list-items {
  flex: 1;
  overflow-y: auto;
  padding: 4px 0;
}

.function-item {
  padding: 3px 12px;
  height: 22px;
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  transition: background 0.1s;
}

.function-item:hover {
  background: #2a2d2e;
}

.func-icon {
  color: #dcdcaa;
  font-size: 14px;
  font-style: normal;
  flex-shrink: 0;
  font-family: 'Consolas', monospace;
}

.function-name {
  font-size: 13px;
  font-family: 'Consolas', 'Courier New', monospace;
  color: #cccccc;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 第三栏：源代码 */
.source-code-column {
  flex: 1 1 auto;
  background: #1e1e1e;
  border-right: 1px solid #3c3c3c;
  display: flex;
  flex-direction: column;
  min-width: 200px;
  overflow: hidden;
}

/* 第四栏：功能介绍 + 问题列表 */
.info-problem-column {
  background: #ffffff;
  display: flex;
  flex-direction: column;
  min-width: 300px;
  max-width: 600px;
  flex-shrink: 0;
  overflow: hidden;
}

.feature-info-section {
  display: flex;
  flex-direction: column;
  border-bottom: 1px solid #dcdfe6;
  min-height: 100px;
  flex-shrink: 0;
}

.section-header {
  padding: 16px;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.problem-count {
  font-size: 12px;
  color: #f56c6c;
  background: #fef0f0;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 600;
}

.feature-info-content {
  flex: 1;
  overflow-y: auto;
  padding: 10px 14px;
}

.feature-overview {
  display: flex;
  flex-direction: column;
}

.overview-text {
  font-size: 13px;
  color: #303133;
  line-height: 1.7;
  margin: 0;
  word-break: break-word;
}

.empty-info {
  text-align: center;
  padding: 20px;
  color: #909399;
}

/* 垂直拖拽分界线 */
.vertical-resize-handle {
  height: 8px;
  background: #f5f7fa;
  cursor: ns-resize;
  border-top: 1px solid #dcdfe6;
  border-bottom: 1px solid #dcdfe6;
  transition: background 0.2s;
}

.vertical-resize-handle:hover {
  background: #409eff;
}

/* 问题列表 */
.problem-list-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

.problem-list-header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.problem-list-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.empty-problems {
  text-align: center;
  padding: 40px 20px;
  color: #67c23a;
}

.empty-problems i {
  font-size: 48px;
  margin-bottom: 16px;
  display: block;
}

.problems-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.problem-block {
  background: #fef2f2;
  padding: 12px;
  border-radius: 8px;
  border-left: 4px solid #e74c3c;
  margin-bottom: 4px;
  transition: all 0.3s ease;
}

.problem-block.status-new {
  background: #f0fdf4;
  border-left-color: #22c55e;
}

.problem-block.status-viewed,
.problem-block.status-filtered {
  background: #f5f5f5;
  border-left-color: #9ca3af;
  opacity: 0.85;
}

.problem-block.status-marked {
  background: #eff6ff;
  border-left-color: #3b82f6;
}

.problem-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  color: #e74c3c;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  padding: 4px 0;
  border-radius: 4px;
  transition: background-color 0.2s ease;
}

.problem-title:hover {
  background-color: rgba(231, 76, 60, 0.1);
}

.problem-title-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.problem-title-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.problem-status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.indicator-green {
  background-color: #22c55e;
  box-shadow: 0 0 6px rgba(34, 197, 94, 0.5);
}

.indicator-gray {
  background-color: #9ca3af;
}

.indicator-marked {
  background-color: #3b82f6;
  box-shadow: 0 0 6px rgba(59, 130, 246, 0.5);
}

.status-tag {
  margin-left: 6px;
}

.problem-level-tag {
  margin-left: 6px;
}

.collapse-icon {
  transition: transform 0.3s ease;
  cursor: pointer;
  user-select: none;
}

.collapse-icon.collapsed {
  transform: rotate(-90deg);
}

.problem-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-left: 16px;
}

.problem-field {
  display: flex;
  flex-direction: column;
  padding: 4px 0;
  border-bottom: 1px dashed #eee;
  gap: 3px;
}

.problem-field:last-child {
  border-bottom: none;
}

.field-label {
  font-size: 12px;
  color: #888;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 2px;
}

.field-value {
  font-size: 13px;
  color: #333;
  font-weight: 400;
  line-height: 1.4;
  word-break: break-word;
}

.location-description {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.location-text {
  white-space: pre-wrap;
}

.location-source-code {
  margin: 0;
  padding: 10px 12px;
  max-height: 260px;
  overflow: auto;
  border-radius: 6px;
  border: 1px solid #d8e2f0;
  background: #0f172a;
  color: #dbeafe;
  font-size: 12px;
  line-height: 1.55;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  white-space: pre;
  word-break: normal;
}

.location-source-code code {
  font-family: inherit;
  color: inherit;
}

/* 第二栏 Tab 深色主题覆盖 */
.directory-tree-column .second-column-tabs {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.directory-tree-column :deep(.el-tabs__header) {
  background: #252526;
  border-bottom: 1px solid #3c3c3c;
  margin: 0;
  padding: 0 8px;
}

.directory-tree-column :deep(.el-tabs__nav-wrap::after) {
  background: #3c3c3c;
  height: 1px;
}

.directory-tree-column :deep(.el-tabs__item) {
  color: #969696;
  font-size: 13px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  height: 35px;
  line-height: 35px;
  padding: 0 16px;
}

.directory-tree-column :deep(.el-tabs__item.is-active) {
  color: #cccccc;
  font-weight: 400;
}

.directory-tree-column :deep(.el-tabs__item:hover) {
  color: #cccccc;
}

.directory-tree-column :deep(.el-tabs__active-bar) {
  background: #0078d4;
  height: 1px;
  bottom: 0;
}

.directory-tree-column :deep(.el-tabs__content) {
  flex: 1;
  overflow: hidden;
  background: #1e1e1e;
}

.directory-tree-column :deep(.el-tab-pane) {
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* vscode-tree-wrapper 撑满 tab-pane */
.directory-tree-column .vscode-tree-wrapper {
  flex: 1;
  overflow: auto;
}

/* 滚动条 - VSCode 风格 */
.vscode-tree-wrapper::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

.vscode-tree-wrapper::-webkit-scrollbar-track {
  background: transparent;
}

.vscode-tree-wrapper::-webkit-scrollbar-thumb {
  background: #424242;
  border-radius: 0;
  border: 2px solid #1e1e1e;
}

.vscode-tree-wrapper::-webkit-scrollbar-thumb:hover {
  background: #4f4f4f;
}

/* 拖拽分界线 */
  .resize-handle {
  width: 2px;
  background: #f5f7fa;
  cursor: ew-resize;
  border-left: 1px solid #dcdfe6;
  border-right: 1px solid #dcdfe6;
  transition: background 0.2s;
  flex-shrink: 0;
}

.resize-handle:hover {
  background: #409eff;
}
</style> 
