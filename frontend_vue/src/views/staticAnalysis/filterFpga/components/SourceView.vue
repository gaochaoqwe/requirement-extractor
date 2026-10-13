<template>
  <div class="source-view">
    <div v-if="!selectedNode" class="empty-state">
      <div class="empty-icon">
        <el-icon size="48"><Document /></el-icon>
      </div>
      <div class="empty-text">
        <h3>请选择一个文件</h3>
        <p>从左侧代码列表中选择要查看的文件</p>
      </div>
    </div>
    
    <div v-else class="source-container">
      <!-- 源码头部 -->
      <div class="source-header">
        <div class="file-info">
          <el-icon><Document /></el-icon>
          <span class="file-name">{{ selectedNode.name }}</span>
          <el-tag type="primary" size="small">文件</el-tag>
        </div>
      </div>
      
      <!-- 源码内容 -->
      <div class="source-content">
        <div class="line-numbers" ref="lineNumbersContainer">
          <div 
            v-for="(line, index) in codeLines" 
            :key="index"
            class="line-number"
            :class="{ 'problem-highlighted': highlightedLines.has(index + 1) }"
            @click="scrollToLine(index + 1)"
          >
            {{ index + 1 }}
          </div>
        </div>
        <div class="code-content" ref="codeContainer" @scroll="handleScroll">
          <pre 
            ref="codeElement"
            class="code-block"
          ><div 
            v-for="(line, index) in codeLines" 
            :key="index"
            :class="{ 'problem-highlighted-line': highlightedLines.has(index + 1) }"
            class="code-line"
            v-html="highlightSyntax(line)"
          ></div></pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { Document } from '@element-plus/icons-vue'

// Props
const props = defineProps({
  selectedNode: {
    type: Object,
    default: null
  },
  highlightedProblem: {
    type: Object,
    default: null
  }
})

// 响应式数据
const codeElement = ref(null)
const codeContainer = ref(null)
const lineNumbersContainer = ref(null)
const highlightedLines = ref(new Set())

// 计算属性
const codeLines = computed(() => {
  if (!props.selectedNode || !props.selectedNode.source_code) {
    return []
  }
  
  return props.selectedNode.source_code.split('\n').map(line => line.replace(/\r/g, ''))
})

// 监听高亮问题变化
watch(() => props.highlightedProblem, async (newProblem) => {
  if (newProblem) {
    await nextTick()
    highlightProblemLines(newProblem)
  }
}, { immediate: true })

// 方法
function highlightSyntax(line) {
  if (!line) return ''
  
  // 转义HTML字符
  let highlightedLine = line
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
  
  // 简单的C/C++语法高亮
  const keywords = [
    'auto', 'break', 'case', 'char', 'const', 'continue', 'default', 'do',
    'double', 'else', 'enum', 'extern', 'float', 'for', 'goto', 'if',
    'inline', 'int', 'long', 'register', 'return', 'short', 'signed',
    'sizeof', 'static', 'struct', 'switch', 'typedef', 'union',
    'unsigned', 'void', 'volatile', 'while'
  ]
  
  // 预处理指令
  highlightedLine = highlightedLine.replace(/^(\s*#\s*\w+.*$)/gm, '<span class="preprocessor">$1</span>')
  
  // 注释
  highlightedLine = highlightedLine.replace(/(\/\/.*$)/gm, '<span class="comment">$1</span>')
  highlightedLine = highlightedLine.replace(/(\/\*.*?\*\/)/g, '<span class="comment">$1</span>')
  
  // 字符串
  highlightedLine = highlightedLine.replace(/(&quot;(?:[^&]|&[^q]|&q[^u]|&qu[^o]|&quo[^t])*?&quot;)(?![^<]*<\/span>)/g, '<span class="string">$1</span>')
  
  // 数字
  highlightedLine = highlightedLine.replace(/\b(\d+\.?\d*[fFlL]?)(?![^<]*<\/span>)\b/g, '<span class="number">$1</span>')
  
  // 关键字
  keywords.forEach(keyword => {
    const regex = new RegExp(`\\b(${keyword})\\b(?![^<]*<\/span>)`, 'g')
    highlightedLine = highlightedLine.replace(regex, '<span class="keyword">$1</span>')
  })
  
  return highlightedLine
}

function scrollToLine(lineNumber) {
  if (!codeContainer.value) return
  
  const lineHeight = 24
  const scrollTop = (lineNumber - 1) * lineHeight - 100
  
  codeContainer.value.scrollTop = Math.max(0, scrollTop)
}

function handleScroll(event) {
  // 同步行号区域的滚动
  if (lineNumbersContainer.value && codeContainer.value) {
    lineNumbersContainer.value.scrollTop = codeContainer.value.scrollTop
  }
}

function highlightProblemLines(problemInfo) {
  if (!problemInfo || !problemInfo.problem) {
    return
  }
  
  const problem = problemInfo.problem
  highlightedLines.value.clear()
  
  console.log('[源码视图] 高亮问题:', problem)
  
  // 尝试从issue_line字段提取行号
  if (problem.issue_line) {
    const lineStr = String(problem.issue_line).trim()
    const lineNum = parseInt(lineStr, 10)
    
    if (!isNaN(lineNum) && lineNum > 0 && lineNum <= codeLines.value.length) {
      highlightedLines.value.add(lineNum)
      scrollToLine(lineNum)
      console.log('[源码视图] 高亮行号:', lineNum)
      return
    }
  }
  
  // 如果没有行号信息，尝试从描述中提取
  if (problem.issue_description) {
    const desc = problem.issue_description
    const lineMatch = desc.match(/第?\s*(\d+)\s*行/) || desc.match(/line\s+(\d+)/i)
    
    if (lineMatch) {
      const lineNum = parseInt(lineMatch[1], 10)
      if (!isNaN(lineNum) && lineNum > 0 && lineNum <= codeLines.value.length) {
        highlightedLines.value.add(lineNum)
        scrollToLine(lineNum)
        console.log('[源码视图] 从描述提取行号:', lineNum)
        return
      }
    }
  }
  
  console.log('[源码视图] 无法确定行号')
}
</script>

<style scoped>
.source-view {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #1a1a1a;
  color: #e0e0e0;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #666;
}

.empty-icon {
  margin-bottom: 20px;
  opacity: 0.5;
}

.empty-text h3 {
  margin: 0 0 10px 0;
  font-size: 18px;
  color: #999;
}

.empty-text p {
  margin: 0;
  font-size: 14px;
  color: #666;
}

.source-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.source-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background: #2d2d2d;
  border-bottom: 1px solid #404040;
  flex-shrink: 0;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.file-name {
  font-size: 16px;
  font-weight: 600;
  color: #61dafb;
}

.source-content {
  flex: 1;
  display: flex;
  overflow: auto;
  background: #1a1a1a;
}

.line-numbers {
  background: #2d2d2d;
  color: #666;
  padding: 20px 10px;
  text-align: right;
  font-size: 14px;
  line-height: 24px;
  border-right: 1px solid #404040;
  user-select: none;
  flex-shrink: 0;
  min-width: 60px;
  overflow: hidden;
}

.line-number {
  height: 24px;
  padding-right: 10px;
  transition: all 0.2s ease;
}

.line-number.problem-highlighted {
  background: #e74c3c;
  color: #fff;
  font-weight: bold;
  animation: problemPulse 2s ease-in-out;
}

.line-number:hover {
  background: #404040;
  cursor: pointer;
}

.code-content {
  flex: 1;
  overflow: auto;
}

.code-block {
  margin: 0;
  padding: 20px;
  background: transparent;
  color: #e0e0e0;
  font-size: 14px;
  line-height: 24px;
  white-space: pre;
  overflow-x: auto;
}

/* 自定义滚动条样式 - 更美观 */
.code-block::-webkit-scrollbar {
  height: 8px;
}

.code-block::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
}

.code-block::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
}

.code-block::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}

.code-line {
  display: block;
  min-height: 24px;
  padding: 0 10px;
  margin: 0;
  transition: background-color 0.2s ease;
  white-space: pre;
  /* 移除单行滚动条，由父容器统一处理 */
  overflow-x: visible;
}

/* 防止进度条样式污染FPGA代码视图 */
.source-view :deep(.el-progress),
.source-view :deep(.el-progress-bar),
.source-view :deep(.el-progress-bar__outer),
.source-view :deep(.el-progress-bar__inner) {
  display: none !important;
}

.code-line.problem-highlighted-line {
  background: rgba(231, 76, 60, 0.15);
  border-left: 4px solid #e74c3c;
  padding-left: 6px;
  animation: problemPulse 2s ease-in-out;
}

@keyframes problemPulse {
  0% {
    background: rgba(231, 76, 60, 0.3);
  }
  50% {
    background: rgba(231, 76, 60, 0.15);
  }
  100% {
    background: rgba(231, 76, 60, 0.15);
  }
}

/* 滚动条样式 */
.code-content::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.code-content::-webkit-scrollbar-track {
  background: #2d2d2d;
}

.code-content::-webkit-scrollbar-thumb {
  background: #555;
  border-radius: 4px;
}

.code-content::-webkit-scrollbar-thumb:hover {
  background: #777;
}

/* 代码高亮样式 */
.code-block :deep(.keyword) {
  color: #c586c0;
  font-weight: bold;
}

.code-block :deep(.string) {
  color: #ce9178;
}

.code-block :deep(.comment) {
  color: #6a9955;
}

.code-block :deep(.number) {
  color: #b5cea8;
}

.code-block :deep(.preprocessor) {
  color: #9cdcfe;
  font-weight: 500;
}
</style>

