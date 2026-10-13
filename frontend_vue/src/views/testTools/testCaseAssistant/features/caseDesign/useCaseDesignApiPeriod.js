import { ElLoading, ElMessage, ElMessageBox } from 'element-plus'
import request from '@/api/request'

// A~AD => 0~29
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

const insertRowClone = (s, targetRi, sheetIndex) => {
  const rowSnapshot = snapshotRowTexts(s, targetRi, sheetIndex)
  const insertIndex = targetRi + 1
  const ok = insertRowAt(s, insertIndex, sheetIndex)
  if (!ok) return null
  restoreRowTexts(s, insertIndex, sheetIndex, rowSnapshot)
  return insertIndex
}

const bindMessageBoxInputInterceptors = () => {
  const onPasteCapture = (evt) => {
    evt.stopImmediatePropagation()
  }

  const onKeydownCapture = (evt) => {
    const key = String(evt?.key || '').toLowerCase()
    const isPaste = (evt.ctrlKey || evt.metaKey) && key === 'v'
    if (!isPaste) return
    evt.stopImmediatePropagation()
  }

  const el = document?.querySelector?.('.el-message-box__input textarea, .el-message-box__input input')
  if (!el) return () => {}

  el.addEventListener('paste', onPasteCapture, true)
  el.addEventListener('keydown', onKeydownCapture, true)

  return () => {
    el.removeEventListener('paste', onPasteCapture, true)
    el.removeEventListener('keydown', onKeydownCapture, true)
  }
}

export const useCaseDesignApiPeriod = (spreadsheetRef, currentTaskIdRef) => {
  const caseDesignApiPeriod = async () => {
    const s = spreadsheetRef?.value
    if (!s) {
      ElMessage.error('表格未初始化')
      return
    }

    const taskId = currentTaskIdRef?.value
    if (!taskId) {
      ElMessage.warning('请先导入Excel并创建任务，再执行接口周期')
      return
    }

    const range = getSelectedRange(s)
    if (!range || !Number.isFinite(range.sri)) {
      ElMessage.warning('请先选中要生成周期用例的目标行')
      return
    }

    const sheetIndex = getActiveSheetIndex(s)
    const targetRi = range.sri

    // 先插入一行并复制所有列
    const insertedRi = insertRowClone(s, targetRi, sheetIndex)
    if (!Number.isFinite(insertedRi)) {
      ElMessage.error('插入新行失败')
      return
    }

    // 弹窗输入代码片段
    let codeSnippet = ''
    const prevFocusing = s?.sheet?.focusing
    if (s?.sheet) s.sheet.focusing = false
    let cleanupInterceptors = null
    try {
      setTimeout(() => {
        const el = document?.querySelector?.('.el-message-box__input textarea, .el-message-box__input input')
        if (el && typeof el.focus === 'function') el.focus()
        cleanupInterceptors = bindMessageBoxInputInterceptors()
      }, 0)
      const { value } = await ElMessageBox.prompt(
        '请粘贴与该接口相关的代码片段（用于定位文件/函数/行号并生成插桩代码）',
        '接口周期',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          customClass: 'case-design-if-period-prompt',
          inputType: 'textarea',
          inputPlaceholder: '粘贴代码片段（建议包含接收/发送处理与打点位置）',
          inputValidator: (v) => {
            if (!String(v || '').trim()) return '代码片段不能为空'
            return true
          },
        }
      )
      codeSnippet = String(value || '').trim()
    } catch (e) {
      if (e === 'cancel' || e === 'close') {
        if (s?.sheet) s.sheet.focusing = prevFocusing
        s.reRender()
        return
      }
      console.error(e)
      ElMessage.error('弹窗异常：' + (e?.message || '未知错误'))
      return
    } finally {
      if (typeof cleanupInterceptors === 'function') cleanupInterceptors()
      if (s?.sheet) s.sheet.focusing = prevFocusing
    }

    const testItemName = String(getCellText(s, targetRi, COL_G_CASE_TEST_ITEM_NAME, sheetIndex) || '').trim()
    const templateCaseName = String(getCellText(s, targetRi, COL_I_CASE_NAME, sheetIndex) || '')
    const templateTestDesc = String(getCellText(s, targetRi, COL_L_TEST_DESC, sheetIndex) || '')
    const templateInputCondition = String(getCellText(s, targetRi, COL_P_INPUT_CONDITION, sheetIndex) || '')
    const templateExpectedResult = String(getCellText(s, targetRi, COL_Q_EXPECTED_RESULT, sheetIndex) || '')

    let loadingInstance = null
    try {
      loadingInstance = ElLoading.service({
        lock: true,
        text: '接口周期：AI生成中... ',
        background: 'rgba(0, 0, 0, 0.2)',
      })

      const resp = await request.post('/test-tools/test-case-assistant/case-design/api-period', {
        task_id: taskId,
        test_item_name: testItemName,
        template_case_name: templateCaseName,
        template_test_desc: templateTestDesc,
        template_input_condition: templateInputCondition,
        template_expected_result: templateExpectedResult,
        user_code_snippet: codeSnippet,
      })

      const cases = Array.isArray(resp?.cases) ? resp.cases : []
      if (cases.length < 2) {
        ElMessage.error('AI返回用例数量不足(需要2条)')
        return
      }

      const c0 = cases[0] || {}
      const c1 = cases[1] || {}
      setCellText(s, targetRi, COL_I_CASE_NAME, c0.case_name ?? '', sheetIndex)
      setCellText(s, targetRi, COL_L_TEST_DESC, c0.test_desc ?? '', sheetIndex)
      setCellText(s, targetRi, COL_P_INPUT_CONDITION, c0.input_condition ?? '', sheetIndex)
      setCellText(s, targetRi, COL_Q_EXPECTED_RESULT, c0.expected_result ?? '', sheetIndex)

      setCellText(s, insertedRi, COL_I_CASE_NAME, c1.case_name ?? '', sheetIndex)
      setCellText(s, insertedRi, COL_L_TEST_DESC, c1.test_desc ?? '', sheetIndex)
      setCellText(s, insertedRi, COL_P_INPUT_CONDITION, c1.input_condition ?? '', sheetIndex)
      setCellText(s, insertedRi, COL_Q_EXPECTED_RESULT, c1.expected_result ?? '', sheetIndex)

      s.reRender()
      ElMessage.success('接口周期生成完成（2条用例已回填）')
    } catch (e) {
      console.error(e)
      ElMessage.error('接口周期失败：' + (e?.message || '未知错误'))
    } finally {
      if (loadingInstance) loadingInstance.close()
    }
  }

  return {
    caseDesignApiPeriod,
  }
}
