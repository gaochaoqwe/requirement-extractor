<template>
  <div class="rule-list">
    <div class="rule-header">
      <h3>规则列表</h3>
      <div class="header-actions">
        <el-button 
          type="primary" 
          size="small" 
          @click="checkAll"
          :disabled="isAllChecked"
        >
          全选
        </el-button>
        <el-button 
          size="small" 
          @click="uncheckAll"
          :disabled="isAllUnchecked"
        >
          取消全选
        </el-button>
      </div>
    </div>

    <div class="rule-content">
      <el-collapse v-model="activeGroups" class="rule-collapse">
        <!-- [NEW] 过滤后问题 - 放在最上方 -->
        <el-collapse-item 
          name="filtered" 
          v-if="filteredRules.length > 0"
          class="filtered-group"
        >
          <template #title>
            <div class="group-title filtered-title">
              <el-icon><Filter /></el-icon>
              <span>过滤后问题</span>
              <el-tag size="small" type="primary" effect="dark">{{ filteredRules.length }}</el-tag>
            </div>
          </template>
          <div class="rules-group">
            <div
              v-for="rule in filteredRules"
              :key="rule.rule_code"
              class="rule-item filtered-rule-item"
            >
              <el-checkbox 
                :model-value="isRuleChecked(rule.rule_code)"
                @change="(val) => toggleRuleCheck(rule.rule_code, val)"
              />
              <div class="rule-info">
                <div class="rule-code">
                  <el-tag :type="getRuleTypeTagType(rule.rule_type)" size="small">
                    {{ rule.rule_code }}
                  </el-tag>
                  <!-- [NEW] 根据filtered_badge显示不同标记 -->
                  <el-tag 
                    v-if="rule.filtered_badge === 'accurate'" 
                    type="success" 
                    size="small"
                    effect="dark"
                  >
                    <el-icon><Check /></el-icon>确定类规则
                  </el-tag>
                  <el-tag 
                    v-else-if="rule.filtered_badge === 'ai_confirmed'" 
                    type="warning" 
                    size="small"
                    effect="dark"
                    class="ai-confirmed-badge"
                  >
                    <el-icon><CircleCheck /></el-icon>AI确认
                  </el-tag>
                </div>
                <div class="rule-name" :title="rule.rule_name">
                  {{ rule.rule_name || '无规则名称' }}
                </div>
                <div v-if="rule.problem_count > 0" class="rule-stats">
                  <el-tag size="small" type="danger" effect="plain">
                    {{ rule.problem_count }} 个问题
                    <span v-if="rule.ai_confirmed_count > 0" class="ai-confirmed-count">
                      (AI确认 {{ rule.ai_confirmed_count }} 个)
                    </span>
                  </el-tag>
                </div>
              </div>
              <el-button
                v-if="rule.problem_count > 0"
                class="rule-fix-btn"
                size="small"
                type="warning"
                text
                @click.stop="requestRuleFix(rule)"
                title="按该规则批量修复问题"
              >
                <el-icon><MagicStick /></el-icon>
                修复该规则 ({{ rule.problem_count }})
              </el-button>
            </div>
          </div>
        </el-collapse-item>

        <!-- 确定勾选 -->
        <el-collapse-item 
          name="accurate-selected" 
          v-if="showAccurateSelected && accurateSelectedRules.length > 0"
        >
          <template #title>
            <div class="group-title">
              <el-icon><Check /></el-icon>
              <span>确定勾选</span>
              <el-tag size="small" type="success">{{ accurateSelectedRules.length }}</el-tag>
            </div>
          </template>
          <div class="rules-group">
            <div
              v-for="rule in accurateSelectedRules"
              :key="rule.rule_code"
              class="rule-item"
            >
              <el-checkbox 
                :model-value="isRuleChecked(rule.rule_code)"
                @change="(val) => toggleRuleCheck(rule.rule_code, val)"
              />
              <div class="rule-info">
                <div class="rule-code">
                  <el-tag :type="getRuleTypeTagType(rule.rule_type)" size="small">
                    {{ rule.rule_code }}
                  </el-tag>
                  <el-tag type="success" size="small">确定</el-tag>
                </div>
                <div class="rule-name" :title="rule.rule_name">
                  {{ rule.rule_name || '无规则名称' }}
                </div>
                <div v-if="rule.problem_count > 0" class="rule-stats">
                  <el-tag size="small" type="danger" effect="plain">
                    {{ rule.problem_count }} 个问题
                  </el-tag>
                </div>
              </div>
              <el-button
                v-if="rule.problem_count > 0"
                class="rule-fix-btn"
                size="small"
                type="warning"
                text
                @click.stop="requestRuleFix(rule)"
                title="按该规则批量修复问题"
              >
                <el-icon><MagicStick /></el-icon>
                修复该规则 ({{ rule.problem_count }})
              </el-button>
            </div>
          </div>
        </el-collapse-item>

        <!-- 确定非勾选 -->
        <el-collapse-item 
          name="accurate-unselected" 
          v-if="showAccurateUnselected && accurateUnselectedRules.length > 0"
        >
          <template #title>
            <div class="group-title">
              <el-icon><Close /></el-icon>
              <span>确定非勾选</span>
              <el-tag size="small" type="info">{{ accurateUnselectedRules.length }}</el-tag>
            </div>
          </template>
          <div class="rules-group">
            <div
              v-for="rule in accurateUnselectedRules"
              :key="rule.rule_code"
              class="rule-item"
            >
              <el-checkbox 
                :model-value="isRuleChecked(rule.rule_code)"
                @change="(val) => toggleRuleCheck(rule.rule_code, val)"
              />
              <div class="rule-info">
                <div class="rule-code">
                  <el-tag :type="getRuleTypeTagType(rule.rule_type)" size="small">
                    {{ rule.rule_code }}
                  </el-tag>
                  <el-tag type="success" size="small">确定</el-tag>
                </div>
                <div class="rule-name" :title="rule.rule_name">
                  {{ rule.rule_name || '无规则名称' }}
                </div>
                <div v-if="rule.problem_count > 0" class="rule-stats">
                  <el-tag size="small" type="danger" effect="plain">
                    {{ rule.problem_count }} 个问题
                  </el-tag>
                </div>
              </div>
              <el-button
                v-if="rule.problem_count > 0"
                class="rule-fix-btn"
                size="small"
                type="warning"
                text
                @click.stop="requestRuleFix(rule)"
                title="按该规则批量修复问题"
              >
                <el-icon><MagicStick /></el-icon>
                修复该规则 ({{ rule.problem_count }})
              </el-button>
            </div>
          </div>
        </el-collapse-item>

        <!-- 不确定勾选 -->
        <el-collapse-item 
          name="uncertain-selected" 
          v-if="showUncertainSelected && uncertainSelectedRules.length > 0"
        >
          <template #title>
            <div class="group-title">
              <el-icon><QuestionFilled /></el-icon>
              <span>不确定勾选</span>
              <el-tag size="small" type="warning">{{ uncertainSelectedRules.length }}</el-tag>
            </div>
          </template>
          <div class="rules-group">
            <div
              v-for="rule in uncertainSelectedRules"
              :key="rule.rule_code"
              class="rule-item"
            >
              <el-checkbox 
                :model-value="isRuleChecked(rule.rule_code)"
                @change="(val) => toggleRuleCheck(rule.rule_code, val)"
              />
              <div class="rule-info">
                <div class="rule-code">
                  <el-tag :type="getRuleTypeTagType(rule.rule_type)" size="small">
                    {{ rule.rule_code }}
                  </el-tag>
                  <el-tag type="warning" size="small">不确定</el-tag>
                </div>
                <div class="rule-name" :title="rule.rule_name">
                  {{ rule.rule_name || '无规则名称' }}
                </div>
                <div v-if="rule.problem_count > 0" class="rule-stats">
                  <el-tag size="small" type="danger" effect="plain">
                    {{ rule.problem_count }} 个问题
                  </el-tag>
                </div>
              </div>
              <el-button
                v-if="rule.problem_count > 0"
                class="rule-fix-btn"
                size="small"
                type="warning"
                text
                @click.stop="requestRuleFix(rule)"
                title="按该规则批量修复问题"
              >
                <el-icon><MagicStick /></el-icon>
                修复该规则 ({{ rule.problem_count }})
              </el-button>
            </div>
          </div>
        </el-collapse-item>

        <!-- 不确定非勾选 -->
        <el-collapse-item 
          name="uncertain-unselected" 
          v-if="showUncertainUnselected && uncertainUnselectedRules.length > 0"
        >
          <template #title>
            <div class="group-title">
              <el-icon><Remove /></el-icon>
              <span>不确定非勾选</span>
              <el-tag size="small" type="info">{{ uncertainUnselectedRules.length }}</el-tag>
            </div>
          </template>
          <div class="rules-group">
            <div
              v-for="rule in uncertainUnselectedRules"
              :key="rule.rule_code"
              class="rule-item"
            >
              <el-checkbox 
                :model-value="isRuleChecked(rule.rule_code)"
                @change="(val) => toggleRuleCheck(rule.rule_code, val)"
              />
              <div class="rule-info">
                <div class="rule-code">
                  <el-tag :type="getRuleTypeTagType(rule.rule_type)" size="small">
                    {{ rule.rule_code }}
                  </el-tag>
                  <el-tag type="warning" size="small">不确定</el-tag>
                </div>
                <div class="rule-name" :title="rule.rule_name">
                  {{ rule.rule_name || '无规则名称' }}
                </div>
                <div v-if="rule.problem_count > 0" class="rule-stats">
                  <el-tag size="small" type="danger" effect="plain">
                    {{ rule.problem_count }} 个问题
                  </el-tag>
                </div>
              </div>
              <el-button
                v-if="rule.problem_count > 0"
                class="rule-fix-btn"
                size="small"
                type="warning"
                text
                @click.stop="requestRuleFix(rule)"
                title="按该规则批量修复问题"
              >
                <el-icon><MagicStick /></el-icon>
                修复该规则 ({{ rule.problem_count }})
              </el-button>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Check, Close, QuestionFilled, Remove, Filter, CircleCheck, MagicStick } from '@element-plus/icons-vue'

// Props
const props = defineProps({
  rules: {
    type: Array,
    default: () => []
  },
  // 四个开关状态
  showAccurateSelected: {
    type: Boolean,
    default: true
  },
  showAccurateUnselected: {
    type: Boolean,
    default: true
  },
  showUncertainSelected: {
    type: Boolean,
    default: true
  },
  showUncertainUnselected: {
    type: Boolean,
    default: true
  },
  // 用户勾选的规则集合（原始选中，用于分类）
  selectedRulesSet: {
    type: Set,
    default: () => new Set()
  },
  // 规则复选框选中状态集合
  checkedRulesSet: {
    type: Set,
    default: () => new Set()
  }
})

// Emits
const emit = defineEmits(['rule-check-change', 'request-batch-fix'])

// [NEW] 按规则批量修复
function requestRuleFix(rule) {
  emit('request-batch-fix', {
    type: 'rule',
    value: rule.rule_code,
    label: `规则 ${rule.rule_code}（${rule.rule_name || ''}）`,
    count: rule.problem_count || 0,
    ruleType: rule.rule_type
  })
}

// 折叠面板激活状态（默认全部展开，包含过滤后问题）
const activeGroups = ref(['filtered', 'accurate-selected', 'accurate-unselected', 'uncertain-selected', 'uncertain-unselected'])

// [NEW] 分组规则：过滤后问题（确定勾选 + 不确定勾选中AI确认）
const filteredRules = computed(() => {
  return props.rules.filter(rule => rule.is_in_filtered === true)
})

// 分组规则：确定勾选
const accurateSelectedRules = computed(() => {
  return props.rules.filter(rule => 
    rule.accuracy_type === 'accurate' && props.selectedRulesSet.has(rule.rule_code)
  )
})

// 分组规则：确定非勾选
const accurateUnselectedRules = computed(() => {
  return props.rules.filter(rule => 
    rule.accuracy_type === 'accurate' && !props.selectedRulesSet.has(rule.rule_code)
  )
})

// 分组规则：不确定勾选
const uncertainSelectedRules = computed(() => {
  return props.rules.filter(rule => 
    rule.accuracy_type === 'uncertain' && props.selectedRulesSet.has(rule.rule_code)
  )
})

// 分组规则：不确定非勾选
const uncertainUnselectedRules = computed(() => {
  return props.rules.filter(rule => 
    rule.accuracy_type === 'uncertain' && !props.selectedRulesSet.has(rule.rule_code)
  )
})

// 总可见规则数（包含过滤后问题）
const totalVisibleRulesCount = computed(() => {
  let count = filteredRules.value.length  // [NEW] 过滤后问题始终显示
  if (props.showAccurateSelected) count += accurateSelectedRules.value.length
  if (props.showAccurateUnselected) count += accurateUnselectedRules.value.length
  if (props.showUncertainSelected) count += uncertainSelectedRules.value.length
  if (props.showUncertainUnselected) count += uncertainUnselectedRules.value.length
  return count
})

// 判断规则复选框是否选中
function isRuleChecked(ruleCode) {
  return props.checkedRulesSet.has(ruleCode)
}

// 切换规则复选框状态
function toggleRuleCheck(ruleCode, checked) {
  emit('rule-check-change', ruleCode, checked)
}

// 计算属性：是否全部已勾选
const isAllChecked = computed(() => {
  const allRuleCodes = props.rules.map(r => r.rule_code)
  return allRuleCodes.length > 0 && allRuleCodes.every(code => props.checkedRulesSet.has(code))
})

// 计算属性：是否全部未勾选
const isAllUnchecked = computed(() => {
  return props.checkedRulesSet.size === 0
})

// 全选所有规则
function checkAll() {
  const allRuleCodes = props.rules.map(r => r.rule_code)
  allRuleCodes.forEach(code => {
    if (!props.checkedRulesSet.has(code)) {
      emit('rule-check-change', code, true)
    }
  })
}

// 取消全选所有规则
function uncheckAll() {
  const checkedCodes = Array.from(props.checkedRulesSet)
  checkedCodes.forEach(code => {
    emit('rule-check-change', code, false)
  })
}

// 获取规则类型标签类型
function getRuleTypeTagType(ruleType) {
  if (ruleType === 'gjb') return 'primary'
  if (ruleType === 'cwe') return 'success'
  return 'info'
}
</script>

<style scoped>
.rule-list {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: white;
}

.rule-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid #e8e8e8;
  background: white;
}

.rule-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
  white-space: nowrap;
  flex-shrink: 0;
}

.header-actions {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.rule-content {
  flex: 1;
  overflow: auto;
  padding: 0;
}

.rule-collapse {
  border: none;
}

.group-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #333;
}

.group-title .el-icon {
  font-size: 16px;
}

.rules-group {
  padding: 8px 0;
}

.rule-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  margin: 4px 8px;
  border-radius: 6px;
  transition: all 0.2s ease;
  background: #fafafa;
  border: 1px solid #e8e8e8;
}

.rule-item:hover {
  background: #f0f0f0;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
}

/* [NEW] 按规则批量修复按钮：hover 才显示 */
.rule-fix-btn {
  opacity: 0;
  transition: opacity 0.2s ease;
  flex-shrink: 0;
  padding: 4px 6px;
  font-size: 12px;
  white-space: nowrap;
}

.rule-item:hover .rule-fix-btn {
  opacity: 1;
}

.rule-info {
  flex: 1;
  min-width: 0;
}

.rule-code {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 6px;
  flex-wrap: wrap;
}

.rule-name {
  font-size: 12px;
  color: #606266;
  line-height: 1.4;
  margin-bottom: 6px;
  word-break: break-word;
}

.rule-stats {
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

/* 折叠面板样式调整 */
:deep(.el-collapse-item__header) {
  padding: 0 16px;
  height: 44px;
  line-height: 44px;
  background: #f5f7fa;
  border-bottom: 1px solid #e8e8e8;
  font-size: 14px;
}

:deep(.el-collapse-item__wrap) {
  border-bottom: none;
  background: white;
}

:deep(.el-collapse-item__content) {
  padding: 0;
}

/* 滚动条样式 */
.rule-content::-webkit-scrollbar {
  width: 6px;
}

.rule-content::-webkit-scrollbar-track {
  background: #f5f5f5;
}

.rule-content::-webkit-scrollbar-thumb {
  background: #d9d9d9;
  border-radius: 3px;
}

.rule-content::-webkit-scrollbar-thumb:hover {
  background: #bfbfbf;
}

/* [NEW] 过滤后问题分组特殊样式 */
.filtered-group :deep(.el-collapse-item__header) {
  background: linear-gradient(135deg, #e6f7ff 0%, #f0f9ff 100%);
  border-left: 4px solid #1890ff;
}

.filtered-title {
  font-weight: 600;
  color: #1890ff;
}

.filtered-title .el-icon {
  color: #1890ff;
  font-size: 18px;
  margin-right: 8px;
}

.filtered-rule-item {
  background: #fafcff;
  border-left: 3px solid #1890ff;
}

/* AI确认标记样式 */
.ai-confirmed-badge {
  background: linear-gradient(135deg, #52c41a 0%, #73d13d 100%);
  border: none;
  color: white;
}

.ai-confirmed-badge .el-icon {
  margin-right: 2px;
  font-size: 12px;
}

.ai-confirmed-count {
  color: #52c41a;
  font-weight: 600;
  margin-left: 4px;
}
</style>
