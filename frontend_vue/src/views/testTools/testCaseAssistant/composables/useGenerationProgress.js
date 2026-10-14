import { ref, computed, onBeforeUnmount } from 'vue'
import request from '@/api/request'

const POLL_INTERVAL = 1000

const buildSessionId = () => {
  try {
    if (window?.crypto?.randomUUID) return window.crypto.randomUUID()
  } catch (_) {
    // ignore
  }
  return `gen-${Date.now()}-${Math.random().toString(16).slice(2, 10)}`
}

/**
 * 长耗时生成任务的进度轮询（上传文件 → 后端逐条 AI 生成 → 导出 Excel）。
 *
 * 用法：
 *   const gp = useGenerationProgress('/test-tools/test-case-assistant/xxx/progress')
 *   const sid = gp.start()          // 生成 session_id 并开始轮询
 *   formData.append('session_id', sid)
 *   ... await request.post(...)
 *   await gp.poll()                 // 收尾拉一次最终进度
 *   gp.markDone({ message, current, total })   // 成功后置为 100%
 *   gp.stop()
 *
 * @param {string} progressUrl 进度查询接口前缀（不含 session_id），需与后端 session_id 参数配套
 */
export function useGenerationProgress(progressUrl, options = {}) {
  const { startMessage = '正在上传 Excel 文件…' } = options

  const sessionId = ref('')
  const progress = ref(null)
  const items = ref([])
  const elapsedSeconds = ref(0)
  const active = ref(false)

  let pollTimer = null
  let elapsedTimer = null

  const percent = computed(() => {
    const value = Number(progress.value?.percent)
    if (!Number.isFinite(value)) return active.value ? 1 : 0
    return Math.max(0, Math.min(100, Math.round(value)))
  })

  const status = computed(() => {
    const s = progress.value?.status
    if (s === 'error') return 'exception'
    if (s === 'done') return 'success'
    return ''
  })

  const message = computed(() => progress.value?.message || (active.value ? '正在生成，请稍候…' : ''))

  const current = computed(() => Number(progress.value?.current) || 0)
  const total = computed(() => Number(progress.value?.total) || 0)

  const stop = () => {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
    if (elapsedTimer) {
      clearInterval(elapsedTimer)
      elapsedTimer = null
    }
  }

  const applyProgress = (data) => {
    if (!data || typeof data !== 'object') return
    if (data.status === 'not_found') return
    progress.value = { ...(progress.value || {}), ...data }
    if (Array.isArray(data.items)) items.value = data.items
  }

  const poll = async () => {
    const sid = sessionId.value
    if (!sid) return
    try {
      const data = await request.get(`${progressUrl}/${encodeURIComponent(sid)}`)
      applyProgress(data)
    } catch (_) {
      // 轮询失败不打断主流程
    }
  }

  /** 生成 session_id、重置状态并开始轮询；返回需要随表单提交的 session_id */
  const start = () => {
    stop()
    sessionId.value = buildSessionId()
    items.value = []
    elapsedSeconds.value = 0
    active.value = true
    progress.value = {
      session_id: sessionId.value,
      status: 'running',
      percent: 1,
      message: startMessage,
      current: 0,
      total: 0,
    }
    elapsedTimer = setInterval(() => {
      elapsedSeconds.value += 1
    }, 1000)
    pollTimer = setInterval(poll, POLL_INTERVAL)
    poll()
    return sessionId.value
  }

  /** 成功收尾：把进度条置为 100% 并展示总结文案 */
  const markDone = (payload = {}) => {
    progress.value = { ...(progress.value || {}), status: 'done', percent: 100, ...payload }
  }

  const reset = () => {
    stop()
    sessionId.value = ''
    progress.value = null
    items.value = []
    elapsedSeconds.value = 0
    active.value = false
  }

  onBeforeUnmount(stop)

  return {
    sessionId,
    progress,
    items,
    elapsedSeconds,
    active,
    percent,
    status,
    message,
    current,
    total,
    start,
    stop,
    poll,
    markDone,
    reset,
  }
}
