// 优化的 axios 封装
import axios from 'axios'

// 🔧 计算基础地址：优先使用环境变量；开发环境(5173)且没有配置时直连后端，绕过代理
let computedBaseURL = (import.meta && import.meta.env && import.meta.env.VITE_BASE_API) || '/api'
try {
  if (typeof window !== 'undefined' && !((import.meta && import.meta.env && import.meta.env.VITE_BASE_API))) {
    const { protocol, hostname, port } = window.location
    if (String(port) === '5173') {
      computedBaseURL = `${protocol}//${hostname}:5002/api`
      // eslint-disable-next-line no-console
      console.log(`[request] 开发环境直连后端: ${computedBaseURL}`)
    }
  }
} catch (_) {}

// 🔧 创建axios实例，添加更多配置
const service = axios.create({
  baseURL: computedBaseURL,
  timeout: 1200000, // 20分钟
  // 🔧 添加重试配置
  retry: 3,
  retryDelay: 1000,
  // 这些仅在部分适配器生效，但保留以提高兼容性
  maxContentLength: Infinity,
  maxBodyLength: Infinity,
  // 🔧 允许携带凭证（cookie），配合后端 allow_credentials=True，用于session登录
  withCredentials: true,
})

// 🔧 请求拦截器 - 添加重试逻辑
service.interceptors.request.use(
  (config) => {
    // 🔧 为每个请求添加时间戳，避免缓存问题
    if (config.method === 'get') {
      config.params = {
        ...config.params,
        _t: Date.now()
      }
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 🔧 响应拦截器 - 添加重试和更好的错误处理
service.interceptors.response.use(
  (response) => {
    console.log('[axios拦截器] 收到响应:', response.config.url, response.status, response.data)
    return response.data
  },
  async (error) => {
    console.log('[axios拦截器] 请求错误:', error.config?.url, error.message)
    const config = error.config
    
    // 🔧 重试逻辑
    if (config && config.retry > 0) {
      // 如果是网络错误或超时，进行重试
      const message = String(error.message || '')
      if (
        error.code === 'ECONNABORTED' ||
        message.includes('timeout') ||
        message.includes('Network Error') ||
        message.includes('ERR_EMPTY_RESPONSE')
      ) {
        config.retry -= 1
        
        console.log(`请求重试中... 剩余次数: ${config.retry}`)
        
        // 延迟重试
        await new Promise(resolve => setTimeout(resolve, config.retryDelay))
        
        return service(config)
      }
    }
    
    // 🔧 更详细的错误处理
    let msg = '请求失败'
    if (error.response) {
      // 服务器响应了错误状态码
      const { status, data } = error.response
      switch (status) {
        case 400:
          msg = data?.detail || '请求参数错误'
          break
        case 401:
          msg = '未授权访问'
          break
        case 403:
          msg = '禁止访问'
          break
        case 404:
          msg = '请求的资源不存在'
          break
        case 500:
          msg = data?.detail || '服务器内部错误'
          break
        case 502:
          msg = '网关错误'
          break
        case 503:
          msg = '服务不可用'
          break
        case 504:
          msg = '网关超时'
          break
        default:
          msg = data?.detail || `请求失败 (${status})`
      }
    } else if (error.request) {
      // 请求已发出但没有收到响应
      if (error.code === 'ECONNABORTED') {
        msg = '请求超时，请检查网络连接'
      } else {
        msg = '网络连接失败，请检查网络'
      }
    } else {
      // 请求配置出错
      msg = error.message || '请求配置错误'
    }
    
    console.error('API请求失败:', {
      url: config?.url,
      method: config?.method,
      error: msg,
      originalError: error
    })
    
    return Promise.reject(new Error(msg))
  }
)

export default service
