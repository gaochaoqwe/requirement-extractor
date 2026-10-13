<template>
  <div class="agent-input">
    <div class="mode-bar">
      <span class="mode-label">模式：</span>
      <button :class="['mode-btn', { active: mode === 'step' }]" @click="mode = 'step'">逐步审批</button>
      <button :class="['mode-btn', { active: mode === 'auto' }]" @click="mode = 'auto'">全自动</button>
    </div>
    <div class="input-row">
      <textarea
        ref="textareaRef"
        v-model="text"
        class="input-box"
        :placeholder="inputPlaceholder"
        :disabled="thinking"
        @keydown.enter.exact.prevent="submit"
        @keydown.shift.enter.exact="text += '\n'"
        rows="2"
      ></textarea>
      <button class="send-btn" :disabled="!text.trim() || thinking" @click="submit">
        <span v-if="!thinking">发送</span>
        <span v-else class="sending-dots">...</span>
      </button>
    </div>
    <div class="hint">Enter 发送 · Shift+Enter 换行</div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  thinking: { type: Boolean, default: false },
})
const emit = defineEmits(['send'])

const text = ref('')
const mode = ref('step')
const textareaRef = ref(null)

const inputPlaceholder = '描述你想对表格做什么，例如：在需求分析表第3行后插入一行，填入测试项名称"RS422初始化"...'

const submit = () => {
  const t = text.value.trim()
  if (!t || props.thinking) return
  emit('send', { text: t, mode: mode.value })
  text.value = ''
}
</script>

<style scoped>
.agent-input {
  border-top: 1px solid #e5e7eb;
  padding: 10px;
  background: #fff;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.mode-bar {
  display: flex;
  align-items: center;
  gap: 6px;
}
.mode-label { font-size: 11px; color: #9ca3af; }
.mode-btn {
  padding: 2px 10px;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  font-size: 11px;
  background: #f9fafb;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.15s;
}
.mode-btn.active {
  background: #eff6ff;
  border-color: #93c5fd;
  color: #1d4ed8;
  font-weight: 600;
}
.input-row {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}
.input-box {
  flex: 1;
  resize: none;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 13px;
  line-height: 1.5;
  outline: none;
  font-family: inherit;
  transition: border-color 0.15s;
}
.input-box:focus { border-color: #3b82f6; }
.input-box:disabled { background: #f9fafb; }
.send-btn {
  flex-shrink: 0;
  width: 56px;
  height: 60px;
  border: none;
  border-radius: 8px;
  background: #3b82f6;
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}
.send-btn:hover:not(:disabled) { background: #2563eb; }
.send-btn:disabled { background: #93c5fd; cursor: not-allowed; }
.sending-dots { letter-spacing: 2px; }
.hint { font-size: 11px; color: #d1d5db; }
</style>
