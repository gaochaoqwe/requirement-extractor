<template>
  <div class="source-view">
    <div v-if="!selectedNode" class="empty-state">
      <div class="empty-icon">
        <el-icon size="48"><Document /></el-icon>
      </div>
      <div class="empty-text">
        <h3>请选择一个文件或函数</h3>
        <p>从左侧代码结构中选择要查看的文件或函数</p>
      </div>
    </div>
    
    <div v-else class="source-container">
      <!-- 源码头部 -->
      <div class="source-header">
        <div class="file-info">
          <el-icon><Document /></el-icon>
          <span class="file-name">{{ getDisplayName(selectedNode) }}</span>
          <el-tag v-if="selectedNode.type === 'function'" type="success" size="small">
            函数: {{ selectedNode.name }}
          </el-tag>
          <el-tag v-else-if="selectedNode.type === 'fpga_module'" type="danger" size="small">
            FPGA模块: {{ selectedNode.name }}
          </el-tag>
          <el-tag v-else-if="selectedNode.type === 'chain'" type="primary" size="small">
            链路: {{ selectedNode.name }}
          </el-tag>
        </div>
        <div class="source-actions">
          <!-- 源码/注释切换按钮 -->
          <el-radio-group v-model="codeViewMode" size="small" @change="handleCodeViewModeChange">
            <el-radio-button label="original">源代码</el-radio-button>
            <el-radio-button label="commented">注释后代码</el-radio-button>
          </el-radio-group>
        </div>
      </div>
      
      <!-- 源码内容 -->
      <div class="source-content">
        <div class="line-numbers">
          <div 
            v-for="(line, index) in codeLines" 
            :key="index"
            class="line-number"
            :class="{ 
              'highlighted': (isLineHighlighted(index + 1) && !highlightedLines.has(index + 1)),
              'problem-highlighted': highlightedLines.has(index + 1)
            }"
            @click="scrollToLine(index + 1)"
          >
            {{ index + 1 }}
          </div>
        </div>
        <div class="code-content" @scroll="handleScroll">
          <pre 
            ref="codeElement"
            class="code-block"
          ><div 
            v-for="(line, index) in codeLines" 
            :key="index"
            :class="{ 
              'highlighted-line': isLineHighlighted(index + 1) && !highlightedLines.has(index + 1),
              'problem-highlighted-line': highlightedLines.has(index + 1)
            }"
            class="code-line"
            v-html="highlightSyntax(line, getFileLanguage())"
          ></div></pre>
        </div>
        
        <!-- 小地图导航 -->
        <div v-if="codeLines.length > 50" class="minimap">
          <div class="minimap-content">
            <div 
              v-for="(line, index) in codeLines" 
              :key="index"
              class="minimap-line"
              :class="{ 
                'minimap-highlighted': isLineHighlighted(index + 1),
                'minimap-visible': isLineVisible(index + 1)
              }"
              @click="scrollToLine(index + 1)"
            ></div>
          </div>
          <div class="minimap-viewport" :style="minimapViewportStyle"></div>
        </div>
      </div>
      

    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Document } from '@element-plus/icons-vue'

// Props
const props = defineProps({
  selectedNode: {
    type: Object,
    default: null
  },
  codeMapData: {
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
const codeViewMode = ref('original') // 'original' | 'commented'
const scrollInfo = ref({
  scrollTop: 0,
  scrollHeight: 0,
  clientHeight: 0
})
const highlightedLines = ref(new Set())

// 计算属性
const codeLines = computed(() => {
  if (!props.selectedNode) {
    return []
  }
  
  // 根据当前视图模式选择显示的代码
  let codeToShow = ''
  if (codeViewMode.value === 'commented') {
    // 查找注释后的代码
    if (props.selectedNode.commented_code) {
      codeToShow = props.selectedNode.commented_code
    } else if (props.selectedNode.function_description) {
      // 如果有函数描述，显示原代码+函数描述
      codeToShow = props.selectedNode.source_code + '\n\n/* AI 生成的函数描述:\n' + props.selectedNode.function_description + '\n*/'
    } else {
      // 如果没有注释后的代码，显示原代码
      codeToShow = props.selectedNode.source_code || ''
      ElMessage.warning('该文件/函数暂无AI注释后的代码')
    }
  } else {
    // 显示原代码
    codeToShow = props.selectedNode.source_code || ''
  }
  
  // 直接分割代码行，不处理转义字符
  // 源代码应该原样显示，包括 \n, \t 等转义字符
  if (!codeToShow) {
    return []
  }
  
  // 分割代码行并清理每行的回车符
  return codeToShow.split('\n').map(line => line.replace(/\r/g, ''))
})

// 小地图视口样式
const minimapViewportStyle = computed(() => {
  if (!scrollInfo.value.scrollHeight || !scrollInfo.value.clientHeight) {
    return {}
  }
  
  const viewportHeight = (scrollInfo.value.clientHeight / scrollInfo.value.scrollHeight) * 100
  const viewportTop = (scrollInfo.value.scrollTop / scrollInfo.value.scrollHeight) * 100
  
  return {
    height: `${viewportHeight}%`,
    top: `${viewportTop}%`
  }
})

// 监听选中节点变化，自动滚动到函数位置
watch(() => props.selectedNode, async (newNode) => {
  if (newNode && (newNode.type === 'function' || newNode.type === 'fpga_module')) {
    await nextTick()
    scrollToFunction(newNode)
  }
}, { immediate: true })

// 监听高亮问题变化
watch(() => props.highlightedProblem, async (newProblem) => {
  if (newProblem) {
    await nextTick()
    highlightProblemLines(newProblem)
  }
}, { immediate: true })

// 方法
function getFileName(filePath) {
  if (!filePath) return ''
  return filePath.split('/').pop() || filePath.split('\\').pop() || filePath
}

function getDisplayName(node) {
  if (!node) return ''
  if (node.type === 'chain') {
    return node.name || '未知链路'
  }
  return getFileName(node.file_path)
}

function getFileLanguage() {
  if (!props.selectedNode || !props.selectedNode.file_path) {
    return 'text'
  }
  
  const fileName = props.selectedNode.file_path.toLowerCase()
  
  // C/C++
  if (fileName.endsWith('.c') || fileName.endsWith('.h')) {
    return 'c'
  }
  if (fileName.endsWith('.cpp') || fileName.endsWith('.cc') || fileName.endsWith('.cxx') || 
      fileName.endsWith('.hpp') || fileName.endsWith('.hxx') || fileName.endsWith('.h++')) {
    return 'cpp'
  }
  
  // FPGA
  if (fileName.endsWith('.v') || fileName.endsWith('.vh')) {
    return 'verilog'
  }
  if (fileName.endsWith('.vhd') || fileName.endsWith('.vhdl')) {
    return 'vhdl'
  }
  
  return 'text'
}

function highlightSyntax(line, language) {
  if (!line) return ''
  
  // 清理行内的换行符和回车符
  let cleanedLine = line.replace(/[\r\n]/g, '')
  
  // 转义HTML字符
  let highlightedLine = cleanedLine
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
  
  // 根据语言类型进行语法高亮
  switch (language) {
    case 'c':
    case 'cpp':
      highlightedLine = highlightCppSyntax(highlightedLine)
      break
    case 'verilog':
      highlightedLine = highlightVerilogSyntax(highlightedLine)
      break
    case 'vhdl':
      highlightedLine = highlightVhdlSyntax(highlightedLine)
      break
    default:
      highlightedLine = highlightGenericSyntax(highlightedLine)
  }
  
  return highlightedLine
}

function highlightCppSyntax(line) {
  // C/C++ 关键字
  const keywords = [
    'auto', 'break', 'case', 'char', 'const', 'continue', 'default', 'do',
    'double', 'else', 'enum', 'extern', 'float', 'for', 'goto', 'if',
    'inline', 'int', 'long', 'register', 'restrict', 'return', 'short',
    'signed', 'sizeof', 'static', 'struct', 'switch', 'typedef', 'union',
    'unsigned', 'void', 'volatile', 'while', '_Bool', '_Complex', '_Imaginary',
    // C++ 关键字
    'class', 'namespace', 'template', 'typename', 'public', 'private', 'protected',
    'virtual', 'override', 'final', 'explicit', 'operator', 'friend', 'using',
    'try', 'catch', 'throw', 'new', 'delete', 'this', 'nullptr', 'true', 'false',
    'bool', 'string', 'vector', 'map', 'set', 'list', 'queue', 'stack'
  ]
  
  // 预处理指令
  line = line.replace(/^(\s*#\s*\w+.*$)/gm, '<span class="preprocessor">$1</span>')
  
  // 先处理注释，避免注释内容被其他规则影响
  // 单行注释 //
  line = line.replace(/(\/\/.*$)/gm, '<span class="comment">$1</span>')
  
  // 多行注释 /* */（在单行中的部分）
  line = line.replace(/(\/\*.*?\*\/)/g, '<span class="comment">$1</span>')
  
  // 字符串字面量（避免在注释中匹配）
  line = line.replace(/(&quot;(?:[^&]|&[^q]|&q[^u]|&qu[^o]|&quo[^t])*?&quot;)(?![^<]*<\/span>)/g, '<span class="string">$1</span>')
  line = line.replace(/(&#39;(?:[^&]|&[^#]|&#[^3]|&#3[^9])*?&#39;)(?![^<]*<\/span>)/g, '<span class="string">$1</span>')
  
  // 数字（避免在注释和字符串中匹配）
  line = line.replace(/\b(\d+\.?\d*[fFlL]?)(?![^<]*<\/span>)\b/g, '<span class="number">$1</span>')
  line = line.replace(/\b(0[xX][0-9a-fA-F]+[uUlL]*)(?![^<]*<\/span>)\b/g, '<span class="number">$1</span>')
  
  // 关键字高亮（避免在注释和字符串中高亮）
  keywords.forEach(keyword => {
    const regex = new RegExp(`\\b(${keyword})\\b(?![^<]*<\/span>)`, 'g')
    line = line.replace(regex, '<span class="keyword">$1</span>')
  })
  
  // 函数调用（避免在注释和字符串中匹配）
  line = line.replace(/\b([a-zA-Z_]\w*)\s*(?=\()(?![^<]*<\/span>)/g, '<span class="function">$1</span>')
  
  return line
}

function highlightVerilogSyntax(line) {
  // Verilog 关键字
  const keywords = [
    'module', 'endmodule', 'input', 'output', 'inout', 'wire', 'reg', 'parameter',
    'localparam', 'assign', 'always', 'initial', 'begin', 'end', 'if', 'else',
    'case', 'endcase', 'for', 'while', 'repeat', 'forever', 'posedge', 'negedge',
    'or', 'and', 'not', 'xor', 'nand', 'nor', 'xnor', 'buf', 'bufif0', 'bufif1',
    'notif0', 'notif1', 'pullup', 'pulldown', 'cmos', 'rcmos', 'nmos', 'pmos',
    'rnmos', 'rpmos', 'tran', 'tranif0', 'tranif1', 'rtran', 'rtranif0', 'rtranif1'
  ]
  
  // 先处理注释
  // 单行注释 //
  line = line.replace(/(\/\/.*$)/gm, '<span class="comment">$1</span>')
  
  // 多行注释 /* */
  line = line.replace(/(\/\*.*?\*\/)/g, '<span class="comment">$1</span>')
  
  // 字符串字面量（避免在注释中匹配）
  line = line.replace(/(&quot;.*?&quot;)(?![^<]*<\/span>)/g, '<span class="string">$1</span>')
  
  // 数字（避免在注释和字符串中匹配）
  line = line.replace(/\b(\d+&#39;[bBoOdDhH][0-9a-fA-FxzXZ_]+)(?![^<]*<\/span>)\b/g, '<span class="number">$1</span>')
  line = line.replace(/\b(\d+)(?![^<]*<\/span>)\b/g, '<span class="number">$1</span>')
  
  // 关键字高亮（避免在注释和字符串中高亮）
  keywords.forEach(keyword => {
    const regex = new RegExp(`\\b(${keyword})\\b(?![^<]*<\/span>)`, 'g')
    line = line.replace(regex, '<span class="keyword">$1</span>')
  })
  
  return line
}

function highlightVhdlSyntax(line) {
  // VHDL 关键字
  const keywords = [
    'entity', 'architecture', 'component', 'configuration', 'library', 'use', 'package',
    'is', 'of', 'begin', 'end', 'signal', 'variable', 'constant', 'type', 'subtype',
    'port', 'generic', 'map', 'in', 'out', 'inout', 'buffer', 'linkage',
    'process', 'if', 'then', 'else', 'elsif', 'case', 'when', 'others',
    'for', 'while', 'loop', 'next', 'exit', 'wait', 'until', 'after',
    'std_logic', 'std_logic_vector', 'integer', 'natural', 'positive', 'boolean',
    'bit', 'bit_vector', 'time', 'string', 'character', 'real',
    'and', 'or', 'not', 'xor', 'nand', 'nor', 'xnor', 'sll', 'srl', 'sla', 'sra', 'rol', 'ror'
  ]
  
  // 先处理注释
  // 单行注释 --
  line = line.replace(/(--.*$)/gm, '<span class="comment">$1</span>')
  
  // 字符串字面量（避免在注释中匹配）
  line = line.replace(/(&quot;.*?&quot;)(?![^<]*<\/span>)/g, '<span class="string">$1</span>')
  line = line.replace(/(&#39;.*?&#39;)(?![^<]*<\/span>)/g, '<span class="string">$1</span>')
  
  // 数字（避免在注释和字符串中匹配）
  line = line.replace(/\b(\d+)(?![^<]*<\/span>)\b/g, '<span class="number">$1</span>')
  
  // 关键字高亮（不区分大小写，避免在注释和字符串中高亮）
  keywords.forEach(keyword => {
    const regex = new RegExp(`\\b(${keyword})\\b(?![^<]*<\/span>)`, 'gi')
    line = line.replace(regex, '<span class="keyword">$1</span>')
  })
  
  return line
}

function highlightGenericSyntax(line) {
  // 通用语法高亮，主要处理注释
  
  // 单行注释 // 或 --
  line = line.replace(/(\/\/.*$|--.*$)/gm, '<span class="comment">$1</span>')
  
  // 多行注释 /* */
  line = line.replace(/(\/\*.*?\*\/)/g, '<span class="comment">$1</span>')
  
  // 字符串字面量
  line = line.replace(/(&quot;.*?&quot;)/g, '<span class="string">$1</span>')
  line = line.replace(/(&#39;.*?&#39;)/g, '<span class="string">$1</span>')
  
  // 数字
  line = line.replace(/\b(\d+\.?\d*)\b/g, '<span class="number">$1</span>')
  
  return line
}

function handleCodeViewModeChange(mode) {
  console.log('代码视图模式切换到:', mode)
  // 模式切换时重新计算代码行
  nextTick(() => {
    if (props.selectedNode && props.selectedNode.type === 'function') {
      scrollToFunction(props.selectedNode)
    }
  })
}

function isLineHighlighted(lineNumber) {
  // 检查是否是问题高亮行
  if (highlightedLines.value.has(lineNumber)) {
    return true
  }
  
  if (!props.selectedNode || (props.selectedNode.type !== 'function' && props.selectedNode.type !== 'fpga_module')) {
    return false
  }
  
  // 如果有行号信息，高亮相关行
  if (props.selectedNode.line) {
    const startLine = props.selectedNode.line
    const endLine = props.selectedNode.end_line || startLine + 10 // 默认高亮10行
    return lineNumber >= startLine && lineNumber <= endLine
  }
  
  // 如果没有行号信息，尝试通过函数名匹配
  const functionName = props.selectedNode.name
  const currentLine = codeLines.value[lineNumber - 1]
  if (currentLine && functionName) {
    return currentLine.includes(functionName) || 
           currentLine.includes(`${functionName}(`) ||
           currentLine.includes(`function ${functionName}`) ||
           currentLine.includes(`def ${functionName}`)
  }
  
  return false
}

function scrollToFunction(node) {
  if (!node || !codeElement.value) return
  
  let targetLine = 1
  
  // 如果有行号信息，直接使用
  if (node.line) {
    targetLine = node.line
  } else if (node.name) {
    // 通过函数名查找行号
    const functionName = node.name
    for (let i = 0; i < codeLines.value.length; i++) {
      const line = codeLines.value[i]
      if (line.includes(functionName) && 
          (line.includes(`${functionName}(`) || 
           line.includes(`function ${functionName}`) ||
           line.includes(`def ${functionName}`) ||
           line.includes(`${functionName} `) ||
           line.trim().startsWith(functionName))) {
        targetLine = i + 1
        break
      }
    }
  }
  
  // 滚动到目标行
  const lineHeight = 24 // 假设每行高度为24px
  const scrollTop = (targetLine - 1) * lineHeight - 100 // 留一些顶部空间
  
  if (codeElement.value.parentElement) {
    codeElement.value.parentElement.scrollTop = Math.max(0, scrollTop)
  }
}

function scrollToLine(lineNumber) {
  if (!codeElement.value || !codeElement.value.parentElement) return
  
  const lineHeight = 24
  const scrollTop = (lineNumber - 1) * lineHeight - 100
  
  codeElement.value.parentElement.scrollTop = Math.max(0, scrollTop)
}

function handleScroll(event) {
  const element = event.target
  scrollInfo.value = {
    scrollTop: element.scrollTop,
    scrollHeight: element.scrollHeight,
    clientHeight: element.clientHeight
  }
}

function isLineVisible(lineNumber) {
  if (!scrollInfo.value.scrollHeight || !scrollInfo.value.clientHeight) {
    return false
  }
  
  const lineHeight = 24
  const lineTop = (lineNumber - 1) * lineHeight
  const lineBottom = lineTop + lineHeight
  
  const viewportTop = scrollInfo.value.scrollTop
  const viewportBottom = viewportTop + scrollInfo.value.clientHeight
  
  return lineTop >= viewportTop && lineBottom <= viewportBottom
}

function highlightProblemLines(problemInfo) {
  if (!problemInfo || !problemInfo.problem) {
    return
  }
  
  const problem = problemInfo.problem
  const linesToHighlight = new Set()
  
  // 清除之前的高亮
  highlightedLines.value.clear()
  
  console.log('=== 开始高亮问题行 ===')
  console.log('问题信息:', problem)
  console.log('当前代码总行数:', codeLines.value.length)
  
  // 唯一方法：从 description_location 提取代码语句并进行全字匹配
  if (problem.description_location) {
    const locationText = problem.description_location
    console.log('解析位置信息:', locationText)
    
    // 提取冒号后的代码语句，支持中文冒号：和英文冒号:
    let colonIndex = locationText.lastIndexOf('：')
    if (colonIndex === -1) {
      colonIndex = locationText.lastIndexOf(':')
    }
    
    if (colonIndex > 0 && colonIndex < locationText.length - 1) {
      const codeStatement = locationText.substring(colonIndex + 1).trim()
      console.log('提取代码语句:', `"${codeStatement}"`)
      console.log('代码语句长度:', codeStatement.length)
      
      // 输出前几行代码用于对比
      console.log('代码前10行内容:')
      for (let i = 0; i < Math.min(10, codeLines.value.length); i++) {
        const line = codeLines.value[i].trim()
        console.log(`行${i + 1}: "${line}" (长度:${line.length})`)
        if (line === codeStatement) {
          console.log(`  ✓ 匹配！`)
        }
      }
      
      // 在代码中查找全字匹配的语句
      for (let i = 0; i < codeLines.value.length; i++) {
        const line = codeLines.value[i].trim()
        if (line === codeStatement) {
          linesToHighlight.add(i + 1)
          console.log(`全字匹配成功: 行号=${i + 1}, 代码=${line}`)
          break
        }
      }
      
      // 如果全字匹配失败，尝试包含匹配（作为备用）
      if (linesToHighlight.size === 0) {
        console.log('全字匹配失败，尝试包含匹配...')
        for (let i = 0; i < codeLines.value.length; i++) {
          const line = codeLines.value[i].trim()
          if (line.includes(codeStatement)) {
            linesToHighlight.add(i + 1)
            console.log(`包含匹配成功: 行号=${i + 1}, 代码=${line}`)
            break
          }
        }
      }
    }
  }
  
  // 如果没有找到匹配，记录日志但不做其他处理
  if (linesToHighlight.size === 0) {
    console.log('❌ 未找到匹配的代码语句')
  }
  
  // 设置高亮行
  highlightedLines.value = linesToHighlight
  
  // 滚动到第一个高亮行
  if (linesToHighlight.size > 0) {
    const firstLine = Math.min(...linesToHighlight)
    console.log('滚动到行:', firstLine)
    scrollToLine(firstLine)
  }
  
  console.log('最终高亮问题行:', Array.from(linesToHighlight))
  console.log('=== 高亮问题行结束 ===')
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

.source-actions {
  display: flex;
  gap: 10px;
}

.source-content {
  flex: 1;
  display: flex;
  overflow: auto;
  background: #1a1a1a;
  position: relative;
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
}

.line-number {
  height: 24px;
  padding-right: 10px;
  transition: all 0.2s ease;
}

.line-number.highlighted {
  background: #3f4b5c;
  color: #61dafb;
  font-weight: bold;
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
}

.code-line {
  display: block;
  min-height: 24px;
  padding: 0 10px;
  margin: 0;
  transition: background-color 0.2s ease;
  white-space: pre;
  /* 移除 overflow-x: auto，避免每行出现独立的横向滚动条 */
}

.code-line.highlighted-line {
  background: rgba(97, 218, 251, 0.1);
  border-left: 3px solid #61dafb;
  padding-left: 7px;
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


/* 小地图样式 */
.minimap {
  position: absolute;
  top: 0;
  right: 0;
  width: 80px;
  height: 100%;
  background: #2d2d2d;
  border-left: 1px solid #404040;
  overflow: hidden;
}

.minimap-content {
  position: relative;
  height: 100%;
  width: 100%;
}

.minimap-line {
  height: 2px;
  width: 100%;
  background: #404040;
  margin-bottom: 1px;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.minimap-line:hover {
  background: #555;
}

.minimap-line.minimap-highlighted {
  background: #61dafb;
  height: 3px;
}

.minimap-line.minimap-visible {
  background: #666;
}

.minimap-viewport {
  position: absolute;
  left: 0;
  right: 0;
  background: rgba(97, 218, 251, 0.2);
  border: 1px solid #61dafb;
  pointer-events: none;
  transition: all 0.1s ease;
}

/* 滚动条样式 */
.source-content::-webkit-scrollbar,
.code-content::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.source-content::-webkit-scrollbar-track,
.code-content::-webkit-scrollbar-track {
  background: #2d2d2d;
}

.source-content::-webkit-scrollbar-thumb,
.code-content::-webkit-scrollbar-thumb {
  background: #555;
  border-radius: 4px;
}

.source-content::-webkit-scrollbar-thumb:hover,
.code-content::-webkit-scrollbar-thumb:hover {
  background: #777;
}

/* 代码高亮样式 */
.code-block {
  /* 关键字 */
  --keyword-color: #c586c0;
  /* 字符串 */
  --string-color: #ce9178;
  /* 注释 */
  --comment-color: #6a9955;
  /* 数字 */
  --number-color: #b5cea8;
  /* 函数名 */
  --function-color: #dcdcaa;
  /* 预处理指令 */
  --preprocessor-color: #9cdcfe;
  
  /* 添加一些基础的语法高亮 */
  position: relative;
}

/* 语法高亮的具体样式 */
.code-block :deep(.keyword) {
  color: var(--keyword-color);
  font-weight: bold;
}

.code-block :deep(.string) {
  color: var(--string-color);
}

.code-block :deep(.comment) {
  color: var(--comment-color);
}

.code-block :deep(.number) {
  color: var(--number-color);
}

.code-block :deep(.function) {
  color: var(--function-color);
  font-weight: 500;
}

.code-block :deep(.preprocessor) {
  color: var(--preprocessor-color);
  font-weight: 500;
}

/* 代码行样式 */
.code-line {
  position: relative;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .source-header {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
  
  .source-actions {
    width: 100%;
    justify-content: flex-end;
  }
  
  .line-numbers {
    min-width: 40px;
    padding: 10px 5px;
  }
  
  .code-block {
    padding: 10px;
    font-size: 12px;
  }
}
</style> 