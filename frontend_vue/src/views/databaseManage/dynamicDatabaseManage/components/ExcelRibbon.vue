<template>
  <div class="excel-ribbon">
    <!-- 主功能区 -->
    <div class="ribbon-tabs">
      <div class="ribbon-tab active">
        <span>开始</span>
      </div>
    </div>
    
    <!-- 功能区内容 - 统一的上图标下文字格式 -->
    <div class="ribbon-content">
      <!-- 粘贴 -->
      <button class="ribbon-button large" @click="$emit('paste')" :disabled="!clipboardHasData" title="粘贴 (Ctrl+V)">
        <img src="../assets/paste.svg" class="button-icon large-icon" alt="粘贴" />
        <span class="button-text">粘贴</span>
      </button>

      <div class="separator"></div>

      <!-- 复制 -->
      <button class="ribbon-button" @click="$emit('copy')" :disabled="selectedCells.length === 0" title="复制 (Ctrl+C)">
        <img src="../assets/copy.svg" class="button-icon" alt="复制" />
        <span class="button-text">复制</span>
      </button>

      <!-- 剪切 -->
      <button class="ribbon-button" @click="$emit('cut')" :disabled="selectedCells.length === 0" title="剪切 (Ctrl+X)">
        <img src="../assets/scissors.svg" class="button-icon" alt="剪切" />
        <span class="button-text">剪切</span>
      </button>

      <div class="separator"></div>

      <!-- 新增行 -->
      <button class="ribbon-button" @click="$emit('add-row')" title="新增行">
        <img src="../assets/add.svg" class="button-icon" alt="新增行" />
        <span class="button-text">新增行</span>
      </button>

      <!-- 上方插入 -->
      <button class="ribbon-button" @click="$emit('insert-row-above')" :disabled="selectedRows.length === 0" title="在上方插入行">
        <img src="../assets/arrow-up.svg" class="button-icon" alt="上方插入" />
        <span class="button-text">上方插入</span>
      </button>

      <!-- 下方插入 -->
      <button class="ribbon-button" @click="$emit('insert-row-below')" :disabled="selectedRows.length === 0" title="在下方插入行">
        <img src="../assets/arrow-down.svg" class="button-icon" alt="下方插入" />
        <span class="button-text">下方插入</span>
      </button>

      <!-- 删除行 -->
      <button class="ribbon-button danger" @click="$emit('delete-rows')" :disabled="selectedRows.length === 0" title="删除选中行">
        <img src="../assets/delete.svg" class="button-icon" alt="删除行" />
        <span class="button-text">删除行</span>
      </button>

      <div class="separator"></div>

      <!-- 普通导入 -->
      <el-upload
        :auto-upload="false"
        :show-file-list="false"
        accept=".xlsx,.xls"
        :on-change="(file) => $emit('normal-import', file)"
        class="upload-wrapper"
      >
        <button class="ribbon-button success" title="普通导入Excel文件">
          <img src="../assets/import.svg" class="button-icon" alt="普通导入" />
          <span class="button-text">普通导入</span>
        </button>
      </el-upload>

      <!-- 智能导入 -->
      <el-upload
        :auto-upload="false"
        :show-file-list="false"
        accept=".xlsx,.xls"
        :on-change="(file) => $emit('smart-import', file)"
        class="upload-wrapper"
      >
        <button class="ribbon-button primary" title="智能导入Excel文件">
          <img src="../assets/magic-wand.svg" class="button-icon" alt="智能导入" />
          <span class="button-text">智能导入</span>
        </button>
      </el-upload>

      <!-- 导出 -->
      <button class="ribbon-button" @click="$emit('export')" title="导出到Excel">
        <img src="../assets/export.svg" class="button-icon" alt="导出" />
        <span class="button-text">导出Excel</span>
      </button>

      <div class="separator"></div>

      <!-- 保存 -->
      <button class="ribbon-button" @click="$emit('save')" :class="{ highlight: isDirty }" title="保存 (Ctrl+S)">
        <img src="../assets/save.svg" class="button-icon" alt="保存" />
        <span class="button-text">保存</span>
      </button>

      <!-- 全选 -->
      <button class="ribbon-button" @click="$emit('select-all')" title="全选 (Ctrl+A)">
        <img src="../assets/select-all.svg" class="button-icon" alt="全选" />
        <span class="button-text">全选</span>
      </button>

      <!-- 自动换行 -->
      <button class="ribbon-button" @click="$emit('toggle-auto-wrap')" :class="{ active: autoWrapEnabled }" title="切换自动换行">
        <img src="../assets/auto-wrap.svg" class="button-icon" alt="自动换行" />
        <span class="button-text">自动换行</span>
      </button>

      <div class="separator"></div>

      <!-- 搜索框 -->
      <div class="search-container">
        <el-input
          ref="searchInput"
          v-model="searchText"
          placeholder="搜索内容... (Ctrl+F)"
          size="small"
          clearable
          @keyup.enter="$emit('find-next')"
          @keyup.escape="$emit('clear-search')"
          class="search-input"
        >
          <template #prefix>
            <img src="../assets/search.svg" class="search-icon" alt="搜索" />
          </template>
        </el-input>
        <div class="search-controls">
          <button class="search-btn" @click="$emit('find-previous')" :disabled="!searchText" title="查找上一个">
            <img src="../assets/find-previous.svg" class="control-icon" alt="上一个" />
          </button>
          <button class="search-btn" @click="$emit('find-next')" :disabled="!searchText" title="查找下一个">
            <img src="../assets/find-next.svg" class="control-icon" alt="下一个" />
          </button>
          <span class="search-info" v-if="searchResults.length > 0">
            {{ currentSearchIndex + 1 }}/{{ searchResults.length }}
          </span>
        </div>
      </div>

      <!-- 清除 -->
      <button class="ribbon-button" @click="$emit('clear-content')" :disabled="selectedCells.length === 0" title="清除内容 (Delete)">
        <img src="../assets/clear.svg" class="button-icon" alt="清除" />
        <span class="button-text">清除</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'

const props = defineProps({
  selectedCells: {
    type: Array,
    default: () => []
  },
  selectedRows: {
    type: Array,
    default: () => []
  },
  clipboardHasData: {
    type: Boolean,
    default: false
  },
  isDirty: {
    type: Boolean,
    default: false
  },
  autoWrapEnabled: {
    type: Boolean,
    default: false
  },
  searchText: {
    type: String,
    default: ''
  },
  searchResults: {
    type: Array,
    default: () => []
  },
  currentSearchIndex: {
    type: Number,
    default: -1
  }
})

const emit = defineEmits([
  'paste', 'copy', 'cut',
  'insert-row-above', 'insert-row-below', 'add-row',
  'delete-rows',
  'normal-import', 'smart-import', 'export',
  'save', 'select-all', 'toggle-auto-wrap',
  'find-next', 'find-previous', 'clear-search', 'clear-content'
])
</script>

<style scoped>
.excel-ribbon {
  background: #f8f9fa;
  border-bottom: 1px solid #d1d5db;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.ribbon-tabs {
  display: flex;
  background: #e5e7eb;
  border-bottom: 1px solid #d1d5db;
}

.ribbon-tab {
  padding: 8px 20px;
  cursor: pointer;
  border-right: 1px solid #d1d5db;
  font-size: 13px;
  font-weight: 500;
}

.ribbon-tab.active {
  background: #f8f9fa;
  border-bottom: 2px solid #3b82f6;
  color: #3b82f6;
}

.ribbon-content {
  display: flex;
  padding: 8px 16px;
  gap: 8px;
  align-items: center;
  min-height: 80px;
}

/* 统一的按钮样式 - 上图标下文字 */
.ribbon-button {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 6px 8px;
  border: 1px solid transparent;
  border-radius: 4px;
  background: transparent;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 60px;
  min-height: 60px;
  font-size: 11px;
  color: #374151;
}

.ribbon-button:hover:not(:disabled) {
  background: #e5e7eb;
  border-color: #d1d5db;
}

.ribbon-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 大按钮样式 */
.ribbon-button.large {
  min-width: 80px;
  min-height: 70px;
  padding: 8px 12px;
}

/* 按钮状态样式 */
.ribbon-button.success {
  color: #059669;
}

.ribbon-button.success:hover:not(:disabled) {
  background: #f0fdf4;
  border-color: #bbf7d0;
}

.ribbon-button.primary {
  color: #3b82f6;
}

.ribbon-button.primary:hover:not(:disabled) {
  background: #eff6ff;
  border-color: #bfdbfe;
}

.ribbon-button.danger {
  color: #dc2626;
}

.ribbon-button.danger:hover:not(:disabled) {
  background: #fef2f2;
  border-color: #fecaca;
}

.ribbon-button.highlight {
  background: #fef3c7;
  border-color: #fbbf24;
  color: #92400e;
}

.ribbon-button.active {
  background: #dbeafe;
  border-color: #3b82f6;
  color: #1d4ed8;
}

/* 图标样式 */
.button-icon {
  width: 24px;
  height: 24px;
  margin-bottom: 4px;
  filter: brightness(0) saturate(100%);
}

.large-icon {
  width: 32px;
  height: 32px;
}

/* 根据按钮状态调整图标颜色 */
.ribbon-button.success .button-icon {
  filter: brightness(0) saturate(100%) invert(48%) sepia(79%) saturate(2476%) hue-rotate(86deg) brightness(118%) contrast(119%);
}

.ribbon-button.primary .button-icon {
  filter: brightness(0) saturate(100%) invert(37%) sepia(99%) saturate(1798%) hue-rotate(213deg) brightness(97%) contrast(94%);
}

.ribbon-button.danger .button-icon {
  filter: brightness(0) saturate(100%) invert(17%) sepia(90%) saturate(7471%) hue-rotate(3deg) brightness(97%) contrast(118%);
}

.ribbon-button.highlight .button-icon {
  filter: brightness(0) saturate(100%) invert(64%) sepia(98%) saturate(1204%) hue-rotate(5deg) brightness(101%) contrast(101%);
}

.ribbon-button.active .button-icon {
  filter: brightness(0) saturate(100%) invert(20%) sepia(95%) saturate(2893%) hue-rotate(214deg) brightness(99%) contrast(94%);
}

/* 按钮文字 */
.button-text {
  font-size: 11px;
  line-height: 1.2;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

/* 分隔线 */
.separator {
  width: 1px;
  height: 50px;
  background: #d1d5db;
  margin: 0 4px;
}

/* 上传组件包装 */
.upload-wrapper {
  display: contents;
}

.upload-wrapper :deep(.el-upload) {
  display: contents;
}

/* 搜索容器 */
.search-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  margin: 0 8px;
}

.search-input {
  width: 200px;
}

.search-icon {
  width: 14px;
  height: 14px;
  filter: brightness(0) saturate(100%) invert(55%) sepia(8%) saturate(878%) hue-rotate(201deg) brightness(92%) contrast(86%);
}

.search-controls {
  display: flex;
  align-items: center;
  gap: 4px;
}

.search-btn {
  padding: 4px;
  border: 1px solid #d1d5db;
  border-radius: 3px;
  background: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;
}

.search-btn:hover:not(:disabled) {
  background: #f3f4f6;
}

.search-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.control-icon {
  width: 12px;
  height: 12px;
  filter: brightness(0) saturate(100%);
}

.search-info {
  font-size: 10px;
  color: #6b7280;
  margin-left: 4px;
  white-space: nowrap;
}

/* 响应式设计 */
@media (max-width: 1400px) {
  .ribbon-content {
    gap: 6px;
  }
  
  .ribbon-button {
    min-width: 55px;
    padding: 4px 6px;
  }
  
  .ribbon-button.large {
    min-width: 70px;
  }
  
  .button-text {
    font-size: 10px;
  }
  
  .search-input {
    width: 180px;
  }
}

@media (max-width: 1200px) {
  .ribbon-content {
    flex-wrap: wrap;
    gap: 4px;
    padding: 6px 12px;
  }
  
  .ribbon-button {
    min-width: 50px;
    min-height: 55px;
  }
  
  .ribbon-button.large {
    min-width: 65px;
    min-height: 65px;
  }
  
  .button-icon {
    width: 20px;
    height: 20px;
  }
  
  .large-icon {
    width: 28px;
    height: 28px;
  }
  
  .search-input {
    width: 160px;
  }
}

@media (max-width: 768px) {
  .ribbon-content {
    gap: 2px;
    padding: 4px 8px;
  }
  
  .ribbon-button {
    min-width: 45px;
    min-height: 50px;
    padding: 2px 4px;
  }
  
  .button-text {
    font-size: 9px;
  }
  
  .search-container {
    margin: 0 4px;
  }
  
  .search-input {
    width: 140px;
  }
  
  .separator {
    height: 40px;
  }
}
</style> 