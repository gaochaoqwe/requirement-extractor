import { ElLoading, ElMessage, ElMessageBox } from 'element-plus'
import { h } from 'vue'
import request from '@/api/request'

// A~AD => 0~29
const COL_I_CASE_NAME = 8
const COL_L_TEST_DESC = 11
const COL_P_INPUT_CONDITION = 15
const COL_Q_EXPECTED_RESULT = 16
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

const extractVariablesFromText = (text) => {
  const s = String(text || '')
  if (!s) return []
  const re = /\"([^\"\n\r]*?(?:xx|yy|zz|mm|nn|kk)[^\"\n\r]*?)\"/gi
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

const normalizeVarCode = (raw) => {
  const s = String(raw || '').toLowerCase()
  if (s.includes('xx')) return 'xx'
  if (s.includes('yy')) return 'yy'
  if (s.includes('zz')) return 'zz'
  if (s.includes('mm')) return 'mm'
  if (s.includes('nn')) return 'nn'
  if (s.includes('kk')) return 'kk'
  return ''
}

const mergeVariablesByCode = (rawVars) => {
  const map = new Map()
  ;(rawVars || []).forEach((v) => {
    const code = normalizeVarCode(v)
    if (!code) return
    if (!map.has(code)) map.set(code, v)
  })

  const order = ['xx', 'yy', 'zz', 'mm', 'nn', 'kk']
  const out = []
  order.forEach((code) => {
    if (map.has(code)) out.push({ code, display: map.get(code) })
  })
  return out
}

const bindMessageBoxInputInterceptors = (rootEl) => {
  const onPasteCapture = (evt) => {
    evt.stopImmediatePropagation()
  }

  const onKeydownCapture = (evt) => {
    const key = String(evt?.key || '').toLowerCase()
    const isPaste = (evt.ctrlKey || evt.metaKey) && key === 'v'
    if (!isPaste) return
    evt.stopImmediatePropagation()
  }

  const root = rootEl || document
  const inputs = root?.querySelectorAll?.('input, textarea')
  if (!inputs || !inputs.length) return () => {}

  inputs.forEach((el) => {
    el.addEventListener('paste', onPasteCapture, true)
    el.addEventListener('keydown', onKeydownCapture, true)
  })

  return () => {
    inputs.forEach((el) => {
      el.removeEventListener('paste', onPasteCapture, true)
      el.removeEventListener('keydown', onKeydownCapture, true)
    })
  }
}

const splitValues = (s) => {
  return String(s || '')
    .split('/')
    .map((it) => String(it || '').trim())
    .filter(Boolean)
}

const openVariableDialog = async (varItems) => {
  let cleanupInterceptors = null
  let resultVariables = null

  const content = () => {
    const nodes = []

    nodes.push(
      h(
        'div',
        { style: 'margin-bottom: 10px; color: #374151; font-size: 13px; line-height: 1.5;' },
        '请为每个变量输入替换内容（多个值用"/"分隔）。勾选"裂变变量"后会进行排列组合生成多条用例。勾选"一对一变量"的变量取值个数必须一致，按顺序一一对应。'
      )
    )

    ;(varItems || []).forEach((it, idx) => {
      const code = String(it?.code || '').trim()
      const display = String(it?.display || code)
      if (!code) return
      
      // 从 display 中提取括号内的内容作为示例
      let placeholder = '例如：随动/自动扫描/手动'
      const match = display.match(/[（(]([^）)]+)[）)]/)
      if (match && match[1]) {
        const exampleContent = match[1].trim()
        if (exampleContent) {
          placeholder = `例如：${exampleContent}`
        }
      }
      
      nodes.push(
        h(
          'div',
          {
            style:
              'padding: 10px 12px; border: 1px solid #E5E7EB; border-radius: 8px; margin-bottom: 10px; background: #FAFAFA;',
          },
          [
            h('div', { style: 'font-weight: 600; margin-bottom: 8px; color: #111827;' }, `变量${idx + 1}：${display}`),
            h('div', { style: 'display: flex; gap: 10px; align-items: center; margin-bottom: 8px;' }, [
              h('input', {
                'data-var-code': code,
                placeholder: placeholder,
                style:
                  'flex: 1; height: 34px; line-height: 34px; padding: 0 10px; border: 1px solid #D1D5DB; border-radius: 6px; outline: none;',
              }),
            ]),
            h('div', { style: 'display: flex; gap: 16px;' }, [
              h('label', { style: 'display: inline-flex; align-items: center; gap: 6px; color: #374151; font-size: 13px;' }, [
                h('input', {
                  type: 'checkbox',
                  checked: true,
                  'data-var-code': code,
                  'data-checkbox-type': 'fissile',
                }),
                h('span', null, '裂变变量'),
              ]),
              h('label', { style: 'display: inline-flex; align-items: center; gap: 6px; color: #374151; font-size: 13px;' }, [
                h('input', {
                  type: 'checkbox',
                  checked: false,
                  'data-var-code': code,
                  'data-checkbox-type': 'one-to-one',
                }),
                h('span', null, '一对一变量'),
              ]),
            ]),
          ]
        )
      )
    })

    return h('div', { style: 'max-height: 65vh; overflow: auto;' }, nodes)
  }

  const p = ElMessageBox({
    title: '用例设计-通用功能',
    message: content(),
    customClass: 'case-design-common-box',
    showCancelButton: true,
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    closeOnClickModal: false,
    closeOnPressEscape: false,
    beforeClose: (action, instance, done) => {
      console.log('[case_design_common] beforeClose action=', action)
      if (action !== 'confirm') {
        console.log('[case_design_common] cancel/close')
        done()
        return
      }

      ElMessage.info('通用功能：校验中...')

      const box = instance?.$el || document?.querySelector?.('.case-design-common-box.el-message-box')
      const inputEls = box?.querySelectorAll?.('input[data-var-code]')
      if (!box || !inputEls) {
        console.error('[case_design_common] box not found', { box })
        ElMessage.error('弹窗组件异常，请重试')
        return
      }

      console.log('[case_design_common] found inputs=', inputEls.length)

      const getInputValue = (code) => {
        const el = box.querySelector(`input[data-var-code="${code}"]:not([type="checkbox"])`)
        return String(el?.value || '')
      }
      const getFissileValue = (code) => {
        const el = box.querySelector(`input[data-var-code="${code}"][data-checkbox-type="fissile"]`)
        return !!el?.checked
      }
      const getOneToOneValue = (code) => {
        const el = box.querySelector(`input[data-var-code="${code}"][data-checkbox-type="one-to-one"]`)
        return !!el?.checked
      }

      const out = []
      const oneToOneVars = []
      
      for (const it of varItems || []) {
        const code = String(it?.code || '').trim()
        const display = String(it?.display || code)
        if (!code) continue
        const values = splitValues(getInputValue(code))
        if (!values.length) {
          console.log('[case_design_common] empty value for', code)
          ElMessage.warning(`请填写变量：${display}`)
          return
        }
        
        const fissile = getFissileValue(code)
        const oneToOne = getOneToOneValue(code)
        
        out.push({
          key: code,
          values,
          fissile: fissile,
          one_to_one: oneToOne,
        })
        
        if (oneToOne) {
          oneToOneVars.push({ code, display, count: values.length })
        }
      }

      // 校验一对一变量的取值个数必须一致
      if (oneToOneVars.length > 1) {
        const firstCount = oneToOneVars[0].count
        const inconsistent = oneToOneVars.find(v => v.count !== firstCount)
        if (inconsistent) {
          ElMessage.warning(`一对一变量的取值个数必须一致！${oneToOneVars[0].display}有${firstCount}个值，${inconsistent.display}有${inconsistent.count}个值`)
          return
        }
      }

      resultVariables = out
      console.log('[case_design_common] collected variables=', resultVariables)
      done()
    },
  })

  p.then((res) => {
    console.log('[case_design_common] messageBox promise resolved', res)
  }).catch((err) => {
    console.log('[case_design_common] messageBox promise rejected', err)
  })

  // messageBox 显示后立即绑定：阻止事件传播到表格，但不影响输入框本身粘贴
  setTimeout(() => {
    const box = document?.querySelector?.('.case-design-common-box.el-message-box')
    if (!box) return
    console.log('[case_design_common] bind interceptors')
    cleanupInterceptors = bindMessageBoxInputInterceptors(box)
    
    // 绑定复选框互斥逻辑
    const fissileCheckboxes = box.querySelectorAll('input[data-checkbox-type="fissile"]')
    const oneToOneCheckboxes = box.querySelectorAll('input[data-checkbox-type="one-to-one"]')
    
    fissileCheckboxes.forEach(fissileBox => {
      fissileBox.addEventListener('change', () => {
        if (fissileBox.checked) {
          const code = fissileBox.getAttribute('data-var-code')
          const oneToOneBox = box.querySelector(`input[data-var-code="${code}"][data-checkbox-type="one-to-one"]`)
          if (oneToOneBox) oneToOneBox.checked = false
        }
      })
    })
    
    oneToOneCheckboxes.forEach(oneToOneBox => {
      oneToOneBox.addEventListener('change', () => {
        if (oneToOneBox.checked) {
          const code = oneToOneBox.getAttribute('data-var-code')
          const fissileBox = box.querySelector(`input[data-var-code="${code}"][data-checkbox-type="fissile"]`)
          if (fissileBox) fissileBox.checked = false
        }
      })
    })
    
    const first = box.querySelector?.('input, textarea')
    if (first && typeof first.focus === 'function') first.focus()
  }, 0)

  try {
    await p
    console.log('[case_design_common] messageBox resolved')
  } finally {
    if (typeof cleanupInterceptors === 'function') cleanupInterceptors()
  }

  if (!Array.isArray(resultVariables) || !resultVariables.length) {
    console.error('[case_design_common] resultVariables empty', resultVariables)
    throw new Error('弹窗未返回变量配置')
  }

  console.log('[case_design_common] openVariableDialog return', resultVariables)

  return resultVariables
}

const callCaseDesignCommon = async ({ case_name, test_desc, input_condition, expected_result, variables }) => {
  const resp = await request.post('/test-tools/test-case-assistant/case-design/common', {
    case_name,
    test_desc,
    input_condition,
    expected_result,
    variables,
  })

  return Array.isArray(resp?.cases) ? resp.cases : []
}

export const useCaseDesignCommon = (spreadsheetRef) => {
  const caseDesignCommon = async () => {
    console.log('[case_design_common] start')
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
    const baseCaseName = getCellText(s, ri, COL_I_CASE_NAME, sheetIndex)
    const baseTestDesc = getCellText(s, ri, COL_L_TEST_DESC, sheetIndex)
    const baseInput = getCellText(s, ri, COL_P_INPUT_CONDITION, sheetIndex)
    const baseExpected = getCellText(s, ri, COL_Q_EXPECTED_RESULT, sheetIndex)

    const vars = [
      ...extractVariablesFromText(baseCaseName),
      ...extractVariablesFromText(baseTestDesc),
      ...extractVariablesFromText(baseInput),
      ...extractVariablesFromText(baseExpected),
    ]
    const uniqVars = mergeVariablesByCode(vars)

    if (!uniqVars.length) {
      ElMessage.warning('未在 I/L/P/Q 中识别到变量占位符（"xx/yy/zz/mm/nn/kk..."）')
      return
    }

    let variables = []
    try {
      variables = await openVariableDialog(uniqVars)
      console.log('[case_design_common] variables collected', variables)
      ElMessage.success('变量已收集，开始请求后端...')
    } catch (e) {
      console.log('[case_design_common] dialog cancelled/failed', e)
      return
    }

    let loadingInstance = null
    try {
      loadingInstance = ElLoading.service({
        lock: true,
        text: '用例设计-通用功能：AI处理中...',
        background: 'rgba(0, 0, 0, 0.2)',
      })

      console.log('[case_design_common] calling backend /case-design/common')

      const cases = await callCaseDesignCommon({
        case_name: String(baseCaseName || ''),
        test_desc: String(baseTestDesc || ''),
        input_condition: String(baseInput || ''),
        expected_result: String(baseExpected || ''),
        variables,
      })

      console.log('[case_design_common] backend returned cases=', cases?.length)

      if (!cases.length) {
        ElMessage.warning('AI未返回用例')
        return
      }

      // 第一条回填当前行，其余插入到下方
      const insertCount = Math.max(0, cases.length - 1)
      for (let i = 0; i < insertCount; i += 1) {
        const ok = insertRowAt(s, ri + 1 + i)
        if (!ok) throw new Error('插入行失败')
        copyRowText(s, ri, ri + 1 + i, sheetIndex)
      }

      cases.forEach((c, idx) => {
        const targetRow = ri + idx
        setCellText(s, targetRow, COL_I_CASE_NAME, c.case_name ?? '', sheetIndex)
        setCellText(s, targetRow, COL_L_TEST_DESC, c.test_desc ?? '', sheetIndex)
        setCellText(s, targetRow, COL_P_INPUT_CONDITION, c.input_condition ?? '', sheetIndex)
        setCellText(s, targetRow, COL_Q_EXPECTED_RESULT, c.expected_result ?? '', sheetIndex)
      })

      s.reRender()
      ElMessage.success(`用例设计-通用功能完成：生成 ${cases.length} 条用例`)
    } catch (e) {
      console.error(e)
      ElMessage.error('用例设计-通用功能失败：' + (e?.message || '未知错误'))
    } finally {
      if (loadingInstance) loadingInstance.close()
    }
  }

  return {
    caseDesignCommon,
  }
}
