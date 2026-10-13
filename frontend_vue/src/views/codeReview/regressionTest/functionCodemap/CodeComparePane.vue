<template>
  <div class="compare-view">
    <div class="diff-overview" @click="handleOverviewClick">
      <div
        v-for="m in overviewMarks"
        :key="m.idx"
        class="diff-overview-mark"
        :style="{ top: m.top + '%' }"
        @click.stop="scrollToCursor(m.cursor)"
      ></div>
    </div>

    <div class="code-pane">
      <div class="code-pane-header">
        <div class="code-pane-title">上一版本代码</div>
        <div class="code-pane-meta">{{ oldMeta }}</div>
      </div>
      <ComparePaneToolbar
        v-model:diffMode="diffMode"
        v-model:onlyChanges="onlyChanges"
        v-model:contextLines="contextLines"
        :change-count="changeCount"
        :current-cursor="currentCursor"
        @prev="prev"
        @next="next"
      />

      <div ref="oldCodePaneRef" class="code-pane-body" @scroll="handleLeftScroll">
        <pre v-if="!diffMode" class="code-block"><code>{{ oldText }}</code></pre>
        <CodeDiffViewport v-else :rows="displayRows" :focused-row-index="focusedRowIndex" side="l" />
      </div>
    </div>

    <div class="code-pane">
      <div class="code-pane-header">
        <div class="code-pane-title">当前版本代码</div>
        <div class="code-pane-header-right">
          <div class="code-pane-meta">{{ newMeta }}</div>
          <el-radio-group v-model="newCodeViewMode" size="small">
            <el-radio-button label="original">源代码</el-radio-button>
            <el-radio-button label="commented">注释后代码</el-radio-button>
          </el-radio-group>
        </div>
      </div>
      <ComparePaneToolbar
        v-model:diffMode="diffMode"
        v-model:onlyChanges="onlyChanges"
        v-model:contextLines="contextLines"
        :change-count="changeCount"
        :current-cursor="currentCursor"
        :show-counter="true"
        @prev="prev"
        @next="next"
      />

      <div ref="newCodePaneRef" class="code-pane-body" @scroll="handleRightScroll">
        <pre v-if="!diffMode" class="code-block"><code>
          <span
            v-for="(ln, i) in newLines"
            :key="i"
            class="code-line"
            :class="{ highlighted: i + 1 === rightHighlightLocalLine }"
          >{{ ln }}\n</span>
        </code></pre>
        <CodeDiffViewport
          v-else
          :rows="displayRows"
          :focused-row-index="focusedRowIndex"
          :highlight-row-index="rightHighlightRowIndex"
          side="r"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, toRef, computed, nextTick, onMounted } from 'vue'
import ComparePaneToolbar from './ComparePaneToolbar.vue'
import CodeDiffViewport from './CodeDiffViewport.vue'
import { useChangeNavigator } from './useChangeNavigator'
import { useDiffDisplay } from './useDiffDisplay'

const props = defineProps({
  oldText: { type: String, default: '' },
  newText: { type: String, default: '' },
  oldMeta: { type: String, default: '' },
  newMeta: { type: String, default: '' },
  newCodeViewMode: { type: String, default: 'original' },
  diffRows: { type: Array, required: true },
  changeRowIndices: { type: Array, required: true }
})

const emit = defineEmits(['update:newCodeViewMode'])

const newCodeViewMode = computed({
  get: () => props.newCodeViewMode,
  set: (v) => emit('update:newCodeViewMode', v)
})

const oldCodePaneRef = ref(null)
const newCodePaneRef = ref(null)

const diffMode = ref(true)
const onlyChanges = ref(false)
const contextLines = ref(3)

const isFlashing = ref(false)
let flashTimer = null

const didAutoFocusOnce = ref(false)

const rightHighlightRowIndex = ref(-1)
const rightHighlightLocalLine = ref(-1)
let rightHighlightTimer = null

const newLines = computed(() => String(props.newText || '').split('\n'))

// 强制同步滚动：任何一侧滚动都将两侧 scrollTop 量化到同一行网格，避免视觉错位。
// 注意：这里同时处理用户滚动与 scrollIntoView 等程序化滚动。
const isSyncScrolling = ref(false)

function quantizeTop(top, rowH = 20) {
  const t = Number(top) || 0
  return Math.round(t / rowH) * rowH
}

function syncScroll(fromEl) {
  if (isSyncScrolling.value) return
  const l = oldCodePaneRef.value
  const r = newCodePaneRef.value
  if (!l || !r) return

  const rowH = 20
  const base = fromEl || l
  const qTop = quantizeTop(base.scrollTop, rowH)

  isSyncScrolling.value = true
  l.scrollTop = qTop
  r.scrollTop = qTop
  l.scrollLeft = base.scrollLeft
  r.scrollLeft = base.scrollLeft
  requestAnimationFrame(() => {
    // 某些浏览器/布局在同一帧内会对 scrollTop 做回弹/重算，导致两侧出现 1 行以内的视觉错位。
    // 这里再校验一次，确保最终一致。
    if (l.scrollTop !== r.scrollTop) {
      const top2 = quantizeTop(l.scrollTop, rowH)
      l.scrollTop = top2
      r.scrollTop = top2
    }
    isSyncScrolling.value = false
  })
}

function handleLeftScroll(e) {
  syncScroll(e?.target)
}

function handleRightScroll(e) {
  syncScroll(e?.target)
}
const changeRowIndicesRef = toRef(props, 'changeRowIndices')

const diffRowsRef = toRef(props, 'diffRows')
const { displayRows, displayChangeIndices } = useDiffDisplay(
  diffRowsRef,
  changeRowIndicesRef,
  onlyChanges,
  contextLines
)

// 关键：切换“注释后代码/源代码”或 diffRows 重算后，两侧滚动容器会保留旧 scrollTop，
// 但由于渲染/高度变化，可能导致左右不在同一 diff 行上（视觉错位）。
// 在 DOM 更新后强制把右侧对齐到左侧，保证函数声明等关键行水平对齐。
watch(
  [
    () => props.newCodeViewMode,
    () => diffMode.value,
    () => (displayRows.value ? displayRows.value.length : 0),
    () => onlyChanges.value,
    () => contextLines.value
  ],
  async () => {
    await nextTick()
    const l = oldCodePaneRef.value
    const r = newCodePaneRef.value
    if (!l || !r) return
    const rowH = 20
    const qTop = Math.round((Number(l.scrollTop) || 0) / rowH) * rowH
    l.scrollTop = qTop
    r.scrollTop = qTop
    r.scrollLeft = l.scrollLeft

    // 再等一帧，防止布局/内容更新后 scrollTop 被回弹
    requestAnimationFrame(() => {
      const l2 = oldCodePaneRef.value
      const r2 = newCodePaneRef.value
      if (!l2 || !r2) return
      const q2 = Math.round((Number(l2.scrollTop) || 0) / rowH) * rowH
      l2.scrollTop = q2
      r2.scrollTop = q2
      r2.scrollLeft = l2.scrollLeft
    })
  }
)

// 监听 displayRows 变化，强制重新对齐（避免过滤/切片后左右错位）
watch(
  () => displayRows.value.length,
  async () => {
    await nextTick()
    const l = oldCodePaneRef.value
    const r = newCodePaneRef.value
    if (!l || !r) return
    const rowH = 20
    const qTop = Math.round((Number(l.scrollTop) || 0) / rowH) * rowH
    l.scrollTop = qTop
    r.scrollTop = qTop
    r.scrollLeft = l.scrollLeft
  }
)

// 组件挂载后立刻对齐一次，确保初始状态就是对齐的
onMounted(async () => {
  await nextTick()
  const l = oldCodePaneRef.value
  const r = newCodePaneRef.value
  if (!l || !r) return
  const rowH = 20
  const qTop = Math.round((Number(l.scrollTop) || 0) / rowH) * rowH
  l.scrollTop = qTop
  r.scrollTop = qTop
  r.scrollLeft = l.scrollLeft
})

const overviewMarks = computed(() => {
  const total = displayRows.value.length || 1
  const out = []
  for (let i = 0; i < (displayChangeIndices.value || []).length; i++) {
    const idx = displayChangeIndices.value[i]
    if (typeof idx !== 'number' || idx < 0) continue
    out.push({
      idx,
      cursor: i,
      top: (idx / total) * 100
    })
  }
  return out
})

function handleOverviewClick(e) {
  const el = e.currentTarget
  if (!el) return
  const rect = el.getBoundingClientRect()
  const y = e.clientY - rect.top
  const ratio = rect.height ? y / rect.height : 0
  const total = displayRows.value.length || 1
  const targetRow = Math.max(0, Math.min(total - 1, Math.floor(ratio * total)))

  // 找到最接近的变更点
  let bestCursor = 0
  let bestDist = Infinity
  for (let i = 0; i < (displayChangeIndices.value || []).length; i++) {
    const idx = displayChangeIndices.value[i]
    const d = Math.abs(idx - targetRow)
    if (d < bestDist) {
      bestDist = d
      bestCursor = i
    }
  }
  scrollToCursor(bestCursor)
}

const { currentCursor, focusedRowIndex, changeCount, prev, next, scrollToCursor } = useChangeNavigator(displayChangeIndices, oldCodePaneRef)

function clamp(n, min, max) {
  return Math.min(max, Math.max(min, n))
}

function scrollToRowCentered(scrollerEl, idx, rowH) {
  if (!scrollerEl || typeof idx !== 'number' || idx < 0) return
  const clientH = scrollerEl.clientHeight || 0
  const scrollH = scrollerEl.scrollHeight || 0
  const maxTop = Math.max(0, scrollH - clientH)
  const target = idx * rowH - Math.floor(clientH / 2) + Math.floor(rowH / 2)
  scrollerEl.scrollTop = clamp(target, 0, maxTop)
}

function scrollToLine({ oldLine, newLine }) {
  if (!diffMode.value) return
  // 外部显式定位（选中函数/切换视图恢复定位）时，禁止内部再把视图强制拉回到第一处变更
  didAutoFocusOnce.value = true
  const rowH = 20
  const idxL = typeof oldLine === 'number' && oldLine > 0
    ? displayRows.value.findIndex((r) => Number(r.leftLineNo) === Number(oldLine))
    : -1
  const idxR = typeof newLine === 'number' && newLine > 0
    ? displayRows.value.findIndex((r) => Number(r.rightLineNo) === Number(newLine))
    : -1

  if (idxL >= 0 && oldCodePaneRef.value) {
    scrollToRowCentered(oldCodePaneRef.value, idxL, rowH)
  }
  if (idxR >= 0 && newCodePaneRef.value) {
    scrollToRowCentered(newCodePaneRef.value, idxR, rowH)
  }
}

function flash(durationMs = 2000) {
  isFlashing.value = false
  if (flashTimer) {
    clearTimeout(flashTimer)
    flashTimer = null
  }
  isFlashing.value = true
  flashTimer = setTimeout(() => {
    isFlashing.value = false
    flashTimer = null
  }, durationMs)
}

function flashRightLine({ rightLineNo, localLine = 1, durationMs = 3000 } = {}) {
  // 外部显式高亮时，禁止内部再把视图强制拉回到第一处变更
  didAutoFocusOnce.value = true
  rightHighlightRowIndex.value = -1
  rightHighlightLocalLine.value = -1
  if (rightHighlightTimer) {
    clearTimeout(rightHighlightTimer)
    rightHighlightTimer = null
  }

  if (diffMode.value) {
    const rowH = 20
    let idx = typeof rightLineNo === 'number' && rightLineNo > 0
      ? displayRows.value.findIndex((r) => Number(r.rightLineNo) === Number(rightLineNo))
      : -1

    // 说明：当右侧展示的是“函数片段/注释后代码”时，diff 行号通常从 1 开始，不再是原文件行号。
    // 此时 rightLineNo（原文件 start_line）可能无法命中，回退用 localLine 做定位。
    if (idx < 0) {
      const ll = Number(localLine)
      if (Number.isFinite(ll) && ll > 0) {
        idx = ll - 1
      }
    }

    if (idx >= 0) {
      rightHighlightRowIndex.value = idx
      if (newCodePaneRef.value) scrollToRowCentered(newCodePaneRef.value, idx, rowH)
    }
  } else {
    const lineH = 20
    const ll = Number(localLine)
    if (Number.isFinite(ll) && ll > 0) {
      rightHighlightLocalLine.value = ll
      if (newCodePaneRef.value) scrollToRowCentered(newCodePaneRef.value, ll - 1, lineH)
    }
  }

  rightHighlightTimer = setTimeout(() => {
    rightHighlightRowIndex.value = -1
    rightHighlightLocalLine.value = -1
    rightHighlightTimer = null
  }, durationMs)
}

defineExpose({ scrollToLine, flash, flashRightLine })

watch(
  () => changeRowIndicesRef.value,
  () => {
    // 变更集合更新后，重置并聚焦第一处变更（若存在）
    // 注意：切换“源代码/注释后代码”会导致 diff 重新计算；此时不应强制把滚动拉回到第一处变更
    if (!didAutoFocusOnce.value && changeRowIndicesRef.value.length > 0 && diffMode.value) {
      scrollToCursor(0)
      didAutoFocusOnce.value = true
    }
  }
)

watch(
  () => [onlyChanges.value, contextLines.value, diffMode.value],
  () => {
    if (diffMode.value && changeCount.value > 0) {
      scrollToCursor(0)
    }
  }
)
</script>

<style scoped>
.compare-view {
  flex: 1;
  min-width: 0;
  display: flex;
  gap: 12px;
  padding: 12px;
  box-sizing: border-box;
}

.diff-overview {
  width: 10px;
  flex: 0 0 10px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.12);
  position: relative;
  margin-top: 72px;
  margin-bottom: 12px;
  cursor: pointer;
}

.diff-overview-mark {
  position: absolute;
  left: 1px;
  right: 1px;
  height: 6px;
  transform: translateY(-50%);
  border-radius: 4px;
  background: rgba(231, 76, 60, 0.9);
}

.code-pane {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
}

.code-pane-header {
  padding: 10px 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  background: #2d2d2d;
  color: #e0e0e0;
  border-bottom: 1px solid #404040;
}

.code-pane-header-right {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  min-width: 0;
}

.code-pane-title {
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
}

.code-pane-meta {
  font-size: 12px;
  color: #bdbdbd;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.code-pane-toolbar {
  display: none;
}

.code-pane-body {
  flex: 1;
  overflow: auto;
  background: #1a1a1a;
}

.code-line {
  display: block;
  white-space: pre;
}

.code-line.highlighted {
  animation: code-line-highlight 3s ease-in-out;
}

@keyframes code-line-highlight {
  0% {
    background: rgba(0, 122, 204, 0);
  }
  20% {
    background: rgba(0, 122, 204, 0.28);
  }
  70% {
    background: rgba(0, 122, 204, 0.12);
  }
  100% {
    background: rgba(0, 122, 204, 0);
  }
}

.code-block {
  margin: 0;
  padding: 12px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 20px;
  color: #e0e0e0;
  white-space: pre;
}

</style>
