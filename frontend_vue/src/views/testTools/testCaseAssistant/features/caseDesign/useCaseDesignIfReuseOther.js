import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'

// A~Q => 0~16
const COL_P_INPUT_CONDITION = 15
const COL_Q_EXPECTED_RESULT = 16

const getActiveSheetIndex = (s) => {
  const bb = s?.bottombar
  if (!bb || !Array.isArray(bb.items) || !bb.activeEl) return 0
  const idx = bb.items.findIndex((it) => it === bb.activeEl)
  return idx >= 0 ? idx : 0
}

const getSelectedRange = (s) => {
  const range = s?.sheet?.data?.selector?.range
  if (!range) return null
  return { sri: range.sri, sci: range.sci, eri: range.eri, eci: range.eci }
}

const getCellText = (s, ri, ci, sheetIndex) => {
  const cell = s?.cell(ri, ci, sheetIndex)
  return cell?.text ?? ''
}

const setCellText = (s, ri, ci, text, sheetIndex) => {
  s?.cellText(ri, ci, text ?? '', sheetIndex)
}

const insertRowAt = (s, insertIndex, sheetIndex) => {
  const data = s?.sheet?.data
  if (!data || !data.rows || typeof data.changeData !== 'function') return false

  data.changeData(() => {
    data.rows.insert(insertIndex, 1)
  })

  return true
}

const getMaxColIndex = (s) => {
  const len = s?.sheet?.data?.cols?.len
  if (Number.isFinite(len) && len > 0) return len - 1
  return 30
}

const snapshotRowTexts = (s, ri, sheetIndex) => {
  const maxCi = getMaxColIndex(s)
  const out = []
  for (let ci = 0; ci <= maxCi; ci += 1) {
    out.push(getCellText(s, ri, ci, sheetIndex))
  }
  return out
}

const restoreRowTexts = (s, ri, sheetIndex, rowTexts) => {
  if (!Array.isArray(rowTexts)) return
  for (let ci = 0; ci < rowTexts.length; ci += 1) {
    setCellText(s, ri, ci, rowTexts[ci], sheetIndex)
  }
}

const setRowBgColor = (s, ri, sheetIndex, prevStyleMapRef, color) => {
  const data = s?.sheet?.data
  if (!data || !data.rows || typeof data.addStyle !== 'function') return

  const maxCi = getMaxColIndex(s)
  data.changeData(() => {
    const styleIdx = data.addStyle({ bgcolor: color })
    for (let ci = 0; ci <= maxCi; ci += 1) {
      const cell = data.rows.getCellOrNew(ri, ci)
      const k = `${ri}:${ci}`
      if (!prevStyleMapRef.value.has(k)) {
        prevStyleMapRef.value.set(k, cell?.style)
      }
      cell.style = styleIdx
    }
  })
}

const restoreRowStyle = (s, ri, prevStyleMapRef) => {
  const data = s?.sheet?.data
  if (!data || !data.rows) return

  const maxCi = getMaxColIndex(s)
  data.changeData(() => {
    for (let ci = 0; ci <= maxCi; ci += 1) {
      const k = `${ri}:${ci}`
      if (!prevStyleMapRef.value.has(k)) continue
      const prev = prevStyleMapRef.value.get(k)
      const cell = data.rows.getCellOrNew(ri, ci)
      if (prev === undefined) {
        delete cell.style
      } else {
        cell.style = prev
      }
      prevStyleMapRef.value.delete(k)
    }
  })
}

const clearHighlights = (s, prevStyleMapRef) => {
  const ris = new Set()
  for (const k of prevStyleMapRef.value.keys()) {
    const ri = Number(String(k).split(':')[0])
    if (Number.isFinite(ri)) ris.add(ri)
  }
  for (const ri of ris) {
    restoreRowStyle(s, ri, prevStyleMapRef)
  }
  prevStyleMapRef.value.clear()
}

const removeRowTracking = (prevStyleMapRef, ri) => {
  const keys = [...prevStyleMapRef.value.keys()]
  for (const k of keys) {
    if (String(k).startsWith(`${ri}:`)) {
      prevStyleMapRef.value.delete(k)
    }
  }
}

export const useCaseDesignIfReuseOther = (spreadsheetRef) => {
  const mode = ref(false)
  const targetRow = ref(null)
  const selectedRows = ref([])
  const prevStyleMap = ref(new Map())
  const altPressed = ref(false)

  const tipTitle = computed(() => {
    const cnt = selectedRows.value.length
    const rows = selectedRows.value
      .map((ri) => (Number.isFinite(ri) ? ri + 1 : ri))
      .filter((x) => x !== null && x !== undefined)
      .join(',')

    const base = '选择模式：按住 Alt + 鼠标左键 点击要复用的用例行（绿色高亮），完成后点“选择完毕”'
    if (!cnt) return base
    return `${base}｜已选择 ${cnt} 条：${rows}`
  })

  const cancel = () => {
    const s = spreadsheetRef?.value
    if (s) {
      clearHighlights(s, prevStyleMap)
      s.reRender()
    }
    mode.value = false
    targetRow.value = null
    selectedRows.value = []
  }

  const toggleSourceRow = (ri) => {
    const s = spreadsheetRef?.value
    if (!s) return
    const sheetIndex = getActiveSheetIndex(s)

    const targetRi = targetRow.value
    if (!Number.isFinite(ri) || ri < 0) return
    if (Number.isFinite(targetRi) && ri === targetRi) return

    const cur = [...selectedRows.value]
    const idx = cur.indexOf(ri)
    if (idx >= 0) {
      cur.splice(idx, 1)
      restoreRowStyle(s, ri, prevStyleMap)
      removeRowTracking(prevStyleMap, ri)
    } else {
      cur.push(ri)
      setRowBgColor(s, ri, sheetIndex, prevStyleMap, '#86efac')
    }

    selectedRows.value = cur
    s.reRender()
  }

  const finish = () => {
    const s = spreadsheetRef?.value
    if (!s) {
      ElMessage.error('表格未初始化')
      return
    }
    const sheetIndex = getActiveSheetIndex(s)
    const t = targetRow.value
    const selected = [...selectedRows.value]

    if (!Number.isFinite(t)) {
      ElMessage.warning('未找到目标用例行')
      return
    }
    if (!selected.length) {
      ElMessage.warning('请先按住Ctrl+Shift点击选择要复用的用例行')
      return
    }

    const rowSnapshot = snapshotRowTexts(s, t, sheetIndex)
    for (let i = 0; i < selected.length; i += 1) {
      const srcRi = selected[i]
      const p = getCellText(s, srcRi, COL_P_INPUT_CONDITION, sheetIndex)
      const q = getCellText(s, srcRi, COL_Q_EXPECTED_RESULT, sheetIndex)

      if (i === 0) {
        setCellText(s, t, COL_P_INPUT_CONDITION, p ?? '', sheetIndex)
        setCellText(s, t, COL_Q_EXPECTED_RESULT, q ?? '', sheetIndex)
        continue
      }

      const insertIndex = t + i
      const ok = insertRowAt(s, insertIndex, sheetIndex)
      if (!ok) continue
      restoreRowTexts(s, insertIndex, sheetIndex, rowSnapshot)
      setCellText(s, insertIndex, COL_P_INPUT_CONDITION, p ?? '', sheetIndex)
      setCellText(s, insertIndex, COL_Q_EXPECTED_RESULT, q ?? '', sheetIndex)
    }

    clearHighlights(s, prevStyleMap)
    s.reRender()
    mode.value = false
    targetRow.value = null
    selectedRows.value = []
    ElMessage.success(`已复用 ${selected.length} 条用例的P/Q，并插入 ${Math.max(selected.length - 1, 0)} 行`)
  }

  const enterFromCtx = () => {
    const s = spreadsheetRef?.value
    if (!s) {
      ElMessage.error('表格未初始化')
      return
    }
    const sheetIndex = getActiveSheetIndex(s)
    const range = getSelectedRange(s)
    if (!range || !Number.isFinite(range.sri)) {
      ElMessage.warning('请先选中要作为“接口测试用例”的目标行')
      return
    }

    cancel()
    mode.value = true
    targetRow.value = range.sri
    selectedRows.value = []

    setRowBgColor(s, range.sri, sheetIndex, prevStyleMap, '#fff7cc')
    s.reRender()
    ElMessage.info('已进入选择模式：按住Alt点击要复用的用例行（绿色高亮），完成后点“选择完毕”。')
  }

  const onCellSelected = (ri) => {
    if (!mode.value) return
    if (!altPressed.value) return
    toggleSourceRow(ri)
  }

  const onKeyChange = (e) => {
    altPressed.value = !!e?.altKey
  }

  return {
    mode,
    tipTitle,
    selectedRows,
    enterFromCtx,
    finish,
    cancel,
    onCellSelected,
    onKeyChange,
  }
}
