/**
 * 普通模式 C/C++ 静态分析服务
 */
import request from '@/api/request'

const BASE_URL = '/staticAnalysis/normalModeC'

const staticAnalysisNormalModeCService = {
  async start({ file_id, selected_rules, language_mode = 'c' }) {
    return request.post(`${BASE_URL}/start`, {
      file_id,
      selected_rules,
      language_mode
    })
  },

  async health() {
    return request.get(`${BASE_URL}/health`)
  },

  async getTaskProgress(taskId) {
    return request.get(`${BASE_URL}/task_progress/${taskId}`)
  },

  async getCodeView(taskId, ruleType = 'mixed') {
    return request.get(`${BASE_URL}/code-view/${taskId}`, {
      params: { rule_type: ruleType }
    })
  },

  getUploadUrl() {
    return `/api${BASE_URL}/upload`
  },

  getDownloadUrl(taskId) {
    return `/api${BASE_URL}/download_result/${taskId}`
  },

  async loadRules() {
    const SHARED_URL = '/staticAnalysis'
    const [gjbAccurate, gjbUncertain, cweAccurate, cweUncertain] = await Promise.all([
      request.get(`${SHARED_URL}/filter/rules/accurate`).catch(() => ({ rules: [] })),
      request.get(`${SHARED_URL}/filter/rules/uncertain`).catch(() => ({ rules: [] })),
      request.get(`${SHARED_URL}/filter/rules/cwe/accurate`).catch(() => ({ rules: [] })),
      request.get(`${SHARED_URL}/filter/rules/cwe/uncertain`).catch(() => ({ rules: [] }))
    ])
    return {
      gjb: [...(gjbAccurate?.rules || []), ...(gjbUncertain?.rules || [])],
      cwe: [...(cweAccurate?.rules || []), ...(cweUncertain?.rules || [])]
    }
  },

  async saveConfig(selectedRules) {
    return request.post(`${BASE_URL}/rules/config/save`, { selected_rules: selectedRules })
  }
}

export default staticAnalysisNormalModeCService
