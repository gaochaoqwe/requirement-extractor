<template>
  <div class="test-tools-container">
    <div class="tools-categories" v-if="!loading">
      <!-- 自测评/鉴定/三方表单工具 -->
      <div class="category-section">
        <div class="category-label">
          <div class="category-title">自测评/鉴定/三方表单工具</div>
        </div>
        <div class="category-tools">
          <div 
            v-for="tool in getToolsByCategory('form')" 
            :key="tool.id"
            class="tool-card"
            @click="navigateToTool(tool)"
            :class="{ disabled: tool.status !== 'active' }"
          >
            <div class="card-image">
              <div class="default-icon">📋</div>
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

      <!-- 分隔线 -->
      <div class="category-divider"></div>

      <!-- 鉴定/三方测评大纲工具 -->
      <div class="category-section">
        <div class="category-label">
          <div class="category-title">鉴定/三方测评大纲工具</div>
        </div>
        <div class="category-tools">
          <div 
            v-for="tool in getToolsByCategory('assessment')" 
            :key="tool.id"
            class="tool-card"
            @click="navigateToTool(tool)"
            :class="{ disabled: tool.status !== 'active' }"
          >
            <div class="card-image">
              <div class="default-icon">📋</div>
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
    
    <div class="loading-container" v-if="loading">
      <div class="loading-spinner"></div>
      <p>加载测试工具中...</p>
    </div>
    
    <div class="empty-state" v-if="!loading && tools.length === 0">
      <div class="empty-icon">🔧</div>
      <h3>暂无可用工具</h3>
      <p>测试工具正在开发中，敬请期待</p>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import testToolsService from '@/services/testToolsService'

export default {
  name: 'TestToolsIndex',
  setup() {
    const router = useRouter()
    const loading = ref(true)
    const tools = ref([])
    
    // 工具分类映射
    const toolCategories = {
      'test_case_assistant': 'form',
      'assessment_form_helper': 'assessment',
      'outline_rewriter': 'assessment'
    }
    
    // 🚀 优化4: 默认工具列表，避免API失败时页面空白
    const getDefaultTools = () => {
      return [
        {
          id: "test_case_assistant",
          name: "测试用例辅助设计（Excel）",
          description: "在线编辑表格，支持导入/导出 .xlsx",
          route: "/test-tools/test-case-assistant",
          status: "active"
        },
        {
          id: "assessment_form_helper",
          name: "充分性要求、通过准则列生成工具",
          description: "根据表单中已有的内容，自动生成充分性要求列和通过准则列",
          route: "/test-tools/assessment-form-helper",
          status: "active"
        },
        {
          id: "outline_rewriter",
          name: "鉴定测评大纲二次编写工具",
          description: "上传大纲docx，勾选章节，AI自动生成正文内容并输出新文档",
          route: "/test-tools/outline-rewriter",
          status: "active"
        }
      ]
    }
    
    const loadTools = async () => {
      try {
        loading.value = true

        const mergeTools = (remoteTools) => {
          const defaults = getDefaultTools()
          const map = new Map()
          defaults.forEach(t => map.set(t.id, t))
          ;(remoteTools || []).forEach(t => {
            if (t && t.id) {
              map.set(t.id, { ...map.get(t.id), ...t })
            }
          })
          return Array.from(map.values())
        }
        
        // 🚀 优化1: 检查本地缓存
        const cacheKey = 'testTools_list_v2'
        const cacheTime = 5 * 60 * 1000 // 5分钟缓存
        const cached = localStorage.getItem(cacheKey)
        const cacheTimestamp = localStorage.getItem(cacheKey + '_timestamp')
        
        if (cached && cacheTimestamp) {
          const isValid = Date.now() - parseInt(cacheTimestamp) < cacheTime
          if (isValid) {
            try {
              tools.value = mergeTools(JSON.parse(cached))
              console.log('✅ 使用缓存的工具列表:', tools.value.length, '个工具')
              loading.value = false
              return
            } catch (e) {
              console.warn('缓存数据解析失败，将重新请求')
            }
          }
        }
        
        // 🚀 优化2: 简化API请求，只重试一次
        try {
          const response = await testToolsService.getToolsList()
          
          if (response && response.success) {
            tools.value = mergeTools(response.tools)
            // 缓存结果
            localStorage.setItem(cacheKey, JSON.stringify(response.tools))
            localStorage.setItem(cacheKey + '_timestamp', Date.now().toString())
            console.log('✅ 工具列表加载成功:', tools.value.length, '个工具')
          } else {
            throw new Error('API响应格式错误')
          }
        } catch (error) {
          console.warn('⚠️ API请求失败，使用默认工具列表:', error.message)
          // 🚀 优化3: 使用本地默认数据作为fallback
          tools.value = getDefaultTools()
        }
      } catch (error) {
        console.error('❌ 加载工具列表失败:', error)
        tools.value = getDefaultTools()
      } finally {
        loading.value = false
      }
    }
    
    const getToolsByCategory = (category) => {
      return tools.value.filter(tool => toolCategories[tool.id] === category)
    }
    
    const navigateToTool = (tool) => {
      if (tool.status !== 'active') {
        return
      }
      
      // 根据工具ID导航到对应的页面
      if (tool.id === 'assessment_form_helper') {
        router.push('/test-tools/assessment-form-helper')
      } else if (tool.id === 'test_case_assistant') {
        router.push('/test-tools/test-case-assistant')
      } else if (tool.id === 'outline_rewriter') {
        router.push('/test-tools/outline-rewriter')
      }
    }
    
    // 移除图片相关的方法，直接使用默认图标
    
    const getStatusText = (status) => {
      const statusMap = {
        'developing': '开发中',
        'maintenance': '维护中',
        'deprecated': '已弃用'
      }
      return statusMap[status] || status
    }
    
    onMounted(() => {
      loadTools()
    })
    
    return {
      loading,
      tools,
      getToolsByCategory,
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
  color: #1f2937;
  margin-bottom: 8px;
  line-height: 1.3;
  text-align: center;
  background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%);
  color: white;
  padding: 12px 16px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(139, 92, 246, 0.3);
}

.category-description {
  font-size: 0.95rem;
  color: #6b7280;
  line-height: 1.4;
}

.category-tools {
  flex: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  align-items: flex-start;
}

.category-divider {
  height: 2px;
  background: linear-gradient(90deg, #8b5cf6 0%, #a855f7 50%, #8b5cf6 100%);
  margin: 0;
  border-radius: 1px;
  box-shadow: 0 1px 3px rgba(139, 92, 246, 0.3);
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

.card-image img {
  max-width: 70%;
  max-height: 70%;
  object-fit: contain;
  filter: brightness(1.1);
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

.loading-container {
  text-align: center;
  padding: 60px 20px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e5e7eb;
  border-top: 4px solid #8b5cf6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 16px;
}

.empty-state h3 {
  font-size: 1.5rem;
  color: #1f2937;
  margin-bottom: 8px;
}

.empty-state p {
  color: #6b7280;
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
  
  .category-divider {
    margin: 20px 0;
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
  
  .category-description {
    font-size: 0.9rem;
  }
}
</style> 