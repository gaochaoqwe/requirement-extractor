/**
 * 静态分析自动修复服务
 *
 * 三个粒度：single（单问题）/ file（文件级）/ rule（规则级）
 * 导出两种模式：导出当前文件 / 导出修复后的代码库(zip)
 */
import request from '@/api/request'
import axios from 'axios'

const BASE_URL = '/staticAnalysis/filter'

function getBaseApi() {
  return (import.meta && import.meta.env && import.meta.env.VITE_BASE_API) || '/api'
}

/**
 * 通用 blob 下载，catch 时把 Blob 解析回 JSON 取 detail
 * （参照 codeReview 函数审查导出注释代码的错误处理）
 */
async function downloadBlob(url, fallbackName) {
  try {
    const response = await axios.get(url, {
      responseType: 'blob',
      withCredentials: true
    })

    // 从 Content-Disposition 解析文件名
    let filename = fallbackName
    const disposition = response.headers?.['content-disposition'] || ''
    const utf8Match = disposition.match(/filename\*=UTF-8''([^;]+)/i)
    const plainMatch = disposition.match(/filename="?([^";]+)"?/i)
    if (utf8Match) {
      try {
        filename = decodeURIComponent(utf8Match[1])
      } catch (e) {
        filename = utf8Match[1]
      }
    } else if (plainMatch) {
      filename = plainMatch[1]
    }

    const blob = new Blob([response.data])
    const objectUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = objectUrl
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(objectUrl)
    return { success: true, filename }
  } catch (error) {
    // 后端报错时返回的是 JSON blob，先还原成文本再抛错
    let detail = error.message
    try {
      if (error.response?.data instanceof Blob) {
        const text = await error.response.data.text()
        try {
          detail = JSON.parse(text).detail || text
        } catch (e) {
          detail = text
        }
      } else if (error.response?.data?.detail) {
        detail = error.response.data.detail
      }
    } catch (e) {
      // ignore
    }
    throw new Error(detail)
  }
}

const staticAnalysisFixService = {
  /**
   * 创建修复任务
   * @param {string} taskId
   * @param {Object} payload { scope: {type, value}, problem_ids, user_prompt, options, rule_type }
   */
  async generate(taskId, payload) {
    try {
      return await request.post(`${BASE_URL}/${taskId}/fix/generate`, payload)
    } catch (error) {
      console.error('[修复] 创建修复任务失败:', error)
      throw error
    }
  },

  /** 轮询进度 */
  async getStatus(taskId, fixTaskId) {
    return request.get(`${BASE_URL}/${taskId}/fix/status/${fixTaskId}`)
  },

  /** 获取修复条目列表 */
  async listFixes(taskId, fixTaskId) {
    return request.get(`${BASE_URL}/${taskId}/fix/list/${fixTaskId}`)
  },

  /** 应用（落盘） */
  async apply(taskId, fixIds) {
    return request.post(`${BASE_URL}/${taskId}/fix/apply`, { fix_ids: fixIds })
  },

  /** 回滚 */
  async rollback(taskId, fixIds) {
    return request.post(`${BASE_URL}/${taskId}/fix/rollback`, { fix_ids: fixIds })
  },

  /** 带新提示词重新生成 */
  async regenerate(taskId, fixId, userPrompt = '') {
    return request.post(`${BASE_URL}/${taskId}/fix/regenerate`, {
      fix_id: fixId,
      user_prompt: userPrompt
    })
  },

  /** 已应用修复的文件列表 */
  async getFixedFiles(taskId) {
    return request.get(`${BASE_URL}/${taskId}/fix/fixed-files`)
  },

  /** 导出当前文件（单文件，不打包） */
  async exportCurrentFile(taskId, filePath) {
    const url = `${getBaseApi()}${BASE_URL}/${taskId}/fix/export-file?file_path=${encodeURIComponent(filePath)}`
    const name = (filePath || 'source.txt').split(/[/\\]/).pop()
    return downloadBlob(url, name)
  },

  /** 导出修复后的代码库（zip） */
  async exportPackage(taskId) {
    const url = `${getBaseApi()}${BASE_URL}/${taskId}/fix/export-package`
    return downloadBlob(url, 'fixed_codebase.zip')
  }
}

export default staticAnalysisFixService
