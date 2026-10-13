<template>
  <div class="codemap-fullscreen">
    <!-- 主内容区域 -->
    <div class="main-content">
      <!-- 最左侧任务列表栏 -->
      <div class="task-sidebar-container" :style="{ width: taskSidebarWidth + 'px' }">
        <div class="task-sidebar-header">
          <h3>任务列表</h3>
        </div>
        <div class="task-sidebar-content">
          <CodeMapTaskList
            :task-data="taskData"
            :selected-task="selectedTask"
            @task-click="handleTaskClick"
          />
        </div>
      </div>

      <!-- 任务列表拖拽分界线 -->
      <div 
        class="resize-handle task-resize"
        @mousedown="startTaskResize"
      ></div>

      <!-- 上一版本代码目录树 -->
      <div class="version-tree-container" :style="{ width: oldVersionTreeWidth + 'px' }">
        <div class="version-tree-header">
          <h3>上一版本代码</h3>
          <el-tag type="info" size="small">{{ oldVersionInfo.version || 'v1.0' }}</el-tag>
        </div>
        <div class="version-tree-content">
          <CodeMapVersionTree
            :tree-data="oldVersionTreeData"
            :selected-file="selectedOldFile"
            :version="'old'"
            @file-click="handleOldFileClick"
          />
        </div>
      </div>

      <!-- 上一版本拖拽分界线 -->
      <div 
        class="resize-handle old-version-resize"
        @mousedown="startOldVersionResize"
      ></div>

      <!-- 当前版本代码目录树 -->
      <div class="version-tree-container" :style="{ width: newVersionTreeWidth + 'px' }">
        <div class="version-tree-header">
          <h3>当前版本代码</h3>
          <el-tag type="success" size="small">{{ newVersionInfo.version || 'v2.0' }}</el-tag>
        </div>
        <div class="version-tree-content">
          <CodeMapVersionTree
            :tree-data="newVersionTreeData"
            :selected-file="selectedNewFile"
            :version="'new'"
            @file-click="handleNewFileClick"
          />
        </div>
      </div>

      <!-- 当前版本拖拽分界线 -->
      <div 
        class="resize-handle new-version-resize"
        @mousedown="startNewVersionResize"
      ></div>

      <!-- 右侧问题显示栏 -->
      <div class="issue-sidebar-container" :style="{ width: issueSidebarWidth + 'px' }">
        <CodeMapIssueSidebar
          :selected-task="selectedTask"
          :filtered-problems="filteredProblems"
          :selected-old-file="selectedOldFile"
          :selected-new-file="selectedNewFile"
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
import CodeMapTaskList from './CodeMapTaskList.vue'
import CodeMapVersionTree from './CodeMapVersionTree.vue'
import CodeMapIssueSidebar from './CodeMapIssueSidebar.vue'

// 路由
const route = useRoute()
const taskId = computed(() => route.params.taskId)

// 响应式数据
const loading = ref(false)

// 拖拽相关
const taskSidebarWidth = ref(250)
const oldVersionTreeWidth = ref(300)
const newVersionTreeWidth = ref(300)
const issueSidebarWidth = ref(400)
const isResizing = ref(false)
const resizeType = ref('') // 'task', 'old-version', 'new-version'
const startX = ref(0)
const startWidth = ref(0)


// 数据
const taskData = ref(null)
const selectedTask = ref(null)
const filteredProblems = ref([])
const oldVersionTreeData = ref([])
const newVersionTreeData = ref([])
const oldVersionInfo = ref({})
const newVersionInfo = ref({})
const selectedOldFile = ref(null)
const selectedNewFile = ref(null)
const highlightedProblem = ref(null)

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


// 方法
async function loadCodeMap() {
  if (!taskId.value) return
  
  loading.value = true
  try {
    console.log('开始加载代码地图，任务ID:', taskId.value)
    const response = await axios.get(`/api/codeReview/regression/codemap/${taskId.value}`)
    console.log('代码地图API响应:', response.data)
    
    if (response.data.success) {
      const data = response.data.data
      taskData.value = data.task_data
      filteredProblems.value = data.filtered_problems || []
      
      // 加载版本信息
      oldVersionInfo.value = data.old_version_info || { version: 'v1.0' }
      newVersionInfo.value = data.new_version_info || { version: 'v2.0' }
      
      // 构建版本树数据
      buildVersionTreeData(data)
      
      console.log('任务数据:', taskData.value)
      console.log('版本树数据:', { old: oldVersionTreeData.value, new: newVersionTreeData.value })
      
      ElMessage.success('代码地图加载成功')
    } else {
      console.error('代码地图加载失败:', response.data)
      ElMessage.error('加载代码地图失败')
    }
  } catch (error) {
    console.error('加载代码地图失败:', error)
    console.error('错误详情:', error.response?.data)
    ElMessage.error('加载代码地图失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

function buildVersionTreeData(data) {
  // 构建旧版本树数据
  if (data.old_version_tree) {
    oldVersionTreeData.value = buildTreeStructure(data.old_version_tree)
  }
  
  // 构建新版本树数据
  if (data.new_version_tree) {
    newVersionTreeData.value = buildTreeStructure(data.new_version_tree)
  }
}

function buildTreeStructure(treeData) {
  if (!treeData || !Array.isArray(treeData)) {
    return []
  }
  
  return treeData.map(node => ({
    id: node.id || node.path,
    name: node.name || getFileNameFromPath(node.path),
    path: node.path,
    type: node.type || 'file',
    isDirectory: node.isDirectory || false,
    children: node.children ? buildTreeStructure(node.children) : [],
    modified: node.modified || false,
    added: node.added || false,
    deleted: node.deleted || false
  }))
}

function getFileNameFromPath(path) {
  if (!path) return ''
  return path.split('/').pop() || path
}


function handleTaskClick(task) {
  selectedTask.value = task
  filteredProblems.value = task.problems || []
  
  console.log(`选择任务: ${task.task_name}, 相关问题数: ${filteredProblems.value.length}`)
}

function handleOldFileClick(fileData) {
  selectedOldFile.value = fileData
  console.log('选择旧版本文件:', fileData)
}

function handleNewFileClick(fileData) {
  selectedNewFile.value = fileData
  console.log('选择新版本文件:', fileData)
}

function handleHighlightProblem(problemInfo) {
  console.log('收到问题高亮请求:', problemInfo)
  highlightedProblem.value = problemInfo
}

function startTaskResize(e) {
  isResizing.value = true
  resizeType.value = 'task'
  startX.value = e.clientX
  startWidth.value = taskSidebarWidth.value
  
  document.addEventListener('mousemove', doResize)
  document.addEventListener('mouseup', stopResize)
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

function startOldVersionResize(e) {
  isResizing.value = true
  resizeType.value = 'old-version'
  startX.value = e.clientX
  startWidth.value = oldVersionTreeWidth.value
  
  document.addEventListener('mousemove', doResize)
  document.addEventListener('mouseup', stopResize)
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

function startNewVersionResize(e) {
  isResizing.value = true
  resizeType.value = 'new-version'
  startX.value = e.clientX
  startWidth.value = newVersionTreeWidth.value
  
  document.addEventListener('mousemove', doResize)
  document.addEventListener('mouseup', stopResize)
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

function doResize(e) {
  if (!isResizing.value) return
  
  const deltaX = e.clientX - startX.value
  
  if (resizeType.value === 'task') {
    const newWidth = startWidth.value + deltaX
    if (newWidth >= 200 && newWidth <= 400) {
      taskSidebarWidth.value = newWidth
    }
  } else if (resizeType.value === 'old-version') {
    const newWidth = startWidth.value + deltaX
    if (newWidth >= 250 && newWidth <= 500) {
      oldVersionTreeWidth.value = newWidth
    }
  } else if (resizeType.value === 'new-version') {
    const newWidth = startWidth.value + deltaX
    if (newWidth >= 250 && newWidth <= 500) {
      newVersionTreeWidth.value = newWidth
    }
  }
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

.task-sidebar-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 0;
  margin: 0;
  box-sizing: border-box;
  min-width: 200px;
  max-width: 400px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-right: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 2px 0 20px rgba(0, 0, 0, 0.1);
}

.task-sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #eee;
  background: rgba(255, 255, 255, 0.8);
}

.task-sidebar-header h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 18px;
  font-weight: 600;
}

.task-sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 0;
}

.version-tree-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 0;
  margin: 0;
  box-sizing: border-box;
  min-width: 250px;
  max-width: 500px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-right: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 2px 0 20px rgba(0, 0, 0, 0.1);
}

.version-tree-header {
  padding: 15px 20px;
  border-bottom: 1px solid #eee;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.version-tree-header h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 16px;
  font-weight: 600;
}

.version-tree-content {
  flex: 1;
  overflow-y: auto;
  padding: 0;
}

.issue-sidebar-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 0;
  margin: 0;
  box-sizing: border-box;
  min-width: 350px;
  max-width: 600px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: -2px 0 20px rgba(0, 0, 0, 0.1);
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