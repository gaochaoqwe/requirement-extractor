import { ElLoading, ElMessage, ElMessageBox } from 'element-plus'
import request from '@/api/request'

// A~W => 0~22
const COL_N_TEST_TYPE = 13
const COL_O_TEST_ITEM_NAME = 14
const COL_S_REQUIREMENT_SUB_ITEM_DESC = 18
const COL_T_TEST_ITEM_DESC = 19
const COL_U_TEST_METHOD = 20

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

const extractVariablesFromText = (text) => {
  const s = String(text || '')
  if (!s) return []

  // 匹配英文双引号中的内容，内容必须包含 xx/yy/zz/mm/nn/kk 之一
  const re = /"([^"\n\r]*?(?:xx|yy|zz|mm|nn|kk)[^"\n\r]*?)"/gi
  const found = []
  let m
  while ((m = re.exec(s)) !== null) {
    const v = String(m[1] || '').trim()
    if (!v) continue
    found.push(v)
  }

  // 去重，保持顺序
  const seen = new Set()
  const uniq = []
  for (const v of found) {
    if (seen.has(v)) continue
    seen.add(v)
    uniq.push(v)
  }
  return uniq
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

const askUserForVariableValue = async (idx, varKey) => {
  const title = `变量${idx + 1}：${varKey}`
  const message = `请为每个变量输入替换内容（多个值用"/"隔开）。右侧"裂变变量"会进行排列组合生成多条例。\n\n`

  // 从 varKey 中提取括号内的内容作为示例
  // 例如：xx（随动/自动扫描） => 随动/自动扫描
  let placeholder = '例如：随动/自动扫描/手动'
  const match = varKey.match(/[（(]([^）)]+)[）)]/)
  if (match && match[1]) {
    const exampleContent = match[1].trim()
    if (exampleContent) {
      placeholder = `例如：${exampleContent}`
    }
  }

  let cleanupInterceptors = null

  try {
    setTimeout(() => {
      const el = document?.querySelector?.('.el-message-box__input textarea, .el-message-box__input input')
      if (el && typeof el.focus === 'function') el.focus()
      cleanupInterceptors = bindMessageBoxInputInterceptors()
    }, 0)

    const { value } = await ElMessageBox.prompt(message, title, {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPlaceholder: placeholder,
      inputValue: '',
      inputValidator: (v) => {
        if (!String(v || '').trim()) return '请输入变量替换内容'
        return true
      },
      customClass: 'req-design-common-prompt',
    })

    return String(value || '').trim()
  } finally {
    if (typeof cleanupInterceptors === 'function') cleanupInterceptors()
  }
}

const callReqDesignCommon = async ({ test_item_name, requirement_sub_item_desc, test_item_desc, test_method, variables }) => {
  const resp = await request.post('/test-tools/test-case-assistant/req-design/common', {
    test_item_name,
    requirement_sub_item_desc,
    test_item_desc,
    test_method,
    variables,
  })

  return {
    test_item_desc: String(resp?.test_item_desc ?? ''),
    test_method: String(resp?.test_method ?? ''),
  }
}

export const useReqDesignCommon = (spreadsheetRef) => {
  const reqDesignCommon = async () => {
    const s = spreadsheetRef?.value
    if (!s) {
      ElMessage.error('表格未初始化')
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

    if (sri !== eri) {
      ElMessage.warning('通用功能暂仅支持单行处理，请只选择一行')
      return
    }

    const ri = sri
    const testItemName = getCellText(s, ri, COL_O_TEST_ITEM_NAME, sheetIndex)
    const requirementSubItemDesc = getCellText(s, ri, COL_S_REQUIREMENT_SUB_ITEM_DESC, sheetIndex)
    const tDesc = getCellText(s, ri, COL_T_TEST_ITEM_DESC, sheetIndex)
    const uMethod = getCellText(s, ri, COL_U_TEST_METHOD, sheetIndex)

    if (!String(tDesc || '').trim() && !String(uMethod || '').trim()) {
      ElMessage.warning('T/U 列为空，无法提取变量')
      return
    }

    const vars = [...extractVariablesFromText(tDesc), ...extractVariablesFromText(uMethod)]
    const uniqVars = Array.from(new Set(vars))

    if (!uniqVars.length) {
      ElMessage.warning('未在 T/U 列中识别到变量占位符（"xx/yy/zz/mm/nn/kk..."）')
      return
    }

    const variables = {}
    try {
      for (let i = 0; i < uniqVars.length; i += 1) {
        const key = uniqVars[i]
        const val = await askUserForVariableValue(i, key)
        variables[key] = val
      }
    } catch (e) {
      // 用户取消
      return
    }

    let loadingInstance = null
    try {
      loadingInstance = ElLoading.service({
        lock: true,
        text: '需求设计-通用功能：AI处理中...',
        background: 'rgba(0, 0, 0, 0.2)',
      })

      const res = await callReqDesignCommon({
        test_item_name: String(testItemName || ''),
        requirement_sub_item_desc: String(requirementSubItemDesc || ''),
        test_item_desc: String(tDesc || ''),
        test_method: String(uMethod || ''),
        variables,
      })

      s.cellText(ri, COL_T_TEST_ITEM_DESC, res.test_item_desc, sheetIndex)
      s.cellText(ri, COL_U_TEST_METHOD, res.test_method, sheetIndex)
      s.reRender()
      ElMessage.success('需求设计-通用功能完成')
    } catch (e) {
      console.error(e)
      ElMessage.error('需求设计-通用功能失败：' + (e?.message || '未知错误'))
    } finally {
      if (loadingInstance) loadingInstance.close()
    }
  }

  return {
    reqDesignCommon,
  }
}
