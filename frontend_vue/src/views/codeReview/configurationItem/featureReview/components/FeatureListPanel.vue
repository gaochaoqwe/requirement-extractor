<template>
  <div class="feature-list-panel">
    <div class="panel-header">
      <h3>功能列表</h3>
      <el-button :icon="Plus" size="small" type="primary" @click="$emit('feature-add')">
        添加功能
      </el-button>
    </div>

    <div class="panel-content">
      <div v-if="features.length === 0" class="empty-state">
        <el-empty description="暂无功能，点击上方按钮添加" />
      </div>

      <div v-else class="features-list">
        <div
          v-for="feature in features"
          :key="feature.id"
          class="feature-item"
          :class="{ 'active': feature.id === selectedFeatureId }"
          @click="$emit('feature-select', feature)"
        >
          <div class="feature-header">
            <div class="feature-name">
              <el-icon><Document /></el-icon>
              <span>{{ feature.name }}</span>
            </div>
            <el-tag
              :type="getStatusTagType(feature.status)"
              size="small"
            >
              {{ getStatusText(feature.status) }}
            </el-tag>
          </div>

          <div class="feature-actions">
            <el-button-group size="small">
              <el-tooltip content="查看详情">
                <el-button :icon="View" @click.stop="toggleDetails(feature.id)" />
              </el-tooltip>
              <el-tooltip content="AI审查">
                <el-button
                  :icon="MagicStick"
                  type="primary"
                  :loading="feature.status === 'reviewing'"
                  :disabled="feature.status === 'reviewing'"
                  @click.stop="$emit('feature-review', feature)"
                />
              </el-tooltip>
              <el-tooltip content="编辑">
                <el-button :icon="Edit" @click.stop="$emit('feature-edit', feature)" />
              </el-tooltip>
              <el-tooltip content="删除">
                <el-button
                  :icon="Delete"
                  type="danger"
                  @click.stop="confirmDelete(feature)"
                />
              </el-tooltip>
            </el-button-group>
          </div>

          <!-- 功能详情（可展开） -->
          <el-collapse-transition>
            <div v-show="expandedFeatureId === feature.id" class="feature-details">
              <div class="detail-section">
                <div class="detail-label">功能描述</div>
                <div class="detail-value">{{ feature.description || '暂无描述' }}</div>
              </div>
              
              <div class="detail-section">
                <div class="detail-label">入口函数</div>
                <div class="detail-value">{{ feature.entry_function || feature.entryFunction || 'main' }}</div>
              </div>

              <div v-if="feature.related_files && feature.related_files.length > 0" class="detail-section">
                <div class="detail-label">相关文件 ({{ feature.related_files.length }})</div>
                <div class="detail-value">
                  <el-tag
                    v-for="(file, index) in feature.related_files.slice(0, 5)"
                    :key="index"
                    size="small"
                    style="margin: 2px;"
                  >
                    {{ file }}
                  </el-tag>
                  <span v-if="feature.related_files.length > 5" class="more-text">
                    +{{ feature.related_files.length - 5 }} 更多
                  </span>
                </div>
              </div>

              <div v-if="feature.related_functions && feature.related_functions.length > 0" class="detail-section">
                <div class="detail-label">相关函数 ({{ feature.related_functions.length }})</div>
                <div class="detail-value">
                  <el-tag
                    v-for="(func, index) in feature.related_functions.slice(0, 5)"
                    :key="index"
                    size="small"
                    type="success"
                    style="margin: 2px;"
                  >
                    {{ func }}
                  </el-tag>
                  <span v-if="feature.related_functions.length > 5" class="more-text">
                    +{{ feature.related_functions.length - 5 }} 更多
                  </span>
                </div>
              </div>
            </div>
          </el-collapse-transition>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { Plus, Document, View, MagicStick, Edit, Delete } from '@element-plus/icons-vue';
import { ElMessageBox, ElCollapseTransition } from 'element-plus';

defineProps({
  features: {
    type: Array,
    default: () => []
  },
  selectedFeatureId: {
    type: Number,
    default: null
  }
});

const emit = defineEmits([
  'feature-select',
  'feature-add',
  'feature-review',
  'feature-edit',
  'feature-delete'
]);

const expandedFeatureId = ref(null);

function toggleDetails(featureId) {
  expandedFeatureId.value = expandedFeatureId.value === featureId ? null : featureId;
}

function getStatusText(status) {
  const statusMap = {
    'pending': '待审查',
    'reviewing': '审查中',
    'completed': '已完成',
    'failed': '失败'
  };
  return statusMap[status] || '未知';
}

function getStatusTagType(status) {
  const typeMap = {
    'pending': 'info',
    'reviewing': 'warning',
    'completed': 'success',
    'failed': 'danger'
  };
  return typeMap[status] || 'info';
}

function confirmDelete(feature) {
  ElMessageBox.confirm(
    `确定要删除功能"${feature.name}"吗？此操作不可恢复。`,
    '确认删除',
    {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(() => {
    emit('feature-delete', feature);
  }).catch(() => {
    // 取消删除
  });
}
</script>

<style scoped>
.feature-list-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.panel-header {
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.empty-state {
  padding: 40px 20px;
}

.features-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.feature-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: white;
}

.feature-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.15);
}

.feature-item.active {
  border-color: #409eff;
  background: #ecf5ff;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.2);
}

.feature-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.feature-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #303133;
  font-size: 14px;
}

.feature-name .el-icon {
  color: #409eff;
}

.feature-actions {
  margin-top: 8px;
}

.feature-details {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #e4e7ed;
}

.detail-section {
  margin-bottom: 12px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.detail-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 6px;
  font-weight: 500;
}

.detail-value {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  word-break: break-word;
}

.more-text {
  font-size: 12px;
  color: #909399;
  margin-left: 4px;
}
</style>

