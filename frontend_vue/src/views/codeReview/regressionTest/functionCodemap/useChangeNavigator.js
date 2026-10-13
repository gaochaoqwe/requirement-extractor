import { computed, nextTick, ref, watch } from 'vue'

export function useChangeNavigator(changeRowIndices, viewportRef) {
  const currentCursor = ref(0)
  const focusedRowIndex = ref(-1)

  const changeCount = computed(() => changeRowIndices.value.length)

  watch(changeCount, () => {
    currentCursor.value = 0
    focusedRowIndex.value = -1
  })

  function focusRow(rowIndex) {
    focusedRowIndex.value = rowIndex
    window.setTimeout(() => {
      if (focusedRowIndex.value === rowIndex) focusedRowIndex.value = -1
    }, 800)
  }

  function scrollToCursor(cursor) {
    const viewport = viewportRef.value
    if (!viewport) return
    const rowIndex = changeRowIndices.value[cursor]
    if (rowIndex == null) return

    nextTick(() => {
      const container = viewport.querySelector('.diff-viewport')
      if (!container) return
      const rows = container.querySelectorAll('.diff-row')
      const el = rows[rowIndex]
      if (!el) return
      el.scrollIntoView({ block: 'center' })
      focusRow(rowIndex)
    })
  }

  function prev() {
    if (changeRowIndices.value.length === 0) return
    currentCursor.value = Math.max(0, currentCursor.value - 1)
    scrollToCursor(currentCursor.value)
  }

  function next() {
    if (changeRowIndices.value.length === 0) return
    currentCursor.value = Math.min(changeRowIndices.value.length - 1, currentCursor.value + 1)
    scrollToCursor(currentCursor.value)
  }

  return { currentCursor, focusedRowIndex, changeCount, prev, next, scrollToCursor }
}
