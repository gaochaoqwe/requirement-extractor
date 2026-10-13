<template>
  <div class="code-review-configuration-item">
    <div class="analysis-panel">
      <div class="upload-container">
        <div class="upload-column">
          <div class="upload-header">
            <el-icon><Document /></el-icon>
            <span>代码文件</span>
          </div>
          <upload-code-file
            @upload-success="setFileId($event)"
          />
          <div v-if="fileId" class="upload-status success">
            <el-icon><SuccessFilled /></el-icon>
            <span>已上传</span>
          </div>
        </div>
      </div>
      <div class="button-row">
        <el-button class="main-action-btn" type="primary" :disabled="!fileId || analyzing" :loading="analyzing" @click="startAnalysis">
          开始代码审查
        </el-button>
      </div>
      <transition name="fade">
        <div style="margin-top: 20px;">
          <download-analysis-result v-if="taskId && analysisDone" :task-id="taskId" />
        </div>
      </transition>
      <el-alert v-if="message" :title="message" :type="messageType" show-icon :closable="false" style="margin-top: 16px;" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import UploadCodeFile from './upload/UploadCodeFile.vue';
import DownloadAnalysisResult from './download/DownloadAnalysisResult.vue';
import { Document, SuccessFilled } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import axios from 'axios';

const codeFileId = ref('');
const analyzing = ref(false);
const taskId = ref('');
const analysisDone = ref(false);
const message = ref('');
const messageType = ref('success');
const progress = ref(0);
const status = ref('pending');

// 计算属性
const fileId = computed(() => codeFileId.value);
const progressStatus = computed(() => {
  if (status.value === 'completed') return 'success';
  if (status.value === 'failed') return 'exception';
  return '';
});
const statusText = computed(() => {
  if (status.value === 'pending') return '分析中...';
  if (status.value === 'processing') return '分析中...';
  if (status.value === 'completed') return '分析完成';
  if (status.value === 'failed') return '分析失败';
  return '处理中...';
});

function setFileId(res) {
  console.log('接收到上传成功响应:', res);
  
  try {
    if (!res || !res.file_id) {
      console.warn('文件ID未定义: ', res);
      return;
    }
    
    codeFileId.value = res.file_id;
    message.value = '代码文件上传成功';
    messageType.value = 'success';
  } catch (error) {
    console.error('设置文件ID时发生错误:', error);
  }
}

// 防重复提交标记
const isSubmitting = ref(false);

async function startAnalysis() {
  // 防止重复提交
  if (isSubmitting.value) {
    console.log('分析请求正在进行中，请勿重复提交');
    return;
  }
  
  // 检查file_id是否有效
  if (!codeFileId.value) {
    message.value = '错误：未获取到有效的文件ID，请重新上传文件';
    messageType.value = 'error';
    console.error('启动分析失败：file_id为空');
    return;
  }
  
  // 设置提交状态
  isSubmitting.value = true;
  analyzing.value = true;
  analysisDone.value = false;
  message.value = '';
  progress.value = 0;
  status.value = 'pending';
  
  console.log('开始代码审查，使用的file_id:', codeFileId.value);
  
  try {
    const response = await axios.post('/api/codeReview/start_analysis', {
      file_id: codeFileId.value
    });
    
    console.log('分析请求响应:', response.data);
    
    if (response.data && response.data.task_id) {
      taskId.value = response.data.task_id;
      console.log('获取到task_id:', taskId.value);
      
      // 开始轮询任务进度
      pollTaskProgress();
    } else {
      throw new Error(response.data.error || '服务端未返回task_id');
    }
  } catch (e) {
    console.error('分析请求失败:', e);
    // 针对并发数量限制的专门提示
    if (e.response && e.response.status === 429) {
      ElMessage.error('当前模型并发数量限制，使用人数已达上限，请稍后再试');
    }
    message.value = '启动代码审查失败：' + (e.message || e);
    messageType.value = 'error';
    analyzing.value = false;
    taskId.value = ''; // 重置任务ID
  } finally {
    // 无论成功失败都重置提交状态
    isSubmitting.value = false;
  }
}

async function pollTaskProgress() {
  if (!taskId.value || !analyzing.value) return;
  
  try {
    const response = await axios.get(`/api/codeReview/task/${taskId.value}/progress`);
    console.log('任务进度:', response.data);
    
    if (response.data) {
      // 直接使用服务器返回的进度值
      progress.value = response.data.progress;
      status.value = response.data.status;
      
      // 检查任务是否完成
      if (status.value === 'completed') {
        analyzing.value = false;
        analysisDone.value = true;
        message.value = '代码审查完成，可以下载结果';
        messageType.value = 'success';
      } else if (status.value === 'failed') {
        analyzing.value = false;
        message.value = '代码审查失败';
        messageType.value = 'error';
      } else {
        // 继续轮询，间隔调整为20秒
        setTimeout(pollTaskProgress, 20000);
      }
    }
  } catch (e) {
    console.error('获取任务进度失败:', e);
    message.value = '获取任务进度失败';
    messageType.value = 'error';
    analyzing.value = false;
  }
}
</script>

<style scoped>
.code-review-configuration-item {
  padding: 20px;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
}
.analysis-panel {
  background: #fff;
  border-radius: 12px;
  padding: 32px 32px 24px 32px;
  box-shadow: 0 8px 32px rgba(32, 101, 209, 0.08);
  max-width: 700px;
  margin: 40px auto 0 auto;
}
.upload-container {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
}
.button-row {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
}
.main-action-btn {
  width: 200px;
  height: 48px;
  font-size: 1.1rem;
  border-radius: 8px;
}
.upload-column {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-right: 20px;
}
.upload-header {
  font-size: 1.1rem;
  color: #34495e;
  margin-bottom: 15px;
  display: flex;
  align-items: center;
}
.upload-header .el-icon {
  margin-right: 8px;
  color: #3498db;
}
.upload-status {
  display: flex;
  align-items: center;
  margin-top: 10px;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 0.95rem;
}
.upload-status.success {
  background-color: #e6f7ff;
  color: #1890ff;
  border: 1px solid #91d5ff;
}
.upload-status .el-icon {
  margin-right: 6px;
}
</style> 