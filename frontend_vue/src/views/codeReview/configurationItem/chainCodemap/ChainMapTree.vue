<template>
  <div class="chain-map-tree">
    <div class="chain-list">
      <div
        v-for="chain in chainList"
        :key="chain.id"
        :class="['chain-item', { selected: selectedChain?.id === chain.id, expanded: expandedChains[chain.id] }]"
      >
        <!-- 链路头部信息 -->
        <div class="chain-header" @click="selectChain(chain)">
          <div class="chain-info">
            <i class="chain-icon el-icon-connection"></i>
            <span class="chain-name">{{ chain.name }}</span>
            <span class="problem-count" v-if="chain.problemCount > 0">({{ chain.problemCount }})</span>
            <i 
              :class="['expand-icon', expandedChains[chain.id] ? 'el-icon-arrow-down' : 'el-icon-arrow-right']"
              @click.stop="toggleChainExpansion(chain.id)"
            ></i>
          </div>
          <div class="chain-functions" v-if="chain.functions && chain.functions.length">
            <span class="function-label">函数数量:</span>
            <span class="function-count">{{ chain.functions.length }}</span>
          </div>
        </div>
        
        <!-- 函数列表（可展开） -->
        <div v-if="expandedChains[chain.id] && chain.functions" class="function-list">
          <div 
            v-for="(func, index) in chain.functions" 
            :key="`${chain.id}_func_${index}`"
            :class="['function-item', { selected: selectedFunction?.chainId === chain.id && selectedFunction?.index === index }]"
            @click.stop="selectFunction(chain, func, index)"
            :title="getFunctionTooltip(func)"
          >
            <div class="function-item-content">
              <i class="function-icon el-icon-cpu"></i>
              <span class="function-display">{{ formatFunctionDisplay(func) }}</span>
            </div>
            <span class="function-order">{{ index + 1 }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'

const props = defineProps({
  taskId: {
    type: [String, Number],
    required: true
  },
  selectedChain: {
    type: Object,
    default: null
  },
  treeData: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['chain-select', 'function-select'])

// 展开状态管理
const expandedChains = reactive({})
const selectedFunction = ref(null)

// 链路列表数据 - 使用从父组件传递的treeData
const chainList = computed(() => {
  return props.treeData || []
})

// 生成模拟链路列表
function generateMockChainList() {
  return [
    {
      id: 'chain_1',
      name: '系统初始化链路',
      description: '系统启动、初始化、配置加载的完整流程',
      functionCount: 8,
      problemCount: 2,
      functions: ['main', 'initialize_system', 'logger_init', 'param_loader_init', 'camera_driver_init', 'feature_extractor_init', 'system_controller_init', 'memory_pool_create']
    },
    {
      id: 'chain_2',
      name: '图像采集链路',
      description: '相机驱动、图像捕获、数据处理的核心流程',
      functionCount: 6,
      problemCount: 5,
      functions: ['camera_driver_start', 'capture_thread_func', 'camera_driver_capture_frame', 'memory_pool_alloc', 'system_controller_process', 'memory_pool_free']
    },
    {
      id: 'chain_3',
      name: '特征提取链路',
      description: '图像特征检测、角点提取、数据分析',
      functionCount: 4,
      problemCount: 1,
      functions: ['feature_extractor_extract', 'harris_corner_detection', 'fast_corner_detection', 'feature_extractor_set_params']
    },
    {
      id: 'chain_4',
      name: '系统监控链路',
      description: '日志记录、状态监控、异常处理',
      functionCount: 5,
      problemCount: 3,
      functions: ['logger_info', 'logger_warning', 'log_internal', 'signal_handler', 'memory_pool_get_stats']
    },
    {
      id: 'chain_5',
      name: '配置管理链路',
      description: '参数加载、配置验证、动态重载',
      functionCount: 4,
      problemCount: 2,
      functions: ['param_loader_load_config', 'param_loader_validate_config', 'param_loader_reload', 'param_loader_cleanup']
    },
    {
      id: 'chain_6',
      name: '系统关闭链路',
      description: '资源释放、系统清理、安全退出',
      functionCount: 7,
      problemCount: 4,
      functions: ['cleanup_system', 'system_controller_shutdown', 'camera_driver_stop', 'feature_extractor_destroy', 'memory_pool_destroy', 'logger_cleanup', 'param_loader_cleanup']
    }
  ]
}

// 选择链路
function selectChain(chain) {
  // 自动展开链路的函数列表
  expandedChains[chain.id] = true
  emit('chain-select', chain)
}

// 切换链路展开状态
function toggleChainExpansion(chainId) {
  expandedChains[chainId] = !expandedChains[chainId]
}

// 选择函数
function selectFunction(chain, func, index) {
  selectedFunction.value = { chainId: chain.id, index }
  emit('function-select', { chain, func, index })
}

// 格式化函数显示 - 显示格式: 文件路径->函数名
function formatFunctionDisplay(func) {
  // 如果是字符串格式（旧格式）
  if (typeof func === 'string') {
    return func
  }
  
  // 如果是对象格式（新格式）
  const funcName = func.function_name || func.name || func.function || '未知函数'
  
  if (func.file_path) {
    // 显示格式: user/user.cpp->userAdd()
    return `${func.file_path}->${funcName}`
  }
  
  return funcName
}

// 获取函数的提示信息
function getFunctionTooltip(func) {
  if (typeof func === 'string') {
    return func
  }
  
  const funcName = func.function_name || func.name || func.function || '未知函数'
  const filePath = func.file_path || '未知文件'
  const lines = func.start_line && func.end_line ? ` (行 ${func.start_line}-${func.end_line})` : ''
  
  return `函数: ${funcName}\n文件: ${filePath}${lines}`
}

// 移除onMounted中的fetchChainList调用，因为现在使用props.treeData
</script>

<style scoped>
.chain-map-tree {
  height: 100%;
  overflow: auto;
}

.chain-list {
  padding: 8px;
}

.chain-item {
  margin-bottom: 8px;
  border-radius: 8px;
  transition: all 0.2s ease;
  border: 1px solid #e4e7ed;
  background: #ffffff;
}

.chain-header {
  padding: 12px;
  cursor: pointer;
}

.chain-header:hover {
  background-color: #f5f7fa;
}

.chain-item:hover {
  border-color: #c0c4cc;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chain-item.selected .chain-header {
  background-color: #ecf5ff;
  color: #409eff;
}

.chain-item.selected {
  border-color: #409eff;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.2);
}

.chain-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.chain-icon {
  font-size: 18px;
  color: #606266;
}

.chain-item.selected .chain-icon {
  color: #409eff;
}

.expand-icon {
  margin-left: auto;
  font-size: 14px;
  color: #909399;
  transition: transform 0.2s ease;
}

.expand-icon:hover {
  color: #409eff;
}

.function-list {
  border-top: 1px solid #f0f0f0;
  background: #fafafa;
}

.function-item {
  padding: 8px 16px 8px 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  transition: background-color 0.2s ease;
  border-bottom: 1px solid #f5f5f5;
}

.function-item:hover {
  background-color: #f0f9ff;
}

.function-item.selected {
  background-color: #e6f7ff;
  color: #1890ff;
}

.function-item-content {
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 0;
}

.function-icon {
  font-size: 14px;
  color: #67c23a;
  margin-right: 8px;
  flex-shrink: 0;
}

.function-display {
  flex: 1;
  font-size: 12px;
  font-family: 'Courier New', monospace;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.4;
}

.function-name {
  flex: 1;
  font-size: 13px;
  font-family: 'Courier New', monospace;
}

.function-order {
  font-size: 12px;
  color: #909399;
  background: #f0f0f0;
  padding: 2px 6px;
  border-radius: 10px;
  min-width: 20px;
  text-align: center;
}

.chain-name {
  font-weight: 600;
  font-size: 15px;
  flex: 1;
}

.problem-count {
  font-size: 12px;
  color: #f56c6c;
  font-weight: bold;
  background: #fef0f0;
  padding: 2px 6px;
  border-radius: 10px;
}

.chain-description {
  font-size: 13px;
  color: #909399;
  margin-bottom: 6px;
  line-height: 1.4;
  margin-left: 26px;
}

.chain-functions {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: 26px;
}

.function-label {
  font-size: 12px;
  color: #909399;
}

.function-count {
  font-size: 12px;
  color: #67c23a;
  font-weight: 600;
  background: #f0f9ff;
  padding: 2px 6px;
  border-radius: 10px;
}

/* 滚动条样式 */
.chain-map-tree::-webkit-scrollbar {
  width: 6px;
}

.chain-map-tree::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.chain-map-tree::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.chain-map-tree::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style> 