import { h, ref } from 'vue'
import { ElButton, ElInput, ElLoading, ElMessage, ElMessageBox } from 'element-plus'
import request from '@/api/request'

// A~W => 0~22
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

  const re = /"([^"\n\r]*?(?:xx|yy|zz|mm|nn|kk)[^"\n\r]*?)"/gi
  const found = []
  let m
  while ((m = re.exec(s)) !== null) {
    const v = String(m[1] || '').trim()
    if (!v) continue
    found.push(v)
  }

  const seen = new Set()
  const uniq = []
  for (const v of found) {
    if (seen.has(v)) continue
    seen.add(v)
    uniq.push(v)
  }
  return uniq
}

const normalizeFaultCategories = async (rawText) => {
  const resp = await request.post('/test-tools/test-case-assistant/req-design/self-check/normalize', {
    raw_text: String(rawText || ''),
  })
  return String(resp?.normalized ?? '')
}

const askUserForFaultCategories = async () => {
  const rawText = ref('')
  const normalizedText = ref('')

  await ElMessageBox({
    title: '故障类别',
    showCancelButton: true,
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    customClass: 'req-design-selfcheck-dialog',
    message: () => h('div', { style: 'display:flex;flex-direction:column;gap:10px;' }, [
      h('div', { style: 'line-height:1.6;' }, '请列出所有故障类别（推荐格式：主控板故障/随动控制板故障/图像板故障）'),
      h(ElInput, {
        modelValue: rawText.value,
        'onUpdate:modelValue': (v) => { rawText.value = v },
        type: 'textarea',
        autosize: { minRows: 4, maxRows: 10 },
        placeholder: '可直接粘贴一段包含故障类别的原始描述',
      }),
      h('div', { style: 'display:flex;gap:10px;align-items:center;' }, [
        h(ElButton, {
          type: 'primary',
          plain: true,
          onClick: async () => {
            if (!String(rawText.value || '').trim()) {
              ElMessage.warning('请先输入故障类别文本')
              return
            }
            let loadingInstance = null
            try {
              loadingInstance = ElLoading.service({
                lock: true,
                text: '格式转换：AI处理中...',
                background: 'rgba(0, 0, 0, 0.2)',
              })
              normalizedText.value = await normalizeFaultCategories(rawText.value)
              if (normalizedText.value) {
                ElMessage.success('格式转换完成')
              } else {
                ElMessage.warning('格式转换未返回有效结果')
              }
            } catch (e) {
              console.error(e)
              ElMessage.error('格式转换失败：' + (e?.message || '未知错误'))
            } finally {
              if (loadingInstance) loadingInstance.close()
            }
          },
        }, () => '格式转换'),
        h('div', { style: 'color:#6b7280;font-size:12px;' }, '转换后会优先使用规范格式'),
      ]),
      h(ElInput, {
        modelValue: normalizedText.value,
        'onUpdate:modelValue': (v) => { normalizedText.value = v },
        type: 'textarea',
        autosize: { minRows: 2, maxRows: 6 },
        placeholder: '规范格式（可编辑）',
      }),
    ]),
    beforeClose: (action, instance, done) => {
      if (action === 'confirm') {
        if (!String(rawText.value || '').trim() && !String(normalizedText.value || '').trim()) {
          ElMessage.warning('请输入故障类别')
          return
        }
      }
      done()
    },
  })

  return String(normalizedText.value || rawText.value || '').trim()
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

const askUserForVariableValue = async (idx, varKey, defaultValue = '') => {
  const title = `变量${idx + 1}：${varKey}`
  const message = `请为该变量输入替换内容（多个值用“/”隔开）`

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
      inputPlaceholder: '例如：主控板故障/随动控制板故障/图像板故障',
      inputValue: String(defaultValue || ''),
      inputValidator: (v) => {
        if (!String(v || '').trim()) return '请输入变量替换内容'
        return true
      },
      customClass: 'req-design-selfcheck-prompt',
    })

    return String(value || '').trim()
  } finally {
    if (typeof cleanupInterceptors === 'function') cleanupInterceptors()
  }
}

const callReqDesignSelfCheck = async ({ test_item_name, requirement_sub_item_desc, test_item_desc, test_method, variables, fault_categories }) => {
  const resp = await request.post('/test-tools/test-case-assistant/req-design/self-check', {
    test_item_name,
    requirement_sub_item_desc,
    test_item_desc,
    test_method,
    variables,
    fault_categories,
  })

  return {
    test_item_desc: String(resp?.test_item_desc ?? ''),
    test_method: String(resp?.test_method ?? ''),
  }
}

export const useReqDesignSelfCheck = (spreadsheetRef) => {
  const reqDesignSelfCheck = async () => {
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
      ElMessage.warning('自检测暂仅支持单行处理，请只选择一行')
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

    let faultCategories = ''
    try {
      faultCategories = await askUserForFaultCategories()
    } catch (e) {
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
        const val = await askUserForVariableValue(i, key, faultCategories)
        variables[key] = val
      }
    } catch (e) {
      return
    }

    let loadingInstance = null
    try {
      loadingInstance = ElLoading.service({
        lock: true,
        text: '需求设计-自检测：AI处理中...',
        background: 'rgba(0, 0, 0, 0.2)',
      })

      const res = await callReqDesignSelfCheck({
        test_item_name: String(testItemName || ''),
        requirement_sub_item_desc: String(requirementSubItemDesc || ''),
        test_item_desc: String(tDesc || ''),
        test_method: String(uMethod || ''),
        variables,
        fault_categories: faultCategories,
      })

      s.cellText(ri, COL_T_TEST_ITEM_DESC, res.test_item_desc, sheetIndex)
      s.cellText(ri, COL_U_TEST_METHOD, res.test_method, sheetIndex)
      s.reRender()
      ElMessage.success('需求设计-自检测完成')
    } catch (e) {
      console.error(e)
      ElMessage.error('需求设计-自检测失败：' + (e?.message || '未知错误'))
    } finally {
      if (loadingInstance) loadingInstance.close()
    }
  }

  return {
    reqDesignSelfCheck,
  }
}
