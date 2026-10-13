import { ElLoading, ElMessage } from 'element-plus'
import request from '@/api/request'

// A~W => 0~22
const COL_N_TEST_TYPE = 13
const COL_O_TEST_ITEM_NAME = 14
const COL_P_TEST_ITEM_ID = 15
const COL_S_SUB_REQUIREMENT_DESC = 18
const COL_MAX = 22

const getActiveSheetIndex = (spreadsheet) => {
  const bb = spreadsheet?.bottombar
  if (!bb || !Array.isArray(bb.items) || !bb.activeEl) return 0
  const idx = bb.items.findIndex((it) => it === bb.activeEl)
  return idx >= 0 ? idx : 0
}

const getSelectedRange = (spreadsheet) => {
  const range = spreadsheet?.sheet?.data?.selector?.range
  if (!range) return null
  return { sri: range.sri, sci: range.sci, eri: range.eri, eci: range.eci }
}

const getCellText = (spreadsheet, ri, ci, sheetIndex) => {
  const cell = spreadsheet?.cell(ri, ci, sheetIndex)
  return cell?.text ?? ''
}

const setCellText = (spreadsheet, ri, ci, text, sheetIndex) => {
  spreadsheet?.cellText(ri, ci, text ?? '', sheetIndex)
}

const transformTestItemId = (oldVal, mode) => {
  const s = String(oldVal || '').trim()
  if (!s) return s
  if (mode === 'perf') {
    if (/-FN\d+$/i.test(s)) return s.replace(/-FN(\d+)$/i, '-PF$1')
    if (/-PF\d+$/i.test(s)) return s
    return s.replace(/(\d+)$/g, 'PF$1')
  }
  if (mode === 'boundary') {
    if (/-FN\d+$/i.test(s)) return s.replace(/-FN(\d+)$/i, '-BF$1')
    if (/-BF\d+$/i.test(s)) return s
    return s.replace(/(\d+)$/g, 'BF$1')
  }
  return s
}

const getTestTypeText = (mode) => {
  if (mode === 'perf') return '性能测试'
  if (mode === 'boundary') return '边界测试'
  return ''
}

const transformTestItemName = (oldVal, mode) => {
  const s = String(oldVal || '').trim()
  if (!s) return s
  if (mode === 'perf') {
    if (s.includes('（性能测试）')) return s
    return `${s}（性能测试）`
  }
  if (mode === 'boundary') {
    if (s.includes('（边界测试）')) return s
    return `${s}（边界测试）`
  }
  return s
}

const insertRowAt = (spreadsheet, insertIndex) => {
  const data = spreadsheet?.sheet?.data
  if (!data || !data.rows || typeof data.changeData !== 'function') return false

  // 直接调用 rows.insert，并通过 changeData 包裹以触发渲染
  data.changeData(() => {
    data.rows.insert(insertIndex, 1)
  })
  return true
}

const copyRowText = (spreadsheet, srcRow, dstRow, sheetIndex) => {
  for (let ci = 0; ci <= COL_MAX; ci += 1) {
    const v = getCellText(spreadsheet, srcRow, ci, sheetIndex)
    setCellText(spreadsheet, dstRow, ci, v, sheetIndex)
  }
}

const generateSubRequirementDesc = async ({ mode, original_text, row_snapshot }) => {
  const resp = await request.post('/test-tools/test-case-assistant/test-item/extend', {
    extend_type: mode,
    original_sub_requirement_desc: original_text,
    row_snapshot,
  })
  return String(resp?.new_sub_requirement_desc ?? '')
}

export const useTestItemExtend = (spreadsheetRef) => {
  const extendTestItem = async (mode) => {
    const s = spreadsheetRef?.value
    if (!s) {
      ElMessage.error('表格未初始化')
      return
    }

    const range = getSelectedRange(s)
    if (!range) {
      ElMessage.warning('请先选择要扩展的行')
      return
    }

    const { sri, eri } = range
    if (!Number.isFinite(sri) || !Number.isFinite(eri) || eri < sri) {
      ElMessage.warning('当前选区无效')
      return
    }

    const sheetIndex = getActiveSheetIndex(s)

    const srcRow = sri
    const insertIndex = eri + 1

    const ok = insertRowAt(s, insertIndex)
    if (!ok) {
      ElMessage.error('插入行失败')
      return
    }

    copyRowText(s, srcRow, insertIndex, sheetIndex)

    const oldName = getCellText(s, insertIndex, COL_O_TEST_ITEM_NAME, sheetIndex)
    const oldId = getCellText(s, insertIndex, COL_P_TEST_ITEM_ID, sheetIndex)
    const oldSub = getCellText(s, insertIndex, COL_S_SUB_REQUIREMENT_DESC, sheetIndex)

    const newName = transformTestItemName(oldName, mode)
    const newId = transformTestItemId(oldId, mode)
    const newTestType = getTestTypeText(mode)

    setCellText(s, insertIndex, COL_O_TEST_ITEM_NAME, newName, sheetIndex)
    setCellText(s, insertIndex, COL_P_TEST_ITEM_ID, newId, sheetIndex)
    if (newTestType) setCellText(s, insertIndex, COL_N_TEST_TYPE, newTestType, sheetIndex)

    let loadingInstance = null
    try {
      loadingInstance = ElLoading.service({
        lock: true,
        text: '测试项扩展：生成需求子项描述中...',
        background: 'rgba(0, 0, 0, 0.2)',
      })

      const rowSnapshot = {}
      for (let ci = 0; ci <= COL_MAX; ci += 1) {
        rowSnapshot[String(ci)] = getCellText(s, insertIndex, ci, sheetIndex)
      }

      const newSub = await generateSubRequirementDesc({
        mode,
        original_text: oldSub,
        row_snapshot: rowSnapshot,
      })

      if (newSub) {
        setCellText(s, insertIndex, COL_S_SUB_REQUIREMENT_DESC, newSub, sheetIndex)
      }

      s.reRender()
      ElMessage.success('测试项扩展完成')
    } catch (e) {
      console.error(e)
      s.reRender()
      ElMessage.warning('测试项扩展完成（S列AI生成失败，可稍后手动补充）：' + (e?.message || '未知错误'))
    } finally {
      if (loadingInstance) loadingInstance.close()
    }
  }

  const extendPerfTestItem = async () => extendTestItem('perf')
  const extendBoundaryTestItem = async () => extendTestItem('boundary')

  return {
    extendPerfTestItem,
    extendBoundaryTestItem,
  }
}
