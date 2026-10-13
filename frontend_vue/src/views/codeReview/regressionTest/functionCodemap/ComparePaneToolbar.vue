<template>
  <div class="code-pane-toolbar">
    <div class="toolbar-left">
      <el-switch v-model="localDiffMode" inline-prompt active-text="Diff" inactive-text="Raw" />
      <el-switch v-model="localOnlyChanges" :disabled="!localDiffMode" active-text="仅变更" inactive-text="全量" />
      <el-select v-model="localContextLines" :disabled="!localDiffMode || !localOnlyChanges" size="small" style="width: 110px">
        <el-option :value="0" label="上下文 0" />
        <el-option :value="3" label="上下文 3" />
        <el-option :value="5" label="上下文 5" />
        <el-option :value="10" label="上下文 10" />
      </el-select>
    </div>
    <div class="toolbar-actions">
      <el-button size="small" :disabled="!localDiffMode || changeCount === 0" @click="$emit('prev')">上一处</el-button>
      <el-button size="small" :disabled="!localDiffMode || changeCount === 0" @click="$emit('next')">下一处</el-button>
    </div>
    <div v-if="showCounter" class="toolbar-right-hint">{{ localDiffMode ? `变更 ${currentDisplay}` : '' }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  diffMode: { type: Boolean, default: true },
  onlyChanges: { type: Boolean, default: true },
  contextLines: { type: Number, default: 3 },
  changeCount: { type: Number, default: 0 },
  currentCursor: { type: Number, default: 0 },
  showCounter: { type: Boolean, default: false }
})

const emit = defineEmits(['update:diffMode', 'update:onlyChanges', 'update:contextLines', 'prev', 'next'])

const localDiffMode = computed({
  get() {
    return props.diffMode
  },
  set(v) {
    emit('update:diffMode', v)
  }
})

const localOnlyChanges = computed({
  get() {
    return props.onlyChanges
  },
  set(v) {
    emit('update:onlyChanges', v)
  }
})

const localContextLines = computed({
  get() {
    return props.contextLines
  },
  set(v) {
    emit('update:contextLines', v)
  }
})

const currentDisplay = computed(() => {
  if (props.changeCount === 0) return '0/0'
  const n = Math.min(Math.max(props.currentCursor + 1, 1), props.changeCount)
  return `${n}/${props.changeCount}`
})
</script>

<style scoped>
.code-pane-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 8px 10px;
  background: rgba(255, 255, 255, 0.92);
  border-bottom: 1px solid #e4e7ed;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toolbar-right-hint {
  font-size: 12px;
  color: #606266;
}
</style>
