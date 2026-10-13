import { h, ref } from 'vue'
import { ElButton, ElInput, ElLoading, ElMessage, ElMessageBox } from 'element-plus'
import request from '@/api/request'

// A~AD => 0~29
const COL_G_TEST_ITEM_NAME = 6
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

const splitValues = (s) => {
  return String(s || '')
    .split('/')
    .map((it) => String(it || '').trim())
    .filter(Boolean)
}

const normalizeFaultCategories = async (rawText) => {
  const resp = await request.post('/test-tools/test-case-assistant/case-design/self-check/normalize', {
    raw_text: String(rawText || ''),
  })
  return String(resp?.normalized ?? '')
}

const askUserForFaultCategories = async () => {
  const rawText = ref('')
  const normalizedText = ref('')

  const focusRawTextarea = () => {
    try {
      const ta = document?.querySelector?.('.case-design-selfcheck-dialog textarea[data-role="fault-raw"]')
      if (ta && typeof ta.focus === 'function') {
        ta.focus()
      }
    } catch (e) {
      // ignore
    }
  }

  await ElMessageBox({
    title: '故障类别',
    showCancelButton: true,
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    customClass: 'case-design-selfcheck-dialog',
    message: () => h('div', { style: 'display:flex;flex-direction:column;gap:10px;' }, [
      h('div', { style: 'line-height:1.6;' }, '请列出所有故障类别（推荐格式：主控板故障/随动控制板故障/图像板故障）'),
      h('textarea', {
        'data-role': 'fault-raw',
        value: rawText.value,
        placeholder: '可直接粘贴一段包含故障类别的原始描述',
        style:
          'width:100%;min-height:110px;max-height:260px;resize:vertical;box-sizing:border-box;'
          + 'border:1px solid #DCDFE6;border-radius:4px;padding:8px 10px;outline:none;'
          + 'font-size:13px;line-height:1.5;',
        onInput: (e) => {
          rawText.value = String(e?.target?.value || '')
        },
        onKeydown: (e) => {
          e?.stopPropagation?.()
        },
        onPaste: (e) => {
          e?.stopPropagation?.()
        },
        onVnodeMounted: () => {
          setTimeout(() => focusRawTextarea(), 0)
        },
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

  // 兜底：弹窗挂载/动画期间再次尝试聚焦
  setTimeout(() => focusRawTextarea(), 50)
  setTimeout(() => focusRawTextarea(), 150)
  setTimeout(() => focusRawTextarea(), 300)

  return String(normalizedText.value || rawText.value || '').trim()
}

const openVariableDialog = async (varItems, defaultValue) => {
  let resultVariables = null

  const content = () => {
    const nodes = []

    nodes.push(
      h(
        'div',
        { style: 'margin-bottom: 10px; color: #374151; font-size: 13px; line-height: 1.5;' },
        '请为每个变量输入替换内容（多个值用“/”分隔）。勾选“裂变变量”后会进行排列组合生成多条用例。'
      )
    )

    ;(varItems || []).forEach((it, idx) => {
      const code = String(it?.code || '').trim()
      const display = String(it?.display || code)
      if (!code) return

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
                placeholder: '例如：随动/自动扫描/手动',
                value: String(defaultValue || ''),
                style:
                  'flex: 1; height: 34px; line-height: 34px; padding: 0 10px; border: 1px solid #D1D5DB; border-radius: 6px; outline: none;',
              }),
            ]),
            h('label', { style: 'display: inline-flex; align-items: center; gap: 6px; color: #374151; font-size: 13px;' }, [
              h('input', {
                type: 'checkbox',
                checked: true,
                'data-var-code': code,
              }),
              h('span', null, '裂变变量'),
            ]),
          ]
        )
      )
    })

    return h('div', { style: 'max-height: 65vh; overflow: auto;' }, nodes)
  }

  await ElMessageBox({
    title: '用例裂变',
    message: content(),
    customClass: 'case-design-selfcheck-fission-box',
    showCancelButton: true,
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    closeOnClickModal: false,
    closeOnPressEscape: false,
    beforeClose: (action, instance, done) => {
      if (action !== 'confirm') {
        done()
        return
      }

      const box = instance?.$el || document?.querySelector?.('.case-design-selfcheck-fission-box.el-message-box')
      if (!box) {
        ElMessage.error('弹窗组件异常，请重试')
        return
      }

      const variables = []
      ;(varItems || []).forEach((it) => {
        const code = String(it?.code || '').trim()
        if (!code) return

        const inputEl = box.querySelector(`input[data-var-code="${code}"]:not([type="checkbox"])`)
        const checkEl = box.querySelector(`input[type="checkbox"][data-var-code="${code}"]`)

        const rawValue = String(inputEl?.value || '')
        const values = splitValues(rawValue)
        if (!values.length) {
          ElMessage.warning(`变量 ${code} 不能为空`)
          return
        }

        variables.push({
          key: code,
          values,
          fissile: Boolean(checkEl?.checked),
        })
      })

      if (!variables.length) {
        ElMessage.warning('未获取到变量配置')
        return
      }

      resultVariables = variables
      done()
    },
  })

  return resultVariables
}

const callCaseDesignSelfCheckFission = async ({ case_name, test_desc, input_condition, expected_result, xx_values }) => {
  const resp = await request.post('/test-tools/test-case-assistant/case-design/self-check/fission', {
    case_name,
    test_desc,
    input_condition,
    expected_result,
    xx_values,
  })

  return Array.isArray(resp?.cases) ? resp.cases : []
}

export const useCaseDesignSelfCheck = (spreadsheetRef, currentTaskIdRef) => {
  const caseDesignSelfCheckFission = async () => {
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
      ElMessage.warning('用例裂变暂仅支持单行处理，请只选择一行')
      return
    }

    const ri = sri
    const testItemName = getCellText(s, ri, COL_G_TEST_ITEM_NAME, sheetIndex)
    if (!String(testItemName || '').trim()) {
      ElMessage.warning('G列(测试项名称)为空')
      return
    }

    const caseName = getCellText(s, ri, COL_I_CASE_NAME, sheetIndex)
    const testDesc = getCellText(s, ri, COL_L_TEST_DESC, sheetIndex)
    const inputCondition = getCellText(s, ri, COL_P_INPUT_CONDITION, sheetIndex)
    const expectedResult = getCellText(s, ri, COL_Q_EXPECTED_RESULT, sheetIndex)

    const rawVars = [
      ...extractVariablesFromText(caseName),
      ...extractVariablesFromText(testDesc),
      ...extractVariablesFromText(inputCondition),
      ...extractVariablesFromText(expectedResult),
    ]

    const varItems = mergeVariablesByCode(rawVars)
    const hasXx = varItems.some((it) => String(it?.code || '').toLowerCase() === 'xx')
    if (!hasXx) {
      ElMessage.warning('未在 I/L/P/Q 中识别到变量占位符（"xx"），无法进行故障类型裂变')
      return
    }

    let faultCategories = ''
    try {
      faultCategories = await askUserForFaultCategories()
    } catch (e) {
      return
    }

    const xxValues = splitValues(faultCategories)
    if (!xxValues.length) {
      ElMessage.warning('故障类别为空，无法裂变')
      return
    }

    let loadingInstance = null
    try {
      loadingInstance = ElLoading.service({
        lock: true,
        text: '用例裂变：AI处理中...',
        background: 'rgba(0, 0, 0, 0.2)',
      })

      const cases = await callCaseDesignSelfCheckFission({
        case_name: String(caseName || ''),
        test_desc: String(testDesc || ''),
        input_condition: String(inputCondition || ''),
        expected_result: String(expectedResult || ''),
        xx_values: xxValues,
      })

      if (!cases.length) {
        ElMessage.warning('AI未返回有效用例')
        return
      }

      cases.forEach((it, idx) => {
        const dstRow = ri + idx
        if (idx > 0) {
          const ok = insertRowAt(s, dstRow)
          if (!ok) return
          copyRowText(s, ri, dstRow, sheetIndex)
        }

        setCellText(s, dstRow, COL_I_CASE_NAME, it.case_name ?? '', sheetIndex)
        setCellText(s, dstRow, COL_L_TEST_DESC, it.test_desc ?? '', sheetIndex)
        setCellText(s, dstRow, COL_P_INPUT_CONDITION, it.input_condition ?? '', sheetIndex)
        setCellText(s, dstRow, COL_Q_EXPECTED_RESULT, it.expected_result ?? '', sheetIndex)
      })

      s.reRender()
      ElMessage.success(`用例裂变完成：生成 ${cases.length} 条`)
    } catch (e) {
      console.error(e)
      ElMessage.error('用例裂变失败：' + (e?.message || '未知错误'))
    } finally {
      if (loadingInstance) loadingInstance.close()
    }
  }

  const caseDesignSelfCheckWrite = async () => {
    const s = spreadsheetRef?.value
    if (!s) {
      ElMessage.error('表格未初始化')
      return
    }

    const taskId = currentTaskIdRef?.value
    if (!taskId) {
      ElMessage.warning('请先导入Excel并创建任务，再执行用例编写')
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

    const focusCodeTextarea = () => {
      try {
        const ta = document?.querySelector?.('.case-design-selfcheck-write-box textarea[data-role="entry-code"]')
        if (ta && typeof ta.focus === 'function') ta.focus()
      } catch (e) {
        // ignore
      }
    }

    const autoResizeTextarea = (ta) => {
      if (!ta) return
      try {
        ta.style.height = 'auto'
        const max = Math.max(220, Math.floor(window.innerHeight * 0.6))
        ta.style.height = Math.min(ta.scrollHeight + 2, max) + 'px'
      } catch (e) {
        // ignore
      }
    }

    let codeSnippet = ''
    try {
      const draft = ref('')
      await ElMessageBox({
        title: '用例编写',
        message: () =>
          h('div', { style: 'display:flex;flex-direction:column;gap:10px;max-width:920px;' }, [
            h('div', { style: 'line-height:1.6;color:#374151;font-size:13px;' }, '请粘贴入口函数中所有初始化相关的代码片段（用于定位文件/行号）'),
            h('textarea', {
              'data-role': 'entry-code',
              value: draft.value,
              placeholder: '粘贴代码片段，例如 main.c 中 main 函数的初始化部分',
              style:
                'width:100%;min-height:260px;max-height:60vh;resize:vertical;overflow:auto;box-sizing:border-box;'
                + 'border:1px solid #DCDFE6;border-radius:6px;padding:10px 12px;outline:none;'
                + 'font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;'
                + 'font-size:12px;line-height:1.5;white-space:pre;tab-size:2;',
              onInput: (e) => {
                draft.value = String(e?.target?.value || '')
                autoResizeTextarea(e?.target)
              },
              onKeydown: (e) => {
                e?.stopPropagation?.()
              },
              onPaste: (e) => {
                e?.stopPropagation?.()
              },
              onVnodeMounted: (vnode) => {
                const el = vnode?.el
                setTimeout(() => {
                  focusCodeTextarea()
                  autoResizeTextarea(el)
                }, 0)
              },
            }),
            h('div', { style: 'color:#6b7280;font-size:12px;' }, '提示：代码较长时可滚动；窗口会尽量自适应增高显示更多内容。'),
          ]),
        customClass: 'case-design-selfcheck-write-box',
        showCancelButton: true,
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        closeOnClickModal: false,
        closeOnPressEscape: false,
        beforeClose: (action, instance, done) => {
          if (action === 'confirm') {
            if (!String(draft.value || '').trim()) {
              ElMessage.warning('代码片段不能为空')
              focusCodeTextarea()
              return
            }
          }
          done()
        },
      })
      codeSnippet = String(draft.value || '').trim()
    } catch (e) {
      if (e === 'cancel' || e === 'close') return
      console.error(e)
      ElMessage.error('弹窗异常：' + (e?.message || '未知错误'))
      return
    }

    // 兜底：弹窗挂载/动画期间再次尝试聚焦
    setTimeout(() => focusCodeTextarea(), 50)
    setTimeout(() => focusCodeTextarea(), 150)
    setTimeout(() => focusCodeTextarea(), 300)

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
        text: `用例编写：处理中（0/${rows.length}）`,
        background: 'rgba(0, 0, 0, 0.2)',
      })

      const resp = await request.post('/test-tools/test-case-assistant/case-design/self-check/write', {
        task_id: taskId,
        entry_code_snippet: codeSnippet,
        rows,
      })

      const results = Array.isArray(resp?.results) ? resp.results : []
      const errors = Array.isArray(resp?.errors) ? resp.errors : []

      results.forEach((it, idx) => {
        if (loadingInstance) loadingInstance.setText(`用例编写：回填中（${idx + 1}/${results.length}）`)
        const ri = Number(it.row_index)
        if (!Number.isFinite(ri)) return
        setCellText(s, ri, COL_I_CASE_NAME, it.case_name ?? '', sheetIndex)
        setCellText(s, ri, COL_L_TEST_DESC, it.test_desc ?? '', sheetIndex)
        setCellText(s, ri, COL_P_INPUT_CONDITION, it.input_condition ?? '', sheetIndex)
        setCellText(s, ri, COL_Q_EXPECTED_RESULT, it.expected_result ?? '', sheetIndex)
      })

      s.reRender()

      if (errors.length) {
        ElMessage.warning(`用例编写完成：成功 ${results.length} 条，失败 ${errors.length} 条（可查看后端日志）`)
      } else {
        ElMessage.success(`用例编写完成：成功 ${results.length} 条`)
      }
    } catch (e) {
      console.error(e)
      ElMessage.error('用例编写失败：' + (e?.message || '未知错误'))
    } finally {
      if (loadingInstance) loadingInstance.close()
    }
  }

  return {
    caseDesignSelfCheckFission,
    caseDesignSelfCheckWrite,
  }
}
