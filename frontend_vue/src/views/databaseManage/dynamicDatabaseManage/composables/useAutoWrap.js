import { ref, nextTick } from 'vue'

export function useAutoWrap() {
  const autoWrapEnabled = ref(false)
  const rowHeights = ref(new Map()) // 存储每行的高度

  // 计算文本行数
  const calculateTextLines = (text, width, fontSize = 12) => {
    if (!text) return 1
    
    // 创建临时canvas来测量文本宽度
    const canvas = document.createElement('canvas')
    const context = canvas.getContext('2d')
    context.font = `${fontSize}px 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif`
    
    const lines = String(text).split('\n')
    let totalLines = 0
    
    lines.forEach(line => {
      if (!line.trim()) {
        totalLines += 1
        return
      }
      
      const textWidth = context.measureText(line).width
      const linesNeeded = Math.ceil(textWidth / (width - 16)) // 减去padding
      totalLines += Math.max(1, linesNeeded)
    })
    
    return totalLines
  }

  // 计算行高
  const calculateRowHeight = (row, columns, columnWidths) => {
    if (!autoWrapEnabled.value) return 32 // 默认行高
    
    let maxLines = 1
    
    columns.value.forEach(column => {
      const cellValue = row[column.key] || ''
      const columnWidth = columnWidths[column.key] || 200
      
      // 对于多行文本字段，计算需要的行数
      if (column.key === 'test_item_description' || column.key === 'test_method') {
        const lines = calculateTextLines(cellValue, columnWidth)
        maxLines = Math.max(maxLines, lines)
      }
    })
    
    // 每行文本高度约20px，最小32px
    return Math.max(32, maxLines * 20 + 12) // 12px为上下padding
  }

  // 更新所有行高
  const updateAllRowHeights = (sortedData, columns, columnWidths) => {
    if (!autoWrapEnabled.value) {
      rowHeights.value.clear()
      return
    }
    
    sortedData.value.forEach((row, index) => {
      const height = calculateRowHeight(row, columns, columnWidths)
      rowHeights.value.set(index, height)
    })
    
    // 触发DOM更新
    nextTick(() => {
      updateTableRowHeights()
    })
  }

  // 更新单行高度
  const updateRowHeight = (rowIndex, row, columns, columnWidths) => {
    if (!autoWrapEnabled.value) return
    
    const height = calculateRowHeight(row, columns, columnWidths)
    rowHeights.value.set(rowIndex, height)
    
    nextTick(() => {
      updateSingleRowHeight(rowIndex, height)
    })
  }

  // 更新DOM中的行高
  const updateTableRowHeights = () => {
    const tableRows = document.querySelectorAll('.table-row')
    tableRows.forEach((row, index) => {
      const height = rowHeights.value.get(index)
      if (height) {
        row.style.height = `${height}px`
        
        // 更新单元格高度
        const cells = row.querySelectorAll('.table-cell')
        cells.forEach(cell => {
          cell.style.height = `${height}px`
        })
        
        // 更新行号高度
        const rowNumber = row.querySelector('.row-number')
        if (rowNumber) {
          rowNumber.style.height = `${height}px`
        }
      }
    })
  }

  // 更新单个行的高度
  const updateSingleRowHeight = (rowIndex, height) => {
    const tableRow = document.querySelector(`.table-row:nth-child(${rowIndex + 1})`)
    if (tableRow) {
      tableRow.style.height = `${height}px`
      
      const cells = tableRow.querySelectorAll('.table-cell')
      cells.forEach(cell => {
        cell.style.height = `${height}px`
      })
      
      const rowNumber = tableRow.querySelector('.row-number')
      if (rowNumber) {
        rowNumber.style.height = `${height}px`
      }
    }
  }

  // 切换自动换行
  const toggleAutoWrap = (sortedData, columns, columnWidths) => {
    autoWrapEnabled.value = !autoWrapEnabled.value
    
    if (autoWrapEnabled.value) {
      updateAllRowHeights(sortedData, columns, columnWidths)
    } else {
      // 恢复默认行高
      rowHeights.value.clear()
      nextTick(() => {
        const tableRows = document.querySelectorAll('.table-row')
        tableRows.forEach(row => {
          row.style.height = '32px'
          
          const cells = row.querySelectorAll('.table-cell')
          cells.forEach(cell => {
            cell.style.height = '32px'
          })
          
          const rowNumber = row.querySelector('.row-number')
          if (rowNumber) {
            rowNumber.style.height = '32px'
          }
        })
      })
    }
  }

  // 应用自动换行到选中的单元格
  const applyAutoWrapToSelection = (selectedCells, sortedData, columns, columnWidths) => {
    if (selectedCells.value.length === 0) return
    
    // 获取涉及的行
    const affectedRows = new Set()
    selectedCells.value.forEach(cell => {
      affectedRows.add(cell.row)
    })
    
    // 更新这些行的高度
    affectedRows.forEach(rowIndex => {
      const row = sortedData.value[rowIndex]
      if (row) {
        updateRowHeight(rowIndex, row, columns, columnWidths)
      }
    })
  }

  // 获取行高
  const getRowHeight = (rowIndex) => {
    return rowHeights.value.get(rowIndex) || 32
  }

  return {
    // 数据
    autoWrapEnabled,
    rowHeights,
    
    // 方法
    calculateTextLines,
    calculateRowHeight,
    updateAllRowHeights,
    updateRowHeight,
    toggleAutoWrap,
    applyAutoWrapToSelection,
    getRowHeight
  }
} 