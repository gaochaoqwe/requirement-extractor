<template>
  <div ref="cytoscapeContainer" class="cytoscape-container"></div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import cytoscape from 'cytoscape'

// Props
const props = defineProps({
  codeMapData: {
    type: Object,
    default: null
  }
})

// Emits
const emit = defineEmits(['nodeSelected', 'nodeDeselected'])

// 响应式数据
const cytoscapeContainer = ref(null)
let cy = null

// 生命周期
onMounted(() => {
  if (props.codeMapData) {
    // 延迟初始化，确保容器尺寸正确
    nextTick(() => {
      setTimeout(() => {
        initCytoscape()
      }, 500) // 增加延迟时间
    })
  }
})

// 监听数据变化
watch(() => props.codeMapData, (newData) => {
  if (newData) {
    nextTick(() => {
      setTimeout(() => {
        initCytoscape()
      }, 500) // 增加延迟时间
    })
  }
})

// 监听容器可见性变化
watch(() => cytoscapeContainer.value?.offsetParent, (newVal) => {
  // 当容器从隐藏变为可见时，重新初始化
  if (newVal && props.codeMapData) {
    console.log('Container became visible, reinitializing...')
    nextTick(() => {
      setTimeout(() => {
        initCytoscape()
      }, 300)
    })
  }
})

// 方法
function initCytoscape() {
  if (!props.codeMapData || !cytoscapeContainer.value) {
    console.log('Data or container not available')
    return
  }
  
  // 检查容器是否可见（不是被v-show隐藏）
  if (!cytoscapeContainer.value.offsetParent) {
    console.log('Container is hidden, skipping initialization')
    return
  }
  
  // 确保容器可见且有尺寸
  const containerRect = cytoscapeContainer.value.getBoundingClientRect()
  console.log('Container rect:', containerRect)
  
  if (containerRect.width === 0 || containerRect.height === 0) {
    console.log('Container not ready, retrying...')
    setTimeout(() => initCytoscape(), 300)
    return
  }
  
  // 如果已存在实例，先销毁
  if (cy) {
    cy.destroy()
    cy = null
  }
  
  const elements = []
  
  // 添加节点
  props.codeMapData.nodes.forEach(node => {
    const hasProblems = node.problems && node.problems.length > 0
    elements.push({
      data: {
        id: node.id,
        label: node.name,
        type: node.type,
        problems: node.problems?.length || 0,
        ...node
      },
      classes: [
        node.type,
        hasProblems ? 'has-problems' : 'no-problems'
      ]
    })
  })
  
  // 添加边
  props.codeMapData.edges.forEach(edge => {
    elements.push({
      data: {
        id: edge.id,
        source: edge.source,
        target: edge.target,
        type: edge.type
      },
      classes: [edge.type]
    })
  })
  
  console.log('Initializing Cytoscape with', elements.length, 'elements')
  
  // 初始化Cytoscape
  try {
    cy = cytoscape({
      container: cytoscapeContainer.value,
      elements: elements,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': '#666',
            'label': 'data(label)',
            'text-valign': 'center',
            'text-halign': 'center',
            'font-size': '20px',  // 进一步增大字体
            'font-weight': 'bold',
            'color': '#fff',
            'text-outline-width': 3,
            'text-outline-color': '#000',
            'width': '140px',     // 增大节点尺寸
            'height': '80px',
            'shape': 'roundrectangle'
          }
        },
        {
          selector: 'node.file',
          style: {
            'background-color': '#3498db',
            'shape': 'rectangle',
            'width': '160px',
            'height': '70px'
          }
        },
        {
          selector: 'node.function',
          style: {
            'background-color': '#2ecc71',
            'shape': 'ellipse',
            'width': '150px',
            'height': '75px'
          }
        },
        {
          selector: 'node.fpga_file',
          style: {
            'background-color': '#9b59b6',
            'shape': 'rectangle',
            'width': '160px',
            'height': '70px'
          }
        },
        {
          selector: 'node.fpga_module',
          style: {
            'background-color': '#e67e22',
            'shape': 'hexagon',
            'width': '150px',
            'height': '75px'
          }
        },
        {
          selector: 'node.has-problems',
          style: {
            'background-color': '#e74c3c',
            'border-width': '4px',
            'border-color': '#c0392b'
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 3,
            'line-color': '#95a5a6',
            'target-arrow-color': '#95a5a6',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier'
          }
        },
        {
          selector: 'edge.calls',
          style: {
            'line-color': '#3498db',
            'target-arrow-color': '#3498db',
            'line-style': 'solid'
          }
        },
        {
          selector: 'edge.contains',
          style: {
            'line-color': '#95a5a6',
            'target-arrow-color': '#95a5a6',
            'line-style': 'dashed'
          }
        },
        {
          selector: ':selected',
          style: {
            'background-color': '#f39c12',
            'border-width': '4px',
            'border-color': '#e67e22'
          }
        },
        {
          selector: '.highlighted',
          style: {
            'background-color': '#9b59b6',
            'border-width': '4px',
            'border-color': '#8e44ad'
          }
        }
      ],
      layout: {
        name: 'breadthfirst',
        directed: true,
        roots: props.codeMapData.root_nodes,
        padding: 20,
        spacingFactor: 2
      },
      minZoom: 0.1,
      maxZoom: 5,
      wheelSensitivity: 0.5,  // 提高缩放灵敏度
      zoomingEnabled: true,
      userZoomingEnabled: true,
      panningEnabled: true,
      userPanningEnabled: true,
      boxSelectionEnabled: false,
      selectionType: 'single',
      autolock: false,
      autoungrabify: false
    })
    
    console.log('Cytoscape initialized successfully')
    
    // 绑定事件
    cy.on('tap', 'node', (event) => {
      const node = event.target
      emit('nodeSelected', node.data())
    })
    
    cy.on('tap', (event) => {
      if (event.target === cy) {
        // 点击空白处
        emit('nodeDeselected')
      }
    })
    
    // 添加双击重置视图
    cy.on('dblclick', (event) => {
      if (event.target === cy) {
        cy.fit()
      }
    })
  } catch (error) {
    console.error('Failed to initialize Cytoscape:', error)
  }
}

// 暴露方法
function highlightNode(nodeId) {
  if (cy) {
    const node = cy.getElementById(nodeId)
    if (node.length > 0) {
      cy.center(node)
      node.select()
      // 高亮节点
      cy.nodes().removeClass('highlighted')
      node.addClass('highlighted')
      emit('nodeSelected', node.data())
    }
  }
}

function refreshLayout() {
  if (cy) {
    cy.layout({
      name: 'breadthfirst',
      directed: true,
      roots: props.codeMapData.root_nodes,
      padding: 20,
      spacingFactor: 2
    }).run()
  }
}

function resizeCytoscape() {
  if (cy) {
    console.log('Resizing Cytoscape...')
    cy.resize()
    cy.fit()
  } else {
    console.log('No Cytoscape instance to resize, initializing...')
    initCytoscape()
  }
}

function forceReinit() {
  console.log('Force reinitializing Cytoscape...')
  if (props.codeMapData && cytoscapeContainer.value) {
    // 先销毁现有实例
    if (cy) {
      cy.destroy()
      cy = null
    }
    // 延迟重新初始化，确保DOM更新完成
    setTimeout(() => {
      initCytoscape()
    }, 100)
  }
}

// 新增方法：聚焦到特定节点
function focusOnNode(nodeId) {
  if (cy) {
    const node = cy.getElementById(nodeId)
    if (node.length > 0) {
      cy.center(node)
      node.select()
      cy.nodes().removeClass('highlighted')
      node.addClass('highlighted')
      emit('nodeSelected', node.data())
    }
  }
}

// 暴露方法给父组件
defineExpose({
  highlightNode,
  refreshLayout,
  resizeCytoscape,
  forceReinit,
  focusOnNode
})
</script>

<style scoped>
.cytoscape-container {
  width: 100%;
  height: 100%;
  min-width: 400px;
  min-height: 300px;
  background: transparent;
  border-radius: 8px;
  box-shadow: inset 0 0 10px rgba(0,0,0,0.1);
}
</style> 