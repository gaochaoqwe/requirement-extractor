<template>
  <div class="ad-dashboard">
    <!-- Header -->
    <div class="ad-header">
      <div class="ad-header-left">
        <svg class="ad-logo" viewBox="0 0 48 48" fill="none">
          <circle cx="24" cy="24" r="22" stroke="url(#logoGrad)" stroke-width="2"/>
          <path d="M14 32 L20 20 L24 26 L28 18 L34 32" stroke="url(#lineGrad)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
          <circle cx="24" cy="24" r="3" fill="#4fc3f7"/>
          <defs>
            <linearGradient id="logoGrad" x1="0" y1="0" x2="48" y2="48">
              <stop offset="0%" stop-color="#4fc3f7"/>
              <stop offset="100%" stop-color="#7c4dff"/>
            </linearGradient>
            <linearGradient id="lineGrad" x1="14" y1="32" x2="34" y2="18">
              <stop offset="0%" stop-color="#4fc3f7"/>
              <stop offset="100%" stop-color="#a78bfa"/>
            </linearGradient>
          </defs>
        </svg>
        <div class="ad-title-block">
          <h1 class="ad-title">光电类软件测评自动化看板</h1>
          <p class="ad-subtitle">Optoelectronic Software Evaluation Automation Dashboard</p>
        </div>
      </div>
      <div class="ad-header-right">
        <div class="ad-config-select">
          <label>评测类型</label>
          <div class="custom-select-wrap">
            <select v-model="activeConfigId" @change="onConfigChange" class="custom-select">
              <option v-for="c in configList" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </div>
        </div>
        <button class="ad-cfg-btn" @click="openConfigPanel">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
          </svg>
          参数配置
        </button>
      </div>
    </div>

    <!-- Overall automation gauge -->
    <div class="ad-overview" v-if="activeConfig">
      <div class="ad-gauge-card">
        <OverallGauge :value="overallAutomation" />
        <div class="ad-gauge-label">
          <span class="ad-gauge-title">综合自动化程度</span>
          <span class="ad-gauge-value">{{ overallAutomation.toFixed(1) }}%</span>
        </div>
      </div>
      <div class="ad-phase-overview">
        <div
          v-for="ph in activeConfig.phases"
          :key="ph.id"
          class="ad-phase-pill"
          :style="{ '--phase-color': ph.color || '#4fc3f7' }"
          @click="togglePhase(ph.id)"
          :class="{ 'is-expanded': expandedPhases.has(ph.id) }"
        >
          <PhaseIcon :icon="ph.icon" :color="ph.color" />
          <span class="ad-pill-name">{{ ph.name }}</span>
          <span class="ad-pill-auto">{{ ph.automation_level.toFixed(0) }}%</span>
          <span class="ad-pill-weight">({{ ph.weight.toFixed(0) }}%工量)</span>
        </div>
      </div>
    </div>

    <!-- Phase cards -->
    <div class="ad-phases" v-if="activeConfig">
      <PhaseCard
        v-for="(ph, idx) in activeConfig.phases"
        :key="ph.id"
        :phase="ph"
        :index="idx"
        :is-expanded="expandedPhases.has(ph.id)"
        @toggle="togglePhase(ph.id)"
      />
    </div>

    <div class="ad-loading" v-if="loading">
      <div class="ad-spinner"></div>
    </div>

    <!-- Config Panel Modal -->
    <ConfigPanel
      v-if="showConfig"
      :config="activeConfig"
      :all-configs="configList"
      @close="showConfig = false"
      @saved="onConfigSaved"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { listConfigs, getConfig } from './automationApi'
import OverallGauge from './components/OverallGauge.vue'
import PhaseIcon from './components/PhaseIcon.vue'
import PhaseCard from './components/PhaseCard.vue'
import ConfigPanel from './components/ConfigPanel.vue'

const loading = ref(false)
const configList = ref([])
const activeConfigId = ref(null)
const activeConfig = ref(null)
const expandedPhases = ref(new Set())
const showConfig = ref(false)

const overallAutomation = computed(() => {
  if (!activeConfig.value?.phases?.length) return 0
  const total = activeConfig.value.phases.reduce((acc, ph) => {
    return acc + ph.automation_level * (ph.weight / 100)
  }, 0)
  return Math.min(100, total)
})

async function loadConfigList() {
  loading.value = true
  try {
    configList.value = await listConfigs()
    if (configList.value.length > 0 && !activeConfigId.value) {
      activeConfigId.value = configList.value[0].id
      await loadActiveConfig()
    }
  } catch (e) {
    ElMessage.error('加载配置列表失败: ' + e.message)
  } finally {
    loading.value = false
  }
}

async function loadActiveConfig() {
  if (!activeConfigId.value) return
  loading.value = true
  try {
    activeConfig.value = await getConfig(activeConfigId.value)
    expandedPhases.value = new Set()
  } catch (e) {
    ElMessage.error('加载配置失败: ' + e.message)
  } finally {
    loading.value = false
  }
}

function onConfigChange() {
  loadActiveConfig()
}

function togglePhase(phaseId) {
  const s = new Set(expandedPhases.value)
  if (s.has(phaseId)) s.delete(phaseId)
  else s.add(phaseId)
  expandedPhases.value = s
}

function openConfigPanel() {
  if (!activeConfig.value) {
    ElMessage.warning('请先选择配置')
    return
  }
  showConfig.value = true
}

async function onConfigSaved() {
  showConfig.value = false
  await loadConfigList()
  await loadActiveConfig()
  ElMessage.success('配置已保存')
}

onMounted(loadConfigList)
</script>

<style scoped>
.ad-dashboard {
  min-height: 100vh;
  background: linear-gradient(135deg, #0a0e1a 0%, #0f172a 40%, #0c1526 100%);
  color: #e2e8f0;
  font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  padding: 0 0 40px;
  position: relative;
  overflow-x: hidden;
}

.ad-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 36px;
  background: rgba(15, 23, 42, 0.85);
  border-bottom: 1px solid rgba(79, 195, 247, 0.15);
  backdrop-filter: blur(12px);
  position: sticky;
  top: 0;
  z-index: 50;
}

.ad-header-left { display: flex; align-items: center; gap: 16px; }
.ad-logo { width: 44px; height: 44px; flex-shrink: 0; }
.ad-title-block { display: flex; flex-direction: column; }

.ad-title {
  font-size: 1.35rem;
  font-weight: 700;
  margin: 0;
  background: linear-gradient(90deg, #4fc3f7, #a78bfa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 0.02em;
}

.ad-subtitle {
  margin: 2px 0 0;
  font-size: 0.72rem;
  color: rgba(148, 163, 184, 0.7);
  letter-spacing: 0.04em;
}

.ad-header-right { display: flex; align-items: center; gap: 16px; }
.ad-config-select { display: flex; align-items: center; gap: 10px; }
.ad-config-select label { font-size: 0.8rem; color: #94a3b8; white-space: nowrap; }

.custom-select-wrap { position: relative; }
.custom-select {
  appearance: none;
  background: rgba(30, 41, 59, 0.9);
  border: 1px solid rgba(79, 195, 247, 0.3);
  border-radius: 8px;
  color: #e2e8f0;
  font-size: 0.88rem;
  padding: 7px 32px 7px 14px;
  cursor: pointer;
  outline: none;
  transition: border-color 0.2s;
  min-width: 140px;
}
.custom-select:hover { border-color: rgba(79, 195, 247, 0.6); }

.ad-cfg-btn {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 8px 18px;
  background: linear-gradient(135deg, rgba(79,195,247,0.15), rgba(124,77,255,0.15));
  border: 1px solid rgba(79,195,247,0.35);
  border-radius: 8px;
  color: #4fc3f7;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}
.ad-cfg-btn svg { width: 16px; height: 16px; }
.ad-cfg-btn:hover {
  background: linear-gradient(135deg, rgba(79,195,247,0.25), rgba(124,77,255,0.25));
  border-color: rgba(79,195,247,0.65);
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(79,195,247,0.2);
}

.ad-overview {
  display: flex;
  align-items: center;
  gap: 28px;
  padding: 28px 36px 20px;
  flex-wrap: wrap;
}

.ad-gauge-card {
  display: flex;
  align-items: center;
  gap: 18px;
  background: rgba(15, 25, 50, 0.6);
  border: 1px solid rgba(79, 195, 247, 0.15);
  border-radius: 16px;
  padding: 20px 24px;
  backdrop-filter: blur(8px);
  flex-shrink: 0;
}

.ad-gauge-label { display: flex; flex-direction: column; }
.ad-gauge-title { font-size: 0.8rem; color: #94a3b8; margin-bottom: 4px; }
.ad-gauge-value {
  font-size: 2.2rem;
  font-weight: 800;
  background: linear-gradient(90deg, #4fc3f7, #a78bfa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1.1;
}

.ad-phase-overview { display: flex; flex-wrap: wrap; gap: 10px; flex: 1; }

.ad-phase-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: rgba(15, 25, 50, 0.55);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 40px;
  cursor: pointer;
  transition: all 0.25s;
  border-left: 3px solid var(--phase-color);
}
.ad-phase-pill:hover,
.ad-phase-pill.is-expanded {
  background: rgba(79, 195, 247, 0.08);
  border-color: var(--phase-color);
  box-shadow: 0 0 14px rgba(79,195,247,0.15);
  transform: translateY(-2px);
}

.ad-pill-name { font-size: 0.85rem; font-weight: 600; color: #cbd5e1; }
.ad-pill-auto { font-size: 1rem; font-weight: 700; color: var(--phase-color); }
.ad-pill-weight { font-size: 0.72rem; color: rgba(148, 163, 184, 0.5); }

.ad-phases { display: flex; flex-direction: column; gap: 14px; padding: 0 36px; }

.ad-loading {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.45);
  z-index: 200;
}
.ad-spinner {
  width: 44px;
  height: 44px;
  border: 3px solid rgba(79, 195, 247, 0.2);
  border-top-color: #4fc3f7;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
