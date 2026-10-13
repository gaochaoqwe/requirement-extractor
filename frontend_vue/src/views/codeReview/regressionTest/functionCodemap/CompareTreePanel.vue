<template>
  <div class="tree-panel" :class="{ collapsed: !treesVisible }" :style="{ width: treesVisible ? treePanelWidth + 'px' : collapsedTreeWidth + 'px' }">
    <div class="tree-panel-header">
      <div class="tree-panel-title">目录树对比</div>
      <div class="tree-panel-actions">
        <el-button size="small" @click="$emit('toggle-trees')" type="primary" plain>
          {{ treesVisible ? '隐藏目录树' : '展开目录树' }}
        </el-button>
      </div>
    </div>

    <div v-show="treesVisible" class="tree-panel-body">
      <el-tabs v-model="activeTab" type="card" class="tree-tabs" @tab-remove="closeTab">
        <el-tab-pane name="dir" label="目录树" :closable="false">
          <AlignedCompareTree
            :tree-data="dirOnlyTreeData"
            :selected-key="selectedKey"
            :file-counts-by-id="fileCountsById"
            :problem-counts-by-id="problemCountsById"
            :problem-badge-types-by-id="problemBadgeTypesById"
            :marked-locations="markedLocations"
            @select-pair="(pid) => emit('select-pair', pid)"
            @file-dblclick="openFileTab"
          />
        </el-tab-pane>

        <el-tab-pane
          v-for="t in fileTabs"
          :key="t.name"
          :name="t.name"
          :label="t.label"
          closable
        >
          <AlignedCompareTree
            :tree-data="t.funcTree"
            :selected-key="selectedKey"
            :file-counts-by-id="null"
            :problem-counts-by-id="problemCountsById"
            :problem-badge-types-by-id="problemBadgeTypesById"
            :marked-locations="markedLocations"
            @select-pair="(pid) => emit('select-pair', pid)"
          />
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

import AlignedCompareTree from './AlignedCompareTree.vue'

const props = defineProps({
  treesVisible: { type: Boolean, required: true },
  treePanelWidth: { type: Number, required: true },
  collapsedTreeWidth: { type: Number, required: true },
  oldTreeData: { type: Array, required: true },
  newTreeData: { type: Array, required: true },
  selectedOldTreeKey: { type: String, default: '' },
  selectedNewTreeKey: { type: String, default: '' },
  problemCountsById: { type: Object, default: null },
  problemBadgeTypesById: { type: Object, default: null },
  markedLocations: { type: Object, default: null },
  functionStartLineByKey: { type: Object, default: null }
})

const emit = defineEmits(['toggle-trees', 'select-pair', 'select-file'])

const activeTab = ref('dir')
const openedFileIds = ref([])

const selectedKey = computed(() => props.selectedNewTreeKey || props.selectedOldTreeKey || '')

const baseTreeData = computed(() => (props.oldTreeData && props.oldTreeData.length > 0 ? props.oldTreeData : props.newTreeData) || [])

function stripFunctions(nodes) {
  const walk = (arr) => {
    const out = []
    for (const n of arr || []) {
      if (!n) continue
      if (n.type === 'function') continue
      if (n.type === 'file') {
        out.push({ ...n, children: [] })
        continue
      }
      // dir
      out.push({ ...n, children: walk(n.children || []) })
    }
    return out
  }
  return walk(nodes)
}

const dirOnlyTreeData = computed(() => stripFunctions(baseTreeData.value))

const nodeById = computed(() => {
  const map = new Map()
  const walk = (n) => {
    if (!n) return
    map.set(n.id, n)
    for (const c of n.children || []) walk(c)
  }
  for (const r of baseTreeData.value || []) walk(r)
  return map
})

function openFileTab(fileId) {
  if (!fileId) return
  if (!String(fileId).startsWith('file:')) return
  const ids = openedFileIds.value.slice()
  if (!ids.includes(fileId)) ids.push(fileId)
  openedFileIds.value = ids
  activeTab.value = fileId

  emit('select-file', fileId)
}

function closeTab(tabName) {
  const ids = openedFileIds.value.filter((x) => x !== tabName)
  openedFileIds.value = ids
  if (activeTab.value === tabName) activeTab.value = 'dir'
}

const fileTabs = computed(() => {
  const out = []

  const normPath = (p) => String(p || '').replace(/\\/g, '/').trim()
  const normName = (s) => String(s || '').trim()
  const pathVariants = (raw) => {
    const p = normPath(raw)
    if (!p) return []
    const seg = p.split('/').filter(Boolean)
    if (seg.length <= 1) return [seg.join('/')]
    const stripped = seg.slice(1).join('/')
    if (stripped && stripped !== p) return [p, stripped]
    return [p]
  }

  const getStartLine = (filePath, fnName) => {
    const fpList = pathVariants(filePath)
    const name0 = normName(fnName)
    if (!name0 || !fpList.length) return null

    const store = props.functionStartLineByKey
    const resolved = store && typeof store === 'object' && 'value' in store ? store.value : store

    const nameVariants = (() => {
      const out = [name0]
      // 兼容：后端可能只存了未带命名空间的函数名（例如 brightness）
      const short = name0.includes('::') ? name0.split('::').pop() : ''
      if (short && short !== name0) out.push(short)
      return out
    })()

    // 生成更多 filePath variants：不仅剥离第一级，还尝试所有后缀（确保能匹配到 core/image.cpp）
    const fpSuffixes = (() => {
      const out = new Set()
      for (const fp of fpList) {
        const seg = String(fp || '').split('/').filter(Boolean)
        for (let i = 0; i < seg.length; i++) {
          const suf = seg.slice(i).join('/')
          if (suf) out.add(suf)
        }
      }
      return Array.from(out)
    })()

    // 1) 先走快速路径：精确 key lookup
    for (const fp of fpSuffixes) {
      for (const name of nameVariants) {
        const key = `${fp}::${name}`
        let v = null
        // 兼容：Map / Proxy(Map)
        if (resolved?.get) v = resolved.get(key)
        // 兼容：普通对象（某些场景下可能被序列化）
        else if (resolved && typeof resolved === 'object') v = resolved[key]
        if (typeof v === 'number' && Number.isFinite(v)) return v
      }
    }

    // 2) 慢路径：Map 里扫描（解决 key 的 path 前缀形态不一致的问题）
    // 规则：
    // - Map 的 key 如果形如 "<somePath>::<someName>", 解析出 path/name
    // - 若 keyPath 以 fpSuffix 结尾（endsWith），且 name 匹配（全名或短名），则认为命中
    if (resolved?.entries) {
      try {
        let best = null
        for (const [k, v] of resolved.entries()) {
          if (typeof v !== 'number' || !Number.isFinite(v)) continue
          const ks = String(k || '')
          const sep = ks.indexOf('::')
          if (sep <= 0) continue
          const kp = normPath(ks.slice(0, sep))
          const kn = normName(ks.slice(sep + 2))
          if (!kp || !kn) continue

          // name 匹配：全名/短名任一相等
          let nameOk = false
          for (const nv of nameVariants) {
            if (kn === nv) {
              nameOk = true
              break
            }
            const knShort = kn.includes('::') ? kn.split('::').pop() : ''
            if (knShort && knShort === nv) {
              nameOk = true
              break
            }
          }
          if (!nameOk) continue

          // path 匹配：keyPath 以 fpSuffix 结尾
          let pathOk = false
          for (const fp of fpSuffixes) {
            if (kp === fp || kp.endsWith(`/${fp}`) || kp.endsWith(fp)) {
              pathOk = true
              break
            }
          }
          if (!pathOk) continue

          if (best == null || v < best) best = v
        }
        if (best != null) return best
      } catch {}
    }

    return null
  }

  const sortFuncNodes = (fileNode, arr) => {
    const fp = normPath(fileNode?.new_path || fileNode?.old_path || '')
    const list = (arr || []).slice()

    list.sort((a, b) => {
      const na = normName(a?.new_label || a?.old_label || '')
      const nb = normName(b?.new_label || b?.old_label || '')

      // 关键：优先使用 compareTreeBuilder 在节点上携带的 start_line（最权威、且不依赖外部 Map）
      const saNode = Number(a?.new_start_line ?? a?.old_start_line)
      const sbNode = Number(b?.new_start_line ?? b?.old_start_line)
      const sa = Number.isFinite(saNode) ? saNode : getStartLine(fp, na)
      const sb = Number.isFinite(sbNode) ? sbNode : getStartLine(fp, nb)
      if (typeof sa === 'number' && typeof sb === 'number') return sa - sb
      if (typeof sa === 'number') return -1
      if (typeof sb === 'number') return 1
      return na.localeCompare(nb)
    })

    return list
  }

  for (const fileId of openedFileIds.value) {
    const node = nodeById.value.get(fileId)
    const label = node ? String(node.label || fileId.replace(/^file:/, '')) : String(fileId).replace(/^file:/, '')
    const funcTreeRaw = node ? (node.children || []) : []
    const funcTree = node ? sortFuncNodes(node, funcTreeRaw) : funcTreeRaw
    out.push({ name: fileId, label, fileId, funcTree })
  }
  return out
})

const fileCountsById = computed(() => {
  const map = new Map()
  const walk = (n) => {
    if (!n) return
    if (n.type === 'file') {
      const counts = { new: 0, modified: 0, deleted: 0 }
      for (const c of n.children || []) {
        // 忽略“空函数名”的占位节点（可能来自解析异常），避免误把文件判定为 modified
        if (c?.type === 'function') {
          const ol = String(c.old_label || '').trim()
          const nl = String(c.new_label || '').trim()
          if (!ol && !nl) continue

          // 以 missing 优先推导函数真实状态，避免两侧都存在却被标成 new/deleted 进而把文件算成变更
          const oldMissing = !!c.old_missing
          const newMissing = !!c.new_missing
          if (oldMissing && !newMissing) {
            counts.new++
            continue
          }
          if (!oldMissing && newMissing) {
            counts.deleted++
            continue
          }
          if (c.change_type === 'modified') {
            counts.modified++
          }
          continue
        }

        if (c.change_type === 'new') counts.new++
        else if (c.change_type === 'modified') counts.modified++
        else if (c.change_type === 'deleted') counts.deleted++
      }
      map.set(n.id, counts)
      for (const c of n.children || []) walk(c)
      return
    }
    for (const c of n.children || []) walk(c)
  }

  for (const root of baseTreeData.value || []) {
    walk(root)
  }
  return map
})
</script>

<style scoped>
.tree-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 0;
  margin: 0;
  box-sizing: border-box;
  min-width: 44px;
  max-width: 900px;
  background: #252526;
  backdrop-filter: none;
  border-right: 1px solid #3c3c3c;
  box-shadow: none;
}

.tree-panel-header {
  padding: 10px 12px;
  border-bottom: 1px solid #3c3c3c;
  background: #252526;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.tree-panel-title {
  font-size: 14px;
  font-weight: 600;
  color: #d4d4d4;
  white-space: nowrap;
}

.tree-search {
  padding: 8px 10px;
  border-bottom: 1px solid #eef1f5;
  background: rgba(255, 255, 255, 0.9);
}

.tree-filters {
  margin-top: 8px;
  display: flex;
  justify-content: space-between;
}

.tree-panel-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.tree-tabs {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.tree-tabs :deep(.el-tabs__content) {
  flex: 1;
  overflow: hidden;
}

.tree-tabs :deep(.el-tabs__header) {
  margin: 0;
  background: #1e1e1e;
  border-bottom: 1px solid #3c3c3c;
}

.tree-tabs :deep(.el-tabs__nav-wrap) {
  padding: 6px 8px;
}

.tree-tabs :deep(.el-tabs__nav) {
  border: none;
}

.tree-tabs :deep(.el-tabs__item) {
  height: 28px;
  line-height: 28px;
  border: 1px solid #3c3c3c;
  border-radius: 6px;
  margin-right: 8px;
  padding: 0 12px;
  background: #2d2d2d;
  color: #c5c5c5;
  transition: background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease;
}

.tree-tabs :deep(.el-tabs__item:last-child) {
  margin-right: 0;
}

.tree-tabs :deep(.el-tabs__item:hover) {
  background: #3a3d41;
  border-color: #4b4b4b;
  color: #ffffff;
}

.tree-tabs :deep(.el-tabs__item.is-active) {
  background: #252526;
  border-color: #007acc;
  color: #ffffff;
  font-weight: 700;
}

.tree-tabs :deep(.el-tabs__nav-wrap::after) {
  background-color: transparent;
}

.tree-tabs :deep(.el-tabs__active-bar) {
  background-color: transparent;
}

.tree-tabs :deep(.el-tabs__item .el-icon) {
  color: #c5c5c5;
}

.tree-tabs :deep(.el-tabs__item:hover .el-icon) {
  color: #ffffff;
}

.tree-tabs :deep(.el-tabs__item.is-active .el-icon) {
  color: #ffffff;
}

.tree-tabs :deep(.el-tabs__item .el-icon-close) {
  margin-left: 8px;
  border-radius: 4px;
  width: 16px;
  height: 16px;
}

.tree-tabs :deep(.el-tabs__item .el-icon-close:hover) {
  background: rgba(255, 255, 255, 0.12);
}

.tree-tabs :deep(.el-tab-pane) {
  height: 100%;
}

.tree-panel.collapsed .tree-panel-title {
  display: none;
}

</style>
