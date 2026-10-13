/**
 * 测试用例总结工具服务
 */
import request from '@/api/request'

const API_BASE = '/test-tools/test-case-summary'

export default {
  /**
   * 上传测试用例Excel文件
   */
  async uploadFile(file) {
    console.log('开始上传文件:', file.name, '到URL:', `${API_BASE}/upload`)
    
    const formData = new FormData()
    formData.append('file', file)
    
    try {
      const response = await request.post(`${API_BASE}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        timeout: 300000 // 5分钟超时
      })
      
      console.log('上传请求响应:', response)
      return response
    } catch (error) {
      console.error('上传请求失败:', error)
      console.error('错误状态:', error.response?.status)
      console.error('错误数据:', error.response?.data)
      throw error
    }
  },

  /**
   * 获取会话处理状态
   */
  async getSessionStatus(sessionId) {
    const response = await request.get(`${API_BASE}/status/${sessionId}`)
    return response
  },

  /**
   * 获取失败测试项
   */
  async getFailedItems(sessionId) {
    const response = await request.get(`${API_BASE}/failed-items/${sessionId}`)
    return response
  },

  /**
   * 手动重试单个测试项
   */
  async retrySingleItem(sessionId, itemId) {
    const response = await request.post(`${API_BASE}/retry/${sessionId}/${itemId}`)
    return response
  },

  /**
   * 生成输出文件
   */
  async generateOutputFile(sessionId) {
    const response = await request.post(`${API_BASE}/download/${sessionId}`)
    return response
  },

  /**
   * 获取下载链接
   */
  async getDownloadUrl(sessionId) {
    try {
      // 首先确保文件已生成
      const generateResult = await this.generateOutputFile(sessionId)
      
      if (!generateResult.success) {
        throw new Error(generateResult.error || '生成文件失败')
      }
      
      // 返回完整的下载URL
      const baseUrl = window.location.origin
      return `${baseUrl}/api${API_BASE}/download/${sessionId}/${generateResult.filename}`
    } catch (error) {
      console.error('获取下载链接失败:', error)
      throw error
    }
  },

  /**
   * 管理员：获取全部会话统计数据
   */
  async getAdminTasks(limit = 500) {
    const response = await request.get(`${API_BASE}/admin/tasks`, { params: { limit } })
    return response
  },

  /**
   * 健康检查
   */
  async healthCheck() {
    const response = await request.get(`${API_BASE}/health`)
    return response.data
  }
} 