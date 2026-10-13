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
          <div 
            class="tree-node"
            :class="{ 
              'highlighted': isHighlighted(data),
              'task-related': isTaskRelated(data)
            }"
          >
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
                
                <!-- 显示问题数量 -->
                <el-badge 
                  v-if="data.problemCount > 0" 
                  :value="data.problemCount" 
                  :type="data.problemCount > 5 ? 'danger' : 'warning'"
                  class="problem-badge"
                />
                
                <!-- 任务关联标识 -->
                <el-tag 
                  v-if="isTaskRelated(data)" 
                  type="success" 
                  size="small" 
                  effect="dark"
                  class="task-tag"
                >
                  任务相关
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
import { ref, computed, watch, nextTick } from 'vue'
import { Document, Operation, Plus, Minus } from '@element-plus/icons-vue'

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
  selectedTask: {
    type: Object,
    default: null
  },
  highlightedItems: {
    type: Array,
    default: () => []
  }
})

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
    // 展开到选中节点的父节点
    if (newNode.type === 'function' || newNode.type === 'fpga_module') {
      // 如果是函数/模块，展开其父文件节点
      const parentKey = newNode.file_path || newNode.parent_id
      if (parentKey) {
        treeRef.value.setExpandedKeys([parentKey], false)
      }
    }
    // 设置当前选中节点
    treeRef.value.setCurrentKey(newNode.id)
  }
}, { immediate: true })

// 方法
function handleTreeNodeClick(data) {
  emit('nodeClick', data)
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

// 判断节点是否高亮
function isHighlighted(data) {
  return props.highlightedItems.some(item => item.id === data.id)
}

// 判断节点是否与当前任务相关
function isTaskRelated(data) {
  if (!props.selectedTask) return false
  
  // 如果节点有problems属性，检查是否有属于当前任务的问题
  if (data.problems && data.problems.length > 0) {
    return data.problems.some(problem => 
      problem.task_id === props.selectedTask.task_id
    )
  }
  
  // 对于函数节点，检查函数名是否与任务相关
  if (data.type === 'function' && props.selectedTask.problems) {
    return props.selectedTask.problems.some(problem => 
      problem.function_name === data.name
    )
  }
  
  // 对于文件节点，检查是否包含任务相关的函数
  if (data.type === 'file' && data.children && props.selectedTask.problems) {
    return data.children.some(child => 
      props.selectedTask.problems.some(problem => 
        problem.function_name === child.name
      )
    )
  }
  
  return false
}
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
  border-radius: 6px;
  transition: all 0.3s ease;
}

/* 高亮节点样式 */
.tree-node.highlighted {
  background: linear-gradient(90deg, #fff3cd, #ffeaa7);
  border-left: 4px solid #f39c12;
  padding-left: 8px;
  box-shadow: 0 2px 8px rgba(243, 156, 18, 0.2);
}

/* 任务相关节点样式 */
.tree-node.task-related {
  background: linear-gradient(90deg, #d1ecf1, #bee5eb);
  border-left: 4px solid #17a2b8;
  padding-left: 8px;
  box-shadow: 0 2px 8px rgba(23, 162, 184, 0.2);
}

/* 同时高亮和任务相关的节点 */
.tree-node.highlighted.task-related {
  background: linear-gradient(90deg, #d4edda, #c3e6cb);
  border-left: 4px solid #28a745;
  box-shadow: 0 2px 8px rgba(40, 167, 69, 0.25);
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

.task-tag {
  margin-left: 4px;
  font-size: 10px;
  padding: 2px 6px;
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