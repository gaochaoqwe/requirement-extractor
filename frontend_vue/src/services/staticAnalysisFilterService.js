/**
 * 静态分析问题过滤工具服务
 */
import request from '@/api/request'

const BASE_URL = '/staticAnalysis/filter'

const staticAnalysisFilterService = {
  /**
   * 上传文件并开始过滤处理
   * @param {File} file - 要上传的Excel文件
   * @param {string} filterKeywords - 过滤关键字，逗号分隔
   * @returns {Promise<Object>} 上传结果
   */
  async uploadFile(file, filterKeywords = '') {
    try {
      const formData = new FormData()
      formData.append('file', file)
      if (filterKeywords) {
        formData.append('filter_keywords', filterKeywords)
      }

      const response = await request.post(`${BASE_URL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      return response
    } catch (error) {
      console.error('上传文件失败:', error)
      throw error
    }
  },

  /**
   * 获取会话处理状态
   * @param {string} sessionId - 会话ID
   * @returns {Promise<Object>} 状态信息
   */
  async getSessionStatus(sessionId) {
    try {
      const response = await request.get(`${BASE_URL}/status/${sessionId}`)
      return response
    } catch (error) {
      console.error('获取会话状态失败:', error)
      throw error
    }
  },

  /**
   * 生成输出文件
   * @param {string} sessionId - 会话ID
   * @param {string} ruleType - 规则类型：'all', 'gjb', 'cwe'
   * @param {string} contentType - 内容类型：'all', 'accurate', 'uncertain'
   * @returns {Promise<Object>} 生成结果
   */
  async generateOutputFile(sessionId, ruleType = 'all', contentType = 'all', includeUnselected = false, split = false, highlightAi = false) {
    try {
      const response = await request.post(`${BASE_URL}/download/${sessionId}`, {
        rule_type: ruleType,
        content_type: contentType,
        include_unselected: includeUnselected,
        split,
        highlight_ai: !!highlightAi,
      })
      return response
    } catch (error) {
      console.error('生成输出文件失败:', error)
      throw error
    }
  },

  /**
   * 获取下载URL
   * @param {string} sessionId - 会话ID
   * @param {string} filename - 文件名
   * @returns {string} 下载URL
   */
  getDownloadUrl(sessionId, filename) {
    const baseUrl = import.meta.env.VITE_BASE_API || '/api'
    return `${baseUrl}${BASE_URL}/download/${sessionId}/${filename}`
  },

  /**
   * 根据类型获取规则列表
   * @param {string} accuracyType - 规则类型：'accurate'(确定规则) 或 'uncertain'(不确定规则)
   * @returns {Promise<Object>} 规则列表
   */
  async getRulesByType(accuracyType) {
    try {
      const response = await request.get(`${BASE_URL}/rules/${accuracyType}`)
      return response
    } catch (error) {
      console.error('获取规则列表失败:', error)
      throw error
    }
  },

  /**
   * 上传增强版文件（Excel + 代码库）
   * @param {File} excelFile - Excel文件
   * @param {File} codebaseFile - 代码库压缩文件（可选）
   * @param {Array} selectedRules - 选中的规则列表
   * @param {Object} customFilters - 自定义关键词过滤规则
   * @param {number} maxIssuesPerRule - 每个规则最多保留的问题数量
   * @returns {Promise<Object>} 上传结果
   */
  async uploadEnhancedFiles(excelFile, codebaseFile, selectedRules = [], customFilters = {}, maxIssuesPerRule = 0) {
    try {
      const formData = new FormData()
      formData.append('excel_file', excelFile)
      
      if (codebaseFile) {
        formData.append('codebase_file', codebaseFile)
      }
      
      // 添加选中的规则
      formData.append('selected_rules', JSON.stringify(selectedRules))
      
      // 添加自定义过滤规则
      formData.append('custom_filters', JSON.stringify(customFilters))
      
      // 添加问题数量限制
      formData.append('max_issues_per_rule', maxIssuesPerRule.toString())

      console.log('[API] 准备发送上传请求...')
      console.log('[API] 选中规则数:', selectedRules.length)
      console.log('[API] 自定义过滤规则:', customFilters)
      console.log('[API] 问题数量限制:', maxIssuesPerRule)
      const response = await request.post(`${BASE_URL}/upload-enhanced`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        // 🔧 禁用重试，避免重复上传
        retry: 0,
        // 不单独设置 timeout，继承全局 axios 超时（20分钟），避免大文件/解压导致120s超时
        // timeout: 600000,
        onUploadProgress: (evt) => {
          try {
            const percent = evt.total ? Math.round((evt.loaded * 100) / evt.total) : undefined
            console.log('[API] 上传进度:', percent !== undefined ? `${percent}%` : `${evt.loaded} bytes`)
          } catch (_) {}
        }
      })

      console.log('[API] 收到上传响应:', response)
      return response
    } catch (error) {
      console.error('上传增强版文件失败:', error)
      throw error
    }
  },

  /**
   * 获取增强版会话处理状态
   * @param {string} sessionId - 会话ID
   * @returns {Promise<Object>} 状态信息
   */
  async getEnhancedSessionStatus(sessionId) {
    try {
      const response = await request.get(`${BASE_URL}/status-enhanced/${sessionId}`)
      return response
    } catch (error) {
      console.error('获取增强版会话状态失败:', error)
      throw error
    }
  },

  /**
   * 健康检查
   * @returns {Promise<Object>} 健康状态
   */
  async healthCheck() {
    try {
      const response = await request.get(`${BASE_URL}/health`)
      return response
    } catch (error) {
      console.error('健康检查失败:', error)
      throw error
    }
  },

  /**
   * 获取CWE规则列表
   * @param {string} accuracyType - 规则类型：'accurate'(确定规则) 或 'uncertain'(不确定规则)
   * @returns {Promise<Object>} CWE规则列表
   */
  async getCWERules(accuracyType) {
    try {
      const response = await request.get(`${BASE_URL}/rules/cwe/${accuracyType}`)
      return response
    } catch (error) {
      console.error('获取CWE规则列表失败:', error)
      throw error
    }
  },

  /**
   * 获取CWE规则统计信息
   * @returns {Promise<Object>} CWE规则统计
   */
  async getCWEStatistics() {
    try {
      const response = await request.get(`${BASE_URL}/rules/cwe/statistics`)
      return response
    } catch (error) {
      console.error('获取CWE统计信息失败:', error)
      throw error
    }
  },

  /**
   * 获取详细状态（包含GJB和CWE两部分）
   * @param {string} sessionId - 会话ID
   * @returns {Promise<Object>} 详细状态信息
   */
  async getDetailedStatus(sessionId) {
    try {
      const response = await request.get(`${BASE_URL}/status/${sessionId}/detailed`)
      // 调试：打印详细状态接口的原始返回内容
      try {
        console.log('[API] getDetailedStatus 响应:', response)
        if (response) {
          console.log('[API] getDetailedStatus 类型:', typeof response, 'keys:', Object.keys(response))
          // 兼容 axios.data 风格，如果是 { data: {...} } 这里也能看到
          if (response.data) {
            console.log('[API] getDetailedStatus response.data:', response.data)
          }
        }
      } catch (logError) {
        // 防止日志本身抛错影响正常逻辑
      }
      return response
    } catch (error) {
      console.error('获取详细状态失败:', error)
      throw error
    }
  },

  /**
   * 保存默认规则配置
   * @param {Array<string>} gjbRules - GJB规则列表
   * @param {Array<string>} cweRules - CWE规则列表
   * @param {Object} ruleOverrides - 规则分类覆盖配置
   * @param {Object} customFilters - 自定义关键词过滤规则
   * @param {number} maxIssuesPerRule - 每个规则最多保留的问题数量
   * @returns {Promise<Object>} 保存结果
   */
  async saveDefaultRulesConfig(gjbRules, cweRules, ruleOverrides = null, customFilters = null, maxIssuesPerRule = 0) {
    try {
      const response = await request.post(`${BASE_URL}/rules/config/save`, {
        gjb_rules: gjbRules,
        cwe_rules: cweRules,
        rule_overrides: ruleOverrides,
        custom_filters: customFilters,
        max_issues_per_rule: maxIssuesPerRule
      })
      return response
    } catch (error) {
      console.error('保存默认规则配置失败:', error)
      throw error
    }
  },

  /**
   * 加载默认规则配置
   * @returns {Promise<Object>} 默认配置
   */
  async loadDefaultRulesConfig() {
    try {
      const response = await request.get(`${BASE_URL}/rules/config/load`)
      return response
    } catch (error) {
      console.error('加载默认规则配置失败:', error)
      throw error
    }
  },

  /**
   * 通过session_id获取task_id
   * @param {string} sessionId - 会话ID (UUID)
   * @returns {Promise<Object>} 包含task_id的响应
   */
  async getTaskIdBySession(sessionId) {
    try {
      const response = await request.get(`${BASE_URL}/session/${sessionId}/task-id`)
      return response
    } catch (error) {
      console.error('获取任务ID失败:', error)
      throw error
    }
  }
}

export default staticAnalysisFilterService 