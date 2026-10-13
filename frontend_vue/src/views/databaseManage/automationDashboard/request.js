import axios from 'axios'

let computedBaseURL = (import.meta && import.meta.env && import.meta.env.VITE_BASE_API) || '/api'

try {
  if (typeof window !== 'undefined' && !((import.meta && import.meta.env && import.meta.env.VITE_BASE_API))) {
    const { protocol, hostname, port } = window.location
    if (String(port) === '5173') {
      computedBaseURL = `${protocol}//${hostname}:5002/api`
    }
  }
} catch (_) {}

const service = axios.create({
  baseURL: computedBaseURL,
  timeout: 30000,
  withCredentials: true,
})

service.interceptors.request.use(
  (config) => {
    if (config.method === 'get') {
      config.params = { ...config.params, _t: Date.now() }
    }
    return config
  },
  (error) => Promise.reject(error)
)

service.interceptors.response.use(
  (response) => response.data,
  (error) => {
    let msg = '请求失败'
    if (error.response) {
      const { status, data } = error.response
      msg = data?.detail || `请求失败 (${status})`
    } else if (error.request) {
      msg = '网络连接失败'
    } else {
      msg = error.message || '请求配置错误'
    }
    return Promise.reject(new Error(msg))
  }
)

export default service
