import axios from 'axios'

// 创建axios实例
const apiClient = axios.create({
  baseURL: '/api',  // 🚀 修复：直接使用/api，确保生产环境正常
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 🚀 调试：记录baseURL设置
console.log('🔧 API Client配置:', {
  baseURL: apiClient.defaults.baseURL,
  environment: import.meta.env.MODE,
  envVariable: import.meta.env.VITE_API_BASE_URL
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 🚀 调试：记录请求详情
    console.log('📤 发送API请求:', {
      method: config.method,
      url: config.url,
      baseURL: config.baseURL,
      fullURL: config.baseURL + config.url,
      params: config.params
    })
    
    // 可以在这里添加认证token等
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    // 🚀 生产环境调试：记录API响应结构
    if (process.env.NODE_ENV === 'production' || import.meta.env.PROD) {
      console.log('🔍 API响应调试:', {
        url: response.config.url,
        method: response.config.method,
        status: response.status,
        dataType: typeof response.data,
        dataIsArray: Array.isArray(response.data),
        headers: response.headers,
        responseData: response.data
      })
    }
    return response
  },
  (error) => {
    // 统一错误处理
    console.error('❌ API请求失败:', {
      url: error.config?.url,
      method: error.config?.method,
      status: error.response?.status,
      statusText: error.response?.statusText,
      responseData: error.response?.data,
      errorMessage: error.message
    })
    
    const message = error.response?.data?.detail || error.message || '请求失败'
    return Promise.reject(new Error(message))
  }
)

export const databaseManageService = {
  // 获取需求记录列表
  getRequirements(params = {}) {
    return apiClient.get('/database/database-manage/requirements/list', { params })
  },

  // 获取排序后的需求记录列表
  getRequirementsSorted(params = {}) {
    return apiClient.get('/database/database-manage/requirements/list/sorted', { params })
  },

  // 获取需求记录总数
  getRequirementsCount(params = {}) {
    return apiClient.get('/database/database-manage/requirements/count', { params })
  },

  // 根据ID获取单个需求记录
  getRequirement(id) {
    return apiClient.get(`/database/database-manage/requirements/${id}`)
  },

  // 创建新的需求记录
  createRequirement(data) {
    return apiClient.post('/database/database-manage/requirements/', data)
  },

  // 批量创建需求记录
  createRequirementsBatch(requirements) {
    // requirements: Array<OptoelectronicRequirementCreate>
    return apiClient.post('/database/database-manage/requirements/batch', { requirements })
  },

  // 批量更新需求记录
  batchUpdateRequirements(items) {
    // items: Array<{ id: number, update: Partial<Requirement> }>
    return apiClient.post('/database/database-manage/requirements/batch/update', { items })
  },

  // 批量删除需求记录
  batchDeleteRequirements(ids) {
    // ids: number[]
    return apiClient.post('/database/database-manage/requirements/batch-delete', { ids })
  },

  // 更新需求记录
  updateRequirement(id, data) {
    return apiClient.put(`/database/database-manage/requirements/${id}`, data)
  },

  // 单元格更新
  updateCell(id, field, value) {
    return apiClient.put(`/database/database-manage/requirements/${id}/cell`, { field, value })
  },

  // 删除需求记录
  deleteRequirement(id) {
    return apiClient.delete(`/database/database-manage/requirements/${id}`)
  },

  // 删除所有需求记录
  deleteAllRequirements() {
    return apiClient.delete('/database/database-manage/requirements/')
  },

  // 验证Excel文件
  validateExcelImport(formData) {
    return apiClient.post('/database/database-manage/requirements/import/validate', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 导入Excel文件
  importExcelRequirements(formData) {
    return apiClient.post('/database/database-manage/requirements/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 60000 // 导入可能需要更长时间
    })
  },

  // 导出需求记录为Excel
  exportRequirements(params = {}) {
    return apiClient.get('/database/database-manage/requirements/export/excel', {
      params,
      responseType: 'blob' // 重要：设置响应类型为blob
    })
  },

  // 多Sheet（7列）导入：mode=full|incremental
  importMultiSheet7Cols(formData, mode = 'full') {
    return apiClient.post(`/database/database-manage/requirements/import/multisheet-7cols`, formData, {
      params: { mode },
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 60000
    })
  },

  // 七列表：按表分页列表（table: 转塔|对抗告警|光雷|吊舱），响应头含 X-Total-Count
  listSevenCols({ table, page = 1, pageSize = 50, softwareCategory, testItemName } = {}, options = {}) {
    const params = { table, page, page_size: pageSize }
    if (softwareCategory) params.software_category = softwareCategory
    if (testItemName) params.test_item_name = testItemName
    
    // 🚀 优化: 支持AbortController和其他请求选项
    const requestConfig = { 
      params,
      timeout: 30000, // 30秒超时
      ...options 
    }
    
    return apiClient.get('/database/database-manage/requirements/seven/list', requestConfig)
  },

  // 七列表：导出Excel
  exportSevenCols({ table, softwareCategory, testItemName } = {}) {
    const params = { table }
    if (softwareCategory) params.software_category = softwareCategory
    if (testItemName) params.test_item_name = testItemName
    return apiClient.get('/database/database-manage/requirements/seven/export', {
      params,
      responseType: 'blob'
    })
  },

  // 清空数据库：清空所有表中的数据（保留表结构）
  resetDatabase() {
    return apiClient.post('/database/database-manage/requirements/admin/reset-db', null, {
      params: { confirm: 'YES' }
    })
  },

  // 智能导出（原有的同步方式，保持兼容）
  intelligentExport(formData) {
    return apiClient.post('/database/database-manage/requirements/intelligent-export', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      responseType: 'blob', // 重要：设置响应类型为blob
      timeout: 60000 // 处理可能需要更长时间
    })
  },

  // 异步智能导出 - 启动任务
  intelligentExportAsync(formData) {
    return apiClient.post('/database/database-manage/requirements/intelligent-export-async', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 30000
    })
  },

  // 获取导出进度
  getExportProgress(taskId) {
    return apiClient.get(`/database/database-manage/requirements/export-progress/${taskId}`)
  },

  // 下载导出结果
  downloadExportResult(taskId) {
    return apiClient.get(`/database/database-manage/requirements/download-export/${taskId}`, {
      responseType: 'blob'
    })
  }
}