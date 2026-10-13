<template>
  <div class="issue-sidebar">
    <div class="sidebar-header">
      <h3>问题列表</h3>
      <div class="header-info">
        <el-tag v-if="selectedTask" type="primary" size="small">
          {{ selectedTask.task_name }}
        </el-tag>
        <el-tag type="danger" size="small">
          {{ filteredProblems.length }} 个问题
        </el-tag>
      </div>
    </div>
    
    <div class="sidebar-content">
      <!-- 文件选择信息 -->
      <div v-if="selectedOldFile || selectedNewFile" class="file-selection-info">
        <div class="section-title">
          <el-icon><Document /></el-icon>
          <span>选中文件</span>
        </div>
        <div class="selected-files">
          <div v-if="selectedOldFile" class="file-info old-file">
            <el-icon><Document /></el-icon>
            <span class="file-label">旧版本:</span>
            <span class="file-name">{{ getFileName(selectedOldFile.path) }}</span>
          </div>
          <div v-if="selectedNewFile" class="file-info new-file">
            <el-icon><Document /></el-icon>
            <span class="file-label">新版本:</span>
            <span class="file-name">{{ getFileName(selectedNewFile.path) }}</span>
          </div>
        </div>
      </div>

      <!-- 问题列表 -->
      <div v-if="filteredProblems.length > 0" class="problems-section">
        <div class="section-title">
          <el-icon><Warning /></el-icon>
          <span>发现的问题</span>
          <el-tag type="danger" size="small">{{ filteredProblems.length }} 个问题</el-tag>
        </div>
        
        <div class="problems-list">
          <div 
            v-for="(problem, index) in filteredProblems" 
            :key="index" 
            class="problem-block"
          >
            <div 
              class="problem-title"
              @click="toggleProblem(index)"
            >
              <div class="problem-title-left">
                <el-icon><Warning /></el-icon>
                <span>问题 {{ index + 1 }}</span>
                <el-tag 
                  v-if="problem.issue_level"
                  :type="getIssueLevelTagType(problem.issue_level)" 
                  size="small"
                  class="problem-level-tag"
                >
                  {{ problem.issue_level }}
                </el-tag>
              </div>
              <div class="problem-title-right">
                <el-button 
                  type="primary" 
                  size="small" 
                  text
                  @click.stop="highlightProblemInCode(problem, index)"
                  title="在代码中高亮显示此问题"
                >
                  <el-icon><Edit /></el-icon>
                  定位
                </el-button>
                <el-icon 
                  class="collapse-icon"
                  :class="{ 'collapsed': collapsedProblems.has(index) }"
                >
                  <ArrowDown />
                </el-icon>
              </div>
            </div>
            
            <el-collapse-transition>
              <div 
                v-show="!collapsedProblems.has(index)"
                class="problem-content"
              >
                <!-- 问题原因 -->
                <div v-if="problem.problem_reason" class="problem-field">
                  <div class="field-label">问题原因</div>
                  <div class="field-value">{{ problem.problem_reason }}</div>
                </div>
                
                <!-- 问题名称 -->
                <div v-if="problem.issue_name" class="problem-field">
                  <div class="field-label">问题名称</div>
                  <div class="field-value">{{ problem.issue_name }}</div>
                </div>
                
                <!-- 问题位置 -->
                <div v-if="problem.issue_location" class="problem-field">
                  <div class="field-label">问题位置</div>
                  <div class="field-value">{{ problem.issue_location }}</div>
                </div>
                
                <!-- 需求描述 -->
                <div v-if="problem.description_requirement" class="problem-field">
                  <div class="field-label">需求描述</div>
                  <div class="field-value">{{ problem.description_requirement }}</div>
                </div>
                
                <!-- 问题描述 -->
                <div v-if="problem.description_issue" class="problem-field">
                  <div class="field-label">问题描述</div>
                  <div class="field-value">{{ problem.description_issue }}</div>
                </div>
                
                <!-- 位置描述 -->
                <div v-if="problem.description_location" class="problem-field">
                  <div class="field-label">位置描述</div>
                  <div class="field-value">{{ problem.description_location }}</div>
                </div>
                
                <!-- 影响描述 -->
                <div v-if="problem.description_impact" class="problem-field">
                  <div class="field-label">影响描述</div>
                  <div class="field-value">{{ problem.description_impact }}</div>
                </div>
                
                <!-- 兼容旧格式 -->
                <div v-if="!problem.problem_reason && !problem.issue_name && (problem.description || problem.message)" class="problem-field">
                  <div class="field-label">问题描述</div>
                  <div class="field-value">{{ problem.description || problem.message || problem }}</div>
                </div>
                
                <!-- 行号信息 -->
                <div v-if="problem.line" class="problem-field">
                  <div class="field-label">行号</div>
                  <div class="field-value">第 {{ problem.line }} 行</div>
                </div>
                
                <!-- 文件信息 -->
                <div v-if="problem.file_name" class="problem-field">
                  <div class="field-label">文件</div>
                  <div class="field-value">{{ problem.file_name }}</div>
                </div>
                
                <!-- 函数信息 -->
                <div v-if="problem.function_name" class="problem-field">
                  <div class="field-label">函数</div>
                  <div class="field-value">{{ problem.function_name }}</div>
                </div>
                
                <!-- 问题类型 -->
                <div v-if="problem.type" class="problem-field">
                  <div class="field-label">问题类型</div>
                  <div class="field-value">
                    <el-tag type="danger" size="small">{{ problem.type }}</el-tag>
                  </div>
                </div>
              </div>
            </el-collapse-transition>
          </div>
        </div>
      </div>

      <!-- 无问题时的显示 -->
      <div v-else class="no-problems">
        <el-empty 
          :description="selectedTask ? '当前任务暂无问题' : '请选择任务查看问题'"
          :image-size="120"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Warning, Document, Edit, ArrowDown } from '@element-plus/icons-vue'
import { ElCollapseTransition } from 'element-plus'

// Props
const props = defineProps({
  selectedTask: {
    type: Object,
    default: null
  },
  filteredProblems: {
    type: Array,
    default: () => []
  },
  selectedOldFile: {
    type: Object,
    default: null
  },
  selectedNewFile: {
    type: Object,
    default: null
  }
})

// Emits
const emit = defineEmits(['highlight-problem'])

// 响应式数据
const collapsedProblems = ref(new Set())

// 方法
function getFileName(filePath) {
  if (!filePath) return ''
  const parts = filePath.split('/')
  return parts[parts.length - 1]
}

function getIssueLevelTagType(level) {
  switch (level) {
    case '重要问题': return 'danger'
    case '一般问题': return 'warning'
    case '建议改进': return 'info'
    default: return 'info'
  }
}

function toggleProblem(index) {
  if (collapsedProblems.value.has(index)) {
    collapsedProblems.value.delete(index)
  } else {
    collapsedProblems.value.add(index)
  }
}

function highlightProblemInCode(problem, problemIndex) {
  // 发送事件到父组件，传递问题信息用于在代码中高亮显示
  emit('highlight-problem', {
    problem,
    problemIndex,
    selectedTask: props.selectedTask
  })
}
</script>

<style scoped>
.issue-sidebar {
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  display: flex;
  flex-direction: column;
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #eee;
  background: rgba(255, 255, 255, 0.8);
  margin: 0;
  box-sizing: border-box;
}

.sidebar-header h3 {
  margin: 0 0 10px 0;
  color: #2c3e50;
  font-size: 18px;
  font-weight: 600;
}

.header-info {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  margin: 0;
  box-sizing: border-box;
}

.file-selection-info {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  padding: 15px;
  border-radius: 8px;
  border: 1px solid #e9ecef;
  margin-bottom: 20px;
}

.selected-files {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.8);
}

.old-file {
  border-left: 3px solid #909399;
}

.new-file {
  border-left: 3px solid #67c23a;
}

.file-label {
  font-size: 12px;
  color: #666;
  font-weight: 500;
  min-width: 60px;
}

.file-name {
  font-size: 13px;
  color: #2c3e50;
  font-weight: 400;
  word-break: break-all;
}

.problems-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.problems-section .section-title {
  color: #e74c3c;
  border-bottom: 2px solid #fecaca;
}

.problems-section .section-title .el-icon {
  color: #e74c3c;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 15px;
  color: #2c3e50;
  font-size: 16px;
  font-weight: 600;
  padding: 10px 0;
  border-bottom: 2px solid #eee;
}

.section-title .el-icon {
  color: #667eea;
}

.problems-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.problem-block {
  background: #fef2f2;
  padding: 12px;
  border-radius: 8px;
  border-left: 4px solid #e74c3c;
  margin-bottom: 8px;
}

.problem-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  color: #e74c3c;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  padding: 4px 0;
  border-radius: 4px;
  transition: background-color 0.2s ease;
}

.problem-title:hover {
  background-color: rgba(231, 76, 60, 0.1);
}

.problem-title-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.problem-title-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.problem-level-tag {
  margin-left: 10px;
}

.problem-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-left: 20px;
}

.problem-field {
  display: flex;
  flex-direction: column;
  padding: 4px 0;
  border-bottom: 1px dashed #eee;
  gap: 3px;
}

.problem-field:last-child {
  border-bottom: none;
}

.field-label {
  font-size: 12px;
  color: #888;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 2px;
}

.field-value {
  font-size: 13px;
  color: #333;
  font-weight: 400;
  line-height: 1.3;
  word-break: break-word;
  padding: 2px 0;
}

.collapse-icon {
  transition: transform 0.3s ease;
  cursor: pointer;
}

.collapse-icon.collapsed {
  transform: rotate(-90deg);
}

.no-problems {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
  color: #999;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .sidebar-header {
    padding: 15px;
  }
  
  .sidebar-content {
    padding: 15px;
  }
  
  .problem-title {
    font-size: 14px;
  }
  
  .field-value {
    font-size: 12px;
  }
}

@media (max-width: 768px) {
  .header-info {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .file-info {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .problem-title-left,
  .problem-title-right {
    gap: 4px;
  }
}
</style>
