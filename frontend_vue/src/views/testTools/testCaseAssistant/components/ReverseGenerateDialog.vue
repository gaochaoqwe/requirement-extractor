<template>
  <el-dialog
    v-model="visible"
    title="反向生成 - 根据测试用例生成测试项分析"
    width="860px"
    :close-on-click-modal="false"
    destroy-on-close
    @closed="onClosed"
  >
    <TestCaseReverse ref="reverseRef" />
    <template #footer>
      <el-button @click="visible = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import TestCaseReverse from '@/views/testTools/testCase2testMethod/TestCaseReverse.vue'

const visible = ref(false)
const reverseRef = ref(null)

const open = () => { visible.value = true }

const onClosed = () => {
  // destroy-on-close 会自动重置组件状态，无需手动清理
}

defineExpose({ open })
</script>

<style scoped>
:deep(.el-dialog__body) {
  padding: 0;
  max-height: 70vh;
  overflow-y: auto;
}
:deep(.test-case-reverse-container) {
  padding: 0;
}
:deep(.test-case-reverse-container .header) {
  display: none;
}
</style>
