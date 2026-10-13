<template>
  <div class="regression-simple">
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
            <span>影响域分析报告</span>
          </div>
          <upload-impact-report
            @upload-success="setFileId($event)"
          />
          <div v-if="fileId" class="upload-status success">
            <el-icon><SuccessFilled /></el-icon>
            <span>已上传</span>
          </div>
        </div>
      </div>
      <div class="button-row">
  <el-button class="main-action-btn" type="primary" :disabled="!fileId || reviewing" :loading="reviewing" @click="startReview">
    开始回归测试审查
  </el-button>
</div>
      <transition name="fade">
        <regression-review v-if="reviewing && reviewSessionId" :session-id="reviewSessionId" @done="onReviewDone" />
      </transition>
      <transition name="fade">
        <div style="margin-top: 20px;">
          <download-review-result v-if="reviewSessionId && reviewDone" :session-id="String(reviewSessionId)" />
        </div>
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
import UploadImpactReport from './upload/UploadImpactReport.vue';
import RegressionReview from './review/RegressionReview.vue';
import DownloadReviewResult from './downloadDocument/DownloadReviewResult.vue';
import DocumentAnnotationsTool from '../testTools/documentAnnotations2problemsSheet/DocumentAnnotations2problemsSheet.vue';
import { Document, SuccessFilled } from '@element-plus/icons-vue';
import axios from 'axios';

// 模式切换：auto(自动模式) 或 manual(手动模式)
const reviewMode = ref('manual');

const impactReportFileId = ref('');
const reviewing = ref(false);
const reviewSessionId = ref('');
const reviewDone = ref(false);
const uploadSuccessMsg = ref('');

// 核心解决方案：用计算属性代理impactReportFileId值，解决模板中ref未自动解包问题
const fileId = computed(() => impactReportFileId.value);

function setFileId(res) {
  console.log('接收到上传成功响应:', res);
  
  try {
    if (!res || !res.file_id) {
      console.warn('文件ID未定义: ', res);
      return;
    }
    
    // 直接从响应中提取file_id
    impactReportFileId.value = res.file_id;
    uploadSuccessMsg.value = '影响域分析报告上传成功';
  } catch (error) {
    console.error('设置文件ID时发生错误:', error);
  }
  
  // 终极解决方案：使用原生DOM操作强制启用按钮
  setTimeout(() => {
    console.log('开始原生DOM强制启用按钮...');
    
    // 1. 强制移除主按钮的disabled属性
    const mainBtn = document.querySelector('.main-action-btn');
    if (mainBtn) {
      console.log('找到了主按钮，强制启用');
      mainBtn.disabled = false;
      mainBtn.classList.remove('is-disabled');
      
      // 添加点击事件
      mainBtn.onclick = function() {
        startReview();
      };
      
      // 添加视觉反馈
      mainBtn.style.opacity = '1';
      mainBtn.style.cursor = 'pointer';
      mainBtn.style.backgroundColor = '#409EFF';
      
      // 不添加多余的提示文字
    } else {
      console.log('没有找到主按钮');
    }
    
    console.log('当前 impactReportFileId:', impactReportFileId.value, '按钮disabled:', !impactReportFileId.value || reviewing.value);
  }, 500); // 给更多时间等待DOM渲染
}

// 添加防重复提交标记
const isSubmitting = ref(false);

async function startReview() {
  // 防止重复提交
  if (isSubmitting.value) {
    console.log('审查请求正在进行中，请勿重复提交');
    return;
  }
  
  // 检查file_id是否有效
  if (!impactReportFileId.value) {
    uploadSuccessMsg.value = '错误：未获取到有效的文件ID，请重新上传文件';
    console.error('启动审查失败：file_id为空');
    return;
  }
  
  // 设置提交状态
  isSubmitting.value = true;
  reviewing.value = true;
  reviewDone.value = false;
  uploadSuccessMsg.value = '';
  
  console.log('开始审查，使用的file_id:', impactReportFileId.value);
  
  try {
    // 路径修正：与后端保持一致
    const response = await axios.post('/api/documentReview/Regression/reviewer/api/regression/review', {
      impact_report_file_id: impactReportFileId.value
    });
    
    console.log('审查请求响应:', response.data);
    
    if (response.data && response.data.session_id) {
      reviewSessionId.value = response.data.session_id;
      console.log('获取到session_id:', reviewSessionId.value);
    } else {
      throw new Error(response.data.error || '服务端未返回session_id');
    }
  } catch (e) {
    console.error('审查请求失败:', e);
    uploadSuccessMsg.value = '启动回归测试审查失败：' + (e.message || e);
    reviewing.value = false;
    reviewSessionId.value = ''; // 重置会话ID
  } finally {
    // 无论成功失败都重置提交状态
    isSubmitting.value = false;
  }
}

function onReviewDone() {
  reviewing.value = false;
  reviewDone.value = true;
}
</script>

<style scoped>
.regression-simple {
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
  justify-content: center;
  margin-bottom: 24px;
}
.button-row {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}
.main-action-btn {
  width: 480px;
  height: 44px;
  font-size: 18px;
  font-weight: 600;
  border-radius: 8px;
  letter-spacing: 2px;
}
.upload-header {
  display: flex;
  align-items: center;
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 12px;
}
.upload-header .el-icon {
  margin-right: 8px;
}
.upload-status.success {
  color: #67c23a;
  margin-top: 8px;
  display: flex;
  align-items: center;
}
.upload-status .el-icon {
  margin-right: 4px;
}
.fade-enter-active, .fade-leave-active {
  transition: opacity .3s;
}
.fade-enter, .fade-leave-to {
  opacity: 0;
}
</style>
