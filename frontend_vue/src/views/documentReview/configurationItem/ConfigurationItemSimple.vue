<template>
  <div class="configuration-item-simple">
    <Document v-if="false" style="display: none;" />
    <Tickets v-if="false" style="display: none;" />
    <SuccessFilled v-if="false" style="display: none;" />
    
    <!-- 模式切换 -->
    <div class="mode-switch-container">
      <el-radio-group v-model="reviewMode" size="large">
        <el-radio-button value="manual">手动模式</el-radio-button>
        <el-radio-button value="auto">自动模式</el-radio-button>
      </el-radio-group>
    </div>
    
    <!-- 自动模式界面 -->
    <div class="simple-panel" v-show="reviewMode === 'auto'">
      <div class="upload-container">
        <div class="upload-column">
          <div class="upload-header">
            <el-icon><Document /></el-icon>
            <span>研制任务书</span>
          </div>
          <upload-document 
            label="研制任务书"
            :upload-url="uploadUrl"
            doc-type="taskBook"
            @upload-success="setFileId('taskBook', $event)"
            @upload-success-notify="showUploadSuccess('任务书')"
            icon="Document"
          />
          <div v-if="taskBookFileId" class="upload-status success">
            <el-icon><SuccessFilled /></el-icon>
            <span>已上传</span>
          </div>
        </div>
        
        <div class="upload-column">
          <div class="upload-header">
            <el-icon><Tickets /></el-icon>
            <span>需求规格说明</span>
          </div>
          <upload-document 
            label="需求规格说明"
            :upload-url="uploadUrl"
            doc-type="requirementSpec"
            @upload-success="setFileId('requirementSpec', $event)"
            @upload-success-notify="showUploadSuccess('需求规格说明')"
            icon="Tickets"
          />
          <div v-if="requirementSpecFileId" class="upload-status success">
            <el-icon><SuccessFilled /></el-icon>
            <span>已上传</span>
          </div>
        </div>
      </div>
      <el-button type="primary" :disabled="!taskBookFileId || !requirementSpecFileId || reviewing" :loading="reviewing" @click="startReview">开始文档审查</el-button>
      <transition name="fade">
        <div v-if="reviewing" class="progress-panel">
          <el-progress :percentage="progress" :status="progress === 100 ? 'success' : ''" :stroke-width="18" :color="customProgressColor"/>
          <div class="progress-text">{{ progressText }}</div>
        </div>
      </transition>
      <transition name="fade">
        <div v-if="reviewResult" class="result-panel">
          <review-document :result="reviewResult" />
        </div>
      </transition>
      <transition name="fade">
        <download-review-result v-if="reviewSessionId && !reviewing && progress === 100" :session-id="String(reviewSessionId)" :api-service="apiService" />
      </transition>
      <el-alert v-if="uploadSuccessMsg" :title="uploadSuccessMsg" type="success" show-icon :closable="false" style="margin-top: 16px;" />
    </div>
    
    <!-- 手动模式界面 -->
    <div v-show="reviewMode === 'manual'">
      <document-annotations-tool />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import UploadDocument from './upload/UploadDocument.vue';
import ReviewDocument from './review/ReviewDocument.vue';
import DownloadReviewResult from './downloadDocument/DownloadReviewResult.vue';
import DocumentAnnotationsTool from '../testTools/documentAnnotations2problemsSheet/DocumentAnnotations2problemsSheet.vue';
import * as ElementPlusIcons from '@element-plus/icons-vue';
import axios from 'axios';

// 导入需要的图标
import { Document, Tickets, SuccessFilled } from '@element-plus/icons-vue';

// 模式切换：auto(自动模式) 或 manual(手动模式)
const reviewMode = ref('manual');

// 使用相对路径，避免在其他电脑上因 localhost 访问失败
const uploadUrl = computed(() => `/api/documentReview/ConfigurationItem/upload/api/upload`);
const taskBookFileId = ref('');
const requirementSpecFileId = ref('');
const reviewing = ref(false);
const progress = ref(0);
const progressText = ref('');
const reviewResult = ref(null);
const reviewSessionId = ref('');
let progressTimer = null;
const uploadSuccessMsg = ref('');

function showUploadSuccess(type) {
  try {
    uploadSuccessMsg.value = `${type}上传成功！`;
    setTimeout(() => { 
      try {
        uploadSuccessMsg.value = ''; 
      } catch (e) {
        console.error('清除上传成功消息时出错:', e);
      }
    }, 1800);
  } catch (error) {
    console.error('显示上传成功消息时出错:', error);
  }
}

const customProgressColor = [
  { color: '#67c23a', percentage: 100 },
  { color: '#409EFF', percentage: 60 },
  { color: '#e6a23c', percentage: 30 },
  { color: '#f56c6c', percentage: 0 }
];

const apiService = {
  async downloadReviewResult(sessionId) {
    // 简单实现：直接打开下载链接
    window.open(`/api/documentReview/ConfigurationItem/download/api/download?session_id=${sessionId}`, '_blank');
  }
};

function setFileId(type, res) {
  try {
    if (!res || !res.file_id) {
      console.warn(`文件ID未定义: ${JSON.stringify(res)}`);
      return;
    }
    if (type === 'taskBook') taskBookFileId.value = res.file_id;
    if (type === 'requirementSpec') requirementSpecFileId.value = res.file_id;
  } catch (error) {
    console.error(`设置文件ID时发生错误:`, error);
  }
}

async function startReview() {
  reviewing.value = true;
  progress.value = 10;
  progressText.value = 'AI正在分析文档...';
  reviewResult.value = null;
  reviewSessionId.value = '';
  
  // 确保任何现有的轮询被清除
  if (window.pollTimerGlobal) {
    clearInterval(window.pollTimerGlobal);
    window.pollTimerGlobal = null;
  }

  try {
    // 1. 发送请求到后端，获取session_id
    const resp = await axios.post(`/api/documentReview/ConfigurationItem/reviewer/api/review`, {
      task_book_file_id: taskBookFileId.value,
      requirement_spec_file_id: requirementSpecFileId.value
    });
    reviewSessionId.value = resp.data.session_id;
    if (!reviewSessionId.value) {
      throw new Error('未获取到session_id');
    }

    // 2. 轮询进度接口
    const pollProgress = async () => {
      try {
        console.log('查询进度: session_id =', reviewSessionId.value);
        const progressResp = await axios.get(`/api/documentReview/ConfigurationItem/reviewer/api/review/progress`, {
          params: { session_id: reviewSessionId.value }
        });
        const data = progressResp.data;
        console.log('进度数据:', data);
        progress.value = data.percent || 0;
        progressText.value = data.desc || '查询中...';
        
        if (data.stage === 'error') {
          if (window.pollTimerGlobal) {
            clearInterval(window.pollTimerGlobal);
            window.pollTimerGlobal = null;
          }
          reviewing.value = false;
          reviewResult.value = data.desc;
          progress.value = 0; // 重置进度以防止下载按钮出现
        } else if (data.stage === 'done') {
          if (window.pollTimerGlobal) {
            clearInterval(window.pollTimerGlobal);
            window.pollTimerGlobal = null;
          }
          // 只有在审查真正完成时才设置reviewing为false
          reviewing.value = false;
          reviewResult.value = 'AI审查完成';
        }
      } catch (err) {
        console.error('查询进度出错:', err);
        if (window.pollTimerGlobal) {
          clearInterval(window.pollTimerGlobal);
          window.pollTimerGlobal = null;
        }
        progressText.value = '进度查询失败';
        reviewing.value = false;
        progress.value = 0; // 重置进度以防止下载按钮出现
      }
    };
    
    window.pollTimerGlobal = setInterval(pollProgress, 1000);
    // 立即执行一次，避免等待1s
    pollProgress();
  } catch (e) {
    progressText.value = e?.response?.data?.message || e.message || '审查请求失败';
    reviewing.value = false;
    progress.value = 0;
  }
}

// 该函数已不再使用，因为startReview会直接获取结果
function pollProgress() {
  // 保留这个空函数以避免旧代码的引用错误
  console.log('该函数已被弃用');
}

// 该函数已不再使用，因为startReview会直接获取结果
function getReviewResult() {
  // 保留这个空函数以避免旧代码的引用错误
  console.log('该函数已被弃用');
}
</script>

<style scoped>
.configuration-item-simple {
  padding: 20px;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
}

.mode-switch-container {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
  padding: 16px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(32, 101, 209, 0.08);
  max-width: 400px;
  margin-left: auto;
  margin-right: auto;
}

.mode-switch-container :deep(.el-radio-button__inner) {
  padding: 12px 24px;
  font-size: 16px;
  font-weight: 600;
}

.mode-switch-container :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background-color: #409EFF;
  border-color: #409EFF;
  box-shadow: -1px 0 0 0 #409EFF;
}
.simple-panel {
  background: #fff;
  border-radius: 12px;
  padding: 32px 32px 24px 32px;
  box-shadow: 0 8px 32px rgba(32, 101, 209, 0.08);
  max-width: 700px;
  margin: 40px auto 0 auto;
}
.upload-container {
  display: flex;
  gap: 24px;
  margin-bottom: 24px;
}

.upload-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 300px;
}

.upload-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.upload-header .el-icon {
  font-size: 18px;
  color: #409EFF;
}

.upload-status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px;
  border-radius: 4px;
  font-size: 14px;
}

.upload-status.success {
  color: #67c23a;
  background-color: #f0f9eb;
}

.upload-status .el-icon {
  font-size: 16px;
}

.simple-panel > .el-button {
  margin-top: 8px;
  width: 100%;
}
.el-button {
  min-width: 140px;
  height: 40px;
  font-size: 16px;
  border-radius: 6px;
}
.progress-panel {
  margin: 24px 0 10px 0;
  padding: 8px 0;
  text-align: center;
}
.progress-text {
  margin-top: 12px;
  color: #409EFF;
  font-size: 16px;
  font-weight: bold;
}
.result-panel {
  margin: 28px 0 0 0;
  background: #f5f7fa;
  border-radius: 8px;
  padding: 18px 24px;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.07);
}
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.4s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

</style>
