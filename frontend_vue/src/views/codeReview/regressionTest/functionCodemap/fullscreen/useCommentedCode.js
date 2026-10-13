import { computed, watch } from 'vue'

export function normalizeCommentedCode(raw) {
  if (!raw) return ''
  return String(raw)
    .replace(/\\n/g, '\n')
    .replace(/\\t/g, '\t')
    .replace(/\\r/g, '\r')
}

function applyOverlay(fullText, startLine, endLine, replacementText) {
  const text = String(fullText || '')
  const rep = String(replacementText || '')
  const s = Number(startLine)
  const e = Number(endLine)

  if (!text) return ''
  if (!rep) return text
  if (!Number.isFinite(s) || !Number.isFinite(e) || s <= 0 || e <= 0 || e < s) return text

  const lines = text.split('\n')
  const segLen = e - s + 1
  let repLines = rep.split('\n')
  if (Number.isFinite(segLen) && segLen > 0) {
    if (repLines.length < segLen) {
      repLines = repLines.concat(new Array(segLen - repLines.length).fill(''))
    } else if (repLines.length > segLen) {
      repLines = repLines.slice(0, segLen)
    }
  }
  const startIdx = Math.max(0, s - 1)
  const endIdx = Math.min(lines.length, e)
  const out = lines.slice(0, startIdx).concat(repLines).concat(lines.slice(endIdx))
  return out.join('\n')
}

function normPath(p) {
  return String(p || '').replace(/\\/g, '/').trim()
}

function pathVariants(raw) {
  const p = normPath(raw)
  if (!p) return []
  const seg = p.split('/').filter(Boolean)
  if (seg.length <= 1) return [seg.join('/')]
  const stripped = seg.slice(1).join('/')
  if (stripped && stripped !== p) return [p, stripped]
  return [p]
}

function isCommentedDebugEnabled() {
  try {
    return String(localStorage.getItem('codemapCommentedDebug') || '') === '1'
  } catch {
    return false
  }
}

export function useCommentedCode({ newCodeViewMode, newCodeText, selectedFuncDetail, sidebarSelectedNode, codeMapData, selectedFileKey, ElMessage }) {
  const newCodeTextEffective = computed(() => {
    // 始终以整文件为基准，保证 diff 对齐
    const full = newCodeText.value
    if (newCodeViewMode.value !== 'commented') return full

    const fileKey = normPath(selectedFileKey?.value)
    const nodes = Array.isArray(codeMapData?.value?.nodes) ? codeMapData.value.nodes : []

    const candidates = []
    const fkList = pathVariants(fileKey)

    try {
      if (isCommentedDebugEnabled()) {
        let withCommented = 0
        let fileMatched = 0
        let fileMatchedWithCommented = 0
        let fileMatchedInvalidRange = 0
        const fileMatchSample = []
        const sample = []
        for (const n of nodes) {
          const npList = pathVariants(n?.file_path)
          const inFile = fkList.length ? fkList.some((fk) => npList.includes(fk)) : true
          if (inFile && (n?.type === 'function' || n?.type === 'fpga_module')) {
            fileMatched++
          }

          const commented = normalizeCommentedCode(n?.commented_code)
          if (!commented) continue
          withCommented++

          if (inFile && (n?.type === 'function' || n?.type === 'fpga_module')) {
            fileMatchedWithCommented++
            const st = Number(n?.start_line)
            const ed = Number(n?.end_line)
            if (!Number.isFinite(st) || !Number.isFinite(ed) || st <= 0 || ed <= 0 || ed < st) {
              fileMatchedInvalidRange++
            }
            if (fileMatchSample.length < 8) {
              fileMatchSample.push({
                type: n?.type,
                name: n?.name,
                file_path: n?.file_path,
                start_line: n?.start_line,
                end_line: n?.end_line,
                commentedLen: commented.length
              })
            }
          }

          if (sample.length < 8) {
            sample.push({
              type: n?.type,
              name: n?.name,
              file_path: n?.file_path,
              start_line: n?.start_line,
              end_line: n?.end_line,
              commentedLen: commented.length
            })
          }
        }
        // eslint-disable-next-line no-console
        console.warn('[commented-code] build candidates', {
          selectedFileKey: fileKey,
          fkList,
          nodeCount: nodes.length,
          withCommented,
          fileMatched,
          fileMatchedWithCommented,
          fileMatchedInvalidRange,
          fileMatchSample,
          sample
        })
      }
    } catch {}

    for (const n of nodes) {
      if (!(n && (n.type === 'function' || n.type === 'fpga_module'))) continue
      const commented = normalizeCommentedCode(n.commented_code)
      if (!commented) continue
      const st = Number(n.start_line)
      const ed = Number(n.end_line)
      if (!Number.isFinite(st) || !Number.isFinite(ed) || st <= 0 || ed <= 0 || ed < st) continue

      if (fkList.length) {
        const npList = pathVariants(n.file_path)
        let ok = false
        for (const fk of fkList) {
          if (npList.includes(fk)) {
            ok = true
            break
          }
        }
        if (!ok) continue
      }
      candidates.push({ start_line: st, end_line: ed, text: commented })
    }

    // 从下往上覆盖，避免上方替换导致后续行号偏移（applyOverlay 会对齐行数）
    candidates.sort((a, b) => (b.start_line || 0) - (a.start_line || 0))

    try {
      if (isCommentedDebugEnabled()) {
        const head = candidates.length ? candidates[candidates.length - 1] : null
        const tail = candidates.length ? candidates[0] : null
        // eslint-disable-next-line no-console
        console.warn('[commented-code] candidates result', {
          selectedFileKey: fileKey,
          count: candidates.length,
          first: head ? { start_line: head.start_line, end_line: head.end_line, textLen: head.text.length } : null,
          last: tail ? { start_line: tail.start_line, end_line: tail.end_line, textLen: tail.text.length } : null
        })
      }
    } catch {}

    let out = full
    for (const it of candidates) {
      out = applyOverlay(out, it.start_line, it.end_line, it.text)
    }
    return out
  })

  watch(
    () => newCodeViewMode.value,
    (mode) => {
      if (mode !== 'commented') return

      const fileKey = normPath(selectedFileKey?.value)
      const nodes = Array.isArray(codeMapData?.value?.nodes) ? codeMapData.value.nodes : []
      const fkList = pathVariants(fileKey)
      let hasAny = false
      for (const n of nodes) {
        if (!(n && (n.type === 'function' || n.type === 'fpga_module'))) continue
        const commented = normalizeCommentedCode(n.commented_code)
        if (!commented) continue
        const st = Number(n.start_line)
        const ed = Number(n.end_line)
        if (!Number.isFinite(st) || !Number.isFinite(ed) || st <= 0 || ed <= 0 || ed < st) continue
        if (fkList.length) {
          const npList = pathVariants(n.file_path)
          let ok = false
          for (const fk of fkList) {
            if (npList.includes(fk)) {
              ok = true
              break
            }
          }
          if (!ok) continue
        }
        hasAny = true
        break
      }

      if (!hasAny) {
        // 兼容旧逻辑：若当前选中函数本身有注释代码，仍不提示
        const sn = sidebarSelectedNode.value
        const hasSelected = !!normalizeCommentedCode(sn?.commented_code)
        if (!hasSelected) ElMessage.warning('当前文件内暂无 AI 注释后代码')
      }
    }
  )

  return { newCodeTextEffective }
}
