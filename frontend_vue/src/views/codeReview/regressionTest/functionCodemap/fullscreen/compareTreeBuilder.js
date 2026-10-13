export function buildCompareTreeState(items) {
  const list = Array.isArray(items) ? items : []

  const pairIdByKey = new Map()
  const funcRowIdByPairId = new Map()
  const changeTypeByPairId = new Map()
  const fileIdByPairId = new Map()

  const dirMap = new Map()
  const fileMap = new Map()

  function normPath(p) {
    return String(p || '').replace(/\\/g, '/').trim()
  }

  function isTreeSortDebugEnabled() {
    try {
      return String(localStorage.getItem('codemapTreeSortDebug') || '') === '1'
    } catch {
      return false
    }
  }

  function splitPath(p) {
    return normPath(p)
      .replace(/^\.(\/)+/, '')
      .replace(/^\/+/, '')
      .split('/')
      .filter(Boolean)
  }

  function looksLikeVersionFolder(seg) {
    return /^v?\d+(?:\.\d+)+$/i.test(seg)
  }

  function buildRootPrefixGetter() {
    const count = (m, seg) => {
      if (!seg) return
      m.set(seg, (m.get(seg) || 0) + 1)
    }

    const oldTop = new Map()
    const newTop = new Map()

    list.forEach((it) => {
      const o = splitPath(it?.old?.file_path)
      const n = splitPath(it?.new?.file_path)
      if (o.length) count(oldTop, o[0])
      if (n.length) count(newTop, n[0])
    })

    const pickTop = (m) => {
      let best = null
      let bestCnt = 0
      for (const [k, v] of m.entries()) {
        if (v > bestCnt) {
          best = k
          bestCnt = v
        }
      }
      const total = Array.from(m.values()).reduce((a, b) => a + b, 0)
      if (!best || total === 0) return null
      if (bestCnt / total < 0.6) return null
      return best
    }

    return { oldRoot: pickTop(oldTop), newRoot: pickTop(newTop) }
  }

  const { oldRoot, newRoot } = buildRootPrefixGetter()

  // 关键：避免“二次剥离”。后端函数扫描阶段可能已剥离过第一级目录，
  // 这时前端再剥离会把 src/ 之类真实目录当成顶层根剥掉，导致子目录上浮。
  // 规则：只有当 old/new 的顶层目录不同（例如 v1.00.00 vs v1.01.01，或任意不同命名）时才剥离。
  const shouldStripTopRoot = Boolean(oldRoot && newRoot && oldRoot !== newRoot)

  function normalizeFileKey(oldPath, newPath) {
    const oRaw = splitPath(oldPath)
    const nRaw = splitPath(newPath)

    const stripRoot = (arr, root) => {
      if (!root || !shouldStripTopRoot) return arr
      if (arr[0] === root) return arr.slice(1)
      return arr
    }

    const o = stripRoot(oRaw, oldRoot)
    const n = stripRoot(nRaw, newRoot)

    const suffix = []
    for (let i = 1; i <= Math.min(o.length, n.length); i++) {
      const os = o[o.length - i]
      const ns = n[n.length - i]
      if (os !== ns) break
      suffix.unshift(os)
    }
    if (suffix.length > 0) return suffix.join('/')

    const pick = (arr) => {
      if (arr.length <= 1) return arr.join('/')
      if (looksLikeVersionFolder(arr[0])) return arr.slice(1).join('/')
      return arr.join('/')
    }

    return pick(o) || pick(n) || '未知文件'
  }

  function ensureDirNode(dirPath) {
    const p = dirPath || ''
    const id = p ? `dir:${p}` : 'dir:__root__'
    if (!dirMap.has(id)) {
      dirMap.set(id, {
        id,
        label: p ? p.split('/').slice(-1)[0] : '',
        type: 'dir',
        old_missing: true,
        new_missing: true,
        children: []
      })
    }
    return dirMap.get(id)
  }

  function ensureFileNode(fileKey) {
    const key = fileKey || '未知文件'
    if (!fileMap.has(key)) {
      const parts = String(key).split('/').filter(Boolean)
      const fileLabel = parts.length ? parts[parts.length - 1] : String(key)
      fileMap.set(key, {
        id: `file:${key}`,
        label: fileLabel,
        type: 'file',
        old_path: '',
        new_path: '',
        old_missing: true,
        new_missing: true,
        children: []
      })
    }
    return fileMap.get(key)
  }

  function attachFileToDirs(fileKey, fileNode) {
    const parts = String(fileKey || '').split('/').filter(Boolean)
    const dirs = parts.slice(0, -1)

    let parent = null
    let curPath = ''
    for (const seg of dirs) {
      curPath = curPath ? `${curPath}/${seg}` : seg
      const dirNode = ensureDirNode(curPath)
      if (parent) {
        if (!(parent.children || []).some((c) => c.id === dirNode.id)) parent.children.push(dirNode)
      }
      parent = dirNode
    }

    const rootNode = ensureDirNode('')
    if (!dirs.length) {
      if (!(rootNode.children || []).some((c) => c.id === fileNode.id)) rootNode.children.push(fileNode)
      return
    }

    const topDir = ensureDirNode(dirs[0])
    if (!(rootNode.children || []).some((c) => c.id === topDir.id)) rootNode.children.push(topDir)

    const lastDirPath = dirs.join('/')
    const lastDir = ensureDirNode(lastDirPath)
    if (!(lastDir.children || []).some((c) => c.id === fileNode.id)) lastDir.children.push(fileNode)
  }

  function markAncestorsPresent(fileKey, side) {
    const parts = String(fileKey || '').split('/').filter(Boolean)
    const dirs = parts.slice(0, -1)

    if (side === 'old') ensureDirNode('').old_missing = false
    else ensureDirNode('').new_missing = false

    let curPath = ''
    for (const seg of dirs) {
      curPath = curPath ? `${curPath}/${seg}` : seg
      const dn = ensureDirNode(curPath)
      if (side === 'old') dn.old_missing = false
      else dn.new_missing = false
    }
  }

  function ensureFuncNode(fileNode, fileKey, functionKey, changeType) {
    const id = `func:${fileKey}:${functionKey}`
    let node = (fileNode.children || []).find((c) => c.id === id)
    if (!node) {
      node = {
        id,
        type: 'function',
        change_type: changeType,
        function_key: functionKey,
        old_start_line: null,
        new_start_line: null,
        sort_line: null,
        old_pair_id: null,
        new_pair_id: null,
        old_label: '',
        new_label: '',
        old_missing: true,
        new_missing: true
      }
      fileNode.children.push(node)
    } else {
      const rank = (t) => (t === 'new' ? 3 : t === 'deleted' ? 3 : t === 'modified' ? 2 : 1)
      if (rank(changeType) > rank(node.change_type)) node.change_type = changeType
    }
    return node
  }

  list.forEach((it) => {
    const pairId = it?.pair_id
    const oldBrief = it?.old
    const newBrief = it?.new
    const changeType = it?.change_type

    if (pairId && changeType) {
      changeTypeByPairId.set(pairId, changeType)
    }

    const fileKey = normalizeFileKey(oldBrief?.file_path, newBrief?.file_path)
    const fileNode = ensureFileNode(fileKey)
    if (oldBrief?.file_path && !fileNode.old_path) fileNode.old_path = String(oldBrief.file_path).replace(/\\/g, '/')
    if (newBrief?.file_path && !fileNode.new_path) fileNode.new_path = String(newBrief.file_path).replace(/\\/g, '/')
    attachFileToDirs(fileKey, fileNode)

    if (pairId) fileIdByPairId.set(pairId, fileNode.id)

    if (oldBrief?.file_path) {
      fileNode.old_missing = false
      markAncestorsPresent(fileKey, 'old')
    }
    if (newBrief?.file_path) {
      fileNode.new_missing = false
      markAncestorsPresent(fileKey, 'new')
    }

    const oldFn = oldBrief?.function_name ? String(oldBrief.function_name) : ''
    const newFn = newBrief?.function_name ? String(newBrief.function_name) : ''
    const functionKey = (newFn || oldFn || '').trim() || `pair_${pairId}`

    const funcNode = ensureFuncNode(fileNode, fileKey, functionKey, changeType)

    if (oldFn) {
      funcNode.old_label = oldFn
      funcNode.old_missing = false
      funcNode.old_pair_id = pairId
      {
        const sl = Number(oldBrief?.start_line)
        if (Number.isFinite(sl) && sl > 0) funcNode.old_start_line = sl
      }
      pairIdByKey.set(`old:${oldBrief.file_path}:${oldFn}`, pairId)
      funcRowIdByPairId.set(pairId, funcNode.id)
    }
    if (newFn) {
      funcNode.new_label = newFn
      funcNode.new_missing = false
      funcNode.new_pair_id = pairId
      {
        const sl = Number(newBrief?.start_line)
        if (Number.isFinite(sl) && sl > 0) funcNode.new_start_line = sl
      }
      pairIdByKey.set(`new:${newBrief.file_path}:${newFn}`, pairId)
      funcRowIdByPairId.set(pairId, funcNode.id)
    }

    const cand =
      (Number.isFinite(Number(funcNode.new_start_line)) && Number(funcNode.new_start_line) > 0
        ? Number(funcNode.new_start_line)
        : null) ??
      (Number.isFinite(Number(funcNode.old_start_line)) && Number(funcNode.old_start_line) > 0
        ? Number(funcNode.old_start_line)
        : null)
    funcNode.sort_line = cand
  })

  for (const f of fileMap.values()) {
    f.children = (f.children || []).sort((a, b) => {
      const sa = Number.isFinite(Number(a.sort_line)) ? Number(a.sort_line) : null
      const sb = Number.isFinite(Number(b.sort_line)) ? Number(b.sort_line) : null
      if (sa != null && sb != null) return sa - sb
      if (sa != null) return -1
      if (sb != null) return 1
      const la = a.new_label || a.old_label || ''
      const lb = b.new_label || b.old_label || ''
      return la.localeCompare(lb)
    })

    try {
      if (isTreeSortDebugEnabled()) {
        const p = normPath(f.new_path || f.old_path || '')
        if (p.endsWith('core/image.cpp') || p === 'core/image.cpp') {
          // eslint-disable-next-line no-console
          console.warn('[tree-sort]', {
            file: p,
            children: (f.children || []).map((x) => ({
              label: x.new_label || x.old_label || '',
              new_start_line: x.new_start_line,
              old_start_line: x.old_start_line,
              sort_line: x.sort_line
            }))
          })
        }
      }
    } catch {}
  }

  const sortTree = (nodes) => {
    const arr = (nodes || []).slice()
    arr.sort((a, b) => {
      const ta = a.type === 'dir' ? 0 : a.type === 'file' ? 1 : 2
      const tb = b.type === 'dir' ? 0 : b.type === 'file' ? 1 : 2
      if (ta !== tb) return ta - tb
      return String(a.label || '').localeCompare(String(b.label || ''))
    })
    for (const n of arr) {
      if (n.type === 'dir') n.children = sortTree(n.children || [])
    }
    return arr
  }

  const root = ensureDirNode('')
  const merged = sortTree(root.children || [])

  return {
    tree: merged,
    pairIdByKey,
    funcRowIdByPairId,
    changeTypeByPairId,
    fileIdByPairId
  }
}
