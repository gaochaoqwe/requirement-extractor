import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { databaseManageService } from '@/services/databaseManageService'

export function useTableData() {
  // 响应式数据
  const data = ref([])
  const loading = ref(false)
  const totalRecords = ref(0)
  const searchText = ref('')
  
  // 表格配置
  const columns = ref([
    { key: 'software_category', title: '软件类别', required: true },
    { key: 'test_item_name', title: '测试项名称', required: true },
    { key: 'test_item_description', title: '测试项描述', required: false },
    { key: 'test_method', title: '测试方法', required: false }
  ])

  // 列宽配置
  const columnWidths = reactive({
    software_category: 120,
    test_item_name: 200,
    test_item_description: 350,
    test_method: 350
  })

  // 软件类别排序映射
  const categoryOrderMap = {
    "通用": 1,
    "随动": 2,
    "图像": 3,
    "红外": 4,
    "激光": 5,
    "分色滤光": 6,
    "手柄": 7
  }

  function getCategoryOrder(category) {
    return categoryOrderMap[category] || 999
  }

  // 计算属性
  const filteredData = computed(() => {
    if (!searchText.value) return data.value
    return data.value.filter(row =>
      Object.values(row).some(value =>
        String(value).toLowerCase().includes(searchText.value.toLowerCase())
      )
    )
  })

  // 按软件类别自动排序
  const sortedData = computed(() => {
    const arr = [...(filteredData.value || [])]
    return arr.sort((a, b) => {
      // 首先按软件类别排序
      const categoryOrderA = getCategoryOrder(a.software_category)
      const categoryOrderB = getCategoryOrder(b.software_category)
      if (categoryOrderA !== categoryOrderB) {
        return categoryOrderA - categoryOrderB
      }
      
      // 然后按测试项排序
      const itemOrderA = a.item_order || 0
      const itemOrderB = b.item_order || 0
      return itemOrderA - itemOrderB
    })
  })

  // 方法
  const loadData = async () => {
    try {
      loading.value = true
      const response = await databaseManageService.getRequirementsSorted()
      data.value = response.data || []
      totalRecords.value = data.value.length
    } catch (error) {
      ElMessage.error('加载数据失败: ' + error.message)
    } finally {
      loading.value = false
    }
  }

  const getCellValue = (row, key) => {
    return row[key] || ''
  }

  // 格式化多行文本显示
  const formatMultilineText = (text) => {
    if (!text) return ''
    return String(text)
      .split('\n')
      .map(line => line.trim())
      .filter(line => line)
      .map(line => `<div class="text-line">${line}</div>`)
      .join('')
  }

  // 构建新行
  const buildNewRow = (anchor = {}) => ({
    software_category: anchor.software_category || '',
    test_item_name: '',
    test_item_description: '',
    test_method: '',
    item_order: 0
  })

  // 创建并插入行
  const createAndInsert = async (newRow, insertIndex) => {
    try {
      const resp = await databaseManageService.createRequirement(newRow)
      const created = (resp && (resp.data || resp)) || {}
      const rowToInsert = { ...newRow, ...created }
      data.value.splice(insertIndex, 0, rowToInsert)
      totalRecords.value = data.value.length
      ElMessage.success('新增行已保存')
      return rowToInsert
    } catch (e) {
      data.value.splice(insertIndex, 0, { ...newRow })
      totalRecords.value = data.value.length
      ElMessage.error('新增行保存失败：' + (e.message || e))
      return newRow
    }
  }

  return {
    // 数据
    data,
    loading,
    totalRecords,
    searchText,
    columns,
    columnWidths,
    
    // 计算属性
    filteredData,
    sortedData,
    
    // 方法
    loadData,
    getCellValue,
    formatMultilineText,
    buildNewRow,
    createAndInsert,
    getCategoryOrder
  }
} 