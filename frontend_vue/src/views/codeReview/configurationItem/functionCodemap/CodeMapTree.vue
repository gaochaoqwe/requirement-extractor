<template>
  <div class="tree-view">
    <!-- 工具栏 -->
    <div class="tree-toolbar">
      <div class="toolbar-left">
        <h3>代码结构</h3>
      </div>
      <div class="toolbar-right">
        <el-button @click="expandAll" :icon="Plus" size="small" type="primary" text>
          全部展开
        </el-button>
        <el-button @click="collapseAll" :icon="Minus" size="small" type="primary" text>
          全部折叠
        </el-button>
      </div>
    </div>
    
    <div v-if="!treeData || treeData.length === 0" class="no-data">
      <el-empty description="暂无数据" />
    </div>
    <div v-else class="tree-container">
      <el-tree
        ref="treeRef"
        :data="treeData"
        :props="treeProps"
        node-key="id"
        :expand-on-click-node="false"
        @node-click="handleTreeNodeClick"
        :default-expand-all="false"
        :default-expanded-keys="defaultExpandedKeys"
        :highlight-current="true"
        :current-node-key="currentNodeKey"
      >
        <template #default="{ data }">
          <div class="tree-node">
            <div class="node-icon">
              <el-icon v-if="data.type === 'file'" color="#3498db"><Document /></el-icon>
              <el-icon v-else-if="data.type === 'function'" color="#2ecc71"><Operation /></el-icon>
              <el-icon v-else-if="data.type === 'fpga_file'" color="#9b59b6"><Document /></el-icon>
              <el-icon v-else-if="data.type === 'fpga_module'" color="#e67e22"><Operation /></el-icon>
            </div>
            <div class="node-content">
              <span class="node-name">{{ data.name }}</span>
              <div class="node-meta">
                <el-tag 
                  :type="getNodeTagType(data.type)" 
                  size="small"
                  effect="plain"
                >
                  {{ getNodeTypeLabel(data.type) }}
                </el-tag>
                <el-badge 
                  v-if="data.problemCount > 0" 
                  :value="data.problemCount" 
                  :type="getProblemBadgeType(data)"
                  class="problem-badge"
                  :class="getProblemBadgeClass(data)"
                />
                <el-tag 
                  v-if="isNodeMarked(data)" 
                  type="primary" 
                  size="small"
                  effect="dark"
                  class="marked-tag"
                >
                  <el-icon><Star /></el-icon>
                  已标记
                </el-tag>
              </div>
            </div>
          </div>
        </template>
      </el-tree>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { Document, Operation, Plus, Minus, Star } from '@element-plus/icons-vue'
import axios from 'axios'

// Props
const props = defineProps({
  treeData: {
    type: Array,
    default: () => []
  },
  selectedNode: {
    type: Object,
    default: null
  },
  markedLocations: {
    type: Object,
    default: () => ({ files: [], functions: [], file_function_map: {} })
  },
  taskId: {
    type: [String, Number],
    default: null
  }
})

// 进度相关
const taskProgress = ref(null)
let progressTimer = null

// Emits
const emit = defineEmits(['nodeClick'])

// 组件引用
const treeRef = ref(null)

// 树形视图配置
const treeProps = {
  children: 'children',
  label: 'name'
}

// 默认展开的节点（不展开任何节点，所有函数都折叠）
const defaultExpandedKeys = computed(() => {
  return [] // 默认全部折叠
})

// 当前选中节点的key
const currentNodeKey = computed(() => {
  return props.selectedNode ? props.selectedNode.id : null
})

// 监听选中节点变化，自动展开到该节点
watch(() => props.selectedNode, async (newNode) => {
  if (newNode && treeRef.value) {
    await nextTick()
    // 设置当前选中节点
    if (treeRef.value.setCurrentKey) {
      treeRef.value.setCurrentKey(newNode.id)
    }
  }
}, { immediate: true })

// 方法
function handleTreeNodeClick(data) {
  emit('nodeClick', data)
}

// 检查节点是否有标记问题
function isNodeMarked(node) {
  if (!props.markedLocations) return false
  
  if (node.type === 'file' || node.type === 'fpga_file') {
    // 检查文件是否在标记列表中
    // 可能需要匹配file_path或name
    const fileName = node.name
    const filePath = node.file_path
    const files = props.markedLocations.files || []
    
    // 尝试多种匹配方式
    const isMarked = files.some(markedFile => {
      return markedFile === fileName || 
             markedFile === filePath ||
             fileName.includes(markedFile) ||
             markedFile.includes(fileName)
    })
    
    console.log('检查文件是否标记:', fileName, filePath, '标记列表:', files, '结果:', isMarked)
    return isMarked
  } else if (node.type === 'function' || node.type === 'fpga_module') {
    // 检查函数是否在标记列表中
    const functions = props.markedLocations.functions || []
    const isMarked = functions.includes(node.name)
    console.log('检查函数是否标记:', node.name, '标记列表:', functions, '结果:', isMarked)
    return isMarked
  }
  return false
}

function getNodeTagType(type) {
  switch (type) {
    case 'file':
      return 'primary'
    case 'function':
      return 'success'
    case 'fpga_file':
      return 'warning'
    case 'fpga_module':
      return 'danger'
    default:
      return 'info'
  }
}

function getNodeTypeLabel(type) {
  switch (type) {
    case 'file':
      return '文件'
    case 'function':
      return '函数'
    case 'fpga_file':
      return 'FPGA文件'
    case 'fpga_module':
      return 'FPGA模块'
    default:
      return '未知'
  }
}

// 获取问题徽章类型（根据问题状态）
function getProblemBadgeType(node) {
  if (!node.problems || node.problems.length === 0) {
    return 'danger'
  }
  
  // 统计各状态的问题数量
  let hasNewProblems = false  // 状态1：新问题
  let hasMarkedProblems = false  // 状态4：已标记
  let allViewedOrFiltered = true  // 所有问题都是状态2或3
  
  node.problems.forEach(problem => {
    const status = problem.problem_status || 1
    if (status === 1) {
      hasNewProblems = true
      allViewedOrFiltered = false
    } else if (status === 4) {
      hasMarkedProblems = true
      allViewedOrFiltered = false
    } else if (status !== 2 && status !== 3) {
      allViewedOrFiltered = false
    }
  })
  
  // 优先级：已标记 > 新问题 > 已查看/已过滤
  if (hasMarkedProblems) {
    return 'primary'  // 蓝色
  } else if (hasNewProblems) {
    return 'success'  // 绿色
  } else if (allViewedOrFiltered) {
    return 'info'  // 灰色
  }
  
  return 'danger'  // 默认红色（不应该出现）
}

// 获取问题徽章的自定义类
function getProblemBadgeClass(node) {
  const type = getProblemBadgeType(node)
  return `problem-badge-${type}`
}

function expandAll() {
  if (treeRef.value) {
    // 获取所有节点的key
    const allKeys = []
    
    function collectKeys(nodes) {
      nodes.forEach(node => {
        allKeys.push(node.id)
        if (node.children && node.children.length > 0) {
          collectKeys(node.children)
        }
      })
    }
    
    collectKeys(props.treeData)
    
    // 展开所有节点
    allKeys.forEach(key => {
      treeRef.value.store.nodesMap[key]?.expand()
    })
  }
}

function collapseAll() {
  if (treeRef.value) {
    // 获取所有节点的key
    const allKeys = []
    
    function collectKeys(nodes) {
      nodes.forEach(node => {
        allKeys.push(node.id)
        if (node.children && node.children.length > 0) {
          collectKeys(node.children)
        }
      })
    }
    
    collectKeys(props.treeData)
    
    // 折叠所有节点
    allKeys.forEach(key => {
      treeRef.value.store.nodesMap[key]?.collapse()
    })
  }
}

// 进度条颜色计算
const progressColor = computed(() => {
  if (!taskProgress.value) return '#409EFF'
  if (taskProgress.value === 100) return '#67C23A'  // 绿色 - 完成
  if (taskProgress.value >= 80) return '#409EFF'     // 蓝色 - 接近完成
  if (taskProgress.value >= 50) return '#E6A23C'     // 橙色 - 进行中
  return '#909399'                                    // 灰色 - 刚开始
})

// 获取任务进度
async function fetchTaskProgress() {
  if (!props.taskId) return
  
  try {
    const response = await axios.get(`/api/codeReview/task/${props.taskId}/progress`)
    if (response.data && response.data.progress !== undefined) {
      taskProgress.value = Math.round(response.data.progress)
      
      // 如果任务已完成，停止轮询
      if (response.data.status === 'completed' || taskProgress.value >= 100) {
        stopProgressPolling()
      }
    }
  } catch (error) {
    console.error('获取任务进度失败:', error)
  }
}

// 开始轮询进度
function startProgressPolling() {
  if (!props.taskId) return
  
  // 立即获取一次
  fetchTaskProgress()
  
  // 每3秒轮询一次
  progressTimer = setInterval(() => {
    fetchTaskProgress()
  }, 3000)
}

// 停止轮询进度
function stopProgressPolling() {
  if (progressTimer) {
    clearInterval(progressTimer)
    progressTimer = null
  }
}

// 生命周期
onMounted(() => {
  if (props.taskId) {
    startProgressPolling()
  }
})

onBeforeUnmount(() => {
  stopProgressPolling()
})

// 监听 taskId 变化
watch(() => props.taskId, (newTaskId) => {
  stopProgressPolling()
  if (newTaskId) {
    taskProgress.value = null
    startProgressPolling()
  }
})
</script>

<style scoped>
.tree-view {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: transparent;
}

.tree-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid #e0e0e0;
  background: #f8f9fa;
  backdrop-filter: blur(5px);
  flex-shrink: 0;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toolbar-left h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

.toolbar-right {
  display: flex;
  gap: 8px;
}

.no-data {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
}

.tree-container {
  flex: 1;
  overflow: auto;
  padding: 10px 15px;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  padding: 8px 0;
  width: 100%;
}

.node-icon {
  flex-shrink: 0;
}

.node-content {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.node-name {
  font-weight: 500;
  color: #2c3e50;
  word-break: break-all;
}

.node-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.problem-badge {
  margin-left: 4px;
}

.marked-tag {
  margin-left: 8px;
  font-weight: 600;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  animation: pulse 2s ease-in-out infinite;
}

.marked-tag .el-icon {
  margin-right: 4px;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.9;
    transform: scale(1.05);
  }
}

/* 深度样式定制 */
:deep(.el-tree-node__content) {
  padding: 8px 12px;
  border-radius: 6px;
  transition: all 0.3s ease;
  margin-bottom: 4px;
  background: transparent;
}

:deep(.el-tree-node__content:hover) {
  background: rgba(102, 126, 234, 0.1);
  transform: translateX(4px);
}

/* 选中状态样式 */
:deep(.el-tree-node.is-current > .el-tree-node__content) {
  background: rgba(97, 218, 251, 0.15) !important;
  border-left: 4px solid #61dafb;
  padding-left: 16px;
  font-weight: 600;
  color: #1890ff;
}

:deep(.el-tree-node.is-current > .el-tree-node__content:hover) {
  background: rgba(97, 218, 251, 0.2) !important;
  transform: none;
}

:deep(.el-tree-node__expand-icon) {
  color: #667eea;
  font-size: 16px;
}

:deep(.el-tree-node__label) {
  font-weight: 500;
  color: #2c3e50;
  flex: 1;
}

:deep(.el-tree-node) {
  margin-bottom: 2px;
}

:deep(.el-tree-node__children) {
  padding-left: 20px;
}

:deep(.el-tree-node.is-expanded > .el-tree-node__content .el-tree-node__expand-icon) {
  transform: rotate(90deg);
}

/* 滚动条样式 */
.tree-container::-webkit-scrollbar {
  width: 6px;
}

.tree-container::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}

.tree-container::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 3px;
}

.tree-container::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5);
}
</style> 