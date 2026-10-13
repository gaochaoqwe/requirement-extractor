import request from './request'

export function getOptoGraph(params) {
  return request.get('/database/opto-knowledge/graph', { params })
}

export function getOptoNode(id) {
  return request.get(`/database/opto-knowledge/node/${id}`)
}

export function createOptoNode(data) {
  return request.post('/database/opto-knowledge/node', data)
}

export function updateOptoNode(id, data) {
  return request.put(`/database/opto-knowledge/node/${id}`, data)
}

export function deleteOptoNode(id) {
  return request.delete(`/database/opto-knowledge/node/${id}`)
}

export function createOptoEdge(data) {
  return request.post('/database/opto-knowledge/edge', data)
}

export function deleteOptoEdge(id) {
  return request.delete(`/database/opto-knowledge/edge/${id}`)
}

export function uploadOptoAsset({ nodeId, assetType, file }) {
  const form = new FormData()
  form.append('file', file)
  return request.post(
    `/database/opto-knowledge/asset/upload?node_id=${encodeURIComponent(nodeId)}&asset_type=${encodeURIComponent(assetType)}`,
    form,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  )
}
