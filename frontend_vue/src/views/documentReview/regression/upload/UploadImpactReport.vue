<template>
  <div class="upload-container">
    <el-upload accept=".docx"
      :action="uploadUrl"
      :show-file-list="false"
      :before-upload="beforeUpload"
      :on-success="handleSuccess"
      :on-error="handleError"
      :http-request="customUpload"
      drag
    >
      <div class="upload-area">
        <el-icon :size="32" class="upload-icon">
          <Document />
        </el-icon>
        <div class="upload-text">
          <p class="title">影响域分析报告</p>
          <p class="hint">点击或拖拽文件到此处上传</p>
        </div>
      </div>
    </el-upload>
  </div>
</template>

<script setup>
import { ElMessage } from 'element-plus';
import { Document } from '@element-plus/icons-vue';
import axios from 'axios';

const props = defineProps({
  uploadUrl: {
    type: String,
    default: '/api/documentReview/Regression/upload/api/regression/upload'
  }
});
const emits = defineEmits(['upload-success', 'upload-error']);

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
  return true;
}

async function customUpload(options) {
  console.log('[DEBUG] 开始上传文件:', options.file.name);
  const formData = new FormData();
  formData.append('file', options.file);
  
  try {
    console.log('[DEBUG] 发送请求到:', props.uploadUrl);
    const response = await axios.post(props.uploadUrl, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    
    console.log('[DEBUG] 上传成功, 原始响应:', response);
    console.log('[DEBUG] 响应数据:', response.data);
    
    // 直接将响应数据传递给成功回调
    options.onSuccess(response.data);
  } catch (error) {
    console.error('[DEBUG] 上传错误:', error);
    options.onError(error);
  }
}

function handleSuccess(response) {
  console.log('上传成功，响应:', response);
  try {
    if (!response) {
      console.warn('上传响应为空');
      return;
    }
    
    // 直接把原始响应传给父组件，不做复杂解析
    emits('upload-success', response);
    ElMessage.success('文件上传成功！');
  } catch (error) {
    console.error('处理上传成功响应时出错:', error);
    ElMessage.warning('文件已上传，但处理响应时出现问题');
  }
}

function handleError(error) {
  ElMessage.error('上传失败，请重试');
  emits('upload-error', error);
}
</script>

<style scoped>
.upload-container {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  min-height: 220px;
}
.upload-area {
  width: 480px;
  height: 120px;
  margin: 0 auto;
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  background: #fafbfc;
  padding: 32px 0 24px 0;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.3s;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}
.upload-area:hover {
  border-color: #409EFF;
}
.upload-icon {
  color: #409EFF;
  margin-bottom: 10px;
}
.upload-text .title {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 6px;
}
.upload-text .hint {
  color: #888;
  font-size: 14px;
}
</style>
