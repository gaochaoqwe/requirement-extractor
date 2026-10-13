import { ref } from 'vue'

function normalizeCodeForEq(s) {
  const text = String(s || '').replace(/\r\n/g, '\n').replace(/\r/g, '\n')
  // 去掉每行行尾空白，避免格式化差异影响判断
  return text
    .split('\n')
    .map((ln) => String(ln).replace(/\s+$/g, ''))
    .join('\n')
    .trim()
}

export function useChangeTypeOverride({ taskId, axios }) {
  const overrideChangeTypeByPairId = ref(new Map())

  async function refreshOverridesFromChanges(changesItems) {
    const items = Array.isArray(changesItems) ? changesItems : []
    const targets = items
      .map((it) => ({ pair_id: it?.pair_id, change_type: it?.change_type }))
      .filter((x) => x.pair_id && x.change_type === 'modified')

    // 合并策略：保留已有 override（比如选中函数后实时校验写入的 modified），
    // 并对后端标 modified 的条目做二次校验：相等 -> 覆盖为 unchanged；不等 -> 移除 unchanged 覆盖。
    const next = new Map(overrideChangeTypeByPairId.value || [])

    if (!targets.length) {
      overrideChangeTypeByPairId.value = next
      return next
    }

    // 并发拉取，但规模通常不大；如果后续觉得慢再加节流/批量接口
    await Promise.all(
      targets.map(async (t) => {
        try {
          const res = await axios.get(`/api/codeReview/regressionTest/regression/pair/${t.pair_id}`)
          const oldSrc = res.data?.old?.source_code
          const newSrc = res.data?.new?.source_code
          if (oldSrc == null || newSrc == null) return

          const a = normalizeCodeForEq(oldSrc)
          const b = normalizeCodeForEq(newSrc)
          if (a === b) {
            next.set(t.pair_id, 'unchanged')
          } else {
            // 若之前因为误判被覆盖成 unchanged，这里撤销，避免压掉真实 modified
            if (next.get(t.pair_id) === 'unchanged') next.delete(t.pair_id)
          }
        } catch {
          // ignore
        }
      })
    )

    overrideChangeTypeByPairId.value = next
    return next
  }

  function applyOverridesToItems(items) {
    const map = overrideChangeTypeByPairId.value
    if (!map || map.size === 0) return items
    return (Array.isArray(items) ? items : []).map((it) => {
      const pid = it?.pair_id
      const ov = pid ? map.get(pid) : null
      if (!ov) return it
      return { ...it, change_type: ov }
    })
  }

  function setOverrideByPairId(pairId, changeType) {
    if (!pairId) return
    const next = new Map(overrideChangeTypeByPairId.value || [])
    if (!changeType) next.delete(pairId)
    else next.set(pairId, changeType)
    overrideChangeTypeByPairId.value = next
  }

  return { overrideChangeTypeByPairId, refreshOverridesFromChanges, applyOverridesToItems, setOverrideByPairId }
}
