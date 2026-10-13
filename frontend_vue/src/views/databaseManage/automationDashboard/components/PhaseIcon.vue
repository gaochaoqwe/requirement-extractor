<template>
  <div class="phase-icon-wrap" :style="{ '--ic': color || '#4fc3f7' }">
    <svg v-if="icon === 'doc'" viewBox="0 0 24 24" fill="none">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" stroke="var(--ic)" stroke-width="1.8" stroke-linejoin="round"/>
      <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" stroke="var(--ic)" stroke-width="1.6" stroke-linecap="round"/>
    </svg>
    <svg v-else-if="icon === 'analysis'" viewBox="0 0 24 24" fill="none">
      <rect x="3" y="3" width="7" height="7" rx="1" stroke="var(--ic)" stroke-width="1.8"/>
      <rect x="14" y="3" width="7" height="7" rx="1" stroke="var(--ic)" stroke-width="1.8"/>
      <rect x="3" y="14" width="7" height="7" rx="1" stroke="var(--ic)" stroke-width="1.8"/>
      <path d="M17.5 14v7M14 17.5h7" stroke="var(--ic)" stroke-width="1.8" stroke-linecap="round"/>
    </svg>
    <svg v-else-if="icon === 'code'" viewBox="0 0 24 24" fill="none">
      <polyline points="16 18 22 12 16 6" stroke="var(--ic)" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
      <polyline points="8 6 2 12 8 18" stroke="var(--ic)" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    <svg v-else-if="icon === 'dynamic'" viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="9" stroke="var(--ic)" stroke-width="1.8"/>
      <path d="M12 7v5l3 3" stroke="var(--ic)" stroke-width="1.8" stroke-linecap="round"/>
    </svg>
    <svg v-else-if="icon === 'report'" viewBox="0 0 24 24" fill="none">
      <path d="M9 17H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2h-2" stroke="var(--ic)" stroke-width="1.8" stroke-linecap="round"/>
      <rect x="9" y="17" width="6" height="4" rx="1" stroke="var(--ic)" stroke-width="1.8"/>
      <path d="M9 9h6M9 12h4" stroke="var(--ic)" stroke-width="1.6" stroke-linecap="round"/>
    </svg>
    <svg v-else viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="9" stroke="var(--ic)" stroke-width="1.8"/>
    </svg>
  </div>
</template>

<script setup>
defineProps({
  icon: String,
  color: String,
})
</script>

<style scoped>
.phase-icon-wrap {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.phase-icon-wrap svg {
  width: 20px;
  height: 20px;
}
</style>
