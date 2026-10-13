<template>
  <div class="cytoscape-wrapper">
    <div ref="cytoscapeContainer" class="cytoscape-container"></div>
    <div class="graph-toolbar">
      <button class="graph-btn" type="button" @click="zoomIn">+</button>
      <button class="graph-btn" type="button" @click="zoomOut">-</button>
      <button class="graph-btn" type="button" @click="fit">适配</button>
      <button class="graph-btn" type="button" @click="resetView">重置</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import cytoscape from 'cytoscape'

// Props
const props = defineProps({
  nodes: {
    type: Array,
    default: () => []
  },
  edges: {
    type: Array,
    default: () => []
  },
  roots: {
    type: Array,
    default: () => []
  },
  statistics: {
    type: Object,
    default: () => ({})
  }
})

// Emits
const emit = defineEmits(['nodeSelected', 'nodeDeselected'])

// 响应式数据
const cytoscapeContainer = ref(null)
let cy = null

// 生命周期
watch(
  () => props.nodes,
  () => {
    scheduleInit()
  },
  { immediate: true }
)

// 监听数据变化
function scheduleInit() {
  if (!props.nodes || props.nodes.length === 0) {
    return
  }

  nextTick(() => {
    requestAnimationFrame(() => {
      initCytoscape()
    })
  })
}

// 监听容器可见性变化
watch(() => cytoscapeContainer.value?.offsetParent, (newVal) => {
  if (newVal) {
    scheduleInit()
  }
})

// 方法
function initCytoscape() {
  if (!cytoscapeContainer.value) {
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
  
  const elements = [];
  
  // 添加节点
  ;(props.nodes || []).forEach(node => {
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
  });
  
  // 添加边
  ;(props.edges || []).forEach(edge => {
    const weight = edge.weight ?? edge.count
    const label = weight != null ? `${edge.type || 'calls'} (${weight})` : (edge.type || 'calls')
    elements.push({
      data: {
        id: edge.id,
        source: edge.source,
        target: edge.target,
        type: edge.type,
        weight,
        label
      },
      classes: [edge.type]
    })
  });
  
  const nodeIdSet = new Set((props.nodes || []).map(n => n.id))
  const indegree = new Map()
  ;(props.nodes || []).forEach(n => indegree.set(n.id, 0))
  ;(props.edges || []).forEach(e => {
    const t = e.target
    const s = e.source
    if (!nodeIdSet.has(t) || !nodeIdSet.has(s)) return
    indegree.set(t, (indegree.get(t) || 0) + 1)
  })
  const roots = (props.nodes || []).filter(n => (indegree.get(n.id) || 0) === 0).map(n => n.id)
  
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
            'font-size': '14px',
            'font-weight': '600',
            'color': '#fff',
            'text-outline-width': 1,
            'text-outline-color': '#000',
            'text-wrap': 'wrap',
            'text-max-width': 320,
            'padding': '10px',
            'width': 'label',
            'height': 'label',
            'min-width': 120,
            'min-height': 56,
            'shape': 'roundrectangle'
          }
        },
        {
          selector: 'node.file',
          style: {
            'background-color': '#3498db',
            'shape': 'rectangle',
            'text-max-width': 320
          }
        },
        {
          selector: 'node.function',
          style: {
            'background-color': '#2ecc71',
            'shape': 'roundrectangle',
            'text-max-width': 320
          }
        },
        {
          selector: 'node.fpga_file',
          style: {
            'background-color': '#9b59b6',
            'shape': 'rectangle',
            'text-max-width': 320
          }
        },
        {
          selector: 'node.fpga_module',
          style: {
            'background-color': '#e67e22',
            'shape': 'hexagon',
            'text-max-width': 320
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
            'curve-style': 'bezier',
            'label': 'data(label)',
            'font-size': '14px',
            'color': '#2c3e50',
            'text-rotation': 'autorotate',
            'text-background-opacity': 1,
            'text-background-color': '#ffffff',
            'text-background-padding': '2px',
            'text-border-color': '#dfe6e9',
            'text-border-width': 1
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
        spacingFactor: 2.2,
        padding: 40,
        circle: false,
        roots: roots.length > 0 ? roots : undefined,
        orientation: 'vertical'
      },
      minZoom: 0.1,
      maxZoom: 5,
      wheelSensitivity: 0.5,  
      zoomingEnabled: true,
      userZoomingEnabled: true,
      panningEnabled: true,
      userPanningEnabled: true,
      boxSelectionEnabled: false,
      selectionType: 'single',
      autolock: false,
      autoungrabify: false
    })
    
    cy.userPanningEnabled(true)
    cy.userZoomingEnabled(true)
    cy.panningEnabled(true)
    cy.zoomingEnabled(true)
    cy.autoungrabify(false)
    cy.autolock(false)
    
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

function zoomIn() {
  if (!cy) return
  const z = cy.zoom()
  cy.zoom({ level: Math.min(z * 1.2, cy.maxZoom()), renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } })
}

function zoomOut() {
  if (!cy) return
  const z = cy.zoom()
  cy.zoom({ level: Math.max(z / 1.2, cy.minZoom()), renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } })
}

function fit() {
  if (!cy) return
  cy.fit(undefined, 40)
}

function resetView() {
  if (!cy) return
  cy.zoom(1)
  cy.pan({ x: 0, y: 0 })
  cy.fit(undefined, 40)
}

// 暴露方法
function highlightNode(nodeId) {
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

function refreshLayout() {
  if (cy) {
    cy.layout({
      name: 'breadthfirst',
      directed: true,
      spacingFactor: 2.2,
      padding: 40,
      circle: false,
      orientation: 'vertical'
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
  if (cytoscapeContainer.value) {
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
  focusOnNode,
  zoomIn,
  zoomOut,
  fit,
  resetView
})
</script>

<style scoped>
.cytoscape-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
}

.cytoscape-container {
  width: 100%;
  height: 100%;
  min-width: 400px;
  min-height: 300px;
  background: transparent;
  border-radius: 8px;
  box-shadow: inset 0 0 10px rgba(0,0,0,0.1);
  touch-action: none;
}

.graph-toolbar {
  position: absolute;
  right: 10px;
  top: 10px;
  display: flex;
  gap: 8px;
  z-index: 10;
}

.graph-btn {
  background: rgba(17, 24, 39, 0.85) !important;
  color: #ffffff !important;
  border: 1px solid rgba(255, 255, 255, 0.35) !important;
  border-radius: 6px;
  padding: 6px 10px;
  font-size: 12px;
  line-height: 1;
  cursor: pointer;
  user-select: none;
  box-shadow: 0 2px 8px rgba(0,0,0,0.25);
}

.graph-btn:hover {
  background: rgba(17, 24, 39, 0.95) !important;
}
</style>