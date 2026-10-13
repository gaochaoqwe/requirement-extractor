<template>
  <div class="file-map-tree">
    <div class="file-list">
      <div
        v-for="file in fileList"
        :key="file.id"
        :class="['file-item', { selected: selectedFile?.id === file.id }]"
        @click="selectFile(file)"
      >
        <div class="file-info">
          <i class="file-icon el-icon-document"></i>
          <span class="file-name">{{ file.name }}</span>
          <span class="problem-count" v-if="file.problemCount > 0">({{ file.problemCount }})</span>
        </div>
        <div class="file-path" v-if="file.path">{{ file.path }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  taskId: {
    type: [String, Number],
    required: true
  },
  selectedFile: {
    type: Object,
    default: null
  },
  treeData: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['file-select'])

// 文件列表数据 - 使用从父组件传递的treeData
const fileList = computed(() => {
  console.log('FileMapTree: props.treeData变化:', props.treeData)
  return props.treeData || []
})

// 生成模拟文件列表
function generateMockFileList() {
  return [
    {
      id: 'main.c',
      name: 'main.c',
      path: 'ImageProcessor/src/main.c',
      problemCount: 3,
      size: 1024
    },
    {
      id: 'camera_driver.c',
      name: 'camera_driver.c', 
      path: 'ImageProcessor/src/camera_driver.c',
      problemCount: 5,
      size: 2048
    },
    {
      id: 'param_loader.c',
      name: 'param_loader.c',
      path: 'ImageProcessor/src/param_loader.c',
      problemCount: 2,
      size: 1536
    },
    {
      id: 'system_controller.c',
      name: 'system_controller.c',
      path: 'ImageProcessor/src/system_controller.c',
      problemCount: 4,
      size: 2560
    },
    {
      id: 'feature_extractor.c',
      name: 'feature_extractor.c',
      path: 'ImageProcessor/src/feature_extractor.c',
      problemCount: 1,
      size: 1792
    },
    {
      id: 'logger.c',
      name: 'logger.c',
      path: 'ImageProcessor/src/utils/logger.c',
      problemCount: 2,
      size: 896
    },
    {
      id: 'memory_pool.c',
      name: 'memory_pool.c',
      path: 'ImageProcessor/src/utils/memory_pool.c',
      problemCount: 1,
      size: 1280
    }
  ]
}

// 选择文件
function selectFile(file) {
  emit('file-select', file)
}

// 移除onMounted中的fetchFileList调用，因为现在使用props.treeData
</script>

<style scoped>
.file-map-tree {
  height: 100%;
  overflow: auto;
}

.file-list {
  padding: 8px;
}

.file-item {
  padding: 8px 12px;
  margin-bottom: 4px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.file-item:hover {
  background-color: #f5f7fa;
  border-color: #e4e7ed;
}

.file-item.selected {
  background-color: #ecf5ff;
  border-color: #409eff;
  color: #409eff;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.file-icon {
  font-size: 16px;
  color: #606266;
}

.file-item.selected .file-icon {
  color: #409eff;
}

.file-name {
  font-weight: 500;
  flex: 1;
}

.problem-count {
  font-size: 12px;
  color: #f56c6c;
  font-weight: bold;
}

.file-path {
  font-size: 12px;
  color: #909399;
  margin-left: 24px;
  word-break: break-all;
}

/* 滚动条样式 */
.file-map-tree::-webkit-scrollbar {
  width: 6px;
}

.file-map-tree::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.file-map-tree::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.file-map-tree::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style> 