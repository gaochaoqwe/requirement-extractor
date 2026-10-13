import { ElMessage, ElMessageBox } from 'element-plus'

export const useSpreadsheetFormat = ({ spreadsheet, reloadSpreadsheetWithData }) => {
  const getActiveSheetIndex = () => {
    const bb = spreadsheet.value?.bottombar
    if (!bb || !Array.isArray(bb.items) || !bb.activeEl) return 0
    const idx = bb.items.findIndex((it) => it === bb.activeEl)
    return idx >= 0 ? idx : 0
  }

  const getSheetsAndActiveIndex = () => {
    if (!spreadsheet.value) return { sheets: [], activeIndex: 0 }
    const raw = spreadsheet.value.getData()
    const sheets = Array.isArray(raw) ? raw : [raw]
    return {
      sheets,
      activeIndex: getActiveSheetIndex(),
    }
  }

  const normalizeRowsAllHeight = (rows, height) => {
    const r = rows && typeof rows === 'object' ? rows : {}
    const len = Number.isFinite(Number(r.len)) ? Number(r.len) : 0
    const out = { ...r, len: len || r.len || 0 }

    const nlen = Number(out.len) > 0 ? Number(out.len) : 0
    for (let i = 0; i < nlen; i++) {
      const key = String(i)
      const row = out[key]
      if (row && typeof row === 'object') {
        out[key] = { ...row, height }
      } else {
        out[key] = { cells: {}, height }
      }
    }
    return out
  }

  const normalizeColsAllWidth = (cols, width) => {
    const c = cols && typeof cols === 'object' ? cols : {}
    const len = Number.isFinite(Number(c.len)) ? Number(c.len) : 0
    const out = { ...c, len: len || c.len || 0 }

    const nlen = Number(out.len) > 0 ? Number(out.len) : 0
    for (let i = 0; i < nlen; i++) {
      const key = String(i)
      const col = out[key]
      if (col && typeof col === 'object') {
        out[key] = { ...col, width }
      } else {
        out[key] = { width }
      }
    }
    return out
  }

  const applyRowHeightToCurrentSheet = (height) => {
    if (!spreadsheet.value) return
    const h = Number(height)
    if (!Number.isFinite(h) || h <= 0) {
      ElMessage.error('请输入有效的行高')
      return
    }

    const { sheets, activeIndex } = getSheetsAndActiveIndex()
    if (!sheets.length) return

    const next = sheets.map((s, idx) => {
      if (idx !== activeIndex) return s
      const rows = normalizeRowsAllHeight(s?.rows, h)
      return { ...s, rows }
    })

    reloadSpreadsheetWithData(next, activeIndex)
  }

  const applyColWidthToCurrentSheet = (width) => {
    if (!spreadsheet.value) return
    const w = Number(width)
    if (!Number.isFinite(w) || w <= 0) {
      ElMessage.error('请输入有效的列宽')
      return
    }

    const { sheets, activeIndex } = getSheetsAndActiveIndex()
    if (!sheets.length) return

    const next = sheets.map((s, idx) => {
      if (idx !== activeIndex) return s
      const cols = normalizeColsAllWidth(s?.cols, w)
      return { ...s, cols }
    })

    reloadSpreadsheetWithData(next, activeIndex)
  }

  const promptSetRowHeight = async () => {
    try {
      const res = await ElMessageBox.prompt('请输入行高（像素）', '设置行高', {
        confirmButtonText: '应用',
        cancelButtonText: '取消',
        inputPattern: /^[1-9]\d*$/,
        inputErrorMessage: '请输入正整数',
      })
      applyRowHeightToCurrentSheet(res.value)
    } catch (e) {
      if (e === 'cancel' || e === 'close') return
    }
  }

  const promptSetColWidth = async () => {
    try {
      const res = await ElMessageBox.prompt('请输入列宽（像素）', '设置列宽', {
        confirmButtonText: '应用',
        cancelButtonText: '取消',
        inputPattern: /^[1-9]\d*$/,
        inputErrorMessage: '请输入正整数',
      })
      applyColWidthToCurrentSheet(res.value)
    } catch (e) {
      if (e === 'cancel' || e === 'close') return
    }
  }

  return {
    promptSetRowHeight,
    promptSetColWidth,
  }
}
