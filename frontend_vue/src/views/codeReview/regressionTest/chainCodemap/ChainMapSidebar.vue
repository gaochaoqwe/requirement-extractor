import { buildProblemKey } from '../shared/problemMarking';
import { ref, watch } from 'vue';
import { ElMessage } from 'element-plus';
import axios from 'axios';

const props = defineProps({
  taskId: {
    type: String,
    required: true,
  },
});

const markedProblems = ref(new Set());
const loading = ref(false);

// 从后端加载标记状态
async function loadMarkedProblems() {
  if (!props.taskId) return;
  
  try {
    loading.value = true;
    const response = await axios.get(`/api/codeReview/regressionTest/${props.taskId}/marked_problems`, {
      params: { analysis_type: 'chain' }
    });
    
    if (response.data.success) {
      const keys = response.data.data.map(item => item.problem_key);
      markedProblems.value = new Set(keys);
    }
  } catch (error) {
    console.error('加载标记问题失败:', error);
  } finally {
    loading.value = false;
  }
}

// 监听任务ID变化，重新加载标记状态
watch(
  () => props.taskId,
  (newTaskId) => {
    if (newTaskId) {
      loadMarkedProblems();
    }
  },
  { immediate: true }
);

// 切换问题标记状态
async function toggleProblemMark(problem) {
  const problemKey = buildProblemKey(problem);
  const isMarked = markedProblems.value.has(problemKey);
  
  try {
    if (isMarked) {
      // 取消标记
      await axios.delete(`/api/codeReview/regressionTest/${props.taskId}/marked_problems`, {
        data: {
          analysis_type: 'chain',
          problem_key: problemKey
        }
      });
      markedProblems.value.delete(problemKey);
      ElMessage.success('已取消标记');
    } else {
      // 添加标记
      await axios.post(`/api/codeReview/regressionTest/${props.taskId}/marked_problems`, {
        analysis_type: 'chain',
        problem_key: problemKey,
        problem_data: problem
      });
      markedProblems.value.add(problemKey);
      ElMessage.success('标记成功');
    }
    markedProblems.value = new Set(markedProblems.value);
  } catch (error) {
    console.error('标记操作失败:', error);
    ElMessage.error('标记操作失败: ' + (error.response?.data?.detail || error.message));
  }
}

// 导出已标记的问题
async function exportMarkedProblems() {
  if (markedProblems.value.size === 0) {
    ElMessage.warning('没有已标记的问题');
    return;
  }
  
  try {
    // 从后端获取所有已标记的问题
    const response = await axios.get(`/api/codeReview/regressionTest/${props.taskId}/marked_problems`, {
      params: { analysis_type: 'chain' }
    });
    
    const markedProblemsArray = response.data.data.map(item => item.problem_data);
    
    if (markedProblemsArray.length === 0) {
      ElMessage.warning('未找到已标记问题的详情');
      return;
    }
    
    // 调用后端API生成Excel
    const exportResponse = await axios.post(
      `/api/codeReview/regressionTest/export_marked_problems/${props.taskId}`,
      {
        analysis_type: 'chain',
        problems: markedProblemsArray
      },
      { responseType: 'blob' }
    );
    
    // 创建下载链接
    const blob = new Blob([exportResponse.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `marked_problems_chain_${props.taskId}_${new Date().getTime()}.xlsx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    
    ElMessage.success('已标记问题导出成功');
  } catch (error) {
    console.error('导出失败:', error);
    ElMessage.error('导出失败: ' + (error.response?.data?.detail || error.message));
  }
}

defineExpose({
  exportMarkedProblems,
  toggleProblemMark,
  markedProblems,
  loadMarkedProblems
});
