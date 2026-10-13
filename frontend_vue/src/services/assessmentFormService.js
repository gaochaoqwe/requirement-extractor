/**
 * 鉴定测评表单辅助工具服务 - 极简版
 */
import request from '../api/request'

const assessmentFormService = {
  /**
   * 上传Excel文件
   */
  async uploadFile(file) {
    const formData = new FormData()
    formData.append('file', file)
    return await request.post('/test-tools/assessment-form-helper/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  /**
   * 获取会话处理状态
   */
  async getSessionStatus(sessionId) {
    return await request.get(`/test-tools/assessment-form-helper/status/${sessionId}`)
  },

  /**
   * 生成输出文件
   */
  async generateOutputFile(sessionId) {
    return await request.post(`/test-tools/assessment-form-helper/download/${sessionId}`)
  },

  /**
   * 下载文件
   */
  async downloadFile(sessionId, filename) {
    const response = await request.get(`/test-tools/assessment-form-helper/download/${sessionId}/${filename}`, {
      responseType: 'blob'
    })

    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)

    return { success: true }
  }
}

export default assessmentFormService 