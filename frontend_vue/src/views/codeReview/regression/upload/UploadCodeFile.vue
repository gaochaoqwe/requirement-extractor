<template>
  <div class="upload-container">
    <el-upload :accept="accept"
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
          <p class="title">{{ titleText }}</p>
          <p class="hint">点击或拖拽{{ acceptText }}文件到此处上传</p>
        </div>
      </div>
    </el-upload>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { ElMessage } from 'element-plus';
import { Document } from '@element-plus/icons-vue';
import axios from 'axios';

const props = defineProps({
  uploadUrl: {
    type: String,
    default: '/api/codeReview/regression/upload_file'
  },
  versionType: {
    type: String,
    required: true,
    validator: (value) => ['old', 'new', 'report'].includes(value)
  },
  accept: {
    type: String,
    default: '.zip'
  }
});

const titleText = computed(() => {
  if (props.versionType === 'old') return '上一版本代码';
  if (props.versionType === 'new') return '当前版本代码';
  if (props.versionType === 'report') return '影响域分析报告';
  return 'C/C++代码压缩包';
});

const acceptText = computed(() => {
  if (props.accept.includes('.doc') || props.accept.includes('.pdf')) {
    return '文档';
  }
  return 'ZIP';
});

const emits = defineEmits(['upload-success', 'upload-error']);

function beforeUpload(file) {
  const fileName = file.name.toLowerCase();
  const fileExt = fileName.substring(fileName.lastIndexOf('.'));
  const acceptList = props.accept.split(',').map(ext => ext.trim());
  
  const isAllowed = acceptList.some(ext => fileExt === ext);
  if (!isAllowed) {
    ElMessage.error(`只能上传${acceptText.value}格式的文件!`);
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
      headers: { 'Content-Type': 'multipart/form-data' },
      params: { version: props.versionType }
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
    
    // 直接把原始响应传给父组件
    emits('upload-success', response);
    ElMessage.success(`${titleText.value}上传成功！`);
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
  width: 100%;
  min-height: 180px;
  box-sizing: border-box;
}

.upload-area {
  width: 100%;
  height: 100%;
  min-height: 180px;
  margin: 0;
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  background: #fafbfc;
  padding: 16px 12px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  box-sizing: border-box;
}

@media (max-width: 768px) {
  .upload-area {
    min-height: 160px;
    padding: 12px 8px;
  }
}

.upload-area:hover {
  border-color: #409EFF;
  box-shadow: 0 2px 12px 0 rgba(64, 158, 255, 0.1);
  transform: translateY(-2px);
}

.upload-icon {
  color: #409EFF;
  margin-bottom: 10px;
}

.upload-text .title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
  padding: 0 8px;
}

.upload-text .hint {
  color: #909399;
  font-size: 13px;
  line-height: 1.4;
  padding: 0 8px;
  word-break: break-word;
  max-width: 100%;
  margin: 0 auto;
}
</style>