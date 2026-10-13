<template>
  <div class="upload-container">
    <el-upload accept=".docx"
      :action="uploadUrl"
      :show-file-list="false"
      :before-upload="beforeUpload"
      :on-success="handleSuccess"
      :on-error="handleError"
      :http-request="customUpload"
      :data="{ doc_type: docType }"
      drag
    >
      <div class="upload-area">
        <el-icon :size="32" :class="['upload-icon', icon]">
          <component :is="icon" />
        </el-icon>
        <div class="upload-text">
          <p class="title">{{ label }}</p>
          <p class="hint">点击或拖拽文件到此处上传</p>
        </div>
      </div>
    </el-upload>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import axios from 'axios';

const props = defineProps({
  uploadUrl: String,
  label: {
    type: String,
    default: '上传文件'
  },
  icon: {
    type: String,
    default: 'Upload'
  },
  docType: {
    type: String,
    required: true,
    validator: (value) => ['taskBook', 'requirementSpec'].includes(value)
  }
});

const emits = defineEmits(['upload-success', 'upload-success-notify', 'upload-error']);

function beforeUpload(file) {
  const isDocx = file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
  const isDoc = file.type === 'application/msword';
  const isPdf = file.type === 'application/pdf';
  const isText = file.type === 'text/plain';
  const isAllowed = isDocx || isDoc || isPdf || isText;
  
  if (!isAllowed) {
    ElMessage.error('只能上传 Word、PDF 或文本文件!');
    return false;
  }
  
  const isLt10M = file.size / 1024 / 1024 < 10;
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过 10MB!');
    return false;
  }
  
  return true;
}

async function customUpload(options) {
  const formData = new FormData();
  formData.append('file', options.file);
  formData.append('doc_type', props.docType);
  
  try {
    const response = await axios.post(options.action, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    options.onSuccess(response.data);
  } catch (error) {
    options.onError(error);
  }
}

function handleSuccess(response) {
  try {
    if (!response) {
      console.warn('上传响应为空');
      return;
    }
    emits('upload-success', response);
    emits('upload-success-notify');
    ElMessage.success('文件上传成功！');
  } catch (error) {
    console.error('处理上传成功响应时出错:', error);
    ElMessage.warning('文件已上传，但处理响应时出现问题');
  }
}

function handleError(error) {
  try {
    emits('upload-error', error);
    const errorMsg = error?.message || (error?.response?.data?.message) || '网络错误';
    ElMessage.error(`上传失败: ${errorMsg}`);
    console.error('上传失败:', error);
  } catch (e) {
    console.error('处理上传错误时发生异常:', e);
    ElMessage.error('上传失败，请检查网络或文件类型');
  }
}
</script>

<style scoped>
.upload-container {
  display: inline-block;
  width: 100%;
}

.upload-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  background-color: #fafafa;
  cursor: pointer;
  transition: border-color 0.3s, background-color 0.3s;
  min-width: 300px;
  height: 160px;
}

.upload-area:hover {
  border-color: #409EFF;
  background-color: #f0f7ff;
}

.upload-icon {
  color: #8c939d;
  margin-bottom: 12px;
  transition: color 0.3s;
}

.upload-area:hover .upload-icon {
  color: #409EFF;
}

.upload-text {
  text-align: center;
}

.title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
}

.hint {
  font-size: 12px;
  color: #909399;
  margin: 0;
}

:deep(.el-upload) {
  width: 100%;
}

:deep(.el-upload-dragger) {
  width: 100%;
  padding: 0;
  border: none;
  background: none;
}
</style>
