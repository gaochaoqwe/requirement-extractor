<template>
  <div class="progressive-discovery-panel">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon :size="20"><TrendCharts /></el-icon>
            <span class="title">渐进式功能发现</span>
          </div>
          <el-tag v-if="discoveryData.statistics" :type="statusTagType" effect="dark">
            {{ statusText }}
          </el-tag>
        </div>
      </template>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="5" animated />
      </div>

      <!-- 无数据提示 -->
      <div v-else-if="!discoveryData.tree" class="no-data">
        <el-empty description="该任务未使用渐进式发现">
          <el-alert
            title="提示"
            type="info"
            :closable="false"
            show-icon
          >
            <template #default>
              <p>当前任务使用传统的一次性功能发现模式</p>
              <p>要启用渐进式发现，请设置环境变量：<code>ENABLE_PROGRESSIVE_DISCOVERY=true</code></p>
            </template>
          </el-alert>
        </el-empty>
      </div>

      <!-- 主要内容 -->
      <div v-else class="content">
        <!-- 统计信息 -->
        <el-row :gutter="20" class="statistics">
          <el-col :span="8">
            <div class="stat-card">
              <div class="stat-value">{{ discoveryData.statistics.total_features }}</div>
              <div class="stat-label">发现功能数</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="stat-card">
              <div class="stat-value">{{ discoveryData.statistics.total_rounds }}</div>
              <div class="stat-label">分析轮次</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="stat-card">
              <div class="stat-value">{{ totalIssuesCount }}</div>
              <div class="stat-label">发现问题</div>
            </div>
          </el-col>
        </el-row>

        <el-divider />

        <!-- 功能树 -->
        <div class="tree-container">
          <div class="tree-header">
            <h3>功能层次结构</h3>
            <el-button-group>
              <el-button size="small" @click="expandAll">全部展开</el-button>
              <el-button size="small" @click="collapseAll">全部折叠</el-button>
            </el-button-group>
          </div>

          <el-tree
            ref="treeRef"
            :data="treeData"
            :props="treeProps"
            node-key="id"
            default-expand-all
            highlight-current
            @node-click="handleNodeClick"
            class="feature-tree"
          >
            <template #default="{ node, data }">
              <div class="custom-tree-node">
                <div class="node-info">
                  <el-icon class="node-icon" :color="getNodeIconColor(data)">
                    <component :is="getNodeIcon(data)" />
                  </el-icon>
                  <span class="node-label">{{ node.label }}</span>
                </div>
                <div class="node-meta">
                  <el-tag
                    v-if="data.confidence"
                    size="small"
                    :type="getConfidenceType(data.confidence)"
                    effect="plain"
                  >
                    {{ confidenceLabel(data.confidence) }}
                  </el-tag>
                  <el-tag
                    v-if="data.issues_count > 0"
                    size="small"
                    type="danger"
                    effect="dark"
                  >
                    {{ data.issues_count }} 问题
                  </el-tag>
                  <el-tag
                    v-if="data.status === 'completed'"
                    size="small"
                    type="success"
                    effect="plain"
                  >
                    已审查
                  </el-tag>
                </div>
              </div>
            </template>
          </el-tree>
        </div>
      </div>
    </el-card>

    <!-- 轮次历史 -->
    <el-card shadow="hover" style="margin-top: 20px;" v-if="roundsHistory.length > 0">
      <template #header>
        <div class="card-header">
          <el-icon :size="20"><Clock /></el-icon>
          <span class="title">分析历史</span>
        </div>
      </template>

      <el-timeline>
        <el-timeline-item
          v-for="round in roundsHistory"
          :key="round.round"
          :timestamp="formatTime(round.timestamp)"
          :color="getRoundColor(round.round)"
          placement="top"
        >
          <el-card shadow="never">
            <div class="round-card">
              <div class="round-header">
                <h4>Round {{ round.round }}: {{ getRoundMethodLabel(round.method) }}</h4>
                <el-tag size="small">{{ round.method }}</el-tag>
              </div>
              <p class="round-summary">{{ round.summary }}</p>
              <div v-if="round.ai_decisions && round.ai_decisions.length > 0" class="ai-decisions">
                <el-collapse accordion>
                  <el-collapse-item title="AI决策详情" name="1">
                    <div v-for="(decision, idx) in round.ai_decisions" :key="idx" class="decision-item">
                      <p><strong>阶段：</strong>{{ decision.stage }}</p>
                      <p><strong>输入：</strong>{{ decision.input }}</p>
                      <p><strong>输出：</strong>{{ decision.output }}</p>
                    </div>
                  </el-collapse-item>
                </el-collapse>
              </div>
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>
    </el-card>

    <!-- 功能详情抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      :title="selectedFeature?.name || '功能详情'"
      size="50%"
      direction="rtl"
    >
      <div v-if="selectedFeature" class="feature-detail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="功能ID">
            <el-tag>{{ selectedFeature.id }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="功能名称">
            {{ selectedFeature.name }}
          </el-descriptions-item>
          <el-descriptions-item label="描述">
            {{ selectedFeature.description || '无' }}
          </el-descriptions-item>
          <el-descriptions-item label="置信度">
            <el-tag :type="getConfidenceType(selectedFeature.confidence)">
              {{ confidenceLabel(selectedFeature.confidence) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="审查状态">
            <el-tag :type="selectedFeature.status === 'completed' ? 'success' : 'info'">
              {{ selectedFeature.status === 'completed' ? '已完成' : '待审查' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="发现问题数">
            <el-tag :type="selectedFeature.issues_count > 0 ? 'danger' : 'success'">
              {{ selectedFeature.issues_count }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <el-divider />

        <div v-if="selectedFeature.related_files && selectedFeature.related_files.length > 0">
          <h4>相关文件</h4>
          <el-tag
            v-for="file in selectedFeature.related_files"
            :key="file"
            style="margin: 4px;"
            effect="plain"
          >
            <el-icon><Document /></el-icon>
            {{ file }}
          </el-tag>
        </div>

        <div v-if="selectedFeature.key_functions && selectedFeature.key_functions.length > 0" style="margin-top: 16px;">
          <h4>关键函数</h4>
          <el-tag
            v-for="func in selectedFeature.key_functions"
            :key="func"
            style="margin: 4px;"
            type="success"
            effect="plain"
          >
            <el-icon><Operation /></el-icon>
            {{ func }}
          </el-tag>
        </div>

        <div v-if="selectedFeature.evidence" style="margin-top: 16px;">
          <h4>证据/理由</h4>
          <el-alert :closable="false" type="info">
            {{ selectedFeature.evidence }}
          </el-alert>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { ElMessage } from 'element-plus';
import {
  TrendCharts,
  Clock,
  Document,
  Operation,
  Folder,
  Files
} from '@element-plus/icons-vue';
import axios from 'axios';

const props = defineProps({
  taskId: {
    type: [Number, String],
    required: true
  }
});

// 数据
const loading = ref(false);
const discoveryData = ref({});
const roundsHistory = ref([]);
const selectedFeature = ref(null);
const drawerVisible = ref(false);
const treeRef = ref(null);

// 计算属性
const treeData = computed(() => {
  if (!discoveryData.value.tree) return [];
  return [discoveryData.value.tree];
});

const treeProps = {
  children: 'children',
  label: 'name'
};

const statusTagType = computed(() => {
  const status = discoveryData.value.statistics?.status;
  return status === 'completed' ? 'success' : 'warning';
});

const statusText = computed(() => {
  const status = discoveryData.value.statistics?.status;
  return status === 'completed' ? '发现完成' : '进行中';
});

const totalIssuesCount = computed(() => {
  return countIssues(discoveryData.value.tree);
});

// 方法
const loadData = async () => {
  loading.value = true;
  try {
    // 加载可视化数据
    const vizResponse = await axios.get(`/api/codeReview/regressionTest/progressive/visualization/${props.taskId}`);
    
    if (vizResponse.data.status === 'success') {
    discoveryData.value = vizResponse.data?.visualization || vizResponse.data;
    } else if (vizResponse.data.status === 'no_data') {
      console.log('该任务未使用渐进式发现');
    }

    // 加载轮次历史
    const roundsResponse = await axios.get(`/api/codeReview/regressionTest/progressive/rounds/${props.taskId}`);
    
    if (roundsResponse.data.status === 'success') {
      roundsHistory.value = roundsResponse.data.rounds;
    }

  } catch (error) {
    console.error('加载渐进式发现数据失败:', error);
    // 不显示错误消息，因为可能是任务未启用渐进式发现
  } finally {
    loading.value = false;
  }
};

const handleNodeClick = async (data) => {
  if (data.id) {
    try {
      const response = await axios.get(`/api/codeReview/regressionTest/progressive/feature/${props.taskId}/${data.id}`);
      
      if (response.data.status === 'success') {
        selectedFeature.value = response.data.feature;
        drawerVisible.value = true;
      }
    } catch (error) {
      ElMessage.error('加载功能详情失败');
      console.error(error);
    }
  }
};

const expandAll = () => {
  // 获取所有节点的key并展开
  const keys = [];
  const collectKeys = (node) => {
    if (node.id) keys.push(node.id);
    if (node.children) {
      node.children.forEach(collectKeys);
    }
  };
  if (discoveryData.value.tree) {
    collectKeys(discoveryData.value.tree);
  }
  
  // 使用nextTick确保DOM已更新
  setTimeout(() => {
    keys.forEach(key => {
      treeRef.value?.store.nodesMap[key]?.expand();
    });
  }, 0);
};

const collapseAll = () => {
  const keys = [];
  const collectKeys = (node) => {
    if (node.id) keys.push(node.id);
    if (node.children) {
      node.children.forEach(collectKeys);
    }
  };
  if (discoveryData.value.tree) {
    collectKeys(discoveryData.value.tree);
  }
  
  setTimeout(() => {
    keys.forEach(key => {
      treeRef.value?.store.nodesMap[key]?.collapse();
    });
  }, 0);
};

const getConfidenceType = (confidence) => {
  const map = {
    'high': 'success',
    'medium': 'warning',
    'low': 'info'
  };
  return map[confidence] || 'info';
};

const confidenceLabel = (confidence) => {
  const map = {
    'high': '高',
    'medium': '中',
    'low': '低'
  };
  return map[confidence] || confidence;
};

const getNodeIcon = (data) => {
  if (data.type === 'project') return Folder;
  if (data.children && data.children.length > 0) return Files;
  return Document;
};

const getNodeIconColor = (data) => {
  if (data.type === 'project') return '#409EFF';
  if (data.confidence === 'high') return '#67C23A';
  if (data.confidence === 'medium') return '#E6A23C';
  return '#909399';
};

const getRoundColor = (round) => {
  const colors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399'];
  return colors[(round - 1) % colors.length];
};

const getRoundMethodLabel = (method) => {
  const labels = {
    'directory_analysis': '目录结构分析',
    'function_signature_analysis': '函数签名分析',
    'main_function_verification': 'main函数验证',
    'completion': '完成'
  };
  return labels[method] || method;
};

const formatTime = (timestamp) => {
  if (!timestamp) return '';
  const date = new Date(timestamp);
  return date.toLocaleString('zh-CN');
};

const countIssues = (node) => {
  if (!node) return 0;
  let count = node.issues_count || 0;
  if (node.children) {
    node.children.forEach(child => {
      count += countIssues(child);
    });
  }
  return count;
};

// 生命周期
onMounted(() => {
  loadData();
});

// 监听taskId变化
watch(() => props.taskId, () => {
  loadData();
});
</script>

<style scoped>
.progressive-discovery-panel {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.loading-container {
  padding: 20px;
}

.no-data {
  padding: 40px 20px;
}

.no-data code {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  color: #e6a23c;
  font-family: monospace;
}

.content {
  padding: 10px 0;
}

.statistics {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  color: white;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
}

.tree-container {
  margin-top: 20px;
}

.tree-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.tree-header h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.feature-tree {
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 10px;
  background: #fafafa;
}

.custom-tree-node {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-right: 12px;
}

.node-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.node-icon {
  font-size: 16px;
}

.node-label {
  font-size: 14px;
  color: #303133;
}

.node-meta {
  display: flex;
  gap: 6px;
  align-items: center;
}

.round-card {
  padding: 4px;
}

.round-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.round-header h4 {
  margin: 0;
  font-size: 15px;
  color: #303133;
}

.round-summary {
  color: #606266;
  font-size: 14px;
  margin: 8px 0;
}

.ai-decisions {
  margin-top: 12px;
}

.decision-item {
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.decision-item:last-child {
  border-bottom: none;
}

.decision-item p {
  margin: 4px 0;
  font-size: 13px;
  color: #606266;
}

.feature-detail {
  padding: 10px;
}

.feature-detail h4 {
  margin: 16px 0 12px 0;
  font-size: 15px;
  color: #303133;
}
</style>

