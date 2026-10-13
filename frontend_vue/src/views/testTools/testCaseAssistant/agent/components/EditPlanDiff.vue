<template>
  <div class="diff-card">
    <div class="diff-header">
      <span class="op-tag" :class="op.op">{{ opLabel }}</span>
      <span class="location">{{ locationText }}</span>
    </div>
    <div class="diff-body">
      <div v-if="op.op === 'set_cell'">
        <div v-if="op.old_value" class="diff-line remove">
          <span class="sign">−</span>
          <span class="val">{{ op.old_value }}</span>
        </div>
        <div class="diff-line add">
          <span class="sign">+</span>
          <span class="val">{{ op.value }}</span>
        </div>
      </div>
      <div v-else-if="op.op === 'insert_row'" class="diff-line add">
        <span class="sign">+</span>
        <span class="val">插入新行：{{ rowPreview }}</span>
      </div>
      <div v-else-if="op.op === 'delete_row'" class="diff-line remove">
        <span class="sign">−</span>
        <span class="val">删除第 {{ op.row + 1 }} 行</span>
      </div>
      <div v-else-if="op.op === 'switch_sheet'" class="diff-line info">
        <span class="sign">→</span>
        <span class="val">切换到 "{{ op.sheet }}"</span>
      </div>
      <div v-else-if="op.op === 'add_sheet'" class="diff-line add">
        <span class="sign">+</span>
        <span class="val">新建 sheet "{{ op.name }}"</span>
      </div>
      <div v-else-if="op.op === 'rename_sheet'" class="diff-line info">
        <span class="sign">→</span>
        <div>
          <div class="diff-line remove"><span class="sign">−</span><span class="val">{{ op.sheet }}</span></div>
          <div class="diff-line add"><span class="sign">+</span><span class="val">{{ op.name }}</span></div>
        </div>
      </div>
      <div v-else-if="op.op === 'delete_sheet'" class="diff-line remove">
        <span class="sign">−</span>
        <span class="val">删除 sheet "{{ op.sheet }}"</span>
      </div>
      <div v-else class="diff-line info">
        <span class="val">{{ JSON.stringify(op) }}</span>
      </div>
    </div>
    <div class="diff-actions">
      <button class="btn accept" @click="$emit('accept')">✓ 接受</button>
      <button class="btn skip" @click="$emit('skip')">✗ 跳过</button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ op: { type: Object, required: true } })
defineEmits(['accept', 'skip'])

const OP_LABELS = {
  set_cell: '修改单元格',
  insert_row: '插入行',
  delete_row: '删除行',
  switch_sheet: '切换 Sheet',
  add_sheet: '新建 Sheet',
  rename_sheet: '重命名 Sheet',
  delete_sheet: '删除 Sheet',
}

const opLabel = computed(() => OP_LABELS[props.op?.op] || props.op?.op)

const locationText = computed(() => {
  const op = props.op
  if (!op) return ''
  if (op.op === 'set_cell') return `${op.sheet} · 第 ${op.row + 1} 行 第 ${op.col + 1} 列`
  if (op.op === 'insert_row') return `${op.sheet} · 第 ${op.after_row + 2} 行`
  if (op.op === 'delete_row') return `${op.sheet} · 第 ${op.row + 1} 行`
  if (op.op === 'switch_sheet') return op.sheet
  if (op.op === 'add_sheet') return op.name
  if (op.op === 'rename_sheet') return `${op.sheet} → ${op.name}`
  if (op.op === 'delete_sheet') return op.sheet
  return ''
})

const rowPreview = computed(() => {
  if (!props.op?.values) return ''
  return Object.values(props.op.values).filter(Boolean).join(' | ').slice(0, 80)
})
</script>

<style scoped>
.diff-card {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
  font-size: 12px;
}
.diff-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}
.op-tag {
  padding: 1px 7px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
}
.op-tag.set_cell   { background: #dbeafe; color: #1d4ed8; }
.op-tag.insert_row { background: #dcfce7; color: #15803d; }
.op-tag.delete_row { background: #fee2e2; color: #b91c1c; }
.op-tag.switch_sheet  { background: #f3e8ff; color: #7c3aed; }
.op-tag.add_sheet     { background: #dcfce7; color: #15803d; }
.op-tag.rename_sheet  { background: #fef9c3; color: #92400e; }
.op-tag.delete_sheet  { background: #fee2e2; color: #b91c1c; }
.location { color: #6b7280; font-size: 11px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.diff-body { padding: 8px 10px; background: #fff; }
.diff-line { display: flex; gap: 6px; padding: 2px 0; align-items: flex-start; }
.sign { font-weight: bold; width: 14px; flex-shrink: 0; margin-top: 1px; }
.diff-line.add    .sign { color: #16a34a; }
.diff-line.remove .sign { color: #dc2626; }
.diff-line.info   .sign { color: #7c3aed; }
.diff-line.remove .val { text-decoration: line-through; color: #9ca3af; }
.diff-line.add    .val { color: #111827; }
.diff-line.info   .val { color: #4b5563; }
.val { word-break: break-word; flex: 1; }
.diff-actions { display: flex; gap: 8px; padding: 8px 10px; border-top: 1px solid #f3f4f6; }
.btn {
  flex: 1; padding: 4px 0; border: none; border-radius: 5px;
  cursor: pointer; font-size: 12px; font-weight: 500; transition: background 0.15s;
}
.btn.accept { background: #dcfce7; color: #15803d; }
.btn.accept:hover { background: #bbf7d0; }
.btn.skip { background: #f3f4f6; color: #6b7280; }
.btn.skip:hover { background: #e5e7eb; }
</style>
