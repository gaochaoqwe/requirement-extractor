import { h, ref, defineComponent, createApp, nextTick } from 'vue'
import { ElMessage, ElMessageBox, ElInput, ElDialog, ElProgress, ElButton } from 'element-plus'
import request from '@/api/request'

// A~Q => 0~16
const COL_E_TEST_ROUND = 4
const COL_G_CASE_TEST_ITEM_NAME = 6
const COL_H_TEST_MARK = 7
const COL_I_CASE_NAME = 8
const COL_J_CASE_ID = 9
const COL_L_TEST_DESC = 11
const COL_O_TEST_ITEM_NAME = 14
const COL_P_INPUT_CONDITION = 15
const COL_Q_EXPECTED_RESULT = 16

// A~X => 0~23
const COL_S_CASE_DESIGNER = 18
const COL_T_TEST_ITEM_DESC = 19
const COL_U_TEST_METHOD = 20
const COL_W_TESTER = 22
const COL_X_SUPERVISOR = 23

// A~AC => 0~28
const COL_V_PROOF_TIME = 21
const COL_Y_TEST_TIME = 24
const COL_AC_EXEC_YYYY_MM = 28

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

const normalizeRange = (range) => {
  if (!range) return null
  const sri = Math.min(range.sri, range.eri)
  const eri = Math.max(range.sri, range.eri)
  const sci = Math.min(range.sci, range.eci)
  const eci = Math.max(range.sci, range.eci)
  return { sri, eri, sci, eci }
}

const getCellText = (s, ri, ci, sheetIndex) => {
  const cell = s?.cell(ri, ci, sheetIndex)
  return cell?.text ?? ''
}

const setCellText = (s, ri, ci, text, sheetIndex) => {
  s?.cellText(ri, ci, text ?? '', sheetIndex)
}

const rowHasAnyData = (s, ri, sheetIndex) => {
  for (let ci = 0; ci <= COL_AC_EXEC_YYYY_MM; ci += 1) {
    const v = String(getCellText(s, ri, ci, sheetIndex) || '').trim()
    if (v) return true
  }
  return false
}

// 判断测试轮次（E列）是否为第一轮：忽略第二轮、第三轮等；轮次为空时按第一轮处理
const isFirstRound = (value) => {
  const text = String(value ?? '').trim()
  if (!text) return true
  if (text.includes('一')) return true
  const matched = text.match(/\d+/)
  return !!matched && matched[0] === '1'
}

const pad2 = (n) => String(n).padStart(2, '0')

const formatDateSlash = (d) => {
  const y = d.getFullYear()
  const m = pad2(d.getMonth() + 1)
  const day = pad2(d.getDate())
  return `${y}/${m}/${day}`
}

const formatYYYYMM = (d) => {
  const y = d.getFullYear()
  const m = pad2(d.getMonth() + 1)
  return `${y}-${m}`
}

const parseStartDate = (raw) => {
  const s = String(raw || '').trim()
  const m = s.match(/^(\d{4})\/(\d{2})\/(\d{2})$/)
  if (!m) return null
  const y = Number(m[1])
  const mo = Number(m[2])
  const da = Number(m[3])
  if (!Number.isFinite(y) || !Number.isFinite(mo) || !Number.isFinite(da)) return null
  const d = new Date(y, mo - 1, da)
  if (d.getFullYear() !== y || (d.getMonth() + 1) !== mo || d.getDate() !== da) return null
  d.setHours(0, 0, 0, 0)
  return d
}

const addDays = (d, days) => {
  const nd = new Date(d)
  nd.setDate(nd.getDate() + days)
  nd.setHours(0, 0, 0, 0)
  return nd
}

const buildDateList = (start, days) => {
  const out = []
  const n = Math.max(0, Number(days) || 0)
  for (let i = 0; i < n; i += 1) out.push(addDays(start, i))
  return out
}

const pickDateByIndex = (dateList, idx, total) => {
  if (!Array.isArray(dateList) || dateList.length === 0) return null
  const n = dateList.length
  const t = Math.max(1, Number(total) || 1)
  const i = Math.max(0, Number(idx) || 0)
  const di = Math.min(n - 1, Math.floor((i * n) / t))
  return dateList[di] || null
}

const getNeighborCaseNames = (s, sheetIndex, targetRi, testItemName) => {
  const names = []
  if (!testItemName) return names

  const tryAdd = (ri) => {
    if (!Number.isFinite(ri) || ri < 0) return
    const g = String(getCellText(s, ri, COL_G_CASE_TEST_ITEM_NAME, sheetIndex) || '').trim()
    if (!g || g !== testItemName) return
    const name = String(getCellText(s, ri, COL_I_CASE_NAME, sheetIndex) || '').trim()
    if (!name) return
    if (!names.includes(name)) names.push(name)
  }

  for (let i = 1; i <= 5; i += 1) {
    tryAdd(targetRi - i)
    if (names.length >= 5) break
    tryAdd(targetRi + i)
    if (names.length >= 5) break
  }

  return names
}

const ensureRender = (s) => {
  if (typeof s?.reRender === 'function') s.reRender()
  else if (typeof s?.render === 'function') s.render()
}

const createProgressOverlay = async ({ title, subtitle = '' }) => {
  const container = document.createElement('div')
  document.body.appendChild(container)
  const state = ref({ visible: true, current: 0, total: 0, title, subtitle, status: '准备中...' , log: '' })

  const app = createApp({
    setup() {
      return () => h(ElDialog, {
        modelValue: state.value.visible,
        'onUpdate:modelValue': (v) => { state.value.visible = v },
        title: state.value.title,
        width: '520px',
        closeOnClickModal: false,
        closeOnPressEscape: false,
        showClose: false,
        appendToBody: true,
      }, {
        default: () => h('div', { style: 'display:flex;flex-direction:column;gap:14px;' }, [
          h('div', { style: 'display:flex;justify-content:space-between;align-items:center;' }, [
            h('div', { style: 'font-size:14px;color:#4b5563;' }, state.value.subtitle || ''),
            h('div', { style: 'font-size:13px;color:#2563eb;font-weight:600;' }, `${state.value.current}/${state.value.total}`),
          ]),
          h(ElProgress, { percentage: state.value.total ? Math.round((state.value.current / state.value.total) * 100) : 0, status: 'active', strokeWidth: 12 }),
          h('div', { style: 'padding:12px 14px;background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;color:#111827;min-height:48px;white-space:pre-wrap;line-height:1.6;' }, state.value.status),
          h('div', { style: 'display:flex;gap:10px;justify-content:flex-end;' }, [
            h(ElButton, { type: 'primary', disabled: true }, { default: () => '处理中' }),
          ]),
        ]),
      })
    },
  })

  app.mount(container)

  return {
    update(next) {
      state.value = { ...state.value, ...next }
    },
    close() {
      state.value.visible = false
      setTimeout(() => {
        app.unmount()
        container.remove()
      }, 200)
    },
  }
}

export const useCaseSheetSmartFill = (spreadsheetRef, currentTaskIdRef, ctxMenuSelectionRef = null, sheetListRef = null) => {
  const resolveSelectedRange = (s, useSelectionCache = false) => {
    const cachedRange = useSelectionCache ? normalizeRange(ctxMenuSelectionRef?.value) : null
    if (cachedRange) return cachedRange
    return normalizeRange(getSelectedRange(s))
  }

  const hasCachedSelection = () => {
    const range = normalizeRange(ctxMenuSelectionRef?.value)
    return !!(range && Number.isFinite(range.sri) && Number.isFinite(range.eri) && range.eri >= range.sri)
  }

  const smartFillCaseId = async ({ useSelectionCache = false } = {}) => {
    const s = spreadsheetRef?.value
    if (!s) {
      ElMessage.error('表格未初始化')
      return
    }

    if (!useSelectionCache && !hasCachedSelection()) {
      ElMessage.warning('请先选中一行或多行，再执行此操作')
      return
    }

    const range = resolveSelectedRange(s, useSelectionCache)
    if (!range || !Number.isFinite(range.sri) || !Number.isFinite(range.eri) || range.eri < range.sri) {
      ElMessage.warning('请先选择一行或多行才能执行此操作')
      return
    }

    const sheetIndex = getActiveSheetIndex(s)

    const rows = []
    for (let ri = range.sri; ri <= range.eri; ri += 1) {
      if (!rowHasAnyData(s, ri, sheetIndex)) continue
      const h = String(getCellText(s, ri, COL_H_TEST_MARK, sheetIndex) || '').trim()
      if (!h) continue
      rows.push({ ri, h })
    }

    if (rows.length === 0) {
      ElMessage.warning('选中范围内未找到可生成编号的有效行（需H列有测试标识）')
      return
    }

    rows.sort((a, b) => a.ri - b.ri)

    const groups = new Map()
    for (const it of rows) {
      if (!groups.has(it.h)) groups.set(it.h, [])
      groups.get(it.h).push(it.ri)
    }

    let written = 0
    for (const [h, ris] of groups.entries()) {
      ris.sort((a, b) => a - b)
      for (let i = 0; i < ris.length; i += 1) {
        const ri = ris[i]
        const seq = String(i + 1).padStart(2, '0')
        const id = `${h}-${seq}`
        setCellText(s, ri, COL_J_CASE_ID, id, sheetIndex)
        written += 1
      }
    }

    if (typeof s?.reRender === 'function') s.reRender()
    else if (typeof s?.render === 'function') s.render()

    ElMessage.success(`测试用例编号填充完成（${written}条）`)
  }

  const smartFillCaseName = async ({ useSelectionCache = false } = {}) => {
    const s = spreadsheetRef?.value
    if (!s) {
      ElMessage.error('表格未初始化')
      return
    }

    if (!useSelectionCache && !hasCachedSelection()) {
      ElMessage.warning('请先选中一行或多行，再执行此操作')
      return
    }

    const range = resolveSelectedRange(s, useSelectionCache)
    if (!range || !Number.isFinite(range.sri) || !Number.isFinite(range.eri) || range.eri < range.sri) {
      ElMessage.warning('请先选择一行或多行才能执行此操作')
      return
    }

    const sheetIndex = getActiveSheetIndex(s)

    const rows = []
    for (let ri = range.sri; ri <= range.eri; ri += 1) {
      const testItemName = String(getCellText(s, ri, COL_G_CASE_TEST_ITEM_NAME, sheetIndex) || '').trim()
      const testDesc = String(getCellText(s, ri, COL_L_TEST_DESC, sheetIndex) || '')
      const inputCondition = String(getCellText(s, ri, COL_P_INPUT_CONDITION, sheetIndex) || '')
      const expectedResult = String(getCellText(s, ri, COL_Q_EXPECTED_RESULT, sheetIndex) || '')
      const neighborCaseNames = getNeighborCaseNames(s, sheetIndex, ri, testItemName)
      rows.push({
        row_index: ri,
        test_item_name: testItemName,
        test_desc: testDesc,
        input_condition: inputCondition,
        expected_result: expectedResult,
        neighbor_case_names: neighborCaseNames,
      })
    }

    const taskId = currentTaskIdRef?.value
    if (!taskId) {
      ElMessage.warning('请先导入Excel并创建任务，再执行智能填充')
      return
    }

    const progress = await createProgressOverlay({ title: '智能生成用例名称', subtitle: '正在逐条分析并回填选中行' })
    try {
      const resp = await request.post('/test-tools/test-case-assistant/case-fill/case-name', { task_id: taskId, rows })
      const results = Array.isArray(resp?.results) ? resp.results : []
      const errors = Array.isArray(resp?.errors) ? resp.errors : []
      if (results.length === 0) {
        const errMsg = String(errors?.[0]?.error || '')
        ElMessage.warning(errMsg ? `未生成任何用例名称：${errMsg}` : '未生成任何用例名称')
        return
      }

      let written = 0
      for (const it of results) {
        const ri = Number(it?.row_index)
        if (!Number.isFinite(ri)) continue
        const name = String(it?.case_name || '').trim()
        if (!name) continue
        setCellText(s, ri, COL_I_CASE_NAME, name, sheetIndex)
        written += 1
        progress.update({
          current: Number(it?.progress_current) || written,
          total: Number(it?.progress_total) || rows.length,
          status: `已生成第 ${Number(it?.progress_current) || written} / ${Number(it?.progress_total) || rows.length} 条\n当前写入：第 ${ri + 1} 行`,
        })
        await nextTick()
      }

      ensureRender(s)

      if (written === 0) {
        const errMsg = String(errors?.[0]?.error || '')
        ElMessage.warning(errMsg ? `未写入任何用例名称：${errMsg}` : '未写入任何用例名称')
        return
      }

      ElMessage.success(`用例名称填充完成（${written}条）`)
    } catch (e) {
      ElMessage.error(e?.message || '智能填充失败')
    } finally {
      progress.close()
    }
  }

  const smartFillTestDesc = async ({ useSelectionCache = false } = {}) => {
    const s = spreadsheetRef?.value
    if (!s) {
      ElMessage.error('表格未初始化')
      return
    }

    if (!useSelectionCache && !hasCachedSelection()) {
      ElMessage.warning('请先选中一行或多行，再执行此操作')
      return
    }

    const range = resolveSelectedRange(s, useSelectionCache)
    if (!range || !Number.isFinite(range.sri) || !Number.isFinite(range.eri) || range.eri < range.sri) {
      ElMessage.warning('请先选择一行或多行才能执行此操作')
      return
    }

    const sheetIndex = getActiveSheetIndex(s)

    const rows = []
    for (let ri = range.sri; ri <= range.eri; ri += 1) {
      const testItemName = String(getCellText(s, ri, COL_G_CASE_TEST_ITEM_NAME, sheetIndex) || '').trim()
      const caseName = String(getCellText(s, ri, COL_I_CASE_NAME, sheetIndex) || '').trim()
      const inputCondition = String(getCellText(s, ri, COL_P_INPUT_CONDITION, sheetIndex) || '')
      const expectedResult = String(getCellText(s, ri, COL_Q_EXPECTED_RESULT, sheetIndex) || '')
      rows.push({
        row_index: ri,
        test_item_name: testItemName,
        case_name: caseName,
        input_condition: inputCondition,
        expected_result: expectedResult,
      })
    }

    const taskId = currentTaskIdRef?.value
    if (!taskId) {
      ElMessage.warning('请先导入Excel并创建任务，再执行智能填充')
      return
    }

    const progress = await createProgressOverlay({ title: '智能生成测试描述', subtitle: '正在逐条分析并回填选中行' })
    try {
      const resp = await request.post('/test-tools/test-case-assistant/case-fill/test-desc', { task_id: taskId, rows })
      const results = Array.isArray(resp?.results) ? resp.results : []
      const errors = Array.isArray(resp?.errors) ? resp.errors : []
      if (results.length === 0) {
        const errMsg = String(errors?.[0]?.error || '')
        ElMessage.warning(errMsg ? `未生成任何测试描述：${errMsg}` : '未生成任何测试描述')
        return
      }

      let written = 0
      for (const it of results) {
        const ri = Number(it?.row_index)
        if (!Number.isFinite(ri)) continue
        const desc = String(it?.test_desc || '').trim()
        if (!desc) continue
        setCellText(s, ri, COL_L_TEST_DESC, desc, sheetIndex)
        written += 1
        progress.update({
          current: Number(it?.progress_current) || written,
          total: Number(it?.progress_total) || rows.length,
          status: `已生成第 ${Number(it?.progress_current) || written} / ${Number(it?.progress_total) || rows.length} 条\n当前写入：第 ${ri + 1} 行`,
        })
        await nextTick()
      }

      ensureRender(s)

      if (written === 0) {
        const errMsg = String(errors?.[0]?.error || '')
        ElMessage.warning(errMsg ? `未写入任何测试描述：${errMsg}` : '未写入任何测试描述')
        return
      }

      ElMessage.success(`测试描述填充完成（${written}条）`)
    } catch (e) {
      ElMessage.error(e?.message || '智能填充失败')
    } finally {
      progress.close()
    }
  }

  const smartFillTester = async () => {
    const s = spreadsheetRef?.value
    if (!s) {
      ElMessage.error('表格未初始化')
      return
    }

    const sheetIndex = getActiveSheetIndex(s)

    const designerAndTester = ref('')
    const proofreader = ref('贾瑞')
    const supervisor = ref('于素芬')

    const sheet = s?.sheet
    const prevFocusing = sheet?.focusing
    if (sheet) sheet.focusing = false

    const DialogForm = defineComponent({
      name: 'SmartFillTesterDialogForm',
      setup() {
        return () => h('div', { style: 'display:flex;flex-direction:column;gap:10px;' }, [
          h('div', { style: 'display:flex;align-items:center;gap:10px;' }, [
            h('div', { style: 'width:120px;flex:0 0 auto;' }, '用例设计人/测试人员'),
            h(ElInput, {
              modelValue: designerAndTester.value,
              'onUpdate:modelValue': (v) => { designerAndTester.value = v },
              placeholder: '请输入用例设计人/测试人员',
              autofocus: true,
            }),
          ]),
          h('div', { style: 'display:flex;align-items:center;gap:10px;' }, [
            h('div', { style: 'width:90px;flex:0 0 auto;' }, '校对人'),
            h(ElInput, {
              modelValue: proofreader.value,
              'onUpdate:modelValue': (v) => { proofreader.value = v },
              placeholder: '请输入校对人',
            }),
          ]),
          h('div', { style: 'display:flex;align-items:center;gap:10px;' }, [
            h('div', { style: 'width:90px;flex:0 0 auto;' }, '监督人员'),
            h(ElInput, {
              modelValue: supervisor.value,
              'onUpdate:modelValue': (v) => { supervisor.value = v },
              placeholder: '请输入监督人员',
            }),
          ]),
        ])
      },
    })

    try {
      await ElMessageBox({
        title: '测试人员智能填充',
        message: h(DialogForm),
        showCancelButton: true,
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        closeOnClickModal: false,
        closeOnPressEscape: false,
        beforeClose: (action, _instance, done) => {
          if (action === 'confirm') {
            if (!String(designerAndTester.value || '').trim()) {
              ElMessage.warning('请输入用例设计人/测试人员')
              return
            }
          }
          done()
        },
      })
    } catch (_) {
      return
    } finally {
      if (sheet) sheet.focusing = prevFocusing
    }

    const d = String(designerAndTester.value || '').trim()
    const t = d
    const p = String(proofreader.value || '').trim()
    const sp = String(supervisor.value || '').trim()

    const maxRows = s?.sheet?.data?.rows?.len
    const upper = Number.isFinite(maxRows) && maxRows > 0 ? maxRows : 1000

    let filled = 0
    let started = false
    for (let ri = 1; ri < upper; ri += 1) {
      const has = rowHasAnyData(s, ri, sheetIndex)
      if (!has) {
        if (started) break
        continue
      }
      started = true

      setCellText(s, ri, COL_S_CASE_DESIGNER, d, sheetIndex)
      setCellText(s, ri, COL_T_PROOFREADER, p, sheetIndex)
      setCellText(s, ri, COL_W_TESTER, t, sheetIndex)
      setCellText(s, ri, COL_X_SUPERVISOR, sp, sheetIndex)
      filled += 1
    }

    if (typeof s?.reRender === 'function') s.reRender()
    else if (typeof s?.render === 'function') s.render()

    if (filled === 0) {
      ElMessage.warning('未找到可填充的有效数据行')
      return
    }
    ElMessage.success(`测试人员填充完成（${filled}行）`)
  }

  const smartFillTestItemDescMethod = async ({ useSelectionCache = false } = {}) => {
    const s = spreadsheetRef?.value
    if (!s) {
      ElMessage.error('表格未初始化')
      return
    }

    if (!useSelectionCache && !hasCachedSelection()) {
      ElMessage.warning('请先选中一行或多行，再执行此操作')
      return
    }

    const range = resolveSelectedRange(s, useSelectionCache)
    if (!range || !Number.isFinite(range.sri) || !Number.isFinite(range.eri) || range.eri < range.sri) {
      ElMessage.warning('请先选择一行或多行才能执行此操作')
      return
    }

    const activeSheetIndex = getActiveSheetIndex(s)
    const requirementSheetIndex = (() => {
      const list = Array.isArray(sheetListRef?.value) ? sheetListRef.value : []
      const byName = list.findIndex((it) => String(it?.name || '').includes('需求'))
      if (byName >= 0) return byName
      return list.findIndex((_, idx) => idx !== activeSheetIndex && String(list?.[idx]?.name || '').includes('需求'))
    })()
    const caseSheetIndex = (() => {
      const list = Array.isArray(sheetListRef?.value) ? sheetListRef.value : []
      const byName = list.findIndex((it) => String(it?.name || '').includes('用例'))
      if (byName >= 0) return byName
      return list.findIndex((_, idx) => idx !== requirementSheetIndex && idx !== activeSheetIndex)
    })()

    const sourceSheetIndex = requirementSheetIndex >= 0 ? requirementSheetIndex : activeSheetIndex
    const targetSheetIndex = requirementSheetIndex >= 0 ? requirementSheetIndex : activeSheetIndex
    const selectedRows = []
    for (let ri = range.sri; ri <= range.eri; ri += 1) {
      const testItemName = String(getCellText(s, ri, COL_O_TEST_ITEM_NAME, sourceSheetIndex) || '').trim()
      if (!testItemName) continue
      selectedRows.push({
        row_index: ri,
        test_item_name: testItemName,
      })
    }

    if (selectedRows.length === 0) {
      ElMessage.warning('选中范围内未找到可生成的测试项名称（O列为空）')
      return
    }

    const groups = new Map()
    for (const row of selectedRows) {
      if (!groups.has(row.test_item_name)) groups.set(row.test_item_name, [])
      groups.get(row.test_item_name).push(row)
    }

    const taskId = currentTaskIdRef?.value
    if (!taskId) {
      ElMessage.warning('请先导入Excel并创建任务，再执行智能填充')
      return
    }

    const progress = await createProgressOverlay({ title: '智能生成测试项描述和测试方法', subtitle: '正在按测试项名称匹配测试用例并回填需求分析表' })
    try {
      const groupEntries = Array.from(groups.entries())
      for (let gi = 0; gi < groupEntries.length; gi += 1) {
        const [testItemName, rows] = groupEntries[gi]
        const caseRows = []
        const upper = Number.isFinite(sheetListRef?.value?.[caseSheetIndex]?.rows?.len) ? sheetListRef.value[caseSheetIndex].rows.len : 1000
        for (let ri = 1; ri < upper; ri += 1) {
          const gName = String(getCellText(s, ri, COL_G_CASE_TEST_ITEM_NAME, caseSheetIndex) || '').trim()
          if (gName !== testItemName) continue
          // 只取第一轮测试用例（E列 测试轮次），忽略第二轮、第三轮
          const roundVal = String(getCellText(s, ri, COL_E_TEST_ROUND, caseSheetIndex) || '').trim()
          if (!isFirstRound(roundVal)) continue
          caseRows.push({
            row_index: ri,
            test_item_name: testItemName,
            case_name: String(getCellText(s, ri, COL_I_CASE_NAME, caseSheetIndex) || '').trim(),
            test_desc: String(getCellText(s, ri, COL_L_TEST_DESC, caseSheetIndex) || '').trim(),
            input_condition: String(getCellText(s, ri, COL_P_INPUT_CONDITION, caseSheetIndex) || '').trim(),
            expected_result: String(getCellText(s, ri, COL_Q_EXPECTED_RESULT, caseSheetIndex) || '').trim(),
          })
        }

        if (caseRows.length === 0) {
          progress.update({
            current: gi + 1,
            total: groupEntries.length,
            status: `已匹配测试项「${testItemName}」，但测试用例单中未找到同名用例`,
          })
          await nextTick()
          continue
        }

        progress.update({
          current: gi + 1,
          total: groupEntries.length,
          status: `已匹配测试项「${testItemName}」，正在生成测试项描述和测试方法...`,
        })
        await nextTick()

        const resp = await request.post('/test-tools/test-case-assistant/case-fill/test-item-desc-method', {
          task_id: taskId,
          test_item_name: testItemName,
          rows: caseRows,
        })
        const results = Array.isArray(resp?.results) ? resp.results : []
        const errors = Array.isArray(resp?.errors) ? resp.errors : []
        if (results.length === 0) {
          const errMsg = String(errors?.[0]?.error || '')
          if (errMsg) ElMessage.warning(`测试项「${testItemName}」未生成结果：${errMsg}`)
          continue
        }

        for (const target of rows) {
          const matched = results[0]
          const desc = String(matched?.test_item_desc || '').trim()
          const method = String(matched?.test_method || '').trim()
          if (!desc || !method) {
            ElMessage.warning(`测试项「${testItemName}」返回结果不完整，已跳过写入`)
            continue
          }
          setCellText(s, target.row_index, COL_T_TEST_ITEM_DESC, desc, targetSheetIndex)
          setCellText(s, target.row_index, COL_U_TEST_METHOD, method, targetSheetIndex)
        }
      }

      ensureRender(s)
      ElMessage.success('测试项描述和测试方法填充完成')
    } catch (e) {
      ElMessage.error(e?.message || '智能填充失败')
    } finally {
      progress.close()
    }
  }

  const smartFillTestTime = async () => {
    const s = spreadsheetRef?.value
    if (!s) {
      ElMessage.error('表格未初始化')
      return
    }

    const sheetIndex = getActiveSheetIndex(s)

    const startDateStr = ref('')
    const durationDaysStr = ref('')

    const DialogForm = defineComponent({
      name: 'SmartFillTestTimeDialogForm',
      setup() {
        return () => h('div', { style: 'display:flex;flex-direction:column;gap:10px;' }, [
          h('div', { style: 'display:flex;align-items:center;gap:10px;' }, [
            h('div', { style: 'width:150px;flex:0 0 auto;' }, '用例设计开始时间'),
            h(ElInput, {
              modelValue: startDateStr.value,
              'onUpdate:modelValue': (v) => { startDateStr.value = v },
              placeholder: '例如：2026/01/05',
              autofocus: true,
            }),
          ]),
          h('div', { style: 'display:flex;align-items:center;gap:10px;' }, [
            h('div', { style: 'width:150px;flex:0 0 auto;' }, '动态测试时长（天）'),
            h(ElInput, {
              modelValue: durationDaysStr.value,
              'onUpdate:modelValue': (v) => { durationDaysStr.value = v },
              placeholder: '例如：4',
            }),
          ]),
        ])
      },
    })

    try {
      await ElMessageBox({
        title: '测试时间智能填充',
        message: h(DialogForm),
        showCancelButton: true,
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        closeOnClickModal: false,
        closeOnPressEscape: false,
        beforeClose: (action, _instance, done) => {
          if (action === 'confirm') {
            const sd = parseStartDate(startDateStr.value)
            if (!sd) {
              ElMessage.warning('开始时间格式错误，请按 2026/01/05 输入')
              return
            }
            const n = Number(String(durationDaysStr.value || '').trim())
            if (!Number.isFinite(n) || n <= 0) {
              ElMessage.warning('动态测试时长（天）必须是大于0的数字')
              return
            }
          }
          done()
        },
      })
    } catch (_) {
      return
    }

    const start = parseStartDate(startDateStr.value)
    const duration = Math.floor(Number(String(durationDaysStr.value || '').trim()))
    if (!start || !Number.isFinite(duration) || duration <= 0) return

    const designDays = Math.max(1, Math.ceil(duration / 2))
    const testDays = Math.max(0, duration - designDays)

    const designDates = buildDateList(start, designDays)
    const testStart = addDays(start, designDays)
    const testDates = buildDateList(testStart, Math.max(1, testDays || 1))

    const maxRows = s?.sheet?.data?.rows?.len
    const upper = Number.isFinite(maxRows) && maxRows > 0 ? maxRows : 1000

    const validRows = []
    let started = false
    for (let ri = 1; ri < upper; ri += 1) {
      const has = rowHasAnyData(s, ri, sheetIndex)
      if (!has) {
        if (started) break
        continue
      }
      started = true
      validRows.push(ri)
    }

    if (validRows.length === 0) {
      ElMessage.warning('未找到可填充的有效数据行')
      return
    }

    for (let i = 0; i < validRows.length; i += 1) {
      const ri = validRows[i]
      const dDate = pickDateByIndex(designDates, i, validRows.length)
      const tDate = pickDateByIndex(testDates, i, validRows.length)
      const dStr = dDate ? formatDateSlash(dDate) : ''
      const tStr = tDate ? formatDateSlash(tDate) : ''
      setCellText(s, ri, COL_U_DESIGN_TIME, dStr, sheetIndex)
      setCellText(s, ri, COL_V_PROOF_TIME, dStr, sheetIndex)
      setCellText(s, ri, COL_Y_TEST_TIME, tStr, sheetIndex)
      setCellText(s, ri, COL_AC_EXEC_YYYY_MM, tDate ? formatYYYYMM(tDate) : '', sheetIndex)
    }

    if (typeof s?.reRender === 'function') s.reRender()
    else if (typeof s?.render === 'function') s.render()

    ElMessage.success(`测试时间填充完成（${validRows.length}行）`)
  }

  return {
    smartFillCaseId,
    smartFillCaseName,
    smartFillTestDesc,
    smartFillTestItemDescMethod,
    smartFillTester,
    smartFillTestTime,
  }
}
