<template>
  <div class="codemap-fullscreen">
    <!-- 主内容区域 -->
    <div class="main-content">
      <!-- 左侧树形视图栏 -->
      <div class="tree-sidebar-container" :style="{ width: treeSidebarWidth + 'px' }">
        <div class="tree-sidebar-header">
          <h3 class="sidebar-title">代码结构</h3>
          <el-button
            type="primary"
            size="small"
            :icon="Download"
            :loading="downloadingCommented"
            @click="downloadAllCommentedCode"
          >
            下载全部注释代码
          </el-button>
        </div>
        <div class="tree-sidebar-content">
          <CodeMapTree
            :tree-data="treeData"
            :selected-node="selectedNode"
            :marked-locations="markedLocations"
            :task-id="taskId"
            @node-click="handleTreeNodeClick"
          />
        </div>
      </div>

      <!-- 左侧拖拽分界线 -->
      <div 
        class="resize-handle left-resize"
        @mousedown="startLeftResize"
      ></div>

      <!-- 中间视图区域 -->
      <div class="main-view-container">
        <!-- 源码视图 -->
        <CodeMapSourceView
          v-show="viewMode === 'source'"
          :selected-node="selectedNode"
          :code-map-data="codeMapData"
          :highlighted-problem="highlightedProblem"
        />
        
        <!-- 代码地图视图 -->
        <CodeMapGraph
          v-show="viewMode === 'graph'"
          ref="codeMapGraph"
          :code-map-data="codeMapData"
          :focused-node="focusedNode"
          @node-selected="selectNode"
          @node-deselected="deselectNode"
        />
      </div>

      <!-- 右侧拖拽分界线 -->
      <div 
        v-show="showSidebar" 
        class="resize-handle right-resize"
        @mousedown="startRightResize"
      ></div>

      <!-- 右侧边栏 -->
      <div v-show="showSidebar" class="sidebar-container" :style="{ width: sidebarWidth + 'px' }">
        <!-- 问题列表视图 -->
        <CodeMapSidebar
          v-if="!showFilterPanel"
          :mode="sidebarMode"
          :title="sidebarTitle"
          :statistics="statistics"
          :selected-node="selectedNode"
          :tree-data="treeData"
          @close="showSidebar = false"
          @highlight-node="highlightNode"
          @highlight-problem="handleHighlightProblem"
          @view-marked-problems="handleViewMarkedProblems"
          @show-filter-panel="showFilterPanel = true"
          @problem-status-changed="handleProblemStatusChanged"
        />
        
        <!-- 过滤设置视图 -->
        <ProblemFilterPanel
          v-else
          @close="showFilterPanel = false"
          @applied="handleFiltersApplied"
        />
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" v-loading="loading" class="loading-overlay" element-loading-text="正在加载代码地图...">
    </div>
    
    <!-- 进度显示组件 -->
    <ProgressDisplay
      :task-id="taskId"
      :auto-start="true"
      @progress-updated="handleProgressUpdated"
      @task-completed="handleTaskCompleted"
      @task-failed="handleTaskFailed"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'
import axios from 'axios'

// 导入子组件
import CodeMapSidebar from './CodeMapSidebar.vue'
import CodeMapGraph from './CodeMapGraph.vue'
import CodeMapTree from './CodeMapTree.vue'
import CodeMapSourceView from './CodeMapSourceView.vue'
import ProblemFilterPanel from './ProblemFilterPanel.vue'
import ProgressDisplay from '../shared/ProgressDisplay.vue'

// 路由
const route = useRoute()
const taskId = computed(() => Number(route.params.taskId))

// 响应式数据
const loading = ref(false)
const viewMode = ref('source')
const showSidebar = ref(true)
const sidebarMode = ref('stats')
const sidebarTitle = ref('统计信息')
const selectedNode = ref(null)
const highlightedProblem = ref(null)
const markedLocations = ref({ files: [], functions: [], file_function_map: {} })
const showFilterPanel = ref(false)  // 显示过滤面板
const downloadingCommented = ref(false)  // 下载全部注释代码中
let eventSource = null  // SSE连接

// 拖拽相关
const sidebarWidth = ref(500)  // 右侧边栏宽度（从400增加到500，增加1/4）
const treeSidebarWidth = ref(350)
const isResizing = ref(false)
const resizeType = ref('') // 'left' or 'right'
const startX = ref(0)
const startWidth = ref(0)

// 聚焦节点
const focusedNode = ref(null)

// 组件引用
const codeMapGraph = ref(null)

// 数据
const codeMapData = ref(null)
const statistics = ref(null)
const treeData = ref([])

// 生命周期
onMounted(async () => {
  await loadCodeMap()
  setupSSE()
})

// 组件卸载时关闭SSE连接
import { onBeforeUnmount } from 'vue'
onBeforeUnmount(() => {
  if (eventSource) {
    eventSource.close()
  }
})

// 监听任务ID变化
watch(() => taskId.value, async (newTaskId) => {
  if (newTaskId) {
    await loadCodeMap()
  }
})

// 监听侧边栏状态变化，重新调整图形
watch(() => showSidebar.value, () => {
  nextTick(() => {
    setTimeout(() => {
      if (codeMapGraph.value && viewMode.value === 'graph') {
        codeMapGraph.value.resizeCytoscape()
      }
    }, 300)
  })
})

// 监听视图模式变化，当切换到图形视图时初始化Cytoscape
watch(() => viewMode.value, (newMode) => {
  if (newMode === 'graph' && codeMapData.value) {
    nextTick(() => {
      setTimeout(() => {
        if (codeMapGraph.value) {
          console.log('Switching to graph view, initializing Cytoscape...')
          codeMapGraph.value.forceReinit()
        }
      }, 300)
    })
  }
})

// 方法
async function loadCodeMap() {
  if (!taskId.value) return
  
  loading.value = true
  try {
    const response = await axios.get(`/api/codeReview/codemap/${taskId.value}`)
    if (response.data.success) {
      codeMapData.value = response.data.data
      statistics.value = response.data.data.statistics
      
      // 构建树形数据
      buildTreeData()
      
      // 确保图形组件在数据加载后重新初始化
      await nextTick()
      setTimeout(() => {
        if (codeMapGraph.value) {
          codeMapGraph.value.forceReinit()
        }
      }, 1000)
      

      
      ElMessage.success('代码地图加载成功')
    } else {
      ElMessage.error('加载代码地图失败')
    }
  } catch (error) {
    console.error('加载代码地图失败:', error)
    ElMessage.error('加载代码地图失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

function selectNode(nodeData) {
  selectedNode.value = nodeData
  sidebarMode.value = 'node'
  sidebarTitle.value = `节点详情 - ${nodeData.name}`
  showSidebar.value = true
}

function deselectNode() {
  selectedNode.value = null
  sidebarMode.value = 'stats'
  sidebarTitle.value = '统计信息'
}

function highlightNode(nodeId) {
  if (codeMapGraph.value) {
    codeMapGraph.value.highlightNode(nodeId)
  }
}

function handleHighlightProblem(problemInfo) {
  console.log('收到问题高亮请求:', problemInfo)
  
  // 确保切换到源码视图
  viewMode.value = 'source'
  
  // 设置高亮问题信息
  highlightedProblem.value = problemInfo
  
  // 如果当前选择的节点不是问题所在的节点，切换节点
  if (problemInfo.nodeInfo && selectedNode.value?.id !== problemInfo.nodeInfo.id) {
    selectedNode.value = problemInfo.nodeInfo
  }
}

// 设置SSE连接用于实时状态更新
function setupSSE() {
  if (!taskId.value) return
  
  try {
    // 关闭已有连接
    if (eventSource) {
      eventSource.close()
    }
    
    // 创建新的SSE连接
    eventSource = new EventSource(`/api/codeReview/${taskId.value}/problems/status/stream`)
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.error) {
          console.error('SSE错误:', data.error)
          return
        }
        
        // 更新统计信息（可选）
        console.log('问题状态更新:', data.statistics)
        
        // 可以在这里添加UI提示，告知用户状态已更新
      } catch (error) {
        console.error('解析SSE数据失败:', error)
      }
    }
    
    eventSource.onerror = (error) => {
      console.error('SSE连接错误:', error)
      // 不自动重连，避免频繁请求
    }
    
    console.log('SSE连接已建立')
  } catch (error) {
    console.error('设置SSE失败:', error)
  }
}

// 处理问题状态变化
function handleProblemStatusChanged() {
  // 重新构建树形数据以更新徽章颜色
  console.log('问题状态已更改，重新构建树形数据')
  
  // 同步更新 codeMapData 中的问题状态
  if (selectedNode.value && selectedNode.value.problems && codeMapData.value) {
    // 更新 nodes 中的对应节点
    if (codeMapData.value.nodes) {
      const nodeIndex = codeMapData.value.nodes.findIndex(n => n.id === selectedNode.value.id)
      if (nodeIndex !== -1) {
        codeMapData.value.nodes[nodeIndex].problems = selectedNode.value.problems
      }
    }
    
    // 更新 file_tree 中的对应节点
    if (codeMapData.value.file_tree) {
      codeMapData.value.file_tree.forEach(fileNode => {
        if (fileNode.id === selectedNode.value.id) {
          fileNode.problems = selectedNode.value.problems
        }
        if (fileNode.children) {
          fileNode.children.forEach(funcNode => {
            if (funcNode.id === selectedNode.value.id) {
              funcNode.problems = selectedNode.value.problems
            }
          })
        }
      })
    }
    
    // 更新 problems 列表中的问题状态
    if (codeMapData.value.problems) {
      selectedNode.value.problems.forEach(updatedProblem => {
        const problemIndex = codeMapData.value.problems.findIndex(p => p.id === updatedProblem.id)
        if (problemIndex !== -1) {
          codeMapData.value.problems[problemIndex].problem_status = updatedProblem.problem_status
        }
      })
    }
  }
  
  buildTreeData()
}

// 处理过滤规则应用
async function handleFiltersApplied() {
  showFilterPanel.value = false
  ElMessage.success('过滤规则已应用')
  
  // 重新加载代码地图以反映过滤后的状态
  await loadCodeMap()
}

// 取源码压缩包名（不含扩展名），用于生成下载包名
function getCodePackageName() {
  const pkgName = codeMapData.value?.project?.name
  if (!pkgName) return ''

  const base = String(pkgName).replace(/\\/g, '/').split('/').filter(Boolean).pop() || ''
  const dotIndex = base.lastIndexOf('.')
  return dotIndex > 0 ? base.slice(0, dotIndex) : base
}

// 从响应头 Content-Disposition 中解析文件名（优先 filename*=UTF-8''）
function parseFilenameFromDisposition(disposition) {
  if (!disposition) return ''

  const utf8Match = /filename\*=UTF-8''([^;]+)/i.exec(disposition)
  if (utf8Match && utf8Match[1]) {
    try {
      return decodeURIComponent(utf8Match[1].trim())
    } catch (e) {
      return utf8Match[1].trim()
    }
  }

  const asciiMatch = /filename="?([^";]+)"?/i.exec(disposition)
  return asciiMatch && asciiMatch[1] ? asciiMatch[1].trim() : ''
}

// 下载全部注释代码（后端打包为 ZIP，保留原目录结构）
async function downloadAllCommentedCode() {
  if (!taskId.value) return

  downloadingCommented.value = true
  try {
    const response = await axios.get(
      `/api/codeReview/download_commented_code/${taskId.value}`,
      { responseType: 'blob' }
    )

    const blob = new Blob([response.data], { type: 'application/zip' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    // 包名与源码压缩包保持一致：源码包名-commented.zip
    // 优先用代码地图里的源码包名，其次用后端响应头中的文件名，最后回退到任务ID
    const pkgName = getCodePackageName()
    const headerName = parseFilenameFromDisposition(response.headers?.['content-disposition'])
    link.download = pkgName
      ? `${pkgName}-commented.zip`
      : (headerName || `commented_code_task_${taskId.value}.zip`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('注释代码下载成功')
  } catch (error) {
    console.error('下载全部注释代码失败:', error)

    // 后端出错时返回的是 JSON，但 responseType=blob，需要先解析
    let detail = error.message
    if (error.response?.data instanceof Blob) {
      try {
        const text = await error.response.data.text()
        try {
          detail = JSON.parse(text).detail || text
        } catch (parseErr) {
          detail = text
        }
      } catch (readErr) {
        // 忽略，保留默认错误信息
      }
    } else if (error.response?.data?.detail) {
      detail = error.response.data.detail
    }

    ElMessage.error('下载失败: ' + detail)
  } finally {
    downloadingCommented.value = false
  }
}

// 处理查看标记问题
async function handleViewMarkedProblems() {
  try {
    // 获取标记问题的位置信息
    const response = await axios.get(`/api/codeReview/${taskId.value}/marked_problems/locations`, {
      params: { analysis_type: 'function' }
    })
    
    if (response.data.success) {
      const locations = response.data.data
      
      // 更新标记位置数据，触发树组件重新渲染
      markedLocations.value = locations
      
      ElMessage.success({
        message: `找到 ${locations.files.length} 个文件，${locations.functions.length} 个函数包含已标记问题`,
        duration: 3000
      })
      
      // 如果有标记的函数，聚焦到第一个
      highlightMarkedItemsInTree(locations)
    }
  } catch (error) {
    console.error('获取标记位置失败:', error)
    ElMessage.error('获取标记位置失败')
  }
}

// 在树形视图中高亮显示标记的文件和函数
function highlightMarkedItemsInTree(locations) {
  // 聚焦到第一个标记的函数
  if (locations.functions && locations.functions.length > 0) {
    const firstFunction = locations.functions[0]
    // 在树中查找这个函数节点
    const functionNode = codeMapData.value.nodes.find(node => 
      node.type === 'function' && node.name === firstFunction
    )
    if (functionNode) {
      handleTreeNodeClick(functionNode)
    }
  }
}

// 移除了搜索、导出、布局刷新等方法

function buildTreeData() {
  if (!codeMapData.value) {
    return
  }
  
  // 先尝试从 file_tree 构建
  if (codeMapData.value.file_tree && codeMapData.value.file_tree.length > 0) {
    treeData.value = codeMapData.value.file_tree.map(fileNode => {
      // 构建子函数列表并计算每个函数的问题数
      const children = fileNode.children?.map(funcNode => ({
        // 保留完整的函数节点数据
        ...funcNode,
        problemCount: funcNode.problems?.length || 0
      })) || []
      
      // 计算文件的总问题数 = 文件自身问题 + 所有子函数问题之和
      const fileProblemCount = fileNode.problems?.length || 0
      const childrenProblemCount = children.reduce((sum, child) => sum + child.problemCount, 0)
      const totalProblemCount = fileProblemCount + childrenProblemCount
      
      return {
        // 保留完整的节点数据
        ...fileNode,
        problemCount: totalProblemCount,
        children: children
      }
    })
  } 
  // 如果 file_tree 不存在，从 nodes 和 edges 构建
  else if (codeMapData.value.nodes && codeMapData.value.nodes.length > 0) {
    const nodes = codeMapData.value.nodes
    const fileNodes = nodes.filter(node => node.type === 'file' || node.type === 'fpga_file')
    const functionNodes = nodes.filter(node => node.type === 'function' || node.type === 'fpga_module')
    
    treeData.value = fileNodes.map(fileNode => {
      // 构建子函数列表并计算每个函数的问题数
      const children = functionNodes
        .filter(funcNode => funcNode.file_path === fileNode.file_path)
        // 按行号排序，确保函数按代码中的顺序显示
        .sort((a, b) => {
          const lineA = a.line || a.start_line || 0
          const lineB = b.line || b.start_line || 0
          return lineA - lineB
        })
        .map(funcNode => ({
          // 保留完整的函数节点数据
          ...funcNode,
          problemCount: funcNode.problems?.length || 0
        }))
      
      // 计算文件的总问题数 = 文件自身问题 + 所有子函数问题之和
      const fileProblemCount = fileNode.problems?.length || 0
      const childrenProblemCount = children.reduce((sum, child) => sum + child.problemCount, 0)
      const totalProblemCount = fileProblemCount + childrenProblemCount
      
      return {
        // 保留完整的文件节点数据
        ...fileNode,
        problemCount: totalProblemCount,
        children: children
      }
    })
  }
}

async function handleTreeNodeClick(data) {
  // 如果之前有选中的节点，先批量更新其未标记的新问题为已查看状态
  if (selectedNode.value && selectedNode.value.problems && selectedNode.value.problems.length > 0) {
    const newProblemsToUpdate = selectedNode.value.problems.filter(p => p.problem_status === 1)
    if (newProblemsToUpdate.length > 0) {
      await batchUpdateProblemsToViewed(newProblemsToUpdate)
    }
  }
  
  // 如果点击的是树形视图中的节点，需要从原始数据中找到完整的节点信息
  let fullNodeData = data
  
  // 如果树形视图的数据不完整，从原始节点数据中查找
  if (codeMapData.value && codeMapData.value.nodes) {
    const foundNode = codeMapData.value.nodes.find(node => node.id === data.id)
    if (foundNode) {
      fullNodeData = foundNode
    }
  }
  
  // 如果点击的是函数节点或FPGA模块节点，切换到源码视图
  if (data.type === 'function' || data.type === 'fpga_module') {
    viewMode.value = 'source'
    
    // 获取函数所在文件的完整源码，用于显示整个文件并定位到函数位置
    if (fullNodeData.file_path) {
      const fileNode = codeMapData.value.nodes.find(node => 
        (node.type === 'file' || node.type === 'fpga_file') && node.file_path === fullNodeData.file_path
      )
      if (fileNode && fileNode.source_code) {
        // 将文件的完整源码赋给函数节点，保留函数的行号和其他信息用于定位
        fullNodeData = {
          ...fullNodeData,
          source_code: fileNode.source_code,  // 使用文件的完整源码
          // 保留函数自己的 line 和 end_line 用于定位和高亮
        }
      }
    }
  }
  
  // 选中节点显示详情
  selectNode(fullNodeData)
  
  // 设置聚焦节点，让代码地图聚焦到该节点
  focusedNode.value = fullNodeData
  
  // 通知代码地图组件聚焦到该节点
  if (codeMapGraph.value) {
    codeMapGraph.value.focusOnNode(data.id)
  }
}

// 批量更新问题为已查看状态
async function batchUpdateProblemsToViewed(problems) {
  try {
    const problemIds = problems.map(p => p.id)
    const response = await axios.patch(
      `/api/codeReview/${taskId.value}/problems/status`,
      {
        problem_ids: problemIds,
        status: 2  // 已查看
      }
    )
    
    if (response.data.success) {
      // 更新本地状态
      problems.forEach(p => {
        p.problem_status = 2
      })
      
      // 触发状态变化处理
      handleProblemStatusChanged()
    }
  } catch (error) {
    console.error('批量更新问题状态失败:', error)
  }
}

// 拖拽相关方法
function startLeftResize(e) {
  isResizing.value = true
  resizeType.value = 'left'
  startX.value = e.clientX
  startWidth.value = treeSidebarWidth.value
  
  document.addEventListener('mousemove', doResize)
  document.addEventListener('mouseup', stopResize)
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

function startRightResize(e) {
  isResizing.value = true
  resizeType.value = 'right'
  startX.value = e.clientX
  startWidth.value = sidebarWidth.value
  
  document.addEventListener('mousemove', doResize)
  document.addEventListener('mouseup', stopResize)
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

function doResize(e) {
  if (!isResizing.value) return
  
  const deltaX = e.clientX - startX.value
  
  if (resizeType.value === 'left') {
    // 左侧树形视图栏
    const newWidth = startWidth.value + deltaX
    if (newWidth >= 200 && newWidth <= 500) {
      treeSidebarWidth.value = newWidth
    }
  } else if (resizeType.value === 'right') {
    // 右侧统计信息栏
    const newWidth = startWidth.value - deltaX
    if (newWidth >= 250 && newWidth <= 800) {
      sidebarWidth.value = newWidth
    }
  }
  
  // 通知图形组件重新调整大小
  nextTick(() => {
    setTimeout(() => {
      if (codeMapGraph.value && viewMode.value === 'graph') {
        codeMapGraph.value.resizeCytoscape()
      }
    }, 50)
  })
}

function stopResize() {
  isResizing.value = false
  resizeType.value = ''
  document.removeEventListener('mousemove', doResize)
  document.removeEventListener('mouseup', stopResize)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

// 进度显示相关方法
function handleProgressUpdated(progressData) {
  console.log('进度更新:', progressData)
  // 可以在这里添加其他进度更新的处理逻辑
}

function handleTaskCompleted(taskData) {
  console.log('任务完成:', taskData)
  // 任务完成后重新加载代码地图以获取最新数据
  loadCodeMap()
}

function handleTaskFailed(taskData) {
  console.log('任务失败:', taskData)
  ElMessage.error('代码审查任务失败')
}
</script>

<style>
/* 全局重置，确保没有默认边距 */
body, html {
  margin: 0 !important;
  padding: 0 !important;
  overflow: hidden;
}
</style>

<style scoped>
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

.main-content {
  flex: 1;
  display: flex;
  flex-direction: row;
  height: calc(100vh - 80px);
  overflow: hidden;
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.tree-sidebar-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 0;
  margin: 0;
  box-sizing: border-box;
  min-width: 200px;
  max-width: 500px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-right: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 2px 0 20px rgba(0, 0, 0, 0.1);
}

.tree-sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #eee;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.tree-sidebar-header h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 18px;
  font-weight: 600;
}

.tree-sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 0;
}

.sidebar-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 0;
  margin: 0;
  box-sizing: border-box;
  min-width: 250px;
  max-width: 800px;
}

.resize-handle {
  width: 4px;
  height: 100%;
  background: rgba(255, 255, 255, 0.3);
  cursor: col-resize;
  position: relative;
  transition: background-color 0.2s ease;
}

.resize-handle:hover {
  background: rgba(255, 255, 255, 0.5);
}

.resize-handle::after {
  content: '';
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 2px;
  height: 40px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 1px;
}

.main-view-container {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  position: relative;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(5px);
  transition: all 0.3s ease;
  padding: 20px;
  overflow: hidden;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

/* 侧边栏标题样式 */
.sidebar-title {
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
  .resize-handle {
    width: 6px;
  }
}

/* 移除小屏幕上下布局，始终保持左右布局 */
@media (max-width: 768px) {
  .resize-handle {
    width: 8px;
  }
  
  .resize-handle::after {
    width: 3px;
    height: 50px;
      }
  }
</style> 