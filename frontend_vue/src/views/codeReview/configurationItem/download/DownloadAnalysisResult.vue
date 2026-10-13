<template>
  <div class="download-btn-row">
    <el-button type="primary" @click="downloadResult" :loading="downloading">下载分析结果</el-button>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const props = defineProps({
  taskId: {
    type: [String, Number],
    required: true
  }
});

const downloading = ref(false);

async function downloadResult() {
  downloading.value = true;
  try {
    const url = `/api/codeReview/download_result/${props.taskId}`;
    window.open(url);
  } finally {
    downloading.value = false;
  }
}
</script>

<style scoped>
.download-btn-row {
  display: flex;
  justify-content: center;
  margin: 20px 0;
}
</style> 