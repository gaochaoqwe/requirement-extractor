<template>
  <div class="aligned-tree">
    <div class="aligned-tree-head">
      <div class="col col-left">上一版本</div>
      <div class="col col-right">当前版本</div>
    </div>

    <div class="aligned-tree-body">
      <div
        v-for="row in rows"
        :key="row.node.id"
        class="row"
        :class="{ selected: row.node.id === selectedKey, file: row.node.type === 'file', func: row.node.type === 'function', dir: row.node.type === 'dir' }"
      >
        <div class="cell col col-left" @click="handleClick(row.node, 'old')">
          <div class="cell-inner" :style="{ paddingLeft: row.depth * 14 + 10 + 'px' }" @dblclick.stop="handleDblClick(row.node)">
            <template v-if="!isSideMissing(row.node, 'old')">
              <span v-if="hasChildren(row.node)" class="caret" :class="{ open: isExpanded(row.node.id) }">▶</span>
              <span class="icon" v-html="iconFor(row.node, 'old')"></span>
              <span class="name" :class="nameClass(row.node, 'old')" @dblclick.stop="handleDblClick(row.node)">{{ leftLabel(row.node) }}</span>
              <el-tag v-if="isMarked(row.node)" size="small" type="success" class="marked-tag">已标记</el-tag>
            </template>
          </div>
        </div>

        <div class="cell col col-right" @click="handleClick(row.node, 'new')">
          <div class="cell-inner" :style="{ paddingLeft: row.depth * 14 + 10 + 'px' }" @dblclick.stop="handleDblClick(row.node)">
            <template v-if="!isSideMissing(row.node, 'new')">
              <span v-if="hasChildren(row.node)" class="caret ghost">▶</span>
              <span class="icon" v-html="iconFor(row.node, 'new')"></span>
              <span class="name" :class="nameClass(row.node, 'new')" @dblclick.stop="handleDblClick(row.node)">{{ rightLabel(row.node) }}</span>
              <el-badge
                v-if="getProblemCount(row.node) > 0"
                :value="getProblemCount(row.node)"
                :type="getProblemBadgeType(row.node)"
                class="problem-badge"
                :class="`problem-badge-${getProblemBadgeType(row.node)}`"
              />
              <el-tag v-if="isMarked(row.node)" size="small" type="success" class="marked-tag">已标记</el-tag>
            </template>
          </div>
        </div>
      </div>

      <div v-if="rows.length === 0" class="empty">暂无数据</div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'

const props = defineProps({
  treeData: { type: Array, required: true },
  selectedKey: { type: String, default: '' },
  fileCountsById: { type: Object, default: null },
  problemCountsById: { type: Object, default: null },
  problemBadgeTypesById: { type: Object, default: null },
  markedLocations: { type: Object, default: null }
})

const emit = defineEmits(['select-pair', 'file-dblclick'])

const expandedKeys = ref(new Set())

const __debug = {
  mounted: false,
  iconLoggedKeys: new Set()
}

function isDebugEnabled() {
  try {
    return String(localStorage.getItem('codemapTreeDebug') || '') === '1'
  } catch {
    return false
  }
}

onMounted(() => {
  if (__debug.mounted) return
  __debug.mounted = true
  try {
    if (isDebugEnabled()) {
      console.warn('[AlignedCompareTree] mounted', {
        rows: Array.isArray(props.treeData) ? props.treeData.length : null,
        selectedKey: props.selectedKey
      })
    }
  } catch {}
})

const parentById = computed(() => {
  const map = new Map()
  const walk = (node, parentId) => {
    if (!node) return
    map.set(node.id, parentId || null)
    for (const c of node.children || []) walk(c, node.id)
  }
  for (const root of props.treeData || []) walk(root, null)
  return map
})

function hasChildren(node) {
  return !!(node && node.children && node.children.length > 0)
}

function isSideMissing(node, side) {
  if (!node) return true
  return side === 'old' ? !!node.old_missing : !!node.new_missing
}

function escapeHtml(raw) {
  return String(raw ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function iconColorFor(node, side) {
  const st = nodeStatus(node)
  if (st === 'unchanged') return { kind: 'solid', color: '#8b949e' }
  if (st === 'modified') {
    // modified：左侧灰，右侧红（与 compare 风格一致）
    if (side === 'new') return { kind: 'solid', color: '#f14c4c' }
    return { kind: 'solid', color: '#8b949e' }
  }
  // 新增/删除：只在存在的一侧显示蓝色
  if (st === 'new' || st === 'deleted') return { kind: 'solid', color: '#1f6feb' }
  return { kind: 'solid', color: '#8b949e' }
}

function guessLangLabelByPath(p) {
  const path = String(p || '').toLowerCase()
  const ext = path.includes('.') ? path.slice(path.lastIndexOf('.')) : ''
  if (ext === '.c') return 'C'
  if (ext === '.h') return 'H'
  if (ext === '.v' || ext === '.sv' || ext === '.vhd') return 'V'
  if (ext === '.cpp' || ext === '.cc' || ext === '.cxx' || ext === '.hpp' || ext === '.hxx') return 'C++'
  return ''
}

function filePathForNode(node, side) {
  if (!node) return ''
  if (node.type === 'file') return side === 'new' ? node.new_path : node.old_path
  if (node.type !== 'function') return ''
  const pid = parentById.value.get(node.id)
  if (!pid) return ''
  const fileNode = nodeById.value.get(pid)
  if (!fileNode) return ''
  return side === 'new' ? fileNode.new_path : fileNode.old_path
}

const nodeById = computed(() => {
  const map = new Map()
  const walk = (n) => {
    if (!n) return
    map.set(n.id, n)
    for (const c of n.children || []) walk(c)
  }
  for (const r of props.treeData || []) walk(r)
  return map
})

function svgFolder({ fillDef, gid }) {
  // 简化 folder 形状，便于小尺寸显示
  return `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="none">
  ${fillDef}
  <path d="M3 6.5C3 5.67 3.67 5 4.5 5h4.6c.45 0 .88.2 1.17.53l.86 1c.2.23.5.37.8.37H19.5C20.33 6.9 21 7.57 21 8.4v9.1c0 .83-.67 1.5-1.5 1.5h-15C3.67 19 3 18.33 3 17.5V6.5z" fill="url(#${gid})"/>
</svg>`.trim()
}

function svgFile({ fillDef, gid }) {
  return `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="none">
  ${fillDef}
  <path d="M7 3h7l3 3v15a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z" fill="url(#${gid})"/>
  <path d="M14 3v3h3" fill="none" stroke="rgba(255,255,255,0.35)" stroke-width="1"/>
</svg>`.trim()
}

function svgLangBadge({ fillDef, gid, text }) {
  const t = escapeHtml(text)
  const fontSize = t.length >= 3 ? 8.8 : 10.5
  const y = 15
  return `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="none">
  ${fillDef}
  <rect x="3" y="3" width="18" height="18" rx="4" fill="url(#${gid})"/>
  <text x="12" y="${y}" text-anchor="middle" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial" font-size="${fontSize}" font-weight="800" fill="rgba(13,17,23,0.92)">${t}</text>
</svg>`.trim()
}

function svgFunc({ fillDef, gid, text }) {
  const t = escapeHtml(text)
  const fontSize = t.length >= 3 ? 8.8 : 10.5
  const y = 15
  return `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="none">
  ${fillDef}
  <rect x="3" y="3" width="18" height="18" rx="4" fill="url(#${gid})"/>
  <text x="12" y="${y}" text-anchor="middle" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial" font-size="${fontSize}" font-weight="700" fill="rgba(13,17,23,0.92)">${t}</text>
</svg>`.trim()
}

function safeSvgId(raw) {
  return String(raw || '')
    .replace(/[^A-Za-z0-9_-]/g, '_')
    .slice(0, 64)
}

function buildFillDef(colorSpec, gid) {
  if (colorSpec.kind === 'gradient') {
    return `<defs><linearGradient id="${gid}" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="${colorSpec.from}"/><stop offset="100%" stop-color="${colorSpec.to}"/></linearGradient></defs>`
  }
  return `<defs><linearGradient id="${gid}" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="${colorSpec.color}"/><stop offset="100%" stop-color="${colorSpec.color}"/></linearGradient></defs>`
}

function iconFor(node, side) {
  if (!node) return ''
  const k = `${node.id}:${side}`
  if (isDebugEnabled() && !__debug.iconLoggedKeys.has(k)) {
    __debug.iconLoggedKeys.add(k)
    try {
      const colorSpec = iconColorFor(node, side)
      const st = nodeStatus(node)
      const bothPresent = !node.old_missing && !node.new_missing
      if (node.type !== 'function' || bothPresent || node.type === 'function') {
        console.log('[AlignedCompareTree] iconFor sample', {
          nodeId: node.id,
          type: node.type,
          side,
          change_type: node.change_type,
          status: st,
          colorSpec,
          label: node.label,
          old_missing: node.old_missing,
          new_missing: node.new_missing,
          old_path: node.old_path,
          new_path: node.new_path,
          old_label: node.old_label,
          new_label: node.new_label
        })
      }
      if (node.type === 'function' && bothPresent && (st === 'new' || st === 'deleted')) {
        console.warn('[AlignedCompareTree] suspicious function status', {
          nodeId: node.id,
          old_label: node.old_label,
          new_label: node.new_label,
          change_type: node.change_type,
          old_missing: node.old_missing,
          new_missing: node.new_missing
        })
      }
    } catch {}
  }
  const gid = `g_${safeSvgId(node.id)}_${side}`
  const fillDef = buildFillDef(iconColorFor(node, side), gid)
  if (node.type === 'dir') return svgFolder({ fillDef, gid })
  if (node.type === 'file') {
    const p = side === 'new' ? node.new_path : node.old_path
    const label = guessLangLabelByPath(p)
    if (label) return svgLangBadge({ fillDef, gid, text: label })
    return svgFile({ fillDef, gid })
  }
  const p = filePathForNode(node, side)
  const label = guessLangLabelByPath(p) || 'ƒ'
  return svgFunc({ fillDef, gid, text: label })
}

function getProblemCount(node) {
  if (!node) return 0
  const v = props.problemCountsById?.get?.(node.id)
  return typeof v === 'number' ? v : 0
}

function getProblemBadgeType(node) {
  if (!node) return 'danger'
  const t = props.problemBadgeTypesById?.get?.(node.id)
  return t || 'danger'
}

function isMarked(node) {
  if (!node) return false
  const loc = props.markedLocations
  if (!loc) return false
  const fnArr = Array.isArray(loc.functions) ? loc.functions : []
  const fileArr = Array.isArray(loc.files) ? loc.files : []

  if (node.type === 'function') {
    const name = String(node.new_label || node.old_label || '').trim()
    return fnArr.some((x) => String(x).trim() === name)
  }

  if (node.type === 'file') {
    const p = String(node.new_path || node.old_path || '').replace(/\\/g, '/').trim()
    if (!p) return false
    return fileArr.some((x) => String(x).replace(/\\/g, '/').trim() === p)
  }

  if (node.type === 'dir') {
    const stack = [].concat(node.children || [])
    while (stack.length) {
      const cur = stack.pop()
      if (!cur) continue
      if (isMarked(cur)) return true
      for (const c of cur.children || []) stack.push(c)
    }
  }
  return false
}

function isFileChanged(node) {
  if (!node || node.type !== 'file') return false
  const c = props.fileCountsById?.get(node.id)
  if (!c) return false
  return (c.new || 0) + (c.modified || 0) + (c.deleted || 0) > 0
}

function nodeStatus(node) {
  if (!node) return 'unchanged'

  // 1) dir/file：缺失优先
  if (node.type === 'dir' || node.type === 'file') {
    if (!!node.old_missing && !node.new_missing) return 'new'
    if (!node.old_missing && !!node.new_missing) return 'deleted'
  }

  // 2) function：缺失优先，其次用 change_type
  if (node.type === 'function') {
    // 兜底：即使后端 change_type 或 merge 逻辑异常，也要保证两侧都存在时不会渲染成 new/deleted
    if (!!node.old_missing && !node.new_missing) return 'new'
    if (!node.old_missing && !!node.new_missing) return 'deleted'
    if (node.change_type === 'modified') return 'modified'
    // 两侧都存在但 change_type 被标成 new/deleted，说明后端/合并逻辑异常；此时应视为 modified，而不是 unchanged
    if (node.change_type === 'new' || node.change_type === 'deleted') return 'modified'
    return 'unchanged'
  }

  // 3) file：根据统计判断 modified/unchanged
  if (node.type === 'file') {
    // 文件级 diff（后端提供）：用于头文件等“无函数变更但文件内容变了”的场景
    if (node.change_type === 'modified') return 'modified'
    return isFileChanged(node) ? 'modified' : 'unchanged'
  }

  // 4) dir：递归汇总子节点
  if (node.type === 'dir') {
    const stack = [...(node.children || [])]
    while (stack.length) {
      const cur = stack.pop()
      if (!cur) continue
      const st = nodeStatus(cur)
      if (st !== 'unchanged') return 'modified'
      for (const c of cur.children || []) stack.push(c)
    }
    return 'unchanged'
  }

  return 'unchanged'
}

function nameClass(node, side) {
  if (!node) return {}
  const missing = side === 'old' ? !!node.old_missing : !!node.new_missing
  const status = nodeStatus(node)
  return {
    missing,
    dir: node.type === 'dir',
    file: node.type === 'file',
    func: node.type === 'function',
    [`side-${side}`]: true,
    [`status-${status}`]: true
  }
}

function isExpanded(id) {
  return expandedKeys.value.has(id)
}

function setExpanded(id, expanded) {
  const next = new Set(expandedKeys.value)
  if (expanded) next.add(id)
  else next.delete(id)
  expandedKeys.value = next
}

function toggleExpanded(id) {
  setExpanded(id, !isExpanded(id))
}

function leftLabel(node) {
  if (!node) return ''
  if (node.type !== 'function') return String(node.label || '')
  return String(node.old_label || '')
}

function rightLabel(node) {
  if (!node) return ''
  if (node.type !== 'function') return String(node.label || '')
  return String(node.new_label || '')
}

function expandToKey(key) {
  if (!key) return
  const pMap = parentById.value
  const next = new Set(expandedKeys.value)
  let cur = pMap.get(key)
  while (cur) {
    next.add(cur)
    cur = pMap.get(cur)
  }
  expandedKeys.value = next
}

watch(
  () => props.selectedKey,
  (k) => {
    if (k) expandToKey(k)
  },
  { immediate: true }
)

watch(
  () => props.treeData,
  () => {
    if (props.selectedKey) expandToKey(props.selectedKey)
  },
  { deep: true }
)

watch(
  () => props.treeData,
  (tree) => {
    if (!isDebugEnabled()) return
    try {
      const roots = Array.isArray(tree) ? tree : []
      const fns = []
      const walk = (n) => {
        if (!n) return
        if (n.type === 'function') fns.push(n)
        for (const c of n.children || []) walk(c)
      }
      for (const r of roots) walk(r)

      console.warn('[AlignedCompareTree] treeData functions summary', {
        functionCount: fns.length,
        sample: fns.slice(0, 30).map((n) => ({
          id: n.id,
          old_label: n.old_label,
          new_label: n.new_label,
          change_type: n.change_type,
          old_missing: n.old_missing,
          new_missing: n.new_missing,
          status: nodeStatus(n)
        }))
      })
    } catch {}
  },
  { deep: false }
)

const rows = computed(() => {
  const out = []
  const dfs = (node, depth) => {
    if (!node) return
    out.push({ node, depth })
    if (hasChildren(node) && isExpanded(node.id)) {
      for (const c of node.children || []) dfs(c, depth + 1)
    }
  }
  for (const r of props.treeData || []) dfs(r, 0)
  return out
})

function handleClick(node, side) {
  if (!node) return
  if (isSideMissing(node, side)) return
  if (node.type === 'dir' || node.type === 'file') {
    toggleExpanded(node.id)
    return
  }
  if (node.type === 'function') {
    const pid = side === 'old' ? node.old_pair_id : node.new_pair_id
    if (pid) emit('select-pair', pid)
  }
}

function handleDblClick(node) {
  if (!node) return
  if (node.type !== 'file') return
  // 缺失侧不触发（此处按“任一侧存在即可打开tab”处理）
  if (node.old_missing && node.new_missing) return
  emit('file-dblclick', node.id)
}
</script>

<style scoped>
.aligned-tree {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #252526;
}

 .marked-tag {
   margin-left: 6px;
   transform: translateY(-1px);
 }

 .problem-badge-success :deep(.el-badge__content) {
   background-color: var(--el-color-success);
 }

 .problem-badge-info :deep(.el-badge__content) {
   background-color: var(--el-color-info);
 }

 .problem-badge-primary :deep(.el-badge__content) {
   background-color: var(--el-color-primary);
 }

 .problem-badge-danger :deep(.el-badge__content) {
   background-color: var(--el-color-danger);
 }

.aligned-tree-head {
  display: grid;
  grid-template-columns: 1fr 1fr;
  background: #1e1e1e;
  border-bottom: 1px solid #3c3c3c;
}

.col {
  padding: 8px 10px;
  font-size: 12px;
  font-weight: 600;
  color: #d4d4d4;
}

.col-left {
  border-right: 1px solid #3c3c3c;
}

.aligned-tree-body {
  flex: 1;
  overflow: auto;
  background: #252526;
}

.row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  border-bottom: 1px solid #2d2d2d;
}

.row:nth-child(even) {
  background: #252526;
}

.row:nth-child(odd) {
  background: #2a2a2a;
}

.row:hover {
  background: #2a2d2e;
}

.row.selected {
  background: rgba(0, 122, 204, 0.20);
  box-shadow: inset 4px 0 0 #007acc;
}

.cell {
  min-width: 0;
  border-right: 1px solid #3c3c3c;
}

.cell.col-left {
  background: rgba(0, 0, 0, 0.08);
}

.cell.col-right {
  background: rgba(0, 122, 204, 0.08);
}

.row .cell:last-child {
  border-right: none;
}

.cell-inner {
  height: 28px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding-right: 10px;
  cursor: pointer;
  user-select: none;
}

.caret {
  width: 14px;
  display: inline-flex;
  justify-content: center;
  color: #858585;
  font-size: 10px;
  transform: translateY(-1px);
}

.caret.open {
  transform: translateY(-1px) rotate(90deg);
}

.caret.ghost {
  opacity: 0;
}

.icon {
  width: 16px;
  text-align: center;
  color: #c5c5c5;
}

.name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
  color: #d4d4d4;
}

.problem-badge {
  margin-left: 6px;
}

.problem-badge :deep(.el-badge__content) {
  border: none;
}

.name.missing {
  color: #6a6a6a;
}

.name.dir {
  font-weight: 600;
}

/* 颜色规则（左旧右新） */
/* 新增：只在右侧显示为蓝色 */
.name.side-new.status-new {
  color: #3794ff;
}

/* 删除：只在左侧显示为蓝色 */
.name.side-old.status-deleted {
  color: #3794ff;
}

/* 修改：左灰右红 */
.name.side-new.status-modified {
  color: #f14c4c;
}

.name.side-old.status-modified {
  color: #d4d4d4;
}

/* 不变：左右都是灰 */
.name.side-old.status-unchanged,
.name.side-new.status-unchanged {
  color: #d4d4d4;
}

.missing-text {
  color: #a8abb2;
  margin-left: 6px;
}

.empty {
  padding: 14px;
  color: #909399;
  font-size: 12px;
}
</style>
