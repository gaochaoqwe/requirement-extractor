<template>
  <div class="upload-panel">
    <div class="upload-column" v-for="item in uploadItems" :key="item.version">
      <div class="upload-header">
        <el-icon><Document /></el-icon>
        <span>{{ item.label }}</span>
      </div>
      <upload-code-file
        :upload-url="item.url"
        :version-type="item.version"
        :accept="item.accept"
        @upload-success="(res) => onSuccess(item.version, res)"
      />
      <div v-if="fileIds[item.version]" class="upload-status success">
        <el-icon><SuccessFilled /></el-icon>
        <span>已上传</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, watch } from 'vue';
import { Document, SuccessFilled } from '@element-plus/icons-vue';
import UploadCodeFile from './upload/UploadCodeFile.vue';

const emits = defineEmits(['uploaded']);

const fileIds = reactive({ old: null, new: null, report: null });

const uploadItems = [
  {
    version: 'old',
    label: '上一版本代码',
    url: '/api/codeReview/regression/upload_file',
    accept: '.zip',
  },
  {
    version: 'new',
    label: '当前版本代码',
    url: '/api/codeReview/regression/upload_file',
    accept: '.zip',
  },
  {
    version: 'report',
    label: '影响域分析报告',
    url: '/api/codeReview/regression/upload_file',
    accept: '.doc,.docx,.pdf,.txt',
  },
];

function onSuccess(version, res) {
  if (res && res.file_id) {
    fileIds[version] = res.file_id;
    emits('uploaded', { ...fileIds });
  }
}

// 监听所有文件是否都已上传
watch(fileIds, (val) => {
  if (val.old && val.new && val.report) {
    emits('uploaded', { ...val });
  }
}, { deep: true });
</script>

<style scoped>
.upload-panel {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
  margin-bottom: 24px;
  width: 100%;
  max-width: 1200px;
  margin-left: auto;
  margin-right: auto;
  padding: 0 16px;
}

.upload-column {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  min-width: 0; /* 防止内容溢出 */
}
.upload-header {
  font-size: 1rem;
  color: #34495e;
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  font-weight: 500;
  width: 100%;
  justify-content: center;
  padding: 0 8px;
}
.upload-header .el-icon {
  margin-right: 6px;
  color: #3498db;
}
.upload-status {
  margin-top: 8px;
  display: flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 4px;
  background-color: #e6f7ff;
  color: #1890ff;
  border: 1px solid #91d5ff;
}
.upload-status .el-icon {
  margin-right: 4px;
}
</style>
