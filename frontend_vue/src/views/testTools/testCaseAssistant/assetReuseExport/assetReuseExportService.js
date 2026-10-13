import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

export const assetReuseExportService = {
  start(formData) {
    return apiClient.post('/test-tools/test-case-assistant/asset-reuse-export/start', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  progress(taskId) {
    return apiClient.get(`/test-tools/test-case-assistant/asset-reuse-export/progress/${taskId}`)
  },

  download(taskId) {
    return apiClient.get(`/test-tools/test-case-assistant/asset-reuse-export/download/${taskId}`, {
      responseType: 'blob',
    })
  },
}
