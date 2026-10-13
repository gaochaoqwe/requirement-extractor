<template>
  <div class="download-container">
    <el-button 
      type="success" 
      :loading="downloading" 
      @click="downloadReport"
    >
      <el-icon><Download /></el-icon>
      下载回归测试审查报告
    </el-button>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import { Download } from '@element-plus/icons-vue';
import axios from 'axios';

const props = defineProps({
  taskId: {
    type: String,
    required: true
  }
});

const downloading = ref(false);

async function downloadReport() {
  if (!props.taskId) {
    ElMessage.error('任务ID不存在，无法下载报告');
    return;
  }

  downloading.value = true;
  
  try {
    const response = await axios.get(`/api/codeReview/regression/download_report/${props.taskId}`, {
      responseType: 'blob'
    });
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    
    // 从响应头获取文件名，如果没有则使用默认名称
    const contentDisposition = response.headers['content-disposition'];
    let filename = '回归测试代码审查报告.docx';
    
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
      if (filenameMatch && filenameMatch[1]) {
        filename = filenameMatch[1].replace(/['"]/g, '');
      }
    }
    
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    
    ElMessage.success('报告下载成功');
  } catch (error) {
    console.error('下载报告时出错:', error);
    ElMessage.error('下载报告失败: ' + (error.message || '未知错误'));
  } finally {
    downloading.value = false;
  }
}
</script>

<style scoped>
.download-container {
  display: flex;
  justify-content: center;
  margin: 16px 0;
}
</style> 