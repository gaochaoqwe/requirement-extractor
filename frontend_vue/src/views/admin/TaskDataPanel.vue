<template>
  <div class="admin-data-panel">
    <div class="page-header">
      <div class="header-left">
        <h1>管理员 · 任务数据面板</h1>
        <el-tag type="danger" size="large">管理员模式</el-tag>
      </div>
      <div class="header-right">
        <el-button @click="goTaskManager">返回任务管理中心</el-button>
      </div>
    </div>

    <!-- 测试类型切换：配置项测试 / 回归测试 -->
    <el-card class="test-mode-card">
      <div class="mode-switch-row">
        <div class="mode-label">
          <span>测试类型：</span>
        </div>
        <el-segmented v-model="testMode" :options="testModeOptions" :props="{ label: 'label', value: 'value' }" size="large" @change="handleTestModeChange" />
        <div class="mode-description">
          <el-tag :type="testMode === 'configuration' ? 'success' : 'warning'">
            {{ testMode === 'configuration' ? '配置项测试' : '回归测试' }}
          </el-tag>
        </div>
      </div>
    </el-card>

    <!-- 分析类型切换：代码审查 / 静态分析C/C++ / 静态分析FPGA -->
    <el-card class="mode-card">
      <div class="mode-switch-row">
        <el-radio-group v-model="activeMode" @change="handleModeChange">
          <el-radio-button label="code_review_function">代码审查（函数）</el-radio-button>
          <el-radio-button label="static_c">静态分析 C/C++</el-radio-button>
          <el-radio-button label="static_fpga">静态分析 FPGA</el-radio-button>
          <el-radio-button label="test_case_summary">测试工具</el-radio-button>
        </el-radio-group>
        <div class="mode-actions">
          <el-button @click="refresh" :loading="loading">刷新</el-button>
          <el-button type="success" :disabled="selectedTasks.length === 0 || activeMode !== 'code_review_function'" @click="exportSelected">导出勾选任务信息</el-button>
          <el-button type="primary" :loading="exportingAll" @click="exportAllData">导出全部数据</el-button>
        </div>
      </div>
    </el-card>

    <!-- 代码审查 · 函数审查数据表格 -->
    <template v-if="activeMode === 'code_review_function'">
      <el-card class="filter-card">
        <div class="filter-row">
          <div class="filter-left">
            <el-radio-group v-model="statusFilter" @change="refresh">
              <el-radio-button label="all">全部状态</el-radio-button>
              <el-radio-button label="completed">已完成</el-radio-button>
              <el-radio-button label="processing">执行中</el-radio-button>
            </el-radio-group>
          </div>
        </div>
      </el-card>

      <el-card class="table-card">
        <el-table
          v-loading="loading"
          :data="pagedTasks"
          border
          style="width: 100%"
          @selection-change="handleSelectionChange"
        >
          <el-table-column type="selection" width="55" />
          <el-table-column prop="id" label="任务ID" width="90" />
          <!-- 核心指标列：突出显示 -->
          <el-table-column prop="accuracy" label="问题检出准确率" width="130" class-name="highlight-column">
            <template #header>
              <span class="highlight-header">问题检出准确率</span>
            </template>
            <template #default="scope">
              <span class="highlight-value" :class="getHighlightClass(scope.row.accuracy)">
                {{ formatAccuracy(scope.row.accuracy) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="comment_accuracy_rate" label="注释准确率" width="120" class-name="highlight-column">
            <template #header>
              <span class="highlight-header">注释准确率</span>
            </template>
            <template #default="scope">
              <span v-if="scope.row.comment_accuracy_rate" class="highlight-value blue">
                {{ scope.row.comment_accuracy_rate }}
              </span>
              <span v-else class="text-gray">-</span>
            </template>
          </el-table-column>
          <el-table-column prop="total_problems" label="总问题数" width="100" />
          <el-table-column prop="effective_total_problems" label="有效问题数" width="100">
            <template #header>
              <el-tooltip content="总问题数减去算法自动过滤的问题数">
                <span>有效问题数</span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="marked_problem_count" label="标记问题数量" width="110" />
          <el-table-column prop="has_marked_problems" label="是否有标记问题" width="120">
            <template #default="scope">
              <el-tag :type="scope.row.has_marked_problems ? 'success' : 'info'">
                {{ scope.row.has_marked_problems ? '是' : '否' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="marked_problems_exported" label="是否导出过标记问题" width="180">
            <template #default="scope">
              <el-tag :type="scope.row.marked_problems_exported ? 'success' : 'warning'">
                {{ scope.row.marked_problems_exported ? '是' : '否' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="tester_name" label="人员名称" width="120" />
          <el-table-column prop="updated_at" label="最近日期" width="130">
            <template #default="scope">
              {{ formatDate(scope.row.updated_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="scope">
              <el-button type="primary" size="small" @click="exportMarked(scope.row)">
                导出标记问题
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="table-pagination-wrapper">
          <el-pagination
            background
            layout="total, prev, pager, next, jumper"
            :current-page="currentPage"
            :page-size="pageSize"
            :total="filteredTasksAll.length"
            @current-change="handlePageChange"
          />
        </div>
      </el-card>
    </template>

    <!-- 静态分析 C/C++ 数据面板 -->
    <template v-else-if="activeMode === 'static_c'">
      <el-card class="filter-card">
        <div class="filter-row">
          <div class="filter-left">
            <el-radio-group v-model="statusFilter" @change="refresh">
              <el-radio-button label="all">全部状态</el-radio-button>
              <el-radio-button label="completed">已完成</el-radio-button>
              <el-radio-button label="processing">执行中</el-radio-button>
              <el-radio-button label="pending">等待中</el-radio-button>
              <el-radio-button label="error">错误</el-radio-button>
            </el-radio-group>
          </div>
        </div>
      </el-card>

      <el-card class="table-card">
        <el-table
          v-loading="loading"
          :data="pagedStaticTasks"
          border
          style="width: 100%"
        >
          <el-table-column prop="id" label="任务ID" width="90" />
          <!-- 核心指标列：突出显示 -->
          <el-table-column prop="accuracy" label="问题检出准确率" width="130" class-name="highlight-column">
            <template #header>
              <span class="highlight-header">问题检出准确率</span>
            </template>
            <template #default="scope">
              <span class="highlight-value" :class="getHighlightClass(scope.row.accuracy)">
                {{ formatAccuracy(scope.row.accuracy) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="problem_sheet_accuracy_rate" label="问题单准确率" width="120" class-name="highlight-column">
            <template #header>
              <span class="highlight-header">问题单准确率</span>
            </template>
            <template #default="scope">
              <span v-if="scope.row.problem_sheet_accuracy_rate" class="highlight-value blue">
                {{ scope.row.problem_sheet_accuracy_rate }}
              </span>
              <span v-else class="text-gray">-</span>
            </template>
          </el-table-column>
          <el-table-column prop="total_four_category" label="总问题数" width="100" />
          <el-table-column prop="filtered_problems_count" label="有效问题数" width="100">
            <template #header>
              <el-tooltip content="确定勾选 + 不确定勾选中AI确认的问题数">
                <span>有效问题数</span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="marked_problem_count" label="标记问题数量" width="110" />
          <el-table-column prop="has_marked_problems" label="是否有标记问题" width="120">
            <template #default="scope">
              <el-tag :type="scope.row.has_marked_problems ? 'success' : 'info'">
                {{ scope.row.has_marked_problems ? '是' : '否' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="marked_problems_exported" label="是否导出过标记问题" width="180">
            <template #default="scope">
              <el-tag :type="scope.row.marked_problems_exported ? 'success' : 'warning'">
                {{ scope.row.marked_problems_exported ? '是' : '否' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="operator_name" label="人员名称" width="120" />
          <el-table-column prop="latest_marked_at" label="最近日期" width="130">
            <template #default="scope">
              {{ scope.row.latest_marked_at ? formatDateTime(scope.row.latest_marked_at) : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="scope">
              <el-button type="primary" size="small" @click="exportMarkedProblems(scope.row, 'static_c')">
                导出标记问题
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="table-pagination-wrapper">
          <el-pagination
            background
            layout="total, prev, pager, next, jumper"
            :current-page="currentPage"
            :page-size="pageSize"
            :total="filteredStaticTasks.length"
            @current-change="handlePageChange"
          />
        </div>
      </el-card>
    </template>

    <!-- 静态分析 FPGA 数据面板 -->
    <template v-else-if="activeMode === 'static_fpga'">
      <el-card class="filter-card">
        <div class="filter-row">
          <div class="filter-left">
            <el-radio-group v-model="statusFilter" @change="refresh">
              <el-radio-button label="all">全部状态</el-radio-button>
              <el-radio-button label="completed">已完成</el-radio-button>
              <el-radio-button label="processing">执行中</el-radio-button>
              <el-radio-button label="pending">等待中</el-radio-button>
              <el-radio-button label="error">错误</el-radio-button>
            </el-radio-group>
          </div>
        </div>
      </el-card>

      <el-card class="table-card">
        <el-table
          v-loading="loading"
          :data="pagedFpgaTasks"
          border
          style="width: 100%"
        >
          <el-table-column prop="id" label="任务ID" width="80" />
          <!-- 核心指标列：问题检出准确率 -->
          <el-table-column prop="accuracy" label="问题检出准确率" width="130" class-name="highlight-column">
            <template #header>
              <span class="highlight-header">问题检出准确率</span>
            </template>
            <template #default="scope">
              <span class="highlight-value" :class="getHighlightClass(scope.row.accuracy)">
                {{ formatAccuracy(scope.row.accuracy) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="problem_sheet_accuracy_rate" label="问题单准确率" width="120" class-name="highlight-column">
            <template #header>
              <span class="highlight-header">问题单准确率</span>
            </template>
            <template #default="scope">
              <span v-if="scope.row.problem_sheet_accuracy_rate" class="highlight-value blue">
                {{ scope.row.problem_sheet_accuracy_rate }}
              </span>
              <span v-else class="text-gray">-</span>
            </template>
          </el-table-column>
          <el-table-column prop="total_four_category" label="总问题数" width="100" />
          <el-table-column prop="filtered_problems_count" label="有效问题数" width="100">
            <template #header>
              <el-tooltip content="确定勾选 + 不确定勾选中AI确认的问题数">
                <span>有效问题数</span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="marked_problem_count" label="标记问题数量" width="110" />
          <el-table-column prop="has_marked_problems" label="是否有标记问题" width="120">
            <template #default="scope">
              <el-tag :type="scope.row.has_marked_problems ? 'success' : 'info'">
                {{ scope.row.has_marked_problems ? '是' : '否' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="marked_problems_exported" label="是否导出过标记问题" width="180">
            <template #default="scope">
              <el-tag :type="scope.row.marked_problems_exported ? 'success' : 'warning'">
                {{ scope.row.marked_problems_exported ? '是' : '否' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="operator_name" label="人员名称" width="120" />
          <el-table-column prop="latest_marked_at" label="最近日期" width="130">
            <template #default="scope">
              {{ scope.row.latest_marked_at ? formatDateTime(scope.row.latest_marked_at) : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="scope">
              <el-button type="primary" size="small" @click="exportMarkedProblems(scope.row, 'static_fpga')">
                导出标记问题
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="table-pagination-wrapper">
          <el-pagination
            background
            layout="total, prev, pager, next, jumper"
            :current-page="currentPage"
            :page-size="pageSize"
            :total="filteredFpgaTasks.length"
            @current-change="handlePageChange"
          />
        </div>
      </el-card>
    </template>
    <!-- 测试工具 · 测试用例总结数据面板 -->
    <template v-else-if="activeMode === 'test_case_summary'">
      <el-card class="table-card">
        <el-table
          v-loading="loading"
          :data="pagedTestToolTasks"
          border
          style="width: 100%"
        >
          <el-table-column prop="id" label="任务ID" width="90" />
          <el-table-column prop="original_filename" label="上传文件" min-width="200" show-overflow-tooltip />
          <el-table-column prop="total_test_items" label="测试项个数" width="110" class-name="highlight-column">
            <template #header>
              <span class="highlight-header">测试项个数</span>
            </template>
            <template #default="scope">
              <span class="highlight-value good">{{ scope.row.total_test_items }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="scope">
              <el-tag :type="getTestToolStatusType(scope.row.status)">
                {{ getTestToolStatusText(scope.row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="tester_name" label="人员名称" width="120">
            <template #default="scope">
              {{ scope.row.tester_name || '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="最近日期" width="160">
            <template #default="scope">
              {{ scope.row.updated_at ? formatDateTime(scope.row.updated_at) : formatDateTime(scope.row.created_at) }}
            </template>
          </el-table-column>
        </el-table>

        <div class="table-pagination-wrapper">
          <el-pagination
            background
            layout="total, prev, pager, next, jumper"
            :current-page="currentPage"
            :page-size="pageSize"
            :total="testToolTasks.length"
            @current-change="handlePageChange"
          />
        </div>
      </el-card>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import testCaseSummaryService from '@/services/testCaseSummaryService'

const router = useRouter()

// 测试模式切换
const testMode = ref('configuration') // 'configuration' | 'regression'
const testModeOptions = [
  { label: '配置项测试', value: 'configuration' },
  { label: '回归测试', value: 'regression' }
]

const tasks = ref([])
const staticTasks = ref([])  // 静态分析C/C++任务
const fpgaTasks = ref([])    // 静态分析FPGA任务
const testToolTasks = ref([]) // 测试工具任务
const loading = ref(false)
const exportingAll = ref(false)
const statusFilter = ref('all')
const selectedTasks = ref([])

// 分页相关
const currentPage = ref(1)
const pageSize = ref(20)

// 分析模式：代码审查函数 / 静态分析 C/C++ / 静态分析 FPGA
const activeMode = ref('code_review_function')
const modeOptions = [
  { label: '代码审查（函数）', value: 'code_review_function' },
  { label: '静态分析 C/C++', value: 'static_c' },
  { label: '静态分析 FPGA', value: 'static_fpga' }
]

const filteredTasksAll = computed(() => {
  // 不过滤 analysis_type，显示所有任务（因为都是代码审查任务）
  let result = tasks.value
  if (statusFilter.value === 'completed') {
    result = result.filter(t => t.status === 'completed')
  } else if (statusFilter.value === 'processing') {
    result = result.filter(t => t.status === 'processing' || t.status === 'pending')
  }
  console.log(`[过滤后] 共 ${result.length} 个任务`)
  return result
})

const pagedTasks = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredTasksAll.value.slice(start, end)
})

// 静态分析C/C++任务过滤和分页
const filteredStaticTasks = computed(() => {
  let result = staticTasks.value
  if (statusFilter.value === 'completed') {
    result = result.filter(t => t.status === 'completed')
  } else if (statusFilter.value === 'processing') {
    result = result.filter(t => t.status === 'processing' || t.status === 'ai_analyzing')
  } else if (statusFilter.value === 'pending') {
    result = result.filter(t => t.status === 'pending')
  } else if (statusFilter.value === 'error') {
    result = result.filter(t => t.status === 'error')
  }
  return result
})

const pagedStaticTasks = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredStaticTasks.value.slice(start, end)
})

// 静态分析FPGA任务过滤和分页（暂时使用相同数据，后续可分离）
const filteredFpgaTasks = computed(() => {
  let result = fpgaTasks.value
  if (statusFilter.value === 'completed') {
    result = result.filter(t => t.status === 'completed')
  } else if (statusFilter.value === 'processing') {
    result = result.filter(t => t.status === 'processing' || t.status === 'ai_analyzing')
  } else if (statusFilter.value === 'pending') {
    result = result.filter(t => t.status === 'pending')
  } else if (statusFilter.value === 'error') {
    result = result.filter(t => t.status === 'error')
  }
  return result
})

const pagedFpgaTasks = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredFpgaTasks.value.slice(start, end)
})

const pagedTestToolTasks = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return testToolTasks.value.slice(start, end)
})

function formatDate(timeStr) {
  if (!timeStr) return '-'
  const d = new Date(timeStr)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function formatDateTime(timeStr) {
  if (!timeStr) return '-'
  const d = new Date(timeStr)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const h = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${y}-${m}-${day} ${h}:${min}`
}

// 静态分析状态类型映射
function getStaticStatusType(status) {
  const types = {
    'pending': 'info',
    'processing': 'warning',
    'ai_analyzing': 'warning',
    'completed': 'success',
    'error': 'danger'
  }
  return types[status] || 'info'
}

// 静态分析状态文本映射
function getStaticStatusText(status) {
  const texts = {
    'pending': '等待中',
    'processing': '处理中',
    'ai_analyzing': 'AI分析中',
    'completed': '已完成',
    'error': '错误'
  }
  return texts[status] || status
}

// 准确率类型映射
function getAccuracyType(accuracy) {
  if (!accuracy || accuracy === 0) return 'info'
  if (accuracy >= 0.8) return 'success'
  if (accuracy >= 0.5) return 'warning'
  return 'danger'
}

// 格式化准确率显示
function formatAccuracy(accuracy) {
  if (!accuracy || accuracy === 0) return '-'
  return `${(accuracy * 100).toFixed(1)}%`
}

// 获取高亮颜色类（用于核心指标列）
function getHighlightClass(accuracy) {
  if (!accuracy || accuracy === 0) return 'gray'
  if (accuracy >= 0.85) return 'excellent'
  if (accuracy >= 0.7) return 'good'
  if (accuracy >= 0.5) return 'medium'
  return 'poor'
}


function getTestToolStatusType(status) {
  const map = { uploaded: 'info', processing: 'warning', completed: 'success', error: 'danger' }
  return map[status] || 'info'
}

function getTestToolStatusText(status) {
  const map = { uploaded: '已上传', processing: '处理中', completed: '已完成', error: '错误' }
  return map[status] || status
}

// 获取API基础路径
function getApiBasePath() {
  return testMode.value === 'configuration' 
    ? '/api/codeReview' 
    : '/api/codeReview/regressionTest'
}

// 处理测试模式切换
function handleTestModeChange() {
  console.log('切换测试模式:', testMode.value)
  refresh()
}

// 处理分析模式切换
function handleModeChange() {
  console.log('切换分析模式:', activeMode.value)
  refresh()
}

async function refresh() {
  loading.value = true
  try {
    // 根据当前激活的模式加载对应数据
    if (activeMode.value === 'code_review_function') {
      const apiPath = getApiBasePath()
      const resp = await axios.get(`${apiPath}/admin/tasks`, { params: { limit: 500 } })
      if (resp.data && resp.data.tasks) {
        tasks.value = resp.data.tasks
        console.log(`[数据面板-${testMode.value}] 加载了 ${tasks.value.length} 个代码审查任务`)
      }
    } else if (activeMode.value === 'static_c') {
      // 加载静态分析C/C++任务
      console.log('[数据面板] 开始加载C/C++任务...')
      const resp = await axios.get('/api/staticAnalysis/filter/admin/tasks', { params: { limit: 500 } })
      console.log('[数据面板] C/C++ API响应:', resp.data)
      if (resp.data && resp.data.success && resp.data.tasks) {
        staticTasks.value = resp.data.tasks
        console.log(`[数据面板] 加载了 ${staticTasks.value.length} 个静态分析C/C++任务`)
      } else {
        console.warn('[数据面板] C/C++ API返回数据格式异常:', resp.data)
      }
    } else if (activeMode.value === 'static_fpga') {
      // 加载静态分析FPGA任务（使用filterFpga专用API）
      console.log('[数据面板] 开始加载FPGA任务...')
      const resp = await axios.get('/api/staticAnalysis/filterFpga/admin/tasks', { params: { limit: 500 } })
      console.log('[数据面板] FPGA API响应:', resp.data)
      if (resp.data && resp.data.success && resp.data.tasks) {
        fpgaTasks.value = resp.data.tasks
        console.log(`[数据面板] 加载了 ${fpgaTasks.value.length} 个静态分析FPGA任务`)
      } else {
        console.warn('[数据面板] FPGA API返回数据格式异常:', resp.data)
      }
    } else if (activeMode.value === 'test_case_summary') {
      const resp = await testCaseSummaryService.getAdminTasks(500)
      if (resp && resp.success) {
        testToolTasks.value = resp.tasks || []
      }
    }
    // 数据刷新后重置到第一页
    currentPage.value = 1
  } catch (e) {
    console.error(e)
    ElMessage.error('加载任务数据失败')
  } finally {
    loading.value = false
  }
}

function handleSelectionChange(rows) {
  selectedTasks.value = rows
}

function handlePageChange(page) {
  currentPage.value = page
}

function goTaskManager() {
  router.push('/admin-task-manager')
}

async function exportMarked(row) {
  try {
    if (activeMode.value !== 'code_review_function') {
      ElMessage.warning('当前模式不支持导出标记问题')
      return
    }

    const apiPath = getApiBasePath()
    // 复用函数审查 CodeMapSidebar 逻辑：先获取所有已标记问题，再调用导出接口
    const markedResp = await axios.get(`${apiPath}/${row.id}/marked_problems`, {
      params: { analysis_type: 'function' }
    })

    const markedProblemsArray = (markedResp.data?.data || []).map(item => item.problem_data)

    if (!markedProblemsArray.length) {
      ElMessage.warning('未找到已标记问题')
      return
    }

    const exportResp = await axios.post(
      `${apiPath}/export_marked_problems/${row.id}`,
      {
        analysis_type: 'function',
        problems: markedProblemsArray
      },
      { responseType: 'blob' }
    )

    const blob = new Blob([exportResp.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `marked_problems_task_${row.id}_${Date.now()}.xlsx`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (e) {
    console.error(e)
    ElMessage.error('导出标记问题失败')
  }
}

// [NEW] 导出静态分析标记问题
async function exportMarkedProblems(row, mode) {
  try {
    const apiPath = mode === 'static_c' 
      ? '/api/static-analysis/filter'
      : '/api/static-analysis/filter-fpga'
    
    // 调用导出标记问题接口
    const exportResp = await axios.post(
      `${apiPath}/export_marked_problems/${row.id}`,
      {},
      { responseType: 'blob' }
    )

    const blob = new Blob([exportResp.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `marked_problems_${mode}_${row.id}_${Date.now()}.xlsx`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    
    ElMessage.success('导出标记问题成功')
  } catch (e) {
    console.error(e)
    ElMessage.error('导出标记问题失败')
  }
}

async function exportSelected() {
  if (!selectedTasks.value.length) {
    ElMessage.warning('请先勾选要导出的任务')
    return
  }

  try {
    // 动态导入 xlsx 库
    const XLSX = await import('xlsx')

    // 准备数据（列顺序与表格显示一致）
    const data = selectedTasks.value.map(t => ({
      '任务ID': t.id,
      '问题检出准确率': formatAccuracy(t.accuracy),
      '注释准确率': t.comment_accuracy_rate || '-',
      '总问题数': t.total_problems ?? 0,
      '有效问题数': t.effective_total_problems ?? 0,
      '标记问题数量': t.marked_problem_count ?? 0,
      '算法过滤数': t.algorithm_filtered_count ?? 0,
      '是否有标记问题': t.has_marked_problems ? '是' : '否',
      '是否导出过标记问题': t.marked_problems_exported ? '是' : '否',
      '人员名称': t.tester_name || '',
      '最近日期': formatDate(t.updated_at)
    }))

    // 创建工作簿和工作表
    const ws = XLSX.utils.json_to_sheet(data)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, '代码审查任务')

    // 设置列宽
    const colWidths = [
      { wch: 10 },  // 任务ID
      { wch: 14 },  // 问题检出准确率
      { wch: 14 },  // 注释准确率
      { wch: 10 },  // 总问题数
      { wch: 12 },  // 有效问题数
      { wch: 12 },  // 标记问题数量
      { wch: 12 },  // 算法过滤数
      { wch: 14 },  // 是否有标记问题
      { wch: 18 },  // 是否导出过标记问题
      { wch: 12 },  // 人员名称
      { wch: 12 },  // 最近日期
    ]
    ws['!cols'] = colWidths

    // 生成文件名（包含日期和任务数量）
    const now = new Date()
    const dateStr = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}`
    const testModeLabel = testMode.value === 'configuration' ? '配置项' : '回归'
    const filename = `函数审查_${testModeLabel}_${dateStr}_${selectedTasks.value.length}个任务.xlsx`

    // 导出文件
    XLSX.writeFile(wb, filename)

    ElMessage.success(`已导出 ${selectedTasks.value.length} 个任务：${filename}`)
  } catch (e) {
    console.error(e)
    ElMessage.error('导出失败：' + (e.message || '未知错误'))
  }
}


async function exportAllData() {
  exportingAll.value = true
  try {
    const XLSX = await import('xlsx')
    let data = []
    let sheetName = ''
    let filename = ''
    const now = new Date()
    const dateStr = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}`
    const testModeLabel = testMode.value === 'configuration' ? '配置项' : '回归'

    if (activeMode.value === 'code_review_function') {
      if (!filteredTasksAll.value.length) {
        ElMessage.warning('当前没有可导出的数据')
        return
      }
      data = filteredTasksAll.value.map(t => ({
        '任务ID': t.id,
        '问题检出准确率': formatAccuracy(t.accuracy),
        '注释准确率': t.comment_accuracy_rate || '-',
        '总问题数': t.total_problems ?? 0,
        '有效问题数': t.effective_total_problems ?? 0,
        '标记问题数量': t.marked_problem_count ?? 0,
        '算法过滤数': t.algorithm_filtered_count ?? 0,
        '是否有标记问题': t.has_marked_problems ? '是' : '否',
        '是否导出过标记问题': t.marked_problems_exported ? '是' : '否',
        '人员名称': t.tester_name || '',
        '最近日期': formatDate(t.updated_at)
      }))
      sheetName = '代码审查（函数）'
      filename = `函数审查_${testModeLabel}_全部_${dateStr}_${data.length}条.xlsx`
    } else if (activeMode.value === 'static_c') {
      if (!filteredStaticTasks.value.length) {
        ElMessage.warning('当前没有可导出的数据')
        return
      }
      data = filteredStaticTasks.value.map(t => ({
        '任务ID': t.id,
        '问题检出准确率': formatAccuracy(t.accuracy),
        '问题单准确率': t.problem_sheet_accuracy_rate || '-',
        '总问题数': t.total_four_category ?? 0,
        '有效问题数': t.filtered_problems_count ?? 0,
        '标记问题数量': t.marked_problem_count ?? 0,
        '是否有标记问题': t.has_marked_problems ? '是' : '否',
        '是否导出过标记问题': t.marked_problems_exported ? '是' : '否',
        '人员名称': t.operator_name || '',
        '最近日期': t.latest_marked_at ? formatDateTime(t.latest_marked_at) : '-'
      }))
      sheetName = '静态分析 CC'
      filename = `静态分析CC_全部_${dateStr}_${data.length}条.xlsx`
    } else if (activeMode.value === 'static_fpga') {
      if (!filteredFpgaTasks.value.length) {
        ElMessage.warning('当前没有可导出的数据')
        return
      }
      data = filteredFpgaTasks.value.map(t => ({
        '任务ID': t.id,
        '问题检出准确率': formatAccuracy(t.accuracy),
        '问题单准确率': t.problem_sheet_accuracy_rate || '-',
        '总问题数': t.total_four_category ?? 0,
        '有效问题数': t.filtered_problems_count ?? 0,
        '标记问题数量': t.marked_problem_count ?? 0,
        '是否有标记问题': t.has_marked_problems ? '是' : '否',
        '是否导出过标记问题': t.marked_problems_exported ? '是' : '否',
        '人员名称': t.operator_name || '',
        '最近日期': t.latest_marked_at ? formatDateTime(t.latest_marked_at) : '-'
      }))
      sheetName = '静态分析FPGA'
      filename = `静态分析FPGA_全部_${dateStr}_${data.length}条.xlsx`
    }

    const ws = XLSX.utils.json_to_sheet(data)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, sheetName)

    const colCount = data.length > 0 ? Object.keys(data[0]).length : 10
    ws['!cols'] = Array(colCount).fill({ wch: 16 })

    XLSX.writeFile(wb, filename)
    ElMessage.success(`已导出全部 ${data.length} 条数据：${filename}`)
  } catch (e) {
    console.error(e)
    ElMessage.error('导出失败：' + (e.message || '未知错误'))
  } finally {
    exportingAll.value = false
  }
}

onMounted(() => {
  refresh()
})
</script>

<style scoped>
.admin-data-panel {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-right {
  display: flex;
  gap: 12px;
}

/* 测试类型切换卡片 */
.test-mode-card {
  margin-bottom: 16px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.test-mode-card :deep(.el-card__body) {
  padding: 20px;
}

.mode-switch-row {
  display: flex;
  align-items: center;
  gap: 20px;
}

.mode-label {
  font-size: 16px;
  font-weight: 600;
  min-width: 100px;
}

.mode-description {
  margin-left: auto;
}

/* 分析类型切换卡片 */
.mode-card {
  margin-bottom: 16px;
}

.mode-actions {
  margin-left: auto;
  display: flex;
  gap: 12px;
}

.filter-card {
  margin-bottom: 16px;
}

.table-card {
  border-radius: 12px;
}

.table-pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}

/* 核心指标列高亮样式 */
:deep(.highlight-column) {
  background-color: #fff8e6 !important;
}

:deep(.highlight-column .cell) {
  font-weight: 700;
}

.highlight-header {
  color: #d46b08;
  font-weight: 700;
  font-size: 14px;
  text-shadow: 0 1px 2px rgba(212, 107, 8, 0.2);
}

.highlight-value {
  font-weight: 700;
  font-size: 15px;
  padding: 4px 8px;
  border-radius: 4px;
  display: inline-block;
}

/* 问题检出准确率颜色等级 */
.highlight-value.excellent {
  color: #52c41a;
  background-color: #f6ffed;
  border: 1px solid #b7eb8f;
}

.highlight-value.good {
  color: #1890ff;
  background-color: #e6f7ff;
  border: 1px solid #91d5ff;
}

.highlight-value.medium {
  color: #faad14;
  background-color: #fffbe6;
  border: 1px solid #ffe58f;
}

.highlight-value.poor {
  color: #f5222d;
  background-color: #fff1f0;
  border: 1px solid #ffa39e;
}

.highlight-value.gray {
  color: #999;
  background-color: #f5f5f5;
}

/* 注释准确率蓝色样式 */
.highlight-value.blue {
  color: #096dd9;
  background-color: #e6f4ff;
  border: 1px solid #69c0ff;
}

/* 普通列文字颜色（黑色） */
:deep(.el-table__body-wrapper .el-table__body td:not(.highlight-column) .cell) {
  color: #000;
}
</style>
