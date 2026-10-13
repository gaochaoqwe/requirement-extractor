export function useResize({
  sidebarWidth,
  treePanelWidth,
  collapsedTreeWidth,
  treesVisible,
  isResizing,
  resizeType,
  startX,
  startWidth
}) {
  function startLeftResize(e) {
    isResizing.value = true
    resizeType.value = 'left'
    startX.value = e.clientX
    startWidth.value = treePanelWidth.value

    document.addEventListener('mousemove', doResize)
    document.addEventListener('mouseup', stopResize)
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
  }

  function startRightResize(e) {
    isResizing.value = true
    resizeType.value = 'right'
    startX.value = e.clientX
    startWidth.value = sidebarWidth.value

    document.addEventListener('mousemove', doResize)
    document.addEventListener('mouseup', stopResize)
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
  }

  function doResize(e) {
    if (!isResizing.value) return

    const deltaX = e.clientX - startX.value

    if (resizeType.value === 'left') {
      const newWidth = startWidth.value + deltaX
      if (newWidth >= 320 && newWidth <= 900) {
        treePanelWidth.value = newWidth
        if (!treesVisible.value) {
          treesVisible.value = true
        }
      }
    } else if (resizeType.value === 'right') {
      const newWidth = startWidth.value - deltaX
      if (newWidth >= 250 && newWidth <= 800) {
        sidebarWidth.value = newWidth
      }
    }
  }

  function stopResize() {
    isResizing.value = false
    resizeType.value = ''
    document.removeEventListener('mousemove', doResize)
    document.removeEventListener('mouseup', stopResize)
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
  }

  function toggleTrees() {
    treesVisible.value = !treesVisible.value
  }

  return {
    startLeftResize,
    startRightResize,
    stopResize,
    doResize,
    toggleTrees
  }
}
