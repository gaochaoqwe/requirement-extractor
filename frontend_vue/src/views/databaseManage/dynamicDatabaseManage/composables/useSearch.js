import { ref, nextTick } from 'vue'

export function useSearch() {
  const searchResults = ref([])
  const currentSearchIndex = ref(-1)

  // 执行搜索
  const performSearch = (searchText, sortedData, columns, getCellValue) => {
    searchResults.value = []
    currentSearchIndex.value = -1
    
    if (!searchText.trim()) return
    
    const searchTerm = searchText.toLowerCase()
    
    sortedData.value.forEach((row, rowIndex) => {
      columns.value.forEach((column, colIndex) => {
        const cellValue = getCellValue(row, column.key)
        if (String(cellValue).toLowerCase().includes(searchTerm)) {
          searchResults.value.push({ row: rowIndex, col: colIndex })
        }
      })
    })
    
    if (searchResults.value.length > 0) {
      currentSearchIndex.value = 0
      highlightSearchResult()
    }
  }

  // 查找下一个
  const findNext = (searchText, sortedData, columns, getCellValue) => {
    if (searchResults.value.length === 0) {
      performSearch(searchText, sortedData, columns, getCellValue)
      return
    }
    
    currentSearchIndex.value = (currentSearchIndex.value + 1) % searchResults.value.length
    highlightSearchResult()
  }

  // 查找上一个
  const findPrevious = (searchText, sortedData, columns, getCellValue) => {
    if (searchResults.value.length === 0) {
      performSearch(searchText, sortedData, columns, getCellValue)
      return
    }
    
    currentSearchIndex.value = currentSearchIndex.value <= 0 
      ? searchResults.value.length - 1 
      : currentSearchIndex.value - 1
    highlightSearchResult()
  }

  // 高亮搜索结果
  const highlightSearchResult = () => {
    if (currentSearchIndex.value >= 0 && currentSearchIndex.value < searchResults.value.length) {
      const result = searchResults.value[currentSearchIndex.value]
      
      // 滚动到可见区域
      nextTick(() => {
        const tableBody = document.querySelector('.table-body')
        const targetRow = document.querySelector(`.table-row:nth-child(${result.row + 1})`)
        if (tableBody && targetRow) {
          targetRow.scrollIntoView({ behavior: 'smooth', block: 'center' })
        }
      })
    }
  }

  // 清除搜索
  const clearSearch = () => {
    searchResults.value = []
    currentSearchIndex.value = -1
  }

  // 检查单元格是否匹配搜索
  const isCellSearchMatch = (row, col) => {
    return searchResults.value.some(result => result.row === row && result.col === col)
  }

  // 检查行是否高亮
  const isRowHighlighted = (rowIndex) => {
    return searchResults.value.some(result => result.row === rowIndex)
  }

  return {
    searchResults,
    currentSearchIndex,
    performSearch,
    findNext,
    findPrevious,
    clearSearch,
    isCellSearchMatch,
    isRowHighlighted
  }
} 