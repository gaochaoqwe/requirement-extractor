import { ElMessage, ElMessageBox } from 'element-plus'

import { draftSet, draftGet, draftDel } from '../utils/draftStore'
import { createEmptySheetData } from '../utils/xlsxAdapter'

export const useSpreadsheetDraft = ({
  spreadsheet,
  sheetList,
  reloadSpreadsheetWithData,
  draftKey = 'default',
}) => {
  const saveDraft = async (options = {}) => {
    const { silent = false } = options || {}
    try {
      if (!spreadsheet.value) {
        ElMessage.error('表格未初始化')
        return
      }

      const raw = spreadsheet.value.getData()
      const sheets = Array.isArray(raw) ? raw : [raw]
      const data = JSON.parse(JSON.stringify(sheets))
      await draftSet(draftKey, {
        version: 1,
        savedAt: Date.now(),
        data,
      })
      if (!silent) ElMessage.success('草稿已保存')
    } catch (e) {
      console.error(e)
      ElMessage.error('保存草稿失败：' + (e?.message || '未知错误'))
    }
  }

  const loadDraft = async () => {
    try {
      if (!spreadsheet.value) {
        ElMessage.error('表格未初始化')
        return
      }

      const draft = await draftGet(draftKey)
      if (!draft?.data) {
        ElMessage.warning('暂无草稿可加载')
        return
      }

      await ElMessageBox.confirm('加载草稿将覆盖当前表格内容，是否继续？', '提示', {
        confirmButtonText: '继续',
        cancelButtonText: '取消',
        type: 'warning',
      })

      const sheets = Array.isArray(draft.data) && draft.data.length ? draft.data : [createEmptySheetData('Sheet1')]
      sheetList.value = sheets
      reloadSpreadsheetWithData(sheets)
      ElMessage.success('草稿已加载')
    } catch (e) {
      if (e === 'cancel' || e === 'close') return
      console.error(e)
      ElMessage.error('加载草稿失败：' + (e?.message || '未知错误'))
    }
  }

  const clearDraft = async () => {
    try {
      await ElMessageBox.confirm('确认清空本地草稿？此操作不可恢复。', '提示', {
        confirmButtonText: '清空',
        cancelButtonText: '取消',
        type: 'warning',
      })
      await draftDel(draftKey)
      ElMessage.success('草稿已清空')
    } catch (e) {
      if (e === 'cancel' || e === 'close') return
      console.error(e)
      ElMessage.error('清空草稿失败：' + (e?.message || '未知错误'))
    }
  }

  return {
    saveDraft,
    loadDraft,
    clearDraft,
  }
}
