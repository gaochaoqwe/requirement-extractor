<template>
  <div class="codemap-fullscreen">
    <!-- 主内容区域 -->
    <div class="main-content">
      <!-- 左侧树形视图栏 -->
      <div class="tree-sidebar-container" :style="{ width: treeSidebarWidth + 'px' }">
        <div class="tree-sidebar-header">
          <!-- 模式切换按钮 -->
          <div class="mode-switcher-buttons">
            <button 
              class="mode-btn"
              :class="{ active: currentMode === 'chain' }"
              @click="switchToMode('chain')"
              title="链路模式：深度审查完整功能链路中的所有函数及其相互调用关系，识别链路级别的业务逻辑问题"
            >
              链路模式
            </button>
            <button 
              class="mode-btn"
              :class="{ active: currentMode === 'file' }"
              @click="switchToMode('file')"
              title="文件模式：按文件维度审查代码，分析单个文件内的业务功能实现和潜在问题"
            >
              文件模式
            </button>
            <button 
              class="mode-btn"
              :class="{ active: currentMode === 'function' }"
              @click="switchToMode('function')"
              title="函数模式：逐个函数进行精细化审查，专注于单个函数的实现逻辑和代码质量"
            >
              函数模式
            </button>
          </div>
        </div>
        <div class="tree-sidebar-content">
          <FileMapTree
            :task-id="taskId"
            :selected-file="selectedFile"
            :tree-data="treeData"
            @file-select="handleFileSelect"
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
        <CodeMapSidebar
          :mode="sidebarMode"
          :title="sidebarTitle"
          :statistics="statistics"
          :selected-node="selectedNode"
          @close="showSidebar = false"
          @highlight-node="highlightNode"
          @highlight-problem="handleHighlightProblem"
        />
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-overlay">
      <el-loading text="正在加载代码地图..." />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'

// 导入子组件
import CodeMapSidebar from './CodeMapSidebar.vue'
import CodeMapGraph from './CodeMapGraph.vue'
import FileMapTree from './FileMapTree.vue'
import CodeMapSourceView from './CodeMapSourceView.vue'

// 路由
const route = useRoute()
const taskId = computed(() => route.params.taskId)

// 模式切换
const currentMode = ref('file')

// 模式切换函数
function switchToMode(mode) {
  console.log('切换到模式:', mode)
  currentMode.value = mode
  
  // 更新URL参数，触发父组件重新渲染
  const newUrl = `/codemap/${taskId.value}?mode=${mode}`
  window.history.pushState({}, '', newUrl)
  
  // 刷新页面以加载新的组件
  window.location.reload()
}

// 响应式数据
const loading = ref(false)
const viewMode = ref('source')
const showSidebar = ref(true)
const sidebarMode = ref('stats')
const sidebarTitle = ref('统计信息')
const selectedNode = ref(null)
const selectedFile = ref(null)
const highlightedProblem = ref(null)

// 拖拽相关
const sidebarWidth = ref(400)
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
    // 文件模式使用现有API，添加mode参数
    const response = await axios.get(`/api/codeReview/regressionTest/codemap/${taskId.value}?mode=file`)
    console.log('文件模式API响应:', response.data)
    
    if (response.data.success) {
      codeMapData.value = response.data.data
      statistics.value = response.data.data.statistics
      
      console.log('文件模式API响应数据:', response.data.data)
      console.log('file_tree数据:', response.data.data.file_tree)
      
      // 构建树形数据
      buildTreeData()
      
      console.log('构建后的treeData:', treeData.value)
      
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

// 移除了搜索、导出、布局刷新等方法

function buildTreeData() {
  if (!codeMapData.value) {
    return
  }
  
  // 文件模式：从 file_tree 构建文件树形结构
  if (codeMapData.value.file_tree && codeMapData.value.file_tree.length > 0) {
    treeData.value = codeMapData.value.file_tree.map(fileNode => ({
      // 保留完整的文件节点数据
      ...fileNode,
      problemCount: fileNode.problemCount || fileNode.problems?.length || 0
    }))
  } 
  // 如果 file_tree 不存在，创建空的文件树
  else {
    treeData.value = []
  }
}

// 处理文件选择
async function handleFileSelect(file) {
  selectedFile.value = file
  console.log('选择文件:', file)
  console.log('文件问题列表:', file.problems)
  console.log('文件源代码长度:', file.source_code?.length || 0)
  
  // 创建一个文件的源码视图节点
  const fileNode = {
    id: file.id || file.name,
    name: file.name,
    type: 'file',
    path: file.path,
    file_path: file.path, // 添加file_path字段供源码视图使用
    source_code: file.source_code || `// 文件: ${file.name}\n// 路径: ${file.path}\n\n// 源代码加载中...`,
    file_function_summary: file.file_function_summary || `文件: ${file.name}`,
    problems: file.problems || [] // 文件相关的业务问题
  }
  
  console.log('创建的文件节点:', fileNode)
  console.log('文件节点源代码:', fileNode.source_code?.substring(0, 200) + '...')
  selectedNode.value = fileNode
  viewMode.value = 'source'
  console.log('设置viewMode为source，selectedNode:', selectedNode.value)
  
  // 更新侧边栏显示文件相关问题
  sidebarMode.value = 'problems'
  sidebarTitle.value = `文件问题 - ${fileNode.name}`
  showSidebar.value = true
}

function handleTreeNodeClick(data) {
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
    
    // 如果函数节点没有源码，尝试获取对应文件的源码
    if (!fullNodeData.source_code && fullNodeData.file_path) {
      const fileNode = codeMapData.value.nodes.find(node => 
        (node.type === 'file' || node.type === 'fpga_file') && node.file_path === fullNodeData.file_path
      )
      if (fileNode && fileNode.source_code) {
        // 将文件的源码赋给函数节点，这样源码视图就能显示并定位到函数
        fullNodeData = {
          ...fullNodeData,
          source_code: fileNode.source_code
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
  position: relative;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(5px);
  transition: all 0.3s ease;
  min-width: 0;
  padding: 20px;
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

/* 模式切换按钮样式 */
.mode-switcher-buttons {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.mode-btn {
  padding: 6px 12px;
  border: 1px solid #d1d9e0;
  background: #ffffff;
  color: #606266;
  cursor: pointer;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  transition: all 0.3s ease;
  min-width: 70px;
  text-align: center;
}

.mode-btn:hover {
  background: #f5f7fa;
  border-color: #c0c4cc;
  color: #409eff;
}

.mode-btn.active {
  background: #409eff;
  border-color: #409eff;
  color: #ffffff;
  box-shadow: 0 2px 4px rgba(64, 158, 255, 0.3);
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