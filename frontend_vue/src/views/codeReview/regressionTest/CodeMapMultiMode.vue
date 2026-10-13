<template>
  <div class="codemap-multimode">
    <!-- 主内容区域 -->
    <div class="main-content">
      <!-- 函数审查模式：显示函数模式和文件模式切换 -->
      <div v-if="analysisType === 'function'" class="function-analysis-mode">
        <!-- 模式切换按钮 -->
        <div class="mode-switcher">
          <div class="mode-tabs">
            <div 
              v-for="mode in functionModes" 
              :key="mode.key"
              class="mode-tab"
              :class="{ active: currentMode === mode.key }"
              @click="switchMode(mode.key)"
            >
              <i :class="mode.icon"></i>
              <span>{{ mode.label }}</span>
            </div>
          </div>
        </div>
        
        <!-- 函数模式内容 -->
        <div v-if="currentMode === 'function' && FunctionCodeMapFullscreen" class="mode-content">
          <component 
            :is="FunctionCodeMapFullscreen"
            :task-id="taskId"
          />
        </div>
        
        <!-- 文件模式内容 -->
        <div v-if="currentMode === 'file' && FileCodeMapFullscreen" class="mode-content">
          <component 
            :is="FileCodeMapFullscreen"
            :task-id="taskId"
          />
        </div>
      </div>
      
      <!-- 链路审查模式：只显示链路视图，无切换按钮 -->
      <div v-else-if="analysisType === 'chain'" class="chain-analysis-mode">
        <component 
          :is="ChainCodeMapFullscreen"
          :task-id="taskId"
        />
      </div>
      
      <!-- 功能审查模式：独立页面（未来扩展） -->
      <div v-else-if="analysisType === 'feature'" class="feature-analysis-mode">
        <div class="placeholder">功能审查模式（开发中）</div>
      </div>
      
      <!-- 加载中 -->
      <div v-else class="loading-analysis-type">
        <i class="el-icon-loading"></i>
        <p>正在加载审查结果...</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import FunctionCodeMapFullscreen from './functionCodemap/CodeMapFullscreen.vue'
import FileCodeMapFullscreen from './fileCodemap/CodeMapFullscreen.vue'
import ChainCodeMapFullscreen from './chainCodemap/CodeMapFullscreen.vue'

const route = useRoute()

// 从路由参数获取任务ID（转为数字，后端接口要求 int）
const taskId = ref(Number(route.params.taskId))

// 审查类型：function（函数审查）、chain（链路审查）、feature（功能审查）
const analysisType = ref(null)

// 当前模式（仅用于函数审查）
const currentMode = ref('function')

// 函数审查的模式配置
const functionModes = [
  {
    key: 'function',
    label: '函数模式',
    icon: 'el-icon-cpu'
  },
  {
    key: 'file',
    label: '文件模式',
    icon: 'el-icon-document'
  }
]

// 切换模式（仅用于函数审查）
function switchMode(mode) {
  currentMode.value = mode
  console.log(`切换到${mode}模式`)
}

// 加载任务信息，获取审查类型
async function loadTaskInfo() {
  try {
    const response = await axios.get(`/api/codeReview/regressionTest/tasks/${taskId.value}`)
    
    if (response.data && response.data.task) {
      const task = response.data.task
      
      // 根据任务名称或analysis_type判断审查类型
      if (task.task_name && task.task_name.includes('链路审查')) {
        analysisType.value = 'chain'
      } else if (task.task_name && task.task_name.includes('功能审查')) {
        analysisType.value = 'feature'
      } else if (task.analysis_type === 'chain') {
        analysisType.value = 'chain'
      } else if (task.analysis_type === 'feature') {
        analysisType.value = 'feature'
      } else {
        analysisType.value = 'function'
      }
      
      console.log('任务类型:', analysisType.value)
    }
  } catch (error) {
    console.error('加载任务信息失败:', error)
    ElMessage.error('加载任务信息失败')
    // 默认为函数审查
    analysisType.value = 'function'
  }
}

onMounted(async () => {
  console.log(`多模式代码地图已加载，任务ID: ${taskId.value}`)
  await loadTaskInfo()
})
</script>

<style scoped>
.codemap-multimode {
  height: 100vh;
  width: 100%;
  background-color: #f5f7fa;
  overflow: hidden;
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.main-content {
  height: 100%;
  width: 100%;
}

/* 函数审查模式 */
.function-analysis-mode {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.mode-switcher {
  background: #ffffff;
  border-bottom: 1px solid #e1e8ed;
  padding: 12px 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  z-index: 100;
}

.mode-tabs {
  display: flex;
  gap: 8px;
}

.mode-tab {
  padding: 10px 20px;
  border: 1px solid #d1d9e0;
  background: #ffffff;
  color: #606266;
  cursor: pointer;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
  min-width: 120px;
  justify-content: center;
}

.mode-tab:hover {
  background: #f5f7fa;
  border-color: #c0c4cc;
  color: #409eff;
  transform: translateY(-2px);
}

.mode-tab.active {
  background: #409eff;
  border-color: #409eff;
  color: #ffffff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.mode-tab i {
  font-size: 18px;
}

.mode-content {
  flex: 1;
  overflow: hidden;
}

/* 链路审查模式 */
.chain-analysis-mode {
  height: 100%;
  width: 100%;
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  overflow: hidden;
}

/* 功能审查模式 */
.feature-analysis-mode {
  height: 100%;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder {
  font-size: 24px;
  color: #909399;
  font-weight: 500;
}

/* 加载中 */
.loading-analysis-type {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #909399;
}

.loading-analysis-type i {
  font-size: 48px;
  margin-bottom: 16px;
}

.loading-analysis-type p {
  font-size: 16px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .mode-tabs {
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .mode-tab {
    min-width: 100px;
    padding: 8px 16px;
    font-size: 13px;
  }
}
</style> 