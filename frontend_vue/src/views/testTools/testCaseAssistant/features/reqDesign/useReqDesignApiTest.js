import { ElLoading, ElMessage } from 'element-plus'
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

const callReqDesignApiTestGenerate = async ({ rows }) => {
  const resp = await request.post('/test-tools/test-case-assistant/req-design/api-test/generate', {
    rows,
  })

  return {
    results: Array.isArray(resp?.results) ? resp.results : [],
    errors: Array.isArray(resp?.errors) ? resp.errors : [],
  }
}

export const useReqDesignApiTest = (spreadsheetRef) => {
  const reqDesignApiTest = async () => {
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

    const rows = []
    for (let ri = sri; ri <= eri; ri += 1) {
      const testItemName = getCellText(s, ri, COL_O_TEST_ITEM_NAME, sheetIndex)
      const templateTestItemDesc = getCellText(s, ri, COL_T_TEST_ITEM_DESC, sheetIndex)
      const templateTestMethod = getCellText(s, ri, COL_U_TEST_METHOD, sheetIndex)

      if (!String(testItemName || '').trim()) continue

      rows.push({
        row_index: ri,
        test_item_name: String(testItemName || ''),
        template_test_item_desc: String(templateTestItemDesc || ''),
        template_test_method: String(templateTestMethod || ''),
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
        text: `需求设计-接口测试：AI处理中（0/${rows.length}）`,
        background: 'rgba(0, 0, 0, 0.2)',
      })

      const resp = await callReqDesignApiTestGenerate({ rows })

      const results = resp.results
      const errors = resp.errors

      results.forEach((it, idx) => {
        if (loadingInstance) loadingInstance.setText(`需求设计-接口测试：回填中（${idx + 1}/${results.length}）`)
        const ri = Number(it.row_index)
        if (!Number.isFinite(ri)) return
        s.cellText(ri, COL_T_TEST_ITEM_DESC, it.test_item_desc ?? '', sheetIndex)
        s.cellText(ri, COL_U_TEST_METHOD, it.test_method ?? '', sheetIndex)
      })

      s.reRender()

      if (errors.length) {
        ElMessage.warning(`需求设计-接口测试完成：成功 ${results.length} 条，失败 ${errors.length} 条（可查看后端日志）`)
      } else {
        ElMessage.success(`需求设计-接口测试完成：成功 ${results.length} 条`)
      }
    } catch (e) {
      console.error(e)
      ElMessage.error('需求设计-接口测试失败：' + (e?.message || '未知错误'))
    } finally {
      if (loadingInstance) loadingInstance.close()
    }
  }

  return {
    reqDesignApiTest,
  }
}
