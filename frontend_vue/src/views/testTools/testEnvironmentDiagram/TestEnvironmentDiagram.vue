<template>
  <div class="test-environment-container">
    <div class="main-container">
      <div class="header">
        <h2>测试环境图和说明生成工具</h2>
        <p>输入设备信息，自动生成测试环境图和环境说明</p>
      </div>

      <!-- 输入表单 -->
      <div class="input-section" v-if="currentStep === 'input'">
        <!-- 模式选择 -->
        <div class="mode-selection">
          <el-radio-group v-model="softwareMode" @change="onModeChange">
            <el-radio-button label="main_control">主控软件</el-radio-button>
            <el-radio-button label="subsystem">分系统软件</el-radio-button>
          </el-radio-group>
        </div>

        <el-form :model="deviceInfo" label-width="140px" class="device-form">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="软件名称" required>
                <el-input v-model="deviceInfo.软件名称" placeholder="请输入软件名称" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="检测仪名称" required>
                <el-input v-model="deviceInfo.检测仪名称" placeholder="请输入检测仪名称" />
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="软件运行设备" required>
                <el-input v-model="deviceInfo.软件运行设备" placeholder="请输入软件运行设备名称" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="目标模拟器">
                <el-input v-model="deviceInfo.目标模拟器" placeholder="请输入目标模拟器名称（可选）" />
              </el-form-item>
            </el-col>
          </el-row>

          <!-- 分系统软件模式下的额外字段 -->
          <div v-if="softwareMode === 'subsystem'">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="主控软件名称" required>
                  <el-input v-model="deviceInfo.主控软件名称" placeholder="请输入主控软件名称" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="主控与被测软件接口类型" required>
                  <el-input v-model="deviceInfo.主控与被测软件接口类型" placeholder="请输入主控软件与被测软件接口类型" />
                </el-form-item>
              </el-col>
            </el-row>
          </div>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="检测仪与软件接口类型" required>
                <el-input v-model="deviceInfo.接口1" placeholder="请输入检测仪与软件接口类型（如：RS422接口）" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="软件与调试计算机接口类型" required>
                <el-input v-model="deviceInfo.接口2" placeholder="请输入软件与调试计算机接口类型（如：以太网）" />
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-form-item>
            <el-button type="primary" @click="generateDiagram" :loading="loading" size="large">
              生成测试环境图
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 生成进度 -->
      <div class="progress-section" v-if="currentStep === 'processing'">
        <div class="progress-content">
          <el-progress :percentage="100" :show-text="false" />
          <p>正在生成测试环境图...</p>
        </div>
      </div>

      <!-- 结果展示 -->
      <div class="result-section" v-if="currentStep === 'result'">
        <div class="diagram-container">
          <h3>测试环境图</h3>
          <div class="diagram-canvas" ref="diagramCanvas">
            <!-- 这里将使用Canvas或SVG绘制图表 -->
          </div>
        </div>
        
        <div class="description-container">
          <h3>测试环境说明</h3>
          <div class="description-content">
            <p>{{ environmentDescription }}</p>
          </div>
        </div>
        
        <div class="action-buttons">
          <el-button @click="resetForm">重新生成</el-button>
          <el-button type="primary" @click="exportDiagram">导出图表</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted, nextTick } from 'vue'
import testEnvironmentService from '@/services/testEnvironmentService'

export default {
  name: 'TestEnvironmentDiagram',
  setup() {
    const currentStep = ref('input') // input, processing, result
    const loading = ref(false)
    const sessionId = ref('')
    const diagramCanvas = ref(null)
    const environmentDescription = ref('')
    const diagramData = ref(null)
    
    const deviceInfo = reactive({
      软件名称: '',
      检测仪名称: '',
      软件运行设备: '',
      接口1: '',
      接口2: '',
      目标模拟器: '',
      主控软件名称: '',
      主控与被测软件接口类型: ''
    })

    const softwareMode = ref('main_control') // 'main_control' or 'subsystem'

    const onModeChange = () => {
      // 切换模式时，清空主控软件相关的字段
      if (softwareMode.value === 'subsystem') {
        deviceInfo.主控软件名称 = ''
        deviceInfo.主控与被测软件接口类型 = ''
      }
    }
    
    const generateDiagram = async () => {
      try {
        loading.value = true
        currentStep.value = 'processing'
        
        console.log('提交设备信息:', deviceInfo)
        
        // 创建测试环境图
        const response = await testEnvironmentService.createEnvironmentDiagram(deviceInfo)
        
        if (response.success) {
          sessionId.value = response.session_id
          console.log('获得会话ID:', sessionId.value)
          
          // 轮询状态直到完成
          await pollStatus()
        } else {
          throw new Error(response.message || '创建失败')
        }
        
      } catch (error) {
        console.error('生成测试环境图失败:', error)
        ElMessage.error(`生成失败: ${error.message}`)
        currentStep.value = 'input'
      } finally {
        loading.value = false
      }
    }
    
    const pollStatus = async () => {
      try {
        const maxAttempts = 30
        let attempts = 0
        
        const checkStatus = async () => {
          attempts++
          console.log(`检查状态 (${attempts}/${maxAttempts}):`, sessionId.value)
          
          const statusResponse = await testEnvironmentService.getSessionStatus(sessionId.value)
          
          if (statusResponse.success) {
            const status = statusResponse.data.status
            console.log('当前状态:', status)
            
            if (status === 'completed') {
              // 获取结果
              await loadResult()
            } else if (status === 'error') {
              throw new Error(statusResponse.data.message || '生成失败')
            } else if (attempts < maxAttempts) {
              // 继续轮询
              setTimeout(checkStatus, 1000)
            } else {
              throw new Error('生成超时')
            }
          } else {
            throw new Error('获取状态失败')
          }
        }
        
        checkStatus()
        
      } catch (error) {
        console.error('轮询状态失败:', error)
        throw error
      }
    }
    
    const loadResult = async () => {
      try {
        console.log('加载结果:', sessionId.value)
        
        const resultResponse = await testEnvironmentService.getDiagramResult(sessionId.value)
        
        if (resultResponse.success) {
          diagramData.value = resultResponse.data.diagram_data
          environmentDescription.value = resultResponse.data.description
          
          console.log('图表数据:', diagramData.value)
          console.log('环境描述:', environmentDescription.value)
          
          currentStep.value = 'result'
          
          // 等待DOM更新后绘制图表
          await nextTick()
          drawDiagram()
          
        } else {
          throw new Error('获取结果失败')
        }
        
      } catch (error) {
        console.error('加载结果失败:', error)
        throw error
      }
    }
    
    const drawDiagram = () => {
      if (!diagramCanvas.value || !diagramData.value) {
        console.error('Canvas元素或图表数据不存在')
        return
      }
      
      try {
        const canvas = document.createElement('canvas')
        canvas.width = 700
        canvas.height = 400
        canvas.style.border = '1px solid #ddd'
        canvas.style.borderRadius = '8px'
        
        // 清空容器并添加canvas
        diagramCanvas.value.innerHTML = ''
        diagramCanvas.value.appendChild(canvas)
        
        const ctx = canvas.getContext('2d')
        
        // 设置字体
        ctx.font = '14px Arial, SimSun'
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        
        // 绘制背景
        ctx.fillStyle = '#FFFFFF'
        ctx.fillRect(0, 0, canvas.width, canvas.height)
        
        // 绘制网格（可选）
        if (diagramData.value.layout.grid && diagramData.value.layout.grid.enabled) {
          drawGrid(ctx, canvas.width, canvas.height, diagramData.value.layout.grid)
        }
        
        // 绘制连接线
        drawConnections(ctx, diagramData.value.connections, diagramData.value.nodes)
        
        // 绘制节点
        drawNodes(ctx, diagramData.value.nodes)
        
        console.log('图表绘制完成')
        
      } catch (error) {
        console.error('绘制图表失败:', error)
      }
    }
    
    const drawGrid = (ctx, width, height, gridConfig) => {
      ctx.strokeStyle = gridConfig.color
      ctx.lineWidth = 0.5
      
      const size = gridConfig.size
      
      // 绘制垂直线
      for (let x = 0; x <= width; x += size) {
        ctx.beginPath()
        ctx.moveTo(x, 0)
        ctx.lineTo(x, height)
        ctx.stroke()
      }
      
      // 绘制水平线
      for (let y = 0; y <= height; y += size) {
        ctx.beginPath()
        ctx.moveTo(0, y)
        ctx.lineTo(width, y)
        ctx.stroke()
      }
    }
    
    const drawNodes = (ctx, nodes) => {
      nodes.forEach(node => {
        const { x, y } = node.position
        const { width, height, backgroundColor, borderColor, textColor, borderWidth = 2 } = node.style
        
        // 绘制节点背景
        ctx.fillStyle = backgroundColor
        ctx.fillRect(x - width/2, y - height/2, width, height)
        
        // 绘制边框
        ctx.strokeStyle = borderColor
        ctx.lineWidth = borderWidth
        ctx.strokeRect(x - width/2, y - height/2, width, height)
        
        // 绘制文本
        ctx.fillStyle = textColor
        
        // 对于容器类型，文本显示在顶部
        if (node.type === 'container') {
          ctx.fillText(node.label, x, y - height/2 + 15)
        } else {
          ctx.fillText(node.label, x, y)
        }
      })
    }
    
    const drawConnections = (ctx, connections, nodes) => {
      // 创建节点位置映射
      const nodePositions = {}
      nodes.forEach(node => {
        nodePositions[node.id] = node.position
      })
      
      connections.forEach(conn => {
        const fromPos = nodePositions[conn.from]
        const toPos = nodePositions[conn.to]
        
        if (!fromPos || !toPos) return
        
        ctx.strokeStyle = conn.style.strokeColor
        ctx.lineWidth = conn.style.strokeWidth
        
        // 设置虚线样式
        if (conn.style.strokeDasharray !== 'none') {
          const dashArray = conn.style.strokeDasharray.split(',').map(Number)
          ctx.setLineDash(dashArray)
        } else {
          ctx.setLineDash([])
        }
        
        // 绘制连接线
        ctx.beginPath()
        ctx.moveTo(fromPos.x, fromPos.y)
        ctx.lineTo(toPos.x, toPos.y)
        ctx.stroke()
        
        // 绘制箭头（如果是单向连接）
        if (conn.type === 'unidirectional') {
          drawArrow(ctx, fromPos, toPos, conn.style.strokeColor)
        }
        
        // 绘制标签
        if (conn.label) {
          const midX = (fromPos.x + toPos.x) / 2
          const midY = (fromPos.y + toPos.y) / 2 - 10
          
          ctx.fillStyle = '#000000'
          ctx.fillText(conn.label, midX, midY)
        }
      })
      
      // 重置虚线
      ctx.setLineDash([])
    }
    
    const drawArrow = (ctx, from, to, color) => {
      const angle = Math.atan2(to.y - from.y, to.x - from.x)
      const arrowLength = 10
      const arrowAngle = Math.PI / 6
      
      ctx.fillStyle = color
      ctx.beginPath()
      ctx.moveTo(to.x, to.y)
      ctx.lineTo(
        to.x - arrowLength * Math.cos(angle - arrowAngle),
        to.y - arrowLength * Math.sin(angle - arrowAngle)
      )
      ctx.lineTo(
        to.x - arrowLength * Math.cos(angle + arrowAngle),
        to.y - arrowLength * Math.sin(angle + arrowAngle)
      )
      ctx.closePath()
      ctx.fill()
    }
    
    const resetForm = () => {
      currentStep.value = 'input'
      sessionId.value = ''
      environmentDescription.value = ''
      diagramData.value = null
      
      // 重置表单
      Object.keys(deviceInfo).forEach(key => {
        deviceInfo[key] = ''
      })
      softwareMode.value = 'main_control' // 重置模式
    }
    
    const exportDiagram = () => {
      try {
        const canvas = diagramCanvas.value.querySelector('canvas')
        if (canvas) {
          // 导出为图片
          const link = document.createElement('a')
          link.download = '测试环境图.png'
          link.href = canvas.toDataURL()
          link.click()
          
          ElMessage.success('图表导出成功')
        } else {
          ElMessage.error('未找到图表')
        }
      } catch (error) {
        console.error('导出失败:', error)
        ElMessage.error('导出失败')
      }
    }
    
    return {
      currentStep,
      loading,
      deviceInfo,
      diagramCanvas,
      environmentDescription,
      generateDiagram,
      resetForm,
      exportDiagram,
      softwareMode,
      onModeChange
    }
  }
}
</script>

<style scoped>
.test-environment-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
  display: flex;
  justify-content: center;
  align-items: flex-start;
}

.main-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  padding: 30px;
  width: 100%;
  max-width: 900px;
}

.header {
  text-align: center;
  margin-bottom: 30px;
}

.header h2 {
  color: #2c3e50;
  margin-bottom: 10px;
  font-size: 28px;
}

.header p {
  color: #7f8c8d;
  font-size: 16px;
}

.mode-selection {
  text-align: center;
  margin-bottom: 30px;
}

.mode-selection .el-radio-group {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 8px;
}

.device-form {
  max-width: 800px;
  margin: 0 auto;
}

.mode-selection {
  margin-bottom: 20px;
  text-align: center;
}

.progress-section {
  text-align: center;
  padding: 40px 0;
}

.progress-content p {
  margin-top: 20px;
  color: #666;
  font-size: 16px;
}

.result-section {
  margin-top: 20px;
}

.diagram-container {
  margin-bottom: 30px;
}

.diagram-container h3 {
  color: #2c3e50;
  margin-bottom: 15px;
  font-size: 20px;
}

.diagram-canvas {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.description-container {
  margin-bottom: 30px;
}

.description-container h3 {
  color: #2c3e50;
  margin-bottom: 15px;
  font-size: 20px;
}

.description-content {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  border-left: 4px solid #667eea;
}

.description-content p {
  line-height: 1.8;
  color: #2c3e50;
  margin: 0;
  text-align: justify;
}

.action-buttons {
  text-align: center;
}

.action-buttons .el-button {
  margin: 0 10px;
}

/* Element Plus 样式覆盖 */
:deep(.el-form-item__label) {
  font-weight: 600;
  color: #2c3e50;
}

:deep(.el-input__wrapper) {
  border-radius: 8px;
}

:deep(.el-button) {
  border-radius: 8px;
  padding: 12px 24px;
  font-weight: 600;
}

:deep(.el-progress-bar__outer) {
  border-radius: 10px;
  background-color: #f0f0f0;
}

:deep(.el-progress-bar__inner) {
  border-radius: 10px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
}
</style> 