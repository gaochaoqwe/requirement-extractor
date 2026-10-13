<template>
  <div class="problem-filter-panel">
    <div class="filter-header">
      <h3>问题过滤设置</h3>
      <el-button @click="$emit('close')" :icon="Close" size="small" text />
    </div>

    <div class="filter-content">
      <!-- 过滤说明 -->
      <el-alert
        title="过滤说明"
        type="info"
        :closable="false"
        style="margin-bottom: 16px;"
      >
        <p><strong>AND逻辑：</strong>问题原因字段<strong>同时包含</strong>所有关键词的问题将被过滤（设置为灰色状态）</p>
        <p><strong>OR逻辑：</strong>问题原因字段<strong>包含任一</strong>关键词的问题将被过滤</p>
        <p>例如：AND("可能", "数组") - 问题原因同时包含"可能"和"数组"才会被过滤</p>
        <p style="margin-top: 4px;">例如：OR("硬编码", "魔法数字") - 问题原因包含"硬编码"或"魔法数字"就会被过滤</p>
      </el-alert>

      <!-- 当前过滤规则列表 -->
      <div class="filter-rules-section">
        <div class="section-header">
          <h4>当前过滤规则</h4>
          <div style="display: flex; gap: 8px;">
            <el-button
              type="success"
              size="small"
              :icon="Plus"
              @click="initFromSystemTemplates"
              :loading="initializing"
            >
              从系统模板初始化
            </el-button>
            <el-button
              type="primary"
              size="small"
              :icon="Plus"
              @click="showAddDialog = true"
            >
              添加规则
            </el-button>
          </div>
        </div>

        <div v-if="filterRules.length > 0" class="rules-list">
          <div
            v-for="rule in filterRules"
            :key="rule.id"
            class="rule-item"
            :class="{ disabled: !rule.is_enabled }"
          >
            <div class="rule-header">
              <el-switch
                v-model="rule.is_enabled"
                @change="toggleRule(rule)"
              />
              <span class="rule-name">{{ rule.filter_name || '未命名规则' }}</span>
              <el-tag size="small" :type="rule.logic_type === 'OR' ? 'warning' : 'info'" style="margin-left: 8px;">
                {{ rule.logic_type }}
              </el-tag>
              <div class="rule-actions">
                <el-button
                  type="primary"
                  size="small"
                  text
                  :icon="Edit"
                  @click="editRule(rule)"
                >
                  编辑
                </el-button>
                <el-button
                  type="danger"
                  size="small"
                  text
                  :icon="Delete"
                  @click="deleteRule(rule)"
                >
                  删除
                </el-button>
              </div>
            </div>
            <div class="rule-keywords">
              <el-tag
                v-for="(keyword, idx) in rule.keywords"
                :key="idx"
                size="small"
                type="info"
                style="margin-right: 6px;"
              >
                {{ keyword }}
              </el-tag>
            </div>
          </div>
        </div>

        <el-empty
          v-else
          description="暂无过滤规则，点击上方按钮添加"
          :image-size="100"
        />
      </div>

      <!-- 应用过滤按钮 -->
      <div class="filter-actions">
        <el-button
          type="success"
          size="large"
          :loading="applying"
          @click="applyFilters"
          style="width: 100%;"
        >
          应用过滤规则
        </el-button>
        <p class="action-hint">应用后，匹配规则的问题将变为灰色（已过滤）状态</p>
      </div>
    </div>

    <!-- 添加/编辑规则对话框 -->
    <el-dialog
      v-model="showAddDialog"
      :title="editingRule ? '编辑过滤规则' : '添加过滤规则'"
      width="500px"
    >
      <el-form :model="ruleForm" label-width="100px">
        <el-form-item label="规则名称">
          <el-input
            v-model="ruleForm.filter_name"
            placeholder="可选，方便识别规则"
          />
        </el-form-item>
        <el-form-item label="过滤关键词" required>
          <el-select
            v-model="ruleForm.keywords"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="输入关键词后按回车添加"
            style="width: 100%;"
          >
          </el-select>
          <div style="margin-top: 8px; font-size: 12px; color: #888;">
            输入关键词后按回车添加
          </div>
        </el-form-item>
        <el-form-item label="逻辑类型">
          <el-radio-group v-model="ruleForm.logic_type">
            <el-radio value="AND">AND（同时满足所有关键词）</el-radio>
            <el-radio value="OR">OR（满足任一关键词）</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="启用规则">
          <el-switch v-model="ruleForm.is_enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button
          type="primary"
          @click="saveRule"
          :disabled="ruleForm.keywords.length === 0"
        >
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { Close, Plus, Edit, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

// Emits
const emit = defineEmits(['close', 'applied'])

// 路由
const route = useRoute()
const taskId = computed(() => route.params.taskId)

// 响应式数据
const filterRules = ref([])
const showAddDialog = ref(false)
const applying = ref(false)
const editingRule = ref(null)
const initializing = ref(false)
const ruleForm = ref({
  filter_name: '',
  keywords: [],
  logic_type: 'AND',
  is_enabled: true
})

// 加载过滤规则
const loadFilterRules = async () => {
  try {
    const response = await axios.get(`/api/codeReview/regressionTest/functionReview/${taskId.value}/problem_filters`)
    if (response.data.success) {
      filterRules.value = response.data.data
    }
  } catch (error) {
    console.error('加载过滤规则失败:', error)
    ElMessage.error('加载过滤规则失败')
  }
}

// 切换规则启用状态
const toggleRule = async (rule) => {
  try {
    await axios.put(`/api/codeReview/regressionTest/functionReview/${taskId.value}/problem_filters/${rule.id}`, {
      is_enabled: rule.is_enabled
    })
    ElMessage.success(rule.is_enabled ? '规则已启用' : '规则已禁用')
  } catch (error) {
    console.error('更新规则失败:', error)
    ElMessage.error('更新规则失败')
    // 回滚状态
    rule.is_enabled = !rule.is_enabled
  }
}

// 编辑规则
const editRule = (rule) => {
  editingRule.value = rule
  ruleForm.value = {
    filter_name: rule.filter_name || '',
    keywords: [...rule.keywords],
    logic_type: rule.logic_type || 'AND',
    is_enabled: rule.is_enabled
  }
  showAddDialog.value = true
}

// 删除规则
const deleteRule = async (rule) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这个过滤规则吗？',
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await axios.delete(`/api/codeReview/regressionTest/functionReview/${taskId.value}/problem_filters/${rule.id}`)
    ElMessage.success('规则删除成功')
    await loadFilterRules()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除规则失败:', error)
      ElMessage.error('删除规则失败')
    }
  }
}

// 保存规则
const saveRule = async () => {
  if (ruleForm.value.keywords.length === 0) {
    ElMessage.warning('请至少添加一个关键词')
    return
  }

  try {
    if (editingRule.value) {
      // 更新规则
      await axios.put(
        `/api/codeReview/regressionTest/functionReview/${taskId.value}/problem_filters/${editingRule.value.id}`,
        ruleForm.value
      )
      ElMessage.success('规则更新成功')
    } else {
      // 创建规则
      await axios.post(
        `/api/codeReview/regressionTest/functionReview/${taskId.value}/problem_filters`,
        ruleForm.value
      )
      ElMessage.success('规则创建成功')
    }
    
    showAddDialog.value = false
    editingRule.value = null
    ruleForm.value = {
      filter_name: '',
      keywords: [],
      logic_type: 'AND',
      is_enabled: true
    }
    await loadFilterRules()
  } catch (error) {
    console.error('保存规则失败:', error)
    ElMessage.error('保存规则失败')
  }
}

// 应用过滤规则
const applyFilters = async () => {
  try {
    applying.value = true
    const response = await axios.post(
      `/api/codeReview/regressionTest/functionReview/${taskId.value}/problem_filters/apply`
    )
    
    if (response.data.success) {
      ElMessage.success({
        message: response.data.message,
        duration: 3000
      })
      emit('applied')
    }
  } catch (error) {
    console.error('应用过滤规则失败:', error)
    ElMessage.error('应用过滤规则失败')
  } finally {
    applying.value = false
  }
}

// 从系统模板初始化规则
const initFromSystemTemplates = async () => {
  try {
    await ElMessageBox.confirm(
      '是否从系统预设模板初始化过滤规则？这将添加8条常用的过滤规则。',
      '确认初始化',
      {
        confirmButtonText: '初始化',
        cancelButtonText: '取消',
        type: 'info',
      }
    )
    
    initializing.value = true
    const response = await axios.post(
      `/api/codeReview/regressionTest/functionReview/${taskId.value}/problem_filters/init_from_system_templates`
    )
    
    if (response.data.success) {
      ElMessage.success(response.data.message)
      await loadFilterRules()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('初始化系统模板失败:', error)
      ElMessage.error('初始化系统模板失败')
    }
  } finally {
    initializing.value = false
  }
}

// 生命周期
onMounted(() => {
  loadFilterRules()
})
</script>

<style scoped>
.problem-filter-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #252526;
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #3c3c3c;
  background: #1e1e1e;
}

.filter-header h3 {
  margin: 0;
  font-size: 18px;
  color: #d4d4d4;
}

.filter-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  color: #d4d4d4;
}

.filter-rules-section {
  margin-bottom: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h4 {
  margin: 0;
  font-size: 16px;
  color: #d4d4d4;
}

.rules-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.rule-item {
  background: #1e1e1e;
  padding: 16px;
  border-radius: 8px;
  border-left: 4px solid #007acc;
  transition: all 0.3s;
  border: 1px solid #3c3c3c;
}

.rule-item.disabled {
  opacity: 0.6;
  border-left-color: #6a6a6a;
}

.rule-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.rule-name {
  flex: 1;
  font-size: 14px;
  font-weight: 600;
  color: #d4d4d4;
}

.rule-actions {
  display: flex;
  gap: 4px;
}

.rule-keywords {
  padding-left: 40px;
}

.filter-actions {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #3c3c3c;
}

.action-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #9aa0a6;
  text-align: center;
}

:deep(.el-alert) {
  background: #1e1e1e;
  border: 1px solid #3c3c3c;
}

:deep(.el-alert__title),
:deep(.el-alert__description),
:deep(.el-alert__description p) {
  color: #d4d4d4;
}

:deep(.el-empty__description) {
  color: #9aa0a6;
}

:deep(.el-dialog__header),
:deep(.el-dialog__body),
:deep(.el-dialog__footer) {
  background: #1e1e1e;
}

:deep(.el-dialog__title) {
  color: #d4d4d4;
}

:deep(.el-form-item__label) {
  color: #c5c5c5;
}

:deep(.el-input__wrapper),
:deep(.el-select__wrapper) {
  background: #252526;
  box-shadow: 0 0 0 1px #3c3c3c inset;
}

:deep(.el-input__inner) {
  color: #d4d4d4;
}

:deep(.el-radio__label) {
  color: #d4d4d4;
}
</style>

