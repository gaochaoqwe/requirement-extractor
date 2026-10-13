<template>
  <div>
    <!-- 移除了多余的"一键AI审查"按钮，只保留结果显示 -->
    <div v-if="reviewResult">
      <h4>审查结果：</h4>
      <pre>{{ reviewResult }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
const props = defineProps({
  documentIds: Array,
  apiService: Object,
});
const emits = defineEmits(['review-completed']);
const loading = ref(false);
const reviewResult = ref('');

async function review() {
  loading.value = true;
  // 假设apiService.reviewDocuments存在
  try {
    const res = await props.apiService.reviewDocuments(props.documentIds);
    reviewResult.value = res.result || JSON.stringify(res);
    emits('review-completed', res);
  } catch (e) {
    reviewResult.value = '审查失败';
  } finally {
    loading.value = false;
  }
}
</script>
