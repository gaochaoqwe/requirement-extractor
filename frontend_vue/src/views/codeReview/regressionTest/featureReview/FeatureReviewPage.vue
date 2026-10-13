<template>
  <div class="feature-review-page">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-button :icon="ArrowLeft" @click="$router.back()">返回</el-button>
        <span class="page-title">功能审查</span>
        <el-tag v-if="fileId" type="success" size="default" style="margin-left: 12px;">
          <el-icon><CircleCheck /></el-icon>
          代码库已加载
        </el-tag>
      </div>
      <div class="toolbar-right">
        <!-- 上传代码库按钮已移除，统一在初始界面上传 -->
      </div>
    </div>

    <!-- 执行过程面板 -->
    <ReviewProcessPanel
      :visible="showReviewProcess"
      :feature-name="reviewingFeature?.name"
      :logs="reviewLogs"
      @close="showReviewProcess = false"
    />

    <!-- 四栏布局 -->
    <div class="four-column-layout">
      <!-- 第一栏：功能列表 -->
      <div class="column feature-list-column">
        <FeatureListPanel
          :features="features"
          :selected-feature-id="selectedFeatureId"
          @feature-select="onFeatureSelect"
          @feature-add="onFeatureAdd"
          @feature-review="onFeatureReview"
          @feature-edit="onFeatureEdit"
          @feature-delete="onFeatureDelete"
        />
      </div>

      <!-- 第二栏：目录结构树 -->
      <div class="column directory-tree-column">
        <DirectoryTreePanel
          :task-id="fileId"
          :selected-feature="selectedFeature"
          :highlighted-files="highlightedFiles"
          @file-select="onFileSelect"
        />
      </div>

      <!-- 第三栏：代码展示 -->
      <div class="column code-view-column">
        <CodeViewPanel
          :file-id="fileId"
          :selected-file="selectedFile"
          :highlighted-lines="highlightedLines"
        />
      </div>

      <!-- 第四栏：问题单 -->
      <div class="column problem-list-column">
        <ProblemListPanel
          :selected-feature="selectedFeature"
          :problems="problems"
          :marked-set="markedSet"
          @problem-select="onProblemSelect"
          @toggle-mark="onToggleProblemMark"
          @export-marked="onExportMarked"
        />
      </div>
    </div>

    <!-- 添加/编辑功能对话框 -->
    <el-dialog
      v-model="showFeatureDialog"
      :title="editingFeature ? '编辑功能' : '添加功能'"
      width="600px"
    >
      <el-form :model="featureForm" label-width="100px">
        <el-form-item label="功能名称">
          <el-input v-model="featureForm.name" placeholder="如：用户登录" />
        </el-form-item>
        <el-form-item label="功能描述">
          <el-input
            v-model="featureForm.description"
            type="textarea"
            :rows="6"
            placeholder="详细描述该功能的实现要求和业务逻辑..."
          />
        </el-form-item>
        <el-form-item label="入口函数">
          <el-input v-model="featureForm.entryFunction" placeholder="main" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showFeatureDialog = false">取消</el-button>
        <el-button type="primary" @click="saveFeature">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { ArrowLeft, CircleCheck } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import axios from 'axios';
import FeatureListPanel from './components/FeatureListPanel.vue';
import DirectoryTreePanel from './components/DirectoryTreePanel.vue';
import CodeViewPanel from './components/CodeViewPanel.vue';
import ProblemListPanel from './components/ProblemListPanel.vue';
import ReviewProcessPanel from './components/ReviewProcessPanel.vue';
import { buildProblemKey } from '../shared/problemMarking';

// 数据状态
const fileId = ref('');  // 代码库文件ID
const features = ref([]);
const selectedFeatureId = ref(null);
const selectedFile = ref(null);
const highlightedFiles = ref([]);
const highlightedLines = ref([]);
const problems = ref([]);
const markedSet = ref(new Set());

// 路由
const route = useRoute();

// UI状态
const showFeatureDialog = ref(false);
const editingFeature = ref(null);
const showReviewProcess = ref(false);
const reviewingFeature = ref(null);
const reviewLogs = ref([]);

// 表单数据
const featureForm = ref({
  name: '',
  description: '',
  entryFunction: 'main'
});

// 计算属性
const selectedFeature = computed(() => {
  return features.value.find(f => f.id === selectedFeatureId.value);
});

// 初始化：从路由获取fileId
onMounted(() => {
  fileId.value = route.params.taskId;
  if (fileId.value) {
    loadFeatureList();
    loadMarkedState();
  }
});

async function loadFeatureList() {
  // 从localStorage加载功能列表
  try {
    const savedFeatures = localStorage.getItem(`features_${fileId.value}`);
    if (savedFeatures) {
      features.value = JSON.parse(savedFeatures);
      console.log('已加载功能列表:', features.value.length, '个功能');
    } else {
      features.value = [];
      console.log('无已保存的功能列表');
    }
  } catch (error) {
    console.error('加载功能列表失败:', error);
    features.value = [];
  }
}

function saveFeatureList() {
  // 保存功能列表到localStorage
  try {
    localStorage.setItem(`features_${fileId.value}`, JSON.stringify(features.value));
  } catch (error) {
    console.error('保存功能列表失败:', error);
  }
}

async function loadMarkedState() {
  if (!fileId.value) return;
  try {
    const response = await axios.get(`/api/codeReview/regressionTest/${fileId.value}/marked_problems`, {
      params: { analysis_type: 'feature' }
    });
    if (response.data.success) {
      const keys = response.data.data.map(item => item.problem_key);
      markedSet.value = new Set(keys);
    }
  } catch (error) {
    console.error('加载标记问题失败:', error);
  }
}

async function syncMarkedSet() {
  await loadMarkedState();
}

// 方法

function onFeatureSelect(feature) {
  selectedFeatureId.value = feature.id;
  
  // 高亮相关文件
  if (feature.related_files) {
    highlightedFiles.value = feature.related_files.map((file, index) => ({
      path: file,
      order: index + 1
    }));
  }
  
  // 加载问题
  loadProblems(feature.id);
}

function onFeatureAdd() {
  editingFeature.value = null;
  featureForm.value = {
    name: '',
    description: '',
    entryFunction: 'main'
  };
  showFeatureDialog.value = true;
}

function onFeatureEdit(feature) {
  editingFeature.value = feature;
  featureForm.value = {
    name: feature.name,
    description: feature.description,
    entryFunction: feature.entry_function || 'main'
  };
  showFeatureDialog.value = true;
}

function saveFeature() {
  if (!featureForm.value.name || !featureForm.value.description) {
    ElMessage.warning('请填写功能名称和描述');
    return;
  }
  
  if (editingFeature.value) {
    // 更新功能
    const index = features.value.findIndex(f => f.id === editingFeature.value.id);
    if (index !== -1) {
      features.value[index] = {
        ...features.value[index],
        ...featureForm.value
      };
    }
  } else {
    // 添加新功能
    features.value.push({
      id: Date.now(),
      ...featureForm.value,
      status: 'pending',
      related_files: [],
      related_functions: []
    });
  }
  
  // 保存到localStorage
  saveFeatureList();
  
  showFeatureDialog.value = false;
  ElMessage.success(editingFeature.value ? '功能更新成功' : '功能添加成功');
}

function onFeatureDelete(feature) {
  const index = features.value.findIndex(f => f.id === feature.id);
  if (index !== -1) {
    features.value.splice(index, 1);
    // 保存到localStorage
    saveFeatureList();
    ElMessage.success('功能删除成功');
  }
}

async function onFeatureReview(feature) {
  if (!fileId.value) {
    ElMessage.warning('请先上传代码库');
    return;
  }
  
  // 显示执行过程
  reviewingFeature.value = feature;
  showReviewProcess.value = true;
  reviewLogs.value = [];
  
  addLog('info', `🚀 开始审查功能: ${feature.name}`);
  addLog('info', `📝 功能描述: ${feature.description}`);
  addLog('info', `📂 代码库ID: ${fileId.value}`);
  
  try {
    // 调用后端API进行功能审查
    addLog('progress', '🔍 正在分析代码结构...');
    
    const response = await axios.post(`/api/codeReview/regressionTest/feature/start/${fileId.value}`, {
      feature_name: feature.name,
      feature_description: feature.description,
      entry_function: feature.entryFunction || 'main'
    });
    
    const taskId = response.data.task_id;
    addLog('success', `✅ 任务创建成功，任务ID: ${taskId}`);
    
    // 轮询检查任务进度
    pollReviewProgress(taskId, feature);
    
  } catch (error) {
    addLog('error', `❌ 审查失败: ${error.message}`);
    ElMessage.error('功能审查失败');
  }
}

function onFileSelect(file) {
  selectedFile.value = file;
}

function onProblemSelect(problem) {
  // 高亮问题相关的代码行
  if (problem.line) {
    highlightedLines.value = [problem.line];
  }
  
  // 如果问题有文件信息，切换到该文件
  if (problem.file_name) {
    selectedFile.value = {
      path: problem.file_name
    };
  }
}

async function loadProblems(featureId, retryCount = 0) {
  try {
    const { data } = await axios.get(`/api/codeReview/regressionTest/feature/problems/${featureId}`);
    problems.value = data.problems || [];
    syncMarkedSet();
  } catch (error) {
    console.error('加载问题失败:', error);
    
    // 如果是500错误且还有重试次数，延迟后重试
    if (error.response?.status === 500 && retryCount < 2) {
      console.log(`等待后重试 (${retryCount + 1}/2)...`);
      setTimeout(() => {
        loadProblems(featureId, retryCount + 1);
      }, 1000); // 延迟1秒后重试
    } else {
      problems.value = [];
    }
  }
}

async function updateMarkedState() {
  await loadMarkedState();
}

async function onToggleProblemMark({ problem, key }) {
  try {
    if (markedSet.value.has(key)) {
      // 取消标记
      await axios.delete(`/api/codeReview/regressionTest/${fileId.value}/marked_problems`, {
        data: {
          analysis_type: 'feature',
          problem_key: key
        }
      });
      markedSet.value.delete(key);
      ElMessage.success('已取消标记');
    } else {
      // 添加标记
      await axios.post(`/api/codeReview/regressionTest/${fileId.value}/marked_problems`, {
        analysis_type: 'feature',
        problem_key: key,
        problem_data: problem
      });
      markedSet.value.add(key);
      ElMessage.success('标记成功');
    }
    markedSet.value = new Set(markedSet.value);
  } catch (error) {
    console.error('标记操作失败:', error);
    ElMessage.error('标记操作失败: ' + (error.response?.data?.detail || error.message));
  }
}

async function onExportMarked() {
  if (markedSet.value.size === 0) {
    ElMessage.warning('请先标记至少一个问题');
    return;
  }
  
  try {
    // 从后端获取所有已标记的问题
    const markedResponse = await axios.get(`/api/codeReview/regressionTest/${fileId.value}/marked_problems`, {
      params: { analysis_type: 'feature' }
    });
    const problemsToExport = markedResponse.data.data.map(item => item.problem_data);
    
    const response = await axios.post(`/api/codeReview/regressionTest/export_marked_problems/${fileId.value}`, {
      analysis_type: 'feature',
      problems: problemsToExport
    }, {
      responseType: 'blob'
    });

    const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `feature_problems_${Date.now()}.xlsx`;
    link.click();
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error('导出标记问题失败:', error);
    ElMessage.error('导出失败');
  }
}

// 添加日志
function addLog(type, message) {
  reviewLogs.value.push({
    type, // 'info', 'progress', 'success', 'error', 'tool'
    message,
    timestamp: new Date().toLocaleTimeString()
  });
}

// 轮询审查进度
async function pollReviewProgress(taskId, feature) {
  const pollInterval = setInterval(async () => {
    try {
      const response = await axios.get(`/api/codeReview/regressionTest/feature/progress/${taskId}`);
      const { status, progress, current_step, logs } = response.data;
      
      // 更新日志
      if (logs && logs.length > 0) {
        logs.forEach(log => {
          addLog(log.type || 'info', log.message);
        });
      }
      
      // 根据状态更新进度
      if (status === 'completed') {
        clearInterval(pollInterval);
        addLog('success', '✅ 功能审查完成！');
        ElMessage.success('功能审查完成');
        
        // 更新功能状态
        const index = features.value.findIndex(f => f.id === feature.id);
        if (index !== -1) {
          features.value[index].status = 'completed';
          features.value[index].taskId = taskId;
          
          // 审查完成后，从后端获取真实的功能点数据（包括数据库ID）
          try {
            const { data: featuresData } = await axios.get(`/api/codeReview/regressionTest/feature/features/${taskId}`);
            if (featuresData.features && featuresData.features.length > 0) {
              // 更新feature的数据库ID
              const dbFeature = featuresData.features[0]; // 单个功能审查只有一个功能点
              features.value[index].id = dbFeature.id; // 使用数据库ID替换临时ID
              features.value[index].feature_name = dbFeature.feature_name;
              features.value[index].implementation_description = dbFeature.implementation_description;
              features.value[index].related_files = dbFeature.related_files ? JSON.parse(dbFeature.related_files) : [];
              features.value[index].related_functions = dbFeature.related_functions ? JSON.parse(dbFeature.related_functions) : [];
              console.log('功能点数据已更新，数据库ID:', dbFeature.id);
              
              // 用真实ID加载问题
              loadProblems(dbFeature.id);
            }
          } catch (err) {
            console.error('获取功能点数据失败:', err);
            // 如果获取失败，尝试使用临时ID
            loadProblems(feature.id);
          }
          
          // 保存到localStorage
          saveFeatureList();
        }
      } else if (status === 'failed') {
        clearInterval(pollInterval);
        addLog('error', `❌ 审查失败: ${response.data.error || '未知错误'}`);
        ElMessage.error('功能审查失败');
        
        // 更新功能状态为失败
        const index = features.value.findIndex(f => f.id === feature.id);
        if (index !== -1) {
          features.value[index].status = 'failed';
          // 保存到localStorage
          saveFeatureList();
        }
      } else {
        // 进行中
        if (current_step) {
          addLog('progress', `⏳ ${current_step} (${progress}%)`);
        }
      }
    } catch (error) {
      console.error('轮询进度失败:', error);
      clearInterval(pollInterval);
      addLog('error', `❌ 获取进度失败: ${error.message}`);
    }
  }, 2000); // 每2秒轮询一次
}
</script>

<style scoped>
.feature-review-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f7fa;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: white;
  border-bottom: 1px solid #e4e7ed;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.four-column-layout {
  display: grid;
  grid-template-columns: 300px 1fr 1fr 350px;
  gap: 1px;
  flex: 1;
  overflow: hidden;
  background: #e4e7ed;
}

.column {
  background: white;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 响应式布局 */
@media (max-width: 1600px) {
  .four-column-layout {
    grid-template-columns: 280px 1fr 1fr 320px;
  }
}

@media (max-width: 1400px) {
  .four-column-layout {
    grid-template-columns: 260px 1fr 1fr 300px;
  }
}
</style>

