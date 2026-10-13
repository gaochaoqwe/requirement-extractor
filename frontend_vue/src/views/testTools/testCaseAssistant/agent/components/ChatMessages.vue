<template>
  <div class="chat-messages" ref="scrollEl">
    <div v-if="messages.length === 0" class="empty-hint">
      <span>描述你想对表格做什么，AI 会帮你完成</span>
    </div>

    <div v-for="msg in messages" :key="msg.id" :class="['msg', msg.role]">
      <div class="bubble">
        <div v-if="msg.thinkingSteps?.length" class="thinking-steps">
          <span v-for="(step, i) in msg.thinkingSteps" :key="i" class="step">{{ step }}</span>
        </div>

        <div v-if="msg.role === 'user'" class="user-content">{{ msg.content }}</div>
        <div
          v-else
          class="md-content"
          v-html="renderMd(msg.content, msg.streaming)"
        ></div>

        <div v-if="msg.plan" class="plan-badge" @click="$emit('show-plan', msg.plan)">
          <span class="badge-icon">📋</span>
          <span>{{ msg.plan.summary || '查看编辑计划' }}</span>
        </div>
      </div>
    </div>

    <div v-if="thinking && !hasStreamingMsg" class="msg assistant">
      <div class="bubble thinking">
        <span class="dot"></span><span class="dot"></span><span class="dot"></span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { marked } from 'marked'

marked.setOptions({ breaks: true, gfm: true })

const props = defineProps({
  messages: { type: Array, default: () => [] },
  thinking: { type: Boolean, default: false },
})
defineEmits(['show-plan'])

const scrollEl = ref(null)

const hasStreamingMsg = computed(() =>
  props.messages.some(m => m.streaming)
)

const renderMd = (text, streaming) => {
  if (!text) return streaming ? '<span class="cursor"></span>' : ''
  const html = marked.parse(text)
  return streaming ? html + '<span class="cursor"></span>' : html
}

watch(
  () => [props.messages.map(m => m.content).join(''), props.thinking],
  () => { nextTick(() => { if (scrollEl.value) scrollEl.value.scrollTop = scrollEl.value.scrollHeight }) }
)
</script>

<style scoped>
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.empty-hint {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
  font-size: 13px;
}
.msg { display: flex; }
.msg.user { justify-content: flex-end; }
.msg.assistant { justify-content: flex-start; }
.bubble {
  max-width: 90%;
  padding: 8px 12px;
  border-radius: 10px;
  font-size: 13px;
  line-height: 1.6;
  word-break: break-word;
}
.msg.user .bubble {
  background: #3b82f6;
  color: #fff;
  border-radius: 10px 10px 2px 10px;
}
.msg.assistant .bubble {
  background: #f3f4f6;
  color: #1f2937;
  border-radius: 10px 10px 10px 2px;
}
.user-content { white-space: pre-wrap; }

/* markdown 渲染区域 */
.md-content :deep(p)          { margin: 0 0 6px; }
.md-content :deep(p:last-child) { margin-bottom: 0; }
.md-content :deep(ul),
.md-content :deep(ol)          { margin: 4px 0 4px 18px; padding: 0; }
.md-content :deep(li)          { margin: 2px 0; }
.md-content :deep(code)        { background: #e5e7eb; padding: 1px 5px; border-radius: 3px; font-size: 12px; }
.md-content :deep(pre)         { background: #1f2937; color: #f9fafb; padding: 10px 12px; border-radius: 6px; overflow-x: auto; margin: 6px 0; }
.md-content :deep(pre code)    { background: none; padding: 0; color: inherit; font-size: 12px; }
.md-content :deep(h1),
.md-content :deep(h2),
.md-content :deep(h3)          { font-weight: 600; margin: 6px 0 4px; }
.md-content :deep(h1)          { font-size: 15px; }
.md-content :deep(h2)          { font-size: 14px; }
.md-content :deep(h3)          { font-size: 13px; }
.md-content :deep(blockquote)  { border-left: 3px solid #d1d5db; margin: 4px 0; padding-left: 10px; color: #6b7280; }
.md-content :deep(table)       { border-collapse: collapse; width: 100%; margin: 6px 0; font-size: 12px; }
.md-content :deep(th),
.md-content :deep(td)          { border: 1px solid #e5e7eb; padding: 4px 8px; }
.md-content :deep(th)          { background: #f9fafb; font-weight: 600; }
.md-content :deep(a)           { color: #3b82f6; text-decoration: underline; }

/* 流式光标 */
.md-content :deep(.cursor) {
  display: inline-block;
  width: 2px;
  height: 14px;
  background: #3b82f6;
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: blink 0.8s step-end infinite;
}
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }

.thinking-steps { margin-bottom: 6px; display: flex; flex-wrap: wrap; gap: 4px; }
.step {
  font-size: 11px; color: #6b7280; background: #e5e7eb;
  padding: 2px 6px; border-radius: 4px;
}
.plan-badge {
  margin-top: 8px; display: flex; align-items: center; gap: 6px;
  background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 6px;
  padding: 5px 10px; cursor: pointer; font-size: 12px; color: #1d4ed8;
}
.plan-badge:hover { background: #dbeafe; }
.badge-icon { font-size: 14px; }
.thinking { display: flex; gap: 4px; align-items: center; padding: 12px 16px; }
.dot {
  width: 7px; height: 7px; background: #9ca3af; border-radius: 50%;
  animation: bounce 1.2s infinite;
}
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); }
  40% { transform: translateY(-6px); }
}
</style>
