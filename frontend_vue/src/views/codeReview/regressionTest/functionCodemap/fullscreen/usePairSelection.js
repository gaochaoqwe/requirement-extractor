import { nextTick } from 'vue'

function resolveHighlightLineInText(text, startLine, endLine) {
  const st = Number(startLine)
  const ed = Number(endLine)
  if (!text) return st
  if (!Number.isFinite(st) || st <= 0) return st
  const lines = String(text).split('\n')
  const maxLine = lines.length
  const limit = Number.isFinite(ed) && ed > 0 ? Math.min(ed, maxLine) : maxLine

  let inBlock = false
  for (let ln = st; ln <= limit; ln++) {
    const raw = lines[ln - 1] ?? ''
    const s = String(raw)
    const t = s.trim()
    if (!t) continue

    // 处理块注释状态机：支持从 start_line 落在注释内部的情况
    if (inBlock) {
      const closeIdx = t.indexOf('*/')
      if (closeIdx >= 0) {
        inBlock = false
        const rest = t.slice(closeIdx + 2).trim()
        if (!rest) continue
        // rest 仍可能是行注释
        if (rest.startsWith('//')) continue
        return ln
      }
      continue
    }

    if (t.startsWith('//')) continue
    if (t.startsWith('/*')) {
      const closeIdx = t.indexOf('*/')
      if (closeIdx >= 0) {
        const rest = t.slice(closeIdx + 2).trim()
        if (!rest) continue
        if (rest.startsWith('//')) continue
        return ln
      }
      inBlock = true
      continue
    }

    // 常见块注释中间行："* xxxx"
    if (t.startsWith('*')) continue

    return ln
  }

  return st
}

function isPairEqDebugEnabled() {
  try {
    return String(localStorage.getItem('codemapPairEqDebug') || '') === '1'
  } catch {
    return false
  }
}

export function usePairSelection({ axios, ElMessage, changeTypeByPairId, funcRowIdByPairId, fileIdByPairId, findFileNodeById, loadFileTextsByNode, codeCompareRef, codeMapData, oldFuncDetail, newFuncDetail, sidebarSelectedNode, selectedPairId, selectedOldTreeKey, selectedNewTreeKey, markSelectedNodeProblemsViewedIfNeeded, oldFileText, newFileText }) {
  async function selectPair(pairId) {
    if (!pairId) return

    // 离开当前函数时才批量将“新发现(1)”的问题置为“已查看(2)”（不在进入/点击问题时置灰）
    await markSelectedNodeProblemsViewedIfNeeded(sidebarSelectedNode.value)

    selectedPairId.value = pairId
    const rowId = funcRowIdByPairId.value.get(pairId) || `pair:${pairId}`
    selectedOldTreeKey.value = rowId
    selectedNewTreeKey.value = rowId

    selectPairAsync(pairId)
  }

  async function selectPairAsync(pairId) {
    try {
      const res = await axios.get(`/api/codeReview/regressionTest/regression/pair/${pairId}`)
      oldFuncDetail.value = res.data?.old || null
      newFuncDetail.value = res.data?.new || null

      if (isPairEqDebugEnabled()) {
        try {
          // eslint-disable-next-line no-console
          console.warn('[pair-detail]', {
            pairId,
            pairChangeType: res.data?.change_type,
            hasOldFromApi: !!res.data?.old,
            hasNewFromApi: !!res.data?.new,
            oldIdFromApi: res.data?.old?.id ?? null,
            newIdFromApi: res.data?.new?.id ?? null,
            mappedChangeType: changeTypeByPairId.value?.get?.(pairId) ?? null
          })
        } catch {}
      }

      const ct = changeTypeByPairId.value.get(pairId)
      if (ct === 'new') {
        oldFuncDetail.value = null
      } else if (ct === 'deleted') {
        newFuncDetail.value = null
      }

      if (isPairEqDebugEnabled() && (ct === 'new' || ct === 'deleted')) {
        try {
          // eslint-disable-next-line no-console
          console.warn('[pair-detail] side cleared by mapped change_type', { pairId, mappedChangeType: ct })
        } catch {}
      }

      updateSidebarSelectedNode()

      const fid = fileIdByPairId.value.get(pairId)
      const fileNode = findFileNodeById(fid)
      if (fileNode) {
        await loadFileTextsByNode(fileNode)
        await nextTick()
        const oldLine = oldFuncDetail.value?.start_line
        const newLine = newFuncDetail.value?.start_line

        const oldHl = resolveHighlightLineInText(
          oldFileText?.value,
          oldFuncDetail.value?.start_line,
          oldFuncDetail.value?.end_line
        )
        const newHl = resolveHighlightLineInText(
          newFileText?.value,
          newFuncDetail.value?.start_line,
          newFuncDetail.value?.end_line
        )

        codeCompareRef.value?.scrollToLine?.({ oldLine: oldHl || oldLine, newLine: newHl || newLine })
        codeCompareRef.value?.flashRightLine?.({
          rightLineNo: typeof newHl === 'number' && newHl > 0 ? newHl : (typeof newLine === 'number' ? newLine : oldLine),
          localLine: 1,
          durationMs: 3000
        })
      }
    } catch (error) {
      console.error('加载函数对详情失败:', error)
      ElMessage.error('加载函数对详情失败')
    }
  }

  function updateSidebarSelectedNode() {
    const target = newFuncDetail.value || oldFuncDetail.value
    if (!target) {
      sidebarSelectedNode.value = null
      return
    }

    let enriched = { ...target }
    const nodes = codeMapData.value?.nodes || []
    const normPath = (p) => String(p || '').replace(/\\/g, '/').trim()
    const pathVariants = (raw) => {
      const p = normPath(raw)
      if (!p) return []
      const seg = p.split('/').filter(Boolean)
      if (seg.length <= 1) return [seg.join('/')]
      const stripped = seg.slice(1).join('/')
      if (stripped && stripped !== p) return [p, stripped]
      return [p]
    }
    const normName = (s) => String(s || '').trim()
    const tPaths = pathVariants(target.file_path)
    const tName = normName(target.function_name)
    const matched = nodes.find((n) => {
      if (!(n && (n.type === 'function' || n.type === 'fpga_module'))) return false
      if (normName(n.name) !== tName) return false
      const nPaths = pathVariants(n.file_path)
      for (const tp of tPaths) {
        if (nPaths.includes(tp)) return true
      }
      return false
    })
    if (matched) {
      const mergedCommented = target?.commented_code ?? matched?.commented_code
      const mergedDesc = target?.function_description ?? matched?.function_description
      enriched = {
        ...matched,
        ...enriched,
        name: matched.name || enriched.function_name,
        problems: matched.problems || [],
        commented_code: mergedCommented,
        function_description: mergedDesc
      }
    } else {
      enriched = {
        ...enriched,
        name: enriched.function_name,
        problems: []
      }
    }
    sidebarSelectedNode.value = enriched
  }

  return { selectPair }
}
