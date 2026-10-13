/**
 * 回归测试服务
 * 提供与后端API交互的方法
 */

import request from '@/api/request'

export const regressionTestService = {
  // 上传影响域分析报告
  uploadImpactAnalysis(file) {
    const formData = new FormData()
    formData.append('impact_file', file)
    
    return request.post(`/dynamic-test/regression/upload-impact`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 上传策划文档
  uploadPlanning(file, sessionId) {
    const formData = new FormData()
    formData.append('planning_file', file)
    formData.append('session_id', sessionId)
    
    return request.post(`/dynamic-test/regression/upload-planning`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 上传需求目录文档
  uploadCatalog(file, sessionId) {
    const formData = new FormData()
    formData.append('catalog_file', file)
    formData.append('session_id', sessionId)
    
    return request.post(`/dynamic-test/regression/upload-catalog`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 生成回归测试表单
  generateForms(sessionId, basicInfo, optionalInfo = {}, codeLines = null) {
    const formData = new FormData()
    formData.append('session_id', sessionId)
    formData.append('test_manager', basicInfo.testManager)
    formData.append('test_personnel', basicInfo.testPersonnel)
    formData.append('developer', basicInfo.developer)
    formData.append('software_name', basicInfo.softwareName)
    formData.append('software_version', basicInfo.softwareVersion)
    formData.append('software_id', basicInfo.softwareId)
    formData.append('domain', basicInfo.domain)
    formData.append('detector_flag', basicInfo.detectorFlag || '有检测仪')
    formData.append('ai_analysis', basicInfo.aiAnalysis !== false)
    formData.append('deep_analysis', basicInfo.deepAnalysis !== false)
    formData.append('has_planning', basicInfo.hasPlanning || false)
    
    // 添加可选信息
    formData.append('aircraft_model', optionalInfo.aircraftModel || '')
    formData.append('project_director', optionalInfo.projectDirector || '')
    formData.append('development_department', optionalInfo.developmentDepartment || '')
    formData.append('chief_designer', optionalInfo.chiefDesigner || '')
    
    // 添加代码行数（如果有的话）
    if (codeLines !== null && codeLines !== undefined) {
      formData.append('code_lines', codeLines)
    }
    
    return request.post(`/dynamic-test/regression/generate-forms`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 获取任务状态
  getTaskStatus(taskId) {
    return request.get(`/dynamic-test/regression/task-status/${taskId}`)
  },

  // 获取会话状态
  getSessionStatus(sessionId) {
    return request.get(`/dynamic-test/regression/status/${sessionId}`)
  },

  // 下载生成的文件
  downloadFile(sessionId, filename) {
    return request.get(`/dynamic-test/regression/download/${sessionId}/${filename}`, {
      responseType: 'blob'
    })
  },

  // 获取下拉数据
  getDomains() {
    return request.get(`/dynamic-test/regression/dropdown-data/domains`)
  },

  getTestManagers() {
    return request.get(`/dynamic-test/regression/dropdown-data/test-managers`)
  },

  getTestPersonnel() {
    return request.get(`/dynamic-test/regression/dropdown-data/test-personnel`)
  },

  getDevelopers() {
    return request.get(`/dynamic-test/regression/dropdown-data/developers`)
  },

  // 添加下拉数据
  addDomain(name) {
    const formData = new FormData()
    formData.append('name', name)
    return request.post(`/dynamic-test/regression/dropdown-data/domains`, formData)
  },

  addTestManager(name) {
    const formData = new FormData()
    formData.append('name', name)
    return request.post(`/dynamic-test/regression/dropdown-data/test-managers`, formData)
  },

  addTestPersonnel(name) {
    const formData = new FormData()
    formData.append('name', name)
    return request.post(`/dynamic-test/regression/dropdown-data/test-personnel`, formData)
  },

  addDeveloper(name) {
    const formData = new FormData()
    formData.append('name', name)
    return request.post(`/dynamic-test/regression/dropdown-data/developers`, formData)
  },

  // ================= 可选信息相关接口 =================
  
  // 获取可选信息下拉数据
  getAircraftModels() {
    return request.get(`/dynamic-test/regression/dropdown-data/aircraft-models`)
  },

  getProjectDirectors() {
    return request.get(`/dynamic-test/regression/dropdown-data/project-directors`)
  },

  getDevelopmentDepartments() {
    return request.get(`/dynamic-test/regression/dropdown-data/development-departments`)
  },

  getChiefDesigners() {
    return request.get(`/dynamic-test/regression/dropdown-data/chief-designers`)
  },

  // 添加可选信息下拉数据
  addAircraftModel(name) {
    const formData = new FormData()
    formData.append('name', name)
    return request.post(`/dynamic-test/regression/dropdown-data/aircraft-models`, formData)
  },

  addProjectDirector(name) {
    const formData = new FormData()
    formData.append('name', name)
    return request.post(`/dynamic-test/regression/dropdown-data/project-directors`, formData)
  },

  addDevelopmentDepartment(name) {
    const formData = new FormData()
    formData.append('name', name)
    return request.post(`/dynamic-test/regression/dropdown-data/development-departments`, formData)
  },

  addChiefDesigner(name) {
    const formData = new FormData()
    formData.append('name', name)
    return request.post(`/dynamic-test/regression/dropdown-data/chief-designers`, formData)
  },

  // OCR图片识别
  extractDataFromImage(imageData) {
    return request.post(`/dynamic-test/regression/ocr/extract-from-image`, {
      image_data: imageData
    })
  },

  // 测试OCR连接
  testOCRConnection() {
    return request.post(`/dynamic-test/regression/ocr/test-connection`)
  },

  // ============== 代码统计相关 ==============
  
  // 上传代码文件进行分析
  uploadCodeForAnalysis(file, taskId = null) {
    const formData = new FormData()
    formData.append('code_file', file)
    if (taskId) {
      formData.append('task_id', taskId)
    }
    
    return request.post(`/dynamic-test/regression/upload-code`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 获取代码分析结果
  getCodeAnalysisResult(taskId) {
    return request.get(`/dynamic-test/regression/code-analysis/${taskId}`)
  },

  // 删除代码分析任务
  deleteCodeAnalysis(taskId) {
    return request.delete(`/dynamic-test/regression/code-analysis/${taskId}`)
  }
}