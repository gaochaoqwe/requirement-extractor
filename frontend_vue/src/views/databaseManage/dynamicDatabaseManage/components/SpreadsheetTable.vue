<template>
  <div class="spreadsheet-table">
    <div class="table-container" ref="tableContainer">
      <table 
        class="excel-table"
        @mousedown="handleMouseDown"
        @mousemove="handleMouseMove"
        @mouseup="handleMouseUp"
        @contextmenu="handleContextMenu"
      >
        <thead>
          <tr>
            <th class="row-number-header">
              <input 
                type="checkbox" 
                v-model="selectAll" 
                @change="handleSelectAll"
              />
            </th>
            <th 
              v-for="column in columns" 
              :key="column.prop"
              :style="{ width: column.width + 'px' }"
              class="column-header"
              @click="handleColumnSelect(column.prop)"
            >
              {{ column.label }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="(row, rowIndex) in data" 
            :key="row.id || rowIndex"
            :class="{ 
              'selected-row': selectedRows.has(rowIndex),
              'hover-row': hoverRowIndex === rowIndex 
            }"
            @mouseenter="hoverRowIndex = rowIndex"
            @mouseleave="hoverRowIndex = -1"
          >
            <!-- 行号和选择框 -->
            <td class="row-number" 
                @click="handleRowSelect(rowIndex, $event)"
                @mousedown="handleRowMouseDown(rowIndex, $event)"
                @mouseenter="handleRowMouseEnter(rowIndex, $event)">
              <input 
                type="checkbox" 
                :checked="selectedRows.has(rowIndex)"
                @change="handleRowCheckChange(rowIndex, $event)"
              />
              <span class="row-index">{{ rowIndex + 1 }}</span>
            </td>
            
            <!-- 数据单元格（支持纵向合并） -->
            <template v-for="column in columns">
              <td 
                v-if="getRowspan(rowIndex, column.prop) !== 0"
                :key="column.prop"
                :rowspan="getRowspan(rowIndex, column.prop)"
                :class="{
                  'selected-cell': selectedCells.has(`${rowIndex}-${column.prop}`),
                  'editing-cell': editingCell?.row === rowIndex && editingCell?.prop === column.prop,
                  'editable-cell': column.editable !== false
                }"
                :style="{ width: column.width + 'px' }"
                @click="handleCellClick(rowIndex, column.prop, $event)"
                @dblclick="handleCellDoubleClick(rowIndex, column.prop)"
                :data-row="rowIndex"
                :data-col="column.prop"
              >
                <!-- 编辑模式 -->
                <div 
                  v-if="editingCell?.row === rowIndex && editingCell?.prop === column.prop"
                  class="cell-editor"
                >
                  <textarea
                    v-if="column.type === 'textarea'"
                    ref="cellInput"
                    v-model="editingValue"
                    @blur="handleCellEditComplete"
                    @keydown="handleCellKeyDown"
                    class="cell-textarea"
                    :rows="3"
                  />
                  <input
                    v-else
                    ref="cellInput"
                    v-model="editingValue"
                    @blur="handleCellEditComplete"
                    @keydown="handleCellKeyDown"
                    class="cell-input"
                    type="text"
                  />
                </div>
                
                <!-- 显示模式 -->
                <div 
                  v-else 
                  class="cell-content"
                  :title="getCellDisplayValue(row, column)"
                >
                  {{ getCellDisplayValue(row, column) }}
                </div>
                
                <!-- 操作按钮 -->
                <div 
                  v-if="hoverRowIndex === rowIndex && column.prop === columns[columns.length - 1].prop"
                  class="row-actions"
                >
                  <el-button 
                    size="small" 
                    type="primary" 
                    @click="handleEdit(row, rowIndex)"
                    :icon="Edit"
                  />
                  <el-button 
                    size="small" 
                    type="danger" 
                    @click="handleDelete(row)"
                    :icon="Delete"
                  />
                </div>
              </td>
            </template>
          </tr>
        </tbody>
      </table>
    </div>
    
    <!-- 分页 -->
    <div class="pagination-container">
      <el-pagination
        :current-page="currentPage"
        :page-size="pageSize"
        :page-sizes="[20, 50, 100, 200]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        :disabled="loading"
      />
    </div>
    
    <!-- 右键菜单 -->
    <div 
      v-if="showContextMenu"
      class="context-menu"
      :style="{ left: contextMenuX + 'px', top: contextMenuY + 'px' }"
      @click.stop
    >
      <div class="menu-item" @click="handleCopy">
        <el-icon><DocumentCopy /></el-icon>
        复制 (Ctrl+C)
      </div>
      <div class="menu-item" @click="handlePaste" :class="{ disabled: !clipboardData }">
        <el-icon><Document /></el-icon>
        粘贴 (Ctrl+V)
      </div>
      <div class="menu-divider"></div>
      <div class="menu-item" @click="handleInsertRowAbove">
        <el-icon><Plus /></el-icon>
        在上方插入行
      </div>
      <div class="menu-item" @click="handleInsertRowBelow">
        <el-icon><Plus /></el-icon>
        在下方插入行
      </div>
      <div class="menu-item" @click="handleMergeCells" :class="{ disabled: !canMerge }">
        <el-icon><Edit /></el-icon>
        合并单元格（同列填充为首值）
      </div>
      <div class="menu-item" @click="handleDeleteSelectedRows" :class="{ disabled: selectedRows.size === 0 }">
        <el-icon><Delete /></el-icon>
        删除选中行
      </div>
    </div>
    
    <!-- 遮罩层，用于关闭右键菜单 -->
    <div 
      v-if="showContextMenu"
      class="context-menu-overlay"
      @click="closeContextMenu"
    ></div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Edit, Delete, Plus, DocumentCopy, Document } from '@element-plus/icons-vue'

// Props
const props = defineProps({
  data: {
    type: Array,
    default: () => []
  },
  columns: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  total: {
    type: Number,
    default: 0
  },
  currentPage: {
    type: Number,
    default: 1
  },
  pageSize: {
    type: Number,
    default: 50
  },
  // 需要纵向合并的列（按连续相同值合并）
  mergeColumns: {
    type: Array,
    default: () => []
  }
})

// Emits
const emit = defineEmits([
  'page-change',
  'size-change', 
  'cell-edit',
  'row-delete',
  'selection-change',
  'insert-row-above',
  'insert-row-below'
])

// 响应式数据
const tableContainer = ref(null)
const cellInput = ref(null)
const hoverRowIndex = ref(-1)
const selectedRows = ref(new Set())
const selectedCells = ref(new Set())
const selectAll = ref(false)
const isSelecting = ref(false)
const selectionStart = ref(null)
const selectionEnd = ref(null)

// 编辑相关
const editingCell = ref(null)
const editingValue = ref('')

// 右键菜单
const showContextMenu = ref(false)
const contextMenuX = ref(0)
const contextMenuY = ref(0)
const clipboardData = ref('')
const contextRowIndex = ref(-1)
const contextProp = ref('')

// 行选择相关
const lastSelectedRow = ref(-1)
const isRowDragging = ref(false)
const dragStartRow = ref(-1)

// 计算属性
const currentPage = computed({
  get: () => props.currentPage,
  set: (value) => emit('page-change', value)
})

const pageSize = computed({
  get: () => props.pageSize,
  set: (value) => emit('size-change', value)
})

// 合并单元格映射：对 mergeColumns 中的每个列，计算每一行的 rowspan（0 表示被合并隐藏）
const rowspanMap = computed(() => {
  const map = {}
  const rows = props.data || []
  const mergeCols = Array.isArray(props.mergeColumns) ? props.mergeColumns : []
  for (const prop of mergeCols) {
    const spans = Array(rows.length).fill(1)
    let i = 0
    while (i < rows.length) {
      const start = i
      const val = rows[i]?.[prop] ?? ''
      while (i < rows.length && (rows[i]?.[prop] ?? '') === val) i++
      const len = i - start
      spans[start] = len
      for (let k = start + 1; k < start + len; k++) spans[k] = 0
    }
    map[prop] = spans
  }
  return map
})

const getRowspan = (rowIndex, prop) => {
  // 未配置合并的列默认不合并（rowspan=1）
  if (!props.mergeColumns || !props.mergeColumns.includes(prop)) return 1
  const colMap = rowspanMap.value[prop]
  if (!colMap) return 1
  return colMap[rowIndex] ?? 1
}

const canMerge = computed(() => {
  if (!contextProp.value) return false
  // 统计选中同列的单元格数量
  let count = 0
  for (const key of selectedCells.value) {
    const [, col] = key.split('-')
    if (col === contextProp.value) count++
  }
  return count >= 2
})

// 生命周期
onMounted(() => {
  document.addEventListener('click', closeContextMenu)
  document.addEventListener('keydown', handleGlobalKeyDown)
})

onUnmounted(() => {
  document.removeEventListener('click', closeContextMenu)
  document.removeEventListener('keydown', handleGlobalKeyDown)
})

// 方法
const getCellDisplayValue = (row, column) => {
  const value = row[column.prop]
  if (column.formatter && typeof column.formatter === 'function') {
    return column.formatter(row)
  }
  return value || ''
}

const handleSelectAll = () => {
  if (selectAll.value) {
    selectedRows.value = new Set(Array.from({ length: props.data.length }, (_, i) => i))
  } else {
    selectedRows.value.clear()
  }
  emit('selection-change', Array.from(selectedRows.value).map(index => props.data[index]))
}

const handleRowSelect = (rowIndex, event) => {
  if (event && event.shiftKey && lastSelectedRow.value >= 0) {
    // Shift+点击：范围选择
    const start = Math.min(lastSelectedRow.value, rowIndex)
    const end = Math.max(lastSelectedRow.value, rowIndex)
    selectedRows.value.clear()
    for (let i = start; i <= end; i++) {
      selectedRows.value.add(i)
    }
  } else if (event && event.ctrlKey) {
    // Ctrl+点击：多选
    if (selectedRows.value.has(rowIndex)) {
      selectedRows.value.delete(rowIndex)
    } else {
      selectedRows.value.add(rowIndex)
    }
    lastSelectedRow.value = rowIndex
  } else {
    // 普通点击：单选
    selectedRows.value.clear()
    selectedRows.value.add(rowIndex)
    lastSelectedRow.value = rowIndex
  }
  updateSelectAllState()
  emit('selection-change', Array.from(selectedRows.value).map(index => props.data[index]))
}

const handleRowCheckChange = (rowIndex, event) => {
  if (event.target.checked) {
    selectedRows.value.add(rowIndex)
  } else {
    selectedRows.value.delete(rowIndex)
  }
  updateSelectAllState()
  emit('selection-change', Array.from(selectedRows.value).map(index => props.data[index]))
}

const updateSelectAllState = () => {
  selectAll.value = selectedRows.value.size === props.data.length && props.data.length > 0
}

const handleColumnSelect = (prop) => {
  selectedCells.value.clear()
  props.data.forEach((_, rowIndex) => {
    selectedCells.value.add(`${rowIndex}-${prop}`)
  })
}

const handleCellClick = (rowIndex, prop, event) => {
  if (event.ctrlKey || event.metaKey) {
    // Ctrl+点击，多选单元格
    const cellKey = `${rowIndex}-${prop}`
    if (selectedCells.value.has(cellKey)) {
      selectedCells.value.delete(cellKey)
    } else {
      selectedCells.value.add(cellKey)
    }
  } else if (event.shiftKey && selectionStart.value) {
    // Shift+点击，选择区域
    selectCellRange(selectionStart.value, { row: rowIndex, col: prop })
  } else {
    // 普通点击，选择单个单元格
    selectedCells.value.clear()
    selectedCells.value.add(`${rowIndex}-${prop}`)
    selectionStart.value = { row: rowIndex, col: prop }
  }
}

const handleCellDoubleClick = (rowIndex, prop) => {
  const column = props.columns.find(col => col.prop === prop)
  if (column && column.editable !== false) {
    startCellEdit(rowIndex, prop)
  }
}

const startCellEdit = async (rowIndex, prop) => {
  const row = props.data[rowIndex]
  editingCell.value = { row: rowIndex, prop }
  editingValue.value = row[prop] || ''
  
  await nextTick()
  if (cellInput.value) {
    if (Array.isArray(cellInput.value)) {
      cellInput.value[0].focus()
      cellInput.value[0].select()
    } else {
      cellInput.value.focus()
      cellInput.value.select()
    }
  }
}

const handleCellEditComplete = () => {
  if (editingCell.value) {
    const { row, prop } = editingCell.value
    const oldValue = props.data[row][prop]
    const newValue = editingValue.value
    
    if (oldValue !== newValue) {
      emit('cell-edit', props.data[row], prop, newValue)
    }
    
    editingCell.value = null
    editingValue.value = ''
  }
}

const handleCellKeyDown = (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    handleCellEditComplete()
  } else if (event.key === 'Escape') {
    event.preventDefault()
    editingCell.value = null
    editingValue.value = ''
  }
}

const selectCellRange = (start, end) => {
  selectedCells.value.clear()
  
  const startRow = Math.min(start.row, end.row)
  const endRow = Math.max(start.row, end.row)
  const startColIndex = props.columns.findIndex(col => col.prop === start.col)
  const endColIndex = props.columns.findIndex(col => col.prop === end.col)
  const startCol = Math.min(startColIndex, endColIndex)
  const endCol = Math.max(startColIndex, endColIndex)
  
  for (let row = startRow; row <= endRow; row++) {
    for (let col = startCol; col <= endCol; col++) {
      selectedCells.value.add(`${row}-${props.columns[col].prop}`)
    }
  }
}

const handleMouseDown = (event) => {
  if (event.target.closest('.cell-content')) {
    isSelecting.value = true
    const cell = event.target.closest('td')
    if (cell) {
      const rowIndex = parseInt(cell.dataset.row)
      const colProp = cell.dataset.col
      selectionStart.value = { row: rowIndex, col: colProp }
    }
  }
}

const handleMouseMove = (event) => {
  if (isSelecting.value && selectionStart.value) {
    const cell = event.target.closest('td')
    if (cell && cell.dataset.row !== undefined && cell.dataset.col) {
      const rowIndex = parseInt(cell.dataset.row)
      const colProp = cell.dataset.col
      selectCellRange(selectionStart.value, { row: rowIndex, col: colProp })
    }
  }
}

const handleMouseUp = () => {
  isSelecting.value = false
  isRowDragging.value = false
}

// 行拖拽选择
const handleRowMouseDown = (rowIndex, event) => {
  if (event.button === 0) { // 只处理左键
    isRowDragging.value = true
    dragStartRow.value = rowIndex
    // 阻止文本选择
    event.preventDefault()
  }
}

const handleRowMouseEnter = (rowIndex, event) => {
  if (isRowDragging.value && dragStartRow.value >= 0) {
    // 拖拽选择行范围
    const start = Math.min(dragStartRow.value, rowIndex)
    const end = Math.max(dragStartRow.value, rowIndex)
    selectedRows.value.clear()
    for (let i = start; i <= end; i++) {
      selectedRows.value.add(i)
    }
    lastSelectedRow.value = rowIndex
    updateSelectAllState()
    emit('selection-change', Array.from(selectedRows.value).map(index => props.data[index]))
  }
}

const handleContextMenu = (event, rowIndex, prop) => {
  event.preventDefault()
  // 寻找最近的td以读取行列
  const td = event.target.closest('td')
  const rowAttr = td?.getAttribute('data-row')
  const colAttr = td?.getAttribute('data-col')
  contextRowIndex.value = rowAttr != null ? parseInt(rowAttr) : rowIndex
  contextProp.value = colAttr || prop
  contextMenuX.value = event.clientX
  contextMenuY.value = event.clientY
  showContextMenu.value = true
}

const closeContextMenu = () => {
  showContextMenu.value = false
}

const handleCopy = () => {
  const selectedData = []
  const sortedCells = Array.from(selectedCells.value).sort((a, b) => {
    const [aRow, aCol] = a.split('-')
    const [bRow, bCol] = b.split('-')
    if (aRow !== bRow) return parseInt(aRow) - parseInt(bRow)
    const aColIndex = props.columns.findIndex(col => col.prop === aCol)
    const bColIndex = props.columns.findIndex(col => col.prop === bCol)
    return aColIndex - bColIndex
  })
  
  let currentRow = -1
  let rowData = []
  
  sortedCells.forEach(cellKey => {
    const [row, col] = cellKey.split('-')
    const rowIndex = parseInt(row)
    
    if (rowIndex !== currentRow) {
      if (rowData.length > 0) {
        selectedData.push(rowData.join('\t'))
      }
      currentRow = rowIndex
      rowData = []
    }
    
    const value = props.data[rowIndex][col] || ''
    rowData.push(value)
  })
  
  if (rowData.length > 0) {
    selectedData.push(rowData.join('\t'))
  }
  
  clipboardData.value = selectedData.join('\n')
  navigator.clipboard.writeText(clipboardData.value)
  ElMessage.success('已复制到剪贴板')
  closeContextMenu()
}

const handlePaste = async () => {
  try {
    const text = await navigator.clipboard.readText()
    ElMessage.info('粘贴功能开发中...')
  } catch (error) {
    ElMessage.error('无法访问剪贴板')
  }
  closeContextMenu()
}

const handleInsertRowAbove = () => {
  if (contextRowIndex.value >= 0) emit('insert-row-above', props.data[contextRowIndex.value])
  closeContextMenu()
}

const handleInsertRowBelow = () => {
  if (contextRowIndex.value >= 0) emit('insert-row-below', props.data[contextRowIndex.value])
  closeContextMenu()
}

const handleMergeCells = () => {
  if (!canMerge.value) return
  // 选择同列的首个值作为合并值
  let mergeValue = ''
  const rowsInCol = []
  const colProp = contextProp.value
  const sorted = Array.from(selectedCells.value)
    .filter(k => k.endsWith(`-${colProp}`))
    .sort((a, b) => parseInt(a.split('-')[0]) - parseInt(b.split('-')[0]))
  for (const key of sorted) {
    const [rowStr] = key.split('-')
    const ri = parseInt(rowStr)
    rowsInCol.push(ri)
    if (mergeValue === '') mergeValue = props.data[ri]?.[colProp] ?? ''
  }
  // 广播到父级逐个保存
  for (const ri of rowsInCol) {
    emit('cell-edit', props.data[ri], colProp, mergeValue)
  }
  ElMessage.success('已合并同列单元格')
  closeContextMenu()
}

const handleDeleteSelectedRows = async () => {
  if (selectedRows.value.size === 0) return
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedRows.value.size} 行数据吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const selectedRowsArray = Array.from(selectedRows.value).sort((a, b) => b - a)
    for (const rowIndex of selectedRowsArray) {
      emit('row-delete', props.data[rowIndex])
    }
    
    selectedRows.value.clear()
    updateSelectAllState()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
  closeContextMenu()
}

const handleEdit = (row, rowIndex) => {
  // 触发编辑事件，由父组件处理
  ElMessage.info('请双击单元格进行编辑')
}

const handleDelete = (row) => {
  emit('row-delete', row)
}

const handleCurrentChange = (page) => {
  emit('page-change', page)
}

const handleSizeChange = (size) => {
  emit('size-change', size)
}

const handleGlobalKeyDown = (event) => {
  if (event.ctrlKey || event.metaKey) {
    switch (event.key) {
      case 'c':
        if (selectedCells.value.size > 0) {
          event.preventDefault()
          handleCopy()
        }
        break
      case 'v':
        if (selectedCells.value.size > 0) {
          event.preventDefault()
          handlePaste()
        }
        break
      case 'a':
        if (tableContainer.value?.contains(document.activeElement)) {
          event.preventDefault()
          // 全选所有单元格
          selectedCells.value.clear()
          props.data.forEach((_, rowIndex) => {
            props.columns.forEach(column => {
              selectedCells.value.add(`${rowIndex}-${column.prop}`)
            })
          })
        }
        break
    }
  } else if (event.key === 'Delete') {
    if (selectedRows.value.size > 0) {
      event.preventDefault()
      handleDeleteSelectedRows()
    }
  }
}
</script>

<style scoped>
.spreadsheet-table {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.table-container {
  flex: 1;
  overflow: auto;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
}

.excel-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 12px;
  user-select: none;
}

.excel-table th,
.excel-table td {
  border-right: 1px solid #e4e7ed;
  border-bottom: 1px solid #e4e7ed;
  padding: 0;
  height: 32px;
  vertical-align: middle;
  position: relative;
}

.row-number-header,
.column-header {
  background: #f5f7fa;
  font-weight: bold;
  text-align: center;
  color: #606266;
  position: sticky;
  top: 0;
  z-index: 10;
}

.row-number-header {
  width: 60px;
  position: sticky;
  left: 0;
  z-index: 11;
}

.column-header {
  cursor: pointer;
  transition: background-color 0.2s;
}

.column-header:hover {
  background: #e6f7ff;
}

.row-number {
  background: #f5f7fa;
  width: 60px;
  text-align: center;
  position: sticky;
  left: 0;
  z-index: 9;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  font-size: 11px;
  color: #909399;
}

.row-index {
  font-weight: bold;
}

.selected-row {
  background: #e6f7ff !important;
}

.hover-row:hover {
  background: #f0f9ff;
}

.selected-cell {
  background: #e6f7ff !important;
  border: 2px solid #409eff !important;
}

.editing-cell {
  background: #fff !important;
  border: 2px solid #67c23a !important;
}

.editable-cell {
  cursor: text;
}

.cell-content {
  padding: 6px 8px;
  min-height: 20px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 20px;
}

.cell-editor {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 100;
}

.cell-input,
.cell-textarea {
  width: 100%;
  height: 100%;
  border: none;
  outline: none;
  padding: 6px 8px;
  font-size: 12px;
  background: white;
  resize: none;
  font-family: inherit;
}

.cell-textarea {
  min-height: 60px;
}

.row-actions {
  position: absolute;
  right: 5px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  gap: 5px;
  z-index: 50;
}

.pagination-container {
  padding: 15px;
  border-top: 1px solid #e4e7ed;
  background: white;
}

.context-menu {
  position: fixed;
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  z-index: 2000;
  min-width: 150px;
}

.menu-item {
  padding: 8px 15px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #606266;
  transition: background-color 0.2s;
}

.menu-item:hover:not(.disabled) {
  background: #f5f7fa;
  color: #409eff;
}

.menu-item.disabled {
  color: #c0c4cc;
  cursor: not-allowed;
}

.menu-divider {
  height: 1px;
  background: #e4e7ed;
  margin: 5px 0;
}

.context-menu-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1999;
}

/* 滚动条样式 */
.table-container::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.table-container::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.table-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.table-container::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style> 