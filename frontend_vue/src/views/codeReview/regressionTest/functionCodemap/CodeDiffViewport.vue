<template>
  <div class="diff-viewport">
    <div
      v-for="(row, idx) in rows"
      :key="row.key"
      class="diff-row"
      :class="[row.type, row.diffKind, { blank: !(row.leftText || '').trim() && !(row.rightText || '').trim(), focused: idx === focusedRowIndex, highlighted: idx === highlightRowIndex }]"
    >
      <div class="diff-lineno">{{ side === 'l' ? (row.leftLineNo || '') : (row.rightLineNo || '') }}</div>
      <div class="diff-code" v-html="highlight(side === 'l' ? row.leftText : row.rightText)"></div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  rows: { type: Array, required: true },
  focusedRowIndex: { type: Number, default: -1 },
  side: { type: String, default: 'l' },
  highlightRowIndex: { type: Number, default: -1 }
})

function escapeHtml(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

let __didDebugLog = false

function highlight(text) {
  const raw = String(text ?? '')
  if (!raw) return ''

  // 先整体转义，避免 XSS
  let s = escapeHtml(raw)

  // 关键字（偏 C/C++/JS 通用）
  const kw = [
    'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'break', 'continue', 'return',
    'try', 'catch', 'throw', 'new', 'delete', 'class', 'struct', 'public', 'private', 'protected',
    'static', 'const', 'constexpr', 'volatile', 'virtual', 'override', 'template', 'typename',
    'using', 'namespace', 'typedef', 'enum', 'union', 'nullptr', 'this',
    'int', 'long', 'short', 'float', 'double', 'char', 'bool', 'void', 'unsigned', 'signed',
    'auto'
  ]
  const kwRe = new RegExp(`\\b(${kw.join('|')})\\b`, 'g')
  s = s.replace(kwRe, '<span class="tok-keyword">$1</span>')

  // 预处理/指令（放在关键字之后，避免破坏标签）
  s = s.replace(/^(\s*#\s*\w+)(.*)$/g, (_m, a, b) => {
    return `<span class="tok-preproc">${a}</span>${b}`
  })

  // 字符串（基于转义后的 &quot; 与 &#39;）
  s = s.replace(/(&quot;.*?&quot;)/g, '<span class="tok-string">$1</span>')
  s = s.replace(/(&#39;.*?&#39;)/g, '<span class="tok-string">$1</span>')

  // 行注释（最后包一层，保证注释整体灰）
  s = s.replace(/(\/\/.*)$/g, '<span class="tok-comment">$1</span>')

  // 数字（放在最后，避免后续正则误命中 <span class="..."> 里的 class 属性导致 HTML 被破坏）
  s = s.replace(/\b(\d+(?:\.\d+)?)\b/g, '<span class="tok-number">$1</span>')

  // 函数名（放在最后：避免关键字/字符串等替换对其造成干扰；仅对“标识符 + (”着色）
  // 注：这里不会命中 <span ...> 的属性文本，因为属性名后不会跟 '('。
  s = s.replace(/\b([A-Za-z_][A-Za-z0-9_]*)\b(?=\s*\()/g, '<span class="tok-func">$1</span>')

  if (!__didDebugLog) {
    __didDebugLog = true
    try {
      // 只打印一次，避免刷屏
      console.debug('[DiffViewport] highlight sample raw=', raw.slice(0, 120))
      console.debug('[DiffViewport] highlight sample html=', s.slice(0, 200))
    } catch {}
  }

  return s
}
</script>

<style scoped>
.diff-viewport {
  padding: 8px 0;
}

.diff-row {
  display: flex;
  gap: 0;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 20px;
  height: 20px;
  align-items: stretch;
}

.diff-row:hover {
  filter: brightness(1.08);
}

.diff-row.equal {
  background: #0d1117;
}

.diff-row.insert {
  background: rgba(46, 204, 113, 0.10);
}

.diff-row.delete {
  background: rgba(231, 76, 60, 0.10);
}

/* 空白行不应显示为变更：即使 row.type 是 insert/delete，也强制中性背景 */
.diff-row.blank {
  background: #0d1117;
}

.diff-row.blank.insert,
.diff-row.blank.delete,
.diff-row.blank.code.insert,
.diff-row.blank.code.delete,
.diff-row.blank.comment.insert,
.diff-row.blank.comment.delete {
  background: #0d1117;
}

/* 覆盖：compare 风格
 * - code 差异：红色
 * - comment 差异：蓝色
 */
.diff-row.code.insert,
.diff-row.code.delete {
  background: rgba(231, 76, 60, 0.18);
}

.diff-row.comment.insert,
.diff-row.comment.delete {
  background: rgba(64, 158, 255, 0.18);
}

.diff-row.focused {
  outline: 2px solid rgba(64, 158, 255, 0.9);
  outline-offset: -2px;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.18);
}

.diff-row.highlighted {
  animation: diff-row-highlight 3s ease-in-out;
}

@keyframes diff-row-highlight {
  0% {
    box-shadow: inset 0 0 0 0 rgba(231, 76, 60, 0);
    background: rgba(231, 76, 60, 0);
  }
  20% {
    box-shadow: inset 0 0 0 4px rgba(231, 76, 60, 0.95);
    background: rgba(231, 76, 60, 0.12);
  }
  60% {
    box-shadow: inset 0 0 0 4px rgba(231, 76, 60, 0.45);
    background: rgba(231, 76, 60, 0.06);
  }
  100% {
    box-shadow: inset 0 0 0 0 rgba(231, 76, 60, 0);
    background: rgba(231, 76, 60, 0);
  }
}

.diff-lineno {
  width: 36px;
  flex: 0 0 36px;
  text-align: right;
  padding: 0 6px 0 0;
  color: #8b949e;
  user-select: none;
  background: rgba(255, 255, 255, 0.03);
  border-right: 1px solid rgba(255, 255, 255, 0.06);
}

.diff-code {
  flex: 1;
  min-width: 0;
  white-space: pre;
  color: #c9d1d9;
  padding: 0 10px;
  overflow: hidden;
  text-overflow: clip;
}

:deep(.tok-comment) {
  color: #7d8590;
}

:deep(.tok-string) {
  color: #a5d6ff;
}

:deep(.tok-number) {
  color: #e3b341;
}

:deep(.tok-keyword) {
  color: #ff7b72;
}

:deep(.tok-preproc) {
  color: #d2a8ff;
}

:deep(.tok-func) {
  color: #79c0ff;
}
</style>
