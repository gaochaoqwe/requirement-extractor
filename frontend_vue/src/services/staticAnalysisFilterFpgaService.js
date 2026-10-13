/**
 * FPGA 静态分析过滤工具服务（与 C/C++ 分离）
 */
import request from '@/api/request'

const BASE_URL = '/staticAnalysis/filterFpga'

const staticAnalysisFilterFpgaService = {
  // 加载默认规则配置（FPGA）
  async loadDefaultRulesConfig() {
    try {
      const response = await request.get(`${BASE_URL}/rules/config/load`)
      return response
    } catch (error) {
      console.error('加载FPGA默认规则配置失败:', error)
      throw error
    }
  },

  // 保存默认规则配置（FPGA）。注意：后端仍使用字段名 gjb_rules/cwe_rules
  async saveDefaultRulesConfig(fpgaRules, cweRules, ruleOverrides = null, customFilters = null, maxIssuesPerRule = 0) {
    try {
      const payloadOverrides = ruleOverrides
        ? { fpga: { ...(ruleOverrides.fpga || {}) }, cwe: { ...(ruleOverrides.cwe || {}) } }
        : { fpga: {}, cwe: {} }
      // 调试输出
      // eslint-disable-next-line no-console
      console.log('[FPGA][SERVICE] saveDefaultRulesConfig overrides:', {
        fpga: Object.keys(payloadOverrides.fpga).length,
        cwe: Object.keys(payloadOverrides.cwe).length,
      })
      const response = await request.post(`${BASE_URL}/rules/config/save`, {
        gjb_rules: fpgaRules,
        cwe_rules: cweRules,
        rule_overrides: payloadOverrides,
        custom_filters: customFilters,
        max_issues_per_rule: maxIssuesPerRule,
      })
      return response
    } catch (error) {
      console.error('保存FPGA默认规则配置失败:', error)
      throw error
    }
  },

  // 通过 session_id 获取 task_id（FPGA）
  async getTaskIdBySession(sessionId) {
    try {
      const response = await request.get(`${BASE_URL}/session/${sessionId}/task-id`)
      return response
    } catch (error) {
      console.error('获取FPGA任务ID失败:', error)
      throw error
    }
  },

  // 生成输出文件
  async generateOutputFile(sessionId, ruleType = 'all', contentType = 'all') {
    try {
      const response = await request.post(`${BASE_URL}/download/${sessionId}`, {
        rule_type: ruleType,
        content_type: contentType
      })
      return response
    } catch (error) {
      console.error('生成FPGA输出文件失败:', error)
      throw error
    }
  },

  // 获取下载URL
  getDownloadUrl(sessionId, filename) {
    return `/api${BASE_URL}/download/${sessionId}/${filename}`
  },
}

export default staticAnalysisFilterFpgaService
