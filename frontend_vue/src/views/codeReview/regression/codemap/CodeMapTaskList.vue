<template>
  <div class="task-list">
    <div v-if="!taskData || taskData.length === 0" class="empty-state">
      <el-empty description="暂无任务数据" />
    </div>
    
    <div v-else class="task-items">
      <div
        v-for="task in taskData"
        :key="task.id"
        class="task-item"
        :class="{ 'active': selectedTask && selectedTask.id === task.id }"
        @click="handleTaskClick(task)"
      >
        <div class="task-header">
          <div class="task-id">{{ task.task_id }}</div>
          <div class="task-name">{{ task.task_name }}</div>
        </div>
        
        <div class="task-description">
          {{ task.task_description || '无描述信息' }}
        </div>
        
        <div class="task-meta">
          <div class="change-type">
            <el-tag 
              :type="getChangeTypeColor(task.change_type)" 
              size="small"
            >
              {{ getChangeTypeText(task.change_type) }}
            </el-tag>
          </div>
          
          <div class="problem-count" v-if="task.problem_count">
            <el-badge :value="task.problem_count" class="problem-badge">
              <span class="problem-text">问题</span>
            </el-badge>
          </div>
        </div>
        
        <div class="task-status">
          <el-tag 
            :type="getStatusColor(task.status)"
            size="small"
          >
            {{ getStatusText(task.status) }}
          </el-tag>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'

const props = defineProps({
  taskData: {
    type: Array,
    default: () => []
  },
  selectedTask: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['task-click'])

function handleTaskClick(task) {
  emit('task-click', task)
}

function getChangeTypeColor(changeType) {
  const colorMap = {
    'requirement': 'primary',
    'design': 'success', 
    'code': 'warning',
    'combined': 'danger',
    'unknown': 'info'
  }
  return colorMap[changeType] || 'info'
}

function getChangeTypeText(changeType) {
  const textMap = {
    'requirement': '需求变更',
    'design': '设计变更',
    'code': '代码变更', 
    'combined': '综合变更',
    'unknown': '未知类型'
  }
  return textMap[changeType] || '未知类型'
}

function getStatusColor(status) {
  const colorMap = {
    'pending': 'info',
    'running': 'warning',
    'completed': 'success',
    'failed': 'danger'
  }
  return colorMap[status] || 'info'
}

function getStatusText(status) {
  const textMap = {
    'pending': '待处理',
    'running': '处理中',
    'completed': '已完成',
    'failed': '失败'
  }
  return textMap[status] || '未知状态'
}
</script>

<style scoped>
.task-list {
  height: 100%;
  overflow-y: auto;
}

.empty-state {
  padding: 40px 20px;
  text-align: center;
}

.task-items {
  padding: 10px;
}

.task-item {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  margin-bottom: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.task-item:hover {
  border-color: #409eff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
  transform: translateY(-2px);
}

.task-item.active {
  border-color: #409eff;
  background: #ecf5ff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.25);
}

.task-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.task-id {
  background: #f0f9ff;
  color: #1e40af;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  margin-right: 8px;
  min-width: 60px;
  text-align: center;
}

.task-name {
  font-weight: 600;
  color: #2c3e50;
  font-size: 14px;
  flex: 1;
}

.task-description {
  color: #606266;
  font-size: 12px;
  line-height: 1.4;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.task-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.problem-badge .problem-text {
  font-size: 12px;
  color: #909399;
}

.task-status {
  text-align: right;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .task-item {
    padding: 12px;
    margin-bottom: 8px;
  }
  
  .task-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .task-id {
    margin-bottom: 4px;
    margin-right: 0;
  }
}
</style> 