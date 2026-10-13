import { computed } from 'vue'

export function useDiffDisplay(diffRowsRef, changeRowIndicesRef, onlyChangesRef, contextLinesRef) {
  const displayRows = computed(() => {
    const rows = diffRowsRef.value || []
    const onlyChanges = !!onlyChangesRef.value
    const ctx = Math.max(0, Number(contextLinesRef.value || 0))

    if (!onlyChanges) return rows

    const changeIdx = changeRowIndicesRef.value || []
    if (changeIdx.length === 0) return rows

    const include = new Set()
    for (const i of changeIdx) {
      const start = Math.max(0, i - ctx)
      const end = Math.min(rows.length - 1, i + ctx)
      for (let k = start; k <= end; k++) include.add(k)
    }

    const sorted = Array.from(include).sort((a, b) => a - b)
    return sorted.map((i) => rows[i])
  })

  const displayChangeIndices = computed(() => {
    const rows = diffRowsRef.value || []
    const onlyChanges = !!onlyChangesRef.value
    const ctx = Math.max(0, Number(contextLinesRef.value || 0))

    const changeIdx = changeRowIndicesRef.value || []
    if (!onlyChanges) return changeIdx
    if (changeIdx.length === 0) return []

    const include = []
    const includedSet = new Set()
    for (const i of changeIdx) {
      const start = Math.max(0, i - ctx)
      const end = Math.min(rows.length - 1, i + ctx)
      for (let k = start; k <= end; k++) {
        if (!includedSet.has(k)) {
          includedSet.add(k)
          include.push(k)
        }
      }
    }
    include.sort((a, b) => a - b)

    const originalToDisplay = new Map()
    for (let di = 0; di < include.length; di++) {
      originalToDisplay.set(include[di], di)
    }

    const out = []
    for (const ci of changeIdx) {
      const di = originalToDisplay.get(ci)
      if (di != null) out.push(di)
    }
    return out
  })

  return { displayRows, displayChangeIndices }
}
