<template>
  <div class="seven-pane">
    <div class="toolbar">
      <el-input
        v-model="filters.softwareCategory"
        placeholder="按软件类别筛选"
        size="small"
        clearable
        style="width: 180px; margin-right: 8px;"
        @keyup.enter.native="fetchData"
        @clear="onFilterChange"
      />
      <el-input
        v-model="filters.testItemName"
        placeholder="按测试项名称筛选"
        size="small"
        clearable
        style="width: 180px; margin-right: 8px;"
        @keyup.enter.native="fetchData"
        @clear="onFilterChange"
      />
      <el-button size="small" type="primary" @click="fetchData">查询</el-button>
      <el-button size="small" @click="resetFilters">重置</el-button>
      <el-button size="small" @click="forceRefresh" :loading="loading" icon="Refresh">刷新</el-button>
      <div style="flex: 1"></div>
      <el-button size="small" @click="onExport" :loading="exporting">导出Excel</el-button>
    </div>

    <div class="table-wrapper">
      <el-table 
        :data="rows" 
        v-loading="loading" 
        size="small" 
        border
        height="100%"
      >
      <el-table-column prop="software_category" label="软件类别" width="140" />
      <el-table-column prop="test_item_name" label="测试项名称" width="200" />
      <el-table-column prop="test_content" label="测试内容" min-width="260" show-overflow-tooltip />
      <el-table-column prop="test_method" label="测试方法" min-width="240" show-overflow-tooltip />
      <el-table-column prop="case_template_name" label="用例模板（用例名称）" min-width="200" show-overflow-tooltip />
      <el-table-column prop="case_template_input" label="用例模板（输入条件）" min-width="220" show-overflow-tooltip />
      <el-table-column prop="case_template_expected" label="用例模板（预期结果）" min-width="220" show-overflow-tooltip />
      <el-table-column prop="submitter" label="提交人" width="120" />
      </el-table>
    </div>

    <!-- 分页组件 -->
    <div class="pager" v-show="shouldShowPagination">
      <el-pagination
        v-if="total > 0"
        background
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        :current-page="page"
        :page-size="pageSize"
        @current-change="handlePageChange"
        @size-change="handleSizeChange"
        :hide-on-single-page="false"
        size="small"
        class="pagination-component"
      />
      <!-- 空表状态显示 -->
      <div v-else class="empty-pagination" style="text-align: center; padding: 16px; color: #909399; font-size: 14px;">
        <div v-if="loading">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span style="margin-left: 8px;">加载中...</span>
        </div>
        <div v-else>
          <div style="margin-bottom: 8px;">
            📋 {{ props.table }}表暂无数据
          </div>
          <div style="font-size: 12px; color: #c0c4cc; margin-bottom: 12px;">
            请使用上方的"导入Excel"功能导入数据
          </div>
          <el-button size="small" type="primary" @click="forceRefresh">
            重新加载
          </el-button>
        </div>
      </div>
    </div>
    

  </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import { databaseManageService } from '@/services/databaseManageService'

const props = defineProps({
  table: { type: String, required: true }
})

const rows = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const loading = ref(false)
const exporting = ref(false)

const filters = reactive({ 
  softwareCategory: '',
  testItemName: ''
})

// 🚀 生产环境调试：组件初始化检查
console.log('🏗️ SevenColsPane组件初始化:', {
  props: props,
  table: props.table,
  rowsType: typeof rows.value,
  rowsIsArray: Array.isArray(rows.value),
  environment: import.meta.env.MODE
})

// 计算属性：控制分页组件显示
const shouldShowPagination = computed(() => {
  // 始终显示分页组件，提供一致的用户体验
  return true
})

async function fetchData(retryCount = 0) {
  try {
    loading.value = true
    
    // 🚀 优化1: 添加超时控制
    const controller = new AbortController()
    const timeoutId = setTimeout(() => {
      controller.abort()
    }, 30000) // 30秒超时
    
    try {
      const res = await databaseManageService.listSevenCols({
        table: props.table,
        page: page.value,
        pageSize: pageSize.value,
        softwareCategory: filters.softwareCategory || undefined,
        testItemName: filters.testItemName || undefined
      }, { signal: controller.signal })
      
      clearTimeout(timeoutId)
      
      // 🚀 修复生产环境数据类型错误：强制数据验证和类型检查
      console.log('📊 API响应数据结构:', {
        responseType: typeof res,
        dataType: typeof res.data,
        dataIsArray: Array.isArray(res.data),
        dataLength: res.data?.length,
        fullResponse: res
      })
      
      // 强制确保 rows.value 始终是数组
      let responseData = res.data
      if (!Array.isArray(responseData)) {
        console.warn('⚠️ API返回的data不是数组，尝试修复:', responseData)
        
        // 如果是对象且包含数组属性，尝试提取
        if (responseData && typeof responseData === 'object') {
          if (Array.isArray(responseData.items)) {
            responseData = responseData.items
          } else if (Array.isArray(responseData.records)) {
            responseData = responseData.records
          } else if (Array.isArray(responseData.data)) {
            responseData = responseData.data
          } else {
            responseData = []
          }
        } else {
          responseData = []
        }
      }
      
      rows.value = responseData || []
      console.log('✅ 设置rows.value:', rows.value.length, '条记录')
      
      // 获取总数
      const totalHeader = res.headers?.['x-total-count'] || res.headers?.['X-Total-Count']
      let totalCount = 0
      
      if (totalHeader) {
        totalCount = Number(totalHeader)
      } else if (rows.value.length > 0) {
        // 如果没有总数头，但有数据，估算总数
        totalCount = Math.max(rows.value.length, pageSize.value * page.value)
      } else {
        // 如果当前total大于0，保持原值，避免分页组件消失
        if (total.value > 0) {
          totalCount = total.value
        } else {
          totalCount = 0
        }
      }
      
      // 只有在获取到有效总数时才更新total
      if (totalCount > 0 || total.value === 0) {
        total.value = totalCount
      }
      
    } catch (fetchError) {
      clearTimeout(timeoutId)
      throw fetchError
    }
    
  } catch (e) {
    console.error('❌ 数据加载失败:', e)
    
    // 🚀 优化2: 更友好的错误提示
    let errorMessage = '加载失败'
    if (e.name === 'AbortError') {
      errorMessage = '请求超时，请稍后重试'
    } else if (e.response?.status === 504) {
      errorMessage = '服务器响应超时，请稍后重试'
    } else if (e.response?.status === 500) {
      errorMessage = '服务器内部错误，请联系管理员'
    } else if (e.message) {
      errorMessage = e.message
    }
    
    ElMessage.error(errorMessage)
    
    // 自动重试机制
    if (retryCount < 2 && !e.name === 'AbortError') {
      setTimeout(() => {
        fetchData(retryCount + 1)
      }, 1000 * (retryCount + 1)) // 递增延迟
      return
    }
    
    // 重试失败后，清空数据但保持分页状态
    rows.value = []
    
  } finally {
    loading.value = false
  }
}

function onFilterChange() { page.value = 1; fetchData() }
function resetFilters() { 
  filters.softwareCategory = ''
  filters.testItemName = ''
  onFilterChange() 
}
function forceRefresh() { 
  // 重置total以确保重新获取
  total.value = 0
  fetchData() 
}

function handlePageChange(newPage) {
  page.value = newPage
  fetchData()
}

function handleSizeChange(newSize) {
  pageSize.value = newSize
  page.value = 1
  fetchData()
}

async function onExport() {
  try {
    exporting.value = true
    const res = await databaseManageService.exportSevenCols({
      table: props.table,
      softwareCategory: filters.softwareCategory || undefined,
      testItemName: filters.testItemName || undefined
    })
    const blob = new Blob([res.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${props.table}_七列需求.xlsx`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  } catch (e) {
    ElMessage.error('导出失败：' + e.message)
  } finally {
    exporting.value = false
  }
}

watch(() => [props.table], () => {
  page.value = 1
  fetchData()
})

onMounted(fetchData)
</script>

<style scoped>
.seven-pane { 
  margin-top: 12px; 
  display: flex;
  flex-direction: column;
  height: 100%; /* 🚀 使用100%高度，依赖父容器的flex布局 */
  min-height: 0; /* 🚀 允许flex子项收缩 */
}
.toolbar { 
  display: flex; 
  align-items: center; 
  margin-bottom: 8px; 
  flex-shrink: 0; /* 🚀 工具栏不缩放 */
}
.pager { 
  display: flex; 
  justify-content: center; /* 居中显示，避免截断 */
  margin-top: 16px;
  padding: 8px 16px; /* 增加左右内边距 */
  min-height: 40px;
  flex-shrink: 0; /* 🚀 分页组件不缩放，始终可见 */
  background: white; /* 🚀 确保背景色 */
  overflow-x: auto; /* 当宽度不足时允许横向滚动 */
  overflow-y: hidden;
}

/* 分页组件响应式优化 */
.pagination-component {
  min-width: fit-content; /* 确保分页组件有足够宽度 */
  flex-shrink: 0;
}

/* 小屏幕下的分页优化 */
@media (max-width: 1200px) {
  .pager {
    justify-content: flex-start; /* 小屏幕下左对齐，避免右侧被截断 */
    padding: 8px 8px;
  }
}

@media (max-width: 800px) {
  .pagination-component {
    /* 在极小屏幕下简化分页布局 */
    --el-pagination-font-size: 12px;
  }
  
  .pagination-component :deep(.el-pagination__sizes) {
    margin-right: 5px; /* 减少间距 */
  }
  
  .pagination-component :deep(.el-pagination__jump) {
    margin-left: 5px; /* 减少间距 */
  }
}
/* 🚀 表格容器样式 */
.table-wrapper {
  flex: 1; /* 🚀 表格包装器占用剩余空间 */
  overflow: hidden; /* 🚀 防止溢出 */
  margin-bottom: 8px;
}
.el-table {
  height: 100%; /* 🚀 表格填满包装器 */
}
</style>
