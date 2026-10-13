import request from '../api/request'

const BASE_URL = '/test-tools/document-annotations-to-problems'

const documentAnnotationsService = {
  // 上传文件
  async uploadFile(file) {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await request.post(`${BASE_URL}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    return response
  },

  // 获取会话状态
  async getSessionStatus(sessionId) {
    const response = await request.get(`${BASE_URL}/status/${sessionId}`)
    return response
  },

  // 生成输出文件
  async generateOutputFile(sessionId) {
    const response = await request.post(`${BASE_URL}/generate/${sessionId}`)
    return response
  },

  // 下载文件
  async downloadFile(sessionId) {
    const response = await request.get(`${BASE_URL}/download/${sessionId}`, {
      responseType: 'blob'
    })
    return response
  }
}

export default documentAnnotationsService 