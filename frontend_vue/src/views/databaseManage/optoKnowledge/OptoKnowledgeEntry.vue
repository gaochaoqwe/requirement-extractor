<template>
  <div class="ok-entry">
    <canvas ref="canvasRef" class="bg"></canvas>

    <div class="orbs">
      <div class="orb" :style="orbStyle(0)" @click="go('turret')">转塔</div>
      <div class="orb" :style="orbStyle(1)" @click="go('countermeasure')">对抗告警</div>
      <div class="orb" :style="orbStyle(2)" @click="go('optoradar')">光雷</div>
      <div class="orb" :style="orbStyle(3)" @click="go('pod')">吊舱</div>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const canvasRef = ref(null)

const state = reactive({
  t: 0,
  w: 0,
  h: 0
})

let rafId = 0

function resize() {
  const canvas = canvasRef.value
  if (!canvas) return
  const dpr = window.devicePixelRatio || 1
  state.w = canvas.clientWidth
  state.h = canvas.clientHeight
  canvas.width = Math.floor(state.w * dpr)
  canvas.height = Math.floor(state.h * dpr)
  const ctx = canvas.getContext('2d')
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
}

function draw() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')

  const w = state.w
  const h = state.h
  state.t += 0.012

  ctx.clearRect(0, 0, w, h)

  const g = ctx.createRadialGradient(w * 0.5, h * 0.45, 0, w * 0.5, h * 0.45, Math.max(w, h) * 0.7)
  g.addColorStop(0, 'rgba(16, 20, 32, 1)')
  g.addColorStop(1, 'rgba(6, 8, 14, 1)')
  ctx.fillStyle = g
  ctx.fillRect(0, 0, w, h)

  const count = 70
  for (let i = 0; i < count; i++) {
    const a = (i / count) * Math.PI * 2 + state.t * 0.15
    const r = Math.min(w, h) * (0.12 + (i % 10) * 0.01)
    const x = w * 0.5 + Math.cos(a * 1.7) * r
    const y = h * 0.45 + Math.sin(a * 1.3) * r

    ctx.fillStyle = `rgba(120, 200, 255, ${0.03 + (i % 7) * 0.004})`
    ctx.beginPath()
    ctx.arc(x, y, 1.2 + (i % 5) * 0.25, 0, Math.PI * 2)
    ctx.fill()
  }

  rafId = requestAnimationFrame(draw)
}

function go(domain) {
  router.push(`/database-manage/opto-knowledge/${domain}`)
}

function orbStyle(i) {
  const base = [
    { x: 0.28, y: 0.35 },
    { x: 0.68, y: 0.32 },
    { x: 0.30, y: 0.68 },
    { x: 0.70, y: 0.68 }
  ][i]

  const dx = Math.sin(state.t * 1.3 + i) * 18
  const dy = Math.cos(state.t * 1.1 + i * 1.7) * 14

  return {
    left: `calc(${base.x * 100}% + ${dx}px)`,
    top: `calc(${base.y * 100}% + ${dy}px)`
  }
}

onMounted(() => {
  resize()
  window.addEventListener('resize', resize)
  rafId = requestAnimationFrame(draw)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  if (rafId) cancelAnimationFrame(rafId)
})
</script>

<style scoped>
.ok-entry {
  position: relative;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}

.bg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.orbs {
  position: absolute;
  inset: 0;
}

.orb {
  position: absolute;
  transform: translate(-50%, -50%);
  width: 168px;
  height: 168px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(225, 245, 255, 0.92);
  letter-spacing: 2px;
  font-weight: 600;
  cursor: pointer;
  user-select: none;
  background: radial-gradient(circle at 30% 30%, rgba(140, 240, 255, 0.25), rgba(50, 90, 160, 0.12) 55%, rgba(10, 14, 22, 0.1) 100%);
  border: 1px solid rgba(130, 220, 255, 0.25);
  box-shadow:
    0 0 24px rgba(80, 200, 255, 0.18),
    inset 0 0 24px rgba(80, 200, 255, 0.12);
  transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease;
}

.orb:hover {
  transform: translate(-50%, -50%) scale(1.06);
  border-color: rgba(170, 255, 255, 0.45);
  box-shadow:
    0 0 34px rgba(80, 200, 255, 0.32),
    inset 0 0 34px rgba(80, 200, 255, 0.16);
}
</style>
