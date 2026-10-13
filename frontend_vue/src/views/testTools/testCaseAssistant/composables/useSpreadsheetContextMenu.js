import { reactive } from 'vue'

export const useSpreadsheetContextMenu = (sheetContainerRef, onAction, onBeforeShow) => {
  const state = reactive({ visible: false, x: 0, y: 0 })
  let lastBeforeShowResult = null

  const hide = () => {
    state.visible = false
  }

  const preventRightMousedown = (evt) => {
    if (evt.button === 2) {
      evt.preventDefault()
      evt.stopPropagation()
    }
  }

  const show = (evt) => {
    evt.preventDefault()
    evt.stopPropagation()
    try {
      if (typeof onBeforeShow === 'function') {
        lastBeforeShowResult = onBeforeShow(evt)
      }
    } catch (e) {
      console.error(e)
    }
    state.x = evt.clientX
    state.y = evt.clientY
    state.visible = true
  }

  const emitAction = (key) => {
    hide()
    if (typeof onAction === 'function') onAction(key)
  }

  const bind = () => {
    if (sheetContainerRef?.value) {
      sheetContainerRef.value.addEventListener('mousedown', preventRightMousedown, true)
      sheetContainerRef.value.addEventListener('contextmenu', show, true)
    }
    window.addEventListener('click', hide)
  }

  const unbind = () => {
    if (sheetContainerRef?.value) {
      sheetContainerRef.value.removeEventListener('mousedown', preventRightMousedown, true)
      sheetContainerRef.value.removeEventListener('contextmenu', show, true)
    }
    window.removeEventListener('click', hide)
  }

  return {
    state,
    bind,
    unbind,
    emitAction,
    hide,
    getLastBeforeShowResult: () => lastBeforeShowResult,
  }
}
