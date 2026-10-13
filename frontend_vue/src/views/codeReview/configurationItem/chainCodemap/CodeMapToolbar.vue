<template>
  <div class="toolbar">
    <div class="toolbar-left">
      <h1 class="title">
        <el-icon><Share /></el-icon>
        代码库地图
      </h1>
      <el-tag v-if="taskId" type="info" size="large">任务ID: {{ taskId }}</el-tag>
    </div>
    
    <div class="toolbar-center">
      <!-- 视图切换 -->
      <el-radio-group v-model="viewMode" size="large">
        <el-radio-button label="source">
          <el-icon><Document /></el-icon>
          源码视图
        </el-radio-button>
        <el-radio-button label="graph">
          <el-icon><Operation /></el-icon>
          代码地图视图
        </el-radio-button>
      </el-radio-group>
    </div>
    
    <div class="toolbar-right">
      <!-- 搜索 -->
      <div class="search-container">
        <el-input
          v-model="searchQuery"
          placeholder="搜索函数、文件或问题..."
          size="large"
          @keyup.enter="$emit('search')"
          class="search-input"
        >
          <template #prepend>
            <el-select v-model="searchType" style="width: 100px">
              <el-option label="全部" value="all" />
              <el-option label="函数" value="function" />
              <el-option label="文件" value="file" />
              <el-option label="问题" value="problem" />
            </el-select>
          </template>
          <template #append>
            <el-button @click="$emit('search')" :icon="Search" />
          </template>
        </el-input>
      </div>
      
      <!-- 工具按钮 -->
      <div class="tool-buttons">
        <el-button @click="$emit('refreshLayout')" :icon="Refresh" size="large">重新布局</el-button>
        <el-button @click="$emit('exportData')" :icon="Download" size="large">导出</el-button>
        <el-button @click="$emit('toggleSidebar')" :icon="showSidebar ? 'ArrowRight' : 'ArrowLeft'" size="large">
          {{ showSidebar ? '隐藏' : '显示' }}侧栏
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { 
  Search, 
  Share, 
  Files, 
  Refresh, 
  Download, 
  Operation,
  Document
} from '@element-plus/icons-vue'

// Props
const props = defineProps({
  taskId: {
    type: [String, Number],
    required: true
  },
  showSidebar: {
    type: Boolean,
    default: true
  },
  viewMode: {
    type: String,
    default: 'source'
  },
  searchQuery: {
    type: String,
    default: ''
  },
  searchType: {
    type: String,
    default: 'all'
  }
})

// Emits
const emit = defineEmits(['search', 'refreshLayout', 'exportData', 'toggleSidebar', 'update:viewMode', 'update:searchQuery', 'update:searchType'])

// v-model
const viewMode = computed({
  get: () => props.viewMode,
  set: (value) => emit('update:viewMode', value)
})

const searchQuery = computed({
  get: () => props.searchQuery,
  set: (value) => emit('update:searchQuery', value)
})

const searchType = computed({
  get: () => props.searchType,
  set: (value) => emit('update:searchType', value)
})
</script>

<style scoped>
.toolbar {
  height: 80px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 30px;
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #2c3e50;
  display: flex;
  align-items: center;
  gap: 10px;
}

.toolbar-center {
  flex: 1;
  display: flex;
  justify-content: center;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.search-container {
  width: 400px;
}

.search-input {
  width: 100%;
}

.tool-buttons {
  display: flex;
  gap: 10px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .search-container {
    width: 300px;
  }
}

@media (max-width: 768px) {
  .toolbar {
    flex-direction: column;
    height: auto;
    padding: 20px;
    gap: 20px;
  }
  
  .toolbar-left, .toolbar-center, .toolbar-right {
    width: 100%;
    justify-content: center;
  }
  
  .search-container {
    width: 100%;
  }
  
  .tool-buttons {
    flex-wrap: wrap;
    justify-content: center;
  }
}
</style> 