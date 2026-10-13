import request from '../api/request'

const BASE_URL = '/test-tools/test-environment-diagram'

const testEnvironmentService = {
  // 创建测试环境图
  createEnvironmentDiagram(deviceInfo) {
    return request({
      url: `${BASE_URL}/create`,
      method: 'post',
      data: deviceInfo
    })
  },

  // 获取会话状态
  getSessionStatus(sessionId) {
    return request({
      url: `${BASE_URL}/status/${sessionId}`,
      method: 'get'
    })
  },

  // 获取图表结果
  getDiagramResult(sessionId) {
    return request({
      url: `${BASE_URL}/result/${sessionId}`,
      method: 'get'
    })
  },

  // 健康检查
  healthCheck() {
    return request({
      url: `${BASE_URL}/health`,
      method: 'get'
    })
  }
}

export default testEnvironmentService 