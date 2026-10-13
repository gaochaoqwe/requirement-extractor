/**
 * 回归测试服务
 * 提供与后端API交互的方法
 */

import request from '@/api/request'

class RegressionService {
  constructor() {
    this.client = request
  }

  /**
   * 上传影响域分析报告
   * @param {File} file - 影响域分析报告文件
   * @param {string} sessionId - 会话ID（可选）
   * @returns {Promise} API响应
   */
  async uploadImpactAnalysis(file, sessionId = null) {
    try {
      const formData = new FormData()
      formData.append('impact_file', file)
      if (sessionId) {
        formData.append('session_id', sessionId)
      }

      const response = await this.client.post('/dynamic-test/regression/upload-impact', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      return response
    } catch (error) {
      console.error('上传影响域分析报告失败:', error)
      throw error
    }
  }

  /**
   * 上传策划文档
   * @param {File} file - 策划文档文件
   * @param {string} sessionId - 会话ID
   * @returns {Promise} API响应
   */
  async uploadPlanning(file, sessionId) {
    try {
      const formData = new FormData()
      formData.append('planning_file', file)
      formData.append('session_id', sessionId)

      const response = await this.client.post('/dynamic-test/regression/upload-planning', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      return response
    } catch (error) {
      console.error('上传策划文档失败:', error)
      throw error
    }
  }

  /**
   * 上传需求目录文档
   * @param {File} file - 需求目录文档文件
   * @param {string} sessionId - 会话ID
   * @returns {Promise} API响应
   */
  async uploadCatalog(file, sessionId) {
    try {
      const formData = new FormData()
      formData.append('catalog_file', file)
      formData.append('session_id', sessionId)

      const response = await this.client.post('/dynamic-test/regression/upload-catalog', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      return response
    } catch (error) {
      console.error('上传需求目录文档失败:', error)
      throw error
    }
  }

  /**
   * 生成回归测试表单（异步任务）
   * @param {string} sessionId - 会话ID
   * @param {Object} params - 生成参数
   * @returns {Promise} API响应
   */
  async generateForms(sessionId, params) {
    try {
      const formData = new FormData()
      formData.append('session_id', sessionId)
      formData.append('test_manager', params.testManager)
      formData.append('test_personnel', params.testPersonnel)
      formData.append('developer', params.developer)
      formData.append('software_name', params.softwareName)
      formData.append('software_version', params.softwareVersion)
      formData.append('software_id', params.softwareId)
      formData.append('domain', params.domain)
      formData.append('detector_flag', params.detectorFlag)
      formData.append('ai_analysis', params.aiAnalysis)
      formData.append('deep_analysis', params.deepAnalysis)
      formData.append('has_planning', params.hasPlanning)

      const response = await this.client.post('/dynamic-test/regression/generate-forms', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      return response
    } catch (error) {
      console.error('生成回归测试表单失败:', error)
      throw error
    }
  }

  /**
   * 获取任务状态
   * @param {string} taskId - 任务ID
   * @returns {Promise} API响应
   */
  async getTaskStatus(taskId) {
    try {
      const response = await this.client.get(`/dynamic-test/regression/task-status/${taskId}`)
      return response
    } catch (error) {
      console.error('获取任务状态失败:', error)
      throw error
    }
  }

  /**
   * 获取会话状态
   * @param {string} sessionId - 会话ID
   * @returns {Promise} API响应
   */
  async getSessionStatus(sessionId) {
    try {
      const response = await this.client.get(`/dynamic-test/regression/status/${sessionId}`)
      return response
    } catch (error) {
      console.error('获取会话状态失败:', error)
      throw error
    }
  }

  /**
   * 下载生成的文件
   * @param {string} sessionId - 会话ID
   * @param {string} filename - 文件名
   * @returns {Promise} 下载响应
   */
  async downloadFile(sessionId, filename) {
    try {
      const response = await this.client.get(`/dynamic-test/regression/download/${sessionId}/${filename}`, {
        responseType: 'blob'
      })
      
      return response
    } catch (error) {
      console.error('下载文件失败:', error)
      throw error
    }
  }

  /**
   * 批量下载文件
   * @param {string} sessionId - 会话ID
   * @param {Array} filenames - 文件名数组
   * @returns {Promise} 下载结果
   */
  async downloadMultipleFiles(sessionId, filenames) {
    try {
      const downloadPromises = filenames.map(filename => 
        this.downloadFile(sessionId, filename)
      )
      
      const results = await Promise.allSettled(downloadPromises)
      
      const successful = results.filter(result => result.status === 'fulfilled').length
      const failed = results.filter(result => result.status === 'rejected').length
      
      return {
        successful,
        failed,
        total: filenames.length
      }
    } catch (error) {
      console.error('批量下载失败:', error)
      throw error
    }
  }

  /**
   * 验证文件格式
   * @param {File} file - 文件对象
   * @param {Array} allowedTypes - 允许的文件类型
   * @returns {boolean} 是否有效
   */
  validateFileType(file, allowedTypes = ['.docx', '.doc', '.pdf']) {
    const fileName = file.name.toLowerCase()
    return allowedTypes.some(type => fileName.endsWith(type))
  }

  /**
   * 验证文件大小
   * @param {File} file - 文件对象
   * @param {number} maxSize - 最大文件大小（字节）
   * @returns {boolean} 是否有效
   */
  validateFileSize(file, maxSize = 50 * 1024 * 1024) { // 默认50MB
    return file.size <= maxSize
  }

  /**
   * 格式化文件大小
   * @param {number} bytes - 字节数
   * @returns {string} 格式化后的大小
   */
  formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes'
    
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  /**
   * 获取文件扩展名
   * @param {string} filename - 文件名
   * @returns {string} 扩展名
   */
  getFileExtension(filename) {
    return filename.slice((filename.lastIndexOf('.') - 1 >>> 0) + 2)
  }
}

export const regressionService = new RegressionService()
