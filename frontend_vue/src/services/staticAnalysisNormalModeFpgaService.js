/**
 * 普通模式 FPGA 静态分析服务
 */
import request from '@/api/request'

const BASE_URL = '/staticAnalysis/normalModeFpga'

const staticAnalysisNormalModeFpgaService = {
  async start({ file_id, selected_rules, language_mode = 'fpga' }) {
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

  async getCodeView(taskId, ruleType = 'fpga') {
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
    const [accurate, uncertain] = await Promise.all([
      request.get(`${SHARED_URL}/filterFpga/rules`, { params: { accuracy: 'accurate' } }).catch(() => ({ items: [] })),
      request.get(`${SHARED_URL}/filterFpga/rules`, { params: { accuracy: 'uncertain' } }).catch(() => ({ items: [] }))
    ])
    return [...(accurate?.items || []), ...(uncertain?.items || [])]
  },

  async saveConfig(selectedRules) {
    return request.post(`${BASE_URL}/rules/config/save`, { selected_rules: selectedRules })
  }
}

export default staticAnalysisNormalModeFpgaService
