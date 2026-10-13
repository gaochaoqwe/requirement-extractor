<template>
  <div class="excel-table-wrapper">
    <div class="table-container" @contextmenu.prevent="$emit('show-context-menu', $event)">
      <!-- 列标题 -->
      <div class="column-headers">
        <div class="corner-cell"></div>
        <div
          v-for="(column, index) in columns"
          :key="column.key"
          class="column-header"
          :style="{ width: columnWidths[column.key] + 'px' }"
          @click="$emit('select-column', index)"
          :class="{ selected: selectedColumns.includes(index) }"
        >
          <span>{{ column.title }}</span>
          <div
            class="column-resizer"
            @mousedown="$emit('start-column-resize', column.key, $event)"
          ></div>
        </div>
      </div>

      <!-- 数据行 -->
      <div class="table-body" ref="tableBody">
        <div
          v-for="(row, rowIndex) in sortedData"
          :key="row.id || rowIndex"
          class="table-row"
          :class="{ 
            selected: selectedRows.includes(rowIndex),
            'search-highlight': isRowHighlighted(rowIndex)
          }"
          :style="{ height: getRowHeight(rowIndex) + 'px' }"
        >
          <!-- 行号 -->
          <div
            class="row-number"
            @click="$emit('select-row', rowIndex)"
            :class="{ selected: selectedRows.includes(rowIndex) }"
            :style="{ height: getRowHeight(rowIndex) + 'px' }"
          >
            {{ rowIndex + 1 }}
          </div>

          <!-- 数据单元格 -->
          <div
            v-for="(column, colIndex) in columns"
            :key="column.key"
            class="table-cell"
            :style="{ 
              width: columnWidths[column.key] + 'px',
              height: getRowHeight(rowIndex) + 'px'
            }"
            :class="{
              selected: isCellSelected(rowIndex, colIndex),
              editing: editingCell && editingCell.row === rowIndex && editingCell.col === colIndex,
              'search-match': isCellSearchMatch(rowIndex, colIndex)
            }"
            @click="$emit('select-cell', rowIndex, colIndex, $event)"
            @dblclick="$emit('start-edit', rowIndex, colIndex)"
          >
            <!-- 编辑状态 -->
            <div v-if="editingCell && editingCell.row === rowIndex && editingCell.col === colIndex" class="cell-editor">
              <el-input
                ref="cellInput"
                v-model="editingValue"
                type="textarea"
                :autosize="{ minRows: 1, maxRows: 10 }"
                @keyup.enter.ctrl="$emit('finish-edit')"
                @keyup.escape="$emit('cancel-edit')"
                @blur="$emit('finish-edit')"
              />
            </div>
            <!-- 显示状态 -->
            <div v-else class="cell-content" :class="{ 'auto-wrap': autoWrapEnabled }">
              <div
                v-if="column.key === 'test_item_description' || column.key === 'test_method'"
                class="multiline-content"
                :class="{ 'wrapped': autoWrapEnabled }"
                v-html="formatMultilineText(getCellValue(row, column.key))"
              ></div>
              <span v-else class="single-line-content" :class="{ 'wrapped': autoWrapEnabled }">
                {{ getCellValue(row, column.key) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'

const props = defineProps({
  columns: {
    type: Array,
    required: true
  },
  columnWidths: {
    type: Object,
    required: true
  },
  sortedData: {
    type: Array,
    required: true
  },
  selectedCells: {
    type: Array,
    default: () => []
  },
  selectedRows: {
    type: Array,
    default: () => []
  },
  selectedColumns: {
    type: Array,
    default: () => []
  },
  editingCell: {
    type: Object,
    default: null
  },
  editingValue: {
    type: String,
    default: ''
  },
  searchResults: {
    type: Array,
    default: () => []
  },
  autoWrapEnabled: {
    type: Boolean,
    default: false
  },
  getCellValue: {
    type: Function,
    required: true
  },
  formatMultilineText: {
    type: Function,
    required: true
  },
  isCellSelected: {
    type: Function,
    required: true
  },
  isCellSearchMatch: {
    type: Function,
    required: true
  },
  isRowHighlighted: {
    type: Function,
    required: true
  },
  getRowHeight: {
    type: Function,
    required: true
  }
})

const emit = defineEmits([
  'select-column', 'start-column-resize', 'show-context-menu',
  'select-row', 'select-cell', 'start-edit',
  'finish-edit', 'cancel-edit'
])
</script>

<style scoped>
.excel-table-wrapper {
  flex: 1;
  overflow: hidden;
  background: white;
  margin: 0;
}

.table-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.column-headers {
  display: flex;
  background: #f8f9fa;
  border-bottom: 2px solid #d1d5db;
  position: sticky;
  top: 0;
  z-index: 10;
}

.corner-cell {
  width: 50px;
  height: 32px;
  border-right: 1px solid #d1d5db;
  background: #e5e7eb;
}

.column-header {
  height: 32px;
  border-right: 1px solid #d1d5db;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 12px;
  position: relative;
  cursor: pointer;
  user-select: none;
  background: #f8f9fa;
  transition: background-color 0.2s;
}

.column-header:hover {
  background: #e5e7eb;
}

.column-header.selected {
  background: #dbeafe;
  color: #3b82f6;
}

.column-resizer {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  cursor: col-resize;
  background: transparent;
}

.column-resizer:hover {
  background: #3b82f6;
}

.table-body {
  flex: 1;
  overflow: auto;
}

.table-row {
  display: flex;
  border-bottom: 1px solid #e5e7eb;
  transition: background-color 0.2s;
  min-height: 32px;
}

.table-row:hover {
  background: #f8f9fa;
}

.table-row.selected {
  background: #dbeafe;
}

.table-row.search-highlight {
  background: #fef3c7;
}

.row-number {
  width: 50px;
  min-height: 32px;
  border-right: 1px solid #d1d5db;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  color: #6b7280;
  background: #f8f9fa;
  cursor: pointer;
  user-select: none;
}

.row-number.selected {
  background: #dbeafe;
  color: #3b82f6;
  font-weight: 600;
}

.table-cell {
  min-height: 32px;
  border-right: 1px solid #e5e7eb;
  position: relative;
  cursor: cell;
  display: flex;
  align-items: stretch;
}

.table-cell.selected {
  background: #dbeafe;
  outline: 2px solid #3b82f6;
  z-index: 5;
}

.table-cell.editing {
  background: white;
  outline: 2px solid #10b981;
  z-index: 10;
}

.table-cell.search-match {
  background: #fbbf24;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.cell-content {
  padding: 4px 8px;
  width: 100%;
  display: flex;
  align-items: center;
  font-size: 12px;
  line-height: 1.4;
  overflow: hidden;
}

.cell-content.auto-wrap {
  align-items: flex-start;
  padding-top: 6px;
}

.multiline-content {
  width: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 2px;
}

.multiline-content.wrapped {
  justify-content: flex-start;
  align-items: flex-start;
}

.single-line-content {
  width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.single-line-content.wrapped {
  white-space: normal;
  word-wrap: break-word;
  word-break: break-all;
  overflow-wrap: break-word;
}

:deep(.text-line) {
  font-size: 12px;
  line-height: 1.3;
  padding: 1px 0;
  border-left: 2px solid transparent;
  padding-left: 4px;
  word-wrap: break-word;
  word-break: break-all;
}

:deep(.text-line:not(:last-child)) {
  border-bottom: 1px solid #f3f4f6;
}

.cell-editor {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 15;
}

.cell-editor :deep(.el-textarea) {
  height: 100%;
}

.cell-editor :deep(.el-textarea__inner) {
  border: none;
  border-radius: 0;
  box-shadow: 0 0 0 2px #10b981;
  resize: none;
  font-size: 12px;
  line-height: 1.4;
  min-height: 100%;
}

/* 滚动条样式 */
.table-body::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.table-body::-webkit-scrollbar-track {
  background: #f3f4f6;
}

.table-body::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 4px;
}

.table-body::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .column-header {
    font-size: 11px;
  }
  
  .cell-content {
    font-size: 11px;
    padding: 2px 4px;
  }
  
  :deep(.text-line) {
    font-size: 11px;
  }
}
</style> 