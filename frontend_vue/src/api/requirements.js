import request from './request'

// 智能导入：预览
export function previewIntelligentImport(formData) {
  return request.post('/database-manage/requirements/import/preview-intelligent', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

// 智能导入：提交
export function commitIntelligentImport(decisions) {
  return request.post('/database-manage/requirements/import/commit-intelligent', decisions)
}

// 常规导入
export function importRequirements(formData, clearExisting = false) {
  return request.post(`/database-manage/requirements/import?clear_existing=${clearExisting}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

// 校验结构
export function validateImport(formData) {
  return request.post('/database-manage/requirements/import/validate', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

// 列表
export function listRequirements(params) {
  return request.get('/database-manage/requirements/list', { params })
}

// 统计
export function getRequirementStats() {
  return request.get('/database-manage/requirements/stats')
}
