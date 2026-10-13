<template>
  <div class="catalog-extraction-section">
    <!-- 等待上传状态 -->
    <div v-if="!uploaded" class="catalog-waiting">
      <div class="waiting-content">
        <el-icon class="waiting-icon"><Document /></el-icon>
        <span class="waiting-text">请先上传需求规格说明文档</span>
      </div>
    </div>

    <!-- 需求提取界面 -->
    <div v-else>
      <!-- 提取按钮（等待状态） -->
      <div class="catalog-extract-actions" v-if="status === 'waiting'">
        <el-button type="primary" @click="extract" :loading="extracting">
          <el-icon><Search /></el-icon>
          {{ extracting ? '正在提取需求目录...' : '提取测试需求目录' }}
        </el-button>
      </div>

      <!-- 已提取状态显示 -->
      <div v-else-if="status === 'extracted'" class="catalog-extracted">
        <div class="catalog-header">
          <el-icon class="status-icon success"><CircleCheckFilled /></el-icon>
          <span class="status-text">已提取 {{ totalItems }} 个测试需求项</span>
          <div class="catalog-actions">
            <el-button size="small" type="success" @click="quickConfirm">
              确认需求
            </el-button>
            <el-button size="small" type="primary" @click="enableEdit">
              编辑需求
            </el-button>
            <el-button size="small" type="default" @click="reExtract">
              重新提取
            </el-button>
          </div>
        </div>

        <!-- 级别选择器 -->
        <div class="level-selector">
          <span class="level-label">显示级别：</span>
          <el-select 
            v-model="innerFilter" 
            size="small" 
            style="width: 100px;"
            @change="updateFilter">
            <el-option label="3级" value="3" />
            <el-option label="4级" value="4" />
            <el-option label="5级" value="5" />
            <el-option label="6级" value="6" />
            <el-option label="全部" value="all" />
          </el-select>
          <span class="level-description">
            (显示{{ innerFilter === 'all' ? '全部' : (innerFilter === '3' ? '所有3级' : '≤' + innerFilter + '级叶子节点') }}需求：{{ filteredCount }}项)
          </span>
        </div>

        <!-- 用户说明 -->
        <div class="user-tips">
          <el-icon class="tip-icon"><InfoFilled /></el-icon>
          <span class="tip-text">
            <strong>说明：</strong>考虑到带子章节的需求一般都不进行测试，仅对其子章节进行测试，因此4级及以上级别选择时不显示有子章节的需求项，只显示具体可测试的叶子节点需求。
          </span>
        </div>

        <!-- 需求列表预览 -->
        <div class="catalog-preview-content">
          <pre>{{ displayedCatalog }}</pre>
        </div>
      </div>

      <!-- 其他状态（失败/已确认等）按需在父级显示，这里保持简化 -->
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Document, Search, CircleCheckFilled, InfoFilled } from '@element-plus/icons-vue'

const props = defineProps({
  uploaded: { type: Boolean, default: false },
  status: { type: String, default: 'waiting' },
  totalItems: { type: Number, default: 0 },
  catalogLevelFilter: { type: [String, Number], default: 'all' },
  filteredCount: { type: Number, default: 0 },
  displayedCatalog: { type: String, default: '' },
  extracting: { type: Boolean, default: false },
  // 事件回调（从父级传入函数）
  extract: { type: Function, required: true },
  quickConfirm: { type: Function, required: true },
  enableEdit: { type: Function, required: true },
  reExtract: { type: Function, required: true },
  updateCatalogFilter: { type: Function, required: true }
})

const innerFilter = ref(String(props.catalogLevelFilter))
watch(() => props.catalogLevelFilter, v => innerFilter.value = String(v))

function updateFilter() {
  props.updateCatalogFilter(innerFilter.value)
}
</script>

<style scoped>
.catalog-extraction-section { margin-top: 10px; }
.catalog-header { display: flex; align-items: center; justify-content: space-between; }
.catalog-actions { display: flex; gap: 8px; }
.level-selector { margin: 10px 0; display: flex; align-items: center; gap: 8px; }
.level-label { font-size: 14px; font-weight: 500; color: #374151; }
.level-description { font-size: 12px; color: #6b7280; margin-left: 8px; }
.user-tips { display: flex; align-items: flex-start; margin: 10px 0; padding: 12px; background: #f0f9ff; border: 1px solid #bfdbfe; border-radius: 6px; color: #1e40af; font-size: 13px; line-height: 1.5; }
.tip-icon { margin-right: 8px; margin-top: 2px; color: #3b82f6; flex-shrink: 0; }
.catalog-preview-content pre { white-space: pre-wrap; }
</style>
