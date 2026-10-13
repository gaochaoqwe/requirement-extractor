import { computed } from 'vue'

function isDiffDebugEnabled() {
  try {
    return String(localStorage.getItem('codemapDiffDebug') || '') === '1'
  } catch {
    return false
  }
}

function funcDefKeyFromLine(line) {
  const s = String(line ?? '')
  if (!s) return ''
  // 与 toLineTokens 中 __funcdef__ 规则保持一致：函数名 + 归一化参数
  const m = s.match(/^[\s\w:<>&*~]+?\b([A-Za-z_~][A-Za-z0-9_:~]*)\s*\(([^)]*)\)\s*(?:const\s*)?(?:noexcept\s*)?(?:->\s*[^\{;]+)?\s*\{/)
  if (!m) return ''
  const fn = String(m[1] || '').trim()
  const args = normalizeFuncParamList(m[2])
  return `__funcdef__:${fn}(${args}){`
}

function pairUnmatchedFuncDefs(rows) {
  const del = new Map()
  const ins = new Map()

  for (let i = 0; i < rows.length; i++) {
    const r = rows[i]
    if (!r) continue

    // delete-only 行（左有右空）
    if (r.leftText && !r.rightText) {
      const k = funcDefKeyFromLine(r.leftText)
      if (k) {
        const arr = del.get(k) || []
        arr.push(i)
        del.set(k, arr)
      }
    }

    // insert-only 行（右有左空）
    if (r.rightText && !r.leftText) {
      const k = funcDefKeyFromLine(r.rightText)
      if (k) {
        const arr = ins.get(k) || []
        arr.push(i)
        ins.set(k, arr)
      }
    }
  }

  for (const [k, di] of del.entries()) {
    const ii = ins.get(k)
    if (!ii) continue
    // 只处理“唯一一对”，避免误配
    if (di.length !== 1 || ii.length !== 1) continue

    const dIdx = di[0]
    const iIdx = ii[0]
    if (dIdx === iIdx) continue

    const dr = rows[dIdx]
    const ir = rows[iIdx]
    if (!dr || !ir) continue

    // 合并：把 insert 的右侧信息搬到 delete 行
    dr.rightText = ir.rightText
    dr.rightLineNo = ir.rightLineNo

    // 如果两侧文本一致，标为 equal；否则保持 delete（作为配对行）
    dr.type = String(dr.leftText) === String(dr.rightText) ? 'equal' : 'delete'
    dr.diffKind = ''

    // 清空原 insert 行，避免出现第二个 main
    ir.leftText = ''
    ir.rightText = ''
    ir.leftLineNo = ''
    ir.rightLineNo = ''
    ir.type = 'equal'
    ir.diffKind = ''
  }
}

export function useLineDiff(oldText, newText) {
  const diffRows = computed(() => {
    const a = toLineTokens(oldText.value || '', 'old')
    const b = toLineTokens(newText.value || '', 'new')
    
    try {
      if (isDiffDebugEnabled()) {
        // 打印新版本第 24-26 行的 token（key 用于 diff 匹配，text 用于显示）
        const probe = b.slice(23, 26)
        if (probe.length > 0) {
          // eslint-disable-next-line no-console
          console.warn('[line-tokens] new lines 24~26', probe.map((t, i) => ({
            lineNo: 24 + i,
            key: String(t.key || '').slice(0, 80),
            text: String(t.text || '').slice(0, 80)
          })))
        }
      }
    } catch {}
    
    const ops = patienceDiff(a, b)

    let leftNo = 1
    let rightNo = 1
    const rows = []
    let idx = 0

    for (let opi = 0; opi < ops.length; opi++) {
      const op = ops[opi]
      if (!op || !op.type) continue

      // 关键：delete + insert 相邻时，视为“替换”，按行配对输出（两侧同一行），避免对齐错乱
      if (op.type === 'delete') {
        const next = ops[opi + 1]
        if (next && next.type === 'insert') {
          const delItems = Array.isArray(op.items) ? op.items : []
          const insItems = Array.isArray(next.items) ? next.items : []
          const max = Math.max(delItems.length, insItems.length)
          for (let i = 0; i < max; i++) {
            const hasDel = i < delItems.length
            const hasIns = i < insItems.length
            const dl = hasDel ? (delItems[i]?.text ?? '') : ''
            const ir = hasIns ? (insItems[i]?.text ?? '') : ''
            rows.push({
              key: `r:${idx++}`,
              type: (hasDel && hasIns) ? 'delete' : (hasDel ? 'delete' : 'insert'),
              diffKind: '',
              // 注意：空行的 text 可能是 ''，但它仍然是有效行，需要占用行号
              leftLineNo: hasDel ? leftNo++ : '',
              rightLineNo: hasIns ? rightNo++ : '',
              leftText: dl,
              rightText: ir
            })
          }
          opi++
          continue
        }

        const delItems = Array.isArray(op.items) ? op.items : []
        for (let i = 0; i < delItems.length; i++) {
          rows.push({
            key: `r:${idx++}`,
            type: 'delete',
            diffKind: '',
            leftLineNo: leftNo++,
            rightLineNo: '',
            leftText: delItems[i]?.text ?? '',
            rightText: ''
          })
        }
        continue
      }

      if (op.type === 'insert') {
        const insItems = Array.isArray(op.items) ? op.items : []
        for (let i = 0; i < insItems.length; i++) {
          rows.push({
            key: `r:${idx++}`,
            type: 'insert',
            diffKind: '',
            leftLineNo: '',
            rightLineNo: rightNo++,
            leftText: '',
            rightText: insItems[i]?.text ?? ''
          })
        }
        continue
      }

      if (op.type === 'equal') {
        const items = Array.isArray(op.items) ? op.items : []
        for (let i = 0; i < items.length; i++) {
          rows.push({
            key: `r:${idx++}`,
            type: 'equal',
            diffKind: '',
            leftLineNo: leftNo++,
            rightLineNo: rightNo++,
            leftText: items[i]?.text ?? '',
            rightText: items[i]?.text ?? ''
          })
        }
      }
    }

    // 关键：Patience 在“注释后代码”场景下可能因为前置插入/重复锚点不足而无法匹配函数声明行，
    // 导致同一个函数定义在 rows 中被拆成远距离的 delete-only + insert-only 两条，视觉上无法对齐。
    // 这里做一次后处理：对同一 funcdef key（函数名+参数类型）的一对 delete/insert 进行合并配对。
    // 这样可以保证 main/load 等函数声明行左右必在同一水平线。
    if (typeof pairUnmatchedFuncDefs === 'function') {
      pairUnmatchedFuncDefs(rows)
    } else {
      try {
        if (isDiffDebugEnabled()) {
          // eslint-disable-next-line no-console
          console.warn('[useLineDiff] pairUnmatchedFuncDefs is not available (HMR/cache?)')
        }
      } catch {}
    }

    // 给变更行打标签：code(红) / comment(蓝)
    // 1) delete+insert 相邻：如果去掉注释后的主体一致 -> comment
    // 2) 单侧 insert/delete：如果是纯注释行 -> comment，否则 code
    for (let i = 0; i < rows.length; i++) {
      const r = rows[i]
      if (!r || r.type === 'equal') continue

      // 配对行（leftText/rightText 同时存在）也按“delete”处理，这里用两侧文本做一次 comment-only 判断
      if (r.type === 'delete') {
        if (r.leftText && r.rightText) {
          const aBody = stripInlineComments(r.leftText)
          const bBody = stripInlineComments(r.rightText)
          const isCommentOnly = isEmptyCode(aBody) && isEmptyCode(bBody)
          const isOnlyCommentChanged = aBody === bBody && r.leftText !== r.rightText
          r.diffKind = (isCommentOnly || isOnlyCommentChanged) ? 'comment' : 'code'
          continue
        }
        r.diffKind = isPureCommentLine(r.leftText) ? 'comment' : 'code'
        continue
      }

      if (r.type === 'insert') {
        r.diffKind = isPureCommentLine(r.rightText) ? 'comment' : 'code'
      }
    }

    try {
      if (isDiffDebugEnabled()) {
        const probe = rows.filter((r) => {
          const rn = Number(r.rightLineNo)
          return Number.isFinite(rn) && rn >= 24 && rn <= 26
        })
        if (probe.length > 0) {
          // eslint-disable-next-line no-console
          console.warn('[diff-rows] rightLineNo 24~26', probe.map((r) => ({
            type: r.type,
            leftLineNo: r.leftLineNo,
            rightLineNo: r.rightLineNo,
            leftText: String(r.leftText || '').slice(0, 80),
            rightText: String(r.rightText || '').slice(0, 80)
          })))
        }

        const mainRows = rows.filter((r) => {
          const lt = String(r.leftText || '')
          const rt = String(r.rightText || '')
          return lt.includes('int main(') || rt.includes('int main(')
        })
        if (mainRows.length > 0) {
          // eslint-disable-next-line no-console
          console.warn('[diff-rows] main signature rows', mainRows.map((r) => ({
            type: r.type,
            leftLineNo: r.leftLineNo,
            rightLineNo: r.rightLineNo,
            leftText: String(r.leftText || '').slice(0, 120),
            rightText: String(r.rightText || '').slice(0, 120)
          })))
        }
      }
    } catch {}

    return rows
  })

  const changeRowIndices = computed(() => {
    const out = []
    for (let i = 0; i < diffRows.value.length; i++) {
      const t = diffRows.value[i].type
      if (t === 'insert' || t === 'delete') out.push(i)
    }
    return out
  })

  return { diffRows, changeRowIndices }
}

function stripInlineComments(line) {
  // 仅用于粗粒度“注释差异”判断：
  // - 去掉行内 //...
  // - 去掉行内 /* ... */（单行）
  // 不处理跨行块注释（先满足你说的 compare 视觉诉求）
  const s = String(line ?? '')
  const noBlock = s.replace(/\/\*.*?\*\//g, '')
  const noLine = noBlock.replace(/\/\/.*$/g, '')
  return noLine.trimEnd()
}

function isEmptyCode(s) {
  return !String(s ?? '').trim()
}

function isPureCommentLine(line) {
  const raw = String(line ?? '').trim()
  if (!raw) return false
  const body = stripInlineComments(raw)
  return isEmptyCode(body)
}

function normalizeFuncParamList(argText) {
  const raw = String(argText ?? '').trim()
  if (!raw) return ''
  if (raw === 'void') return 'void'

  const parts = raw.split(',')
  const out = []
  for (let p of parts) {
    p = String(p ?? '').trim()
    if (!p) continue
    // 去默认值
    const eq = p.indexOf('=')
    if (eq >= 0) p = p.slice(0, eq).trim()
    // 折叠空白
    p = p.replace(/[\t ]+/g, ' ').trim()

    // 去掉参数名（粗略启发式）：移除最后一个标识符；保留指针/引用/数组后缀
    // 例："const std::string& filename" -> "const std::string&"
    // 例："char* argv[]" -> "char*[]"
    const m = p.match(/^(.*?)(\b[A-Za-z_]\w*\b)(\s*(?:\[[^\]]*\]\s*)*)$/)
    if (m) {
      const before = String(m[1] || '').trim()
      const name = String(m[2] || '').trim()
      const suffix = String(m[3] || '').replace(/[\t ]+/g, '')

      // 如果 before 为空，说明这可能不是“类型+变量名”，不要错误删除
      if (before) {
        const lowered = name.toLowerCase()
        // 避免把类型关键字当作变量名删掉
        if (!['const', 'volatile', 'unsigned', 'signed', 'struct', 'class', 'enum', 'typename', 'auto'].includes(lowered)) {
          p = (before + suffix).trim()
        }
      }
    }

    out.push(p)
  }
  return out.join(',')
}

function toLineTokens(text, side = '') {
  // 用于 diff 的 key 做归一化（CRLF/行尾空白），但展示仍用原文 text
  const lines = String(text || '').split(/\r?\n/)

  let inBlock = false
  return lines.map((ln, idx) => {
    const raw = String(ln ?? '')
    let key = raw

    // 生成 diff key 时尽量去除注释影响，避免“注释后代码”插入大量注释导致锚点不足
    // 注意：这里仅影响 key（匹配），不影响 text（展示）
    let s = key
    if (inBlock) {
      const close = s.indexOf('*/')
      if (close >= 0) {
        s = s.slice(close + 2)
        inBlock = false
      } else {
        s = ''
      }
    }
    if (s) {
      while (true) {
        const open = s.indexOf('/*')
        if (open < 0) break
        const close = s.indexOf('*/', open + 2)
        if (close >= 0) {
          s = s.slice(0, open) + s.slice(close + 2)
          continue
        }
        s = s.slice(0, open)
        inBlock = true
        break
      }
      const lineIdx = s.indexOf('//')
      if (lineIdx >= 0) s = s.slice(0, lineIdx)
    }

    key = String(s ?? '').replace(/\s+$/g, '')
    
    // 空行：给唯一 key，避免错误配对
    if (!key.trim()) {
      key = `__blank_${idx}__`
      return { key, text: raw }
    }
    
    // 关键改进：对于 C++ 构造函数/成员函数签名，归一化初始化列表部分
    // 例如 "Image::Image(int w, int h) : width(w), height(h), metadata("") {"
    // 归一化为 "Image::Image(int w, int h) {"
    // 这样不同初始化列表的同一函数能被识别为"应配对的行"
    const funcSigMatch = key.match(/^(\s*)([A-Za-z_:][A-Za-z0-9_:]*\s*\([^)]*\))\s*:\s*[^\{]+(\{.*)$/)
    if (funcSigMatch) {
      // 保留缩进 + 函数签名 + 左花括号及之后
      key = funcSigMatch[1] + funcSigMatch[2] + ' ' + funcSigMatch[3]
    }

    // 新增：对“函数定义行”生成稳定 key（函数名 + 参数类型列表）
    // 目的：注释后代码经常改变参数名/空格/默认值，导致 main/load 等锚点无法配对从而整体错位。
    // 这里仅影响 key，不影响展示。
    const def = key.match(/^[\s\w:<>&*~]+?\b([A-Za-z_~][A-Za-z0-9_:~]*)\s*\(([^)]*)\)\s*(?:const\s*)?(?:noexcept\s*)?(?:->\s*[^\{;]+)?\s*\{/)
    if (def) {
      const fn = String(def[1] || '').trim()
      const args = normalizeFuncParamList(def[2])
      key = `__funcdef__:${fn}(${args}){`
    }

    // 进一步归一化空白字符：AI 注释后代码常会改变空格/缩进，导致本应配对的行 key 不一致
    // 这里仅影响 key（匹配），不影响 text（展示）
    key = String(key).replace(/[\t ]+/g, ' ').replace(/\s+$/g, '')

    try {
      if (isDiffDebugEnabled()) {
        if (raw.includes('main(') || raw.includes(' main(')) {
          // eslint-disable-next-line no-console
          console.warn('[line-key-probe]', {
            side,
            lineNo: idx + 1,
            inBlock,
            raw: String(raw).slice(0, 160),
            key: String(key).slice(0, 160)
          })
        }
      }
    } catch {}
    
    return { key, text: raw }
  })
}

function patienceDiff(aLines, bLines) {
  const N = aLines.length
  const M = bLines.length
  if (N === 0 && M === 0) return []
  if (N === 0) return [{ type: 'insert', items: bLines.slice() }]
  if (M === 0) return [{ type: 'delete', items: aLines.slice() }]

  const aCount = new Map()
  const bCount = new Map()
  for (const t of aLines) aCount.set(t.key, (aCount.get(t.key) || 0) + 1)
  for (const t of bLines) bCount.set(t.key, (bCount.get(t.key) || 0) + 1)

  const aIndex = new Map()
  const bIndex = new Map()
  for (let i = 0; i < aLines.length; i++) {
    const k = aLines[i].key
    if ((aCount.get(k) || 0) === 1 && (bCount.get(k) || 0) === 1) aIndex.set(k, i)
  }
  for (let j = 0; j < bLines.length; j++) {
    const k = bLines[j].key
    if ((aCount.get(k) || 0) === 1 && (bCount.get(k) || 0) === 1) bIndex.set(k, j)
  }

  const pairs = []
  for (const [k, ai] of aIndex.entries()) {
    const bi = bIndex.get(k)
    if (typeof bi === 'number') pairs.push({ ai, bi })
  }
  pairs.sort((p1, p2) => p1.ai - p2.ai)

  if (pairs.length === 0) return myersDiff(aLines, bLines)

  const anchors = longestIncreasingSubsequencePairs(pairs)
  if (!anchors.length) return myersDiff(aLines, bLines)

  let aStart = 0
  let bStart = 0
  let out = []
  for (const an of anchors) {
    out = mergeOps(out, myersDiff(aLines.slice(aStart, an.ai), bLines.slice(bStart, an.bi)))
    out = mergeOps(out, [{ type: 'equal', items: [aLines[an.ai]] }])
    aStart = an.ai + 1
    bStart = an.bi + 1
  }
  out = mergeOps(out, myersDiff(aLines.slice(aStart), bLines.slice(bStart)))
  return out
}

function mergeOps(baseOps, nextOps) {
  const out = baseOps ? baseOps.slice() : []
  for (const op of nextOps || []) {
    if (!op || !op.type) continue
    const items = Array.isArray(op.items) ? op.items : []
    if (!items.length) continue
    const last = out[out.length - 1]
    if (last && last.type === op.type) {
      last.items = (last.items || []).concat(items)
    } else {
      out.push({ type: op.type, items: items.slice() })
    }
  }
  return out
}

function longestIncreasingSubsequencePairs(pairs) {
  const n = pairs.length
  if (n === 0) return []

  const tails = []
  const tailsIdx = []
  const prev = new Array(n).fill(-1)

  for (let i = 0; i < n; i++) {
    const v = pairs[i].bi
    let l = 0
    let r = tails.length
    while (l < r) {
      const mid = (l + r) >> 1
      if (tails[mid] < v) l = mid + 1
      else r = mid
    }
    if (l > 0) prev[i] = tailsIdx[l - 1]
    if (l === tails.length) {
      tails.push(v)
      tailsIdx.push(i)
    } else {
      tails[l] = v
      tailsIdx[l] = i
    }
  }

  let k = tailsIdx[tailsIdx.length - 1]
  const out = []
  while (k >= 0) {
    out.push(pairs[k])
    k = prev[k]
  }
  out.reverse()
  return out
}

function myersDiff(aLines, bLines) {
  const N = aLines.length
  const M = bLines.length
  const max = N + M
  let v = new Map()
  v.set(1, 0)
  const trace = []

  for (let d = 0; d <= max; d++) {
    const vNext = new Map()
    for (let k = -d; k <= d; k += 2) {
      let x
      const vKPlus = v.get(k + 1)
      const vKMinus = v.get(k - 1)
      if (k === -d || (k !== d && (vKMinus ?? -1) < (vKPlus ?? -1))) {
        x = vKPlus ?? 0
      } else {
        x = (vKMinus ?? 0) + 1
      }
      let y = x - k
      while (x < N && y < M && aLines[x]?.key === bLines[y]?.key) {
        x++
        y++
      }
      vNext.set(k, x)
      if (x >= N && y >= M) {
        trace.push(vNext)
        return buildOps(trace, aLines, bLines)
      }
    }
    trace.push(vNext)
    v = vNext
  }

  return buildOps(trace, aLines, bLines)
}

function buildOps(trace, aLines, bLines) {
  const N = aLines.length
  const M = bLines.length
  let x = N
  let y = M
  const edits = []

  for (let d = trace.length - 1; d > 0; d--) {
    const v = trace[d]
    const k = x - y
    let prevK

    const vKPlus = v.get(k + 1)
    const vKMinus = v.get(k - 1)
    if (k === -d || (k !== d && (vKMinus ?? -1) < (vKPlus ?? -1))) {
      prevK = k + 1
    } else {
      prevK = k - 1
    }

    const vPrev = trace[d - 1]
    const prevX = vPrev.get(prevK) ?? 0
    const prevY = prevX - prevK

    while (x > prevX && y > prevY) {
      edits.push({ type: 'equal', a: aLines[x - 1] })
      x--
      y--
    }

    if (x === prevX) {
      edits.push({ type: 'insert', b: bLines[y - 1] })
      y--
    } else {
      edits.push({ type: 'delete', a: aLines[x - 1] })
      x--
    }
  }

  // 处理剩余前缀：仅当两侧行确实相等时才算 equal，否则应作为 insert/delete
  while (x > 0 && y > 0) {
    if (aLines[x - 1]?.key === bLines[y - 1]?.key) {
      edits.push({ type: 'equal', a: aLines[x - 1] })
      x--
      y--
      continue
    }
    break
  }
  while (x > 0) {
    edits.push({ type: 'delete', a: aLines[x - 1] })
    x--
  }
  while (y > 0) {
    edits.push({ type: 'insert', b: bLines[y - 1] })
    y--
  }

  edits.reverse()

  const ops = []
  for (const e of edits) {
    const last = ops[ops.length - 1]
    if (!last || last.type !== e.type) {
      ops.push({ type: e.type, items: [] })
    }
    const cur = ops[ops.length - 1]
    if (e.type === 'equal' || e.type === 'delete') cur.items.push(e.a)
    if (e.type === 'insert') cur.items.push(e.b)
  }
  return ops
}
