import { ElLoading, ElMessage, ElMessageBox } from 'element-plus'
import request from '@/api/request'

// 0-based column index
const COL_G_TEST_ITEM_NAME = 6
const COL_I_CASE_NAME = 8
const COL_L_TEST_DESC = 11
const COL_P_INPUT_CONDITION = 15
const COL_Q_EXPECTED_RESULT = 16

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

export const useCaseDesignInit = (spreadsheetRef, currentTaskIdRef) => {
  const caseDesignInit = async () => {
    const s = spreadsheetRef?.value
    if (!s) {
      ElMessage.error('表格未初始化')
      return
    }

    const taskId = currentTaskIdRef?.value
    if (!taskId) {
      ElMessage.warning('请先导入Excel并创建任务，再执行用例设计-初始化')
      return
    }

    const sheetIndex = getActiveSheetIndex(s)
    const range = getSelectedRange(s)
    if (!range) {
      ElMessage.warning('请先选择要处理的行')
      return
    }

    const { sri, eri } = range
    if (!Number.isFinite(sri) || !Number.isFinite(eri) || eri < sri) {
      ElMessage.warning('当前选区无效')
      return
    }

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
      const { value } = await ElMessageBox.prompt('请粘贴入口函数中所有初始化相关的代码片段（用于定位文件/行号）', '用例设计-初始化', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        customClass: 'case-design-init-prompt',
        inputType: 'textarea',
        inputPlaceholder: '粘贴代码片段，例如 main.c 中 main 函数的初始化部分',
        inputValidator: (v) => {
          if (!String(v || '').trim()) return '代码片段不能为空'
          return true
        },
      })
      codeSnippet = String(value || '').trim()
    } catch (e) {
      if (e === 'cancel' || e === 'close') return
      console.error(e)
      ElMessage.error('弹窗异常：' + (e?.message || '未知错误'))
      return
    }
    finally {
      if (typeof cleanupInterceptors === 'function') cleanupInterceptors()
      if (s?.sheet) s.sheet.focusing = prevFocusing
    }

    const rows = []
    for (let ri = sri; ri <= eri; ri += 1) {
      const testItemName = getCellText(s, ri, COL_G_TEST_ITEM_NAME, sheetIndex)
      const templateCaseName = getCellText(s, ri, COL_I_CASE_NAME, sheetIndex)
      const templateTestDesc = getCellText(s, ri, COL_L_TEST_DESC, sheetIndex)
      const templateInputCondition = getCellText(s, ri, COL_P_INPUT_CONDITION, sheetIndex)
      const templateExpectedResult = getCellText(s, ri, COL_Q_EXPECTED_RESULT, sheetIndex)

      if (!String(testItemName).trim()) continue

      rows.push({
        row_index: ri,
        test_item_name: String(testItemName || ''),
        template_case_name: String(templateCaseName || ''),
        template_test_desc: String(templateTestDesc || ''),
        template_input_condition: String(templateInputCondition || ''),
        template_expected_result: String(templateExpectedResult || ''),
      })
    }

    if (!rows.length) {
      ElMessage.warning('选区内没有可处理的数据（测试项名称为空）')
      return
    }

    let loadingInstance = null
    try {
      loadingInstance = ElLoading.service({
        lock: true,
        text: `用例设计-初始化：处理中（0/${rows.length}）`,
        background: 'rgba(0, 0, 0, 0.2)',
      })

      const resp = await request.post('/test-tools/test-case-assistant/case-design/init', {
        task_id: taskId,
        entry_code_snippet: codeSnippet,
        rows,
      })

      const results = Array.isArray(resp?.results) ? resp.results : []
      const errors = Array.isArray(resp?.errors) ? resp.errors : []

      results.forEach((it, idx) => {
        if (loadingInstance) loadingInstance.setText(`用例设计-初始化：回填中（${idx + 1}/${results.length}）`)
        const ri = Number(it.row_index)
        if (!Number.isFinite(ri)) return
        s.cellText(ri, COL_I_CASE_NAME, it.case_name ?? '', sheetIndex)
        s.cellText(ri, COL_L_TEST_DESC, it.test_desc ?? '', sheetIndex)
        s.cellText(ri, COL_P_INPUT_CONDITION, it.input_condition ?? '', sheetIndex)
        s.cellText(ri, COL_Q_EXPECTED_RESULT, it.expected_result ?? '', sheetIndex)
      })

      s.reRender()

      if (errors.length) {
        ElMessage.warning(`用例设计-初始化完成：成功 ${results.length} 条，失败 ${errors.length} 条（可查看后端日志）`)
      } else {
        ElMessage.success(`用例设计-初始化完成：成功 ${results.length} 条`)
      }
    } catch (e) {
      console.error(e)
      ElMessage.error('用例设计-初始化失败：' + (e?.message || '未知错误'))
    } finally {
      if (loadingInstance) loadingInstance.close()
    }
  }

  return {
    caseDesignInit,
  }
}
