<template>
  <div class="static-analysis">
    <div class="view-switch-container">
      <el-segmented v-model="currentView" :options="viewOptions" size="large" />
    </div>

    <div v-show="currentView === 'analysis'" class="analysis-panel">
      <div class="mode-switch mode-switch--analysis">
        <el-segmented v-model="analysisMode" :options="analysisOptions" size="large" />
      </div>
      <component :is="analysisMode === 'c' ? NormalModeC : NormalModeFpga" />
    </div>

    <div v-show="currentView === 'filter'" class="filter-panel">
      <div class="mode-switch">
        <el-segmented v-model="filterMode" :options="filterOptions" size="large" />
      </div>
      <component :is="filterMode === 'c' ? StaticAnalysisFilter : FpgaFilter" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { deployConfig } from '@/config/deployConfig'
import StaticAnalysisFilter from './filter/StaticAnalysisFilter.vue'
import FpgaFilter from './filterFpga/StaticAnalysisFilter.vue'
import NormalModeC from './normalModeC/StaticAnalysisNormal.vue'
import NormalModeFpga from './normalModeFpga/StaticAnalysisNormal.vue'

const currentView = ref(deployConfig.staticAnalysisDefaultView)
const viewOptions = deployConfig.staticAnalysisViewOptions

const filterMode = ref(deployConfig.staticAnalysisDefaultLang)
const filterOptions = [
  { label: 'C语言', value: 'c' },
  { label: 'FPGA', value: 'fpga' }
]

const analysisMode = ref(deployConfig.staticAnalysisDefaultLang)
const analysisOptions = [
  { label: 'C语言', value: 'c' },
  { label: 'FPGA', value: 'fpga' }
]
</script>

<style scoped>
.static-analysis {
  padding: 20px;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
  background: linear-gradient(180deg, #f3f7fc 0%, #eef4fb 100%);
}

.view-switch-container {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
  padding: 16px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(15, 40, 80, 0.08);
}

.mode-switch {
  display: flex;
  justify-content: center;
  margin-bottom: 16px;
}

.mode-switch--analysis {
  margin-bottom: 20px;
}

.analysis-panel,
.filter-panel {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 8px 32px rgba(32, 101, 209, 0.08);
}
</style>
