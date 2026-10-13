<template>
  <div class="chain-review-progress-page">
    <div class="page-header">
      <h1>
        <el-icon :size="24" style="vertical-align: middle;"><Connection /></el-icon>
        链路审查 - 实时进度
      </h1>
      <div class="header-actions">
        <el-button 
          v-if="status === 'completed'" 
          type="success" 
          @click="downloadExcelReport" 
          icon="Download"
        >
          下载审查结果
        </el-button>
        <el-button @click="goBack" icon="Back">返回</el-button>
      </div>
    </div>
    
    <!-- 总体进度卡片 -->
    <el-card shadow="hover" class="progress-card">
      <template #header>
        <div class="card-header">
          <el-tag :type="statusTagType" effect="dark">{{ statusText }}</el-tag>
        </div>
      </template>
      
      <el-progress 
        :percentage="overallProgress" 
        :status="progressStatus"
        :stroke-width="20"
      >
        <span class="progress-text">{{ currentActivity }}</span>
      </el-progress>
      
    </el-card>
    
    <!-- 分析阶段步骤条 -->
    <el-card shadow="hover" class="stages-card">
      <template #header>
        <div class="card-header">
          <el-icon><TrendCharts /></el-icon>
          <span>分析阶段</span>
        </div>
      </template>
      
      <div class="stages-container">
        <!-- 功能划分阶段（前半段） -->
        <div class="stage-section discovery-section">
          <div class="section-title">功能划分</div>
          <el-steps :active="discoveryStepActive" align-center class="stage-steps">
            <el-step 
              title="目录结构分析" 
              :icon="getStepIcon(1)"
              :status="getStepStatus(1)"
            >
              <template #description>
                <div class="step-desc">
                  {{ getStepDescription(1) }}
                </div>
              </template>
            </el-step>
            <el-step 
              title="函数签名分析" 
              :icon="getStepIcon(2)"
              :status="getStepStatus(2)"
            >
              <template #description>
                <div class="step-desc">
                  {{ getStepDescription(2) }}
                </div>
              </template>
            </el-step>
            <el-step 
              title="main函数验证" 
              :icon="getStepIcon(3)"
              :status="getStepStatus(3)"
            >
              <template #description>
                <div class="step-desc">
                  {{ getStepDescription(3) }}
                </div>
              </template>
            </el-step>
          </el-steps>
        </div>
        
        <!-- 功能审查阶段（后半段） -->
        <div class="stage-section review-section" v-if="discoveryStatus === 'completed' || reviewProgress > 0">
          <div class="section-title">功能审查</div>
          <div class="review-status">
            <div class="current-feature">
              <el-icon class="feature-icon rotating-icon" v-if="status === 'in_progress'">
                <Loading />
              </el-icon>
              <el-icon class="feature-icon" v-else color="#67C23A">
                <Check />
              </el-icon>
              <span class="feature-name">{{ currentReviewFeature }}</span>
            </div>
            <div class="review-progress-text">
              {{ reviewedFeatures }} / {{ featuresCount }} 已完成
            </div>
          </div>
        </div>
      </div>
    </el-card>
    
    <!-- 功能树卡片 -->
    <el-card shadow="hover" class="features-card" v-if="featuresTree.length > 0">
      <template #header>
        <div class="card-header">
          <el-icon><FolderOpened /></el-icon>
          <span>发现的功能模块</span>
          <el-button-group style="margin-left: auto;">
            <el-button size="small" @click="expandAllFeatures">全部展开</el-button>
            <el-button size="small" @click="collapseAllFeatures">全部折叠</el-button>
          </el-button-group>
        </div>
      </template>
      
      <el-tree
        ref="featureTreeRef"
        :data="featuresTree"
        :props="{ label: 'name', children: 'sub_features' }"
        node-key="id"
        default-expand-all
        class="feature-tree"
      >
        <template #default="{ node, data }">
          <div class="tree-node">
            <div class="node-info">
              <el-icon :color="getNodeIconColor(data)">
                <component :is="getNodeIcon(data)" />
              </el-icon>
              <span class="node-label">{{ data.name }}</span>
              <!-- 显示子功能数量 -->
              <span v-if="data.sub_features && data.sub_features.length > 0" class="sub-count">
                ({{ data.sub_features.length }} 个子功能)
              </span>
            </div>
            <div class="node-meta">
              <el-tag
                v-if="data.issues_count > 0"
                size="small"
                type="danger"
              >
                {{ data.issues_count }} 问题
              </el-tag>
            </div>
          </div>
        </template>
      </el-tree>
    </el-card>
    
    <!-- 审查完成后的操作按钮 -->
    <el-card shadow="hover" class="actions-card" v-if="status === 'completed'">
      <div class="completion-message">
        <el-icon :size="48" color="#67C23A"><CircleCheck /></el-icon>
        <h2>🎉 链路审查完成！</h2>
        <p>共发现 <strong>{{ featuresCount }}</strong> 个功能模块，请选择下一步操作</p>
      </div>
      
      <div class="action-buttons">
        <el-button 
          type="primary" 
          size="large"
          @click="downloadExcelReport" 
          :icon="Download"
        >
          <span style="font-size: 16px;">下载审查结果</span>
        </el-button>
        <el-button 
          type="success" 
          size="large"
          @click="viewResults" 
          :icon="View"
        >
          <span style="font-size: 16px;">查看代码视图</span>
        </el-button>
      </div>
    </el-card>
    
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';
import { ElMessage, ElLoading } from 'element-plus';
import {
  Connection,
  Clock,
  FolderOpened,
  Loading,
  Check,
  Back,
  View,
  Document,
  Files,
  Folder,
  Download,
  TrendCharts,
  CircleCheck
} from '@element-plus/icons-vue';

const route = useRoute();
const router = useRouter();

const taskId = ref(route.params.taskId);

// 进度数据
const status = ref('not_started');
const discoveryStatus = ref('not_started');  // 新增：功能发现状态
const currentRound = ref(0);
const totalRounds = ref(3);
const discoveryProgress = ref(0);
const reviewProgress = ref(0);
const overallProgress = ref(0);
const currentActivity = ref('准备开始...');
const featuresCount = ref(0);
const reviewedFeatures = ref(0);
const currentReviewFeature = ref('等待开始...');  // 当前审查的功能名称

// 记忆数据
const roundsHistory = ref([]);
const featuresTree = ref([]);

// 树形组件ref
const featureTreeRef = ref(null);

// 轮询定时器
let pollTimer = null;

// 计算属性
const statusText = computed(() => {
  const statusMap = {
    'not_started': '未开始',
    'in_progress': '进行中',
    'completed': '已完成',
    'error': '错误'
  };
  return statusMap[status.value] || '未知';
});

const statusTagType = computed(() => {
  const typeMap = {
    'not_started': 'info',
    'in_progress': 'primary',
    'completed': 'success',
    'error': 'danger'
  };
  return typeMap[status.value] || 'info';
});

const progressStatus = computed(() => {
  if (status.value === 'completed') return 'success';
  if (status.value === 'error') return 'exception';
  return '';
});

// 功能划分阶段的激活步骤（0-3）
const discoveryStepActive = computed(() => {
  if (discoveryStatus.value === 'completed') return 3;
  return currentRound.value;
});

// 方法
const pollProgress = async () => {
  try {
    const response = await axios.get(`/api/codeReview/regressionTest/progressive/progress/${taskId.value}`);
    const data = response.data;
    
    console.log('轮询进度:', data);
    
    // 更新进度
    status.value = data.status || 'not_started';
    discoveryStatus.value = data.discovery_status || 'not_started';  // 新增
    currentRound.value = data.current_round || 0;
    totalRounds.value = data.total_rounds || 3;
    discoveryProgress.value = Math.round(data.discovery_progress || 0);
    reviewProgress.value = Math.round(data.review_progress || 0);
    overallProgress.value = Math.round(data.overall_progress || 0);
    currentActivity.value = data.current_activity || '准备中...';
    featuresCount.value = data.features_count || 0;
    reviewedFeatures.value = data.reviewed_features || 0;
    currentReviewFeature.value = data.current_feature || '等待开始...';
    
    // 更新记忆数据
    if (data.memory) {
      // 对roundsHistory去重，保留每个round的最后一条记录
      const allRounds = data.memory.metadata?.rounds_history || [];
      const roundMap = new Map();
      allRounds.forEach(round => {
        roundMap.set(round.round, round); // 后面的会覆盖前面的
      });
      roundsHistory.value = Array.from(roundMap.values()).sort((a, b) => a.round - b.round);
      
      featuresTree.value = data.memory.features || [];
    }
    
    // 如果完成，停止轮询并显示操作按钮
    if (data.status === 'completed') {
      clearInterval(pollTimer);
      ElMessage.success({
        message: '链路审查完成！请选择下一步操作',
        type: 'success',
        duration: 3000
      });
    }
    
    // 如果出错，停止轮询
    if (data.status === 'error') {
      clearInterval(pollTimer);
      ElMessage.error('链路审查出错：' + (data.message || '未知错误'));
    }
  } catch (error) {
    console.error('获取进度失败:', error);
    // 不停止轮询，可能只是临时网络问题
  }
};

const viewResults = () => {
  // 跳转到代码地图
  router.push(`/codemap/${taskId.value}?mode=chain`);
};

const goBack = () => {
  router.back();
};

const downloadExcelReport = async () => {
  try {
    const url = `/api/codeReview/regressionTest/download_result/${taskId.value}`;
    
    // 显示加载提示
    const loading = ElLoading.service({
      lock: true,
      text: '正在生成Excel报告...',
      background: 'rgba(0, 0, 0, 0.7)',
    });
    
    // 使用fetch下载文件
    const response = await fetch(url);
    
    if (!response.ok) {
      loading.close();
      const errorText = await response.text();
      throw new Error(errorText || '下载失败');
    }
    
    // 获取文件名
    const contentDisposition = response.headers.get('Content-Disposition');
    let filename = `code_review_result_task_${taskId.value}.xlsx`;
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename=(.+)/);
      if (filenameMatch) {
        filename = filenameMatch[1];
      }
    }
    
    // 下载文件
    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(downloadUrl);
    
    loading.close();
    ElMessage.success('审查结果下载成功！');
  } catch (error) {
    console.error('下载审查结果失败:', error);
    ElMessage.error('下载失败：' + error.message);
  }
};

const getRoundStatus = (round) => {
  // 如果功能发现阶段已完成，所有round都应该是success
  if (discoveryStatus.value === 'completed') {
    return 'success';
  }
  if (round.round < currentRound.value) return 'success';
  if (round.round === currentRound.value) return 'primary';
  return 'info';
};

const getRoundIcon = (round) => {
  // 如果功能发现阶段已完成，所有round都应该显示完成图标
  if (discoveryStatus.value === 'completed') {
    return Check;
  }
  if (round.round < currentRound.value) return Check;
  if (round.round === currentRound.value) return Loading;
  return Clock;
};

const getRoundTitle = (roundNum) => {
  const titles = {
    1: 'Round 1: 目录结构分析',
    2: 'Round 2: 函数签名分析',
    3: 'Round 3: main函数验证'
  };
  return titles[roundNum] || `Round ${roundNum}`;
};

// 步骤图标
const getStepIcon = (stepNum) => {
  if (discoveryStatus.value === 'completed' || currentRound.value > stepNum) {
    return Check;
  }
  if (currentRound.value === stepNum) {
    return Loading;
  }
  return Clock;
};

// 步骤状态
const getStepStatus = (stepNum) => {
  if (discoveryStatus.value === 'completed' || currentRound.value > stepNum) {
    return 'success';
  }
  if (currentRound.value === stepNum) {
    return 'process';
  }
  return 'wait';
};

// 步骤描述
const getStepDescription = (stepNum) => {
  const round = roundsHistory.value.find(r => r.round === stepNum);
  
  if (discoveryStatus.value === 'completed' || currentRound.value > stepNum) {
    return round?.summary || '已完成';
  }
  if (currentRound.value === stepNum) {
    return round?.summary || '分析中...';
  }
  return '等待中';
};

const getConfidenceType = (confidence) => {
  const types = {
    'high': 'success',
    'medium': 'warning',
    'low': 'info'
  };
  return types[confidence] || 'info';
};

const confidenceLabel = (confidence) => {
  const labels = {
    'high': '高',
    'medium': '中',
    'low': '低'
  };
  return labels[confidence] || confidence;
};

const getNodeIcon = (data) => {
  if (data.type === 'project') return Folder;
  if (data.children && data.children.length > 0) return Files;
  return Document;
};

const getNodeIconColor = (data) => {
  if (data.type === 'project') return '#409EFF';
  // 有问题的显示红色
  if (data.issues_count && data.issues_count > 0) return '#F56C6C';
  // 有子功能的显示蓝色
  if (data.sub_features && data.sub_features.length > 0) return '#409EFF';
  // 普通功能显示绿色
  return '#67C23A';
};

const formatTime = (timestamp) => {
  if (!timestamp) return '';
  const date = new Date(timestamp);
  return date.toLocaleString('zh-CN');
};

const expandAllFeatures = () => {
  const tree = featureTreeRef.value;
  if (tree) {
    // 获取所有节点的key
    const keys = [];
    const collectKeys = (nodes) => {
      nodes.forEach(node => {
        if (node.id) keys.push(node.id);
        if (node.sub_features) collectKeys(node.sub_features);
      });
    };
    collectKeys(featuresTree.value);
    
    // 展开所有节点
    keys.forEach(key => {
      tree.store.nodesMap[key]?.expand();
    });
  }
};

const collapseAllFeatures = () => {
  const tree = featureTreeRef.value;
  if (tree) {
    const keys = [];
    const collectKeys = (nodes) => {
      nodes.forEach(node => {
        if (node.id) keys.push(node.id);
        if (node.sub_features) collectKeys(node.sub_features);
      });
    };
    collectKeys(featuresTree.value);
    
    keys.forEach(key => {
      tree.store.nodesMap[key]?.collapse();
    });
  }
};

// 生命周期
onMounted(() => {
  console.log('链路审查进度页面加载，任务ID:', taskId.value);
  
  // 立即获取一次
  pollProgress();
  
  // 每2秒轮询
  pollTimer = setInterval(pollProgress, 2000);
});

onUnmounted(() => {
  if (pollTimer) {
    clearInterval(pollTimer);
  }
});
</script>

<style scoped>
.chain-review-progress-page {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
  min-height: 100vh;
  background: #f5f7fa;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.page-header h1 {
  margin: 0;
  font-size: 28px;
  color: #303133;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.progress-card {
  margin-bottom: 20px;
}

.stages-card {
  margin-bottom: 20px;
}

.features-card {
  margin-bottom: 20px;
}

.stages-container {
  display: flex;
  flex-direction: column;
  gap: 30px;
  padding: 20px 10px;
}

.stage-section {
  position: relative;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
  padding-left: 12px;
  border-left: 4px solid #409EFF;
}

.discovery-section .section-title {
  border-left-color: #409EFF;
}

.review-section .section-title {
  border-left-color: #67C23A;
}

.stage-steps {
  padding: 0 20px;
}

:deep(.stage-steps .el-step__head) {
  min-width: 80px;
}

:deep(.stage-steps .el-step__title) {
  font-size: 15px;
  font-weight: 500;
}

:deep(.stage-steps .el-step__description) {
  padding-right: 20px;
  font-size: 13px;
  margin-top: 8px;
}

.step-desc {
  color: #606266;
  line-height: 1.5;
  min-height: 20px;
}

.review-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
}

.current-feature {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 18px;
  font-weight: 500;
}

.feature-icon {
  font-size: 24px;
}

.feature-name {
  font-size: 16px;
  font-weight: 500;
}

.review-progress-text {
  font-size: 14px;
  opacity: 0.9;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 600;
}

.progress-text {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

:deep(.el-progress__text) {
  font-size: 16px !important;
}

.timeline-content h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
  color: #303133;
}

.round-summary {
  margin: 4px 0;
  color: #606266;
  font-size: 14px;
}

.round-time {
  color: #909399;
  font-size: 12px;
}

.rotating-icon {
  animation: rotating 2s linear infinite;
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.feature-tree {
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 10px;
  background: #fafafa;
}

.tree-node {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-right: 12px;
}

.node-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.node-label {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}

.sub-count {
  font-size: 12px;
  color: #909399;
  margin-left: 6px;
  font-weight: normal;
}

.node-meta {
  display: flex;
  gap: 6px;
  align-items: center;
}

.actions-card {
  margin-bottom: 20px;
}

.completion-message {
  text-align: center;
  padding: 40px 20px 30px;
}

.completion-message h2 {
  margin: 20px 0 10px;
  font-size: 24px;
  color: #303133;
  font-weight: 600;
}

.completion-message p {
  font-size: 16px;
  color: #606266;
  margin: 0;
}

.completion-message strong {
  color: #409EFF;
  font-size: 18px;
  font-weight: 600;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
  padding: 20px 20px 40px;
}

.action-buttons .el-button {
  min-width: 200px;
  height: 50px;
}
</style>

