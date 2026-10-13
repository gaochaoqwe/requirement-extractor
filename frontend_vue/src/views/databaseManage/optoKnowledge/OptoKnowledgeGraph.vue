<template>
  <div class="ok-graph">
    <div class="topbar">
      <div class="title">光电知识图谱 - {{ domainLabel }}</div>
      <div class="tools">
        <el-button size="small" type="primary" @click="openCreateNode">新增节点</el-button>
        <el-button size="small" :type="linkMode ? 'warning' : 'default'" @click="toggleLinkMode">
          {{ linkMode ? '连边中…(点2个节点)' : '新增连边' }}
        </el-button>
        <el-input
          v-model="searchText"
          size="small"
          placeholder="搜索节点名称"
          clearable
          @keyup.enter="searchAndFocus"
          class="search"
        />
        <el-button text type="primary" @click="searchAndFocus">定位</el-button>
      </div>
      <el-button text type="primary" @click="back">返回入口</el-button>
    </div>

    <div class="content">
      <div ref="cyRef" class="cy"></div>
    </div>

    <el-drawer v-model="drawerVisible" :with-header="false" size="420px">
      <div class="drawer">
        <div class="drawer-title">{{ drawerTitle }}</div>

        <template v-if="drawerType === 'node'">
          <div class="drawer-row"><span class="k">类型</span><span class="v">{{ selectedNode?.type }}</span></div>
          <div class="drawer-row"><span class="k">Domain</span><span class="v">{{ selectedNode?.domain }}</span></div>
          <div class="drawer-row"><span class="k">摘要</span><span class="v">{{ selectedNode?.summary || '-' }}</span></div>
          <div class="drawer-row"><span class="k">ID</span><span class="v mono">{{ selectedNode?.id }}</span></div>

          <div class="drawer-actions">
            <el-button size="small" type="danger" plain @click="deleteCurrentNode" :disabled="!selectedNode?.id" :loading="deleting">
              删除节点
            </el-button>
          </div>

          <div class="editor">
            <TiptapEditor
              v-model="editorJson"
              :saving="saving"
              :uploading="uploading"
              @save="saveNode"
              @upload-image="handleUploadImage"
            />
          </div>
        </template>

        <template v-else-if="drawerType === 'edge'">
          <div class="drawer-row"><span class="k">类型</span><span class="v">{{ selectedEdge?.type }}</span></div>
          <div class="drawer-row"><span class="k">Source</span><span class="v mono">{{ selectedEdge?.source_id }}</span></div>
          <div class="drawer-row"><span class="k">Target</span><span class="v mono">{{ selectedEdge?.target_id }}</span></div>
          <div class="drawer-row"><span class="k">ID</span><span class="v mono">{{ selectedEdge?.id }}</span></div>

          <div class="drawer-actions">
            <el-button size="small" type="danger" plain @click="deleteCurrentEdge" :disabled="!selectedEdge?.id" :loading="deleting">
              删除连边
            </el-button>
          </div>
        </template>
      </div>
    </el-drawer>

    <el-dialog v-model="createNodeDialog" title="新增节点" width="520px" :close-on-click-modal="false">
      <el-form label-width="88px">
        <el-form-item label="名称">
          <el-input v-model="newNode.name" placeholder="节点名称" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="newNode.type" placeholder="选择类型" style="width: 100%">
            <el-option label="Product" value="Product" />
            <el-option label="Platform" value="Platform" />
            <el-option label="SensorOrEffector" value="SensorOrEffector" />
            <el-option label="SoftwareModule" value="SoftwareModule" />
            <el-option label="DataArtifact" value="DataArtifact" />
            <el-option label="Document" value="Document" />
          </el-select>
        </el-form-item>
        <el-form-item label="摘要">
          <el-input v-model="newNode.summary" type="textarea" :rows="3" placeholder="可选" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="createNodeDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="createNode">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import cytoscape from 'cytoscape'

import TiptapEditor from './TiptapEditor.vue'
import {
  getOptoGraph,
  getOptoNode,
  updateOptoNode,
  uploadOptoAsset,
  createOptoNode,
  deleteOptoNode,
  createOptoEdge,
  deleteOptoEdge,
} from './optoKnowledgeApi'

const route = useRoute()
const router = useRouter()

const domain = computed(() => String(route.params.domain || ''))

const cyRef = ref(null)
let cy = null

const drawerVisible = ref(false)
const selectedNode = ref(null)
const selectedEdge = ref(null)
const drawerType = ref('node')

const searchText = ref('')

const editorJson = ref({ type: 'doc', content: [{ type: 'paragraph' }] })
const saving = ref(false)
const uploading = ref(false)

const creating = ref(false)
const deleting = ref(false)

const createNodeDialog = ref(false)
const newNode = ref({ name: '', type: 'Document', summary: '' })

const linkMode = ref(false)
const linkPick = ref({ sourceId: null })

const domainLabel = computed(() => {
  const m = {
    turret: '转塔',
    countermeasure: '对抗告警',
    optoradar: '光雷',
    pod: '吊舱'
  }

  return m[domain.value] || domain.value
})

const drawerTitle = computed(() => {
  if (drawerType.value === 'edge') return '连边详情'
  return selectedNode.value?.name || '节点详情'
})

function openCreateNode() {
  newNode.value = { name: '', type: 'Document', summary: '' }
  createNodeDialog.value = true
}

async function createNode() {
  const name = (newNode.value.name || '').trim()
  if (!name) return

  creating.value = true
  try {
    await createOptoNode({
      domain: domain.value,
      type: newNode.value.type,
      name,
      summary: newNode.value.summary || null,
      content_json: { type: 'doc', content: [{ type: 'paragraph' }] },
      plain_text: null,
      tags: null,
    })
    createNodeDialog.value = false
    await loadAndRender()
  } finally {
    creating.value = false
  }
}

function toggleLinkMode() {
  linkMode.value = !linkMode.value
  linkPick.value = { sourceId: null }
}

async function handleLinkPick(nodeId) {
  if (!linkPick.value.sourceId) {
    linkPick.value = { sourceId: nodeId }
    const ele = cy?.getElementById(String(nodeId))
    if (ele) {
      applyFocus(ele)
      ele.addClass('flash')
      setTimeout(() => ele.removeClass('flash'), 500)
    }
    return
  }

  const sourceId = linkPick.value.sourceId
  const targetId = nodeId
  if (sourceId === targetId) {
    linkPick.value = { sourceId: null }
    clearFocus()
    return
  }

  creating.value = true
  try {
    await createOptoEdge({
      domain: domain.value,
      type: 'DEPENDS_ON',
      source_id: sourceId,
      target_id: targetId,
      props_json: null,
    })
    linkMode.value = false
    linkPick.value = { sourceId: null }
    await loadAndRender()
  } finally {
    creating.value = false
  }
}

async function deleteCurrentNode() {
  if (!selectedNode.value?.id) return
  deleting.value = true
  try {
    await deleteOptoNode(selectedNode.value.id)
    drawerVisible.value = false
    selectedNode.value = null
    editorJson.value = { type: 'doc', content: [{ type: 'paragraph' }] }
    clearFocus()
    await loadAndRender()
  } finally {
    deleting.value = false
  }
}

async function deleteCurrentEdge() {
  if (!selectedEdge.value?.id) return
  deleting.value = true
  try {
    await deleteOptoEdge(selectedEdge.value.id)
    drawerVisible.value = false
    selectedEdge.value = null
    clearFocus()
    await loadAndRender()
  } finally {
    deleting.value = false
  }
}

function back() {
  router.push('/database-manage/opto-knowledge')
}

function buildElements(graph) {
  const nodes = (graph?.nodes || []).map(n => ({
    data: {
      id: String(n.id),
      label: n.name,
      ...n
    },
    classes: `nt-${n.type || 'default'}`
  }))

  const edges = (graph?.edges || []).map(e => ({
    data: {
      id: String(e.id),
      source: String(e.source_id),
      target: String(e.target_id),
      label: e.type,
      ...e
    },
    classes: `et-${e.type || 'default'}`
  }))

  return [...nodes, ...edges]
}

async function loadAndRender() {
  const graph = await getOptoGraph({ domain: domain.value })
  const elements = buildElements(graph)

  if (!cy) {
    cy = cytoscape({
      container: cyRef.value,
      elements,
      layout: { name: 'cose', animate: true, fit: true, padding: 20 },
      style: [
        {
          selector: 'node',
          style: {
            'background-color': 'rgba(90, 180, 255, 0.18)',
            'border-color': 'rgba(130, 220, 255, 0.35)',
            'border-width': 1,
            'label': 'data(label)',
            'color': 'rgba(235, 247, 255, 0.92)',
            'font-size': 12,
            'text-outline-width': 2,
            'text-outline-color': 'rgba(10, 14, 22, 0.85)',
            'width': 46,
            'height': 46,
          }
        },
        {
          selector: '.nt-Product',
          style: {
            'width': 62,
            'height': 62,
            'background-color': 'rgba(90, 220, 255, 0.28)',
            'border-color': 'rgba(180, 255, 255, 0.55)',
          }
        },
        {
          selector: '.nt-SoftwareModule',
          style: {
            'shape': 'round-rectangle',
            'background-color': 'rgba(150, 120, 255, 0.20)',
            'border-color': 'rgba(190, 170, 255, 0.45)',
          }
        },
        {
          selector: '.nt-SensorOrEffector',
          style: {
            'background-color': 'rgba(255, 180, 80, 0.18)',
            'border-color': 'rgba(255, 210, 130, 0.45)',
          }
        },
        {
          selector: '.nt-DataArtifact',
          style: {
            'background-color': 'rgba(80, 255, 180, 0.14)',
            'border-color': 'rgba(140, 255, 220, 0.35)',
          }
        },
        {
          selector: '.nt-Document',
          style: {
            'background-color': 'rgba(220, 230, 255, 0.12)',
            'border-color': 'rgba(220, 230, 255, 0.28)',
          }
        },
        {
          selector: 'edge',
          style: {
            'curve-style': 'bezier',
            'width': 1,
            'line-color': 'rgba(130, 220, 255, 0.22)',
            'target-arrow-shape': 'triangle',
            'target-arrow-color': 'rgba(130, 220, 255, 0.22)',
            'label': 'data(label)',
            'font-size': 10,
            'color': 'rgba(210, 235, 255, 0.7)',
            'text-background-color': 'rgba(6, 8, 14, 0.7)',
            'text-background-opacity': 1,
            'text-background-padding': 2,
          }
        },
        {
          selector: '.et-TRIGGERS',
          style: {
            'line-color': 'rgba(255, 120, 80, 0.55)',
            'target-arrow-color': 'rgba(255, 120, 80, 0.55)',
          }
        },
        {
          selector: '.et-PROVIDES_DATA_TO',
          style: {
            'line-style': 'dashed',
            'line-dash-pattern': [6, 3],
          }
        },
        {
          selector: '.dim',
          style: {
            'opacity': 0.15,
            'text-opacity': 0.08,
          }
        },
        {
          selector: '.flash',
          style: {
            'border-width': 3,
            'border-color': 'rgba(255, 255, 255, 0.85)',
          }
        }
      ]
    })

    cy.on('tap', 'node', evt => {
      const data = evt.target.data()
      if (linkMode.value) {
        handleLinkPick(data.id)
        return
      }

      selectedEdge.value = null
      drawerType.value = 'node'
      selectedNode.value = data
      drawerVisible.value = true
      applyFocus(evt.target)
      loadNodeDetail(data.id)
    })

    cy.on('tap', 'edge', evt => {
      if (linkMode.value) return

      const data = evt.target.data()
      selectedNode.value = null
      selectedEdge.value = data
      drawerType.value = 'edge'
      drawerVisible.value = true

      // focus: 高亮边及两端节点
      const src = cy.getElementById(String(data.source))
      const tgt = cy.getElementById(String(data.target))
      cy.elements().addClass('dim')
      evt.target.removeClass('dim')
      src.removeClass('dim')
      tgt.removeClass('dim')
    })

    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        clearFocus()
      }
    })
  } else {
    cy.elements().remove()
    cy.add(elements)
    cy.layout({ name: 'cose', animate: true, fit: true, padding: 20 }).run()
  }
}

function clearFocus() {
  if (!cy) return
  cy.elements().removeClass('dim')
}

function applyFocus(nodeEle) {
  if (!cy || !nodeEle) return
  const neighborhood = nodeEle.closedNeighborhood()
  cy.elements().addClass('dim')
  neighborhood.removeClass('dim')
}

async function loadNodeDetail(nodeId) {
  try {
    const node = await getOptoNode(nodeId)
    selectedNode.value = { ...selectedNode.value, ...node }
    editorJson.value = node.content_json || { type: 'doc', content: [{ type: 'paragraph' }] }
  } catch (e) {
    editorJson.value = { type: 'doc', content: [{ type: 'paragraph' }] }
  }
}

async function saveNode() {
  if (!selectedNode.value?.id) return
  saving.value = true
  try {
    await updateOptoNode(selectedNode.value.id, { content_json: editorJson.value })
  } finally {
    saving.value = false
  }
}

async function handleUploadImage({ file, insert }) {
  if (!selectedNode.value?.id) return
  uploading.value = true
  try {
    const asset = await uploadOptoAsset({ nodeId: selectedNode.value.id, assetType: 'image', file })
    const url = `/api/database/opto-knowledge/asset/${asset.id}`
    insert(url)
  } finally {
    uploading.value = false
  }
}

function searchAndFocus() {
  if (!cy) return
  const q = (searchText.value || '').trim().toLowerCase()
  if (!q) return

  const match = cy.nodes().filter(n => String(n.data('label') || '').toLowerCase().includes(q)).first()
  if (!match || match.empty()) return

  applyFocus(match)
  cy.animate({
    center: { eles: match },
    zoom: 1.25,
    duration: 260,
  })

  match.addClass('flash')
  setTimeout(() => {
    match.removeClass('flash')
  }, 550)
}

onMounted(() => {
  loadAndRender()
})

watch(domain, () => {
  drawerVisible.value = false
  selectedNode.value = null
  selectedEdge.value = null
  drawerType.value = 'node'
  editorJson.value = { type: 'doc', content: [{ type: 'paragraph' }] }
  linkMode.value = false
  linkPick.value = { sourceId: null }
  loadAndRender()
})

onBeforeUnmount(() => {
  if (cy) {
    cy.destroy()
    cy = null
  }
})
</script>

<style scoped>
.ok-graph {
  width: 100vw;
  height: 100vh;
  background: radial-gradient(circle at 50% 40%, rgba(16, 20, 32, 1), rgba(6, 8, 14, 1));
  color: rgba(235, 247, 255, 0.92);
  display: flex;
  flex-direction: column;
}

.topbar {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 18px;
  border-bottom: 1px solid rgba(130, 220, 255, 0.12);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
}

.tools {
  display: flex;
  align-items: center;
  gap: 8px;
}

.search {
  width: 220px;
}

.title {
  font-weight: 600;
  letter-spacing: 1px;
}

.content {
  flex: 1;
  position: relative;
}

.cy {
  position: absolute;
  inset: 0;
}

.drawer {
  padding: 16px;
  color: rgba(235, 247, 255, 0.92);
  background: radial-gradient(circle at 30% 20%, rgba(16, 20, 32, 1), rgba(6, 8, 14, 1));
  height: 100%;
  display: flex;
  flex-direction: column;
}

.drawer-title {
  font-weight: 700;
  letter-spacing: 1px;
  margin-bottom: 14px;
}

.drawer-row {
  display: flex;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid rgba(130, 220, 255, 0.10);
}

.k {
  width: 72px;
  opacity: 0.75;
}

.v {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 12px;
  opacity: 0.9;
  word-break: break-all;
}

.editor {
  margin-top: 12px;
  flex: 1;
  min-height: 0;
}
</style>
