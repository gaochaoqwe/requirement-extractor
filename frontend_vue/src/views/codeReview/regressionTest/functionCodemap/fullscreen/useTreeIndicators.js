import { computed } from 'vue'

export function useTreeIndicators({ codeMapData, oldTreeData }) {
  const pathVariants = (raw) => {
    const p = String(raw || '').replace(/\\/g, '/').trim()
    if (!p) return []
    const seg = p.split('/').filter(Boolean)
    if (seg.length <= 1) return [seg.join('/')]
    const stripped = seg.slice(1).join('/')
    // 兼容：既保留原路径，又保留“剥离任意第一级目录”的路径
    if (stripped && stripped !== p) return [p, stripped]
    return [p]
  }

  const mergeAgg = (base, cur) => {
    if (!cur) {
      return base
        ? { count: base.count, hasNew: base.hasNew, hasMarked: base.hasMarked, allViewedOrFiltered: base.allViewedOrFiltered }
        : { count: 0, hasNew: false, hasMarked: false, allViewedOrFiltered: true }
    }
    const next = base
      ? { count: base.count, hasNew: base.hasNew, hasMarked: base.hasMarked, allViewedOrFiltered: base.allViewedOrFiltered }
      : { count: 0, hasNew: false, hasMarked: false, allViewedOrFiltered: true }
    next.count += cur.count
    next.hasNew = next.hasNew || cur.hasNew
    next.hasMarked = next.hasMarked || cur.hasMarked
    next.allViewedOrFiltered = next.allViewedOrFiltered && cur.allViewedOrFiltered
    return next
  }

  const problemCountsById = computed(() => {
    const out = new Map()

    const nodes = Array.isArray(codeMapData.value?.nodes) ? codeMapData.value.nodes : []
    const fnCountByKey = new Map()
    const fileCountByPath = new Map()

    for (const n of nodes) {
      if (!n) continue
      const problemsCount = Array.isArray(n.problems) ? n.problems.length : 0
      if (problemsCount <= 0) continue

      if (n.type === 'function' || n.type === 'fpga_module') {
        const fpList = pathVariants(n.file_path)
        const name = String(n.name || '').trim()
        for (const fp of fpList) {
          if (fp && name) fnCountByKey.set(`${fp}::${name}`, problemsCount)
          if (fp) fileCountByPath.set(fp, (fileCountByPath.get(fp) || 0) + problemsCount)
        }
      } else if (n.type === 'file' || n.type === 'fpga_file') {
        const fpList = pathVariants(n.file_path)
        for (const fp of fpList) {
          if (fp) fileCountByPath.set(fp, (fileCountByPath.get(fp) || 0) + problemsCount)
        }
      }
    }

    const walk = (treeNode, ctx) => {
      if (!treeNode) return 0

      if (treeNode.type === 'function') {
        const filePath = String(ctx?.filePath || '').replace(/\\/g, '/').trim()
        const fnName = String(treeNode.new_label || treeNode.old_label || '').trim()
        let c = 0
        if (filePath && fnName) {
          const fpList = pathVariants(filePath)
          for (const fp of fpList) c = Math.max(c, fnCountByKey.get(`${fp}::${fnName}`) || 0)
        }
        out.set(treeNode.id, c)
        return c
      }

      if (treeNode.type === 'file') {
        const filePath = String(treeNode.new_path || treeNode.old_path || '').replace(/\\/g, '/').trim()
        let sumChildren = 0
        for (const ch of treeNode.children || []) sumChildren += walk(ch, { filePath })

        // 关键：当文件节点下已经挂了 function 子节点时，子节点统计已覆盖函数问题数；
        // 再叠加 fileCountByPath 会把同一批函数问题重复计数。
        let sum = sumChildren
        if (sumChildren <= 0 && filePath) {
          const fpList = pathVariants(filePath)
          for (const fp of fpList) sum += fileCountByPath.get(fp) || 0
        }

        out.set(treeNode.id, sum)
        return sum
      }

      let sum = 0
      for (const ch of treeNode.children || []) sum += walk(ch, ctx)
      out.set(treeNode.id, sum)
      return sum
    }

    for (const r of oldTreeData.value || []) walk(r, null)
    return out
  })

  const functionStartLineByKey = computed(() => {
    const map = new Map()
    const nodes = Array.isArray(codeMapData.value?.nodes) ? codeMapData.value.nodes : []
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
    for (const n of nodes) {
      if (!n) continue
      if (n.type !== 'function' && n.type !== 'fpga_module') continue
      const name = normName(n.name)
      const st = Number(n.start_line)
      if (!name) continue
      if (!Number.isFinite(st)) continue

      const fps = pathVariants(n.file_path)
      for (const fp of fps) {
        if (!fp) continue
        map.set(`${fp}::${name}`, st)
      }
    }
    return map
  })

  const problemBadgeTypesById = computed(() => {
    const out = new Map()

    const nodes = Array.isArray(codeMapData.value?.nodes) ? codeMapData.value.nodes : []
    const fnAggByKey = new Map()
    const fileAggByPath = new Map()

    const aggToType = (agg) => {
      if (!agg || !agg.count) return ''
      if (agg.hasMarked) return 'primary'
      if (agg.hasNew) return 'success'
      if (agg.allViewedOrFiltered) return 'info'
      return 'danger'
    }

    for (const n of nodes) {
      if (!n) continue
      const problems = Array.isArray(n.problems) ? n.problems : []
      if (!problems.length) continue

      let hasNew = false
      let hasMarked = false
      let allViewedOrFiltered = true

      for (const p of problems) {
        const st = p?.problem_status ?? p?.problems_status ?? 1
        if (st === 1) {
          hasNew = true
          allViewedOrFiltered = false
        } else if (st === 4) {
          hasMarked = true
          allViewedOrFiltered = false
        } else if (st !== 2 && st !== 3) {
          allViewedOrFiltered = false
        }
      }

      const curAgg = { count: problems.length, hasNew, hasMarked, allViewedOrFiltered }
      const fpList = pathVariants(n.file_path)

      if (n.type === 'function' || n.type === 'fpga_module') {
        const name = String(n.name || '').trim()
        for (const fp of fpList) {
          if (fp && name) fnAggByKey.set(`${fp}::${name}`, curAgg)
          if (fp) fileAggByPath.set(fp, mergeAgg(fileAggByPath.get(fp), curAgg))
        }
      } else if (n.type === 'file' || n.type === 'fpga_file') {
        for (const fp of fpList) {
          if (fp) fileAggByPath.set(fp, mergeAgg(fileAggByPath.get(fp), curAgg))
        }
      }
    }

    const walk = (treeNode, ctx) => {
      if (!treeNode) return { count: 0, type: '' }

      if (treeNode.type === 'function') {
        const filePath = String(ctx?.filePath || '').replace(/\\/g, '/').trim()
        const fnName = String(treeNode.new_label || treeNode.old_label || '').trim()
        let agg = null
        if (filePath && fnName) {
          const fpList = pathVariants(filePath)
          for (const fp of fpList) {
            const a = fnAggByKey.get(`${fp}::${fnName}`)
            if (a && (!agg || a.count > agg.count)) agg = a
          }
        }
        const t = aggToType(agg)
        if (t) out.set(treeNode.id, t)
        return { count: agg?.count || 0, type: t }
      }

      if (treeNode.type === 'file') {
        const filePath = String(treeNode.new_path || treeNode.old_path || '').replace(/\\/g, '/').trim()
        let merged = { count: 0, hasNew: false, hasMarked: false, allViewedOrFiltered: true }
        for (const ch of treeNode.children || []) {
          const childAgg = walk(ch, { filePath })
          if (childAgg.count > 0) {
            merged.count += childAgg.count
            if (childAgg.type === 'success') merged.hasNew = true
            else if (childAgg.type === 'primary') merged.hasMarked = true
            else if (childAgg.type === 'danger') merged.allViewedOrFiltered = false
          }
        }

        // 同上：如果子节点已有统计（通常是 function 节点），就不要再叠加 fileAggByPath，避免重复。
        if (merged.count <= 0 && filePath) {
          let ownAgg = null
          const fpList = pathVariants(filePath)
          for (const fp of fpList) ownAgg = mergeAgg(ownAgg, fileAggByPath.get(fp))
          if (ownAgg) merged = mergeAgg(merged, ownAgg)
        }

        const t = aggToType(merged)
        if (t) out.set(treeNode.id, t)
        return { count: merged.count, type: t }
      }

      let merged = { count: 0, hasNew: false, hasMarked: false, allViewedOrFiltered: true }
      for (const ch of treeNode.children || []) {
        const childAgg = walk(ch, ctx)
        if (childAgg.count > 0) {
          merged.count += childAgg.count
          if (childAgg.type === 'success') merged.hasNew = true
          else if (childAgg.type === 'primary') merged.hasMarked = true
          else if (childAgg.type === 'danger') merged.allViewedOrFiltered = false
        }
      }
      const t = aggToType(merged)
      if (t) out.set(treeNode.id, t)
      return { count: merged.count, type: t }
    }

    for (const r of oldTreeData.value || []) walk(r, null)
    return out
  })

  return { problemCountsById, problemBadgeTypesById, functionStartLineByKey }
}
