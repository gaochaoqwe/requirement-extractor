<template>
  <div class="test-tools-container">
    <div class="tools-categories">
      <div class="category-section">
        <div class="category-label">
          <div class="category-title">测试报告工具</div>
        </div>
        <div class="category-tools">
          <div
            v-for="tool in tools"
            :key="tool.id"
            class="tool-card"
            @click="navigateToTool(tool)"
            :class="{ disabled: tool.status !== 'active' }"
          >
            <div class="card-image">
              <div class="default-icon">📊</div>
            </div>
            <div class="card-content">
              <h3>{{ tool.name }}</h3>
              <p>{{ tool.description }}</p>
              <div class="card-status" v-if="tool.status !== 'active'">
                <span class="status-badge">{{ getStatusText(tool.status) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

export default {
  name: 'TestReportIndex',
  setup() {
    const router = useRouter()

    // 测试报告工具列表（入口卡片，页面路由保持 /test-tools/... 不变）
    const tools = ref([
      {
        id: 'test_environment_diagram',
        name: '测试环境图和说明生成工具',
        description: '输入设备信息，自动生成测试环境图和环境说明',
        route: '/test-tools/test-environment-diagram',
        status: 'active'
      },
      {
        id: 'test_case_summary',
        name: '功能性能指标符合性表生成工具',
        description: '上传测试用例表，AI自动生成功能性能指标符合性分析表',
        route: '/test-tools/test-case-summary',
        status: 'active'
      }
    ])

    const navigateToTool = (tool) => {
      if (tool.status !== 'active') {
        return
      }
      router.push(tool.route)
    }

    const getStatusText = (status) => {
      const statusMap = {
        'developing': '开发中',
        'maintenance': '维护中',
        'deprecated': '已弃用'
      }
      return statusMap[status] || status
    }

    return {
      tools,
      navigateToTool,
      getStatusText
    }
  }
}
</script>

<style scoped>
.test-tools-container {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.tools-categories {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.category-section {
  display: flex;
  align-items: flex-start;
  min-height: 280px;
  padding: 32px 0;
}

.category-label {
  flex: 0 0 280px;
  padding-right: 40px;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  padding-top: 20px;
}

.category-title {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 8px;
  line-height: 1.3;
  text-align: center;
  background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%);
  color: white;
  padding: 12px 16px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(139, 92, 246, 0.3);
}

.category-tools {
  flex: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  align-items: flex-start;
}

.tool-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  cursor: pointer;
  overflow: hidden;
  border: 1px solid #e5e7eb;
  width: 300px;
  flex-shrink: 0;
}

.tool-card:hover:not(.disabled) {
  transform: translateY(-4px);
  box-shadow: 0 10px 25px -3px rgba(0, 0, 0, 0.1);
  border-color: #8b5cf6;
}

.tool-card.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.card-image {
  height: 160px;
  background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.default-icon {
  font-size: 3rem;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  color: white;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

.card-content {
  padding: 20px;
  position: relative;
}

.card-content h3 {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 8px;
  line-height: 1.3;
}

.card-content p {
  color: #6b7280;
  line-height: 1.5;
  margin-bottom: 12px;
  font-size: 0.9rem;
}

.card-status {
  margin-top: 12px;
}

.status-badge {
  display: inline-block;
  padding: 4px 8px;
  background: #fef3c7;
  color: #92400e;
  border-radius: 4px;
  font-size: 0.875rem;
  font-weight: 500;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .category-section {
    flex-direction: column;
    align-items: stretch;
  }

  .category-label {
    flex: none;
    padding-right: 0;
    padding-bottom: 20px;
    text-align: center;
  }

  .category-tools {
    justify-content: center;
  }
}

@media (max-width: 768px) {
  .test-tools-container {
    padding: 16px;
  }

  .category-section {
    padding: 24px 0;
    min-height: auto;
  }

  .category-title {
    font-size: 1.3rem;
  }

  .tool-card {
    width: 100%;
    max-width: 350px;
  }

  .category-tools {
    gap: 16px;
  }
}

@media (max-width: 480px) {
  .category-label {
    padding-right: 0;
  }

  .category-title {
    font-size: 1.2rem;
  }
}
</style>
