import { ref, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { databaseManageService } from '@/services/databaseManageService'

export function useTableEdit() {
  // 编辑状态
  const editingCell = ref(null)
  const editingValue = ref('')
  const cellInput = ref(null)
  const formulaValue = ref('')
  
  // 持久化策略
  const pendingChanges = ref(new Map()) // 待保存的更改
  const autoSaveTimer = ref(null)
  const isDirty = ref(false) // 是否有未保存的更改

  // 持久化策略配置
  const PERSISTENCE_STRATEGY = {
    AUTO_SAVE_DELAY: 2000, // 2秒后自动保存
    BATCH_SAVE_SIZE: 10,   // 批量保存阈值
    IMMEDIATE_SAVE: ['delete', 'create'], // 立即保存的操作
    DEBOUNCED_SAVE: ['edit', 'update']    // 防抖保存的操作
  }

  // 开始编辑
  const startEdit = (row, col, getCellValue, sortedData, columns) => {
    editingCell.value = { row, col }
    const currentValue = getCellValue(sortedData.value[row], columns.value[col].key)
    editingValue.value = currentValue
    formulaValue.value = currentValue

    nextTick(() => {
      if (cellInput.value) {
        cellInput.value.focus()
      }
    })
  }

  // 完成编辑 - 使用防抖保存策略
  const finishEdit = async (data, sortedData, columns) => {
    if (!editingCell.value) return
    
    const { row, col } = editingCell.value
    const rowData = sortedData.value[row]
    const column = columns.value[col]
    
    try {
      const dataIndex = data.value.findIndex(r => r.id === rowData.id)
      if (dataIndex >= 0) {
        const id = data.value[dataIndex].id
        const oldValue = data.value[dataIndex][column.key]
        const newValue = editingValue.value
        
        // 只有值真正改变时才保存
        if (oldValue !== newValue) {
          // 更新本地数据
          data.value[dataIndex] = { ...data.value[dataIndex], [column.key]: newValue }
          
          // 添加到待保存队列（防抖保存）
          addToPendingChanges(id, column.key, newValue, 'edit')
          
          ElMessage.success('已保存')
        }
      }
    } catch (e) {
      ElMessage.error('保存失败：' + (e.message || e))
    }
    
    editingCell.value = null
    editingValue.value = ''
  }

  // 取消编辑
  const cancelEdit = () => {
    editingCell.value = null
    editingValue.value = ''
  }

  // 应用公式栏内容
  const applyFormula = (selectedCells) => {
    if (selectedCells.value.length === 1) {
      const cell = selectedCells.value[0]
      editingCell.value = { row: cell.row, col: cell.col }
      editingValue.value = formulaValue.value
      return true // 表示需要调用finishEdit
    }
    return false
  }

  // 添加到待保存队列
  const addToPendingChanges = (id, field, value, operation) => {
    const key = `${id}_${field}`
    pendingChanges.value.set(key, {
      id,
      field,
      value,
      operation,
      timestamp: Date.now()
    })
    
    isDirty.value = true
    
    // 根据操作类型决定保存策略
    if (PERSISTENCE_STRATEGY.IMMEDIATE_SAVE.includes(operation)) {
      // 立即保存
      savePendingChanges()
    } else if (PERSISTENCE_STRATEGY.DEBOUNCED_SAVE.includes(operation)) {
      // 防抖保存
      scheduleAutoSave()
    }
  }

  // 调度自动保存
  const scheduleAutoSave = () => {
    if (autoSaveTimer.value) {
      clearTimeout(autoSaveTimer.value)
    }
    
    autoSaveTimer.value = setTimeout(() => {
      savePendingChanges()
    }, PERSISTENCE_STRATEGY.AUTO_SAVE_DELAY)
  }

  // 保存待处理的更改
  const savePendingChanges = async () => {
    if (pendingChanges.value.size === 0) return
    
    const changes = Array.from(pendingChanges.value.values())
    pendingChanges.value.clear()
    isDirty.value = false
    
    if (autoSaveTimer.value) {
      clearTimeout(autoSaveTimer.value)
      autoSaveTimer.value = null
    }
    
    try {
      // 批量保存
      for (const change of changes) {
        await databaseManageService.updateCell(change.id, change.field, change.value)
      }
      
      if (changes.length > 1) {
        ElMessage.success(`批量保存了 ${changes.length} 个更改`)
      }
    } catch (error) {
      ElMessage.error('批量保存失败: ' + error.message)
      
      // 保存失败，重新添加到队列
      changes.forEach(change => {
        const key = `${change.id}_${change.field}`
        pendingChanges.value.set(key, change)
      })
      isDirty.value = true
    }
  }

  // Ctrl+S 手动保存
  const manualSave = async () => {
    if (pendingChanges.value.size === 0) {
      ElMessage.info('没有需要保存的更改')
      return
    }
    
    await savePendingChanges()
    ElMessage.success('手动保存完成')
  }

  // 立即保存单个更改（用于删除、创建等操作）
  const immediateUpdate = async (id, field, value) => {
    try {
      await databaseManageService.updateCell(id, field, value)
      return true
    } catch (error) {
      ElMessage.error('保存失败: ' + error.message)
      return false
    }
  }

  // 清理资源
  const cleanup = () => {
    if (autoSaveTimer.value) {
      clearTimeout(autoSaveTimer.value)
    }
  }

  return {
    // 数据
    editingCell,
    editingValue,
    cellInput,
    formulaValue,
    isDirty,
    
    // 方法
    startEdit,
    finishEdit,
    cancelEdit,
    applyFormula,
    addToPendingChanges,
    savePendingChanges,
    manualSave,
    immediateUpdate,
    cleanup
  }
} 