<template>
  <div class="codemap-fullscreen">
    <!-- 主内容区域 -->
    <div class="main-content">
      <!-- 左侧：双目录树（旧/新） -->
      <CompareTreePanel
        :trees-visible="treesVisible"
        :tree-panel-width="treePanelWidth"
        :collapsed-tree-width="collapsedTreeWidth"
        :old-tree-data="oldTreeData"
        :new-tree-data="newTreeData"
        :selected-old-tree-key="selectedOldTreeKey"
        :selected-new-tree-key="selectedNewTreeKey"
        :problem-counts-by-id="problemCountsById"
        :problem-badge-types-by-id="problemBadgeTypesById"
        :marked-locations="markedLocations"
        :function-start-line-by-key="functionStartLineByKey"
        @toggle-trees="toggleTrees"
        @select-pair="selectPair"
        @select-file="selectFile"
      />

      <!-- 左侧拖拽分界线 -->
      <div class="resize-handle left-resize" @mousedown="startLeftResize"></div>

      <!-- 中间：双代码栏（旧/新） -->
      <CodeComparePane
        ref="codeCompareRef"
        :old-text="oldCodeText"
        :new-text="newCodeTextEffective"
        :old-meta="oldCodeMeta"
        :new-meta="newCodeMeta"
        v-model:newCodeViewMode="newCodeViewMode"
        :diff-rows="diffRows"
        :change-row-indices="changeRowIndices"
      />

      <!-- 右侧拖拽分界线 -->
      <div v-show="showSidebar" class="resize-handle right-resize" @mousedown="startRightResize"></div>

      <!-- 右侧边栏（函数功能介绍 + 问题单） -->
      <div v-show="showSidebar" class="sidebar-container" :style="{ width: sidebarWidth + 'px' }">
        <CodeMapSidebar
          v-if="!showFilterPanel"
          :mode="sidebarMode"
          :title="sidebarTitle"
          :statistics="statistics"
          :selected-node="sidebarSelectedNode"
          @close="showSidebar = false"
          @highlight-problem="handleHighlightProblem"
          @view-marked-problems="handleViewMarkedProblems"
          @show-filter-panel="showFilterPanel = true"
          @problem-status-changed="handleProblemStatusChanged"
        />

        <ProblemFilterPanel
          v-else
          @close="showFilterPanel = false"
          @applied="handleFiltersApplied"
        />
      </div>
    </div>

    <!-- 进度显示组件（默认最小化为右下角悬浮球） -->
    <ProgressDisplay
      :task-id="taskId"
      :auto-start="true"
      review-type="function"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'

// 导入子组件
import CompareTreePanel from './CompareTreePanel.vue'
import CodeComparePane from './CodeComparePane.vue'
import CodeMapSidebar from './CodeMapSidebar.vue'
import ProblemFilterPanel from './ProblemFilterPanel.vue'

import ProgressDisplay from '../shared/ProgressDisplay.vue'

import { useLineDiff } from './useLineDiff'

import { buildCompareTreeState } from './fullscreen/compareTreeBuilder'
import { useResize } from './fullscreen/useResize'
import { useCommentedCode } from './fullscreen/useCommentedCode'
import { useDataLoad } from './fullscreen/useDataLoad'
import { useFileContent } from './fullscreen/useFileContent'
import { useProblems } from './fullscreen/useProblems'
import { usePairSelection } from './fullscreen/usePairSelection'
import { useTreeIndicators } from './fullscreen/useTreeIndicators'

// 路由
const route = useRoute()
const taskId = computed(() => route.params.taskId)

// 响应式数据
const loading = ref(false)
const showSidebar = ref(true)
const sidebarMode = ref('node')
const sidebarTitle = ref('函数信息 / 问题单')
const highlightedProblem = ref(null)
const markedLocations = ref({ files: [], functions: [], file_function_map: {} })
const showFilterPanel = ref(false)  // 显示过滤面板

// 拖拽相关
const sidebarWidth = ref(500)  // 右侧边栏宽度（从400增加到500，增加1/4）
const treePanelWidth = ref(520)
const collapsedTreeWidth = ref(44)
const treesVisible = ref(true)
const isResizing = ref(false)
const resizeType = ref('') // 'left' or 'right'
const startX = ref(0)
const startWidth = ref(0)

const selectedOldTreeKey = ref('')
const selectedNewTreeKey = ref('')

const codeCompareRef = ref(null)

// 数据
const codeMapData = ref(null)
const statistics = ref(null)

// 变更对比数据
const changesData = ref(null)
const pairIdByKey = ref(new Map())
const funcRowIdByPairId = ref(new Map())
const changeTypeByPairId = ref(new Map())
const fileIdByPairId = ref(new Map())

const selectedFileKey = ref('')
const oldFileText = ref('')
const newFileText = ref('')

// 左侧双树
const oldTreeData = ref([])
const newTreeData = ref([])

// 当前选中的 pair 详情
const selectedPairId = ref(null)
const oldFuncDetail = ref(null)
const newFuncDetail = ref(null)

// 右侧侧栏选中节点（优先新版本函数）
const sidebarSelectedNode = ref(null)

// 计算属性
const oldCodeText = computed(() => String(oldFileText.value || ''))

const newCodeText = computed(() => String(newFileText.value || ''))

const newCodeViewMode = ref('original')

const selectedFuncDetail = computed(() => newFuncDetail.value || oldFuncDetail.value)

const { newCodeTextEffective } = useCommentedCode({
  newCodeViewMode,
  newCodeText,
  selectedFuncDetail,
  sidebarSelectedNode,
  codeMapData,
  selectedFileKey,
  ElMessage
})

const oldCodeMeta = computed(() => (selectedFileKey.value ? selectedFileKey.value : ''))

const newCodeMeta = computed(() => (selectedFileKey.value ? selectedFileKey.value : ''))

const { diffRows, changeRowIndices } = useLineDiff(oldCodeText, newCodeTextEffective)

function resolveHighlightLineInText(text, startLine, endLine) {
  const st = Number(startLine)
  const ed = Number(endLine)
  if (!text) return st
  if (!Number.isFinite(st) || st <= 0) return st
  const lines = String(text).split('\n')
  const maxLine = lines.length
  const limit = Number.isFinite(ed) && ed > 0 ? Math.min(ed, maxLine) : maxLine

  let inBlock = false
  for (let ln = st; ln <= limit; ln++) {
    const raw = lines[ln - 1] ?? ''
    const t = String(raw).trim()
    if (!t) continue

    if (inBlock) {
      const closeIdx = t.indexOf('*/')
      if (closeIdx >= 0) {
        inBlock = false
        const rest = t.slice(closeIdx + 2).trim()
        if (!rest) continue
        if (rest.startsWith('//')) continue
        return ln
      }
      continue
    }

    if (t.startsWith('//')) continue
    if (t.startsWith('/*')) {
      const closeIdx = t.indexOf('*/')
      if (closeIdx >= 0) {
        const rest = t.slice(closeIdx + 2).trim()
        if (!rest) continue
        if (rest.startsWith('//')) continue
        return ln
      }
      inBlock = true
      continue
    }

    if (t.startsWith('*')) continue
    return ln
  }

  return st
}

watch(
  () => newCodeViewMode.value,
  async () => {
    // 切换“源代码/注释后代码”会触发右侧视图重渲染，部分场景会导致滚动回到顶部；这里强制恢复到当前选中函数
    const oldLine = oldFuncDetail.value?.start_line
    const newLine = newFuncDetail.value?.start_line
    const oldHl = resolveHighlightLineInText(oldFileText.value, oldFuncDetail.value?.start_line, oldFuncDetail.value?.end_line)
    const newHl = resolveHighlightLineInText(newFileText.value, newFuncDetail.value?.start_line, newFuncDetail.value?.end_line)

    const targetLine = typeof newHl === 'number' && newHl > 0
      ? newHl
      : (typeof newLine === 'number' ? newLine : (typeof oldHl === 'number' && oldHl > 0 ? oldHl : oldLine))
    if (!targetLine || !codeCompareRef.value) return

    await nextTick()
    codeCompareRef.value?.scrollToLine?.({ oldLine: oldHl || oldLine, newLine: newHl || newLine })
    codeCompareRef.value?.flashRightLine?.({
      rightLineNo: targetLine,
      localLine: 1,
      durationMs: 3000
    })
  }
)

const { problemCountsById, problemBadgeTypesById, functionStartLineByKey } = useTreeIndicators({
  codeMapData,
  oldTreeData
})

// 生命周期
onMounted(async () => {
  await loadCodeMap()
  await loadChanges()
})

// 监听任务ID变化
watch(() => taskId.value, async (newTaskId) => {
  if (newTaskId) {
    oldRepoTree.value = null
    newRepoTree.value = null
    await loadCodeMap()
    await loadChanges()
  }
})

// 监听 changesData 变化
watch(
  () => changesData.value?.items,
  async (items) => {
    buildCompareTrees()
  },
  { deep: false }
)

// 方法
const { loadCodeMap, loadChanges } = useDataLoad({
  taskId,
  axios,
  ElMessage,
  codeMapData,
  statistics,
  changesData,
  buildCompareTrees
})

const oldRepoTree = ref(null)
const newRepoTree = ref(null)

async function loadRepoTreesIfNeeded() {
  if (!taskId.value) return
  if (oldRepoTree.value && newRepoTree.value) return

  const loadOne = async (version) => {
    const res = await axios.get(`/api/codeReview/regressionTest/regression/tree/${taskId.value}`, {
      params: { version }
    })
    return res.data?.root || null
  }

  const [o, n] = await Promise.all([loadOne('old'), loadOne('new')])
  oldRepoTree.value = o
  newRepoTree.value = n
}

function buildAlignedRepoTree(oldRoot, newRoot) {
  const normPath = (p) => String(p || '').replace(/\\/g, '/').replace(/^\/+/, '').replace(/^\.\/(?:\/)?/, '').trim()
  const split = (p) => normPath(p).split('/').filter(Boolean)
  const baseName = (p) => {
    const seg = split(p)
    return seg.length ? seg[seg.length - 1] : ''
  }

  const getWrapperPrefix = (root) => {
    const children = Array.isArray(root?.children) ? root.children : []
    if (children.length !== 1) return { node: root, prefix: '' }
    const only = children[0]
    const t = String(only?.type || '').toLowerCase()
    if (t === 'directory' || t === 'dir') {
      const p = normPath(only?.path)
      return { node: only, prefix: p }
    }
    return { node: root, prefix: '' }
  }

  const { node: oldEffectiveRoot, prefix: oldPrefix } = getWrapperPrefix(oldRoot)
  const { node: newEffectiveRoot, prefix: newPrefix } = getWrapperPrefix(newRoot)

  const ensureDir = (path, oldPresent, newPresent, children) => {
    return {
      id: path ? `dir:${path}` : 'dir:__root__',
      label: path ? baseName(path) : '',
      type: 'dir',
      old_missing: !oldPresent,
      new_missing: !newPresent,
      children: children || []
    }
  }

  const ensureFile = (path, oldPresent, newPresent) => {
    return {
      id: `file:${path}`,
      label: baseName(path),
      type: 'file',
      old_path: oldPresent ? path : '',
      new_path: newPresent ? path : '',
      old_missing: !oldPresent,
      new_missing: !newPresent,
      children: []
    }
  }

  const stripPrefix = (raw, prefix) => {
    if (!prefix) return raw
    if (raw === prefix) return ''
    const withSlash = `${prefix}/`
    if (raw.startsWith(withSlash)) return raw.slice(withSlash.length)
    return raw
  }

  const indexChildren = (node, prefix) => {
    const map = new Map()
    const children = Array.isArray(node?.children) ? node.children : []
    for (const c of children) {
      const raw = normPath(c?.path)
      const p = stripPrefix(raw, prefix)
      if (!p && String(c?.type || '').toLowerCase() !== 'directory' && String(c?.type || '').toLowerCase() !== 'dir') continue
      map.set(p, { node: c, raw })
    }
    return map
  }

  const mergeDir = (dirPath, oldNode, newNode) => {
    const oMap = indexChildren(oldNode, oldPrefix)
    const nMap = indexChildren(newNode, newPrefix)
    const keys = new Set([...oMap.keys(), ...nMap.keys()])

    const children = []
    for (const k of keys) {
      const oWrap = oMap.get(k)
      const nWrap = nMap.get(k)
      const oNode = oWrap?.node
      const nNode = nWrap?.node
      const oType = oNode?.type
      const nType = nNode?.type
      const t = (oType || nType || '').toLowerCase()

      if (t === 'directory' || t === 'dir') {
        children.push(mergeDir(k, oNode, nNode))
      } else {
        const f = ensureFile(k, Boolean(oNode), Boolean(nNode))
        if (oWrap?.raw) f.old_path = oWrap.raw
        if (nWrap?.raw) f.new_path = nWrap.raw
        children.push(f)
      }
    }

    const oldPresent = Boolean(oldNode)
    const newPresent = Boolean(newNode)
    return ensureDir(dirPath, oldPresent, newPresent, children)
  }

  const root = mergeDir('', oldEffectiveRoot, newEffectiveRoot)
  return root.children || []
}

function sortAlignedTree(nodes) {
  const arr = (nodes || []).slice()
  arr.sort((a, b) => {
    const ta = a.type === 'dir' ? 0 : a.type === 'file' ? 1 : 2
    const tb = b.type === 'dir' ? 0 : b.type === 'file' ? 1 : 2
    if (ta !== tb) return ta - tb
    return String(a.label || '').localeCompare(String(b.label || ''))
  })
  for (const n of arr) {
    if (n.type === 'dir') n.children = sortAlignedTree(n.children || [])
  }
  return arr
}

function indexFunctionChildrenByFileId(tree) {
  const map = new Map()
  const walk = (nodes) => {
    for (const n of nodes || []) {
      if (!n) continue
      if (n.type === 'file' && n.id) map.set(n.id, (n.children || []).slice())
      if (n.children && n.children.length) walk(n.children)
    }
  }
  walk(tree || [])
  return map
}

function attachFunctionChildren(alignedTree, fnChildrenByFileId) {
  const walk = (nodes) => {
    for (const n of nodes || []) {
      if (!n) continue
      if (n.type === 'file') {
        const kids = fnChildrenByFileId.get(n.id)
        if (kids && kids.length) n.children = kids
      } else if (n.type === 'dir') {
        walk(n.children || [])
      }
    }
  }
  walk(alignedTree)
}

function applyFileChangeTypes(alignedTree, fileChanges) {
  const changes = fileChanges && typeof fileChanges === 'object' ? fileChanges : {}
  const walk = (nodes) => {
    for (const n of nodes || []) {
      if (!n) continue
      if (n.type === 'file') {
        const key = String(n.id || '').replace(/^file:/, '')
        const ct = changes[key]
        if (ct) n.change_type = ct
      } else if (n.type === 'dir') {
        walk(n.children || [])
      }
    }
  }
  walk(alignedTree)
}

async function buildCompareTrees() {
  const items = changesData.value?.items || []
  const result = buildCompareTreeState(items)

  pairIdByKey.value = result.pairIdByKey
  funcRowIdByPairId.value = result.funcRowIdByPairId
  changeTypeByPairId.value = result.changeTypeByPairId
  fileIdByPairId.value = result.fileIdByPairId

  try {
    await loadRepoTreesIfNeeded()
  } catch {
    oldTreeData.value = result.tree
    newTreeData.value = result.tree
    return
  }

  const aligned = buildAlignedRepoTree(oldRepoTree.value, newRepoTree.value)
  const fnChildrenByFileId = indexFunctionChildrenByFileId(result.tree)
  attachFunctionChildren(aligned, fnChildrenByFileId)
  applyFileChangeTypes(aligned, changesData.value?.file_changes)

  const merged = sortAlignedTree(aligned)
  oldTreeData.value = merged
  newTreeData.value = merged
}

const { findFileNodeById, loadFileTextsByNode, selectFile } = useFileContent({
  taskId,
  axios,
  selectedFileKey,
  oldFileText,
  newFileText,
  oldTreeData
})

const problemsApi = useProblems({
  taskId,
  axios,
  ElMessage,
  sidebarSelectedNode,
  codeMapData,
  oldTreeData,
  loadCodeMap
})

const {
  getProblemStatus,
  handleProblemStatusChanged,
  markSelectedNodeProblemsViewedIfNeeded
} = problemsApi

const { selectPair } = usePairSelection({
  axios,
  ElMessage,
  changeTypeByPairId,
  funcRowIdByPairId,
  fileIdByPairId,
  findFileNodeById,
  loadFileTextsByNode,
  codeCompareRef,
  codeMapData,
  oldFuncDetail,
  newFuncDetail,
  sidebarSelectedNode,
  selectedPairId,
  selectedOldTreeKey,
  selectedNewTreeKey,
  markSelectedNodeProblemsViewedIfNeeded,
  oldFileText,
  newFileText
})

async function handleFiltersApplied() {
  showFilterPanel.value = false
  await problemsApi.handleFiltersApplied()
}

async function handleViewMarkedProblems() {
  await problemsApi.handleViewMarkedProblems(markedLocations, selectPair)
}

function handleHighlightProblem(problemInfo) {
  problemsApi.handleHighlightProblem(problemInfo, highlightedProblem)

  const problem = problemInfo?.problem
  if (!problem || !codeCompareRef.value) return

  const n1 = Number(problem?.line)
  const n2 = Number(problem?.line_no)
  const n3 = Number(problem?.start_line)

  // 只使用明确的行号字段；不要从 description_location 中随便抓数字（章节号/序号会导致总是跳到第1行附近）
  let lineNo = Number.isFinite(n1) && n1 > 0
    ? n1
    : (Number.isFinite(n2) && n2 > 0 ? n2 : (Number.isFinite(n3) && n3 > 0 ? n3 : 0))

  nextTick(async () => {
    const node = problemInfo?.nodeInfo
    const pid = node?.new_pair_id || node?.old_pair_id

    // 先确保中间代码视图切换到对应文件/函数（保证 diffRows 与文本已加载）
    if (pid) {
      await selectPair(pid)
    } else if (node?.type === 'file') {
      const fileId = node?.id
      if (fileId) selectFile(fileId)
    }

    // 若问题没有行号：兜底用当前函数起始行，避免每次都落到第1行
    if (!lineNo) {
      const fnStartFromLoaded = Number(newFuncDetail.value?.start_line || oldFuncDetail.value?.start_line)
      if (Number.isFinite(fnStartFromLoaded) && fnStartFromLoaded > 0) lineNo = fnStartFromLoaded
    }
    if (!lineNo) return

    // 函数片段/注释后代码视图时，右侧行号可能从1开始；localLine 用相对行号确保高亮命中
    const baseStart = Number(newFuncDetail.value?.start_line || oldFuncDetail.value?.start_line)
    const localLine = Number.isFinite(baseStart) && baseStart > 0 ? Math.max(1, lineNo - baseStart + 1) : 1

    await nextTick()
    codeCompareRef.value?.scrollToLine?.({ oldLine: lineNo, newLine: lineNo })
    codeCompareRef.value?.flashRightLine?.({ rightLineNo: lineNo, localLine, durationMs: 3000 })
  })
}

// 拖拽相关方法
const { startLeftResize, startRightResize, toggleTrees } = useResize({
  sidebarWidth,
  treePanelWidth,
  collapsedTreeWidth,
  treesVisible,
  isResizing,
  resizeType,
  startX,
  startWidth
})
</script>

<style>
/* 全局重置，确保没有默认边距 */
.codemap-fullscreen {
  margin: 0 !important;
  padding: 0 !important;
  overflow: hidden;
}

.codemap-fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  flex-direction: column;
  z-index: 9999;
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.codemap-fullscreen .main-content {
  flex: 1;
  display: flex;
  flex-direction: row;
  height: calc(100vh - 80px);
  overflow: hidden;
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.codemap-fullscreen .resize-handle {
  width: 4px;
  height: 100%;
  background: rgba(255, 255, 255, 0.3);
  cursor: col-resize;
  position: relative;
  transition: background-color 0.2s ease;
}

/* 侧边栏标题样式 */
.codemap-fullscreen .sidebar-title {
  margin: 0;
  padding: 10px 15px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  border-bottom: 1px solid #e4e7ed;
  background: #f5f7fa;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .codemap-fullscreen .resize-handle {
    width: 6px;
  }
}

/* 移除小屏幕上下布局，始终保持左右布局 */
@media (max-width: 768px) {
  .codemap-fullscreen .resize-handle {
    width: 8px;
  }
  
  .codemap-fullscreen .resize-handle::after {
    width: 3px;
    height: 50px;
  }
}
</style>