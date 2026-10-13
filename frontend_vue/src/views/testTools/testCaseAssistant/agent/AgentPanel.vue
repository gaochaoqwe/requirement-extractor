<template>
  <div class="agent-panel">
    <div class="panel-titlebar">
      <span class="panel-title">AI 助手</span>
      <button class="clear-btn" @click="clearChat" title="清空对话">清空</button>
      <button class="collapse-btn" @click="$emit('collapse')" title="收起面板">◀</button>
    </div>

    <ChatMessages
      :messages="messages"
      :thinking="thinking"
      @show-plan="onShowPlan"
    />

    <PendingChanges
      v-if="hasPending"
      :hasPending="hasPending"
      :currentPlan="currentPlan"
      :currentOp="currentOp"
      :currentOpIndex="currentOpIndex"
      :totalOps="totalOps"
      @accept="handleAccept"
      @skip="handleSkip"
      @accept-all="handleAcceptAll"
      @dismiss="dismissPlan"
    />

    <AgentInput :thinking="thinking" @send="handleSend" />

    <div v-if="error" class="error-bar">{{ error }}</div>
  </div>
</template>

<script setup>
import ChatMessages from './components/ChatMessages.vue'
import PendingChanges from './components/PendingChanges.vue'
import AgentInput from './components/AgentInput.vue'
import { useAgentChat } from './composables/useAgentChat.js'
import { useEditPlan } from './composables/useEditPlan.js'

const props = defineProps({
  spreadsheet: Object,
  sheetList: Object,
  taskId: [String, Object, null],
  applyOp: Function,
  applyOps: Function,
  getSnapshot: Function,
})
defineEmits(['collapse'])

const { messages, thinking, error, sendMessage, clear: clearChat } = useAgentChat({
  getSnapshot: props.getSnapshot,
  taskId: props.taskId,
})

const {
  currentPlan, hasPending, totalOps, currentOpIndex, currentOp,
  addPlan, acceptCurrentOp, skipCurrentOp, acceptAll, dismissPlan, clear: clearPlans,
} = useEditPlan()

const handleSend = async ({ text, mode }) => {
  const plan = await sendMessage(text, mode)
  if (!plan) return
  if (mode === 'auto') {
    props.applyOps?.(plan.operations)
  } else {
    addPlan(plan)
  }
}

const onShowPlan = (plan) => { addPlan(plan) }
const handleAccept = () => { const op = acceptCurrentOp(); if (op) props.applyOp?.(op) }
const handleSkip = () => { skipCurrentOp() }
const handleAcceptAll = () => { props.applyOps?.(acceptAll()) }
const clear = () => { clearChat(); clearPlans() }
defineExpose({ clear })
</script>

<style scoped>
.agent-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  background: #fff;
  overflow: hidden;
}
.panel-titlebar {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
  gap: 8px;
  flex-shrink: 0;
}
.panel-title { font-size: 13px; font-weight: 600; color: #1f2937; flex: 1; }
.clear-btn, .collapse-btn {
  padding: 3px 8px;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  font-size: 11px;
  background: #fff;
  color: #6b7280;
  cursor: pointer;
}
.clear-btn:hover, .collapse-btn:hover { background: #f3f4f6; }
.error-bar {
  padding: 8px 12px;
  background: #fee2e2;
  color: #b91c1c;
  font-size: 12px;
  border-top: 1px solid #fca5a5;
  flex-shrink: 0;
}
</style>
