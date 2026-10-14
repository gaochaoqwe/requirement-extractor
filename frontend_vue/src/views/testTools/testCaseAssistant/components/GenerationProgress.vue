<template>
  <div v-if="show" class="gen-progress">
    <el-progress
      :percentage="percent"
      :status="status"
      :stroke-width="16"
      :text-inside="true"
    />
    <div class="gen-progress-head">
      <span class="gen-progress-msg">{{ message }}</span>
      <span class="gen-progress-time">已用时 {{ elapsed }} 秒</span>
    </div>
    <div v-if="total > 0" class="gen-progress-sub">
      {{ unit ? `${unit}进度` : '进度' }}：{{ current }} / {{ total }}
      <span v-if="summary">（{{ summary }}）</span>
    </div>
    <div v-if="items.length" class="gen-progress-items">
      <div
        v-for="(item, idx) in items"
        :key="idx"
        class="gen-progress-item"
        :class="{ 'is-warn': !item.ok }"
      >
        <span class="gen-progress-item-icon">{{ item.ok ? '✓' : '!' }}</span>
        <span class="gen-progress-item-name">{{ item.name }}</span>
        <span class="gen-progress-item-detail">{{ item.detail }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  /** useGenerationProgress 返回的 progress 对象 */
  progress: { type: Object, default: null },
  /** useGenerationProgress 返回的 items 明细数组 */
  items: { type: Array, default: () => [] },
  /** 是否正在处理（处理中即使还没有进度也要展示） */
  active: { type: Boolean, default: false },
  /** 已用时（秒） */
  elapsed: { type: Number, default: 0 },
  /** 条目单位，例如「测试项」「行」 */
  unit: { type: String, default: '' },
  /** 附在进度后面的补充说明，例如「已生成 3 条问题单」 */
  summary: { type: String, default: '' },
})

const show = computed(() => props.active || Boolean(props.progress))

const percent = computed(() => {
  const value = Number(props.progress?.percent)
  if (!Number.isFinite(value)) return props.active ? 1 : 0
  return Math.max(0, Math.min(100, Math.round(value)))
})

const status = computed(() => {
  const s = props.progress?.status
  if (s === 'error') return 'exception'
  if (s === 'done') return 'success'
  return ''
})

const message = computed(() => {
  if (props.progress?.message) return props.progress.message
  return props.active ? '正在生成，请稍候…' : ''
})

const current = computed(() => Number(props.progress?.current) || 0)
const total = computed(() => Number(props.progress?.total) || 0)
</script>

<style scoped>
.gen-progress {
  margin-top: 16px;
  padding: 12px 14px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f9fafb;
}

.gen-progress-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 10px;
}

.gen-progress-msg {
  color: #1f2937;
  font-size: 13px;
  font-weight: 600;
  word-break: break-all;
}

.gen-progress-time {
  flex-shrink: 0;
  color: #9ca3af;
  font-size: 12px;
}

.gen-progress-sub {
  margin-top: 6px;
  color: #6b7280;
  font-size: 12px;
}

.gen-progress-items {
  margin-top: 10px;
  max-height: 180px;
  overflow-y: auto;
  border-top: 1px dashed #e5e7eb;
  padding-top: 8px;
}

.gen-progress-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  line-height: 1.8;
  color: #374151;
}

.gen-progress-item-icon {
  width: 14px;
  flex-shrink: 0;
  color: #16a34a;
  font-weight: 700;
}

.gen-progress-item.is-warn .gen-progress-item-icon {
  color: #d97706;
}

.gen-progress-item-name {
  flex-shrink: 0;
  max-width: 45%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.gen-progress-item-detail {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #9ca3af;
}

.gen-progress-item.is-warn .gen-progress-item-detail {
  color: #d97706;
}
</style>
