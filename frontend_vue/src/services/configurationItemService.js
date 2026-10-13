/**
 * 配置项测试服务
 * 提供与后端API交互的方法
 */

import request from '@/api/request'

export const configurationItemService = {
  // 上传需求文档
  uploadRequirement(file) {
    const formData = new FormData()
    formData.append('requirement_file', file)
    
    return request.post(`/dynamic-test/configuration-item/upload-requirement`, formData, {
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
    
    return request.post(`/dynamic-test/configuration-item/upload-planning`, formData, {
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
    
    return request.post(`/dynamic-test/configuration-item/upload-catalog`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 生成配置项测试表单（异步任务）
  generateForms(sessionId, basicInfo, optionalInfo = {}, codeLines = null) {
    // 添加调试日志
    console.log('🔍 [DEBUG] generateForms调用参数:')
    console.log('  sessionId:', sessionId)
    console.log('  basicInfo:', basicInfo)
    console.log('  optionalInfo:', optionalInfo)
    console.log('  codeLines:', codeLines)
    console.log('  optionalInfo.developmentDepartment:', optionalInfo.developmentDepartment)
    
    const formData = new FormData()
    formData.append('session_id', sessionId)
    formData.append('test_manager', basicInfo.testManager)
    formData.append('test_personnel', basicInfo.testPersonnel)
    formData.append('developer', basicInfo.developer)
    formData.append('software_name', basicInfo.softwareName)
    formData.append('software_version', basicInfo.softwareVersion)
    formData.append('software_id', basicInfo.softwareId)
    formData.append('domain', basicInfo.domain)
    formData.append('product_type', basicInfo.productType)
    formData.append('detector_flag', basicInfo.detectorFlag || '有检测仪')
    formData.append('ai_analysis', basicInfo.aiAnalysis !== false)
    formData.append('deep_analysis', basicInfo.deepAnalysis !== false)
    formData.append('has_planning', basicInfo.hasPlanning || false)
    
    // 添加可选信息
    formData.append('aircraft_model', optionalInfo.aircraftModel || '')
    formData.append('project_director', optionalInfo.projectDirector || '')
    formData.append('development_department', optionalInfo.developmentDepartment || '')
    formData.append('chief_designer', optionalInfo.chiefDesigner || '')
    formData.append('project_manager', optionalInfo.projectManager || '')
    
    // 添加调试日志 - 显示实际发送的值
    console.log('🔍 [DEBUG] 实际发送的development_department值:', optionalInfo.developmentDepartment || '')
    
    // 添加代码行数（如果有的话）
    if (codeLines !== null && codeLines !== undefined) {
      formData.append('code_lines', codeLines)
    }
    
    return request.post(`/dynamic-test/configuration-item/generate-forms`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 获取任务状态
  getTaskStatus(taskId) {
    return request.get(`/dynamic-test/configuration-item/task-status/${taskId}`)
  },

  // 获取会话状态
  getSessionStatus(sessionId) {
    return request.get(`/dynamic-test/configuration-item/status/${sessionId}`)
  },

  // 下载生成的文件
  downloadFile(sessionId, filename) {
    return request.get(`/dynamic-test/configuration-item/download/${sessionId}/${filename}`, {
      responseType: 'blob'
    })
  },

  // 获取下拉数据
  getDomains() {
    return request.get(`/dynamic-test/configuration-item/dropdown-data/domains`)
  },

  getTestManagers() {
    return request.get(`/dynamic-test/configuration-item/dropdown-data/test-managers`)
  },

  getTestPersonnel() {
    return request.get(`/dynamic-test/configuration-item/dropdown-data/test-personnel`)
  },

  getDevelopers() {
    return request.get(`/dynamic-test/configuration-item/dropdown-data/developers`)
  },

  // 添加下拉数据
  addDomain(name) {
    const formData = new FormData()
    formData.append('name', name)
    return request.post(`/dynamic-test/configuration-item/dropdown-data/domains`, formData)
  },

  addTestManager(name) {
    const formData = new FormData()
    formData.append('name', name)
    return request.post(`/dynamic-test/configuration-item/dropdown-data/test-managers`, formData)
  },

  addTestPersonnel(name) {
    const formData = new FormData()
    formData.append('name', name)
    return request.post(`/dynamic-test/configuration-item/dropdown-data/test-personnel`, formData)
  },

  addDeveloper(name) {
    const formData = new FormData()
    formData.append('name', name)
    return request.post(`/dynamic-test/configuration-item/dropdown-data/developers`, formData)
  },

  // ================= 可选信息相关接口 =================
  
  // 获取可选信息下拉数据
  getAircraftModels() {
    return request.get(`/dynamic-test/configuration-item/dropdown-data/aircraft-models`)
  },

  getProjectDirectors() {
    return request.get(`/dynamic-test/configuration-item/dropdown-data/project-directors`)
  },

  getDevelopmentDepartments() {
    return request.get(`/dynamic-test/configuration-item/dropdown-data/development-departments`)
  },

  getChiefDesigners() {
    return request.get(`/dynamic-test/configuration-item/dropdown-data/chief-designers`)
  },

  getProjectManagers() {
    return request.get(`/dynamic-test/configuration-item/dropdown-data/project-managers`)
  },

  // 添加可选信息下拉数据
  addAircraftModel(name) {
    const formData = new FormData()
    formData.append('name', name)
    return request.post(`/dynamic-test/configuration-item/dropdown-data/aircraft-models`, formData)
  },

  addProjectDirector(name) {
    const formData = new FormData()
    formData.append('name', name)
    return request.post(`/dynamic-test/configuration-item/dropdown-data/project-directors`, formData)
  },

  addDevelopmentDepartment(name) {
    const formData = new FormData()
    formData.append('name', name)
    return request.post(`/dynamic-test/configuration-item/dropdown-data/development-departments`, formData)
  },

  addChiefDesigner(name) {
    const formData = new FormData()
    formData.append('name', name)
    return request.post(`/dynamic-test/configuration-item/dropdown-data/chief-designers`, formData)
  },

  addProjectManager(name) {
    const formData = new FormData()
    formData.append('name', name)
    return request.post(`/dynamic-test/configuration-item/dropdown-data/project-managers`, formData)
  },

  // OCR图片识别
  extractDataFromImage(imageData) {
    return request.post(`/dynamic-test/configuration-item/ocr/extract-from-image`, {
      image_data: imageData
    })
  },

  // 测试OCR连接
  testOCRConnection() {
    return request.post(`/dynamic-test/configuration-item/ocr/test-connection`)
  },

  // ============== 代码统计相关 ==============
  
  // 上传代码文件进行分析
  uploadCodeForAnalysis(file, taskId = null) {
    const formData = new FormData()
    formData.append('code_file', file)
    if (taskId) {
      formData.append('task_id', taskId)
    }
    
    return request.post(`/dynamic-test/configuration-item/upload-code`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 获取代码分析结果
  getCodeAnalysisResult(taskId) {
    return request.get(`/dynamic-test/configuration-item/code-analysis/${taskId}`)
  },

  // 删除代码分析任务
  deleteCodeAnalysis(taskId) {
    return request.delete(`/dynamic-test/configuration-item/code-analysis/${taskId}`)
  },

  // ============== 目录提取相关 ==============
  
  // 确认目录内容
  confirmCatalog(sessionId, catalogContent) {
    const formData = new FormData()
    formData.append('session_id', sessionId)
    formData.append('catalog_content', catalogContent)
    
    return request.post(`/dynamic-test/configuration-item/confirm-catalog`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 重新提取目录
  reExtractCatalog(sessionId) {
    return request.get(`/dynamic-test/configuration-item/extract-catalog/${sessionId}?force=true`)
  },

  // 轮询获取目录提取结果（不触发重提取）
  getCatalogExtraction(sessionId) {
    return request.get(`/dynamic-test/configuration-item/extract-catalog/${sessionId}`)
  },

  // ============== 软件信息相关 ==============
  
  // 从需求文档中提取软件信息
  extractSoftwareInfo(sessionId) {
    return request.post(`/dynamic-test/configuration-item/extract-software-info/${sessionId}`)
  },

  // 获取软件信息
  getSoftwareInfo(sessionId) {
    return request.get(`/dynamic-test/configuration-item/software-info/${sessionId}`)
  },

  // 更新软件信息
  updateSoftwareInfo(sessionId, softwareInfo) {
    const formData = new FormData()
    formData.append('software_name', softwareInfo.softwareName || '')
    formData.append('software_version', softwareInfo.softwareVersion || '')
    formData.append('software_id', softwareInfo.softwareId || '')
    
    return request.post(`/dynamic-test/configuration-item/update-software-info/${sessionId}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 删除软件信息
  deleteSoftwareInfo(sessionId) {
    return request.delete(`/dynamic-test/configuration-item/software-info/${sessionId}`)
  },

  // 列出所有包含软件信息的会话
  listSessionsWithSoftwareInfo() {
    return request.get(`/dynamic-test/configuration-item/sessions-with-software-info`)
  },

  // ============================================================================
  // 分步生成API方法
  // ============================================================================

  // 步骤1: 生成项目信息表
  generateProjectInfo(sessionId, basicInfo, optionalInfo = {}, codeLines = null) {
    const formData = new FormData()
    formData.append('session_id', sessionId)
    formData.append('test_manager', basicInfo.testManager)
    formData.append('test_personnel', basicInfo.testPersonnel)
    formData.append('developer', basicInfo.developer)
    formData.append('software_name', basicInfo.softwareName)
    formData.append('software_version', basicInfo.softwareVersion)
    formData.append('software_id', basicInfo.softwareId)
    formData.append('domain', basicInfo.domain)
    formData.append('product_type', basicInfo.productType)
    formData.append('detector_flag', basicInfo.detectorFlag || '有检测仪')
    
    // 添加可选信息
    formData.append('aircraft_model', optionalInfo.aircraftModel || '')
    formData.append('project_director', optionalInfo.projectDirector || '')
    formData.append('development_department', optionalInfo.developmentDepartment || '')
    formData.append('chief_designer', optionalInfo.chiefDesigner || '')
    formData.append('project_manager', optionalInfo.projectManager || '')
    
    // 添加代码行数
    if (codeLines !== null && codeLines !== undefined) {
      formData.append('code_lines', codeLines)
    }
    
    return request.post(`/dynamic-test/configuration-item/generate-step1-project-info`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 步骤2前置: 上传步骤1生成的文件
  uploadStep1Result(formData) {
    return request.post(`/dynamic-test/configuration-item/upload-step1-result`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 步骤3前置: 上传步骤2生成的文件
  uploadStep2Result(formData) {
    return request.post(`/dynamic-test/configuration-item/upload-step2-result`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 步骤4前置: 上传步骤3生成的文件
  uploadStep3Result(formData) {
    return request.post(`/dynamic-test/configuration-item/upload-step3-result`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 步骤2: 生成策划表与问题单
  generateTestIssue(sessionId) {
    const formData = new FormData()
    formData.append('session_id', sessionId)
    
    return request.post(`/dynamic-test/configuration-item/generate-step2-test-issue`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 步骤3a: 生成需求分析表基础信息
  generateRequirementBasic(sessionId, aiAnalysis = true, deepAnalysis = true) {
    const formData = new FormData()
    formData.append('session_id', sessionId)
    formData.append('ai_analysis', aiAnalysis)
    formData.append('deep_analysis', deepAnalysis)
    
    return request.post(`/dynamic-test/configuration-item/generate-step3a-requirement-basic`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 步骤3a上传: 上传需求分析表基础版
  uploadStep3aResult(formData) {
    return request.post(`/dynamic-test/configuration-item/upload-step3a-result`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 步骤3b: 完善需求分析表（测试项）
  generateTestItems(sessionId, aiAnalysis = true) {
    const formData = new FormData()
    formData.append('session_id', sessionId)
    formData.append('ai_analysis', aiAnalysis)
    
    return request.post(`/dynamic-test/configuration-item/generate-step3b-test-items`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 步骤3: 生成需求分析表（保留用于兼容）
  generateRequirementAnalysis(sessionId, aiAnalysis = true, deepAnalysis = true) {
    const formData = new FormData()
    formData.append('session_id', sessionId)
    formData.append('ai_analysis', aiAnalysis)
    formData.append('deep_analysis', deepAnalysis)
    
    return request.post(`/dynamic-test/configuration-item/generate-step3-requirement-analysis`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 步骤4: 生成测试用例单
  generateTestCase(sessionId, aiAnalysis = true) {
    const formData = new FormData()
    formData.append('session_id', sessionId)
    formData.append('ai_analysis', aiAnalysis)
    
    return request.post(`/dynamic-test/configuration-item/generate-step4-test-case`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 获取生成状态
  getGenerationState(sessionId) {
    return request.get(`/dynamic-test/configuration-item/generation-state/${sessionId}`)
  }
}
