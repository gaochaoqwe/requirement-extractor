import { ref, computed } from 'vue'

export function useTableSelection() {
  // 选择状态
  const selectedCells = ref([])
  const selectedRows = ref([])
  const selectedColumns = ref([])

  // 计算属性
  const currentCellName = computed(() => {
    if (selectedCells.value.length === 1) {
      const cell = selectedCells.value[0]
      const colName = String.fromCharCode(65 + cell.col) // A, B, C...
      return `${colName}${cell.row + 1}`
    }
    return ''
  })

  // 方法
  const isCellSelected = (row, col) => {
    return selectedCells.value.some(cell => cell.row === row && cell.col === col)
  }

  const selectCell = (row, col, event, getCellValue, sortedData, columns, formulaValue) => {
    if (event.ctrlKey) {
      // Ctrl+点击：多选
      const index = selectedCells.value.findIndex(cell => cell.row === row && cell.col === col)
      if (index > -1) {
        selectedCells.value.splice(index, 1)
      } else {
        selectedCells.value.push({ row, col })
      }
    } else if (event.shiftKey && selectedCells.value.length > 0) {
      // Shift+点击：范围选择
      const lastCell = selectedCells.value[selectedCells.value.length - 1]
      selectRange(lastCell.row, lastCell.col, row, col)
    } else {
      // 普通点击：单选
      selectedCells.value = [{ row, col }]
      selectedRows.value = []
      selectedColumns.value = []
      
      // 更新公式栏
      const cellValue = getCellValue(sortedData.value[row], columns.value[col].key)
      formulaValue.value = cellValue
    }
  }

  const selectRange = (startRow, startCol, endRow, endCol) => {
    selectedCells.value = []
    const minRow = Math.min(startRow, endRow)
    const maxRow = Math.max(startRow, endRow)
    const minCol = Math.min(startCol, endCol)
    const maxCol = Math.max(startCol, endCol)
    
    for (let r = minRow; r <= maxRow; r++) {
      for (let c = minCol; c <= maxCol; c++) {
        selectedCells.value.push({ row: r, col: c })
      }
    }
  }

  const selectRow = (row) => {
    if (selectedRows.value.includes(row)) {
      selectedRows.value = selectedRows.value.filter(r => r !== row)
    } else {
      selectedRows.value = [row]
    }
    selectedCells.value = []
    selectedColumns.value = []
  }

  const selectColumn = (col) => {
    if (selectedColumns.value.includes(col)) {
      selectedColumns.value = selectedColumns.value.filter(c => c !== col)
    } else {
      selectedColumns.value = [col]
    }
    selectedCells.value = []
    selectedRows.value = []
  }

  const selectAll = (sortedData, columns) => {
    selectedCells.value = []
    for (let row = 0; row < sortedData.value.length; row++) {
      for (let col = 0; col < columns.value.length; col++) {
        selectedCells.value.push({ row, col })
      }
    }
    selectedRows.value = []
    selectedColumns.value = []
  }

  const clearSelection = () => {
    selectedCells.value = []
    selectedRows.value = []
    selectedColumns.value = []
  }

  return {
    // 数据
    selectedCells,
    selectedRows,
    selectedColumns,
    
    // 计算属性
    currentCellName,
    
    // 方法
    isCellSelected,
    selectCell,
    selectRange,
    selectRow,
    selectColumn,
    selectAll,
    clearSelection
  }
} 