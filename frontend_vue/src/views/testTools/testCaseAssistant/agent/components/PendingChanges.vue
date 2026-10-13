<template>
  <div class="pending-changes" v-if="hasPending">
    <div class="panel-header">
      <span class="title">待审批变更</span>
      <span class="counter">{{ currentOpIndex + 1 }} / {{ totalOps }}</span>
      <button class="accept-all-btn" @click="$emit('accept-all')">全部接受</button>
      <button class="dismiss-btn" @click="$emit('dismiss')">放弃</button>
    </div>
    <div class="summary" v-if="currentPlan?.summary">{{ currentPlan.summary }}</div>
    <div class="op-list">
      <EditPlanDiff
        v-if="currentOp"
        :op="currentOp"
        @accept="$emit('accept')"
        @skip="$emit('skip')"
      />
    </div>
    <div class="progress-bar">
      <div class="progress-fill" :style="{ width: progressPct + '%' }"></div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import EditPlanDiff from './EditPlanDiff.vue'

const props = defineProps({
  hasPending: Boolean,
  currentPlan: Object,
  currentOp: Object,
  currentOpIndex: Number,
  totalOps: Number,
})
defineEmits(['accept', 'skip', 'accept-all', 'dismiss'])

const progressPct = computed(() => {
  if (!props.totalOps) return 0
  return Math.round((props.currentOpIndex / props.totalOps) * 100)
})
</script>

<style scoped>
.pending-changes {
  border-top: 1px solid #e5e7eb;
  background: #fff;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.title {
  font-size: 12px;
  font-weight: 600;
  color: #374151;
}
.counter {
  font-size: 11px;
  color: #9ca3af;
  margin-right: auto;
}
.accept-all-btn, .dismiss-btn {
  padding: 3px 10px;
  border: none;
  border-radius: 4px;
  font-size: 11px;
  cursor: pointer;
}
.accept-all-btn { background: #d1fae5; color: #065f46; }
.accept-all-btn:hover { background: #a7f3d0; }
.dismiss-btn { background: #f3f4f6; color: #6b7280; }
.dismiss-btn:hover { background: #e5e7eb; }
.summary {
  font-size: 12px;
  color: #4b5563;
  padding: 4px 8px;
  background: #f9fafb;
  border-radius: 5px;
  border-left: 3px solid #93c5fd;
}
.progress-bar {
  height: 3px;
  background: #e5e7eb;
  border-radius: 2px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: #3b82f6;
  transition: width 0.2s;
}
</style>
