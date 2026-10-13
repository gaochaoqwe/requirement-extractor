<template>
  <div v-if="visible" class="review-process-panel">
    <div class="process-header">
      <div class="header-left">
        <el-icon class="process-icon"><Loading /></el-icon>
        <span class="process-title">执行过程</span>
        <el-tag v-if="featureName" size="small" type="info">{{ featureName }}</el-tag>
      </div>
      <div class="header-right">
        <el-button
          :icon="isCollapsed ? ArrowDown : ArrowUp"
          circle
          size="small"
          @click="toggleCollapse"
        />
        <el-button
          :icon="Close"
          circle
          size="small"
          @click="$emit('close')"
        />
      </div>
    </div>

    <el-collapse-transition>
      <div v-show="!isCollapsed" class="process-content">
        <div ref="logsContainer" class="logs-container">
          <div
            v-for="(log, index) in logs"
            :key="index"
            class="log-item"
            :class="`log-${log.type}`"
          >
            <span class="log-timestamp">{{ log.timestamp }}</span>
            <span class="log-message">{{ log.message }}</span>
          </div>
          
          <div v-if="logs.length === 0" class="empty-logs">
            <el-empty description="暂无执行日志" :image-size="60" />
          </div>
        </div>
      </div>
    </el-collapse-transition>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue';
import { Loading, Close, ArrowUp, ArrowDown } from '@element-plus/icons-vue';

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  featureName: {
    type: String,
    default: ''
  },
  logs: {
    type: Array,
    default: () => []
  }
});

defineEmits(['close']);

const isCollapsed = ref(false);
const logsContainer = ref(null);

function toggleCollapse() {
  isCollapsed.value = !isCollapsed.value;
}

// 自动滚动到最新日志
watch(() => props.logs.length, async () => {
  if (!isCollapsed.value && logsContainer.value) {
    await nextTick();
    logsContainer.value.scrollTop = logsContainer.value.scrollHeight;
  }
});
</script>

<style scoped>
.review-process-panel {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 600px;
  max-height: 500px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12), 0 0 0 1px rgba(0, 0, 0, 0.05);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    transform: translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.process-header {
  padding: 16px 20px;
  border-bottom: 2px solid #e8eaed;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px 12px 0 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.process-icon {
  font-size: 20px;
  color: #ffffff;
  animation: rotate 1.5s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.process-title {
  font-size: 16px;
  font-weight: 600;
  color: #ffffff;
}

.header-left .el-tag {
  background: rgba(255, 255, 255, 0.2);
  color: #ffffff;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.header-right {
  display: flex;
  gap: 8px;
}

.header-right :deep(.el-button) {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.3);
  color: #ffffff;
}

.header-right :deep(.el-button:hover) {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.4);
}

.process-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.logs-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #fafbfc;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  max-height: 400px;
}

.log-item {
  display: flex;
  align-items: flex-start;
  padding: 8px 12px;
  margin-bottom: 4px;
  border-radius: 6px;
  transition: background-color 0.2s;
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.log-item:hover {
  background: rgba(0, 0, 0, 0.02);
}

.log-timestamp {
  flex-shrink: 0;
  width: 80px;
  color: #8590a6;
  font-size: 12px;
  margin-right: 12px;
}

.log-message {
  flex: 1;
  color: #1f2937;
  word-break: break-word;
}

/* 不同类型日志的样式 */
.log-info {
  background: #f0f9ff;
  border-left: 3px solid #0ea5e9;
}

.log-info .log-message {
  color: #0369a1;
}

.log-progress {
  background: #fef3c7;
  border-left: 3px solid #f59e0b;
}

.log-progress .log-message {
  color: #92400e;
}

.log-success {
  background: #dcfce7;
  border-left: 3px solid #22c55e;
}

.log-success .log-message {
  color: #15803d;
  font-weight: 500;
}

.log-error {
  background: #fee2e2;
  border-left: 3px solid #ef4444;
}

.log-error .log-message {
  color: #991b1b;
  font-weight: 500;
}

.log-tool {
  background: #f3e8ff;
  border-left: 3px solid #a855f7;
}

.log-tool .log-message {
  color: #6b21a8;
  font-family: 'Consolas', 'Monaco', monospace;
}

.empty-logs {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
  color: #9ca3af;
}

/* 滚动条样式 */
.logs-container::-webkit-scrollbar {
  width: 8px;
}

.logs-container::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 4px;
}

.logs-container::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.logs-container::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>

