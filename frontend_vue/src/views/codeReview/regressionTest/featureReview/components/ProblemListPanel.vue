<template>
  <div class="problem-list-panel">
    <div class="panel-header">
      <h3>问题单</h3>
      <div v-if="selectedFeature" class="header-info">
        <el-tag type="warning" size="small">
          {{ problems.length }} 个问题
        </el-tag>
        <el-button
          v-if="hasMarked"
          type="primary"
          size="small"
          @click="$emit('export-marked')"
        >
          <el-icon><Download /></el-icon>
          导出已标记
        </el-button>
      </div>
    </div>

    <div class="panel-content">
      <div v-if="!selectedFeature" class="empty-state">
        <el-empty description="请选择一个功能" />
      </div>

      <div v-else-if="problems.length === 0" class="empty-state">
        <el-empty description="暂无问题" />
      </div>

      <div v-else class="problems-list">
        <div
          v-for="(problem, index) in problems"
          :key="problemKey(problem, index)"
          class="problem-item"
          :class="{ marked: isMarked(problem, index) }"
          @click="$emit('problem-select', problem)"
        >
          <div class="problem-header" @click.stop="toggleProblem(index)">
            <div class="problem-title-left">
              <el-icon><Warning /></el-icon>
              <span class="problem-number">问题 {{ index + 1 }}</span>
              <el-tag
                v-if="problem.issue_level"
                :type="getIssueLevelTagType(problem.issue_level)"
                size="small"
              >
                {{ problem.issue_level }}
              </el-tag>
            </div>
            <div class="problem-title-right">
              <el-button
                type="primary"
                size="small"
                text
                @click.stop="$emit('problem-select', problem)"
              >
                <el-icon><Position /></el-icon>
                定位
              </el-button>
              <el-button
                class="mark-btn"
                size="small"
                :type="isMarked(problem, index) ? 'success' : 'info'"
                @click.stop="toggleMark(problem, index)"
              >
                <el-icon><Check /></el-icon>
                {{ isMarked(problem, index) ? '已标记' : '标记' }}
              </el-button>
              <el-icon
                class="collapse-icon"
                :class="{ 'collapsed': !expandedProblems.has(index) }"
              >
                <ArrowDown />
              </el-icon>
            </div>
          </div>

          <el-collapse-transition>
            <div v-show="expandedProblems.has(index)" class="problem-content">
              <div v-if="problem.issue_name" class="problem-field">
                <div class="field-label">问题名称</div>
                <div class="field-value">{{ problem.issue_name }}</div>
              </div>
              <div v-if="problem.issue_location" class="problem-field">
                <div class="field-label">问题位置</div>
                <div class="field-value">{{ problem.issue_location }}</div>
              </div>
              <div v-if="problem.file_name" class="problem-field">
                <div class="field-label">文件名称</div>
                <div class="field-value">{{ problem.file_name }}</div>
              </div>
              <div v-if="problem.function_name" class="problem-field">
                <div class="field-label">函数名称</div>
                <div class="field-value">{{ problem.function_name }}</div>
              </div>
              <div v-if="problem.problem_reason" class="problem-field">
                <div class="field-label">问题原因</div>
                <div class="field-value">{{ problem.problem_reason }}</div>
              </div>
              <div v-if="problem.description_requirement" class="problem-field">
                <div class="field-label">功能需求</div>
                <div class="field-value">{{ problem.description_requirement }}</div>
              </div>
              <div v-if="problem.description_issue" class="problem-field">
                <div class="field-label">问题描述</div>
                <div class="field-value">{{ problem.description_issue }}</div>
              </div>
              <div v-if="problem.description_location" class="problem-field">
                <div class="field-label">位置描述</div>
                <div class="field-value">{{ problem.description_location }}</div>
              </div>
              <div v-if="problem.description_impact" class="problem-field">
                <div class="field-label">影响描述</div>
                <div class="field-value">{{ problem.description_impact }}</div>
              </div>
              <div v-if="problem.business_rule" class="problem-field">
                <div class="field-label">违反的业务规则</div>
                <div class="field-value">{{ problem.business_rule }}</div>
              </div>
              <div v-if="problem.suggestion" class="problem-field">
                <div class="field-label">改进建议</div>
                <div class="field-value">{{ problem.suggestion }}</div>
              </div>
              <div v-if="problem.source_code" class="problem-field">
                <div class="field-label">相关代码</div>
                <pre class="source-code">{{ problem.source_code }}</pre>
              </div>
            </div>
          </el-collapse-transition>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { Warning, Position, ArrowDown, Check, Download } from '@element-plus/icons-vue';
import { ElCollapseTransition } from 'element-plus';

const props = defineProps({
  selectedFeature: {
    type: Object,
    default: null
  },
  problems: {
    type: Array,
    default: () => []
  },
  markedSet: {
    type: Object,
    default: () => new Set()
  }
});

const emit = defineEmits(['problem-select', 'toggle-mark', 'export-marked']);

const expandedProblems = ref(new Set());

const hasMarked = computed(() => props.markedSet && props.markedSet.size > 0);

function toggleProblem(index) {
  if (expandedProblems.value.has(index)) {
    expandedProblems.value.delete(index);
  } else {
    expandedProblems.value.add(index);
  }
}

function getIssueLevelTagType(level) {
  const typeMap = {
    '重要问题': 'danger',
    '一般问题': 'warning',
    '建议改进': 'info'
  };
  return typeMap[level] || 'info';
}

function problemKey(problem, index) {
  if (problem.key) return problem.key;
  return (
    problem.id ||
    `${problem.issue_name || ''}-${problem.file_name || ''}-${problem.function_name || ''}-${problem.description_location || ''}-${index}`
  );
}

function isMarked(problem, index) {
  if (!props.markedSet) return false;
  return props.markedSet.has(problemKey(problem, index));
}

function toggleMark(problem, index) {
  emit('toggle-mark', { problem, key: problemKey(problem, index) });
}
</script>

<style scoped>
.problem-list-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.panel-header {
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.header-info {
  margin-left: 12px;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #909399;
}

.problems-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.problem-item {
  border: 1px solid #fecaca;
  border-radius: 8px;
  padding: 12px;
  background: #fef2f2;
  transition: all 0.3s ease;
  cursor: pointer;
}

.problem-item:hover {
  box-shadow: 0 2px 12px rgba(239, 68, 68, 0.15);
}

.problem-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
}

.problem-title-left {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #e74c3c;
  font-weight: 600;
}

.problem-title-left .el-icon {
  color: #e74c3c;
}

.problem-number {
  font-size: 14px;
}

.problem-title-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.collapse-icon {
  transition: transform 0.3s ease;
  cursor: pointer;
}

.collapse-icon.collapsed {
  transform: rotate(-90deg);
}

.problem-content {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #fecaca;
}

.problem-field {
  margin-bottom: 12px;
}

.problem-field:last-child {
  margin-bottom: 0;
}

.field-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.field-value {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  word-break: break-word;
}

.source-code {
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 12px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.5;
  overflow-x: auto;
  margin: 8px 0 0 0;
}
</style>

