import request from './request'

const BASE = '/database/automation-dashboard'

export function listConfigs() {
  return request.get(`${BASE}/configs`)
}

export function getConfig(configId) {
  return request.get(`${BASE}/configs/${configId}`)
}

export function createConfig(data) {
  return request.post(`${BASE}/configs`, data)
}

export function updateConfig(configId, data) {
  return request.put(`${BASE}/configs/${configId}`, data)
}

export function deleteConfig(configId) {
  return request.delete(`${BASE}/configs/${configId}`)
}

export function bulkReplacePhases(configId, phases) {
  return request.put(`${BASE}/configs/${configId}/phases`, { phases })
}

export function addPhase(configId, data) {
  return request.post(`${BASE}/configs/${configId}/phases`, data)
}

export function updatePhase(phaseId, data) {
  return request.put(`${BASE}/phases/${phaseId}`, data)
}

export function deletePhase(phaseId) {
  return request.delete(`${BASE}/phases/${phaseId}`)
}

export function bulkReplaceSubSteps(phaseId, subSteps) {
  return request.put(`${BASE}/phases/${phaseId}/sub-steps`, { sub_steps: subSteps })
}

export function addSubStep(phaseId, data) {
  return request.post(`${BASE}/phases/${phaseId}/sub-steps`, data)
}

export function updateSubStep(subStepId, data) {
  return request.put(`${BASE}/sub-steps/${subStepId}`, data)
}

export function deleteSubStep(subStepId) {
  return request.delete(`${BASE}/sub-steps/${subStepId}`)
}
