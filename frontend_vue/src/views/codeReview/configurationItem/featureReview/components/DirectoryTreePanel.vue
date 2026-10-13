<template>
  <div class="directory-tree-panel">
    <div class="panel-header">
      <h3>目录结构</h3>
      <el-button :icon="Refresh" size="small" @click="loadDirectoryTree">
        刷新
      </el-button>
    </div>

    <div class="panel-content">
      <div v-if="!taskId" class="empty-state">
        <el-empty description="请先上传代码库" />
      </div>

      <div v-else-if="loading" class="loading-state">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>加载中...</span>
      </div>

      <div v-else class="tree-container">
        <el-tree
          :data="treeData"
          :props="{ label: 'name', children: 'children' }"
          :highlight-current="true"
          :expand-on-click-node="false"
          node-key="path"
          @node-click="onNodeClick"
        >
          <template #default="{ node, data }">
            <div class="tree-node" :class="{ 'highlighted': isHighlighted(data) }">
              <el-icon v-if="data.type === 'directory'">
                <Folder />
              </el-icon>
              <el-icon v-else>
                <Document />
              </el-icon>
              <span class="node-label">{{ data.name }}</span>
              <el-tag
                v-if="getCallOrder(data)"
                type="success"
                size="small"
                class="call-order-tag"
              >
                {{ getCallOrder(data) }}
              </el-tag>
            </div>
          </template>
        </el-tree>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { Refresh, Folder, Document, Loading } from '@element-plus/icons-vue';
import axios from 'axios';

const props = defineProps({
  taskId: {
    type: String,
    default: ''
  },
  selectedFeature: {
    type: Object,
    default: null
  },
  highlightedFiles: {
    type: Array,
    default: () => []
  }
});

const emit = defineEmits(['file-select']);

const treeData = ref([]);
const loading = ref(false);

// 监听taskId变化，自动加载目录树
watch(() => props.taskId, (newVal) => {
  if (newVal) {
    loadDirectoryTree();
  }
}, { immediate: true });

async function loadDirectoryTree() {
  if (!props.taskId) return;
  
  loading.value = true;
  try {
    // 调用后端API获取目录结构
    const response = await axios.get(`/api/codeReview/feature/directory/${props.taskId}`);
    treeData.value = response.data.tree;
    
    console.log('目录树加载成功:', treeData.value);
  } catch (error) {
    console.error('加载目录树失败:', error);
  } finally {
    loading.value = false;
  }
}

function onNodeClick(data) {
  if (data.type === 'file') {
    emit('file-select', data);
  }
}

function isHighlighted(data) {
  if (!props.highlightedFiles || props.highlightedFiles.length === 0) {
    return false;
  }
  return props.highlightedFiles.some(f => f.path === data.path);
}

function getCallOrder(data) {
  if (!props.highlightedFiles || props.highlightedFiles.length === 0) {
    return null;
  }
  const found = props.highlightedFiles.find(f => f.path === data.path);
  return found ? found.order : null;
}
</script>

<style scoped>
.directory-tree-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.panel-header {
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.empty-state,
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #909399;
}

.loading-state .el-icon {
  font-size: 32px;
  margin-bottom: 12px;
}

.tree-container {
  :deep(.el-tree-node__content) {
    padding: 4px 0;
  }
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.tree-node.highlighted {
  background: linear-gradient(90deg, #e6f7ff 0%, #bae7ff 100%);
  border: 1px solid #91d5ff;
  font-weight: 600;
}

.node-label {
  flex: 1;
  font-size: 14px;
}

.call-order-tag {
  margin-left: auto;
  font-weight: bold;
}

:deep(.el-tree-node__content:hover) {
  background-color: #f5f7fa;
}
</style>

