<template>
  <el-dialog
    v-model="dialogVisible"
    :title="panelTitle"
    width="960px"
    top="5vh"
    :close-on-click-modal="false"
    destroy-on-close
    @closed="handleClosed"
  >
    <!-- 步骤一：确认范围与提示词 -->
    <div v-if="step === 'config'" class="batch-config">
      <div class="scope-bar">
        <el-icon><Collection /></el-icon>
        <span class="scope-label">{{ scope?.label || '批量修复' }}</span>
        <el-tag type="danger" size="small" effect="plain">共 {{ allCandidates.length }} 个问题</el-tag>
        <el-tag type="primary" size="small" effect="plain">已勾选 {{ checkedIds.length }} 个</el-tag>
      </div>

      <div class="candidate-list">
        <div
          v-for="item in allCandidates"
          :key="item.id"
          class="candidate-item"
        >
          <el-checkbox
            :model-value="checkedIds.includes(item.id)"
            @change="(val) => toggleCandidate(item.id, val)"
          />
          <el-tag :type="item.rule_type === 'cwe' ? 'success' : 'primary'" size="small">
            {{ item.rule_code }}
          </el-tag>
          <span class="candidate-name">{{ item.problem_sheet?.issue_name || item.issue_name }}</span>
          <span class="candidate-loc">{{ item.issue_file }}:{{ item.issue_line }}</span>
        </div>
      </div>

      <div class="field-block">
        <div class="field-label">统一修复提示词（可选）</div>
        <el-input
          v-model="userPrompt"
          type="textarea"
          :rows="3"
          maxlength="1000"
          show-word-limit
          placeholder="对所有选中问题统一生效的修复要求，例如：只做最小改动、统一使用 NULL、保持缩进风格。"
        />
        <div class="quick-tags">
          <el-tag
            v-for="tag in quickTags"
            :key="tag"
            class="quick-tag"
            effect="plain"
            @click="appendTag(tag)"
          >
            {{ tag }}
          </el-tag>
        </div>
      </div>

      <div class="options-row">
        <span class="tags-label">并发数：</span>
        <el-select v-model="options.concurrency" size="small" style="width: 90px;">
          <el-option :value="1" label="1" />
          <el-option :value="2" label="2" />
          <el-option :value="3" label="3" />
          <el-option :value="5" label="5" />
        </el-select>
        <el-checkbox v-model="options.keep_style">保持原有代码风格</el-checkbox>
        <el-checkbox v-model="options.add_comment">补充中文注释</el-checkbox>
      </div>
    </div>

    <!-- 步骤二：生成中 -->
    <div v-else-if="step === 'generating'" class="batch-generating">
      <el-progress
        :percentage="progress.progress || 0"
        :status="progress.status === 'done' ? 'success' : undefined"
        :stroke-width="16"
        text-inside
      />
      <div class="progress-detail">
        <el-tag type="success" size="small">成功 {{ progress.succeeded || 0 }}</el-tag>
        <el-tag type="warning" size="small">冲突 {{ progress.conflicted || 0 }}</el-tag>
        <el-tag type="danger" size="small">失败 {{ progress.failed || 0 }}</el-tag>
        <span class="progress-total">/ 共 {{ progress.total || 0 }}</span>
      </div>
      <div class="generating-tip">
        <el-icon class="is-loading"><Loading /></el-icon>
        AI 正在按文件并发分析，请稍候…
      </div>
    </div>

    <!-- 步骤三：结果汇总 -->
    <div v-else class="batch-result">
      <div class="result-summary">
        <el-tag type="success" size="small" effect="dark">成功 {{ summary.succeeded }}</el-tag>
        <el-tag type="warning" size="small" effect="dark">冲突 {{ summary.conflicted }}</el-tag>
        <el-tag type="danger" size="small" effect="dark">失败 {{ summary.failed }}</el-tag>
        <div class="summary-actions">
          <el-button size="small" @click="selectAllGenerated">全选可应用</el-button>
          <el-button size="small" type="primary" :loading="applying" @click="applySelected">
            应用选中 ({{ applicableSelected.length }})
          </el-button>
          <el-button size="small" type="success" :loading="applying" @click="applyAll">全部应用</el-button>
        </div>
      </div>

      <div class="result-list">
        <div
          v-for="item in items"
          :key="item.id"
          class="result-item"
          :class="`status-${item.status}`"
        >
          <div class="result-head" @click="toggleExpand(item.id)">
            <el-checkbox
              v-if="item.status === 'generated'"
              :model-value="selectedFixIds.includes(item.id)"
              @click.stop
              @change="(val) => toggleFix(item.id, val)"
            />
            <span v-else class="checkbox-placeholder"></span>
            <el-tag :size="'small'" :type="statusTagType(item.status)">{{ statusLabel(item.status) }}</el-tag>
            <el-tag :type="item.rule_type === 'cwe' ? 'success' : 'primary'" size="small">
              {{ item.rule_code }}
            </el-tag>
            <span class="result-name">{{ item.issue_name }}</span>
            <span class="result-loc">{{ item.file_path }}:{{ item.line_no || item.issue_line }}</span>
            <el-tag v-if="item.confidence !== null" size="small" effect="plain">
              {{ Math.round((item.confidence || 0) * 100) }}%
            </el-tag>
            <el-icon class="expand-icon" :class="{ expanded: expandedIds.includes(item.id) }">
              <ArrowDown />
            </el-icon>
          </div>
          <div v-if="expandedIds.includes(item.id)" class="result-detail">
            <FixDiffViewer
              :diff-text="item.diff_text"
              :explanation="item.ai_explanation"
              :confidence="item.confidence"
              :status="item.status"
              :error-message="item.error_message"
              :applied="item.status === 'applied'"
            />
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <div class="footer-actions">
          <el-button v-if="step === 'config'" @click="dialogVisible = false">取消</el-button>
          <el-button v-if="step === 'config'" type="primary" :disabled="checkedIds.length === 0" @click="startGenerate">
            开始生成 ({{ checkedIds.length }})
          </el-button>
          <el-button v-else-if="step === 'result'" @click="dialogVisible = false">关闭</el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, onUnmounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Collection, Loading, ArrowDown } from '@element-plus/icons-vue'
import FixDiffViewer from './FixDiffViewer.vue'
import staticAnalysisFixService from '@/services/staticAnalysisFixService'

const props = defineProps({
  visible: { type: Boolean, default: false },
  taskId: { type: String, required: true },
  scope: { type: Object, default: null },      // { type: 'file'|'rule', value, label }
  candidates: { type: Array, default: () => [] }
})

const emit = defineEmits(['update:visible', 'applied'])

const quickTags = ['最小改动', '保持代码风格', '统一使用 NULL', '补充注释']

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

const panelTitle = computed(() =>
  props.scope?.type === 'rule' ? '按规则批量修复' : '按文件批量修复'
)

const allCandidates = computed(() => props.candidates || [])

const step = ref('config')
const userPrompt = ref('')
const options = ref({ concurrency: 3, keep_style: true, add_comment: false })
const checkedIds = ref([])

const fixTaskId = ref(null)
const progress = ref({ progress: 0, total: 0, succeeded: 0, failed: 0, conflicted: 0, status: 'pending' })
const items = ref([])
const selectedFixIds = ref([])
const expandedIds = ref([])
const applying = ref(false)

let pollTimer = null

watch(() => props.visible, (val) => {
  if (val) {
    step.value = 'config'
    userPrompt.value = ''
    fixTaskId.value = null
    items.value = []
    selectedFixIds.value = []
    expandedIds.value = []
    checkedIds.value = (props.candidates || []).map(p => p.id)
    progress.value = { progress: 0, total: 0, succeeded: 0, failed: 0, conflicted: 0, status: 'pending' }
  } else {
    stopPolling()
  }
})

onUnmounted(stopPolling)

const summary = computed(() => {
  const s = { succeeded: 0, conflicted: 0, failed: 0 }
  items.value.forEach(item => {
    if (item.status === 'generated' || item.status === 'applied') s.succeeded++
    else if (item.status === 'conflict') s.conflicted++
    else s.failed++
  })
  return s
})

const applicableSelected = computed(() =>
  items.value.filter(item => selectedFixIds.value.includes(item.id) && item.status === 'generated')
)

function toggleCandidate(id, checked) {
  const set = new Set(checkedIds.value)
  if (checked) set.add(id)
  else set.delete(id)
  checkedIds.value = Array.from(set)
}

function appendTag(tag) {
  const text = userPrompt.value.trim()
  userPrompt.value = text ? `${text}；${tag}` : tag
}

async function startGenerate() {
  if (!checkedIds.value.length) {
    ElMessage.warning('请至少选择一个要修复的问题')
    return
  }
  try {
    const res = await staticAnalysisFixService.generate(props.taskId, {
      scope: { type: props.scope?.type || 'file', value: props.scope?.value },
      problem_ids: checkedIds.value,
      user_prompt: userPrompt.value,
      options: options.value
    })
    if (!res?.success) {
      ElMessage.error(res?.message || '创建修复任务失败')
      return
    }
    fixTaskId.value = res.fix_task_id
    step.value = 'generating'
    progress.value = { ...progress.value, total: res.total || checkedIds.value.length }
    startPolling()
  } catch (error) {
    ElMessage.error(error.message || '创建修复任务失败')
  }
}

function startPolling() {
  stopPolling()
  pollTimer = setInterval(pollStatus, 2500)
  pollStatus()
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

async function pollStatus() {
  if (!fixTaskId.value) return
  try {
    const res = await staticAnalysisFixService.getStatus(props.taskId, fixTaskId.value)
    if (res?.success) {
      progress.value = res.data
      if (['done', 'partial', 'error'].includes(res.data.status)) {
        stopPolling()
        await loadItems()
        step.value = 'result'
        selectedFixIds.value = items.value.filter(i => i.status === 'generated').map(i => i.id)
        if (items.value.length) expandedIds.value = [items.value[0].id]
      }
    }
  } catch (error) {
    console.error('[批量修复] 轮询失败:', error)
  }
}

async function loadItems() {
  const res = await staticAnalysisFixService.listFixes(props.taskId, fixTaskId.value)
  items.value = res?.data?.items || []
}

function statusLabel(status) {
  return {
    generated: '待应用',
    applied: '已应用',
    conflict: '冲突',
    failed: '失败',
    rejected: '已忽略',
    rolled_back: '已回滚'
  }[status] || status
}

function statusTagType(status) {
  return {
    generated: 'primary',
    applied: 'success',
    conflict: 'warning',
    failed: 'danger'
  }[status] || 'info'
}

function toggleFix(id, checked) {
  const set = new Set(selectedFixIds.value)
  if (checked) set.add(id)
  else set.delete(id)
  selectedFixIds.value = Array.from(set)
}

function toggleExpand(id) {
  const set = new Set(expandedIds.value)
  if (set.has(id)) set.delete(id)
  else set.add(id)
  expandedIds.value = Array.from(set)
}

function selectAllGenerated() {
  selectedFixIds.value = items.value.filter(i => i.status === 'generated').map(i => i.id)
}

async function applyFixIds(ids) {
  if (!ids.length) {
    ElMessage.warning('没有可应用的修复')
    return
  }
  applying.value = true
  try {
    const res = await staticAnalysisFixService.apply(props.taskId, ids)
    const applied = res?.data?.applied || []
    const conflicted = res?.data?.conflicted || []
    await loadItems()
    selectedFixIds.value = items.value.filter(i => i.status === 'generated').map(i => i.id)
    if (applied.length) {
      ElMessage.success(`已应用 ${applied.length} 条修复${conflicted.length ? `，${conflicted.length} 条冲突需人工处理` : ''}`)
      emit('applied', { fixIds: applied.map(a => a.fix_id), applied })
    } else if (conflicted.length) {
      ElMessage.error('应用失败：' + (conflicted[0].reason || '存在冲突'))
    } else {
      ElMessage.error(res?.message || '应用失败')
    }
  } catch (error) {
    ElMessage.error(error.message || '应用失败')
  } finally {
    applying.value = false
  }
}

function applySelected() {
  applyFixIds(applicableSelected.value.map(i => i.id))
}

function applyAll() {
  applyFixIds(items.value.filter(i => i.status === 'generated').map(i => i.id))
}

function handleClosed() {
  stopPolling()
}
</script>

<style scoped>
.scope-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: #f1f5f9;
  border-radius: 8px;
  margin-bottom: 12px;
}

.scope-label {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.candidate-list {
  max-height: 220px;
  overflow: auto;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 6px 10px;
  margin-bottom: 14px;
}

.candidate-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 2px;
  font-size: 13px;
  border-bottom: 1px dashed #f0f0f0;
}

.candidate-item:last-child {
  border-bottom: none;
}

.candidate-name {
  color: #374151;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.candidate-loc {
  color: #909399;
  font-size: 12px;
  flex-shrink: 0;
}

.field-block {
  margin-bottom: 12px;
}

.field-label {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
}

.quick-tags {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  flex-wrap: wrap;
}

.quick-tag {
  cursor: pointer;
}

.options-row {
  display: flex;
  align-items: center;
  gap: 16px;
}

.tags-label {
  font-size: 12px;
  color: #909399;
}

.batch-generating {
  padding: 20px 4px;
}

.progress-detail {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 16px;
}

.progress-total {
  font-size: 13px;
  color: #909399;
}

.generating-tip {
  margin-top: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #606266;
  font-size: 13px;
}

.result-summary {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.summary-actions {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.result-list {
  max-height: 460px;
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.result-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
}

.result-item.status-generated {
  border-left: 3px solid #3b82f6;
}

.result-item.status-applied {
  border-left: 3px solid #10b981;
}

.result-item.status-conflict {
  border-left: 3px solid #f59e0b;
}

.result-item.status-failed {
  border-left: 3px solid #ef4444;
}

.result-head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  cursor: pointer;
  background: #fafafa;
  font-size: 13px;
}

.result-head:hover {
  background: #f5f5f5;
}

.checkbox-placeholder {
  width: 14px;
  flex-shrink: 0;
}

.result-name {
  color: #374151;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-loc {
  color: #909399;
  font-size: 12px;
  flex-shrink: 0;
}

.expand-icon {
  transition: transform 0.2s ease;
  color: #909399;
}

.expand-icon.expanded {
  transform: rotate(180deg);
}

.result-detail {
  padding: 12px;
  background: #fff;
  border-top: 1px solid #f0f0f0;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
}

.footer-actions {
  display: flex;
  gap: 10px;
}
</style>
