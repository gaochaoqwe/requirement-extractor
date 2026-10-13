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
            v-if="features.length > 0"
            :data="features"
            :props="{ label: 'name', children: 'sub_features' }"
            node-key="id"
            default-expand-all
            @node-click="selectFeatureNode"
            :expand-on-click-node="false"
          >
            <template #default="{ node, data }">
              <div class="feature-tree-node">
                <span class="feature-name">{{ data.name }}</span>
                <el-tag 
                  v-if="data.issues_count > 0" 
                  size="small" 
                  type="danger"
                  class="feature-problem-tag"
                >
                  {{ data.issues_count }}
                </el-tag>
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
        <div class="header-info">
          <h3>代码目录树</h3>
          <div v-if="projectInfo" class="project-meta">
            <el-tag size="small" type="info">项目：{{ projectInfo.name }}</el-tag>
            <el-tag size="small" type="success" class="meta-tag">模式：{{ projectInfo.mode }}</el-tag>
            <el-tag size="small" type="warning" class="meta-tag">路径：{{ projectInfo.root_path }}</el-tag>
          </div>
        </div>
        <span class="hint-text" v-if="selectedFeature">链路顺序：A → B → C</span>
      </div>
        <div class="tree-content">
          <el-tree
            ref="directoryTree"
            :data="directoryTreeData"
            :props="{ label: 'label', children: 'children' }"
            node-key="id"
            @node-click="handleTreeNodeClick"
            default-expand-all
            :expand-on-click-node="false"
          >
            <template #default="{ node, data }">
              <div class="tree-node-content">
                <span class="node-label">
                  <i :class="getNodeIcon(data)" class="node-icon"></i>
                  {{ data.label }}
                </span>
                <span v-if="data.problemCount && data.problemCount > 0" class="problem-count-badge">
                  {{ data.problemCount }}
                </span>
                <span v-if="data.chainOrder" class="chain-order-badge">
                  {{ data.chainOrder }}
                </span>
              </div>
            </template>
          </el-tree>

          <!-- 函数列表面板（点击文件时弹出） -->
          <div v-if="showFunctionList" class="function-list-panel">
            <div class="function-list-header">
              <h4>{{ selectedFileName }} - 函数列表</h4>
              <button class="close-btn" @click="showFunctionList = false">
                <i class="el-icon-close"></i>
            </button>
            </div>
            <div class="function-list-items">
              <div 
                v-for="func in currentFileFunctions"
                :key="func.name"
                class="function-item"
                @click="selectFunction(func)"
              >
                <span class="function-name">{{ func.name }}</span>
                <span v-if="func.chainOrder" class="chain-order-badge">
                  {{ func.chainOrder }}
                </span>
          </div>
        </div>
          </div>
        </div>
      </div>

      <!-- 拖拽分界线2 -->
      <div class="resize-handle" @mousedown="startResize(2, $event)"></div>

      <!-- 第三栏：源代码显示 -->
      <div class="source-code-column">
        <div class="column-header">
          <h3>源代码</h3>
          <span class="file-path" v-if="currentSourceFile">{{ currentSourceFile }}</span>
          </div>
        <div class="source-code-content">
          <div v-if="!currentSourceCode" class="empty-source">
            <i class="el-icon-document"></i>
            <p>请在左侧选择文件或函数</p>
        </div>
          <pre v-else class="source-code"><code ref="codeBlock">{{ currentSourceCode }}</code></pre>
          </div>
        </div>
        
      <!-- 拖拽分界线3 -->
      <div class="resize-handle" @mousedown="startResize(3, $event)"></div>

      <!-- 第四栏：功能介绍 + 问题列表 -->
      <div class="info-problem-column" :style="columnStyle(infoProblemWidth)">
        <!-- 上半部分：功能介绍 -->
        <div class="feature-info-section" :style="{ height: featureInfoHeight + 'px' }">
          <div class="section-header">
            <h3>功能介绍</h3>
          </div>
          <div class="feature-info-content">
            <div v-if="selectedFeature" class="feature-details">
              <div class="info-row">
                <label>功能名称：</label>
                <span>{{ selectedFeature.name }}</span>
              </div>
              <div class="info-row">
                <label>功能描述：</label>
                <p>{{ selectedFeature.description || '暂无描述' }}</p>
              </div>
              <div class="info-row">
                <label>调用链：</label>
                <span class="call-chain">{{ selectedFeature.call_chain || 'main → ...' }}</span>
              </div>
              <div class="info-row">
                <label>相关文件：</label>
                <div class="file-chips">
                  <span 
                    v-for="file in selectedFeature.related_files" 
                    :key="file"
                    class="file-chip"
                  >
                    {{ file }}
                  </span>
                </div>
              </div>
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
            <span class="problem-count" v-if="selectedFeature">
              {{ featureProblems.length }} 个问题
            </span>
      </div>
          <div class="problem-list-content">
            <div v-if="featureProblems.length === 0" class="empty-problems">
              <i class="el-icon-circle-check"></i>
              <p>{{ selectedFeature ? '未发现问题' : '请选择功能模块' }}</p>
            </div>
            <div 
              v-for="(problem, index) in featureProblems"
              :key="problem.id"
              class="problem-item"
              @click="locateProblem(problem)"
            >
              <div class="problem-header">
                <span class="problem-index">{{ index + 1 }}</span>
                <span class="problem-severity" :class="problem.severity">
                  {{ problem.severity }}
                </span>
              </div>
              <div class="problem-title">{{ problem.title }}</div>
              <div class="problem-location">
                <i class="el-icon-location"></i>
                {{ problem.file }}:{{ problem.line }}
              </div>
              <div class="problem-description">{{ problem.description }}</div>
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
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import ProgressDisplay from '../shared/ProgressDisplay.vue'

const route = useRoute()
const taskId = computed(() => route.params.taskId)

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

// 目录树
const directoryTreeData = ref([])
const directoryTree = ref(null)
const projectInfo = ref(null)

// 函数列表面板
const showFunctionList = ref(false)
const selectedFileName = ref('')
const currentFileFunctions = ref([])

// 源代码
const currentSourceFile = ref('')
const currentSourceCode = ref('')
const codeBlock = ref(null)

// 问题列表
const featureProblems = ref([])

// 列宽度（增大宽度，提升可读性）
const featureListWidth = ref(300)  // 从150增大到300
const treeWidth = ref(360)          // 从180增大到360
const infoProblemWidth = ref(400)   // 从200增大到400
const featureInfoHeight = ref(300)

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
    name: feature.name,
    description: feature.description,
    call_chain: feature.call_chain,
    related_files: feature.related_files || [],
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
    const response = await axios.get(`/api/codeReview/regressionTest/progressive/visualization/${taskId.value}`)
    
    if (response.data && response.data.features) {
      // 递归复制整个功能树，保留sub_features和issues_count
      features.value = response.data.features.map(f => copyFeatureWithSubFeatures(f))
    }
  } catch (error) {
    console.error('加载功能列表失败:', error)
    ElMessage.error('加载功能列表失败')
  }
}

// 加载目录树（实际的文件系统结构）
async function loadDirectoryTree() {
  try {
    const response = await axios.get(`/api/codeReview/regressionTest/codemap/${taskId.value}`)
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
  const isDirectory = (node.type || '').toLowerCase() === 'directory' || Array.isArray(node.children)

  const converted = {
    id: nodePath,
    label: nodeName,
    type: isDirectory ? 'directory' : 'file',
    path: node.path || nodePath,
    problemCount: node.problemCount || node.problem_count || 0,
    chainOrder: node.chainOrder || null,
    children: []
  }

  if (node.children && Array.isArray(node.children)) {
    converted.children = node.children
      .map(child => convertProjectNode(child, nodePath))
      .filter(Boolean)
  }

  return converted
}

function formatProjectTree(tree) {
  if (!tree) return []
  const rootNode = convertProjectNode(tree)
  return rootNode ? [rootNode] : []
}

// 选择功能节点（从树形组件点击）
async function selectFeatureNode(data) {
  await selectFeature(data)
}

// 选择功能
async function selectFeature(feature) {
  selectedFeature.value = feature
  
  // 更新目录树的链路顺序标记
  updateChainOrderMarkers(feature)
  
  // 加载功能的问题列表（链路审查问题，按功能过滤）
  try {
    const resp = await axios.get(`/api/codeReview/regressionTest/progressive/problems/${taskId.value}`, {
      params: { feature: feature.name }
    })
    if (resp.data && resp.data.problems) {
      featureProblems.value = resp.data.problems.map(problem => ({
        ...problem,
        severity: problem.issue_level,
        title: problem.issue_name,
        description: problem.description_issue,
        impact: problem.description_impact,
        file: problem.issue_location?.split(':')[0] || '',
        line: Number(problem.issue_location?.split(':')[1]) || null
      }))
    } else {
      featureProblems.value = []
    }
  } catch (e) {
    console.error('加载功能问题失败:', e)
    featureProblems.value = []
  }
}

// 更新链路顺序标记
function updateChainOrderMarkers(feature) {
  // 清除所有标记
  clearChainOrderMarkers(directoryTreeData.value)
  
  // 为相关文件添加链路顺序标记
  if (feature.related_files && feature.related_files.length > 0) {
    feature.related_files.forEach((file, index) => {
      const orderLabel = String.fromCharCode(65 + index) // A, B, C...
      markFileWithChainOrder(directoryTreeData.value, file, orderLabel)
    })
  }
}

// 清除链路顺序标记
function clearChainOrderMarkers(nodes) {
  nodes.forEach(node => {
    node.chainOrder = null
    if (node.children && node.children.length > 0) {
      clearChainOrderMarkers(node.children)
    }
  })
}

// 标记文件的链路顺序
function markFileWithChainOrder(nodes, filePath, orderLabel) {
  for (const node of nodes) {
    if (node.type === 'file' && node.path.includes(filePath)) {
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

// 加载功能的问题列表
async function loadFeatureProblems(featureId) {
  try {
    const response = await axios.get(`/api/codeReview/regressionTest/progressive/problems/${taskId.value}`, {
      params: { feature: featureId }
    })
    
    if (response.data && response.data.problems) {
      featureProblems.value = response.data.problems.map(problem => ({
        ...problem,
        severity: problem.issue_level,
        title: problem.issue_name,
        description: problem.description_issue,
        impact: problem.description_impact,
        file: problem.issue_location?.split(':')[0] || '',
        line: Number(problem.issue_location?.split(':')[1]) || null
      }))
    } else {
      featureProblems.value = []
    }
  } catch (error) {
    console.error('加载问题列表失败:', error)
    featureProblems.value = []
  }
}

// 处理树节点点击
async function handleTreeNodeClick(data) {
  if (data.type === 'file') {
    // 点击文件：显示函数列表并加载源代码
    selectedFileName.value = data.label
    await loadFileFunctions(data.path)
    await loadSourceCode(data.path)
    showFunctionList.value = true
  } else if (data.type === 'directory') {
    // 点击目录：展开/折叠（由 Element Plus Tree 自动处理）
  }
}

// 加载文件的函数列表
async function loadFileFunctions(filePath) {
  try {
    const response = await axios.get(`/api/codeReview/regressionTest/codemap/${taskId.value}`)
    
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
    const url = `/api/codeReview/regressionTest/codemap/${taskId.value}/file/${encodedPath}`
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
  currentSourceFile.value = problem.file
  await loadSourceCode(problem.file, problem.line)
}

// 滚动到指定行
function scrollToLine(lineNumber) {
  // TODO: 实现行号高亮和滚动
  console.log('滚动到行号:', lineNumber)
}

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
    loadFeatures(),
    loadDirectoryTree()
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
  overflow: auto;
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.four-column-layout {
  display: flex;
  height: 100%;
  width: max(100%, calc(150px + 180px + 200px + 200px));
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  overflow-x: auto;
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

/* 功能树节点样式 */
.feature-tree-node {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding-right: 8px;
}

.feature-tree-node .feature-name {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
}

.feature-problem-tag {
  margin-left: 8px;
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
  background: #ffffff;
  border-right: 1px solid #dcdfe6;
  display: flex;
  flex-direction: column;
  min-width: 250px;
  max-width: 600px;
  position: relative;
  flex-shrink: 0;
}

.hint-text {
  font-size: 12px;
  color: #67c23a;
  font-weight: normal;
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

.tree-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  position: relative;
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

.chain-order-badge {
  background: #67c23a;
  color: #ffffff;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
}

.problem-count-badge {
  background: #f56c6c;
  color: #ffffff;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
  margin-left: 4px;
}

/* 函数列表面板 */
.function-list-panel {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  max-height: 50%;
  background: #ffffff;
  border-top: 2px solid #409eff;
  box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
}

.function-list-header {
  padding: 12px 16px;
  background: #ecf5ff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #dcdfe6;
}

.function-list-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.close-btn {
  background: none;
  border: none;
  font-size: 18px;
  color: #909399;
  cursor: pointer;
  padding: 4px;
  transition: color 0.2s;
}

.close-btn:hover {
  color: #303133;
}

.function-list-items {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.function-item {
  padding: 10px 12px;
  margin-bottom: 6px;
  background: #f9fafc;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.function-item:hover {
  background: #ecf5ff;
  border-color: #409eff;
}

.function-name {
  font-size: 13px;
  font-family: 'Consolas', monospace;
}

/* 第三栏：源代码 */
.source-code-column {
  flex: 1 1 auto;
  background: #ffffff;
  border-right: 1px solid #dcdfe6;
  display: flex;
  flex-direction: column;
  min-width: 200px;
}

.file-path {
  font-size: 12px;
  color: #67c23a;
  font-family: 'Consolas', monospace;
}

.source-code-content {
  flex: 1;
  overflow: auto;
  background: #282c34;
}

.empty-source {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
}

.empty-source i {
  font-size: 64px;
  margin-bottom: 16px;
}

.source-code {
  margin: 0;
  padding: 16px;
  background: #282c34;
  color: #abb2bf;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.6;
  overflow: auto;
}

/* 第四栏：功能介绍 + 问题列表 */
.info-problem-column {
  background: #ffffff;
  display: flex;
  flex-direction: column;
  min-width: 300px;
  max-width: 600px;
  flex-shrink: 0;
}

.feature-info-section {
  display: flex;
  flex-direction: column;
  border-bottom: 1px solid #dcdfe6;
  min-height: 150px;
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
  padding: 16px;
}

.feature-details {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-row label {
  font-size: 13px;
  font-weight: 600;
  color: #606266;
}

.info-row span, .info-row p {
  font-size: 13px;
  color: #303133;
  margin: 0;
  line-height: 1.6;
}

.call-chain {
  font-family: 'Consolas', monospace;
  color: #67c23a;
  font-weight: 600;
}

.file-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.file-chip {
  background: #ecf5ff;
  color: #409eff;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-family: 'Consolas', monospace;
}

.empty-info {
  text-align: center;
  padding: 40px 20px;
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
}

.problem-list-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
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

.problem-item {
  padding: 12px;
  margin-bottom: 8px;
  background: #fef0f0;
  border: 1px solid #fbc4c4;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.problem-item:hover {
  border-color: #f56c6c;
  box-shadow: 0 2px 8px rgba(245, 108, 108, 0.2);
}

.problem-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.problem-index {
  width: 24px;
  height: 24px;
  background: #f56c6c;
  color: #ffffff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}

.problem-severity {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.problem-severity.high {
  background: #f56c6c;
  color: #ffffff;
}

.problem-severity.medium {
  background: #e6a23c;
  color: #ffffff;
}

.problem-severity.low {
  background: #67c23a;
  color: #ffffff;
}

.problem-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 6px;
}

.problem-location {
  font-size: 12px;
  color: #909399;
  font-family: 'Consolas', monospace;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.problem-description {
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
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
