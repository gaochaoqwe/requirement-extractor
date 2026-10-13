import { ElLoading, ElMessage } from 'element-plus'

import {
  createEmptySheetData,
  readWorkbookSheetsWithProgress,
  exportWorkbookFromSheets,
} from '../utils/xlsxAdapter'

export const useSpreadsheetIO = ({
  spreadsheet,
  spreadsheetReady,
  exportFilename,
  sheetList,
  reloadSpreadsheetWithData,
  onAfterImport,
}) => {
  const handleFileChange = async (file) => {
    let loadingInstance = null
    try {
      if (!file?.raw) {
        ElMessage.error('请选择有效的Excel文件')
        return
      }

      loadingInstance = ElLoading.service({
        lock: true,
        text: '正在读取Excel... ',
        background: 'rgba(0, 0, 0, 0.2)',
      })

      const arrayBuffer = await file.raw.arrayBuffer()
      const { sheets, meta } = await readWorkbookSheetsWithProgress(
        arrayBuffer,
        { minRows: 100, maxRows: 10000, maxCols: 200 },  // 增加maxRows到10000，确保minRows也传递
        ({ index, total, name }) => {
          if (loadingInstance) {
            loadingInstance.setText(`正在导入Sheet：${name}（${index}/${total}）`)
          }
        }
      )

      if (!sheets.length) {
        ElMessage.error('Excel中没有工作表')
        return
      }

      if (!spreadsheet.value) {
        ElMessage.error('表格未初始化')
        return
      }

      sheetList.value = sheets
      reloadSpreadsheetWithData(sheets)

      // 导入后同步文件名（去掉路径，保留扩展名）
      if (exportFilename && file.raw?.name) {
        exportFilename.value = file.raw.name
      }

      try {
        if (typeof onAfterImport === 'function') {
          await onAfterImport({ file, sheets, meta })
        }
      } catch (e) {
        console.error(e)
        ElMessage.warning('导入后处理失败：' + (e?.message || '未知错误'))
      }

      const hiddenTip = meta?.skippedHiddenSheetCount ? `，已跳过隐藏Sheet：${meta.skippedHiddenSheetCount} 个` : ''
      if (meta?.truncatedSheetCount) {
        ElMessage.warning(
          `已导入：${sheets.length} 个Sheet（其中 ${meta.truncatedSheetCount} 个Sheet被截断，限制为最多 ${meta.maxRows} 行 / ${meta.maxCols} 列）${hiddenTip}`
        )
      } else {
        ElMessage.success(`已导入：${sheets.length} 个Sheet${hiddenTip}`)
      }
    } catch (e) {
      console.error(e)
      ElMessage.error('导入失败：' + (e?.message || '未知错误'))
    } finally {
      if (loadingInstance) loadingInstance.close()
    }
  }

  const exportXlsx = () => {
    try {
      if (!spreadsheet.value) {
        ElMessage.error('表格未初始化')
        return
      }

      const raw = spreadsheet.value.getData()
      const sheets = Array.isArray(raw) ? raw : [raw]
      const name = exportFilename.value?.trim() || 'test_case_assistant.xlsx'
      const filename = name.toLowerCase().endsWith('.xlsx') ? name : `${name}.xlsx`
      exportWorkbookFromSheets(sheets, filename)
      ElMessage.success('导出完成')
    } catch (e) {
      console.error(e)
      ElMessage.error('导出失败：' + (e?.message || '未知错误'))
    }
  }

  const resetSheet = () => {
    if (!spreadsheet.value) return
    const first = createEmptySheetData('Sheet1')
    sheetList.value = [first]
    reloadSpreadsheetWithData([first])
  }

  return {
    handleFileChange,
    exportXlsx,
    resetSheet,
  }
}
