<template>
  <div class="version-tree">
    <el-tree
      :data="treeData"
      :props="treeProps"
      node-key="id"
      :default-expand-all="false"
      :expand-on-click-node="false"
      :highlight-current="true"
      @node-click="handleNodeClick"
      class="file-tree"
    >
      <template #default="{ node, data }">
        <div class="tree-node" :class="getNodeClass(data)">
          <div class="node-content">
            <el-icon class="node-icon">
              <Folder v-if="data.isDirectory" />
              <Document v-else />
            </el-icon>
            <span class="node-label">{{ node.label }}</span>
            <div class="node-badges">
              <el-tag v-if="data.added" type="success" size="small" class="status-badge">新增</el-tag>
              <el-tag v-if="data.modified" type="warning" size="small" class="status-badge">修改</el-tag>
              <el-tag v-if="data.deleted" type="danger" size="small" class="status-badge">删除</el-tag>
            </div>
          </div>
        </div>
      </template>
    </el-tree>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Folder, Document } from '@element-plus/icons-vue'

// Props
const props = defineProps({
  treeData: {
    type: Array,
    default: () => []
  },
  selectedFile: {
    type: Object,
    default: null
  },
  version: {
    type: String,
    default: 'old' // 'old' or 'new'
  }
})

// Emits
const emit = defineEmits(['file-click'])

// 树形控件配置
const treeProps = {
  children: 'children',
  label: 'name'
}

// 计算属性
const processedTreeData = computed(() => {
  return props.treeData || []
})

// 方法
function handleNodeClick(data, node) {
  if (!data.isDirectory) {
    emit('file-click', {
      ...data,
      version: props.version
    })
  }
}

function getNodeClass(data) {
  const classes = []
  
  if (data.isDirectory) {
    classes.push('directory-node')
  } else {
    classes.push('file-node')
  }
  
  if (data.added) {
    classes.push('added-node')
  } else if (data.modified) {
    classes.push('modified-node')
  } else if (data.deleted) {
    classes.push('deleted-node')
  }
  
  if (props.selectedFile && props.selectedFile.id === data.id) {
    classes.push('selected-node')
  }
  
  return classes.join(' ')
}
</script>

<style scoped>
.version-tree {
  height: 100%;
  padding: 10px;
}

.file-tree {
  background: transparent;
  border: none;
}

.file-tree :deep(.el-tree-node__content) {
  background: transparent;
  border: none;
  padding: 4px 0;
  margin: 2px 0;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.file-tree :deep(.el-tree-node__content:hover) {
  background: rgba(103, 126, 234, 0.1);
}

.tree-node {
  width: 100%;
  display: flex;
  align-items: center;
  padding: 2px 4px;
}

.node-content {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.node-icon {
  flex-shrink: 0;
  font-size: 16px;
  color: #667eea;
}

.node-label {
  flex: 1;
  font-size: 13px;
  color: #2c3e50;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}

.node-badges {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.status-badge {
  font-size: 10px;
  padding: 1px 4px;
  height: 16px;
  line-height: 14px;
}

/* 节点状态样式 */
.directory-node .node-icon {
  color: #f39c12;
}

.file-node .node-icon {
  color: #3498db;
}

.added-node {
  background: rgba(46, 204, 113, 0.1);
  border-left: 3px solid #2ecc71;
}

.modified-node {
  background: rgba(241, 196, 15, 0.1);
  border-left: 3px solid #f1c40f;
}

.deleted-node {
  background: rgba(231, 76, 60, 0.1);
  border-left: 3px solid #e74c3c;
  opacity: 0.7;
}

.deleted-node .node-label {
  text-decoration: line-through;
  color: #999;
}

.selected-node {
  background: rgba(103, 126, 234, 0.2) !important;
  border: 1px solid #667eea;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .node-label {
    font-size: 12px;
  }
  
  .status-badge {
    font-size: 9px;
    padding: 1px 3px;
    height: 14px;
    line-height: 12px;
  }
}
</style>
