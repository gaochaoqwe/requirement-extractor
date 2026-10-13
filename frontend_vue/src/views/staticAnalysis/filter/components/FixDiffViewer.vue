<template>
  <div class="fix-diff-viewer">
    <div v-if="status === 'conflict'" class="diff-alert conflict">
      <el-icon><WarningFilled /></el-icon>
      <div>
        <div class="alert-title">无法唯一定位，未生成补丁</div>
        <div class="alert-desc">{{ errorMessage || '原文片段在文件中匹配到多处或已被修改' }}</div>
      </div>
    </div>

    <div v-else-if="status === 'failed'" class="diff-alert failed">
      <el-icon><CircleCloseFilled /></el-icon>
      <div>
        <div class="alert-title">生成失败</div>
        <div class="alert-desc">{{ errorMessage || 'AI 未能给出修复方案' }}</div>
      </div>
    </div>

    <template v-else>
      <div class="diff-meta">
        <el-tag :type="confidenceTagType" size="small" effect="dark">
          置信度 {{ confidenceText }}
        </el-tag>
        <el-tag v-if="applied" type="success" size="small" effect="dark">已应用</el-tag>
        <span class="meta-explain">{{ explanation || 'AI 未提供说明' }}</span>
      </div>

      <div class="diff-body">
        <div class="diff-code">
          <div
            v-for="(line, index) in diffLines"
            :key="index"
            class="diff-line"
            :class="lineClass(line)"
          >
            <span class="diff-sign">{{ lineSign(line) }}</span>
            <span class="diff-text">{{ lineDisplay(line) }}</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { WarningFilled, CircleCloseFilled } from '@element-plus/icons-vue'

const props = defineProps({
  diffText: { type: String, default: '' },
  explanation: { type: String, default: '' },
  confidence: { type: Number, default: null },
  status: { type: String, default: 'generated' },
  errorMessage: { type: String, default: '' },
  applied: { type: Boolean, default: false }
})

const diffLines = computed(() => {
  const text = props.diffText || ''
  if (!text) return []
  return text.replace(/\r/g, '').split('\n')
})

const confidenceText = computed(() => {
  if (props.confidence === null || props.confidence === undefined) return '未知'
  return `${Math.round(props.confidence * 100)}%`
})

const confidenceTagType = computed(() => {
  const c = props.confidence
  if (c === null || c === undefined) return 'info'
  if (c >= 0.85) return 'success'
  if (c >= 0.6) return 'warning'
  return 'danger'
})

function lineClass(line) {
  if (line.startsWith('+++') || line.startsWith('---')) return 'diff-file-header'
  if (line.startsWith('@@')) return 'diff-hunk'
  if (line.startsWith('+')) return 'diff-add'
  if (line.startsWith('-')) return 'diff-del'
  return 'diff-context'
}

function lineSign(line) {
  if (line.startsWith('+++') || line.startsWith('---') || line.startsWith('@@')) return ''
  if (line.startsWith('+') || line.startsWith('-')) return line.charAt(0)
  return ' '
}

function lineDisplay(line) {
  if (line.startsWith('+++') || line.startsWith('---') || line.startsWith('@@')) return line
  if (line.startsWith('+') || line.startsWith('-')) return line.slice(1)
  return line
}
</script>

<style scoped>
.fix-diff-viewer {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.diff-alert {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.6;
}

.diff-alert.conflict {
  background: #fffbeb;
  border: 1px solid #fcd34d;
  color: #92400e;
}

.diff-alert.failed {
  background: #fef2f2;
  border: 1px solid #fca5a5;
  color: #991b1b;
}

.alert-title {
  font-weight: 600;
  margin-bottom: 2px;
}

.diff-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.meta-explain {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  flex: 1;
  min-width: 200px;
}

.diff-body {
  max-height: 420px;
  overflow: auto;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.diff-code {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 12.5px;
  line-height: 1.7;
  background: #fafafa;
}

.diff-line {
  display: flex;
  align-items: flex-start;
  white-space: pre;
  padding: 0 8px;
}

.diff-sign {
  width: 14px;
  flex-shrink: 0;
  text-align: center;
  color: #909399;
  user-select: none;
}

.diff-text {
  flex: 1;
  word-break: break-all;
  white-space: pre-wrap;
}

.diff-add {
  background: #dcfce7;
  border-left: 3px solid #22c55e;
}

.diff-add .diff-sign {
  color: #16a34a;
  font-weight: 700;
}

.diff-del {
  background: #fee2e2;
  border-left: 3px solid #ef4444;
}

.diff-del .diff-sign {
  color: #dc2626;
  font-weight: 700;
}

.diff-hunk {
  background: #eff6ff;
  color: #2563eb;
  border-left: 3px solid #93c5fd;
}

.diff-file-header {
  background: #f3f4f6;
  color: #6b7280;
  border-left: 3px solid #d1d5db;
}

.diff-context {
  color: #4b5563;
}
</style>
