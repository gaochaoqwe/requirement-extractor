import { nextTick } from 'vue'

export function useProblems({ taskId, axios, ElMessage, sidebarSelectedNode, codeMapData, oldTreeData, loadCodeMap }) {
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

  function getProblemStatus(p) {
    return p?.problem_status ?? p?.problems_status ?? 1
  }

  function handleProblemStatusChanged() {
    if (!sidebarSelectedNode.value || !Array.isArray(sidebarSelectedNode.value.problems) || !codeMapData.value) {
      return
    }

    const updated = sidebarSelectedNode.value
    const nodes = Array.isArray(codeMapData.value.nodes) ? codeMapData.value.nodes : []
    const uPaths = pathVariants(updated.file_path)
    const idx = nodes.findIndex(
      (n) => {
        if (!(n && (n.type === 'function' || n.type === 'fpga_module'))) return false
        if (String(n.name || '').trim() !== String(updated.name || '').trim()) return false
        const nPaths = pathVariants(n.file_path)
        for (const up of uPaths) {
          if (nPaths.includes(up)) return true
        }
        return false
      }
    )
    if (idx !== -1) {
      nodes[idx].problems = updated.problems
    }

    if (Array.isArray(codeMapData.value.problems)) {
      for (const p of updated.problems) {
        const pIdx = codeMapData.value.problems.findIndex((x) => x.id === p.id)
        if (pIdx !== -1) codeMapData.value.problems[pIdx].problem_status = getProblemStatus(p)
      }
    }
  }

  async function batchUpdateProblemsToViewed(problems) {
    const list = Array.isArray(problems) ? problems : []
    const ids = list.map((p) => p?.id).filter(Boolean)
    if (!ids.length || !taskId.value) return

    try {
      const res = await axios.patch(
        `/api/codeReview/regressionTest/functionReview/${taskId.value}/problems/status`,
        {
          problem_ids: ids,
          status: 2
        }
      )
      if (res.data?.success) {
        for (const p of list) {
          if (!p) continue
          if (getProblemStatus(p) === 1) p.problem_status = 2
        }
        handleProblemStatusChanged()
      }
    } catch (error) {
      console.error('批量更新问题状态失败:', error)
    }
  }

  async function markSelectedNodeProblemsViewedIfNeeded(node) {
    if (!node || !Array.isArray(node.problems) || !node.problems.length) return
    const toViewed = node.problems.filter((p) => getProblemStatus(p) === 1)
    if (toViewed.length) await batchUpdateProblemsToViewed(toViewed)
  }

  async function handleFiltersApplied() {
    ElMessage.success('过滤规则已应用')
    await loadCodeMap()
  }

  async function handleViewMarkedProblems(markedLocationsRef, selectPair) {
    try {
      const response = await axios.get(
        `/api/codeReview/regressionTest/functionReview/${taskId.value}/marked_problems/locations`,
        { params: { analysis_type: 'function' } }
      )
      if (response.data?.success) {
        const locations = response.data.data
        markedLocationsRef.value = locations
        ElMessage.success({
          message: `找到 ${locations.files.length} 个文件，${locations.functions.length} 个函数包含已标记问题`,
          duration: 3000
        })

        const firstFn = Array.isArray(locations?.functions) ? locations.functions[0] : null
        if (firstFn) {
          const stack = [].concat(oldTreeData.value || [])
          while (stack.length) {
            const n = stack.shift()
            if (!n) continue
            if (n.type === 'function') {
              const fnName = String(n.new_label || n.old_label || '').trim()
              if (fnName === String(firstFn).trim()) {
                const pid = n.new_pair_id || n.old_pair_id
                if (pid) {
                  await nextTick()
                  if (typeof selectPair === 'function') selectPair(pid)
                }
                break
              }
            }
            for (const c of n.children || []) stack.push(c)
          }
        }
      }
    } catch (error) {
      console.error('获取标记位置失败:', error)
      ElMessage.error('获取标记位置失败')
    }
  }

  function handleHighlightProblem(problemInfo, highlightedProblemRef) {
    highlightedProblemRef.value = problemInfo
  }

  return {
    getProblemStatus,
    handleProblemStatusChanged,
    markSelectedNodeProblemsViewedIfNeeded,
    handleFiltersApplied,
    handleViewMarkedProblems,
    handleHighlightProblem
  }
}
