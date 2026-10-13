<template>
  <svg :width="size" :height="size" :viewBox="`0 0 ${size} ${size}`">
    <defs>
      <linearGradient :id="`gaugeBg${uid}`" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#1e293b"/>
        <stop offset="100%" stop-color="#0f172a"/>
      </linearGradient>
      <linearGradient :id="`gaugeGrad${uid}`" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%" stop-color="#4fc3f7"/>
        <stop offset="60%" stop-color="#818cf8"/>
        <stop offset="100%" stop-color="#a78bfa"/>
      </linearGradient>
    </defs>
    <!-- bg circle -->
    <circle :cx="cx" :cy="cy" :r="r" fill="none"
      stroke="#1e293b" :stroke-width="sw" />
    <!-- track -->
    <circle :cx="cx" :cy="cy" :r="r" fill="none"
      stroke="rgba(79,195,247,0.08)" :stroke-width="sw" />
    <!-- progress arc -->
    <circle
      :cx="cx" :cy="cy" :r="r"
      fill="none"
      :stroke="`url(#gaugeGrad${uid})`"
      :stroke-width="sw"
      :stroke-dasharray="`${arcLen} ${circumference}`"
      :stroke-dashoffset="dashOffset"
      stroke-linecap="round"
      :transform="`rotate(-90 ${cx} ${cy})`"
      style="transition: stroke-dasharray 1.2s cubic-bezier(0.4,0,0.2,1)"
    />
    <!-- glow ring -->
    <circle :cx="cx" :cy="cy" :r="r" fill="none"
      stroke="rgba(79,195,247,0.05)" :stroke-width="sw + 8" />
    <!-- center text -->
    <text :x="cx" :y="cy - 6" text-anchor="middle" fill="#94a3b8" font-size="11">自动化</text>
    <text :x="cx" :y="cy + 18" text-anchor="middle"
      fill="url(#gaugeGrad1)" font-size="22" font-weight="800">
      {{ value.toFixed(0) }}%
    </text>
  </svg>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  value: { type: Number, default: 0 },
  size: { type: Number, default: 110 },
})

const uid = Math.random().toString(36).slice(2, 7)
const sw = 10
const cx = computed(() => props.size / 2)
const cy = computed(() => props.size / 2)
const r = computed(() => props.size / 2 - sw / 2 - 4)
const circumference = computed(() => 2 * Math.PI * r.value)
const arcLen = computed(() => (props.value / 100) * circumference.value)
const dashOffset = computed(() => 0)
</script>
