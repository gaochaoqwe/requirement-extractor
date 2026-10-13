export function useFileContent({ taskId, axios, selectedFileKey, oldFileText, newFileText, oldTreeData }) {
  function isFileContentDebugEnabled() {
    try {
      return String(localStorage.getItem('codemapFileContentDebug') || '') === '1'
    } catch {
      return false
    }
  }

  function debugProbeContent(tag, path, text) {
    try {
      if (!isFileContentDebugEnabled()) return
      const p = String(path || '').replace(/\\/g, '/').trim()
      if (!(p.endsWith('core/image.cpp') || p === 'core/image.cpp')) return
      const s = String(text || '')
      const needle = 'Image::Image(int w, int h)'
      const lines = s.split('\n')
      let foundAt = -1
      for (let i = 0; i < lines.length; i++) {
        if (String(lines[i]).includes(needle)) {
          foundAt = i + 1
          break
        }
      }
      // eslint-disable-next-line no-console
      console.warn('[file-content]', {
        tag,
        path: p,
        length: s.length,
        lines: lines.length,
        hasNeedle: foundAt > 0,
        foundLine: foundAt,
        near: foundAt > 0 ? lines.slice(Math.max(0, foundAt - 3), Math.min(lines.length, foundAt + 2)) : lines.slice(0, 12)
      })
    } catch {}
  }

  function findFileNodeById(fileId) {
    const targetId = String(fileId || '')
    if (!targetId) return null
    const stack = [].concat(oldTreeData.value || [])
    while (stack.length) {
      const n = stack.shift()
      if (!n) continue
      if (n.id === targetId && n.type === 'file') return n
      for (const c of n.children || []) stack.push(c)
    }
    return null
  }

  async function loadFileTextsByNode(fileNode) {
    const oldPath = String(fileNode?.old_path || '')
    const newPath = String(fileNode?.new_path || '')
    selectedFileKey.value = String(fileNode?.id || '').replace(/^file:/, '')
    oldFileText.value = ''
    newFileText.value = ''

    const loadOne = async (version, path) => {
      if (!taskId.value || !path) return ''
      try {
        const res = await axios.get(`/api/codeReview/regressionTest/regression/file/${taskId.value}`, {
          params: { version, path }
        })
        return String(res.data?.content || '')
      } catch {
        return ''
      }
    }

    const [o, n] = await Promise.all([loadOne('old', oldPath), loadOne('new', newPath)])
    oldFileText.value = o
    newFileText.value = n

    debugProbeContent('old', oldPath, o)
    debugProbeContent('new', newPath, n)
  }

  async function selectFile(fileId) {
    const node = findFileNodeById(fileId)
    if (!node) return
    await loadFileTextsByNode(node)
  }

  return { findFileNodeById, loadFileTextsByNode, selectFile }
}
