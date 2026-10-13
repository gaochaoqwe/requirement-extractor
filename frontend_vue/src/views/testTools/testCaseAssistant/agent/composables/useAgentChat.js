import { ref } from 'vue'

const BASE = '/api/test-tools/test-case-assistant'

export function useAgentChat({ getSnapshot, taskId }) {
  const messages = ref([])
  const thinking = ref(false)
  const error = ref(null)

  const addMsg = (role, content, extra = {}) => {
    messages.value.push({ id: Date.now() + Math.random(), role, content, ...extra })
    return messages.value[messages.value.length - 1]
  }

  const sendMessage = async (text, mode = 'step') => {
    if (!text.trim() || thinking.value) return null

    addMsg('user', text)
    thinking.value = true
    error.value = null

    const history = messages.value
      .filter(m => m.role === 'user' || m.role === 'assistant')
      .slice(-10)
      .map(m => ({ role: m.role, content: m.content }))

    const snapshot = getSnapshot ? getSnapshot() : []

    // 先插入一条空的 assistant 消息，后续 token 累积进去
    const assistantMsg = addMsg('assistant', '', { streaming: true, thinkingSteps: [], plan: null })

    let plan = null

    try {
      const response = await fetch(`${BASE}/agent/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task_id: taskId?.value || '',
          message: text,
          mode,
          history,
          sheets_snapshot: snapshot,
        }),
      })

      if (!response.ok) throw new Error(`HTTP ${response.status}`)

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buf = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buf += decoder.decode(value, { stream: true })
        const lines = buf.split('\n')
        buf = lines.pop()

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const raw = line.slice(6).trim()
          if (!raw) continue
          let evt
          try { evt = JSON.parse(raw) } catch { continue }

          if (evt.type === 'token') {
            // 流式追加 token
            assistantMsg.content += evt.data
          } else if (evt.type === 'tool_call') {
            assistantMsg.thinkingSteps.push(`调用工具：${evt.data.name}`)
          } else if (evt.type === 'plan') {
            plan = evt.data
            assistantMsg.plan = plan
          } else if (evt.type === 'error') {
            error.value = evt.data
          }
        }
      }
    } catch (e) {
      error.value = e.message
      assistantMsg.content = assistantMsg.content || `请求失败：${e.message}`
    } finally {
      assistantMsg.streaming = false
      thinking.value = false
    }

    return plan
  }

  const clear = () => { messages.value = [] }

  return { messages, thinking, error, sendMessage, clear }
}
