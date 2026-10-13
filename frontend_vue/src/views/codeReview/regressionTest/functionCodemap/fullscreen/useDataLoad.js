import { nextTick } from 'vue'

export function useDataLoad({ taskId, axios, ElMessage, codeMapData, statistics, changesData, buildCompareTrees }) {
  async function loadCodeMap() {
    if (!taskId.value) return

    try {
      const response = await axios.get(`/api/codeReview/regressionTest/functionReview/codemap/${taskId.value}`)
      if (response.data?.success) {
        codeMapData.value = response.data.data
        statistics.value = response.data.data?.statistics
        await nextTick()
        ElMessage.success('代码地图加载成功')
      } else {
        ElMessage.error('加载代码地图失败')
      }
    } catch (error) {
      console.error('加载代码地图失败:', error)
      ElMessage.error('加载代码地图失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  async function loadChanges() {
    if (!taskId.value) return

    try {
      const res = await axios.get(`/api/codeReview/regressionTest/regression/changes/${taskId.value}`, {
        params: { refresh: false }
      })
      changesData.value = res.data
      buildCompareTrees()
    } catch (error) {
      console.error('加载变更列表失败:', error)
      ElMessage.error('加载变更列表失败')
    }
  }

  return { loadCodeMap, loadChanges }
}
