<template>
  <div class="excel-assistant" :class="{ 'agent-open': agentVisible }">
    <div class="toolbar">
      <el-upload
        class="upload"
        :auto-upload="false"
        :show-file-list="false"
        accept=".xlsx,.xls"
        :on-change="handleFileChange"
      >
        <el-button type="primary">导入 .xlsx</el-button>
      </el-upload>

      <el-button type="success" @click="exportXlsx" :disabled="!spreadsheetReady">
        导出 .xlsx
      </el-button>

      <el-tooltip content="根据测试用例内容，反向生成测试项分析、测试方法及用例描述" placement="bottom">
        <el-button class="btn-purple" @click="reverseGenerateDialogRef?.open()">
          反向生成
        </el-button>
      </el-tooltip>

      <el-tooltip content="上传问题报告单，根据T列研制单位意见生成AA列问题确认意见/归零说明" placement="bottom">
        <el-button class="btn-amber" @click="issueReportOpinionDialogRef?.open()">
          问题报告单归零
        </el-button>
      </el-tooltip>

      <el-tooltip content="上传测试用例单，按测试项为测试结论为“不通过”的用例生成问题单" placement="bottom">
        <el-button class="btn-orange" @click="dynamicIssueReportDialogRef?.open()">
          生成问题单
        </el-button>
      </el-tooltip>

      <el-button class="btn-teal" @click="assetReuseExportVisible = true">
        组织资产复用
      </el-button>

      <el-upload
        class="upload"
        :auto-upload="false"
        :show-file-list="false"
        accept=".zip"
        :disabled="!currentTaskId"
        :on-change="handleRepoZipChange"
      >
        <el-button type="primary" :disabled="!currentTaskId">上传代码库</el-button>
      </el-upload>

      <el-dropdown trigger="click" :disabled="!spreadsheetReady">
        <el-button :disabled="!spreadsheetReady">草稿 ▾</el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="saveDraft">保存草稿</el-dropdown-item>
            <el-dropdown-item @click="loadDraft">加载草稿</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <el-alert
        v-if="caseIfReuseMode"
        class="case-if-reuse-tip"
        type="warning"
        :closable="false"
        show-icon
        :title="caseIfReuseTipTitle"
      />

      <el-button
        v-if="caseIfReuseMode"
        type="primary"
        @click="finishCaseIfReuseSelection"
        :disabled="caseIfReuseSelectedRows.length === 0"
      >
        选择完毕
      </el-button>
      <el-button v-if="caseIfReuseMode" @click="cancelCaseIfReuseSelection">取消选择</el-button>

      <div class="filename-inline" :class="{ disabled: !spreadsheetReady }">
        <el-input
          v-model="exportFilename"
          class="filename-input"
          placeholder="导出文件名"
          :disabled="!spreadsheetReady"
        />
      </div>
    </div>

    <!-- 左右分栏主体 -->
    <div class="main-body">
      <!-- 左侧：表格区 -->
      <div class="spreadsheet-area">
        <div class="sheet-wrapper">
          <div ref="sheetContainer" class="sheet-container" :style="sheetScaleStyle"></div>
        </div>

        <div class="zoom-bar">
          <button class="zoom-btn" @click="zoomOut" title="缩小">－</button>
          <input
            class="zoom-slider"
            type="range"
            min="50"
            max="200"
            step="10"
            :value="zoomPercent"
            @input="onZoomSlider"
          />
          <button class="zoom-btn" @click="zoomIn" title="放大">＋</button>
          <span class="zoom-label" @click="resetZoom" title="点击重置为 100%">{{ zoomPercent }}%</span>

          <!-- AI 面板切换按钮 -->
          <button
            class="ai-toggle-btn"
            :class="{ active: agentVisible }"
            @click="agentVisible = !agentVisible"
            title="AI 助手"
          >✦ AI 助手</button>
        </div>
      </div>

      <!-- 右侧：AI 面板 -->
      <div v-if="agentVisible" class="agent-area" :style="{ width: agentWidth + 'px' }">
        <div class="agent-resize-handle" @mousedown="startResize"></div>
        <AgentPanel
          :spreadsheet="spreadsheet"
          :sheetList="sheetList"
          :taskId="currentTaskId"
          :applyOp="applyOp"
          :applyOps="applyOps"
          :getSnapshot="getSnapshot"
          @collapse="agentVisible = false"
        />
      </div>
    </div>

    <SpreadsheetContextMenu
      :visible="ctxMenuState.visible"
      :x="ctxMenuState.x"
      :y="ctxMenuState.y"
      :scope="ctxMenuScope"
      @action="onCtxAction"
    />

    <AssetReuseExportDialog v-model:visible="assetReuseExportVisible" :task-id="currentTaskId" />
    <ReverseGenerateDialog ref="reverseGenerateDialogRef" />
    <IssueReportOpinionDialog ref="issueReportOpinionDialogRef" />
    <DynamicIssueReportDialog ref="dynamicIssueReportDialogRef" />

    <AssetReuseSelectedDialog
      v-model:visible="assetReuseSelectedVisible"
      :task-id="currentTaskId"
      @confirm="onAssetReuseSelectedConfirm"
    />

    <AssetReuseSelectedDialog
      v-model:visible="assetReuseSelectedCaseVisible"
      :task-id="currentTaskId"
      @confirm="onAssetReuseSelectedCaseConfirm"
    />
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox, ElLoading } from 'element-plus'
import Spreadsheet from './x-spreadsheet-master/src/index.js'

import request from '@/api/request'

import SpreadsheetContextMenu from './components/SpreadsheetContextMenu.vue'
import AssetReuseExportDialog from './assetReuseExport/AssetReuseExportDialog.vue'
import AssetReuseSelectedDialog from './assetReuseSelected/AssetReuseSelectedDialog.vue'
import ReverseGenerateDialog from './components/ReverseGenerateDialog.vue'
import IssueReportOpinionDialog from './components/IssueReportOpinionDialog.vue'
import DynamicIssueReportDialog from './components/DynamicIssueReportDialog.vue'
import AgentPanel from './agent/AgentPanel.vue'
import { useSpreadsheetContextMenu } from './composables/useSpreadsheetContextMenu'
import { useSpreadsheetBridge } from './agent/composables/useSpreadsheetBridge.js'

import { useSpreadsheetIO } from './composables/useSpreadsheetIO'
import { useSpreadsheetDraft } from './composables/useSpreadsheetDraft'

import { useReqDesignInit } from './features/reqDesign/useReqDesignInit'
import { useReqDesignCommon } from './features/reqDesign/useReqDesignCommon'
import { useReqDesignSelfCheck } from './features/reqDesign/useReqDesignSelfCheck.js'
import { useReqDesignApiTest } from './features/reqDesign/useReqDesignApiTest'
import { useCaseDesignInit } from './features/caseDesign/useCaseDesignInit'
import { useCaseDesignCommon } from './features/caseDesign/useCaseDesignCommon'
import { useCaseDesignSelfCheck } from './features/caseDesign/useCaseDesignSelfCheck'
import { useCaseDesignApiException } from './features/caseDesign/useCaseDesignApiException'
import { useCaseDesignApiPeriod } from './features/caseDesign/useCaseDesignApiPeriod'
import { useAssetReuseSelected } from './features/assetReuse/useAssetReuseSelected'
import { useCaseDesignIfReuseOther } from './features/caseDesign/useCaseDesignIfReuseOther'
import { useCaseSheetSmartFill } from './features/caseFill/useCaseSheetSmartFill'
import { useTestItemExtend } from './features/reqExpand/useTestItemExtend'
import { useTestCaseExtend } from './features/caseExpand/useTestCaseExtend'

import {
  createEmptySheetData,
} from './utils/xlsxAdapter'

const sheetContainer = ref(null)
const spreadsheet = ref(null)
const spreadsheetReady = ref(false)
const exportFilename = ref('test_case_assistant.xlsx')
const sheetList = ref([])

const ctxMenuScope = ref('req')
const ctxMenuSelection = ref(null)

const assetReuseExportVisible = ref(false)
const assetReuseSelectedVisible = ref(false)
const reverseGenerateDialogRef = ref(null)
const issueReportOpinionDialogRef = ref(null)
const dynamicIssueReportDialogRef = ref(null)

const assetReuseSelectedCaseVisible = ref(false)

const currentTaskId = ref('')

const {
  mode: caseIfReuseMode,
  tipTitle: caseIfReuseTipTitle,
  selectedRows: caseIfReuseSelectedRows,
  enterFromCtx: enterCaseIfReuseFromCtx,
  finish: finishCaseIfReuseSelection,
  cancel: cancelCaseIfReuseSelection,
  onCellSelected: onCaseIfReuseCellSelected,
  onKeyChange,
} = useCaseDesignIfReuseOther(spreadsheet)

const DRAFT_KEY = 'default'

const { reqDesignInit } = useReqDesignInit(spreadsheet)
const { reqDesignCommon } = useReqDesignCommon(spreadsheet)
const { reqDesignSelfCheck } = useReqDesignSelfCheck(spreadsheet)
const { reqDesignApiTest } = useReqDesignApiTest(spreadsheet)
const { caseDesignInit } = useCaseDesignInit(spreadsheet, currentTaskId)
const { caseDesignCommon } = useCaseDesignCommon(spreadsheet)
const { caseDesignSelfCheckFission, caseDesignSelfCheckWrite } = useCaseDesignSelfCheck(spreadsheet, currentTaskId)
const { caseDesignApiException } = useCaseDesignApiException(spreadsheet, currentTaskId)
const { caseDesignApiPeriod } = useCaseDesignApiPeriod(spreadsheet, currentTaskId)
const { onAssetReuseSelectedConfirm, onAssetReuseSelectedCaseConfirm } = useAssetReuseSelected(spreadsheet, currentTaskId)
const { extendPerfTestItem, extendBoundaryTestItem } = useTestItemExtend(spreadsheet)
const { extendPerfTestCase, extendBoundaryTestCase } = useTestCaseExtend(spreadsheet)
const { smartFillCaseId, smartFillCaseName, smartFillTestDesc, smartFillTestItemDescMethod, smartFillTester, smartFillTestTime } = useCaseSheetSmartFill(spreadsheet, currentTaskId, ctxMenuSelection, sheetList)

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

const inferCtxMenuScope = () => {
  const s = spreadsheet?.value
  if (!s) return 'case'
  const raw = s.getData?.()
  const sheets = Array.isArray(raw) ? raw : [raw]
  const idx = getActiveSheetIndex(s)
  const name = String(sheets?.[idx]?.name || '')

  if (name.includes('需求')) return 'req'
  if (name.includes('用例')) return 'case'

  // 兜底：默认第一个 sheet 当作需求，其余当作用例
  if (idx === 0) return 'req'
  return 'case'
}

const cacheContextMenuSelection = () => {
  const s = spreadsheet?.value
  const range = normalizeRange(getSelectedRange(s))
  ctxMenuSelection.value = range
  return range
}

const restoreContextMenuSelectionHighlight = () => {
  const s = spreadsheet?.value
  const cached = normalizeRange(ctxMenuSelection.value)
  if (!s || !cached) return
  try {
    const selector = s?.sheet?.data?.selector
    if (selector) {
      selector.range = { ...cached }
      selector.sri = cached.sri
      selector.sci = cached.sci
      selector.eri = cached.eri
      selector.eci = cached.eci
    }
    if (typeof s?.reRender === 'function') s.reRender()
    else if (typeof s?.render === 'function') s.render()
  } catch (_) {
    // ignore
  }
}

const getContextMenuSelectionRange = (s) => {
  const cached = normalizeRange(ctxMenuSelection.value)
  if (cached) return cached
  return normalizeRange(getSelectedRange(s))
}

const onCtxAction = async (key) => {
  if (key === 'sheet_delete_row') {
    const s = spreadsheet?.value
    if (!s) {
      ElMessage.error('表格未初始化')
      return
    }
    const range = getContextMenuSelectionRange(s)
    if (!range || !Number.isFinite(range.sri) || !Number.isFinite(range.eri) || range.eri < range.sri) {
      ElMessage.warning('请先选择要删除的行范围')
      return
    }
    try {
      s.sheet?.data?.delete?.('row')
      if (typeof s?.reRender === 'function') s.reRender()
      else if (typeof s?.render === 'function') s.render()
      ElMessage.success('删除行完成')
    } catch (e) {
      ElMessage.error(e?.message || '删除行失败')
    }
    return
  }
  if (key === 'case_fill_case_id') {
    await smartFillCaseId()
    return
  }
  if (key === 'case_fill_case_name') {
    await smartFillCaseName({ useSelectionCache: true })
    return
  }
  if (key === 'case_fill_test_desc') {
    await smartFillTestDesc({ useSelectionCache: true })
    return
  }
  if (key === 'case_fill_test_item_desc_method') {
    await smartFillTestItemDescMethod({ useSelectionCache: true })
    return
  }
  if (key === 'case_fill_tester') {
    await smartFillTester()
    return
  }
  if (key === 'case_fill_test_time') {
    await smartFillTestTime()
    return
  }
  if (key === 'case_design_if_reuse_other') {
    enterCaseIfReuseFromCtx()
    return
  }
  if (key === 'asset_reuse_selected') {
    const s = spreadsheet?.value
    if (!s) {
      ElMessage.error('表格未初始化')
      return
    }
    const range = getContextMenuSelectionRange(s)
    if (!range) {
      ElMessage.warning('请先选择要匹配的行范围')
      return
    }
    const { sri, eri } = range
    if (!Number.isFinite(sri) || !Number.isFinite(eri) || eri < sri) {
      ElMessage.warning('当前选区无效')
      return
    }

    const tid = currentTaskId.value
    if (tid) {
      try {
        const taskResp = await request.get(`/test-tools/test-case-assistant/tasks/${tid}`)
        const pt = taskResp?.product_type
        const st = taskResp?.software_type
        if (pt && st) {
          await onAssetReuseSelectedConfirm({ selectedType: pt, selectedSoftwareType: st })
          return
        }
      } catch (_) {
        // ignore
      }
    }

    assetReuseSelectedVisible.value = true
    return
  }
  if (key === 'asset_reuse_selected_case') {
    const s = spreadsheet?.value
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

    const tid = currentTaskId.value
    if (tid) {
      try {
        const taskResp = await request.get(`/test-tools/test-case-assistant/tasks/${tid}`)
        const pt = taskResp?.product_type
        const st = taskResp?.software_type
        if (pt && st) {
          await onAssetReuseSelectedCaseConfirm({ selectedType: pt, selectedSoftwareType: st })
          return
        }
      } catch (_) {
        // ignore
      }
    }

    assetReuseSelectedCaseVisible.value = true
    return
  }
  if (key === 'req_design_init') {
    reqDesignInit()
    return
  }
  if (key === 'req_design_common') {
    reqDesignCommon()
    return
  }
  if (key === 'req_design_selfcheck') {
    reqDesignSelfCheck()
    return
  }
  if (key === 'req_design_api_test') {
    reqDesignApiTest()
    return
  }
  if (key === 'req_expand_perf') {
    extendPerfTestItem()
    return
  }
  if (key === 'req_expand_boundary') {
    extendBoundaryTestItem()
    return
  }
  if (key === 'case_design_if_exception_test') {
    await caseDesignApiException()
    return
  }
  if (key === 'case_design_if_period') {
    await caseDesignApiPeriod()
    return
  }
  if (key === 'case_design_init') {
    caseDesignInit()
    return
  }
  if (key === 'case_design_common') {
    caseDesignCommon()
    return
  }
  if (key === 'case_design_selfcheck_fission') {
    caseDesignSelfCheckFission()
    return
  }
  if (key === 'case_design_selfcheck_write') {
    caseDesignSelfCheckWrite()
    return
  }
  if (key === 'case_expand_perf') {
    extendPerfTestCase()
    return
  }
  if (key === 'case_expand_boundary') {
    extendBoundaryTestCase()
    return
  }
  ElMessage.info(`指令触发（占位）：${key}`)
}

const {
  state: ctxMenuState,
  bind: bindCtxMenu,
  unbind: unbindCtxMenu,
} = useSpreadsheetContextMenu(sheetContainer, onCtxAction, () => {
  cacheContextMenuSelection()
  ctxMenuScope.value = inferCtxMenuScope()
  setTimeout(() => {
    restoreContextMenuSelectionHighlight()
  }, 0)
})

const handleRepoZipChange = async (file) => {
  try {
    if (!currentTaskId.value) {
      ElMessage.warning('请先导入Excel以创建任务，再上传代码库')
      return
    }
    if (!file?.raw) {
      ElMessage.error('请选择有效的zip文件')
      return
    }

    const fd = new FormData()
    fd.append('file', file.raw)

    const resp = await request.post(
      `/test-tools/test-case-assistant/tasks/${currentTaskId.value}/repo/upload`,
      fd,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )

    if (resp?.success) {
      ElMessage.success('代码库上传并解压成功')
    } else {
      ElMessage.warning('代码库上传失败')
    }
  } catch (e) {
    console.error(e)
    ElMessage.error('代码库上传失败：' + (e?.message || '未知错误'))
  }
}

const initSpreadsheet = (initialSheets = null, initialActiveIndex = 0) => {
  if (!sheetContainer.value) return

  // x-data-spreadsheet 会往 container 里 append DOM；如果重复初始化但不清理，会出现上下两个表格
  sheetContainer.value.innerHTML = ''

  const s = new Spreadsheet(sheetContainer.value, {
    showToolbar: true,
    showGrid: true,
    showContextmenu: false,
    showBottomBar: true,
    view: {
      height: () => window.innerHeight - 140,
      width: () => window.innerWidth - 80,
    },
    row: {
      len: 10000,  // 增加默认行数到10000
      height: 25,
    },
    col: {
      len: 26,
      width: 100,
      indexWidth: 60,
      minWidth: 60,
    },
  })

  const sheets = Array.isArray(initialSheets) && initialSheets.length ? initialSheets : [createEmptySheetData('Sheet1')]
  sheetList.value = sheets
  s.loadData(sheets)
  spreadsheet.value = s
  spreadsheetReady.value = true

  // 选择模式：Ctrl+Shift 点击行，加入/移出来源集合并高亮
  s.on('cell-selected', (_cell, ri, _ci) => {
    onCaseIfReuseCellSelected(ri)
  })

  // loadData 默认会显示第 0 个 sheet，这里尽量切回调用方期望的 sheet
  if (initialActiveIndex && initialActiveIndex > 0) {
    setTimeout(() => {
      const bb = spreadsheet.value?.bottombar
      if (!bb || !Array.isArray(bb.items) || typeof bb.clickSwap2 !== 'function') return
      const it = bb.items[initialActiveIndex]
      if (it) bb.clickSwap2(it)
    }, 0)
  }
}

const destroySpreadsheet = () => {
  try {
    if (spreadsheet.value && typeof spreadsheet.value.destroy === 'function') {
      spreadsheet.value.destroy()
    }
  } catch (_) {
    // ignore
  } finally {
    spreadsheet.value = null
    spreadsheetReady.value = false

    if (sheetContainer.value) {
      sheetContainer.value.innerHTML = ''
    }
  }
}

function reloadSpreadsheetWithData(data, activeIndex = 0) {
  destroySpreadsheet()
  initSpreadsheet(data, activeIndex)
  setTimeout(initSheetTabScroll, 0)
}

const { handleFileChange, exportXlsx } = useSpreadsheetIO({
  spreadsheet,
  spreadsheetReady,
  exportFilename,
  sheetList,
  reloadSpreadsheetWithData,
  onAfterImport: async ({ file }) => {
    try {
      const filename = file?.raw?.name || ''
      const name = filename ? `用例设计-${filename}` : '用例设计-未命名任务'
      const resp = await request.post('/test-tools/test-case-assistant/tasks', {
        name,
        excel_filename: filename || null,
      })
      const taskId = resp?.task_id
      if (taskId) {
        currentTaskId.value = taskId
        ElMessage.success(`已创建任务：${taskId}`)
      } else {
        ElMessage.warning('已导入Excel，但创建任务未返回task_id')
      }
    } catch (e) {
      console.error(e)
      ElMessage.warning('已导入Excel，但创建任务失败：' + (e?.message || '未知错误'))
    } finally {
      try {
        await saveDraft({ silent: true })
      } catch (_) {
        // ignore
      }
    }
  },
})

const { saveDraft, loadDraft } = useSpreadsheetDraft({
  spreadsheet,
  sheetList,
  reloadSpreadsheetWithData,
  draftKey: DRAFT_KEY,
})


const zoomPercent = ref(100)
const ZOOM_STEP = 10
const ZOOM_MIN = 50
const ZOOM_MAX = 200

const agentVisible = ref(false)
const agentWidth = ref(360)
const { applyOp, applyOps, getSnapshot } = useSpreadsheetBridge(spreadsheet, sheetList)

const startResize = (e) => {
  e.preventDefault()
  const startX = e.clientX
  const startW = agentWidth.value
  const onMove = (ev) => {
    const delta = startX - ev.clientX
    agentWidth.value = Math.min(800, Math.max(240, startW + delta))
  }
  const onUp = () => {
    window.removeEventListener('mousemove', onMove)
    window.removeEventListener('mouseup', onUp)
  }
  window.addEventListener('mousemove', onMove)
  window.addEventListener('mouseup', onUp)
}

const sheetScaleStyle = computed(() => ({}))

const applyZoom = () => {
  const s = zoomPercent.value / 100
  if (!spreadsheet.value) return
  // 对所有 sheet 的 rows/cols 设置 zoomFactor，触发重绘
  const datas = spreadsheet.value.datas
  if (datas) {
    datas.forEach((data) => {
      data.rows.zoomFactor = s
      data.cols.zoomFactor = s
    })
  }
  spreadsheet.value.reRender()
}

const zoomIn = () => {
  zoomPercent.value = Math.min(ZOOM_MAX, zoomPercent.value + ZOOM_STEP)
  nextTick(applyZoom)
}
const zoomOut = () => {
  zoomPercent.value = Math.max(ZOOM_MIN, zoomPercent.value - ZOOM_STEP)
  nextTick(applyZoom)
}
const resetZoom = () => {
  zoomPercent.value = 100
  nextTick(applyZoom)
}
const onZoomSlider = (e) => {
  zoomPercent.value = Number(e.target.value)
  nextTick(applyZoom)
}

let sheetTabScrollCleanup = null

const initSheetTabScroll = () => {
  if (sheetTabScrollCleanup) sheetTabScrollCleanup()

  const bottombar = sheetContainer.value?.querySelector('.x-spreadsheet-bottombar')
  if (!bottombar) return

  const menuEl = bottombar.querySelector('.x-spreadsheet-menu')
  if (!menuEl) return

  const btnStyle = `
    position: absolute; top: 50%; transform: translateY(-50%);
    width: 28px; height: 28px; border: 1px solid #d1d5db; border-radius: 4px;
    background: #f5f6f7; color: #555; font-size: 18px; line-height: 1;
    cursor: pointer; display: flex; align-items: center; justify-content: center;
    padding: 0; z-index: 10;
  `
  const btnLeft = document.createElement('button')
  btnLeft.style.cssText = btnStyle + 'right: 32px;'
  btnLeft.innerHTML = '&#8249;'
  btnLeft.title = '向左滚动'

  const btnRight = document.createElement('button')
  btnRight.style.cssText = btnStyle + 'right: 4px;'
  btnRight.innerHTML = '&#8250;'
  btnRight.title = '向右滚动'

  bottombar.appendChild(btnLeft)
  bottombar.appendChild(btnRight)

  const SCROLL_STEP = 120
  const onLeft = () => { menuEl.scrollLeft -= SCROLL_STEP }
  const onRight = () => { menuEl.scrollLeft += SCROLL_STEP }

  btnLeft.addEventListener('click', onLeft)
  btnRight.addEventListener('click', onRight)

  sheetTabScrollCleanup = () => {
    btnLeft.removeEventListener('click', onLeft)
    btnRight.removeEventListener('click', onRight)
    btnLeft.remove()
    btnRight.remove()
    sheetTabScrollCleanup = null
  }
}

onMounted(() => {
  initSpreadsheet()
  setTimeout(initSheetTabScroll, 0)

  window.addEventListener('keydown', onKeyChange)
  window.addEventListener('keyup', onKeyChange)

  bindCtxMenu()
})

onBeforeUnmount(() => {
  destroySpreadsheet()
  if (sheetTabScrollCleanup) sheetTabScrollCleanup()

  window.removeEventListener('keydown', onKeyChange)
  window.removeEventListener('keyup', onKeyChange)

  unbindCtxMenu()
})
</script>

<style scoped>
.excel-assistant {
  height: 100%;
  padding: 16px;
  display: flex;
  flex-direction: column;
}

.main-body {
  flex: 1;
  display: flex;
  min-height: 0;
  gap: 0;
}

.spreadsheet-area {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.agent-area {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  min-height: 0;
  position: relative;
  border-left: 1px solid #e5e7eb;
  margin-left: 14px;
}

.agent-resize-handle {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 5px;
  cursor: col-resize;
  z-index: 10;
  background: transparent;
  transition: background 0.15s;
}
.agent-resize-handle:hover,
.agent-resize-handle:active {
  background: #93c5fd;
}

.ai-toggle-btn {
  margin-left: auto;
  padding: 3px 12px;
  border: 1px solid #c7d2fe;
  border-radius: 4px;
  background: #f5f3ff;
  color: #6d28d9;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}
.ai-toggle-btn:hover { background: #ede9fe; }
.ai-toggle-btn.active { background: #6d28d9; color: #fff; border-color: #6d28d9; }

.toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 12px;
}

.btn-purple.el-button {
  background-color: #7c3aed;
  border-color: #7c3aed;
  color: #fff;
}
.btn-purple.el-button:hover {
  background-color: #6d28d9;
  border-color: #6d28d9;
}
.btn-purple.el-button:disabled {
  background-color: #c4b5fd;
  border-color: #c4b5fd;
}

.btn-amber.el-button {
  background-color: #d97706;
  border-color: #d97706;
  color: #fff;
}
.btn-amber.el-button:hover {
  background-color: #b45309;
  border-color: #b45309;
}
.btn-amber.el-button:disabled {
  background-color: #fcd34d;
  border-color: #fcd34d;
  color: #fff;
}

.btn-orange.el-button {
  background-color: #ea580c;
  border-color: #ea580c;
  color: #fff;
}
.btn-orange.el-button:hover {
  background-color: #c2410c;
  border-color: #c2410c;
}
.btn-orange.el-button:disabled {
  background-color: #fdba74;
  border-color: #fdba74;
  color: #fff;
}

.btn-teal.el-button {
  background-color: #0d9488;
  border-color: #0d9488;
  color: #fff;
}
.btn-teal.el-button:hover {
  background-color: #0f766e;
  border-color: #0f766e;
}
.btn-teal.el-button:disabled {
  background-color: #99f6e4;
  border-color: #99f6e4;
  color: #fff;
}

.case-if-reuse-tip {
  flex: 1;
  min-width: 420px;
  font-weight: 700;
}

:deep(.case-if-reuse-tip .el-alert) {
  border: 1px solid #f59e0b;
}

:deep(.case-if-reuse-tip .el-alert__title) {
  color: #92400e;
}

.filename-inline {
  margin-left: auto;
}

:deep(.filename-inline .filename-input) {
  width: 200px;
}

:deep(.filename-inline .el-input__wrapper) {
  box-shadow: none;
  background: transparent;
  padding: 0 4px;
}

:deep(.filename-inline .el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #d1d5db inset;
}

:deep(.filename-inline .el-input__inner) {
  font-size: 12px;
  color: #9ca3af;
  text-align: right;
}

:deep(.filename-inline .el-input__inner::placeholder) {
  color: #d1d5db;
}

:deep(.filename-inline.disabled .el-input__inner) {
  color: #d1d5db;
}

.sheet-wrapper {
  position: relative;
  width: 100%;
  flex: 1;
  min-height: 0;
  border: 1px solid #e5e7eb;
}

.sheet-container {
  width: 100%;
  height: 100%;
}

.zoom-bar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  padding: 4px 12px;
  background: #f5f6f7;
  border: 1px solid #e0e2e4;
  border-top: none;
  user-select: none;
}

.zoom-btn {
  width: 22px;
  height: 22px;
  border: 1px solid #d1d5db;
  border-radius: 3px;
  background: #fff;
  color: #444;
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  flex-shrink: 0;
}

.zoom-btn:hover {
  background: #e5e7eb;
}

.zoom-slider {
  width: 120px;
  height: 4px;
  cursor: pointer;
  accent-color: #3498db;
}

.zoom-label {
  width: 40px;
  font-size: 12px;
  color: #555;
  text-align: right;
  cursor: pointer;
  flex-shrink: 0;
}

.zoom-label:hover {
  color: #3498db;
  text-decoration: underline;
}

:deep(.x-spreadsheet-bottombar) {
  position: relative;
  display: flex;
  align-items: center;
  overflow: hidden;
  padding-right: 60px;
}

:deep(.x-spreadsheet-bottombar .x-spreadsheet-menu) {
  display: flex;
  flex-wrap: nowrap;
  overflow-x: auto;
  overflow-y: hidden;
  flex: 1;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

:deep(.x-spreadsheet-bottombar .x-spreadsheet-menu::-webkit-scrollbar) {
  display: none;
}

:deep(.x-spreadsheet-bottombar .x-spreadsheet-menu > li) {
  float: none;
  flex-shrink: 0;
}



 :deep(.case-design-init-prompt.el-message-box) {
   width: min(980px, 80vw);
 }

 :deep(.case-design-init-prompt .el-message-box__content) {
   max-height: 70vh;
 }

 :deep(.case-design-init-prompt .el-message-box__input) {
   margin-top: 10px;
 }

 :deep(.case-design-init-prompt .el-message-box__input textarea) {
   height: min(52vh, 520px);
   resize: vertical;
   font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
   font-size: 13px;
   line-height: 1.55;
   background: #0b1220;
   color: #e5e7eb;
   border: 1px solid rgba(255, 255, 255, 0.12);
   border-radius: 8px;
   padding: 10px 12px;
 }

 :deep(.case-design-init-prompt .el-message-box__input textarea::placeholder) {
   color: rgba(229, 231, 235, 0.55);
 }

 :deep(.case-design-init-prompt .el-message-box__input textarea:focus) {
   border-color: rgba(59, 130, 246, 0.8);
   box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.25);
 }

 :deep(.case-design-init-prompt .el-message-box__btns) {
   padding-top: 12px;
 }

 :deep(.case-design-if-exception-prompt.el-message-box) {
   width: min(1280px, 92vw);
   max-width: 92vw;
 }

 :deep(.case-design-if-exception-prompt .el-message-box__content) {
   max-height: 80vh;
 }

 :deep(.case-design-if-exception-prompt .el-message-box__input) {
   margin-top: 10px;
 }

 :deep(.case-design-if-exception-prompt .el-message-box__input textarea) {
   height: min(62vh, 720px);
   resize: vertical;
   font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
   font-size: 13px;
   line-height: 1.65;
   background: #0b1220;
   color: #e5e7eb;
   border: 1px solid rgba(255, 255, 255, 0.12);
   border-radius: 8px;
   padding: 10px 12px;
   overflow: auto;
 }

 :deep(.case-design-if-exception-prompt .el-message-box__input textarea::-webkit-scrollbar) {
   width: 10px;
   height: 10px;
 }

 :deep(.case-design-if-exception-prompt .el-message-box__input textarea::-webkit-scrollbar-thumb) {
   background: rgba(255, 255, 255, 0.18);
   border-radius: 10px;
 }

 :deep(.case-design-if-exception-prompt .el-message-box__input textarea::-webkit-scrollbar-thumb:hover) {
   background: rgba(255, 255, 255, 0.26);
 }

 :deep(.case-design-if-exception-prompt .el-message-box__input textarea::-webkit-scrollbar-track) {
   background: rgba(255, 255, 255, 0.06);
 }

 :deep(.case-design-if-exception-prompt .el-message-box__input textarea::placeholder) {
   color: rgba(229, 231, 235, 0.55);
 }

 :deep(.case-design-if-exception-prompt .el-message-box__input textarea:focus) {
   border-color: rgba(59, 130, 246, 0.8);
   box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.25);
 }

 :deep(.case-design-if-exception-prompt .el-message-box__btns) {
   padding-top: 12px;
 }

 :deep(.case-design-if-period-prompt.el-message-box) {
   width: min(1280px, 92vw);
   max-width: 92vw;
 }

 :deep(.case-design-if-period-prompt .el-message-box__content) {
   max-height: 80vh;
 }

 :deep(.case-design-if-period-prompt .el-message-box__input) {
   margin-top: 10px;
 }

 :deep(.case-design-if-period-prompt .el-message-box__input textarea) {
   height: min(62vh, 720px);
   resize: vertical;
   font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
   font-size: 13px;
   line-height: 1.65;
   background: #0b1220;
   color: #e5e7eb;
   border: 1px solid rgba(255, 255, 255, 0.12);
   border-radius: 8px;
   padding: 10px 12px;
   overflow: auto;
 }

 :deep(.case-design-if-period-prompt .el-message-box__input textarea::placeholder) {
   color: rgba(229, 231, 235, 0.55);
 }

 :deep(.case-design-if-period-prompt .el-message-box__input textarea:focus) {
   border-color: rgba(59, 130, 246, 0.8);
   box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.25);
 }

 :deep(.case-design-if-period-prompt .el-message-box__btns) {
   padding-top: 12px;
 }

 :deep(.req-design-common-prompt.el-message-box) {
   width: min(720px, 80vw);
 }

 :deep(.req-design-common-prompt .el-message-box__content) {
   max-height: 65vh;
 }

 :deep(.case-design-common-box.el-message-box) {
   width: min(820px, 86vw);
 }

 :deep(.case-design-common-box .el-message-box__content) {
   max-height: 70vh;
 }
</style>
