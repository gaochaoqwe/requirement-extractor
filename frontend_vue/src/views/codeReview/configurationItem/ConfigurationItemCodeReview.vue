<template>
  <div class="code-review-configuration-item">
    <!-- 审查模式切换 -->
    <div class="review-mode-switch">
      <el-radio-group v-model="reviewMode" size="large" @change="onReviewModeChange">
        <el-radio-button label="function">
          <el-icon><Operation /></el-icon>
          函数审查
        </el-radio-button>
        <el-radio-button label="chain">
          <el-icon><Connection /></el-icon>
          链路审查
        </el-radio-button>
        <el-radio-button label="feature">
          <el-icon><MagicStick /></el-icon>
          功能审查
        </el-radio-button>
      </el-radio-group>
    </div>

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
      
      <!-- 参数配置区域 -->
      <div class="review-configs-container">
        <div class="config-section params-config-section">
          <div class="config-header">
            <el-icon><Setting /></el-icon>
            <span>审查参数配置</span>
          </div>
          <div class="config-content">
            <!-- 入口函数输入（function和chain都需要） -->
            <div v-if="reviewMode === 'function' || reviewMode === 'chain'" class="config-row">
              <div class="config-item">
                <label class="config-label">入口函数/顶层模块：</label>
                <el-input 
                  v-model="entryFunction" 
                  placeholder="C语言填 main，FPGA 可填顶层模块名"
                  style="width: 180px;"
                  clearable
                />
                <span class="config-hint-text">程序入口函数名称</span>
              </div>
            </div>

            <!-- 链路审查：需求文档上传 -->
            <div v-if="reviewMode === 'chain'" class="config-row requirement-upload-row">
              <div class="requirement-upload-area">
                <label class="config-label" style="min-width:100px;">需求文档：</label>
                <el-upload
                  accept=".docx"
                  :show-file-list="false"
                  :before-upload="beforeRequirementUpload"
                  :http-request="uploadRequirement"
                  :disabled="requirementUploading"
                >
                  <el-button
                    :type="requirementText ? 'success' : 'default'"
                    :icon="requirementText ? 'CircleCheck' : 'Upload'"
                    :loading="requirementUploading"
                    size="default"
                  >
                    {{ requirementText ? requirementFileName : '上传需求文档(.docx)' }}
                  </el-button>
                </el-upload>
                <el-button
                  v-if="requirementText"
                  size="small"
                  type="danger"
                  plain
                  icon="Delete"
                  style="margin-left:8px;"
                  @click="clearRequirement"
                >清除</el-button>
                <span class="config-hint-text" style="margin-left:10px;">
                  上传功能需求目录（如 3.1.1 系统初始化），AI将按此划分功能层级
                </span>
              </div>
            </div>

            <!-- 提示信息 -->
            <div class="config-hint">
              <el-alert
                :title="getReviewModeTitle()"
                :type="getReviewModeAlertType()"
                :closable="false"
                show-icon
              >
                <template #default>
                  <div>
                    <p v-if="reviewMode === 'function'">
                      <strong>函数审查</strong>：从入口文件开始，先审查文件，再审查文件内的所有函数
                    </p>
                    <p v-else-if="reviewMode === 'chain'">
                      <strong>链路审查</strong>：使用渐进式AI分析，自动发现项目的功能模块，然后进行链路审查（现已支持 C 与 FPGA）
                    </p>
                    <p v-else-if="reviewMode === 'feature'">
                      <strong>功能审查</strong>：手动配置功能点，使用Agent进行智能审查
                    </p>
                    <p style="margin-top: 8px; color: #909399; font-size: 13px;">
                      当前模式：<strong style="color: #303133;">{{ getReviewModeName() }}</strong>
                    </p>
                  </div>
                </template>
              </el-alert>
            </div>
          </div>
        </div>
      </div>
      
      <div class="button-row">
        <el-button class="main-action-btn" type="primary" :disabled="!fileId || analyzing" :loading="analyzing" @click="startAnalysis">
          {{ startButtonText }}
        </el-button>
      </div>
      
      <!-- 进度条显示 -->
      <transition name="fade">
        <div v-if="analyzing && taskId" class="progress-container" style="margin-top: 20px;">
          <div class="progress-header">
            <div class="progress-info">
              <span class="progress-label">当前任务ID: <strong>{{ taskId }}</strong></span>
            </div>
            <el-button 
              type="danger" 
              size="small" 
              icon="Close"
              plain
              @click="cancelMyTask"
              class="cancel-task-btn"
            >
              取消任务
            </el-button>
          </div>
          <el-progress 
            :percentage="progress" 
            :status="progressStatus"
            :stroke-width="20"
          >
            <template #default="{ percentage }">
              <span class="progress-text">{{ statusText }} {{ percentage }}%</span>
            </template>
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
              icon="Share"
              @click="openCodeMapInNewTab"
              size="large"
            >
              查看代码视图
            </el-button>
          </div>
        </div>
      </transition>
      <el-alert v-if="message" :title="message" :type="messageType" show-icon :closable="false" style="margin-top: 16px;" />
    </div>

    <!-- 任务队列对话框 -->
    <el-dialog
      v-model="taskQueueDialogVisible"
      title="⏳ 当前任务队列已满"
      width="700px"
      :close-on-click-modal="false"
    >
      <div class="queue-dialog-content">
        <el-alert
          type="warning"
          :closable="false"
          show-icon
          style="margin-bottom: 20px;"
        >
          <template #title>
            <div style="font-size: 15px; font-weight: 600;">
              当前受模型并发限制，使用人数已达上限（{{ runningTasksInfo.running_count }}/{{ runningTasksInfo.max_concurrent }}）
            </div>
          </template>
          <div style="margin-top: 8px; font-size: 13px; line-height: 1.6;">
            系统当前有 <strong>{{ runningTasksInfo.running_count }}</strong> 个任务正在执行中，
            请稍后再试或查看下方任务队列了解预计等待时间。
          </div>
        </el-alert>

        <div class="queue-header">
          <h3>
            <el-icon><List /></el-icon>
            运行中的任务队列
          </h3>
          <el-button @click="refreshTaskQueue" icon="Refresh" size="small" :loading="loadingQueue">
            刷新
          </el-button>
        </div>

        <div v-if="loadingQueue" class="queue-loading">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>加载任务队列中...</span>
        </div>

        <div v-else-if="runningTasksInfo.tasks && runningTasksInfo.tasks.length > 0" class="task-queue-list">
          <div
            v-for="(task, index) in runningTasksInfo.tasks"
            :key="task.id"
            class="queue-task-item"
          >
            <div class="queue-task-number">{{ index + 1 }}</div>
            <div class="queue-task-info">
              <div class="queue-task-name">{{ task.task_name }}</div>
              <div class="queue-task-meta">
                <el-tag size="small" :type="task.status === 'processing' ? 'warning' : 'info'">
                  {{ task.status === 'processing' ? '执行中' : '等待中' }}
                </el-tag>
                <span class="meta-text">
                  <el-icon><Clock /></el-icon>
                  已运行 {{ formatTime(task.elapsed_minutes) }}
                </span>
                <span class="meta-text estimated">
                  <el-icon><Timer /></el-icon>
                  预计 {{ formatTime(task.estimated_remaining_minutes) }} 后完成
                </span>
              </div>
              <el-progress
                :percentage="task.progress"
                :stroke-width="8"
                :show-text="true"
                style="margin-top: 8px;"
              />
            </div>
          </div>
        </div>

        <el-empty v-else description="暂无运行中的任务" :image-size="80" />
      </div>

      <template #footer>
        <div class="queue-dialog-footer">
          <div class="footer-tip">
            💡 提示：任务完成后会自动释放执行位，请耐心等待
          </div>
          <el-button type="primary" @click="taskQueueDialogVisible = false">
            我知道了
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 管理员取消任务对话框（仍保留，仅支持取消，不在此页做暂停/恢复） -->
    <el-dialog
      v-model="adminCancelDialogVisible"
      title="🔐 管理员取消任务"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="adminCancelForm" label-width="100px" label-position="right">
        <el-form-item label="任务ID">
          <el-input 
            v-model="adminCancelForm.taskId" 
            placeholder="请输入要取消的任务ID"
            type="number"
            clearable
          />
          <div class="form-hint">当前正在运行的任务ID: {{ taskId || '无' }}</div>
        </el-form-item>
        <el-form-item label="管理员密码">
          <el-input 
            v-model="adminCancelForm.password" 
            type="password" 
            placeholder="请输入管理员密码"
            show-password
            clearable
            @keyup.enter="confirmCancelTask"
          />
          <div class="form-hint warning-hint">⚠️ 此操作将立即停止任务执行，无法恢复</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="adminCancelDialogVisible = false">取消</el-button>
          <el-button 
            type="danger"
            :loading="cancelingTask"
            :disabled="!adminCancelForm.taskId || !adminCancelForm.password"
            @click="confirmCancelTask"
          >
            确认取消任务
          </el-button>
        </span>
      </template>
    </el-dialog>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import UploadCodeFile from './upload/UploadCodeFile.vue';
import DownloadAnalysisResult from './download/DownloadAnalysisResult.vue';
import { Document, Share, Setting, MagicStick, Operation, Connection, SuccessFilled, Close, List, Clock, Timer, Refresh, Loading } from '@element-plus/icons-vue';
import { ElMessage, ElNotification, ElMessageBox } from 'element-plus';
import axios from 'axios';

const router = useRouter();
const authStore = useAuthStore();

// 审查模式
const reviewMode = ref('function'); // function: 函数审查, chain: 链路审查, feature: 功能审查

const codeFileId = ref('');
const analyzing = ref(false);
const taskId = ref('');
const analysisDone = ref(false);
const message = ref('');
const messageType = ref('success');
const progress = ref(0);
const status = ref('pending');

// 审查参数配置
const entryFunction = ref('main');  // 默认填充main

// 链路审查：需求文档
const requirementText = ref('');
const requirementFileName = ref('');
const requirementUploading = ref(false);

function beforeRequirementUpload(file) {
  if (!file.name.toLowerCase().endsWith('.docx')) {
    ElMessage.error('只支持 .docx 格式的需求文档');
    return false;
  }
  return true;
}

async function uploadRequirement(options) {
  requirementUploading.value = true;
  const formData = new FormData();
  formData.append('file', options.file);
  try {
    const res = await axios.post('/api/codeReview/upload_requirement', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    requirementText.value = res.data.text || '';
    requirementFileName.value = options.file.name;
    ElMessage.success(`需求文档解析成功，共 ${res.data.char_count} 个字符`);
  } catch (e) {
    ElMessage.error('需求文档上传失败：' + (e.response?.data?.detail || e.message));
  } finally {
    requirementUploading.value = false;
  }
}

function clearRequirement() {
  requirementText.value = '';
  requirementFileName.value = '';
}


// 计算属性
const fileId = computed(() => codeFileId.value);
const progressStatus = computed(() => {
  if (status.value === 'completed') return 'success';
  if (status.value === 'failed') return 'exception';
  return '';
});
const statusText = computed(() => {
  if (status.value === 'pending') return '准备开始...';
  if (status.value === 'processing') {
    if (progress.value < 20) return '正在扫描代码文件...';
    if (progress.value < 60) return '正在分析代码结构...';
    if (progress.value < 90) return '正在执行审查...';
    return '正在生成报告...';
  }
  if (status.value === 'completed') return '分析完成';
  if (status.value === 'failed') return '分析失败';
  return '处理中...';
});

// 获取审查模式名称
const getReviewModeName = () => {
  const names = {
    'function': '函数审查',
    'chain': '链路审查',
    'feature': '功能审查'
  };
  return names[reviewMode.value] || '代码审查';
};

const getReviewModeTitle = () => {
  return getReviewModeName() + '模式';
};

const getReviewModeAlertType = () => {
  const types = {
    'function': 'info',
    'chain': 'success',
    'feature': 'warning'
  };
  return types[reviewMode.value] || 'info';
};

// 计算按钮文字
const startButtonText = computed(() => {
  const buttonTexts = {
    'function': '开始函数审查',
    'chain': '开始链路审查',
    'feature': '开始功能审查'
  };
  return buttonTexts[reviewMode.value] || '开始代码审查';
});


// 组件挂载时的初始化（链路审查不再需要领域和软件类型）
onMounted(async () => {
  // 无需初始化
});

// 审查模式切换处理
function onReviewModeChange(mode) {
  console.log('切换审查模式:', mode);
  // 切换模式时清空之前的状态
  message.value = '';
  analyzing.value = false;
  analysisDone.value = false;
  progress.value = 0;
  // 不做其他操作，留在当前配置页面
}

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

// 管理员取消任务相关（仅支持取消，不在此页做暂停/恢复）
const adminCancelDialogVisible = ref(false);
const cancelingTask = ref(false);
const adminCancelForm = ref({
  taskId: '',
  password: ''
});

// 任务队列对话框相关
const taskQueueDialogVisible = ref(false);
const loadingQueue = ref(false);
const runningTasksInfo = ref({
  running_count: 0,
  max_concurrent: 0,
  tasks: []
});

async function startAnalysis() {
  // 防止重复提交
  if (isSubmitting.value) {
    console.log('分析请求正在进行中，请勿重复提交');
    return;
  }
  
  // 检查是否已登录
  if (!authStore.isAuthenticated || !authStore.user) {
    message.value = '请先登录';
    messageType.value = 'warning';
    ElMessage.warning('请先登录后再进行代码审查');
    // 跳转到登录页面
    router.push('/login');
    return;
  }
  
  // 检查file_id是否有效
  if (!codeFileId.value) {
    message.value = '错误：未获取到有效的文件ID，请重新上传文件';
    messageType.value = 'error';
    console.error('启动分析失败：file_id为空');
    return;
  }
  
  // 功能审查模式：直接跳转到功能审查页面，不创建任务
  if (reviewMode.value === 'feature') {
    message.value = '正在跳转到功能审查页面...';
    messageType.value = 'success';
    
    setTimeout(() => {
      // 使用file_id作为参数跳转
      router.push(`/code-review/feature-review/${codeFileId.value}`);
    }, 500);
    return;
  }
  
  // 函数审查和链路审查：需要创建任务
  // 设置提交状态
  isSubmitting.value = true;
  analyzing.value = true;
  analysisDone.value = false;
  message.value = '';
  progress.value = 0;
  status.value = 'pending';
  
  // 构建请求数据（不再传递tester_name，后端会从session获取）
  const requestData = {
    file_id: codeFileId.value,
    review_mode: reviewMode.value,
    entry_function: entryFunction.value || 'main',
    requirement_text: reviewMode.value === 'chain' ? (requirementText.value || '') : undefined
  }
  
  console.log('开始代码审查，请求数据:', requestData);
  
  try {
    const response = await axios.post('/api/codeReview/start_analysis', requestData);
    
    console.log('分析请求响应:', response.data);
    
    if (response.data && response.data.task_id) {
      taskId.value = response.data.task_id;
      console.log('获取到task_id:', taskId.value);
      
      // 显示代码视图地址（如果后端返回了）
      if (response.data.codemap_url) {
        const codeMapUrl = response.data.codemap_url;
        
        ElNotification({
          title: '✅ 审查任务已启动',
          message: `
            <div style="margin-top: 12px;">
              <div style="background: #f0f9ff; padding: 12px; border-radius: 6px; border-left: 3px solid #409EFF; margin-bottom: 12px;">
                <div style="color: #606266; font-size: 13px; margin-bottom: 6px;">📍 代码视图地址：</div>
                <div style="color: #303133; font-size: 14px; font-family: monospace; word-break: break-all;">${codeMapUrl}</div>
              </div>
              <a href="${codeMapUrl}" target="_blank" 
                 style="display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; 
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        color: white; text-decoration: none; border-radius: 6px; 
                        font-weight: 500; font-size: 14px; transition: all 0.3s; 
                        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);"
                 onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(102, 126, 234, 0.4)';"
                 onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 8px rgba(102, 126, 234, 0.3)';">
                🔗 立即查看代码视图
              </a>
            </div>
          `,
          dangerouslyUseHTMLString: true,
          type: 'success',
          duration: 0,  // 不自动关闭
          position: 'top-right',
          showClose: true,
          offset: 80
        });

        if (reviewMode.value === 'function') {
          const fileName = `重要：代码视图地址，查看审查结果使用.txt`;
          const blob = new Blob([codeMapUrl], { type: 'text/plain;charset=utf-8' });
          const link = document.createElement('a');
          link.href = URL.createObjectURL(blob);
          link.download = fileName;
          document.body.appendChild(link);
          link.click();
          setTimeout(() => {
            URL.revokeObjectURL(link.href);
            document.body.removeChild(link);
          }, 0);
        }
      }
      
      // 根据模式选择不同的处理逻辑
      if (reviewMode.value === 'chain') {
        // 链路审查：跳转到实时进度页面
        message.value = '链路审查已启动，正在跳转到进度页面...';
        messageType.value = 'success';
        
        setTimeout(() => {
          router.push(`/code-review/chain-progress/${taskId.value}`);
        }, 1000);
      } else {
        // 函数审查：轮询进度
        message.value = `${response.data.analysis_mode}已启动`;
        messageType.value = 'info';
        pollTaskProgress();
      }
    } else {
      throw new Error(response.data.error || '服务端未返回task_id');
    }
  } catch (e) {
    console.error('分析请求失败:', e);
    // 并发上限提示 - 显示任务队列
    if (e && e.response && e.response.status === 429) {
      message.value = '当前受模型并发限制，使用人数已达上限';
      messageType.value = 'warning';
      
      // 获取并显示任务队列
      await showTaskQueueDialog();
    } else if (e && e.response && e.response.status === 409) {
      const tip = '检测到重复任务：同名且同大小的代码库正在进行审查，请稍后再试';
      try {
        await ElMessageBox.alert(tip, '提示', { type: 'warning' });
      } catch (_) {}
      message.value = tip;
      messageType.value = 'warning';
    } else {
      message.value = '启动代码审查失败：' + (e.message || e);
      messageType.value = 'error';
    }
    analyzing.value = false;
    taskId.value = ''; // 重置任务ID
  } finally {
    // 无论成功失败都重置提交状态
    isSubmitting.value = false;
  }
}

async function pollTaskProgress() {
  console.log('[ConfigurationItemCodeReview] pollTaskProgress enter', {
    taskId: taskId.value,
    analyzing: analyzing.value,
    reviewMode: reviewMode.value,
    progress: progress.value,
    status: status.value
  });
  
  if (!taskId.value || !analyzing.value) {
    console.log('[ConfigurationItemCodeReview] pollTaskProgress exit early', {
      taskId: taskId.value,
      analyzing: analyzing.value
    });
    return;
  }
  
  try {
    const response = await axios.get(`/api/codeReview/task/${taskId.value}/progress`);
    console.log('[ConfigurationItemCodeReview] 任务进度响应', response.data);
    
    if (response.data) {
      // 直接使用服务器返回的进度值
      progress.value = response.data.progress;
      status.value = response.data.status;
      
      console.log('[ConfigurationItemCodeReview] 更新进度状态', {
        taskId: taskId.value,
        progress: progress.value,
        status: status.value,
        analyzing: analyzing.value
      });
      
      // 检查任务是否完成/暂停
      if (status.value === 'completed') {
        console.log('[ConfigurationItemCodeReview] task completed, stop polling', {
          taskId: taskId.value,
          progress: progress.value
        });
        analyzing.value = false;
        analysisDone.value = true;
        message.value = '代码审查完成，可以下载结果或查看代码地图';
        messageType.value = 'success';
      } else if (status.value === 'failed') {
        console.log('[ConfigurationItemCodeReview] task failed, stop polling', {
          taskId: taskId.value,
          progress: progress.value
        });
        analyzing.value = false;
        message.value = '代码审查失败';
        messageType.value = 'error';
      } else if (status.value === 'paused') {
        console.log('[ConfigurationItemCodeReview] task paused, stop polling', {
          taskId: taskId.value,
          progress: progress.value
        });
        analyzing.value = false;
        message.value = '代码审查已暂停';
        messageType.value = 'warning';
      } else {
        // 继续轮询，间隔调整为3秒
        console.log('[ConfigurationItemCodeReview] schedule next poll', {
          taskId: taskId.value,
          nextInterval: 3000,
          status: status.value
        });
        setTimeout(pollTaskProgress, 3000);
      }
    }
  } catch (e) {
    console.error('获取任务进度失败:', e);
    message.value = '获取任务进度失败';
    messageType.value = 'error';
    analyzing.value = false;
  }
}

function openCodeMapInNewTab() {
  // 在新标签页中打开代码地图
  const mode = reviewMode.value === 'chain' ? '?mode=chain' : ''
  const url = `/codemap/${taskId.value}${mode}`;
  window.open(url, '_blank');
}

// 显示任务队列对话框
async function showTaskQueueDialog() {
  taskQueueDialogVisible.value = true;
  await refreshTaskQueue();
}

// 刷新任务队列
async function refreshTaskQueue() {
  loadingQueue.value = true;
  
  try {
    const response = await axios.get('/api/codeReview/running_tasks_queue');
    
    if (response.data) {
      runningTasksInfo.value = response.data;
      console.log('任务队列信息:', runningTasksInfo.value);
    }
  } catch (error) {
    console.error('获取任务队列失败:', error);
    ElMessage.error('获取任务队列信息失败');
  } finally {
    loadingQueue.value = false;
  }
}

// 格式化时间（分钟转为可读格式）
function formatTime(minutes) {
  if (!minutes || minutes < 0) return '未知';
  
  if (minutes < 1) {
    return '不到1分钟';
  } else if (minutes < 60) {
    return `${Math.round(minutes)}分钟`;
  } else if (minutes < 1440) {
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    return mins > 0 ? `${hours}小时${mins}分钟` : `${hours}小时`;
  } else {
    const days = Math.floor(minutes / 1440);
    const hours = Math.floor((minutes % 1440) / 60);
    return hours > 0 ? `${days}天${hours}小时` : `${days}天`;
  }
}

// 取消我的任务（无需密码）
async function cancelMyTask() {
  try {
    await ElMessageBox.confirm(
      `确定要取消当前任务吗？任务ID: ${taskId.value}`,
      '确认取消',
      {
        confirmButtonText: '确认取消',
        cancelButtonText: '继续执行',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    );
    
    // 执行取消（使用新的无需密码的API）
    const response = await axios.post(`/api/codeReview/cancel_my_task/${taskId.value}`);
    
    if (response.data && response.data.success) {
      ElMessage.success('任务已成功取消');
      
      // 更新UI状态
      analyzing.value = false;
      analysisDone.value = false;
      status.value = 'cancelled';
      message.value = '任务已取消';
      messageType.value = 'warning';
    }
  } catch (error) {
    if (error === 'cancel') {
      // 用户点击了"继续执行"
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

// 显示管理员取消对话框（保留，仅支持取消）
function showAdminCancelDialog() {
  adminCancelForm.value.taskId = taskId.value || '';
  adminCancelForm.value.password = '';
  adminCancelDialogVisible.value = true;
}

// 确认取消任务
async function confirmCancelTask() {
  const cancelTaskId = adminCancelForm.value.taskId;
  const password = adminCancelForm.value.password;
  
  if (!cancelTaskId || !password) {
    ElMessage.warning('请填写任务ID和管理员密码');
    return;
  }
  
  try {
    cancelingTask.value = true;
    
    const response = await axios.post(`/api/codeReview/cancel_task/${cancelTaskId}`, {
      password: password
    });
    
    console.log('取消任务响应:', response.data);
    
    if (response.data && response.data.success) {
      ElMessage.success(response.data.message);
      adminCancelDialogVisible.value = false;
      
      // 如果取消的是当前任务，更新UI状态
      if (cancelTaskId == taskId.value) {
        analyzing.value = false;
        analysisDone.value = false;
        status.value = 'cancelled';
        message.value = '任务已被管理员取消';
        messageType.value = 'warning';
      }
    } else {
      throw new Error(response.data.message || '取消任务失败');
    }
  } catch (error) {
    console.error('取消任务失败:', error);
    
    let errorMsg = '取消任务失败';
    if (error.response) {
      if (error.response.status === 403) {
        errorMsg = '管理员密码错误';
      } else if (error.response.status === 404) {
        errorMsg = '任务不存在';
      } else if (error.response.status === 400) {
        errorMsg = error.response.data.detail || '任务状态不支持取消';
      } else if (error.response.data && error.response.data.detail) {
        errorMsg = error.response.data.detail;
      }
    }
    
    ElMessage.error(errorMsg);
  } finally {
    cancelingTask.value = false;
  }
}
</script>

<style scoped>
/* 任务队列对话框样式 */
.queue-dialog-content {
  max-height: 500px;
  overflow-y: auto;
}

.queue-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 2px solid #e4e7ed;
}

.queue-header h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.queue-loading {
  text-align: center;
  padding: 40px;
  color: #909399;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  font-size: 14px;
}

.queue-loading .el-icon {
  font-size: 32px;
}

.task-queue-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.queue-task-item {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  transition: all 0.3s;
}

.queue-task-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.15);
  transform: translateY(-2px);
}

.queue-task-number {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: white;
  font-weight: bold;
  font-size: 16px;
  border-radius: 50%;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
}

.queue-task-info {
  flex: 1;
  min-width: 0;
}

.queue-task-name {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.queue-task-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}

.meta-text {
  font-size: 13px;
  color: #606266;
  display: flex;
  align-items: center;
  gap: 4px;
}

.meta-text.estimated {
  color: #e6a23c;
  font-weight: 600;
}

.queue-dialog-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
}

.footer-tip {
  font-size: 13px;
  color: #909399;
  line-height: 1.6;
}

/* 暂停任务列表样式 */
.paused-tasks-header {
  margin-bottom: 16px;
}

.loading-container {
  text-align: center;
  padding: 40px;
  color: #909399;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  font-size: 14px;
}

.loading-container .el-icon {
  font-size: 32px;
}

.code-review-configuration-item {
  padding: 10px 20px 20px 20px;
  min-height: 100vh;
  overflow-y: auto;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
}

/* 审查模式切换 */
.review-mode-switch {
  display: flex;
  justify-content: center;
  margin: 20px auto 30px auto;
  max-width: 2000px;
}

.review-mode-switch :deep(.el-radio-button__inner) {
  padding: 14px 30px;
  font-size: 16px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
}

.review-mode-switch :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}
.analysis-panel {
  background: #fff;
  border-radius: 12px;
  padding: 32px 40px 32px 40px;
  box-shadow: 0 8px 32px rgba(32, 101, 209, 0.08);
  max-width: 2000px;
  width: 98%;
  margin: 10px auto 40px auto;
}
.upload-container {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
}
.button-row {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin: 20px 0 24px 0;
}
.main-action-btn {
  min-width: 200px;
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

/* 业务审查配置容器 */
.review-configs-container {
  display: flex;
  justify-content: center;
  margin: 24px auto;
  max-width: 1200px;
}

/* 参数配置区域样式 */
.config-section.params-config-section {
  background: #f0f7ff;
  border: 1px solid #409EFF;
  border-radius: 8px;
  padding: 20px 24px;
  width: 100%;
  max-width: 900px;
}

.config-header {
  font-size: 1.1rem;
  color: #34495e;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  font-weight: 500;
}

.config-header .el-icon {
  margin-right: 8px;
  color: #67c23a;
}

.config-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.config-row {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 8px;
}

.params-row {
  justify-content: flex-start;
  flex-wrap: nowrap;
  gap: 0;
  padding: 8px 0;
  align-items: center;
}

/* 响应式布局 */
@media (max-width: 950px) {
  .params-row {
    flex-wrap: wrap;
  }
  
  .params-row .config-item:nth-child(3) {
    margin-left: 0 !important;
    margin-top: 8px;
  }
  
  .config-section.params-config-section {
    max-width: 100%;
  }
}

@media (max-width: 768px) {
  .code-review-configuration-item {
    padding: 5px 10px 20px 10px;
    min-height: 100vh;
  }
  
  .analysis-panel {
    max-width: 95%;
    padding: 24px 16px;
    margin: 5px auto 30px auto;
  }
  
  .review-configs-container {
    max-width: 100%;
    margin: 16px 0;
  }
  
  .params-row {
    flex-direction: column;
    align-items: flex-start;
    flex-wrap: nowrap;
  }
  
  .params-row .config-item {
    margin-left: 0 !important;
    margin-bottom: 8px;
    width: 100%;
  }
  
  .config-section.params-config-section {
    padding: 16px;
  }
  
  .business-config {
    padding: 10px 16px;
  }
}

.config-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.config-label {
  font-size: 14px;
  color: #606266;
  min-width: 80px;
  text-align: right;
  font-weight: 500;
}

.config-hint {
  margin-top: 8px;
}

.config-hint .el-alert {
  border-radius: 6px;
}

.config-hint .el-alert .el-alert__content {
  padding: 0;
}

.config-hint p {
  margin: 4px 0;
  font-size: 13px;
  line-height: 1.4;
}

/* 业务审查配置行样式 */
.business-config {
  background: #f8f9fa;
  padding: 12px 20px;
  border-radius: 8px;
  margin: 8px 0;
  border-left: 4px solid #409eff;
}

.config-hint-text {
  font-size: 12px;
  color: #909399;
  margin-left: 8px;
}

/* 需求文档上传行 */
.requirement-upload-row {
  margin-top: 12px;
}

.requirement-upload-area {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px 16px;
  background: #f0f7ff;
  border: 1px dashed #409EFF;
  border-radius: 8px;
  width: 100%;
}

/* 必填项样式 */
.required-label::before {
  content: '*';
  color: #f56c6c;
  margin-right: 4px;
  font-weight: bold;
}

.required-hint {
  color: #f56c6c !important;
  font-weight: 500;
}

.business-config .config-label {
  color: #409eff;
  font-weight: 600;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity .3s;
}
.fade-enter, .fade-leave-to {
  opacity: 0;
}

/* 进度条容器样式 */
.progress-container {
  max-width: 800px;
  margin: 20px auto;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e4e7ed;
}

.progress-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-label {
  font-size: 14px;
  color: #606266;
}

.progress-label strong {
  color: #409EFF;
  font-size: 16px;
}

.cancel-task-btn {
  min-width: 120px;
}

.progress-text {
  font-size: 14px;
  font-weight: 500;
  color: #606266;
  white-space: nowrap;
}

/* 对话框样式 */
.form-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}

.form-hint.warning-hint {
  color: #E6A23C;
  font-weight: 500;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 代码地图对话框样式 */
:deep(.code-map-dialog) {
  height: 90vh;
}

:deep(.code-map-dialog .el-dialog__body) {
  padding: 0;
  height: calc(90vh - 120px);
}

:deep(.code-map-dialog .el-dialog__header) {
  padding: 20px 20px 10px 20px;
}

:deep(.code-map-dialog .el-dialog__footer) {
  padding: 10px 20px 20px 20px;
}

</style>

<style>
/* 全局样式确保页面可以滚动 */
html, body {
  overflow-y: auto !important;
  height: auto !important;
}
</style>
