// 键盘快捷键封装：创建可复用的按键处理函数
// 使用示例：
// const handleKeydown = createHandleKeydown(editingCell, {
//   finishEdit, cancelEdit, ctxCopy, ctxCut, ctxPaste, ctxClear, ctxEditCell
// })
export function createHandleKeydown(editingCell, actions) {
  const {
    finishEdit,
    cancelEdit,
    ctxCopy,
    ctxCut,
    ctxPaste,
    ctxClear,
    ctxEditCell,
  } = actions

  return function handleKeydown(e) {
    // 编辑态优先处理回车/ESC
    if (editingCell?.value) {
      if (e.key === 'Enter') { e.preventDefault(); finishEdit && finishEdit() }
      if (e.key === 'Escape') { e.preventDefault(); cancelEdit && cancelEdit() }
      return
    }

    const isCtrl = e.ctrlKey || e.metaKey
    if (isCtrl && e.key.toLowerCase() === 'c') { e.preventDefault(); ctxCopy && ctxCopy() }
    else if (isCtrl && e.key.toLowerCase() === 'x') { e.preventDefault(); ctxCut && ctxCut() }
    else if (isCtrl && e.key.toLowerCase() === 'v') { e.preventDefault(); ctxPaste && ctxPaste() }
    else if (e.key === 'Delete') { e.preventDefault(); ctxClear && ctxClear() }
    else if (e.key === 'Enter') { e.preventDefault(); ctxEditCell && ctxEditCell() }
  }
}
