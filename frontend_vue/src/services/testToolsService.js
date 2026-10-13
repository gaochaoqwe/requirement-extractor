/**
 * 测试工具服务
 * 提供测试工具相关的API调用
 */
import request from '../api/request'

const testToolsService = {
  /**
   * 获取测试工具列表
   */
  async getToolsList() {
    try {
      const response = await request.get('/test-tools/list')
      return response
    } catch (error) {
      console.error('获取工具列表失败:', error)
      throw error
    }
  }
}

export default testToolsService 