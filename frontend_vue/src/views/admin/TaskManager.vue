<template>
  <div class="admin-task-manager">
    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 页面标题 -->
      <div class="page-header">
        <div class="header-left">
          <h1>
            <el-icon><Setting /></el-icon>
            任务管理中心
          </h1>
          <el-tag type="danger" size="large">管理员模式</el-tag>
        </div>
        <div class="header-right">
          <el-button @click="goBack" icon="Back">返回首页</el-button>
          <el-button type="primary" @click="goDataPanel">数据查看与导出</el-button>
          <el-button type="success" icon="UserFilled" @click="goUserManage">人员管理</el-button>
          <el-button @click="refreshTasks" icon="Refresh" :loading="loading">刷新</el-button>
        </div>
      </div>

      <!-- 测试类型切换 -->
      <el-card class="mode-switch-card">
        <div class="mode-switch-row">
          <div class="mode-label">
            <el-icon><Operation /></el-icon>
            <span>测试类型：</span>
          </div>
          <el-segmented v-model="testMode" :options="testModeOptions" size="large" @change="handleTestModeChange" />
          <div class="mode-description">
            <el-tag :type="testMode === 'configuration' ? 'success' : 'warning'">
              {{ testMode === 'configuration' ? '配置项测试' : '回归测试' }}
            </el-tag>
          </div>
        </div>
      </el-card>

      <!-- 统计卡片 -->
      <div class="stats-cards">
        <el-card class="stat-card running">
          <div class="stat-icon">
            <el-icon><Loading /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ runningCount }}</div>
            <div class="stat-label">运行中</div>
          </div>
        </el-card>
        <el-card class="stat-card paused">
          <div class="stat-icon">
            <el-icon><VideoPause /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ pausedCount }}</div>
            <div class="stat-label">已暂停</div>
          </div>
        </el-card>
        <el-card class="stat-card total">
          <div class="stat-icon">
            <el-icon><List /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ totalCount }}</div>
            <div class="stat-label">总任务数</div>
          </div>
        </el-card>
      </div>

      <!-- 筛选和操作栏 -->
      <el-card class="filter-card">
        <div class="filter-row">
          <div class="filter-left">
            <el-radio-group v-model="statusFilter" @change="handleFilterChange">
              <el-radio-button value="all">全部任务</el-radio-button>
              <el-radio-button value="running">运行中</el-radio-button>
              <el-radio-button value="paused">已暂停</el-radio-button>
              <el-radio-button value="completed">已完成</el-radio-button>
              <el-radio-button value="failed">失败</el-radio-button>
              <el-radio-button value="cancelled">已取消</el-radio-button>
            </el-radio-group>
          </div>
          <div class="filter-right">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索任务名称或ID"
              clearable
              style="width: 300px;"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>
        </div>
      </el-card>

      <!-- 任务列表 -->
      <el-card class="task-list-card">
        <div v-if="loading" class="loading-container">
          <el-icon class="is-loading" :size="50"><Loading /></el-icon>
          <p>加载任务列表中...</p>
        </div>

        <el-empty v-else-if="filteredTasks.length === 0" description="暂无任务" />

        <div v-else class="task-list">
          <div
            v-for="task in filteredTasks"
            :key="task.id"
            class="task-item"
            :class="{'can-cancel': task.can_cancel}"
          >
            <div class="task-main">
              <div class="task-id">
                <el-tag size="large" type="info">ID: {{ task.id }}</el-tag>
              </div>
              <div class="task-info">
                <div class="task-name">{{ task.task_name }}</div>
                <div class="task-meta">
                  <span class="meta-item">
                    <el-icon><Clock /></el-icon>
                    {{ formatTime(task.created_at) }}
                  </span>
                  <span class="meta-item">
                    <el-icon><Document /></el-icon>
                    {{ task.analysis_type || 'code_review' }}
                  </span>
                </div>
              </div>
              <div class="task-status">
                <el-tag :type="getStatusType(task.status)" size="large">
                  {{ getStatusText(task.status) }}
                </el-tag>
                <el-progress
                  v-if="typeof task.progress === 'number' && task.progress > 0"
                  :percentage="task.progress"
                  :stroke-width="8"
                  :status="task.status === 'failed' ? 'exception' : task.status === 'completed' ? 'success' : undefined"
                  style="margin-top: 8px; width: 200px;"
                />
                <div v-else class="task-progress-placeholder">
                  <span v-if="task.status === 'processing'">进度加载中...</span>
                </div>
              </div>
              <div class="task-actions">
                <!-- 暂停的任务显示恢复按钮 -->
                <el-button
                  v-if="task.status === 'paused'"
                  type="success"
                  size="small"
                  icon="VideoPlay"
                  @click="resumeTask(task.id, task.task_name)"
                  :loading="resumingTaskId === task.id"
                >
                  继续执行
                </el-button>
                <!-- 运行中的任务显示暂停和取消按钮 -->
                <template v-else-if="task.can_cancel">
                  <el-button
                    type="warning"
                    size="small"
                    icon="VideoPause"
                    @click="pauseTask(task.id, task.task_name)"
                  >
                    暂停
                  </el-button>
                  <el-button
                    type="danger"
                    size="small"
                    icon="Close"
                    @click="cancelTask(task.id, task.task_name)"
                  >
                    取消
                  </el-button>
                </template>
                <!-- 其他状态 -->
                <el-button
                  v-else
                  type="info"
                  size="small"
                  disabled
                >
                  {{ task.status === 'completed' ? '已完成' : '不可操作' }}
                </el-button>
              </div>
            </div>
            <div v-if="task.task_description" class="task-description">
              {{ task.task_description }}
            </div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Setting, Loading, List, Search, Clock, Document, Back, Refresh, Close, VideoPlay, VideoPause, Operation, UserFilled } from '@element-plus/icons-vue';
import axios from 'axios';

const router = useRouter();


// 测试模式切换
const testMode = ref('configuration'); // 'configuration' | 'regression'
const testModeOptions = [
  { label: '配置项测试', value: 'configuration' },
  { label: '回归测试', value: 'regression' }
];

// 任务列表相关
const tasks = ref([]);
const loading = ref(false);
const statusFilter = ref('all');
const searchKeyword = ref('');
const resumingTaskId = ref(null);

// 统计数据
const runningCount = computed(() => {
  return tasks.value.filter(t => t.status === 'pending' || t.status === 'processing').length;
});

const pausedCount = computed(() => {
  return tasks.value.filter(t => t.status === 'paused').length;
});

const totalCount = computed(() => {
  return tasks.value.length;
});

// 过滤任务
const filteredTasks = computed(() => {
  let result = tasks.value;
  
  // 状态过滤
  if (statusFilter.value === 'running') {
    result = result.filter(t => t.status === 'pending' || t.status === 'processing');
  } else if (statusFilter.value !== 'all') {
    result = result.filter(t => t.status === statusFilter.value);
  }
  
  // 关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase();
    result = result.filter(t => 
      t.task_name.toLowerCase().includes(keyword) ||
      t.id.toString().includes(keyword)
    );
  }
  
  return result;
});

// 跳转到任务数据面板
function goDataPanel() {
  router.push('/admin-task-data');
}

// 跳转到人员管理页面
function goUserManage() {
  router.push('/admin-user-manage');
}

// 获取API基础路径
function getApiBasePath() {
  return testMode.value === 'configuration' 
    ? '/api/codeReview' 
    : '/api/codeReview/regressionTest';
}

// 处理测试模式切换
function handleTestModeChange() {
  console.log('切换测试模式:', testMode.value);
  refreshTasks();
}

// 刷新任务列表
async function refreshTasks() {
  loading.value = true;
  
  try {
    const apiPath = getApiBasePath();
    const response = await axios.get(`${apiPath}/admin/tasks`, {
      params: {
        limit: 100
      }
    });
    
    if (response.data && response.data.tasks) {
      tasks.value = response.data.tasks;
      console.log(`[${testMode.value}] 加载了 ${tasks.value.length} 个任务`);
    }
  } catch (error) {
    console.error('获取任务列表失败:', error);
    ElMessage.error('获取任务列表失败');
  } finally {
    loading.value = false;
  }
}

// 取消任务
async function cancelTask(taskId, taskName) {
  try {
    await ElMessageBox.confirm(
      `确定要取消任务 "${taskName}" (ID: ${taskId}) 吗？此操作不可恢复。`,
      '确认取消',
      {
        confirmButtonText: '确认取消',
        cancelButtonText: '放弃',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    );
    
    // 执行取消
    const apiPath = getApiBasePath();
    const response = await axios.post(`${apiPath}/cancel_task/${taskId}`);
    
    if (response.data && response.data.success) {
      ElMessage.success(`任务 ${taskId} 已成功取消`);
      // 刷新列表
      await refreshTasks();
    }
  } catch (error) {
    if (error === 'cancel') {
      // 用户取消操作
      return;
    }
    
    console.error('取消任务失败:', error);
    let errorMsg = '取消任务失败';
    
    if (error.response && error.response.data && error.response.data.detail) {
      errorMsg = error.response.data.detail;
    }
    
    ElMessage.error(errorMsg);
  }
}

// 处理状态筛选变化
function handleFilterChange() {
  console.log('筛选条件变更:', statusFilter.value);
}

// 格式化时间
function formatTime(timeStr) {
  if (!timeStr) return '-';
  const date = new Date(timeStr);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}

// 获取状态类型
function getStatusType(status) {
  const types = {
    'pending': 'info',
    'processing': 'warning',
    'completed': 'success',
    'failed': 'danger',
    'cancelled': 'info',
    'paused': 'warning'
  };
  return types[status] || 'info';
}

// 获取状态文本
function getStatusText(status) {
  const texts = {
    'pending': '等待中',
    'processing': '执行中',
    'completed': '已完成',
    'failed': '失败',
    'cancelled': '已取消',
    'paused': '已暂停'
  };
  return texts[status] || status;
}

// 暂停任务
async function pauseTask(taskId, taskName) {
  try {
    const apiPath = getApiBasePath();
    const response = await axios.post(`${apiPath}/cancel_task/${taskId}`, {
      pause: true
    });
    
    if (response.data && response.data.success) {
      ElMessage.success(`任务 ${taskId} 已暂停，可在后端重启后恢复`);
      await refreshTasks();
    }
  } catch (error) {
    if (error === 'cancel') {
      return;
    }
    
    console.error('暂停任务失败:', error);
    let errorMsg = '暂停任务失败';
    
    if (error.response && error.response.data && error.response.data.detail) {
      errorMsg = error.response.data.detail;
    }
    
    ElMessage.error(errorMsg);
  }
}

// 恢复任务
async function resumeTask(taskId, taskName) {
  try {
    await ElMessageBox.confirm(
      `确定要恢复任务 "${taskName}" (ID: ${taskId}) 吗？任务将从上次中断的位置继续执行。`,
      '确认恢复',
      {
        confirmButtonText: '确认恢复',
        cancelButtonText: '取消',
        type: 'success'
      }
    );
    
    resumingTaskId.value = taskId;
    
    // 执行恢复
    const apiPath = getApiBasePath();
    const response = await axios.post(`${apiPath}/resume_task/${taskId}`);
    
    if (response.data && response.data.success) {
      ElMessage.success(response.data.message);
      // 刷新列表
      await refreshTasks();
    }
  } catch (error) {
    if (error === 'cancel') {
      return;
    }
    
    console.error('恢复任务失败:', error);
    let errorMsg = '恢复任务失败';
    
    if (error.response && error.response.data && error.response.data.detail) {
      errorMsg = error.response.data.detail;
    }
    
    ElMessage.error(errorMsg);
  } finally {
    resumingTaskId.value = null;
  }
}

// 返回首页
function goBack() {
  router.push('/');
}

// 页面加载时自动加载任务列表
onMounted(() => {
  console.log('管理员任务管理页面加载');
  refreshTasks();
});
</script>

<style scoped>
.admin-task-manager {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 20px;
}

.main-content {
  max-width: 1400px;
  margin: 0 auto;
}

/* 页面标题 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-left h1 {
  font-size: 28px;
  color: #303133;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-right {
  display: flex;
  gap: 12px;
}

/* 测试类型切换卡片 */
.mode-switch-card {
  margin-bottom: 24px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.mode-switch-card :deep(.el-card__body) {
  padding: 20px;
}

.mode-switch-row {
  display: flex;
  align-items: center;
  gap: 20px;
}

.mode-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  min-width: 110px;
}

.mode-description {
  margin-left: auto;
}

/* 统计卡片 */
.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  border-radius: 12px;
  overflow: hidden;
}

.stat-card :deep(.el-card__body) {
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
}

.stat-card.running {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.stat-card.paused {
  background: linear-gradient(135deg, #ffa726 0%, #fb8c00 100%);
  color: white;
}

.stat-card.total {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.stat-icon {
  font-size: 48px;
  opacity: 0.9;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 36px;
  font-weight: bold;
  line-height: 1;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
}

/* 筛选卡片 */
.filter-card {
  margin-bottom: 24px;
  border-radius: 12px;
}

.filter-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
}

.filter-left {
  flex: 1;
}

/* 任务列表卡片 */
.task-list-card {
  border-radius: 12px;
  min-height: 400px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
  color: #909399;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.task-item {
  padding: 20px;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  background: #fafafa;
  transition: all 0.3s;
}

.task-item.can-cancel {
  border-color: #fca5a5;
  background: #fef2f2;
}

.task-item:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.task-main {
  display: flex;
  align-items: center;
  gap: 20px;
}

.task-id {
  min-width: 80px;
}

.task-info {
  flex: 1;
}

.task-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.task-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #909399;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.task-status {
  min-width: 240px;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.task-actions {
  min-width: 180px;
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.task-description {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #e4e7ed;
  font-size: 13px;
  color: #606266;
}

/* 响应式 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .filter-row {
    flex-direction: column;
    align-items: stretch;
  }
  
  .task-main {
    flex-wrap: wrap;
  }
}
</style>

