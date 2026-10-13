<template>
  <div class="sidebar">
    <div class="sidebar-header">
      <h3>{{ title }}</h3>
      <div class="header-actions">
        <el-button 
          v-if="mode === 'node' && hasMarkedProblems"
          type="success" 
          size="small"
          @click="viewMarkedProblems"
          :icon="View"
        >
          查看标记问题 ({{ markedProblemsCount }})
        </el-button>
        <el-button 
          v-if="mode === 'node' && hasMarkedProblems"
          type="primary" 
          size="small"
          @click="exportMarkedProblems"
          :loading="exporting"
          :icon="Download"
        >
          导出已标记
        </el-button>
        <el-button @click="$emit('close')" :icon="Close" size="small" text />
      </div>
    </div>
    
    <div class="sidebar-content">
      <!-- 统计信息 -->
      <div v-if="mode === 'stats'" class="stats-panel">
        <div v-if="statistics" class="stats-grid">
          <div class="stat-item">
            <div class="stat-number">{{ statistics.total_nodes }}</div>
            <div class="stat-label">总节点数</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">{{ statistics.total_functions }}</div>
            <div class="stat-label">函数数量</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">{{ statistics.total_files }}</div>
            <div class="stat-label">文件数量</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">{{ statistics.total_problems }}</div>
            <div class="stat-label">问题数量</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">{{ statistics.total_edges }}</div>
            <div class="stat-label">调用关系</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">{{ statistics.max_depth }}</div>
            <div class="stat-label">最大深度</div>
          </div>
        </div>
        
        <!-- 颜色说明 -->
        <div class="color-legend">
          <h4>节点颜色说明</h4>
          <div class="legend-item">
            <div class="legend-color file-color"></div>
            <span>C/C++文件</span>
          </div>
          <div class="legend-item">
            <div class="legend-color function-color"></div>
            <span>C/C++函数</span>
          </div>
          <div class="legend-item">
            <div class="legend-color fpga-file-color"></div>
            <span>FPGA文件</span>
          </div>
          <div class="legend-item">
            <div class="legend-color fpga-module-color"></div>
            <span>FPGA模块</span>
          </div>
          <div class="legend-item">
            <div class="legend-color problem-color"></div>
            <span>有问题的节点</span>
          </div>
        </div>
      </div>

      <!-- 节点详情 -->
      <div v-else-if="mode === 'node' && selectedNode" class="node-details">
        <div class="node-header">
          <h4>{{ selectedNode.name }}</h4>
          <el-tag :type="getNodeTagType(selectedNode.type)">
            {{ getNodeTypeLabel(selectedNode.type) }}
          </el-tag>
        </div>
        
        <div class="node-info">
          <!-- 函数描述信息（模型返回的文件功能信息） -->
          <div v-if="selectedNode.function_description" class="function-description-section">
            <div class="section-title">
              <el-icon><Document /></el-icon>
              <span>函数功能描述</span>
            </div>
            <div class="function-description-content">
              <div class="description-text">{{ selectedNode.function_description }}</div>
            </div>
          </div>
          
          <!-- 如果没有函数描述，显示提示 -->
          <div v-else-if="selectedNode.type === 'function' || selectedNode.type === 'fpga_module'" class="no-description-section">
            <div class="section-title">
              <el-icon><Document /></el-icon>
              <span>{{ selectedNode.type === 'fpga_module' ? 'FPGA模块功能描述' : '函数功能描述' }}</span>
            </div>
            <div class="no-description-content">
              <el-empty :description="selectedNode.type === 'fpga_module' ? '暂无AI生成的模块描述' : '暂无AI生成的函数描述'" />
            </div>
          </div>
          
          <!-- 文件类型节点显示基本信息 -->
          <div v-else-if="selectedNode.type === 'file' || selectedNode.type === 'fpga_file'" class="file-basic-info">
            <div class="section-title">
              <el-icon><Document /></el-icon>
              <span>文件信息</span>
            </div>
            <div class="file-basic-content">
              <div class="info-item">
                <span class="info-label">文件名:</span>
                <span class="info-value">{{ getFileName(selectedNode.file_path) }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">文件类型:</span>
                <span class="info-value">{{ getFileType(selectedNode.file_path) }}</span>
              </div>
              <div v-if="selectedNode.function_count" class="info-item">
                <span class="info-label">函数数量:</span>
                <span class="info-value">{{ selectedNode.function_count }} 个</span>
              </div>
            </div>
          </div>
          
          <!-- 问题列表（问题1、问题2、问题3等） -->
          <div v-if="selectedNode.problems && selectedNode.problems.length > 0" class="problems-section">
            <div class="section-title">
              <el-icon><Warning /></el-icon>
              <span>发现的问题</span>
              <el-tag type="danger" size="small">{{ selectedNode.problems.length }} 个问题</el-tag>
              <el-button
                type="primary"
                size="small"
                text
                @click="$emit('showFilterPanel')"
                style="margin-left: auto;"
              >
                过滤设置
              </el-button>
            </div>
            
            <div class="problems-list">
              <div 
                v-for="(problem, index) in selectedNode.problems" 
                :key="index" 
                class="problem-block"
                :class="getProblemStatusClass(problem)"
              >
                <div 
                  class="problem-title"
                  @click="handleProblemClick(problem, index)"
                >
                  <div class="problem-title-left">
                    <div class="problem-status-indicator" :class="getProblemStatusIndicatorClass(problem)"></div>
                    <el-icon><Warning /></el-icon>
                    <span>问题 {{ index + 1 }}</span>
                    <el-tag 
                      v-if="getProblemStatusLabel(problem)"
                      :type="getProblemStatusTagType(problem)" 
                      size="small"
                      class="status-tag"
                    >
                      {{ getProblemStatusLabel(problem) }}
                    </el-tag>
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
                      :type="isProblemMarked(problem) ? 'success' : 'info'" 
                      size="small" 
                      text
                      @click.stop="toggleProblemMark(problem)"
                      :title="isProblemMarked(problem) ? '取消标记' : '标记为已确认'"
                    >
                      <el-icon><Check v-if="isProblemMarked(problem)" /><Flag v-else /></el-icon>
                      {{ isProblemMarked(problem) ? '已标记' : '标记' }}
                    </el-button>
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
                    <!-- 问题来源 -->
                    <div v-if="problem.problem_source" class="problem-field">
                      <div class="field-label">问题来源</div>
                      <div class="field-value">
                        <el-tag :type="getProblemSourceTagType(problem.problem_source)" size="small">
                          {{ getProblemSourceLabel(problem.problem_source) }}
                        </el-tag>
                      </div>
                    </div>

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
                    <div v-if="problem.description_location" class="problem-field location-problem-field">
                      <div class="field-label">位置描述</div>
                      <div class="field-value">{{ getDescriptionLocationSummary(problem.description_location) }}</div>
                      <div v-if="getDescriptionLocationSource(problem.description_location)" class="source-program-section">
                        <div class="source-program-title">源程序为：</div>
                        <pre class="source-program-code">{{ getDescriptionLocationSource(problem.description_location) }}</pre>
                      </div>
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
        </div>
      </div>

      <!-- 搜索结果 -->
      <div v-else-if="mode === 'search'" class="search-results">
        <div v-if="searchResults.length === 0" class="no-results">
          <p>没有找到匹配的结果</p>
        </div>
        <div v-else>
          <div
            v-for="result in searchResults"
            :key="result.id"
            class="search-result-item"
            @click="$emit('highlightNode', result.id)"
          >
            <div class="result-header">
              <span class="result-name">{{ result.name }}</span>
              <el-tag size="small" :type="getResultTagType(result.type)">
                {{ result.type }}
              </el-tag>
            </div>
            <div class="result-details">
              <p v-if="result.file_path">{{ result.file_path }}</p>
              <p v-if="result.description">{{ result.description }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 注释准确率反馈弹窗 -->
    <CommentAccuracyFeedback
      v-model:visible="showFeedbackDialog"
      :task-id="taskId"
      :clicked-count="feedbackStatus.clickedCount"
      :total-functions="feedbackStatus.totalFunctions"
      :trigger-point="feedbackTriggerPoint"
      :delayed-count="feedbackStatus.delayedCount"
      @submitted="handleFeedbackSubmitted"
      @delayed="handleFeedbackDelayed"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Close, Warning, Document, Edit, ArrowDown, Download, Check, Flag, View } from '@element-plus/icons-vue'
import { ElCollapseTransition, ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import { buildProblemKey } from '../shared/problemMarking';
import CommentAccuracyFeedback from './CommentAccuracyFeedback.vue'

// Props
const props = defineProps({
  mode: {
    type: String,
    default: 'stats'
  },
  title: {
    type: String,
    default: '侧边栏'
  },
  statistics: {
    type: Object,
    default: null
  },
  selectedNode: {
    type: Object,
    default: null
  },
  searchResults: {
    type: Array,
    default: () => []
  },
  showFullCode: {
    type: Boolean,
    default: false
  },
  treeData: {
    type: Array,
    default: () => []
  }
})

// Emits
const emit = defineEmits(['close', 'highlightNode', 'highlightProblem', 'viewMarkedProblems', 'showFilterPanel', 'problemStatusChanged'])

// 路由
const route = useRoute()
const taskId = computed(() => route.params.taskId)

// 响应式数据
const collapsedProblems = ref(new Set())
const markedProblems = ref(new Set()) // 存储已标记的问题key
const exporting = ref(false)
const loading = ref(false)

// 计算目录树中实际的函数节点总数
const treeFunctionCount = computed(() => {
  let count = 0
  const countFunctions = (nodes) => {
    for (const node of nodes) {
      if (node.type === 'function' || node.type === 'fpga_module') {
        count++
      }
      if (node.children && node.children.length > 0) {
        countFunctions(node.children)
      }
    }
  }
  countFunctions(props.treeData)
  return count
})

// 注释准确率反馈相关
const showFeedbackDialog = ref(false)
const feedbackStatus = ref({
  clickedCount: 0,
  totalFunctions: 0,
  hasFeedback: false,
  delayedCount: 0
})
const feedbackTriggerPoint = ref('50%')

// 方法
function getFileName(filePath) {
  if (!filePath) return '';
  const parts = filePath.split('/');
  return parts[parts.length - 1];
}

function getFileType(filePath) {
  if (!filePath) return '未知'
  const ext = filePath.split('.').pop()?.toLowerCase()
  switch (ext) {
    case 'c': return 'C文件'
    case 'cpp': case 'cc': case 'cxx': return 'C++文件'
    case 'h': case 'hpp': case 'hxx': return '头文件'
    case 'v': return 'Verilog文件'
    case 'vhd': case 'vhdl': return 'VHDL文件'
    default: return '代码文件'
  }
}

function getNodeTagType(type) {
  switch (type) {
    case 'file':
      return 'primary'
    case 'function':
      return 'success'
    case 'fpga_file':
      return 'warning'
    case 'fpga_module':
      return 'danger'
    default:
      return 'info'
  }
}

function getNodeTypeLabel(type) {
  switch (type) {
    case 'file':
      return '文件'
    case 'function':
      return '函数'
    case 'fpga_file':
      return 'FPGA文件'
    case 'fpga_module':
      return 'FPGA模块'
    default:
      return '未知'
  }
}

function getResultTagType(type) {
  switch (type) {
    case 'node': return 'primary'
    case 'problem': return 'danger'
    case 'file': return 'primary'
    case 'function': return 'success'
    default: return 'info'
  }
}

function getIssueLevelTagType(level) {
  switch (level) {
    case '重要问题': return 'danger'
    case '一般问题': return 'warning'
    case '建议改进': return 'info'
    default: return 'info'
  }
}

function getProblemSourceLabel(source) {
  switch (source) {
    case 'comment_review':
      return '注释专项'
    case 'main_review':
    default:
      return '主审查'
  }
}

function getProblemSourceTagType(source) {
  switch (source) {
    case 'comment_review':
      return 'warning'
    case 'main_review':
    default:
      return 'success'
  }
}

function normalizeLocationText(value) {
  return String(value || '').replace(/\\r\\n/g, '\n').replace(/\\n/g, '\n').replace(/\\t/g, '\t')
}

function splitDescriptionLocation(value) {
  const normalized = normalizeLocationText(value)
  const markers = ['源程序为：', '源代码为：', '源程序为:', '源代码为:']
  const markerInfo = markers
    .map(marker => ({ marker, index: normalized.indexOf(marker) }))
    .filter(item => item.index !== -1)
    .sort((a, b) => a.index - b.index)[0]

  if (!markerInfo) {
    return {
      summary: normalized,
      source: ''
    }
  }

  return {
    summary: normalized.slice(0, markerInfo.index).trim(),
    source: normalized.slice(markerInfo.index + markerInfo.marker.length).replace(/^\s*\n/, '')
  }
}

function getDescriptionLocationSummary(value) {
  return splitDescriptionLocation(value).summary
}

function getDescriptionLocationSource(value) {
  return splitDescriptionLocation(value).source
}

function toggleProblem(index) {
  if (collapsedProblems.value.has(index)) {
    collapsedProblems.value.delete(index)
  } else {
    collapsedProblems.value.add(index)
  }
}

// 处理问题点击（展开/折叠 + 更新状态）
async function handleProblemClick(problem, index) {
  // 先切换展开/折叠
  toggleProblem(index)
  
  // 如果问题状态为1（新发现），点击后更新为2（已查看）
  if (problem.problem_status === 1) {
    await updateProblemStatus(problem, 2)
  }
}

// 更新问题状态
async function updateProblemStatus(problem, newStatus) {
  try {
    const response = await axios.patch(
      `/api/codeReview/${taskId.value}/problems/${problem.id}/status`,
      null,
      {
        params: { status: newStatus }
      }
    )
    if (response.data.success) {
      // 更新本地状态
      problem.problem_status = newStatus
      emit('problemStatusChanged')
    }
  } catch (error) {
    console.error('更新问题状态失败:', error)
  }
}

// 获取问题状态class
function getProblemStatusClass(problem) {
  const status = problem.problem_status || 1
  return {
    'status-new': status === 1,
    'status-viewed': status === 2,
    'status-filtered': status === 3,
    'status-marked': status === 4
  }
}

// 获取问题状态指示器class
function getProblemStatusIndicatorClass(problem) {
  const status = problem.problem_status || 1
  return {
    'indicator-green': status === 1,
    'indicator-gray': status === 2 || status === 3,
    'indicator-marked': status === 4
  }
}

// 获取问题状态标签
function getProblemStatusLabel(problem) {
  const status = problem.problem_status || 1
  if (status === 4) return '已标记'
  if (status === 3) return '已过滤'
  return null
}

// 获取问题状态标签类型
function getProblemStatusTagType(problem) {
  const status = problem.problem_status || 1
  if (status === 4) return 'success'
  if (status === 3) return 'info'
  return ''
}

function highlightProblemInCode(problem, problemIndex) {
  // 发送事件到父组件，传递问题信息用于在代码中高亮显示
  emit('highlightProblem', {
    problem,
    problemIndex,
    nodeInfo: props.selectedNode
  })
}

// 标记功能相关
// 计算属性：已标记问题数量
const markedProblemsCount = computed(() => {
  return markedProblems.value.size
})

// 计算属性：是否有已标记的问题
const hasMarkedProblems = computed(() => {
  return markedProblems.value.size > 0
})

// 检查问题是否已标记
function isProblemMarked(problem) {
  const problemId = buildProblemKey(problem)
  return markedProblems.value.has(problemId)
}

// 切换问题标记状态
async function toggleProblemMark(problem) {
  const problemKey = buildProblemKey(problem);
  const isMarked = markedProblems.value.has(problemKey);
  
  try {
    if (isMarked) {
      // 取消标记
      await axios.delete(`/api/codeReview/${taskId.value}/marked_problems`, {
        data: {
          analysis_type: 'function',
          problem_key: problemKey
        }
      });
      markedProblems.value.delete(problemKey);
      
      // 取消标记时，将状态恢复为已查看（状态2）
      await updateProblemStatus(problem, 2);
      
      ElMessage.success('已取消标记');
    } else {
      // 添加标记
      // 将Proxy对象转换为普通对象
      const plainProblem = typeof problem === 'object' ? JSON.parse(JSON.stringify(problem)) : { raw: problem };
      
      const requestData = {
        analysis_type: 'function',
        problem_key: String(problemKey), // 确保是字符串
        problem_data: plainProblem
      };
      console.log('发送标记请求:', requestData);
      console.log('problem_key类型:', typeof requestData.problem_key);
      console.log('problem_data类型:', typeof requestData.problem_data);
      
      await axios.post(`/api/codeReview/${taskId.value}/marked_problems`, requestData);
      markedProblems.value.add(problemKey);
      
      // 标记时，将状态设置为已标记（状态4）
      await updateProblemStatus(problem, 4);
      
      ElMessage.success('标记成功');
    }
    markedProblems.value = new Set(markedProblems.value);
  } catch (error) {
    console.error('标记操作失败:', error);
    console.error('错误详情:', error.response?.data);
    ElMessage.error('标记操作失败: ' + (error.response?.data?.detail || error.message));
  }
}

// 导出已标记的问题
async function exportMarkedProblems() {
  if (markedProblems.value.size === 0) {
    ElMessage.warning('没有已标记的问题')
    return
  }
  
  exporting.value = true
  
  try {
    // 从后端获取所有已标记的问题
    const response = await axios.get(`/api/codeReview/${taskId.value}/marked_problems`, {
      params: { analysis_type: 'function' }
    });
    
    const markedProblemsArray = response.data.data.map(item => item.problem_data);
    
    if (markedProblemsArray.length === 0) {
      ElMessage.warning('未找到已标记问题的详情')
      return
    }
    
    // 调用后端API生成Excel
    const exportResponse = await axios.post(
      `/api/codeReview/export_marked_problems/${taskId.value}`,
      {
        analysis_type: 'function',
        problems: markedProblemsArray
      },
      { responseType: 'blob' }
    )
    
    // 创建下载链接
    const blob = new Blob([exportResponse.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `marked_problems_task_${taskId.value}_${new Date().getTime()}.xlsx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('已标记问题导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    exporting.value = false
  }
}

// 查看标记的问题
function viewMarkedProblems() {
  emit('viewMarkedProblems', markedProblems.value);
}

// 从后端加载标记状态
async function loadMarkedProblems() {
  if (!taskId.value) return;
  
  try {
    loading.value = true;
    const response = await axios.get(`/api/codeReview/${taskId.value}/marked_problems`, {
      params: { analysis_type: 'function' }
    });
    
    if (response.data.success) {
      const keys = response.data.data.map(item => item.problem_key);
      markedProblems.value = new Set(keys);
    }
  } catch (error) {
    console.error('加载标记问题失败:', error);
  } finally {
    loading.value = false;
  }
}

// 监听任务ID变化，重新加载标记状态
watch(
  () => taskId.value,
  (newTaskId) => {
    if (newTaskId) {
      loadMarkedProblems();
      loadFeedbackStatus();
    }
  },
  { immediate: true }
);

// 监听选中节点变化，当点击函数节点时增加计数
watch(
  () => props.selectedNode,
  async (newNode, oldNode) => {
    // 只在函数节点且是新节点时触发
    if (newNode && newNode.type === 'function' && newNode.id !== oldNode?.id) {
      await incrementClickedFunction();
    }
  }
);

// 加载反馈状态
async function loadFeedbackStatus() {
  if (!taskId.value) return;
  
  try {
    const response = await axios.get(`/api/codeReview/${taskId.value}/comment_accuracy_status`);
    if (response.data.success) {
      feedbackStatus.value = response.data.data;
    }
  } catch (error) {
    console.error('加载反馈状态失败:', error);
  }
}

// 增加点击函数计数
async function incrementClickedFunction() {
  if (!taskId.value || feedbackStatus.value.hasFeedback) return;
  
  try {
    const totalOverride = treeFunctionCount.value > 0 ? treeFunctionCount.value : undefined
    const body = totalOverride ? { total_override: totalOverride } : {}
    const response = await axios.post(`/api/codeReview/${taskId.value}/increment_clicked_function`, body);
    if (response.data.success) {
      const data = response.data.data;
      feedbackStatus.value.clickedCount = data.clicked_count;
      feedbackStatus.value.totalFunctions = data.total_functions;
      feedbackStatus.value.delayedCount = data.delayed_count;
      
      // 如果需要显示反馈框
      if (data.should_show_feedback && !data.already_feedback) {
        feedbackTriggerPoint.value = data.feedback_trigger_point || '50%';
        showFeedbackDialog.value = true;
      }
    }
  } catch (error) {
    console.error('增加点击计数失败:', error);
  }
}

// 处理反馈提交
function handleFeedbackSubmitted(rate) {
  feedbackStatus.value.hasFeedback = true;
  ElMessage.success('感谢您的反馈！');
}

// 处理延迟反馈
function handleFeedbackDelayed(data) {
  feedbackStatus.value.delayedCount = data.delayed_count;
  const nextTrigger = data.next_trigger;
  if (nextTrigger) {
    ElMessage.info(`已延迟反馈，将在${nextTrigger}时再次提醒`);
  }
}
</script>

<style scoped>
.sidebar {
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-left: 1px solid rgba(255, 255, 255, 0.2);
  display: flex;
  flex-direction: column;
  box-shadow: -2px 0 20px rgba(0, 0, 0, 0.1);
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.8);
  margin: 0;
  box-sizing: border-box;
  flex-wrap: wrap;
  gap: 10px;
}

.sidebar-header h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 18px;
  font-weight: 600;
  flex: 1;
  min-width: 120px;
}

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  margin: 0;
  box-sizing: border-box;
}

.stats-panel {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.stat-item {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
  border-radius: 12px;
  text-align: center;
  color: white;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.stat-number {
  font-size: 28px;
  font-weight: bold;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
}

.color-legend {
  background: rgba(255, 255, 255, 0.8);
  padding: 20px;
  border-radius: 12px;
  border: 1px solid #eee;
}

.color-legend h4 {
  margin: 0 0 15px 0;
  color: #2c3e50;
  font-size: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.legend-color {
  width: 20px;
  height: 20px;
  border-radius: 4px;
}

.file-color {
  background-color: #3498db;
}

.function-color {
  background-color: #2ecc71;
}

.fpga-file-color {
  background-color: #9b59b6;
}

.fpga-module-color {
  background-color: #e67e22;
}

.problem-color {
  background-color: #e74c3c;
}

.node-details {
  background: rgba(255, 255, 255, 0.8);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #eee;
}

.node-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.node-header h4 {
  margin: 0;
  color: #2c3e50;
  font-size: 18px;
}

.node-info {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.function-description-section {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  padding: 15px;
  border-radius: 8px;
  border: 1px solid #e9ecef;
  margin-bottom: 20px;
}

.function-description-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.description-text {
  font-size: 14px;
  color: #333;
  line-height: 1.6;
  word-break: break-word;
}

.no-description-section {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  padding: 15px;
  border-radius: 8px;
  border: 1px solid #e9ecef;
  margin-bottom: 20px;
}

.no-description-content {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
}

.file-basic-info {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  padding: 15px;
  border-radius: 8px;
  border: 1px solid #e9ecef;
  margin-bottom: 20px;
}

.file-basic-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-label {
  font-size: 13px;
  color: #888;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-value {
  font-size: 14px;
  color: #333;
  font-weight: 400;
  text-align: right;
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
  transition: all 0.3s ease;
}

/* 问题状态样式 */
.problem-block.status-new {
  background: #f0fdf4;
  border-left-color: #22c55e;
}

.problem-block.status-viewed,
.problem-block.status-filtered {
  background: #f5f5f5;
  border-left-color: #9ca3af;
  opacity: 0.8;
}

.problem-block.status-marked {
  background: #eff6ff;
  border-left-color: #3b82f6;
}

/* 状态指示器 */
.problem-status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.indicator-green {
  background-color: #22c55e;
  box-shadow: 0 0 6px rgba(34, 197, 94, 0.5);
}

.indicator-gray {
  background-color: #9ca3af;
}

.indicator-marked {
  background-color: #3b82f6;
  box-shadow: 0 0 6px rgba(59, 130, 246, 0.5);
}

.status-tag {
  margin-left: 6px;
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

.location-problem-field .field-value {
  line-height: 1.5;
}

.source-program-section {
  margin-top: 8px;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  overflow: hidden;
  background: #1f2937;
}

.source-program-title {
  padding: 6px 10px;
  background: #374151;
  color: #e5e7eb;
  font-size: 12px;
  font-weight: 600;
  border-bottom: 1px solid #4b5563;
}

.source-program-code {
  margin: 0;
  padding: 12px;
  max-height: 360px;
  overflow: auto;
  color: #e5e7eb;
  background: #111827;
  font-size: 12px;
  line-height: 1.6;
  font-family: Consolas, Monaco, 'Courier New', monospace;
  white-space: pre;
  tab-size: 4;
}

.collapse-icon {
  transition: transform 0.3s ease;
  cursor: pointer;
}

.collapse-icon.collapsed {
  transform: rotate(-90deg);
}

.search-results {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.search-result-item {
  background: rgba(255, 255, 255, 0.8);
  padding: 15px;
  border-radius: 8px;
  cursor: pointer;
  border: 1px solid #eee;
  transition: all 0.3s ease;
}

.search-result-item:hover {
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.result-name {
  font-weight: 600;
  color: #2c3e50;
}

.result-details p {
  margin: 5px 0;
  color: #666;
  font-size: 14px;
}

.no-results {
  text-align: center;
  color: #999;
  padding: 40px 20px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .sidebar {
    width: 350px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .sidebar {
    width: 100%;
    position: absolute;
    z-index: 100;
  }
}
</style> 