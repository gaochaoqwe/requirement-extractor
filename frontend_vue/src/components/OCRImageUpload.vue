<template>
  <div class="ocr-upload-container">
    <div class="ocr-compact-card">
      <div class="compact-header">
        <div class="header-left">
          <el-icon class="header-icon"><Document /></el-icon>
          <span class="header-title">智能表单填写</span>
        </div>
        <div class="header-right">
          <el-tooltip content="粘贴OCR识别后的文本到下方区域" placement="top">
            <el-icon class="info-icon"><QuestionFilled /></el-icon>
          </el-tooltip>
        </div>
      </div>
      
      <div 
        class="compact-drop-zone"
        :class="{ 'processing': isProcessing }"
        @paste="handlePaste"
        tabindex="0"
        ref="dropZone"
      >
        <div v-if="!isProcessing && !hasResult" class="compact-drop-content">
          <img src="@/assets/icons8-paste-64.png" alt="粘贴" class="compact-upload-icon" />
          <span class="compact-text">请粘贴OCR识别结果到此处（<kbd>Ctrl+V</kbd>）</span>
        </div>
        
        <div v-else-if="isProcessing" class="compact-processing">
          <el-icon class="compact-processing-icon"><Loading /></el-icon>
          <span class="compact-processing-text">{{ processingMessage }}</span>
          <el-progress 
            :percentage="processingProgress" 
            :show-text="false"
            :stroke-width="3"
            color="#409eff"
            class="compact-progress"
          />
        </div>

        <div v-else-if="hasResult" class="compact-result">
          <el-icon class="compact-success-icon"><CircleCheck /></el-icon>
          <span class="compact-result-text">识别完成，数据已自动填入表单</span>
          <el-button 
            type="text" 
            size="small" 
            @click="clearResult"
            class="clear-button"
          >
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, Loading, CircleCheck, Close, QuestionFilled } from '@element-plus/icons-vue'

// Props
const props = defineProps({
  service: {
    type: Object,
    required: false
  }
})

// Emits
const emit = defineEmits(['dataExtracted'])

// 响应式数据
const isProcessing = ref(false)
const hasResult = ref(false)
const processingMessage = ref('')
const processingProgress = ref(0)
const dropZone = ref(null)

// 部门到领域的映射配置（与后端保持一致）
const departmentToDomain = {
  '图像部': '光电',
  '光电部': '光电', 
  '激光部': '光电',
  '光电系统一部': '光电',
  '光电系统二部': '光电',
  '光电系统三部': '光电',
  '光电系统四部': '光电',
  '光电系统一部/控制室': '光电',
  '光电系统二部/控制室': '光电',
  '光电系统三部/控制室': '光电',
  '光电系统四部/控制室': '光电',
  '瞄准显示部': '显示',
  '总体部': '火控',
  '重点实验室': '火控',
  '武控部': '外挂'
}

// 领域对应的测试人员配置（与后端保持一致）
const domainPersonnel = {
  '光电': {
    testManager: '李玲子',
    testPersonnel: '王凯旋(外协)'
  },
  '显示': {
    testManager: '赵寒冰', 
    testPersonnel: '李岩岩(外协)'
  },
  '火控': {
    testManager: '潘帅',
    testPersonnel: '王刚(外协)'
  },
  '外挂': {
    testManager: '武慧莹',
    testPersonnel: '王星(外协)'
  }
}

// 字段映射配置 - 支持多种可能的key名称（容错）
const fieldMappings = {
  // 基本信息字段
  'domain': ['所属领域', '领域', '产品领域'],
  'testManager': ['测试主管', '主管'],
  'testPersonnel': ['测试人员', '测试员', '测试工程师'],
  'developer': ['开发人员', '开发者', '开发工程师', '申请人'],
  'softwareName': ['软件名称', '名称', '产品名称', '产品'],
  'softwareVersion': ['软件版本', '版本号', '版本'],
  'softwareId': ['软件标识', '软件ID', '标识', 'ID', '编号', '项目编号', '课题编号', '报错编号'],
  'productType': ['组件', '产品类型', '类型'],
  'detectorFlag': ['检测仪标识', '检测仪配置', '检测仪'],
  
  // 可选信息字段
  'aircraftModel': ['机型', '飞机型号', '型号'],
  'projectDirector': ['项目总师', '总师', '项目主管总师'],
  'developmentDepartment': ['研制部门', '申请部门', '部门'],
  'chiefDesigner': ['主任设计师', '设计师'],
  'projectManager': ['项目主管'],
  
  // 其他字段（可能出现但不映射到表单）
  'phone': ['电话', '联系电话'],
  'testLevel': ['申请测试级别', '测试级别'],
  'purpose': ['用途'],
  'productModel': ['产品型号'],
  'relatedMatter': ['关联重大事项', '重大事项'],
  'fillTime': ['填写时间', '时间'],
  'projectCode': ['课题代号', '代号']
}

// 清除结果
const clearResult = () => {
  hasResult.value = false
}

// 模糊匹配字段名（容错）
const fuzzyMatchField = (inputKey) => {
  // 清理输入的key（去除星号、空格、冒号、引号等）
  // 支持: "*电话", "* 电话", " *电话 ", ""电话"" 等格式
  let cleanKey = inputKey.trim()
  
  // 去除开头的星号和空格
  cleanKey = cleanKey.replace(/^[\s*""'']+/g, '')
  // 去除结尾的空格、冒号、引号
  cleanKey = cleanKey.replace(/[:：\s""'']+$/g, '')
  
  console.log('🔍 尝试匹配字段:', `"${inputKey}" => "${cleanKey}"`)
  
  // 第一轮：完全匹配
  for (const [fieldName, possibleKeys] of Object.entries(fieldMappings)) {
    if (possibleKeys.includes(cleanKey)) {
      console.log(`  ✅ 完全匹配: "${cleanKey}" -> ${fieldName}`)
      return fieldName
    }
  }
  
  // 第二轮：从右向左部分匹配（优先匹配末尾）
  // 例如："报错编号" 应该匹配 "编号"
  for (const [fieldName, possibleKeys] of Object.entries(fieldMappings)) {
    for (const possibleKey of possibleKeys) {
      if (cleanKey.endsWith(possibleKey) && possibleKey.length >= 2) {
        console.log(`  ✅ 末尾匹配: "${cleanKey}" -> ${fieldName} (关键词: ${possibleKey})`)
        return fieldName
      }
    }
  }
  
  // 第三轮：包含关系匹配
  for (const [fieldName, possibleKeys] of Object.entries(fieldMappings)) {
    for (const possibleKey of possibleKeys) {
      if (cleanKey.includes(possibleKey) && possibleKey.length >= 2) {
        console.log(`  ✅ 包含匹配: "${cleanKey}" -> ${fieldName} (关键词: ${possibleKey})`)
        return fieldName
      }
    }
  }
  
  console.log(`  ❌ 未匹配: "${cleanKey}"`)
  return null
}

// 获取所有可能的字段关键词（用于智能匹配）
const getAllFieldKeywords = () => {
  const keywords = []
  for (const [fieldName, possibleKeys] of Object.entries(fieldMappings)) {
    for (const key of possibleKeys) {
      keywords.push({ keyword: key, fieldName, length: key.length })
    }
  }
  // 按长度降序排序，优先匹配更长的关键词（避免"主管"匹配了"测试主管"）
  keywords.sort((a, b) => b.length - a.length)
  return keywords
}

// 解析OCR文本（支持无冒号格式）
const parseOCRText = (text) => {
  console.log('==================== 开始解析OCR文本 ====================')
  console.log('原始文本长度:', text.length, '字符')
  console.log('原始文本内容:\n', text)
  console.log('=========================================================')
  
  const basicInfo = {}
  const optionalInfo = {}
  const unmatchedFields = []
  
  // 获取所有字段关键词
  const fieldKeywords = getAllFieldKeywords()
  console.log('📚 已加载', fieldKeywords.length, '个字段关键词')
  
  // 按行分割
  const lines = text.split('\n')
  console.log(`📝 共 ${lines.length} 行`)
  
  let lineIndex = 0
  for (const line of lines) {
    lineIndex++
    // 跳过空行
    if (!line.trim()) {
      console.log(`行 ${lineIndex}: (空行，跳过)`)
      continue
    }
    
    console.log(`\n行 ${lineIndex}: "${line}"`)
    
    // 清理行：去除前导星号和空格
    let cleanLine = line.trim().replace(/^[\s*]+/, '')
    console.log(`  🧹 清理后: "${cleanLine}"`)
    
    // 方法1: 尝试用冒号分隔（兼容旧格式）
    const colonMatch = cleanLine.match(/^([^:：]+?)[:：]\s*(.*)$/)
    if (colonMatch) {
      let key = colonMatch[1].trim()
      const value = colonMatch[2].trim()
      
      console.log(`  📌 [冒号格式] key="${key}", value="${value}"`)
      
      if (!value) {
        console.log(`  ⚠️  值为空，跳过`)
        continue
      }
      
      const matchedField = fuzzyMatchField(key)
      
      if (matchedField) {
        storeField(matchedField, value, basicInfo, optionalInfo)
      } else {
        unmatchedFields.push({ key, value })
        console.log(`  ❌ 字段未匹配`)
      }
      continue
    }
    
    // 方法2: 智能匹配（无冒号格式）
    // 尝试从行首匹配所有可能的字段关键词
    let matched = false
    for (const { keyword, fieldName } of fieldKeywords) {
      // 检查行是否以该关键词开头
      if (cleanLine.startsWith(keyword)) {
        // 提取值：去除关键词后的剩余部分
        let value = cleanLine.substring(keyword.length).trim()
        
        // 值不能为空
        if (!value) {
          continue
        }
        
        console.log(`  📌 [智能匹配] 关键词="${keyword}" → 字段="${fieldName}", 值="${value}"`)
        
        storeField(fieldName, value, basicInfo, optionalInfo)
        matched = true
        break
      }
    }
    
    if (!matched) {
      unmatchedFields.push({ key: cleanLine, value: '' })
      console.log(`  ❌ 未能匹配任何字段`)
    }
  }
  
  console.log('\n==================== 解析结果统计 ====================')
  console.log('✅ 基本信息字段:', Object.keys(basicInfo).length, '个', basicInfo)
  console.log('✅ 可选信息字段:', Object.keys(optionalInfo).length, '个', optionalInfo)
  console.log('❌ 未匹配字段:', unmatchedFields.length, '个', unmatchedFields.map(f => f.key))
  console.log('=========================================================\n')
  
  // ✨ 根据申请部门推断所属领域和测试人员
  console.log('==================== 智能推断 ====================')
  inferDomainAndPersonnel(basicInfo, optionalInfo)
  console.log('===================================================\n')
  
  return { basicInfo, optionalInfo, unmatchedFields }
}

// 根据申请部门推断所属领域和测试人员
const inferDomainAndPersonnel = (basicInfo, optionalInfo) => {
  const department = optionalInfo.developmentDepartment
  
  if (!department) {
    console.log('⚠️  未找到申请部门，无法推断领域和测试人员')
    return
  }
  
  console.log(`🔍 开始推断 - 申请部门: "${department}"`)
  
  // 1. 精确匹配
  let domain = departmentToDomain[department]
  
  // 2. 部分匹配（如果精确匹配失败）
  if (!domain) {
    console.log('  尝试部分匹配...')
    for (const [configDept, configDomain] of Object.entries(departmentToDomain)) {
      if (configDept.includes(department) || department.includes(configDept)) {
        domain = configDomain
        console.log(`  ✓ 部分匹配成功: "${department}" ≈ "${configDept}" → "${domain}"`)
        break
      }
    }
  }
  
  // 3. 关键词匹配（如果部分匹配也失败）
  if (!domain) {
    console.log('  尝试关键词匹配...')
    if (department.includes('光电') || department.includes('图像') || department.includes('激光')) {
      domain = '光电领域'
    } else if (department.includes('瞄准') || department.includes('显示')) {
      domain = '显示领域'
    } else if (department.includes('总体') || department.includes('火控') || department.includes('重点实验室')) {
      domain = '火控领域'
    } else if (department.includes('武控') || department.includes('外挂')) {
      domain = '外挂领域'
    }
    
    if (domain) {
      console.log(`  ✓ 关键词匹配成功: "${department}" → "${domain}"`)
    }
  }
  
  // 4. 根据领域设置测试人员
  if (domain) {
    basicInfo.domain = domain
    console.log(`  ✅ 所属领域: "${domain}"`)
    
    const personnel = domainPersonnel[domain]
    if (personnel) {
      basicInfo.testManager = personnel.testManager
      basicInfo.testPersonnel = personnel.testPersonnel
      console.log(`  ✅ 测试主管: "${personnel.testManager}"`)
      console.log(`  ✅ 测试人员: "${personnel.testPersonnel}"`)
    }
  } else {
    console.log(`  ❌ 所有匹配策略都失败，无法推断领域`)
  }
}

// 存储字段到对应的对象中
const storeField = (fieldName, value, basicInfo, optionalInfo) => {
  // 基本信息字段
  if (['domain', 'testManager', 'testPersonnel', 'developer', 'softwareName', 
       'softwareVersion', 'softwareId', 'productType', 'detectorFlag'].includes(fieldName)) {
    basicInfo[fieldName] = value
    console.log(`  ✅ 存入基本信息: ${fieldName} = "${value}"`)
  }
  // 可选信息字段
  else if (['aircraftModel', 'projectDirector', 'developmentDepartment', 
            'chiefDesigner', 'projectManager'].includes(fieldName)) {
    optionalInfo[fieldName] = value
    console.log(`  ✅ 存入可选信息: ${fieldName} = "${value}"`)
  }
}

// 处理粘贴
const handlePaste = async (e) => {
  e.preventDefault()
  
  if (isProcessing.value) {
    ElMessage.warning('正在处理中，请稍候...')
    return
  }
  
  // 获取粘贴的文本
  const text = e.clipboardData.getData('text')
  
  if (!text || !text.trim()) {
    ElMessage.warning('粘贴内容为空，请复制OCR识别结果后再粘贴')
    return
  }
  
  try {
    // 开始处理
    isProcessing.value = true
    hasResult.value = false
    processingProgress.value = 0
    processingMessage.value = '正在解析文本...'
    
    // 模拟处理进度
    processingProgress.value = 30
    
    // 解析文本
    const { basicInfo, optionalInfo, unmatchedFields } = parseOCRText(text)
    
    processingProgress.value = 70
    processingMessage.value = '正在填充表单...'
    
    // 检查是否解析到任何字段
    const totalFields = Object.keys(basicInfo).length + Object.keys(optionalInfo).length
    
    if (totalFields === 0) {
      console.error('❌ 解析失败：未能识别到任何有效字段')
      console.error('提示：支持以下格式')
      console.error('  1. 带冒号: "编号：20250909" 或 "编号:20250909"')
      console.error('  2. 无冒号: "编号20250909"')
      console.error('  3. 带空格: "主任设计师 张三"')
      console.error('  4. 带星号: "*电话5833" 或 "* 机型雷霆"')
      throw new Error('未能识别到任何有效字段。\n请确保：\n1. 每个字段单独一行\n2. 字段名在支持列表中\n3. 查看控制台(F12)了解详细信息')
    }
    
    // 构建返回的数据结构（与原OCR API格式一致）
    const extractedData = {}
    
    if (Object.keys(basicInfo).length > 0) {
      // 转换为后端期望的字段名
      extractedData.basic_info = {
        domain: basicInfo.domain,
        test_manager: basicInfo.testManager,
        test_personnel: basicInfo.testPersonnel,
        developer: basicInfo.developer
      }
    }
    
    if (Object.keys(optionalInfo).length > 0) {
      extractedData.optional_info = {
        aircraft_model: optionalInfo.aircraftModel,
        project_director: optionalInfo.projectDirector,
        development_department: optionalInfo.developmentDepartment,
        chief_designer: optionalInfo.chiefDesigner,
        project_manager: optionalInfo.projectManager,
        component: basicInfo.productType  // 组件字段放在optional_info中
      }
    }
    
    // 完成
    processingProgress.value = 100
    processingMessage.value = '解析完成'
    
    // 短暂延迟后显示结果
    setTimeout(() => {
      isProcessing.value = false
      hasResult.value = true
      
      // 发送数据到父组件
      emit('dataExtracted', extractedData)
      
      let message = `文本解析完成，已自动填入${totalFields}个字段`
      if (unmatchedFields.length > 0) {
        message += `，${unmatchedFields.length}个字段未识别`
      }
      ElMessage.success(message)
      
      // 如果有未匹配的字段，显示提示
      if (unmatchedFields.length > 0) {
        console.warn('以下字段未能匹配:', unmatchedFields.map(f => f.key).join(', '))
      }
    }, 500)
    
  } catch (error) {
    console.error('文本解析错误:', error)
    isProcessing.value = false
    hasResult.value = false
    ElMessage.error(error.message || '文本解析失败')
  }
}

// 生命周期
onMounted(() => {
  // 全局粘贴事件监听
  document.addEventListener('paste', handlePaste)
  
  // 聚焦到拖拽区域以便接收键盘事件
  if (dropZone.value) {
    dropZone.value.addEventListener('paste', handlePaste)
    // 自动聚焦
    dropZone.value.focus()
  }
})

onUnmounted(() => {
  document.removeEventListener('paste', handlePaste)
})
</script>

<style scoped>
.ocr-upload-container {
  margin-bottom: 0;
}

.ocr-compact-card {
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  background: #fafbfc;
  overflow: hidden;
}

.compact-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.header-icon {
  color: #409eff;
  font-size: 16px;
}

.header-title {
  font-weight: 600;
  color: #303133;
  font-size: 14px;
}

.header-right {
  flex-shrink: 0;
}

.info-icon {
  color: #909399;
  font-size: 14px;
  cursor: help;
}

.info-icon:hover {
  color: #409eff;
}

.compact-drop-zone {
  height: 60px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  border: none;
  background: #ffffff;
  cursor: text;
  transition: all 0.3s ease;
  outline: none;
}

.compact-drop-zone:hover,
.compact-drop-zone:focus {
  background-color: #f5f7fa;
  border-left: 2px solid #409eff;
}

.compact-drop-zone.processing {
  background-color: #ecf5ff;
  cursor: default;
}

.compact-drop-content {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.compact-upload-icon {
  width: 18px;
  height: 18px;
  opacity: 0.6;
}

.compact-text {
  font-size: 13px;
  color: #606266;
}

.compact-processing {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.compact-processing-icon {
  font-size: 16px;
  color: #409eff;
  animation: rotating 2s linear infinite;
}

.compact-processing-text {
  font-size: 13px;
  color: #409eff;
  margin-right: 12px;
}

.compact-progress {
  flex: 1;
  max-width: 200px;
}

.compact-result {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.compact-success-icon {
  font-size: 16px;
  color: #67c23a;
}

.compact-result-text {
  font-size: 13px;
  color: #67c23a;
  flex: 1;
}

.clear-button {
  color: #909399;
  padding: 0;
  margin-left: auto;
}

.clear-button:hover {
  color: #f56c6c;
}

@keyframes rotating {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

kbd {
  background-color: #f5f5f5;
  border: 1px solid #d0d0d0;
  border-radius: 2px;
  padding: 1px 3px;
  font-size: 11px;
  font-family: monospace;
}
</style> 