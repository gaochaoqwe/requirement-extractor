<template>
  <div class="code-view-panel">
    <div class="panel-header">
      <h3>代码视图</h3>
      <div v-if="selectedFile" class="file-info">
        <el-tag type="info" size="small">{{ selectedFile.path }}</el-tag>
      </div>
    </div>

    <div class="panel-content">
      <div v-if="!selectedFile" class="empty-state">
        <el-empty description="请选择一个文件" />
      </div>

      <div v-else-if="loading" class="loading-state">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>加载中...</span>
      </div>

      <div v-else class="code-container">
        <pre class="code-content"><code v-for="(line, index) in codeLines" 
          :key="index" 
          :class="{ 'highlighted-line': isLineHighlighted(index + 1) }"
          class="code-line"
        ><span class="line-number">{{ index + 1 }}</span><span class="line-content">{{ line }}</span></code></pre>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue';
import { Loading } from '@element-plus/icons-vue';
import axios from 'axios';

const props = defineProps({
  fileId: {
    type: [Number, String],
    default: null
  },
  selectedFile: {
    type: Object,
    default: null
  },
  highlightedLines: {
    type: Array,
    default: () => []
  }
});

const fileContent = ref('');
const loading = ref(false);

// 计算属性：将文件内容分割为行
const codeLines = computed(() => {
  if (!fileContent.value) return [];
  return fileContent.value.split('\n');
});

// 监听选中文件变化
watch(() => props.selectedFile, (newFile) => {
  if (newFile) {
    loadFileContent(newFile);
  } else {
    fileContent.value = '';
  }
}, { immediate: true });

async function loadFileContent(file) {
  if (!props.fileId || !file.path) {
    console.warn('缺少 fileId 或 file.path');
    return;
  }
  
  loading.value = true;
  try {
    // 调用后端API获取文件内容
    const response = await axios.get(`/api/codeReview/feature/file/${props.fileId}/content`, {
      params: {
        file_path: file.path
      }
    });
    fileContent.value = response.data.content;
    
    console.log(`文件内容加载成功: ${file.path}`);
  } catch (error) {
    console.error('加载文件内容失败:', error);
    fileContent.value = `// 加载文件失败: ${error.message}`;
  } finally {
    loading.value = false;
  }
}

function isLineHighlighted(lineNumber) {
  return props.highlightedLines.includes(lineNumber);
}
</script>

<style scoped>
.code-view-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.panel-header {
  padding: 16px 20px;
  border-bottom: 2px solid #e8eaed;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(to bottom, #fafbfc, #ffffff);
}

.panel-header h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
  display: flex;
  align-items: center;
}

.panel-header h3::before {
  content: '📄';
  margin-right: 8px;
  font-size: 18px;
}

.file-info {
  flex: 1;
  margin-left: 16px;
  overflow: hidden;
}

.file-info .el-tag {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  background: #e0f2fe;
  color: #0369a1;
  border: 1px solid #bae6fd;
}

.panel-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.empty-state,
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #909399;
  flex: 1;
}

.loading-state .el-icon {
  font-size: 32px;
  margin-bottom: 12px;
  color: #409eff;
}

.code-container {
  flex: 1;
  overflow: auto;
  background: #1e1e1e;
}

.code-content {
  margin: 0;
  padding: 0;
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.8;
  color: #d4d4d4;
  background: #1e1e1e;
  border: none;
  counter-reset: line;
}

.code-line {
  display: block;
  white-space: pre;
  padding: 0;
  margin: 0;
  min-height: 1.8em;
  transition: background-color 0.15s ease;
}

.code-line:hover {
  background: rgba(255, 255, 255, 0.05);
}

.code-line.highlighted-line {
  background: rgba(255, 193, 7, 0.15);
  border-left: 3px solid #ffc107;
}

.code-line.highlighted-line .line-number {
  background: rgba(255, 193, 7, 0.2);
  color: #ffc107;
  font-weight: bold;
}

.line-number {
  display: inline-block;
  width: 60px;
  color: #858585;
  text-align: right;
  user-select: none;
  padding: 0 16px 0 12px;
  background: #252526;
  border-right: 1px solid #3e3e42;
  font-size: 13px;
}

.line-content {
  color: #d4d4d4;
  padding-left: 16px;
  word-wrap: break-word;
  white-space: pre-wrap;
}

/* 代码语法高亮基础样式 */
.code-content :deep(.keyword) {
  color: #569cd6;
  font-weight: 500;
}

.code-content :deep(.string) {
  color: #ce9178;
}

.code-content :deep(.comment) {
  color: #6a9955;
  font-style: italic;
}

.code-content :deep(.number) {
  color: #b5cea8;
}

.code-content :deep(.function) {
  color: #dcdcaa;
}

.code-content :deep(.type) {
  color: #4ec9b0;
}

/* 滚动条样式 */
.code-container::-webkit-scrollbar {
  width: 12px;
  height: 12px;
}

.code-container::-webkit-scrollbar-track {
  background: #2d2d30;
}

.code-container::-webkit-scrollbar-thumb {
  background: #424242;
  border-radius: 6px;
}

.code-container::-webkit-scrollbar-thumb:hover {
  background: #4e4e4e;
}

.code-container::-webkit-scrollbar-corner {
  background: #2d2d30;
}
</style>

