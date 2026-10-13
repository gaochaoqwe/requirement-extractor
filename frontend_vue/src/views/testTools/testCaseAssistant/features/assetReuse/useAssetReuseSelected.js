import { ElMessage } from 'element-plus'
import request from '@/api/request'

// A~W => 0~22
const COL_O_TEST_ITEM_NAME = 14
const COL_T_TEST_CONTENT = 19
const COL_U_TEST_METHOD = 20

// A~Q => 0~16
const COL_G_CASE_TEST_ITEM_NAME = 6
const COL_I_CASE_NAME = 8
const COL_L_TEST_DESC = 11
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

export const useAssetReuseSelected = (spreadsheetRef, currentTaskIdRef) => {
  const onAssetReuseSelectedConfirm = async ({ selectedType, selectedSoftwareType }) => {
    const s = spreadsheetRef?.value
    if (!s) {
      ElMessage.error('表格未初始化')
      return
    }

    const range = getSelectedRange(s)
    if (!range) {
      ElMessage.warning('请先选择要匹配的行范围')
      return
    }

    const { sri, eri } = range
    if (!Number.isFinite(sri) || !Number.isFinite(eri) || eri < sri) {
      ElMessage.warning('当前选区无效')
      return
    }

    const sheetIndex = getActiveSheetIndex(s)

    const items = []
    for (let ri = sri; ri <= eri; ri += 1) {
      const name = String(getCellText(s, ri, COL_O_TEST_ITEM_NAME, sheetIndex) || '').trim()
      items.push({ row_index: ri, test_item_name: name })
    }

    try {
      const resp = await request.post('/test-tools/test-case-assistant/asset-reuse-selected/match', {
        task_id: currentTaskIdRef?.value || null,
        selected_type: selectedType,
        selected_software_type: selectedSoftwareType,
        items,
      })

      const results = resp?.results || []
      let matchedCount = 0
      let unmatchedCount = 0

      for (const r of results) {
        const rowIndex = r?.row_index
        if (!Number.isFinite(rowIndex)) continue

        if (r?.matched) {
          matchedCount += 1
          if (r?.test_content) setCellText(s, rowIndex, COL_T_TEST_CONTENT, String(r.test_content), sheetIndex)
          if (r?.test_method) setCellText(s, rowIndex, COL_U_TEST_METHOD, String(r.test_method), sheetIndex)
        } else {
          unmatchedCount += 1
        }
      }

      s.reRender()
      if (unmatchedCount > 0) {
        ElMessage.warning(`组织资产复用完成：命中${matchedCount}条，未命中${unmatchedCount}条（未命中行保持不变）`)
      } else {
        ElMessage.success(`组织资产复用完成：命中${matchedCount}条`)
      }
    } catch (e) {
      console.error(e)
      ElMessage.error('组织资产复用失败：' + (e?.message || '未知错误'))
    }
  }

  const onAssetReuseSelectedCaseConfirm = async ({ selectedType, selectedSoftwareType }) => {
    const s = spreadsheetRef?.value
    if (!s) {
      ElMessage.error('表格未初始化')
      return
    }

    const range = getSelectedRange(s)
    if (!range) {
      ElMessage.warning('请先选择要匹配的行范围')
      return
    }

    const { sri, eri } = range
    if (!Number.isFinite(sri) || !Number.isFinite(eri) || eri < sri) {
      ElMessage.warning('当前选区无效')
      return
    }

    const sheetIndex = getActiveSheetIndex(s)

    const items = []
    for (let ri = sri; ri <= eri; ri += 1) {
      const name = String(getCellText(s, ri, COL_G_CASE_TEST_ITEM_NAME, sheetIndex) || '').trim()
      items.push({ row_index: ri, test_item_name: name })
    }

    try {
      const resp = await request.post('/test-tools/test-case-assistant/asset-reuse-selected/case-sheet/match', {
        task_id: currentTaskIdRef?.value || null,
        selected_type: selectedType,
        selected_software_type: selectedSoftwareType,
        items,
      })

      const results = Array.isArray(resp?.results) ? resp.results : []

      // 按行从上到下处理，插入新行时维护偏移
      const sorted = [...results].sort((a, b) => Number(a?.row_index || 0) - Number(b?.row_index || 0))
      let rowOffset = 0
      let matchedRows = 0
      let insertedRows = 0
      let totalMatches = 0

      for (const it of sorted) {
        const originalRi = Number(it?.row_index)
        if (!Number.isFinite(originalRi)) continue
        const ri = originalRi + rowOffset

        const matches = Array.isArray(it?.matches) ? it.matches : []
        if (!it?.matched || !matches.length) continue

        matchedRows += 1
        totalMatches += matches.length

        // 先快照原行，后续插入行用于复制原行其它列
        const rowSnapshot = snapshotRowTexts(s, ri, sheetIndex)

        // 第1条写回原行
        const m0 = matches[0] || {}
        setCellText(s, ri, COL_I_CASE_NAME, m0.case_name ?? '', sheetIndex)
        setCellText(s, ri, COL_L_TEST_DESC, m0.test_desc ?? '', sheetIndex)
        setCellText(s, ri, COL_P_INPUT_CONDITION, m0.input_condition ?? '', sheetIndex)
        setCellText(s, ri, COL_Q_EXPECTED_RESULT, m0.expected_result ?? '', sheetIndex)

        // 第2..N条：在下方插入新行并逐行填充
        for (let j = 1; j < matches.length; j += 1) {
          const insertIndex = ri + j
          const ok = insertRowAt(s, insertIndex, sheetIndex)
          if (!ok) continue

          insertedRows += 1
          rowOffset += 1

          // 先恢复整行（复制原行其它列），再覆盖I/L/P/Q
          restoreRowTexts(s, insertIndex, sheetIndex, rowSnapshot)

          const mj = matches[j] || {}
          setCellText(s, insertIndex, COL_I_CASE_NAME, mj.case_name ?? '', sheetIndex)
          setCellText(s, insertIndex, COL_L_TEST_DESC, mj.test_desc ?? '', sheetIndex)
          setCellText(s, insertIndex, COL_P_INPUT_CONDITION, mj.input_condition ?? '', sheetIndex)
          setCellText(s, insertIndex, COL_Q_EXPECTED_RESULT, mj.expected_result ?? '', sheetIndex)
        }
      }

      s.reRender()

      if (!results.length) {
        ElMessage.warning('未返回任何匹配结果')
      } else if (!matchedRows) {
        ElMessage.warning('组织资产复用完成：全部未命中（未命中行保持不变）')
      } else {
        ElMessage.success(`组织资产复用完成：命中行 ${matchedRows}/${results.length}，生成用例 ${totalMatches} 条，插入行 ${insertedRows} 行`)
      }
    } catch (e) {
      console.error(e)
      ElMessage.error('组织资产复用失败：' + (e?.message || '未知错误'))
    }
  }

  return {
    onAssetReuseSelectedConfirm,
    onAssetReuseSelectedCaseConfirm,
  }
}
