<template>
  <div class="upload-container">
    <el-upload accept=".zip"
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
          <p class="title">{{ uploadTitle }}</p>
          <p class="hint">{{ uploadHint }}</p>
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
    default: '/api/staticAnalysis/upload_file'
  },
  mode: {
    type: String,
    default: 'c'
  }
});
const emits = defineEmits(['upload-success', 'upload-error']);

const uploadTitle = computed(() => {
  return props.mode === 'fpga' ? 'FPGA代码压缩包' : 'C/C++代码压缩包';
});

const uploadHint = computed(() => {
  return props.mode === 'fpga'
    ? '支持 Verilog/VHDL/IP 代码，点击或拖拽 ZIP 文件到此处上传'
    : '支持 C/C++ 代码，点击或拖拽 ZIP 文件到此处上传';
});

function beforeUpload(file) {
  const fileName = file.name.toLowerCase();
  const isAllowed = fileName.endsWith('.zip');
  if (!isAllowed) {
    ElMessage.error('只能上传ZIP格式的代码压缩包!');
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
    
    emits('upload-success', response);
    ElMessage.success('代码压缩包上传成功！');
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