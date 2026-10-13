<template>
  <div class="pc-card" :class="{ 'is-expanded': isExpanded }" :style="{ '--pc': phase.color || '#4fc3f7' }">
    <!-- Phase header row -->
    <div class="pc-header" @click="$emit('toggle')">
      <div class="pc-header-left">
        <div class="pc-index">{{ String(index + 1).padStart(2, '0') }}</div>
        <PhaseIcon :icon="phase.icon" :color="phase.color" />
        <div class="pc-name-block">
          <span class="pc-name">{{ phase.name }}</span>
          <span class="pc-weight-badge">工作量占比 {{ phase.weight.toFixed(0) }}%</span>
        </div>
      </div>

      <div class="pc-header-center">
        <div class="pc-bar-wrap">
          <div class="pc-bar-bg">
            <div
              class="pc-bar-fill"
              :style="{ width: `${phase.automation_level}%`, background: barGradient }"
            />
          </div>
          <span class="pc-bar-label">{{ phase.automation_level.toFixed(1) }}%</span>
        </div>
        <div class="pc-auto-label">自动化程度</div>
      </div>

      <div class="pc-header-right">
        <div class="pc-auto-badge" :style="{ color: phase.color, borderColor: phase.color + '55' }">
          <svg viewBox="0 0 20 20" fill="none">
            <circle cx="10" cy="10" r="8" :stroke="phase.color" stroke-width="1.5" opacity="0.4"/>
            <path
              :d="arcPath(phase.automation_level)"
              :stroke="phase.color"
              stroke-width="2"
              stroke-linecap="round"
              fill="none"
            />
          </svg>
          <span>{{ phase.automation_level.toFixed(0) }}%</span>
        </div>
        <div class="pc-chevron" :class="{ rotated: isExpanded }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </div>
      </div>
    </div>

    <!-- Expanded sub-steps -->
    <transition name="pc-expand">
      <div class="pc-substeps" v-if="isExpanded && phase.sub_steps?.length">
        <div
          v-for="(ss, si) in phase.sub_steps"
          :key="ss.id"
          class="pc-substep"
          :style="{ '--ss-delay': `${si * 0.05}s` }"
        >
          <div class="pc-ss-left">
            <div class="pc-ss-dot" :style="{ background: phase.color }"></div>
            <span class="pc-ss-name">{{ ss.name }}</span>
          </div>
          <div class="pc-ss-center">
            <div class="pc-ss-bar-bg">
              <div
                class="pc-ss-bar-fill"
                :style="{ width: `${ss.automation_level}%`, background: ssBarGradient(ss.automation_level) }"
              />
            </div>
          </div>
          <div class="pc-ss-right">
            <span class="pc-ss-auto" :style="{ color: ssColor(ss.automation_level) }">
              {{ ss.automation_level.toFixed(1) }}%
            </span>
            <span class="pc-ss-weight">({{ ss.weight.toFixed(0) }}%)</span>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import PhaseIcon from './PhaseIcon.vue'

const props = defineProps({
  phase: { type: Object, required: true },
  index: { type: Number, default: 0 },
  isExpanded: { type: Boolean, default: false },
})
defineEmits(['toggle'])

const barGradient = `linear-gradient(90deg, ${props.phase.color || '#4fc3f7'}99, ${props.phase.color || '#4fc3f7'})`

function ssBarGradient(val) {
  if (val >= 70) return 'linear-gradient(90deg, #4fc3f7, #22d3ee)'
  if (val >= 40) return 'linear-gradient(90deg, #818cf8, #a78bfa)'
  return 'linear-gradient(90deg, #f97316, #fb923c)'
}

function ssColor(val) {
  if (val >= 70) return '#4fc3f7'
  if (val >= 40) return '#a78bfa'
  return '#fb923c'
}

function arcPath(pct) {
  const angle = (pct / 100) * 2 * Math.PI - Math.PI / 2
  const startX = 10 + 7 * Math.cos(-Math.PI / 2)
  const startY = 10 + 7 * Math.sin(-Math.PI / 2)
  const endX = 10 + 7 * Math.cos(angle)
  const endY = 10 + 7 * Math.sin(angle)
  const largeArc = pct > 50 ? 1 : 0
  if (pct >= 99.9) {
    return `M ${startX} ${startY} A 7 7 0 1 1 ${startX - 0.001} ${startY}`
  }
  return `M ${startX} ${startY} A 7 7 0 ${largeArc} 1 ${endX} ${endY}`
}
</script>

<style scoped>
.pc-card {
  background: rgba(15, 23, 42, 0.65);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-left: 3px solid var(--pc);
  border-radius: 14px;
  overflow: hidden;
  transition: all 0.25s;
  backdrop-filter: blur(8px);
}
.pc-card:hover { border-color: var(--pc); box-shadow: 0 0 20px rgba(79,195,247,0.08); }
.pc-card.is-expanded { border-color: var(--pc); box-shadow: 0 0 28px rgba(79,195,247,0.12); }

.pc-header {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 18px 24px;
  cursor: pointer;
  user-select: none;
}

.pc-header-left { display: flex; align-items: center; gap: 14px; flex: 0 0 200px; }
.pc-index {
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--pc);
  opacity: 0.6;
  font-family: monospace;
  letter-spacing: 0.05em;
}
.pc-name-block { display: flex; flex-direction: column; gap: 3px; }
.pc-name { font-size: 1rem; font-weight: 700; color: #e2e8f0; }
.pc-weight-badge {
  font-size: 0.7rem;
  color: rgba(148, 163, 184, 0.5);
  letter-spacing: 0.03em;
}

.pc-header-center { flex: 1; }
.pc-bar-wrap { display: flex; align-items: center; gap: 10px; }
.pc-bar-bg {
  flex: 1;
  height: 8px;
  background: rgba(255,255,255,0.06);
  border-radius: 99px;
  overflow: hidden;
}
.pc-bar-fill {
  height: 100%;
  border-radius: 99px;
  transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 0 8px rgba(79,195,247,0.4);
}
.pc-bar-label { font-size: 0.88rem; font-weight: 700; color: #94a3b8; min-width: 42px; text-align: right; }
.pc-auto-label { font-size: 0.68rem; color: rgba(148, 163, 184, 0.4); margin-top: 4px; }

.pc-header-right { display: flex; align-items: center; gap: 16px; flex-shrink: 0; }

.pc-auto-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  border: 1px solid;
  border-radius: 8px;
  padding: 6px 12px;
  font-size: 1.05rem;
  font-weight: 700;
}
.pc-auto-badge svg { width: 22px; height: 22px; }

.pc-chevron {
  width: 24px;
  height: 24px;
  color: #475569;
  transition: transform 0.3s;
}
.pc-chevron.rotated { transform: rotate(180deg); color: var(--pc); }
.pc-chevron svg { width: 100%; height: 100%; }

/* Sub-steps */
.pc-substeps {
  padding: 4px 24px 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  border-top: 1px solid rgba(255,255,255,0.05);
}

.pc-substep {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 10px 14px;
  background: rgba(255,255,255,0.03);
  border-radius: 10px;
  animation: slideIn 0.3s ease var(--ss-delay) both;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateX(-10px); }
  to { opacity: 1; transform: translateX(0); }
}

.pc-ss-left { display: flex; align-items: center; gap: 10px; flex: 0 0 220px; }
.pc-ss-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.pc-ss-name { font-size: 0.85rem; color: #cbd5e1; }

.pc-ss-center { flex: 1; }
.pc-ss-bar-bg {
  height: 5px;
  background: rgba(255,255,255,0.05);
  border-radius: 99px;
  overflow: hidden;
}
.pc-ss-bar-fill {
  height: 100%;
  border-radius: 99px;
  transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
}

.pc-ss-right { display: flex; align-items: center; gap: 8px; flex-shrink: 0; min-width: 90px; justify-content: flex-end; }
.pc-ss-auto { font-size: 0.92rem; font-weight: 700; }
.pc-ss-weight { font-size: 0.7rem; color: rgba(148, 163, 184, 0.35); }

/* Expand transition */
.pc-expand-enter-active { transition: max-height 0.35s ease, opacity 0.3s ease; }
.pc-expand-leave-active { transition: max-height 0.25s ease, opacity 0.2s ease; }
.pc-expand-enter-from, .pc-expand-leave-to { max-height: 0; opacity: 0; }
.pc-expand-enter-to, .pc-expand-leave-from { max-height: 1000px; opacity: 1; }
</style>
