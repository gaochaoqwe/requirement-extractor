<template>
  <el-dialog
    v-model="visible"
    :title="announcement?.title || '更新公告'"
    width="600px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    @close="handleClose"
  >
    <div v-if="announcement">
      <div style="white-space: pre-wrap; line-height: 1.6;">
        {{ announcement.content }}
      </div>
      <div style="margin-top: 12px; color: #909399; font-size: 12px;">
        发布时间：{{ formatDate(announcement.publish_at) }}
      </div>

      <div style="margin-top: 16px;">
        <el-checkbox v-model="snoozeThisWeek">本周不再弹出</el-checkbox>
      </div>
    </div>

    <template #footer>
      <el-button @click="handleConfirm">我知道了</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { snoozeAnnouncementWeek } from '@/api/maintenance'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  announcement: { type: Object, default: null }
})

const emit = defineEmits(['update:modelValue', 'closed'])

const snoozeThisWeek = ref(false)

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v)
})

watch(
  () => visible.value,
  (v) => {
    if (v) snoozeThisWeek.value = false
  }
)

function formatDate(value) {
  try {
    const d = new Date(value)
    return d.toLocaleString()
  } catch (e) {
    return String(value)
  }
}

async function handleConfirm() {
  try {
    if (snoozeThisWeek.value && props.announcement?.id) {
      await snoozeAnnouncementWeek(props.announcement.id)
    }
  } finally {
    visible.value = false
    emit('closed')
  }
}

function handleClose() {
  emit('closed')
}
</script>
