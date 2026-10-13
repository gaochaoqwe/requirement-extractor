<template>
  <div class="upload-container">
    <el-upload
      accept=".zip"
      :action="uploadUrl"
      :show-file-list="false"
      :before-upload="beforeUpload"
      :on-success="handleSuccess"
      :on-error="handleError"
      :http-request="customUpload"
      :disabled="disabled"
      drag
    >
      <div class="upload-area">
        <el-icon :size="32" class="upload-icon">
          <Document />
        </el-icon>
        <div class="upload-text">
          <p class="title">{{ titleText }}</p>
          <p class="hint">支持C/C++和FPGA代码，点击或拖拽ZIP文件到此处上传</p>
        </div>
      </div>
    </el-upload>
  </div>
</template>

<script setup>
import { ElMessage } from 'element-plus';
import { Document } from '@element-plus/icons-vue';
import axios from 'axios';
import { computed } from 'vue';

const props = defineProps({
  uploadUrl: {
    type: String,
    default: '/api/codeReview/regressionTest/upload_file'
  },
  version: {
    type: String,
    default: 'new'
  },
  taskId: {
    type: [String, Number],
    default: null
  },
  disabled: {
    type: Boolean,
    default: false
  }
});
const emits = defineEmits(['upload-success', 'upload-error']);

const titleText = computed(() => {
  const v = String(props.version || '').toLowerCase();
  if (v === 'old') return '旧版本代码压缩包';
  if (v === 'new') return '新版本代码压缩包';
  return '代码压缩包';
});

function beforeUpload(file) {
  const fileName = file.name.toLowerCase();
  const isAllowed = fileName.endsWith('.zip');
  if (!isAllowed) {
    ElMessage.error('只能上传ZIP格式的代码压缩包（支持C/C++和FPGA代码）!');
    return false;
  }
  
  // 检查文件大小（15MB = 15 * 1024 * 1024 bytes）
  const maxSizeMB = 15;
  const maxSizeBytes = maxSizeMB * 1024 * 1024;
  const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2);
  
  if (file.size > maxSizeBytes) {
    ElMessage({
      type: 'error',
      duration: 8000,
      dangerouslyUseHTMLString: true,
      message: `
        <div style="text-align: left;">
          <div style="font-weight: bold; margin-bottom: 8px;">压缩包过大（${fileSizeMB} MB），请清理后重新上传</div>
          <div style="font-size: 13px; line-height: 1.6;">
            <div style="margin-bottom: 4px;"><strong>建议操作：</strong></div>
            <div>1. 仅保留源码文件（C/C++: .c/.cpp/.h/.hpp，FPGA: .v/.vhd/.vhdl）</div>
            <div>2. 删除编译产物（.o/.obj/.exe/.dll等）</div>
            <div>3. 删除临时文件和文档（.txt/.pdf/.doc等）</div>
            <div>4. 删除图片和媒体文件</div>
            <div style="margin-top: 6px; color: #909399;">当前限制: ${maxSizeMB} MB</div>
          </div>
        </div>
      `
    });
    return false;
  }
  
  return true;
}

async function customUpload(options) {
  console.log('[DEBUG] 开始上传文件:', options.file.name);
  const formData = new FormData();
  formData.append('file', options.file);
  formData.append('version', props.version);
  if (props.taskId) {
    formData.append('task_id', props.taskId);
  }
  const token = localStorage.getItem('token');
  
  try {
    console.log('[DEBUG] 发送请求到:', props.uploadUrl);
    const response = await axios.post(props.uploadUrl, formData, {
      withCredentials: true,
      headers: {
        'Content-Type': 'multipart/form-data',
        ...(token ? { Authorization: `Bearer ${token}` } : {})
      }
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
    ElMessage.success('代码压缩包上传成功！');
  } catch (error) {
    console.error('处理上传成功响应时出错:', error);
    ElMessage.warning('文件已上传，但处理响应时出现问题');
  }
}

function handleError(error) {
  console.error('上传错误详情:', error);
  
  // 处理后端返回的详细错误信息
  let errorMessage = '上传失败，请重试';
  
  if (error.response && error.response.data && error.response.data.detail) {
    const detail = error.response.data.detail;
    // 如果是压缩包过大的错误，显示详细提示
    if (detail.includes('压缩包过大') || detail.includes('ZIP文件过大')) {
      ElMessage({
        type: 'error',
        duration: 8000,
        dangerouslyUseHTMLString: true,
        message: `<div style="white-space: pre-line; text-align: left;">${detail}</div>`
      });
      emits('upload-error', error);
      return;
    }
    errorMessage = detail;
  }
  
  ElMessage.error(errorMessage);
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