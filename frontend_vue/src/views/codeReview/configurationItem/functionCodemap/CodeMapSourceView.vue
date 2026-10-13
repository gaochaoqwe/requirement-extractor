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
          <span class="file-name">{{ getFileName(selectedNode.file_path) }}</span>
          <el-tag v-if="selectedNode.type === 'function'" type="success" size="small">
            函数: {{ selectedNode.name }}
          </el-tag>
          <el-tag v-else-if="selectedNode.type === 'fpga_module'" type="danger" size="small">
            FPGA模块: {{ selectedNode.name }}
          </el-tag>
        </div>
        <div class="source-actions">
          <!-- 源码/注释切换按钮 -->
          <el-radio-group v-model="codeViewMode" size="small" @change="handleCodeViewModeChange">
            <el-radio-button label="original">源代码</el-radio-button>
            <el-radio-button label="commented">注释后代码</el-radio-button>
          </el-radio-group>
          <!-- 下载注释后代码 -->
          <el-button
            v-if="codeViewMode === 'commented'"
            type="primary"
            size="small"
            :icon="Download"
            :disabled="!codeLines.length"
            @click="downloadCommentedCode"
          >
            下载注释代码
          </el-button>
        </div>
      </div>
      
      <!-- 源码内容 -->
      <div class="source-content">
        <div class="line-numbers" @wheel="handleLineNumberWheel">
          <div class="line-numbers-inner" ref="lineNumbers">
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
        </div>
        <div class="code-content" ref="codeContainer" @scroll="handleScroll">
          <pre ref="codeElement" class="code-block"><code>
            <span 
              v-for="(line, index) in codeLines" 
              :key="index"
              :class="{ 
                'highlighted-line': isLineHighlighted(index + 1) && !highlightedLines.has(index + 1),
                'problem-highlighted-line': highlightedLines.has(index + 1)
              }"
              class="code-line"
              v-html="highlightSyntax(line, getFileLanguage())"
            ></span>
          </code></pre>
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
import { Document, Download } from '@element-plus/icons-vue'

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
const codeContainer = ref(null)
const lineNumbers = ref(null)
const codeViewMode = ref('original') // 'original' | 'commented'
const scrollInfo = ref({
  scrollTop: 0,
  scrollHeight: 0,
  clientHeight: 0
})
const highlightedLines = ref(new Set())

function logRenderMetrics(tag = 'render') {
  nextTick(() => {
    const container = codeContainer.value
    const codeEl = codeElement.value
    const lineElCount = codeEl?.querySelectorAll?.('.code-line')?.length || 0
    const lastLineEl = codeEl?.querySelector?.('.code-line:last-child')
    const containerRect = container?.getBoundingClientRect?.()
    const codeRect = codeEl?.getBoundingClientRect?.()

    console.log(`[FunctionCodeMapSourceView][${tag}] DOM统计`, {
      codeLineCount: codeLines.value.length,
      renderedLineElements: lineElCount,
      selectedNode: props.selectedNode?.name,
      selectedType: props.selectedNode?.type,
      codeViewMode: codeViewMode.value,
      containerClientHeight: container?.clientHeight,
      containerScrollHeight: container?.scrollHeight,
      containerScrollTop: container?.scrollTop,
      codeOffsetHeight: codeEl?.offsetHeight,
      codeScrollHeight: codeEl?.scrollHeight,
      containerRect,
      codeRect,
      lastLineText: codeLines.value[codeLines.value.length - 1]?.substring(0, 120),
      lastLineElementText: lastLineEl?.textContent?.substring(0, 120),
      lastLineElementOffsetTop: lastLineEl?.offsetTop,
      lastLineElementOffsetHeight: lastLineEl?.offsetHeight
    })
  })
}

// 计算属性
const codeLines = computed(() => {
  if (!props.selectedNode) {
    return []
  }
  
  // 根据当前视图模式选择显示的代码
  let codeToShow = ''
  if (codeViewMode.value === 'commented') {
    console.log('[FunctionCodeMapSourceView] 切换到注释后代码模式')
    console.log('[FunctionCodeMapSourceView] 节点类型:', props.selectedNode.type)
    console.log('[FunctionCodeMapSourceView] 节点名称:', props.selectedNode.name)
    
    // 如果是函数或FPGA模块节点，直接使用其commented_code
    if (props.selectedNode.type === 'function' || props.selectedNode.type === 'fpga_module' || props.selectedNode.type === 'fpga_file') {
      console.log('[FunctionCodeMapSourceView] 处理函数/FPGA模块节点')
      console.log('[FunctionCodeMapSourceView] commented_code 存在:', !!props.selectedNode.commented_code)
      console.log('[FunctionCodeMapSourceView] commented_code 长度:', props.selectedNode.commented_code?.length || 0)
      
      if (props.selectedNode.commented_code) {
        codeToShow = props.selectedNode.commented_code
        console.log('[FunctionCodeMapSourceView] 使用 commented_code，长度:', codeToShow.length)
        console.log('[FunctionCodeMapSourceView] 前500字符:', codeToShow.substring(0, 500))
      } else if (props.selectedNode.function_description) {
        // 如果有函数描述，显示原代码+函数描述
        codeToShow = props.selectedNode.source_code + '\n\n/* AI 生成的函数描述:\n' + props.selectedNode.function_description + '\n*/'
        console.log('[FunctionCodeMapSourceView] 使用 function_description，长度:', codeToShow.length)
      } else {
        // 如果没有注释后的代码，显示原代码
        codeToShow = props.selectedNode.source_code || ''
        const nodeTypeName = props.selectedNode.type === 'fpga_file' ? '文件' : '函数'
        console.log('[FunctionCodeMapSourceView] 没有注释后代码，使用原代码，长度:', codeToShow.length)
        ElMessage.warning(`该${nodeTypeName}暂无AI注释后的代码`)
      }
    } else if (props.selectedNode.type === 'file') {
      console.log('[FunctionCodeMapSourceView] 处理文件节点')
      console.log('[FunctionCodeMapSourceView] 子函数数量:', props.selectedNode.children?.length || 0)
      
      // 如果是文件节点，尝试拼接所有子函数的注释后代码
      if (props.selectedNode.children && props.selectedNode.children.length > 0) {
        const commentedParts = []
        let hasCommented = false
        const fileSourceCode = props.selectedNode.source_code || ''
        const fileLines = fileSourceCode.split('\n')

        // 对子函数按 start_line 排序
        const sortedChildren = [...props.selectedNode.children].sort(
          (a, b) => (a.start_line || 0) - (b.start_line || 0)
        )

        // 插入文件头（第一个函数之前的内容）
        if (fileLines.length > 0 && sortedChildren.length > 0) {
          const firstFuncStart = (sortedChildren[0].start_line || 1) - 1  // 转为0-based
          if (firstFuncStart > 0) {
            const fileHeader = fileLines.slice(0, firstFuncStart).join('\n').trimEnd()
            if (fileHeader.trim()) {
              commentedParts.push(fileHeader)
              commentedParts.push('')
            }
          }
        }

        let prevEndLine = sortedChildren.length > 0 ? (sortedChildren[0].start_line || 1) - 1 : 0

        for (let i = 0; i < sortedChildren.length; i++) {
          const child = sortedChildren[i]
          const childStart = (child.start_line || 1) - 1  // 0-based
          const childEnd = child.end_line || childStart

          console.log(`[FunctionCodeMapSourceView] 处理子函数 ${i}: ${child.name}, commented_code长度: ${child.commented_code?.length || 0}`)

          // 插入函数间的非函数代码（如全局变量、结构体等）
          if (i > 0 && childStart > prevEndLine) {
            const between = fileLines.slice(prevEndLine, childStart).join('\n').trim()
            if (between) {
              commentedParts.push(between)
              commentedParts.push('')
            }
          }

          if (child.commented_code) {
            hasCommented = true
            commentedParts.push(`// ========== ${child.name} ==========`)
            commentedParts.push(child.commented_code)
            commentedParts.push('')
            console.log(`[FunctionCodeMapSourceView] 添加子函数 ${child.name} 的注释后代码，长度: ${child.commented_code.length}`)
          } else if (child.source_code) {
            commentedParts.push(`// ========== ${child.name} (未注释) ==========`)
            commentedParts.push(child.source_code)
            commentedParts.push('')
            console.log(`[FunctionCodeMapSourceView] 添加子函数 ${child.name} 的原代码，长度: ${child.source_code.length}`)
          }

          prevEndLine = childEnd
        }

        // 插入最后一个函数之后的内容
        if (fileLines.length > prevEndLine) {
          const fileFooter = fileLines.slice(prevEndLine).join('\n').trim()
          if (fileFooter) {
            commentedParts.push(fileFooter)
          }
        }

        if (hasCommented) {
          codeToShow = commentedParts.join('\n')
          console.log('[FunctionCodeMapSourceView] 文件注释后代码总长度:', codeToShow.length)
        } else {
          codeToShow = props.selectedNode.source_code || ''
          console.log('[FunctionCodeMapSourceView] 文件没有注释后代码，使用原代码，长度:', codeToShow.length)
          ElMessage.warning('该文件中的函数暂无AI注释后的代码，显示原代码')
        }
      } else {
        // 文件节点没有子函数，显示原代码
        codeToShow = props.selectedNode.source_code || ''
        console.log('[FunctionCodeMapSourceView] 文件节点没有子函数，使用原代码，长度:', codeToShow.length)
        ElMessage.warning('该文件暂无AI注释后的代码')
      }
    } else {
      // 其他类型节点，显示原代码
      codeToShow = props.selectedNode.source_code || ''
      console.log('[FunctionCodeMapSourceView] 其他类型节点，使用原代码，长度:', codeToShow.length)
      ElMessage.warning('暂无AI注释后的代码')
    }
  } else {
    // 显示原代码
    codeToShow = props.selectedNode.source_code || ''
    console.log('[FunctionCodeMapSourceView] 显示原代码，长度:', codeToShow.length)
  }
  
  // 直接分割代码行，不处理转义字符
  // 源代码应该原样显示，包括 \n, \t 等转义字符
  if (!codeToShow) {
    console.log('[FunctionCodeMapSourceView] codeToShow 为空')
    return []
  }
  
  // 分割代码行并清理每行的回车符
  const lines = codeToShow.split('\n').map(line => line.replace(/\r/g, ''))
  console.log('[FunctionCodeMapSourceView] 分割后的代码行数:', lines.length)
  console.log('[FunctionCodeMapSourceView] 最后一行内容:', lines[lines.length - 1]?.substring(0, 100))
  
  return lines
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
    console.log('[FunctionCodeMapSourceView] 节点变化，新节点:', newNode.name)
    console.log('[FunctionCodeMapSourceView] 新节点 commented_code 长度:', newNode.commented_code?.length || 0)
    await nextTick()
    logRenderMetrics('selected-node-change-before-scroll')
    scrollToFunction(newNode)
    logRenderMetrics('selected-node-change-after-scroll')
  }
}, { immediate: true })

// 监听高亮问题变化
watch(() => props.highlightedProblem, async (newProblem) => {
  if (newProblem) {
    await nextTick()
    highlightProblemLines(newProblem)
  }
}, { immediate: true })

// 监听 codeLines 变化，检测截断
watch(() => codeLines.value, (newLines) => {
  console.log('[FunctionCodeMapSourceView] codeLines 变化，新行数:', newLines.length)
  if (newLines.length > 0) {
    console.log('[FunctionCodeMapSourceView] 第一行:', newLines[0]?.substring(0, 50))
    console.log('[FunctionCodeMapSourceView] 最后一行:', newLines[newLines.length - 1]?.substring(0, 50))
  }
  logRenderMetrics('code-lines-change')
}, { immediate: false })

// 方法
function getFileName(filePath) {
  if (!filePath) return ''
  return filePath.split('/').pop() || filePath.split('\\').pop() || filePath
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
  console.log('[FunctionCodeMapSourceView] 代码视图模式切换到:', mode)
  console.log('[FunctionCodeMapSourceView] 当前节点:', props.selectedNode?.name)
  console.log('[FunctionCodeMapSourceView] 节点 commented_code 长度:', props.selectedNode?.commented_code?.length || 0)
  console.log('[FunctionCodeMapSourceView] 节点 source_code 长度:', props.selectedNode?.source_code?.length || 0)
  
  // 模式切换时重新计算代码行
  nextTick(() => {
    console.log('[FunctionCodeMapSourceView] 模式切换后，当前代码行数:', codeLines.value.length)
    logRenderMetrics('mode-change')
    if (props.selectedNode && props.selectedNode.type === 'function') {
      scrollToFunction(props.selectedNode)
      logRenderMetrics('mode-change-after-scroll')
    }
  })
}

// 构造下载文件名：保持与原始文件完全一致，不添加任何前后缀
function buildCommentedFileName() {
  const node = props.selectedNode
  if (!node) {
    return 'commented_code.txt'
  }

  // 统一分隔符后取文件名部分，确保下载名与原始文件名一致
  const rawPath = String(node.file_path || '').replace(/\\/g, '/')
  const baseName = rawPath.split('/').filter(Boolean).pop() || ''

  return baseName || 'code.txt'
}

// 下载当前「注释后代码」
function downloadCommentedCode() {
  if (!codeLines.value.length) {
    ElMessage.warning('当前没有可下载的注释代码')
    return
  }

  try {
    const content = codeLines.value.join('\n')
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = buildCommentedFileName()
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('注释代码下载成功')
  } catch (error) {
    console.error('[FunctionCodeMapSourceView] 下载注释代码失败:', error)
    ElMessage.error('下载注释代码失败')
  }
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
  if (!node || !codeContainer.value) return
  
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
  
  codeContainer.value.scrollTop = Math.max(0, scrollTop)
}

function scrollToLine(lineNumber) {
  if (!codeContainer.value) return
  
  const lineHeight = 24
  const scrollTop = (lineNumber - 1) * lineHeight - 100
  
  codeContainer.value.scrollTop = Math.max(0, scrollTop)
}

function handleScroll(event) {
  const element = event.target
  scrollInfo.value = {
    scrollTop: element.scrollTop,
    scrollHeight: element.scrollHeight,
    clientHeight: element.clientHeight
  }

  console.log('[FunctionCodeMapSourceView][scroll]', {
    scrollTop: element.scrollTop,
    scrollHeight: element.scrollHeight,
    clientHeight: element.clientHeight,
    visibleBottomLineEstimate: Math.floor((element.scrollTop + element.clientHeight) / 24)
  })
  
  // 同步行号容器的垂直滚动（使用 transform 而不是 scrollTop）
  if (lineNumbers.value) {
    // 使用 transform 来移动行号，不需要行号容器本身可滚动
    const translateY = -element.scrollTop
    lineNumbers.value.style.transform = `translateY(${translateY}px)`
  }
}

// 处理行号区域的滚轮事件，将其转发到代码容器
function handleLineNumberWheel(event) {
  if (codeContainer.value) {
    event.preventDefault()
    // 将滚轮事件转发到代码容器
    codeContainer.value.scrollTop += event.deltaY
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
  console.log('当前节点类型:', props.selectedNode?.type)
  console.log('当前节点名称:', props.selectedNode?.name)
  
  // 唯一方法：从 description_location 提取代码语句并进行全字匹配
  if (problem.description_location) {
    const normalizedLocationText = String(problem.description_location)
      .replace(/\\r\\n/g, '\n')
      .replace(/\\n/g, '\n')
      .replace(/\\t/g, '\t')
    const sourceMarkers = ['源程序为：', '源代码为：', '源程序为:', '源代码为:']
    const markerInfo = sourceMarkers
      .map(marker => ({ marker, index: normalizedLocationText.indexOf(marker) }))
      .filter(item => item.index !== -1)
      .sort((a, b) => a.index - b.index)[0]
    const locationText = markerInfo
      ? normalizedLocationText.slice(0, markerInfo.index)
      : normalizedLocationText
    console.log('解析位置信息:', normalizedLocationText)
    
    // 提取冒号后的代码语句，支持中文冒号：和英文冒号:
    let colonIndex = locationText.lastIndexOf('：')
    if (colonIndex === -1) {
      colonIndex = locationText.lastIndexOf(':')
    }
    
    if (colonIndex > 0 && colonIndex < locationText.length - 1) {
      const codeStatement = locationText.substring(colonIndex + 1).trim()
      console.log('提取代码语句:', `"${codeStatement}"`)
      console.log('代码语句长度:', codeStatement.length)
      console.log('代码语句字符编码:', Array.from(codeStatement).map(c => c.charCodeAt(0)))
      
      // 输出前几行代码用于对比
      console.log('代码前20行内容:')
      for (let i = 0; i < Math.min(20, codeLines.value.length); i++) {
        const line = codeLines.value[i].trim()
        console.log(`行${i + 1}: "${line}" (长度:${line.length})`)
        if (line === codeStatement) {
          console.log(`  ✓ 全字匹配！`)
        } else if (line.includes(codeStatement)) {
          console.log(`  ~ 包含匹配`)
        }
      }
      
      // 方法1: 全字匹配
      for (let i = 0; i < codeLines.value.length; i++) {
        const line = codeLines.value[i].trim()
        if (line === codeStatement) {
          linesToHighlight.add(i + 1)
          console.log(`✓ 全字匹配成功: 行号=${i + 1}`)
          break
        }
      }
      
      // 方法2: 如果全字匹配失败，尝试包含匹配
      if (linesToHighlight.size === 0) {
        console.log('全字匹配失败，尝试包含匹配...')
        for (let i = 0; i < codeLines.value.length; i++) {
          const line = codeLines.value[i].trim()
          if (line.includes(codeStatement)) {
            linesToHighlight.add(i + 1)
            console.log(`✓ 包含匹配成功: 行号=${i + 1}`)
            break
          }
        }
      }
      
      // 方法3: 如果还是失败，尝试规范化空白字符后匹配（处理制表符、多余空格等）
      if (linesToHighlight.size === 0) {
        console.log('包含匹配失败，尝试规范化空白字符后匹配...')
        const normalizedStatement = codeStatement.replace(/\s+/g, ' ')
        console.log('规范化后的代码语句:', `"${normalizedStatement}"`)
        
        for (let i = 0; i < codeLines.value.length; i++) {
          const line = codeLines.value[i].trim()
          const normalizedLine = line.replace(/\s+/g, ' ')
          
          if (normalizedLine === normalizedStatement) {
            linesToHighlight.add(i + 1)
            console.log(`✓ 规范化匹配成功: 行号=${i + 1}`)
            console.log(`  原始行: "${line}"`)
            console.log(`  规范化行: "${normalizedLine}"`)
            break
          }
        }
      }
      
      // 方法4: 如果还是失败，尝试部分匹配（至少匹配代码语句的主要部分）
      if (linesToHighlight.size === 0) {
        console.log('规范化匹配失败，尝试模糊匹配...')
        // 提取代码语句的关键部分（去除可能变化的空格和标点符号）
        const keyPart = codeStatement.replace(/[^\w]/g, '').toLowerCase()
        console.log('关键部分:', `"${keyPart}"`)
        
        if (keyPart.length >= 5) { // 至少5个字符才尝试模糊匹配
          for (let i = 0; i < codeLines.value.length; i++) {
            const line = codeLines.value[i].trim()
            const lineKeyPart = line.replace(/[^\w]/g, '').toLowerCase()
            
            if (lineKeyPart.includes(keyPart)) {
              linesToHighlight.add(i + 1)
              console.log(`✓ 模糊匹配成功: 行号=${i + 1}`)
              console.log(`  原始行: "${line}"`)
              console.log(`  行关键部分: "${lineKeyPart}"`)
              break
            }
          }
        }
      }
    } else {
      console.log('❌ description_location格式不正确，无法提取代码语句')
    }
  } else {
    console.log('❌ 问题没有description_location字段')
  }
  
  // 如果没有找到匹配，记录详细日志
  if (linesToHighlight.size === 0) {
    console.log('❌ 所有匹配方法都失败了')
    console.log('问题完整信息:', JSON.stringify(problem, null, 2))
    ElMessage.warning('无法在当前代码中定位到该问题，可能是代码语句格式不匹配')
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
  min-height: 0;
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
  min-height: 0;
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
  min-height: 0;
  display: flex;
  overflow: hidden;
  background: #1a1a1a;
  position: relative;
}

.line-numbers {
  background: #2d2d2d;
  border-right: 1px solid #404040;
  flex-shrink: 0;
  min-width: 60px;
  height: 100%;
  overflow: hidden;
  position: relative;
}

.line-numbers-inner {
  color: #666;
  padding: 20px 10px;
  text-align: right;
  font-size: 14px;
  line-height: 24px;
  user-select: none;
  /* 行号通过 transform 移动 */
  will-change: transform;
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
  height: 100%;
  min-width: 0;
  overflow: auto;
}

.code-block {
  margin: 0;
  padding: 20px;
  min-height: 100%;
  box-sizing: border-box;
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