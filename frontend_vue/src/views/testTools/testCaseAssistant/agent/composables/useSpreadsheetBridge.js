/**
 * 将 EditPlan 的 operations 应用到 x-data-spreadsheet 实例
 * 支持的 op：set_cell | insert_row | delete_row | switch_sheet | add_sheet | rename_sheet | delete_sheet
 */
export function useSpreadsheetBridge(spreadsheet, sheetList) {
  const getSheetIndex = (sheetName) => {
    const list = sheetList.value || []
    const idx = list.findIndex(s => s.name === sheetName)
    return idx >= 0 ? idx : 0
  }

  const applyOp = (op) => {
    const s = spreadsheet.value
    if (!s) return false

    // ── sheet 管理类操作 ──────────────────────────────────────────
    if (op.op === 'switch_sheet') {
      const idx = getSheetIndex(op.sheet)
      const item = s.bottombar?.items?.[idx]
      if (item) {
        s.bottombar.clickSwap2(item)
      }
      return true
    }

    if (op.op === 'add_sheet') {
      const name = op.name || `sheet${(s.datas?.length || 0) + 1}`
      const d = s.addSheet(name, true)
      s.sheet.resetData(d)
      return true
    }

    if (op.op === 'rename_sheet') {
      const idx = getSheetIndex(op.sheet)
      if (s.bottombar) {
        s.bottombar.renameItem(idx, op.name)
      }
      if (s.datas?.[idx]) {
        s.datas[idx].name = op.name
      }
      s.sheet.trigger('change')
      return true
    }

    if (op.op === 'delete_sheet') {
      const idx = getSheetIndex(op.sheet)
      const item = s.bottombar?.items?.[idx]
      if (item) {
        s.bottombar.deleteEl = item
        s.deleteSheet()
      }
      return true
    }

    // ── 单元格 / 行操作 ──────────────────────────────────────────
    const si = getSheetIndex(op.sheet)

    if (op.op === 'set_cell') {
      s.cellText(op.row, op.col, op.value ?? '', si)
      if (typeof s.reRender === 'function') s.reRender()
      return true
    }

    if (op.op === 'insert_row') {
      const data = s.datas?.[si]
      if (!data) return false
      data.rows.insert(op.after_row + 1, 1)
      if (op.values) {
        Object.entries(op.values).forEach(([colStr, val]) => {
          s.cellText(op.after_row + 1, parseInt(colStr), val ?? '', si)
        })
      }
      if (typeof s.reRender === 'function') s.reRender()
      return true
    }

    if (op.op === 'delete_row') {
      const data = s.datas?.[si]
      if (!data) return false
      data.rows.delete(op.row, 1)
      if (typeof s.reRender === 'function') s.reRender()
      return true
    }

    return false
  }

  const applyOps = (ops) => {
    if (!Array.isArray(ops)) return
    ops.forEach(applyOp)
  }

  /** 从 spreadsheet 当前数据生成快照，传给后端 AI */
  const getSnapshot = () => {
    const s = spreadsheet.value
    if (!s) return []
    const raw = s.getData?.()
    return Array.isArray(raw) ? raw : [raw]
  }

  return { applyOp, applyOps, getSnapshot }
}
