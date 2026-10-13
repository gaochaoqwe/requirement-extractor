<template>
  <div class="sidebar">
    <div class="sidebar-header">
      <h3>{{ title }}</h3>
      <el-button @click="$emit('close')" :icon="Close" size="small" text />
    </div>
    
    <div class="sidebar-content">
      <!-- 文件问题列表 -->
      <div v-if="mode === 'problems'" class="problems-panel">
        <!-- 文件功能概述 -->
        <div v-if="selectedNode && selectedNode.file_function_summary" class="file-summary-section">
          <div class="section-title">
            <el-icon><Document /></el-icon>
            <span>文件功能概述</span>
          </div>
          <div class="file-summary-content">
            <div class="summary-text">{{ selectedNode.file_function_summary }}</div>
          </div>
        </div>
        
        <div v-if="selectedNode && selectedNode.problems && selectedNode.problems.length > 0" class="problems-section">
          <div class="section-title">
            <el-icon><Warning /></el-icon>
            <span>文件问题</span>
            <el-tag type="danger" size="small">{{ selectedNode.problems.length }} 个问题</el-tag>
          </div>
          
          <div class="problems-list">
            <div 
              v-for="(problem, index) in selectedNode.problems" 
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
                  <!-- 文件名称 -->
                  <div v-if="problem.file_name" class="problem-field">
                    <div class="field-label">文件名称</div>
                    <div class="field-value">{{ problem.file_name }}</div>
                  </div>
                  
                  <!-- 文件功能概述 -->
                  <div v-if="problem.file_function_summary" class="problem-field">
                    <div class="field-label">文件功能</div>
                    <div class="field-value">{{ problem.file_function_summary }}</div>
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
                  
                  <!-- 影响描述 -->
                  <div v-if="problem.description_impact" class="problem-field">
                    <div class="field-label">影响描述</div>
                    <div class="field-value">{{ problem.description_impact }}</div>
                  </div>
                </div>
              </el-collapse-transition>
            </div>
          </div>
        </div>
        
        <div v-else class="no-problems">
          <el-icon><InfoFilled /></el-icon>
          <span>此文件暂无发现问题</span>
        </div>
      </div>

      <!-- 统计信息 -->
      <div v-else-if="mode === 'stats'" class="stats-panel">
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
            </div>
            
            <div class="problems-list">
              <div 
                v-for="(problem, index) in selectedNode.problems" 
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
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Close, Warning, Document, Edit, ArrowDown, InfoFilled } from '@element-plus/icons-vue'
import { ElCollapseTransition } from 'element-plus'

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
  }
})

// Emits
const emit = defineEmits(['close', 'highlightNode', 'highlightProblem'])

// 响应式数据
const collapsedProblems = ref(new Set())

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

function toggleProblem(index) {
  if (collapsedProblems.value.has(index)) {
    collapsedProblems.value.delete(index)
  } else {
    collapsedProblems.value.add(index)
  }
}

function highlightProblemInCode(problem, problemIndex) {
  // 发送事件到父组件，传递问题信息用于在代码中高亮显示
  emit('highlightProblem', {
    problem,
    problemIndex,
    nodeInfo: props.selectedNode
  })
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
}

.sidebar-header h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 18px;
  font-weight: 600;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  margin: 0;
  box-sizing: border-box;
}

.problems-panel {
  padding: 0;
}

.file-summary-section {
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
  padding: 20px;
  border-radius: 12px;
  border: 1px solid #90caf9;
  margin-bottom: 20px;
}

.file-summary-section .section-title {
  color: #1976d2;
  border-bottom: 2px solid #90caf9;
  margin-bottom: 15px;
}

.file-summary-section .section-title .el-icon {
  color: #1976d2;
}

.file-summary-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.summary-text {
  font-size: 14px;
  color: #37474f;
  line-height: 1.8;
  word-break: break-word;
  background: rgba(255, 255, 255, 0.8);
  padding: 12px;
  border-radius: 8px;
  border-left: 4px solid #1976d2;
}

.no-problems {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 20px;
  color: #909399;
  font-size: 14px;
  justify-content: center;
  background: #f5f7fa;
  border-radius: 8px;
  margin-top: 20px;
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