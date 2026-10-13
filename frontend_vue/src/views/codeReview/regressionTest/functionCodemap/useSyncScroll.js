import { ref } from 'vue'

export function useSyncScroll(leftRef, rightRef) {
  const isSyncScrolling = ref(false)

  const ROW_H = 20

  function quantizeTop(top) {
    const t = Number(top) || 0
    return Math.round(t / ROW_H) * ROW_H
  }

  function sync(from, to) {
    if (isSyncScrolling.value) return
    if (!from || !to) return
    isSyncScrolling.value = true
    // 关键：按行高量化 scrollTop，避免两侧渲染高度/小数滚动导致的“视觉错位/漂移”
    // 该组件主要用于 diff 视图，行高固定为 20px。
    const qTop = quantizeTop(from.scrollTop)
    // 同时量化 from/to，保证两侧严格落在同一行网格上
    from.scrollTop = qTop
    to.scrollTop = qTop
    to.scrollLeft = from.scrollLeft
    requestAnimationFrame(() => {
      isSyncScrolling.value = false
    })
  }

  function handleLeftScroll() {
    sync(leftRef.value, rightRef.value)
  }

  function handleRightScroll() {
    sync(rightRef.value, leftRef.value)
  }

  return { handleLeftScroll, handleRightScroll }
}
