import { ElMessage } from 'element-plus'

// A~AD => 0~29
const COL_G_TEST_ITEM_NAME = 6
const COL_H_TEST_ITEM_ID = 7
const COL_J_CASE_ID = 9
const COL_K_TEST_TYPE = 10
const COL_MAX = 29

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

const insertRowAt = (spreadsheet, insertIndex) => {
  const data = spreadsheet?.sheet?.data
  if (!data || !data.rows || typeof data.changeData !== 'function') return false

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

const getTestTypeText = (mode) => {
  if (mode === 'perf') return '性能测试'
  if (mode === 'boundary') return '边界测试'
  return ''
}

const pad2 = (n) => String(n).padStart(2, '0')

const extractCaseSeq = (caseId, baseTestItemId) => {
  const s = String(caseId || '').trim()
  const base = String(baseTestItemId || '').trim()
  if (!s || !base) return null
  const re = new RegExp(`^${base.replace(/[.*+?^${}()|[\\]\\]/g, '\\$&')}-?(\\d{2})$`)
  const m = s.match(re)
  if (!m) return null
  const num = parseInt(m[1], 10)
  return Number.isFinite(num) ? num : null
}

const buildNextCaseId = (spreadsheet, sheetIndex, baseTestItemId) => {
  const base = String(baseTestItemId || '').trim()
  if (!base) return ''

  const data = spreadsheet?.datas?.[sheetIndex]
  const rows = data?.rows
  const len = rows?.len
  const maxRows = Number.isFinite(len) ? len : 2000

  let maxSeq = 0
  for (let ri = 0; ri < maxRows; ri += 1) {
    const v = getCellText(spreadsheet, ri, COL_J_CASE_ID, sheetIndex)
    const seq = extractCaseSeq(v, base)
    if (seq && seq > maxSeq) maxSeq = seq
  }

  return `${base}-${pad2(maxSeq + 1)}`
}

export const useTestCaseExtend = (spreadsheetRef) => {
  const extendTestCase = async (mode) => {
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

    const oldName = getCellText(s, insertIndex, COL_G_TEST_ITEM_NAME, sheetIndex)
    const oldId = getCellText(s, insertIndex, COL_H_TEST_ITEM_ID, sheetIndex)

    const newName = transformTestItemName(oldName, mode)
    const newId = transformTestItemId(oldId, mode)
    const newTestType = getTestTypeText(mode)
    const newCaseId = buildNextCaseId(s, sheetIndex, newId)

    setCellText(s, insertIndex, COL_G_TEST_ITEM_NAME, newName, sheetIndex)
    setCellText(s, insertIndex, COL_H_TEST_ITEM_ID, newId, sheetIndex)
    if (newCaseId) setCellText(s, insertIndex, COL_J_CASE_ID, newCaseId, sheetIndex)
    if (newTestType) setCellText(s, insertIndex, COL_K_TEST_TYPE, newTestType, sheetIndex)

    s.reRender()
    ElMessage.success('测试用例扩展完成')
  }

  const extendPerfTestCase = async () => extendTestCase('perf')
  const extendBoundaryTestCase = async () => extendTestCase('boundary')

  return {
    extendPerfTestCase,
    extendBoundaryTestCase,
  }
}
