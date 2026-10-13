/**
 * 问题标记功能工具
 * 用于在浏览器本地存储已标记的问题
 */

const STORAGE_KEY_PREFIX = 'static_analysis_marked_problems_'

/**
 * 构建问题的唯一键
 * @param {Object} problem - 问题对象
 * @returns {String} - 唯一键
 */
export function buildProblemKey(problem) {
  const parts = [
    problem.id || '',
    problem.issue_file || '',
    problem.issue_name || '',
    problem.issue_line || '',
    problem.rule_code || ''
  ]
  return parts.filter(p => p).join('_')
}

/**
 * 获取指定会话的存储键
 * @param {String} sessionId - 会话ID
 * @param {String} ruleType - 规则类型 (gjb/cwe)
 * @returns {String} - 存储键
 */
function getStorageKey(sessionId, ruleType) {
  return `${STORAGE_KEY_PREFIX}${sessionId}_${ruleType}`
}

/**
 * 保存标记的问题
 * @param {String} sessionId - 会话ID
 * @param {String} ruleType - 规则类型
 * @param {Object} markedData - 标记数据 {key, problem}
 */
export function saveMarkedProblem(sessionId, ruleType, markedData) {
  const storageKey = getStorageKey(sessionId, ruleType)
  
  try {
    // 获取现有数据
    const existing = localStorage.getItem(storageKey)
    const markedMap = existing ? JSON.parse(existing) : {}
    
    // 添加新标记
    markedMap[markedData.key] = {
      problem: markedData.problem,
      markedAt: new Date().toISOString()
    }
    
    // 保存到本地存储
    localStorage.setItem(storageKey, JSON.stringify(markedMap))
    
    console.log('[问题标记] 保存标记:', markedData.key)
  } catch (error) {
    console.error('[问题标记] 保存失败:', error)
  }
}

/**
 * 移除标记的问题
 * @param {String} sessionId - 会话ID
 * @param {String} ruleType - 规则类型
 * @param {String} problemKey - 问题键
 */
export function removeMarkedProblem(sessionId, ruleType, problemKey) {
  const storageKey = getStorageKey(sessionId, ruleType)
  
  try {
    const existing = localStorage.getItem(storageKey)
    if (!existing) return
    
    const markedMap = JSON.parse(existing)
    delete markedMap[problemKey]
    
    localStorage.setItem(storageKey, JSON.stringify(markedMap))
    
    console.log('[问题标记] 移除标记:', problemKey)
  } catch (error) {
    console.error('[问题标记] 移除失败:', error)
  }
}

/**
 * 获取已标记问题的键集合
 * @param {String} sessionId - 会话ID
 * @param {String} ruleType - 规则类型
 * @returns {Set} - 问题键集合
 */
export function getMarkedProblemSet(sessionId, ruleType) {
  const storageKey = getStorageKey(sessionId, ruleType)
  
  try {
    const existing = localStorage.getItem(storageKey)
    if (!existing) return new Set()
    
    const markedMap = JSON.parse(existing)
    return new Set(Object.keys(markedMap))
  } catch (error) {
    console.error('[问题标记] 获取失败:', error)
    return new Set()
  }
}

/**
 * 获取所有已标记的问题详情
 * @param {String} sessionId - 会话ID
 * @param {String} ruleType - 规则类型
 * @returns {Array} - 问题数组
 */
export function getMarkedProblems(sessionId, ruleType) {
  const storageKey = getStorageKey(sessionId, ruleType)
  
  try {
    const existing = localStorage.getItem(storageKey)
    if (!existing) return []
    
    const markedMap = JSON.parse(existing)
    return Object.values(markedMap).map(item => item.problem)
  } catch (error) {
    console.error('[问题标记] 获取失败:', error)
    return []
  }
}

/**
 * 清除指定会话的所有标记
 * @param {String} sessionId - 会话ID
 * @param {String} ruleType - 规则类型
 */
export function clearMarkedProblems(sessionId, ruleType) {
  const storageKey = getStorageKey(sessionId, ruleType)
  
  try {
    localStorage.removeItem(storageKey)
    console.log('[问题标记] 清除所有标记')
  } catch (error) {
    console.error('[问题标记] 清除失败:', error)
  }
}

