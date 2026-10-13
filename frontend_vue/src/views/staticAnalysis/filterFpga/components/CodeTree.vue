<template>
  <div class="code-tree">
    <div class="tree-header">
      <h3>代码结构</h3>
      <div class="tree-actions">
        <el-button @click="expandAll" size="small" link type="primary">
          <el-icon><Plus /></el-icon>
          全部展开
        </el-button>
        <el-button @click="collapseAll" size="small" link type="primary">
          <el-icon><Minus /></el-icon>
          全部折叠
        </el-button>
      </div>
    </div>

    <div class="tree-content">
      <div v-if="!treeData || treeData.length === 0" class="empty-state">
        <el-empty description="暂无文件" />
      </div>
      <div v-else class="tree-list">
        <div
          v-for="node in treeData"
          :key="node.id"
          class="tree-node"
          :class="{ 'active': selectedNode && selectedNode.id === node.id }"
          @click="handleNodeClick(node)"
        >
          <div class="node-left">
            <el-icon class="node-icon" :style="{ color: '#409EFF' }">
              <Document />
            </el-icon>
            <span class="node-name">{{ node.name }}</span>
          </div>
          <div class="node-right">
            <el-tag type="success" size="small" effect="light">文件</el-tag>
            <el-tag 
              v-if="node.problemCount > 0"
              size="small"
              :class="['problem-count-tag', getAggregatedStatusClass(node)]"
            >
              {{ node.problemCount }}
            </el-tag>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Document, Plus, Minus } from '@element-plus/icons-vue'

// Props
const props = defineProps({
  treeData: {
    type: Array,
    default: () => []
  },
  selectedNode: {
    type: Object,
    default: null
  }
})

// Emits
const emit = defineEmits(['nodeClick'])

// 方法
function handleNodeClick(node) {
  emit('nodeClick', node)
}

function getAggregatedStatusClass(node) {
  try {
    const problems = node.problems || []
    const hasMarked = problems.some(p => p.problem_status === 4)
    const hasNew = problems.some(p => !p.problem_status || p.problem_status === 1)
    const hasViewed = problems.some(p => p.problem_status === 2 || p.problem_status === 3)
    if (hasMarked) return 'status-marked'
    if (hasNew) return 'status-new'
    if (hasViewed) return 'status-viewed'
  } catch (e) {
    // ignore
  }
  return 'status-new'
}

function expandAll() {
  // 静态分析代码视图不需要展开/折叠（文件列表是扁平的）
}

function collapseAll() {
  // 静态分析代码视图不需要展开/折叠（文件列表是扁平的）
}
</script>

<style scoped>
.code-tree {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: white;
}

.tree-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e8e8e8;
  background: white;
}

.tree-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.tree-actions {
  display: flex;
  gap: 10px;
}

.tree-content {
  flex: 1;
  overflow: auto;
  padding: 10px 0;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.tree-list {
  display: flex;
  flex-direction: column;
}

.tree-node {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 20px;
  cursor: pointer;
  transition: all 0.2s ease;
  border-left: 3px solid transparent;
}

.tree-node:hover {
  background: #f5f5f5;
}

.tree-node.active {
  background: #e6f7ff;
  border-left-color: #1890ff;
}

.node-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.node-icon {
  flex-shrink: 0;
  font-size: 16px;
}

.node-name {
  font-size: 14px;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.node-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.problem-count-tag {
  flex-shrink: 0;
  font-weight: 600;
}

/* 聚合状态颜色：已标记(蓝) > 新发现(绿) > 已查看(灰) */
.problem-count-tag.status-new {
  background-color: #ecfdf5;
  color: #059669;
  border: 1px solid #a7f3d0;
}

.problem-count-tag.status-viewed {
  background-color: #f3f4f6;
  color: #6b7280;
  border: 1px solid #e5e7eb;
}

.problem-count-tag.status-marked {
  background-color: #eff6ff;
  color: #2563eb;
  border: 1px solid #bfdbfe;
}

.no-problem-text {
  font-size: 12px;
  color: #909399;
  flex-shrink: 0;
}

/* 滚动条样式 */
.tree-content::-webkit-scrollbar {
  width: 6px;
}

.tree-content::-webkit-scrollbar-track {
  background: #f5f5f5;
}

.tree-content::-webkit-scrollbar-thumb {
  background: #d9d9d9;
  border-radius: 3px;
}

.tree-content::-webkit-scrollbar-thumb:hover {
  background: #bfbfbf;
}
</style>

