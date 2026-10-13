<template>
  <Teleport to="body">
    <div class="cp-overlay" @click.self="$emit('close')">
      <div class="cp-panel">
        <!-- Panel Header -->
        <div class="cp-header">
          <div class="cp-header-left">
            <svg viewBox="0 0 24 24" fill="none" stroke="#4fc3f7" stroke-width="2" class="cp-header-icon">
              <circle cx="12" cy="12" r="3"/>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
            </svg>
            <div>
              <h2 class="cp-title">参数配置</h2>
              <p class="cp-subtitle">配置评测类型、阶段权重和自动化程度</p>
            </div>
          </div>
          <button class="cp-close" @click="$emit('close')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <!-- Config name editor -->
        <div class="cp-section">
          <div class="cp-section-title">评测类型名称</div>
          <div class="cp-row">
            <input class="cp-input" v-model="localName" placeholder="输入配置名称..." />
            <div class="cp-row-hint">可修改当前配置名称</div>
          </div>
        </div>

        <!-- Phases config -->
        <div class="cp-section cp-phases-section">
          <div class="cp-section-header">
            <div class="cp-section-title">阶段配置</div>
            <div class="cp-weight-sum" :class="{ error: Math.abs(totalPhaseWeight - 100) > 0.5 }">
              权重合计: {{ totalPhaseWeight.toFixed(1) }}%
              <span v-if="Math.abs(totalPhaseWeight - 100) > 0.5" class="cp-warn">（应为100%）</span>
            </div>
          </div>

          <div class="cp-phases">
            <div
              v-for="(ph, pi) in localPhases"
              :key="ph._key"
              class="cp-phase-block"
              :style="{ '--phc': ph.color || '#4fc3f7' }"
            >
              <!-- Phase row -->
              <div class="cp-phase-row">
                <div class="cp-ph-drag">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="9" y1="6" x2="15" y2="6"/><line x1="9" y1="12" x2="15" y2="12"/><line x1="9" y1="18" x2="15" y2="18"/>
                  </svg>
                </div>
                <div class="cp-ph-color-dot" :style="{ background: ph.color }"></div>
                <input class="cp-input cp-ph-name" v-model="ph.name" placeholder="阶段名称" />
                <div class="cp-field-group">
                  <label>权重%</label>
                  <input type="number" class="cp-input cp-num" v-model.number="ph.weight" min="0" max="100" step="0.5" />
                </div>
                <div class="cp-field-group">
                  <label>自动化%</label>
                  <input type="number" class="cp-input cp-num" v-model.number="ph.automation_level" min="0" max="100" step="1" />
                </div>
                <div class="cp-field-group">
                  <label>颜色</label>
                  <input type="color" class="cp-color-input" v-model="ph.color" />
                </div>
                <button class="cp-icon-btn cp-expand-btn" @click="togglePhaseExpand(pi)" :title="expandedPhaseIdx === pi ? '收起子步骤' : '展开子步骤'">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :style="{ transform: expandedPhaseIdx === pi ? 'rotate(180deg)' : '' }">
                    <polyline points="6 9 12 15 18 9"/>
                  </svg>
                </button>
                <button class="cp-icon-btn cp-del-btn" @click="deletePhase(pi)" title="删除阶段">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4h6v2"/>
                  </svg>
                </button>
              </div>

              <!-- Sub-steps panel -->
              <transition name="cp-ss-expand">
                <div class="cp-substeps-panel" v-if="expandedPhaseIdx === pi">
                  <div class="cp-ss-header">
                    <span class="cp-ss-header-title">子步骤</span>
                    <div class="cp-ss-weight-sum" :class="{ error: Math.abs(subStepWeightSum(ph) - 100) > 0.5 }">
                      权重合计: {{ subStepWeightSum(ph).toFixed(1) }}%
                      <span v-if="Math.abs(subStepWeightSum(ph) - 100) > 0.5" class="cp-warn">（应为100%）</span>
                    </div>
                  </div>

                  <div
                    v-for="(ss, si) in ph.sub_steps"
                    :key="ss._key"
                    class="cp-ss-row"
                  >
                    <div class="cp-ss-dot" :style="{ background: ph.color }"></div>
                    <input class="cp-input cp-ss-name-input" v-model="ss.name" placeholder="子步骤名称" />
                    <div class="cp-field-group">
                      <label>权重%</label>
                      <input type="number" class="cp-input cp-num" v-model.number="ss.weight" min="0" max="100" step="0.5"/>
                    </div>
                    <div class="cp-field-group">
                      <label>自动化%</label>
                      <input type="number" class="cp-input cp-num" v-model.number="ss.automation_level" min="0" max="100" step="1"/>
                    </div>
                    <button class="cp-icon-btn cp-del-btn" @click="deleteSubStep(pi, si)">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                      </svg>
                    </button>
                  </div>

                  <button class="cp-add-ss-btn" @click="addSubStep(pi)">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
                    </svg>
                    添加子步骤
                  </button>
                </div>
              </transition>
            </div>
          </div>

          <button class="cp-add-phase-btn" @click="addPhase">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            添加阶段
          </button>
        </div>

        <!-- Footer actions -->
        <div class="cp-footer">
          <button class="cp-btn cp-btn-cancel" @click="$emit('close')">取消</button>
          <button class="cp-btn cp-btn-save" @click="handleSave" :disabled="saving">
            <span v-if="saving">保存中...</span>
            <span v-else>保存配置</span>
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { updateConfig, bulkReplacePhases } from '../automationApi'

const props = defineProps({
  config: { type: Object, required: true },
  allConfigs: { type: Array, default: () => [] },
})
const emit = defineEmits(['close', 'saved'])

const saving = ref(false)
const expandedPhaseIdx = ref(null)

function mkKey() { return Math.random().toString(36).slice(2) }

const localName = ref(props.config.name)
const localPhases = ref([])

function initLocal() {
  localName.value = props.config.name
  localPhases.value = (props.config.phases || []).map(ph => ({
    ...ph,
    _key: mkKey(),
    sub_steps: (ph.sub_steps || []).map(ss => ({ ...ss, _key: mkKey() })),
  }))
}

watch(() => props.config, initLocal, { immediate: true, deep: true })

// 根据子步骤权重+自动化程度加权计算阶段自动化程度
function calcPhaseAutomation(ph) {
  const steps = ph.sub_steps || []
  if (!steps.length) return ph.automation_level
  const totalW = steps.reduce((s, ss) => s + (ss.weight || 0), 0)
  if (totalW <= 0) return 0
  return steps.reduce((s, ss) => s + (ss.automation_level || 0) * ((ss.weight || 0) / totalW), 0)
}

// 子步骤任何变化时自动刷新父阶段的 automation_level
watch(
  localPhases,
  (phases) => {
    phases.forEach(ph => {
      if (ph.sub_steps && ph.sub_steps.length > 0) {
        ph.automation_level = Math.round(calcPhaseAutomation(ph) * 10) / 10
      }
    })
  },
  { deep: true }
)

const totalPhaseWeight = computed(() =>
  localPhases.value.reduce((s, ph) => s + (ph.weight || 0), 0)
)

function subStepWeightSum(ph) {
  return (ph.sub_steps || []).reduce((s, ss) => s + (ss.weight || 0), 0)
}

function togglePhaseExpand(idx) {
  expandedPhaseIdx.value = expandedPhaseIdx.value === idx ? null : idx
}

function addPhase() {
  localPhases.value.push({
    _key: mkKey(),
    name: '新阶段',
    order_index: localPhases.value.length,
    weight: 0,
    automation_level: 0,
    icon: 'doc',
    color: '#4fc3f7',
    sub_steps: [],
  })
  expandedPhaseIdx.value = localPhases.value.length - 1
}

function deletePhase(idx) {
  localPhases.value.splice(idx, 1)
  if (expandedPhaseIdx.value === idx) expandedPhaseIdx.value = null
  else if (expandedPhaseIdx.value > idx) expandedPhaseIdx.value--
}

function addSubStep(phIdx) {
  localPhases.value[phIdx].sub_steps.push({
    _key: mkKey(),
    name: '新子步骤',
    order_index: localPhases.value[phIdx].sub_steps.length,
    weight: 0,
    automation_level: 0,
    description: '',
  })
}

function deleteSubStep(phIdx, ssIdx) {
  localPhases.value[phIdx].sub_steps.splice(ssIdx, 1)
}

async function handleSave() {
  saving.value = true
  try {
    await updateConfig(props.config.id, { name: localName.value })

    const phasesPayload = localPhases.value.map((ph, i) => ({
      name: ph.name,
      order_index: i,
      weight: ph.weight,
      automation_level: ph.automation_level,
      icon: ph.icon || 'doc',
      color: ph.color || '#4fc3f7',
      sub_steps: (ph.sub_steps || []).map((ss, si) => ({
        name: ss.name,
        order_index: si,
        weight: ss.weight,
        automation_level: ss.automation_level,
        description: ss.description || '',
      })),
    }))
    await bulkReplacePhases(props.config.id, phasesPayload)
    emit('saved')
  } catch (e) {
    ElMessage.error('保存失败: ' + e.message)
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.cp-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.65);
  backdrop-filter: blur(4px);
  z-index: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.cp-panel {
  background: linear-gradient(160deg, #0f172a 0%, #1e293b 100%);
  border: 1px solid rgba(79, 195, 247, 0.2);
  border-radius: 20px;
  width: min(900px, 100%);
  max-height: 88vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 24px 80px rgba(0,0,0,0.6), 0 0 0 1px rgba(79,195,247,0.08);
  overflow: hidden;
}

.cp-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 28px;
  border-bottom: 1px solid rgba(255,255,255,0.07);
  flex-shrink: 0;
}

.cp-header-left { display: flex; align-items: center; gap: 14px; }
.cp-header-icon { width: 28px; height: 28px; flex-shrink: 0; }
.cp-title { margin: 0; font-size: 1.15rem; font-weight: 700; color: #e2e8f0; }
.cp-subtitle { margin: 2px 0 0; font-size: 0.72rem; color: #64748b; }

.cp-close {
  width: 36px; height: 36px;
  display: flex; align-items: center; justify-content: center;
  background: rgba(255,255,255,0.05);
  border: none; border-radius: 8px;
  color: #94a3b8; cursor: pointer;
  transition: all 0.2s;
}
.cp-close:hover { background: rgba(239,68,68,0.2); color: #ef4444; }
.cp-close svg { width: 18px; height: 18px; }

/* Scrollable body */
.cp-section {
  padding: 20px 28px;
  border-bottom: 1px solid rgba(255,255,255,0.05);
  overflow-y: auto;
}
.cp-phases-section { flex: 1; overflow-y: auto; }

.cp-section-title { font-size: 0.78rem; font-weight: 600; color: #4fc3f7; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 12px; }

.cp-section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }

.cp-weight-sum { font-size: 0.78rem; color: #64748b; }
.cp-weight-sum.error { color: #f97316; }
.cp-warn { margin-left: 4px; }

.cp-row { display: flex; align-items: center; gap: 14px; }
.cp-row-hint { font-size: 0.72rem; color: #475569; }

/* Inputs */
.cp-input {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px;
  color: #e2e8f0;
  font-size: 0.85rem;
  padding: 7px 12px;
  outline: none;
  transition: border-color 0.2s;
  width: 100%;
}
.cp-input:focus { border-color: rgba(79,195,247,0.5); }

.cp-num { width: 75px; text-align: center; flex-shrink: 0; }
.cp-auto-val {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 34px;
  background: rgba(79,195,247,0.07);
  border: 1px solid rgba(79,195,247,0.25);
  border-radius: 8px;
  color: #4fc3f7;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: default;
  user-select: none;
}
.cp-auto-calc-tag {
  font-size: 0.6rem;
  font-weight: 600;
  background: rgba(79,195,247,0.15);
  color: #4fc3f7;
  border-radius: 4px;
  padding: 1px 5px;
  margin-left: 4px;
  letter-spacing: 0.04em;
  vertical-align: middle;
}

.cp-color-input {
  width: 36px; height: 36px;
  padding: 2px;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px;
  background: transparent;
  cursor: pointer;
  flex-shrink: 0;
}

.cp-field-group { display: flex; flex-direction: column; gap: 3px; flex-shrink: 0; }
.cp-field-group label { font-size: 0.68rem; color: #64748b; white-space: nowrap; text-align: center; }

/* Phase blocks */
.cp-phases { display: flex; flex-direction: column; gap: 10px; margin-bottom: 12px; }

.cp-phase-block {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.07);
  border-left: 3px solid var(--phc);
  border-radius: 12px;
  overflow: hidden;
  transition: border-color 0.2s;
}
.cp-phase-block:hover { border-color: var(--phc); }

.cp-phase-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
}

.cp-ph-drag {
  width: 20px; height: 20px;
  color: #475569; cursor: grab; flex-shrink: 0;
}
.cp-ph-drag svg { width: 100%; height: 100%; }

.cp-ph-color-dot {
  width: 12px; height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

.cp-ph-name { flex: 1; }

/* Icon buttons */
.cp-icon-btn {
  width: 32px; height: 32px;
  display: flex; align-items: center; justify-content: center;
  background: rgba(255,255,255,0.05);
  border: none; border-radius: 7px;
  color: #64748b; cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}
.cp-icon-btn svg { width: 15px; height: 15px; }
.cp-icon-btn:hover { background: rgba(255,255,255,0.1); color: #e2e8f0; }
.cp-del-btn:hover { background: rgba(239,68,68,0.2); color: #ef4444; }

.cp-expand-btn svg { transition: transform 0.25s; }

/* Substeps panel */
.cp-substeps-panel {
  padding: 12px 16px 14px 36px;
  border-top: 1px solid rgba(255,255,255,0.05);
  background: rgba(0,0,0,0.15);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.cp-ss-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}
.cp-ss-header-title { font-size: 0.72rem; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.08em; }
.cp-ss-weight-sum { font-size: 0.72rem; color: #64748b; }
.cp-ss-weight-sum.error { color: #f97316; }

.cp-ss-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  background: rgba(255,255,255,0.02);
  border-radius: 8px;
}

.cp-ss-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.cp-ss-name-input { flex: 1; }

.cp-add-ss-btn {
  display: flex; align-items: center; gap: 7px;
  padding: 7px 14px;
  background: rgba(255,255,255,0.04);
  border: 1px dashed rgba(79,195,247,0.25);
  border-radius: 8px;
  color: #4fc3f7;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: 4px;
  align-self: flex-start;
}
.cp-add-ss-btn svg { width: 14px; height: 14px; }
.cp-add-ss-btn:hover { background: rgba(79,195,247,0.08); border-color: rgba(79,195,247,0.5); }

/* ss expand transition */
.cp-ss-expand-enter-active { transition: max-height 0.3s ease, opacity 0.25s ease; }
.cp-ss-expand-leave-active { transition: max-height 0.2s ease, opacity 0.15s ease; }
.cp-ss-expand-enter-from, .cp-ss-expand-leave-to { max-height: 0; opacity: 0; overflow: hidden; }
.cp-ss-expand-enter-to, .cp-ss-expand-leave-from { max-height: 800px; opacity: 1; overflow: hidden; }

/* Add phase button */
.cp-add-phase-btn {
  display: flex; align-items: center; gap: 8px;
  width: 100%;
  padding: 10px;
  background: rgba(79,195,247,0.06);
  border: 1px dashed rgba(79,195,247,0.3);
  border-radius: 10px;
  color: #4fc3f7;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
  justify-content: center;
}
.cp-add-phase-btn svg { width: 16px; height: 16px; }
.cp-add-phase-btn:hover { background: rgba(79,195,247,0.12); border-color: rgba(79,195,247,0.6); }

/* Footer */
.cp-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 28px;
  border-top: 1px solid rgba(255,255,255,0.07);
  flex-shrink: 0;
}

.cp-btn {
  padding: 9px 24px;
  border-radius: 9px;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}
.cp-btn-cancel {
  background: rgba(255,255,255,0.07);
  color: #94a3b8;
}
.cp-btn-cancel:hover { background: rgba(255,255,255,0.12); color: #e2e8f0; }
.cp-btn-save {
  background: linear-gradient(135deg, #0ea5e9, #7c3aed);
  color: #fff;
  box-shadow: 0 4px 14px rgba(14,165,233,0.3);
}
.cp-btn-save:hover { box-shadow: 0 6px 20px rgba(14,165,233,0.45); transform: translateY(-1px); }
.cp-btn-save:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
</style>
