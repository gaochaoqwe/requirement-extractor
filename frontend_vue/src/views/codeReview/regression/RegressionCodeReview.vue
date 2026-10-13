<template>
  <div class="code-review-regression">
    <div class="analysis-panel">
      <!-- 上传面板组件 -->
      <regression-upload-panel @uploaded="setFileIds" />
      
      <div class="button-row">
        <el-button 
          class="main-action-btn" 
          type="primary" 
          :disabled="!isReadyToAnalyze || analyzing" 
          :loading="analyzing" 
          @click="startAnalysis"
        >
          开始回归审查
        </el-button>
      </div>
      
      <transition name="fade">
        <div v-if="analyzing && taskId" class="progress-container">
          <el-progress :percentage="progress" :status="progressStatus">
            <span>{{ statusText }}</span>
          </el-progress>
        </div>
      </transition>
      
      <transition name="fade">
        <div v-if="taskId && analysisDone" style="margin-top: 20px;">
          <div style="display: flex; justify-content: center; align-items: center; gap: 20px;">
            <download-analysis-result :task-id="taskId" />
            
            <!-- 代码地图按钮 -->
            <el-button 
              type="success" 
              icon="Map" 
              @click="openCodeMap"
              size="large"
            >
              查看代码地图
            </el-button>
          </div>
        </div>
      </transition>
      
      <!-- 移除原来下方的代码地图按钮 -->

      <el-alert v-if="message" :title="message" :type="messageType" show-icon :closable="false" style="margin-top: 16px;" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import RegressionUploadPanel from './RegressionUploadPanel.vue';
import DownloadAnalysisResult from './download/DownloadAnalysisResult.vue';
import axios from 'axios';

const router = useRouter();

// 文件ID
const oldFileId = ref(null);
const newFileId = ref(null);
const reportFileId = ref(null);

// 分析状态
const analyzing = ref(false);
const taskId = ref('');
const analysisDone = ref(false);
const message = ref('');
const messageType = ref('success');
const progress = ref(0);
const status = ref('pending');

// 是否可以开始分析
const isReadyToAnalyze = computed(() => {
  return oldFileId.value && newFileId.value && reportFileId.value;
});

// 进度状态
const progressStatus = computed(() => {
  if (status.value === 'completed') return 'success';
  if (status.value === 'failed') return 'exception';
  return '';
});

// 状态文本
const statusText = computed(() => {
  if (status.value === 'pending') return '分析中...';
  if (status.value === 'processing') return '分析中...';
  if (status.value === 'completed') return '分析完成';
  if (status.value === 'failed') return '分析失败';
  return '处理中...';
});

// 设置文件ID
function setFileIds(ids) {
  console.log('收到上传文件IDs:', ids);
  
  oldFileId.value = ids.old;
  newFileId.value = ids.new;
  reportFileId.value = ids.report;
  
  if (isReadyToAnalyze.value) {
    message.value = '所有文件已上传，可以开始回归审查';
    messageType.value = 'success';
  }
}

// 防重复提交标记
const isSubmitting = ref(false);

// 开始分析
async function startAnalysis() {
  // 防止重复提交
  if (isSubmitting.value) {
    console.log('分析请求正在进行中，请勿重复提交');
    return;
  }
  
  // 检查文件ID是否有效
  if (!isReadyToAnalyze.value) {
    message.value = '错误：请先上传所有必需文件';
    messageType.value = 'error';
    console.error('启动分析失败：文件未完全上传');
    return;
  }
  
  // 设置提交状态
  isSubmitting.value = true;
  analyzing.value = true;
  analysisDone.value = false;
  message.value = '';
  progress.value = 0;
  status.value = 'pending';
  
  console.log('开始回归审查，使用文件ID:', {
    old_file_id: oldFileId.value,
    new_file_id: newFileId.value,
    report_file_id: reportFileId.value
  });
  
  try {
    const response = await axios.post('/api/codeReview/regression/start_analysis', {
      old_file_id: oldFileId.value,
      new_file_id: newFileId.value,
      report_file_id: reportFileId.value
    });
    
    console.log('回归审查请求响应:', response.data);
    
    if (response.data && response.data.task_id) {
      taskId.value = response.data.task_id;
      console.log('获取到task_id:', taskId.value);
      
      // 开始轮询任务进度
      pollTaskProgress();
    } else {
      throw new Error(response.data.error || '服务端未返回task_id');
    }
  } catch (e) {
    console.error('回归审查请求失败:', e);
    message.value = '启动回归审查失败：' + (e.message || e);
    messageType.value = 'error';
    analyzing.value = false;
    taskId.value = ''; // 重置任务ID
  } finally {
    // 无论成功失败都重置提交状态
    isSubmitting.value = false;
  }
}

// 轮询任务进度
async function pollTaskProgress() {
  if (!taskId.value || !analyzing.value) return;
  
  try {
    const response = await axios.get(`/api/codeReview/regression/task_progress/${taskId.value}`);
    console.log('任务进度:', response.data);
    
    if (response.data) {
      // 直接使用服务器返回的进度值
      progress.value = response.data.progress;
      status.value = response.data.status;
      
      // 检查任务是否完成
      if (status.value === 'completed') {
        analyzing.value = false;
        analysisDone.value = true;
        message.value = '回归审查完成，可以下载结果';
        messageType.value = 'success';
      } else if (status.value === 'failed') {
        analyzing.value = false;
        message.value = '回归审查失败';
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

// 打开代码地图
function openCodeMap() {
  if (taskId.value) {
    // 在新标签页中打开代码地图
    const url = `/regression/codemap/${taskId.value}`;
    window.open(url, '_blank');
  } else {
    message.value = '错误：未找到任务ID，无法打开代码地图';
    messageType.value = 'error';
  }
}
</script>

<style scoped>
.code-review-regression {
  padding: 0;
  max-height: calc(100vh - 200px);
  overflow-y: auto;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
}
.analysis-panel {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 8px 32px rgba(32, 101, 209, 0.08);
  max-width: 900px;
  margin: 0 auto;
}
.button-row {
  display: flex;
  justify-content: center;
  margin: 24px 0;
}
.main-action-btn {
  width: 200px;
  height: 48px;
  font-size: 1.1rem;
  border-radius: 8px;
}
.progress-container {
  margin-top: 20px;
  text-align: center;
}
.progress-container .el-progress-bar__outer {
  background-color: #ecf5ff;
}
.progress-container .el-progress-bar__inner {
  background-color: #409eff;
}
.progress-container .el-progress__text {
  color: #409eff;
}
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.5s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style> 