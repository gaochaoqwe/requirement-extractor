import request from '@/api/request'

const BASE_URL = '/test-tools/test-case-reverse'

export default {
  /**
   * 上传测试用例Excel文件
   * @param {File} file - Excel文件
   * @param {string} processingMode - 处理模式 ('normal' 或 'template')
   * @returns {Promise<Object>} 上传结果
   */
  async uploadFile(file, processingMode = 'normal') {
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('processing_mode', processingMode)
      
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
   * @returns {Promise<Object>} 生成结果
   */
  async generateOutputFile(sessionId) {
    try {
      const response = await request.post(`${BASE_URL}/generate_output_file/${sessionId}`)
      return response
    } catch (error) {
      console.error('生成输出文件失败:', error)
      throw error
    }
  },

  /**
   * 下载结果文件
   * @param {string} sessionId - 会话ID
   * @returns {string} 下载URL
   */
  getDownloadUrl(sessionId) {
    return `${window.location.origin}/api${BASE_URL}/download/${sessionId}`
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
  }
} 