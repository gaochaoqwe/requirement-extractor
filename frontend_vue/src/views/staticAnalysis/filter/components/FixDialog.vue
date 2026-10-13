<template>
  <el-dialog
    v-model="dialogVisible"
    title="AI 修复问题"
    width="880px"
    top="6vh"
    :close-on-click-modal="false"
    destroy-on-close
    @closed="handleClosed"
  >
    <!-- 问题摘要 -->
    <div class="problem-summary">
      <div class="summary-line">
        <el-tag :type="ruleType === 'cwe' ? 'success' : 'primary'" size="small">
          {{ problem?.rule_code || '未知规则' }}
        </el-tag>
        <span class="issue-name">{{ problem?.problem_sheet?.issue_name || problem?.issue_name || '未知问题' }}</span>
      </div>
      <div class="summary-loc">
        <el-icon><Location /></el-icon>
        {{ problem?.issue_file || '-' }} : {{ problem?.issue_line || '-' }}
      </div>
      <el-collapse v-if="problem?.problem_sheet?.four_part_description" class="summary-collapse">
        <el-collapse-item title="查看问题单详情（四段式）" name="detail">
          <pre class="four-part">{{ problem.problem_sheet.four_part_description }}</pre>
        </el-collapse-item>
      </el-collapse>
    </div>

    <!-- 步骤一：输入提示词 -->
    <div v-if="step === 'input'" class="fix-input">
      <div class="field-label">修复提示词（可选）</div>
      <el-input
        v-model="userPrompt"
        type="textarea"
        :rows="4"
        maxlength="1000"
        show-word-limit
        placeholder="告诉 AI 你希望怎么修复，例如：只做最小改动、保持原有代码风格、使用 NULL 而不是 0 等。留空则由 AI 依据规范自行判断。"
      />
      <div class="quick-tags">
        <span class="tags-label">快捷提示：</span>
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

      <div class="options-row">
        <el-checkbox v-model="options.keep_style">保持原有代码风格</el-checkbox>
        <el-checkbox v-model="options.add_comment">补充中文注释</el-checkbox>
        <el-checkbox v-model="options.only_near_line" disabled>只改问题行附近（固定）</el-checkbox>
      </div>
    </div>

    <!-- 步骤二：结果预览 -->
    <div v-else class="fix-result">
      <div v-if="loading" class="loading-box">
        <el-icon class="is-loading" :size="22"><Loading /></el-icon>
        <span>AI 正在分析函数上下文并生成修复方案…</span>
      </div>
      <FixDiffViewer
        v-else
        :diff-text="currentFix?.diff_text"
        :explanation="currentFix?.ai_explanation"
        :confidence="currentFix?.confidence"
        :status="currentFix?.status"
        :error-message="currentFix?.error_message"
        :applied="currentFix?.status === 'applied'"
      />
      <div v-if="!loading" class="result-prompt">
        <span class="tags-label">补充/修改提示词：</span>
        <el-input v-model="userPrompt" size="small" placeholder="可修改提示词后点「重新生成」" style="width: 380px;" />
        <el-button size="small" :loading="loading" @click="regenerate">重新生成</el-button>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <span v-if="loading" class="footer-tip">生成中请稍候…</span>
        <div class="footer-actions">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button v-if="step === 'input'" type="primary" :loading="loading" @click="generate">
            <el-icon><MagicStick /></el-icon>
            生成修复方案
          </el-button>
          <template v-else>
            <el-button
              v-if="canApply"
              type="primary"
              :loading="applying"
              @click="applyFix"
            >
              应用修复
            </el-button>
            <el-button v-if="currentFix?.status === 'generated'" @click="dialogVisible = false">放弃</el-button>
          </template>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Location, MagicStick, Loading } from '@element-plus/icons-vue'
import FixDiffViewer from './FixDiffViewer.vue'
import staticAnalysisFixService from '@/services/staticAnalysisFixService'

const props = defineProps({
  visible: { type: Boolean, default: false },
  problem: { type: Object, default: null },
  taskId: { type: String, required: true },
  ruleType: { type: String, default: 'gjb' }
})

const emit = defineEmits(['update:visible', 'applied'])

const quickTags = ['最小改动', '保持代码风格', '只加判空', '补充注释', '不要改变业务逻辑']

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

const step = ref('input')
const userPrompt = ref('')
const options = ref({ keep_style: true, add_comment: false, only_near_line: true })
const loading = ref(false)
const applying = ref(false)
const currentFix = ref(null)

watch(() => props.visible, (val) => {
  if (val) {
    step.value = 'input'
    userPrompt.value = ''
    currentFix.value = null
    loading.value = false
  }
})

const canApply = computed(() => currentFix.value && currentFix.value.status === 'generated')

function appendTag(tag) {
  const text = userPrompt.value.trim()
  userPrompt.value = text ? `${text}；${tag}` : tag
}

async function generate() {
  if (!props.problem?.id) {
    ElMessage.warning('缺少问题ID，无法修复')
    return
  }
  loading.value = true
  step.value = 'result'
  try {
    const res = await staticAnalysisFixService.generate(props.taskId, {
      scope: { type: 'single', value: String(props.problem.id) },
      user_prompt: userPrompt.value,
      options: options.value,
      rule_type: props.problem.rule_type || props.ruleType
    })
    if (res?.success && res.items?.length) {
      currentFix.value = res.items[0]
      if (currentFix.value.status === 'generated') {
        ElMessage.success('修复方案已生成，请确认后应用')
      } else {
        ElMessage.warning(currentFix.value.error_message || '生成失败')
      }
    } else {
      ElMessage.error(res?.message || '生成修复方案失败')
    }
  } catch (error) {
    ElMessage.error(error.message || '生成修复方案失败')
  } finally {
    loading.value = false
  }
}

async function regenerate() {
  if (!currentFix.value?.id) {
    await generate()
    return
  }
  loading.value = true
  try {
    const res = await staticAnalysisFixService.regenerate(props.taskId, currentFix.value.id, userPrompt.value)
    if (res?.success) {
      currentFix.value = { ...currentFix.value, ...res.item }
      ElMessage.success('已重新生成')
    }
  } catch (error) {
    ElMessage.error(error.message || '重新生成失败')
  } finally {
    loading.value = false
  }
}

async function applyFix() {
  if (!currentFix.value?.id) return
  applying.value = true
  try {
    const res = await staticAnalysisFixService.apply(props.taskId, [currentFix.value.id])
    const applied = res?.data?.applied || []
    const conflicted = res?.data?.conflicted || []
    if (applied.length) {
      currentFix.value = { ...currentFix.value, status: 'applied' }
      ElMessage.success('修复已应用到代码库')
      emit('applied', { fixIds: [currentFix.value.id], problemId: props.problem?.id, applied })
      dialogVisible.value = false
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

function handleClosed() {
  step.value = 'input'
  currentFix.value = null
  userPrompt.value = ''
}
</script>

<style scoped>
.problem-summary {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 12px 14px;
  margin-bottom: 14px;
}

.summary-line {
  display: flex;
  align-items: center;
  gap: 8px;
}

.issue-name {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.summary-loc {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  font-size: 13px;
  color: #64748b;
}

.summary-collapse {
  margin-top: 8px;
}

.four-part {
  margin: 0;
  font-size: 13px;
  color: #374151;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

.field-label {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
}

.quick-tags {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.tags-label {
  font-size: 12px;
  color: #909399;
}

.quick-tag {
  cursor: pointer;
}

.options-row {
  display: flex;
  align-items: center;
  gap: 18px;
  margin-top: 14px;
}

.loading-box {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 30px;
  justify-content: center;
  color: #606266;
  font-size: 14px;
}

.result-prompt {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
}

.dialog-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.footer-tip {
  font-size: 12px;
  color: #909399;
}

.footer-actions {
  display: flex;
  gap: 10px;
  margin-left: auto;
}
</style>
