import * as XLSX from 'xlsx'
import ExcelJS from 'exceljs'

export const DEFAULT_MIN_ROWS = 100
export const DEFAULT_MAX_ROWS = 10000
export const DEFAULT_MAX_COLS = 200

export const createEmptySheetData = (name = 'Sheet1') => ({
  id: name,
  name,
  cols: {},
  rows: { 0: { cells: { 0: { text: '' } } } },
  merges: [],
  styles: [],
})

export const normalizeSheetData = (sheet, fallbackName = 'Sheet1') => {
  if (!sheet || typeof sheet !== 'object') return createEmptySheetData(fallbackName)
  const name = sheet.name || fallbackName
  const id = sheet.id || name
  const rows = sheet.rows && typeof sheet.rows === 'object' ? sheet.rows : {}
  const cols = sheet.cols && typeof sheet.cols === 'object' ? sheet.cols : {}
  return {
    ...sheet,
    id,
    name,
    rows,
    cols,
    merges: Array.isArray(sheet.merges) ? sheet.merges : [],
    styles: Array.isArray(sheet.styles) ? sheet.styles : [],
  }
}

export const aoaToSheetData = (aoa, name = 'Sheet1', minRows = DEFAULT_MIN_ROWS) => {
  const rows = {}
  aoa.forEach((row, rIdx) => {
    const cells = {}
    row.forEach((cell, cIdx) => {
      if (cell === null || cell === undefined || cell === '') return
      cells[cIdx] = { text: String(cell) }
    })
    rows[rIdx] = { cells }
  })
  for (let r = aoa.length; r < minRows; r++) {
    if (!rows[r]) rows[r] = { cells: {} }
  }
  return { id: name, name, rows, cols: {}, merges: [], styles: [] }
}

// Standard Office theme palette (index 0-11)
const OFFICE_THEME_COLORS = [
  '#FFFFFF', '#000000', '#E7E6E6', '#44546A',
  '#4472C4', '#ED7D31', '#A9D18E', '#FFC000',
  '#5B9BD5', '#70AD47', '#0070C0', '#954F72',
]

// Excel legacy indexed color palette (64 standard colors, indices 0-63)
// Reference: ECMA-376 Part 1, Section 18.8.27
const EXCEL_INDEXED_COLORS = [
  '#000000', '#FFFFFF', '#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF', // 0-7
  '#000000', '#FFFFFF', '#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF', // 8-15
  '#800000', '#008000', '#000080', '#808000', '#800080', '#008080', '#C0C0C0', '#808080', // 16-23
  '#9999FF', '#993366', '#FFFFCC', '#CCFFFF', '#660066', '#FF8080', '#0066CC', '#CCCCFF', // 24-31
  '#000080', '#FF00FF', '#FFFF00', '#00FFFF', '#800080', '#800000', '#008080', '#0000FF', // 32-39
  '#00CCFF', '#CCFFFF', '#CCFFCC', '#FFFF99', '#99CCFF', '#FF99CC', '#CC99FF', '#FFCC99', // 40-47
  '#3366FF', '#33CCCC', '#99CC00', '#FFCC00', '#FF9900', '#FF6600', '#666699', '#969696', // 48-55
  '#003366', '#339966', '#003300', '#333300', '#993300', '#993366', '#333399', '#333333', // 56-63
]

const applyTint = (hex, tint) => {
  if (!tint || tint === 0) return hex
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  const clamp = v => Math.max(0, Math.min(255, v))
  let nr, ng, nb
  if (tint > 0) {
    nr = clamp(Math.round(r + (255 - r) * tint))
    ng = clamp(Math.round(g + (255 - g) * tint))
    nb = clamp(Math.round(b + (255 - b) * tint))
  } else {
    nr = clamp(Math.round(r * (1 + tint)))
    ng = clamp(Math.round(g * (1 + tint)))
    nb = clamp(Math.round(b * (1 + tint)))
  }
  return `#${nr.toString(16).padStart(2, '0')}${ng.toString(16).padStart(2, '0')}${nb.toString(16).padStart(2, '0')}`
}

const ejsColorToHex = (color) => {
  if (!color) return null
  // ARGB string: first 2 hex chars are alpha, last 6 are RRGGBB
  if (color.argb) {
    const argb = String(color.argb)
    if (argb.length === 8) return `#${argb.slice(2)}`
    if (argb.length === 6) return `#${argb}`
  }
  // Theme color with optional tint
  if (typeof color.theme === 'number') {
    const base = OFFICE_THEME_COLORS[color.theme]
    if (!base) return null
    return applyTint(base, color.tint || 0)
  }
  // Legacy indexed palette
  if (typeof color.indexed === 'number') {
    return EXCEL_INDEXED_COLORS[color.indexed] || null
  }
  return null
}

const isWhiteOrEmpty = (hex) => {
  if (!hex) return true
  const h = hex.toLowerCase()
  return h === '#ffffff' || h === '#ffffffff'
}

const ejsCellToStyleObj = (cell) => {
  const style = {}

  const fill = cell.fill
  if (fill && fill.type === 'pattern' && fill.pattern !== 'none') {
    const fgHex = ejsColorToHex(fill.fgColor)
    if (fgHex && !isWhiteOrEmpty(fgHex)) {
      style.bgcolor = fgHex
    }
  }

  const ejsFont = cell.font
  if (ejsFont) {
    const fontColorHex = ejsColorToHex(ejsFont.color)
    if (fontColorHex) style.color = fontColorHex
    const font = {}
    if (ejsFont.bold) font.bold = true
    if (ejsFont.italic) font.italic = true
    if (ejsFont.name) font.name = ejsFont.name
    if (ejsFont.size) font.size = ejsFont.size
    if (Object.keys(font).length) style.font = font
    if (ejsFont.underline) style.underline = true
    if (ejsFont.strike) style.strike = true
  }

  const alignH = cell.alignment?.horizontal
  const alignMap = { left: 'left', center: 'center', right: 'right', general: 'left' }
  if (alignH && alignMap[alignH]) style.align = alignMap[alignH]

  const alignV = cell.alignment?.vertical
  const valignMap = { top: 'top', middle: 'middle', bottom: 'bottom', distributed: 'middle' }
  if (alignV && valignMap[alignV]) style.valign = valignMap[alignV]

  if (cell.alignment?.wrapText) style.textwrap = true

  return Object.keys(style).length ? style : null
}

const ejsWorksheetToSheetData = (ws, name, { minRows, maxRows, maxCols }) => {
  const styles = []
  const styleCache = new Map()
  const rows = {}
  const cols = {}
  const merges = []

  const getOrAddStyle = (styleObj) => {
    const key = JSON.stringify(styleObj)
    if (styleCache.has(key)) return styleCache.get(key)
    const idx = styles.length
    styles.push(styleObj)
    styleCache.set(key, idx)
    return idx
  }

  ws.columns?.forEach((col, ci) => {
    if (ci >= maxCols) return
    if (col?.width && col.width > 0) cols[ci] = { width: Math.round(col.width * 7) }
  })

  let maxDataRow = 0

  ws.eachRow({ includeEmpty: false }, (row, rowNumber) => {
    const ri = rowNumber - 1
    if (ri >= maxRows) return
    const rowObj = { cells: {} }
    let hasContent = false
    if (row.height && row.height > 0) rowObj.height = Math.round(row.height)

    row.eachCell({ includeEmpty: true }, (cell, colNumber) => {
      const ci = colNumber - 1
      if (ci >= maxCols) return
      const rawVal = cell.value
      let text = ''
      if (rawVal !== null && rawVal !== undefined) {
        if (typeof rawVal === 'object' && rawVal.richText) {
          text = rawVal.richText.map(r => r.text || '').join('')
        } else if (typeof rawVal === 'object' && rawVal.result !== undefined) {
          text = String(rawVal.result ?? '')
        } else if (rawVal instanceof Date) {
          text = rawVal.toLocaleDateString('zh-CN')
        } else {
          text = String(rawVal)
        }
      }
      const styleObj = ejsCellToStyleObj(cell)
      if (!text && !styleObj) return
      const cellData = {}
      if (text) cellData.text = text
      if (styleObj) cellData.style = getOrAddStyle(styleObj)
      rowObj.cells[ci] = cellData
      hasContent = true
    })

    if (hasContent) {
      rows[ri] = rowObj
      if (ri > maxDataRow) maxDataRow = ri
    }
  })

  const targetRows = Math.max(maxDataRow + 1, minRows)
  for (let r = 0; r < targetRows; r++) {
    if (!rows[r]) rows[r] = { cells: {} }
  }
  if (ws.model?.merges) ws.model.merges.forEach((m) => merges.push(m))

  return {
    sheet: { id: name, name, cols, rows, merges, styles },
    truncated: maxDataRow >= maxRows - 1,
  }
}

const makeUniqueSheetName = (name, used) => {
  const base = (name || 'Sheet').trim() || 'Sheet'
  if (!used.has(base)) { used.add(base); return base }
  let i = 2
  while (used.has(`${base}_${i}`)) i += 1
  const next = `${base}_${i}`
  used.add(next)
  return next
}

export const sheetDataToAoa = (sheet) => {
  const rows = sheet?.rows || {}
  const rowIndexes = Object.keys(rows).map(x => Number(x)).filter(n => !Number.isNaN(n)).sort((a, b) => a - b)
  let maxCol = 0
  rowIndexes.forEach((r) => {
    const colIndexes = Object.keys(rows[r]?.cells || {}).map(x => Number(x)).filter(n => !Number.isNaN(n))
    if (colIndexes.length) maxCol = Math.max(maxCol, Math.max(...colIndexes))
  })
  const maxRow = rowIndexes.length ? Math.max(...rowIndexes) : 0
  const aoa = []
  for (let r = 0; r <= maxRow; r++) {
    const row = []
    const cells = rows[r]?.cells || {}
    for (let c = 0; c <= maxCol; c++) row.push(cells[c]?.text ?? '')
    aoa.push(row)
  }
  return aoa
}

export const readWorkbookSheets = async (
  arrayBuffer,
  { minRows = DEFAULT_MIN_ROWS, maxRows = DEFAULT_MAX_ROWS, maxCols = DEFAULT_MAX_COLS } = {}
) => {
  const wb = new ExcelJS.Workbook()
  await wb.xlsx.load(arrayBuffer)
  const sheets = []
  const usedNames = new Set()
  let truncatedSheetCount = 0
  wb.worksheets.forEach((ws) => {
    if (ws.state === 'hidden' || ws.state === 'veryHidden') return
    const uniqueName = makeUniqueSheetName(ws.name || 'Sheet', usedNames)
    const result = ejsWorksheetToSheetData(ws, uniqueName, { minRows, maxRows, maxCols })
    sheets.push(normalizeSheetData(result.sheet, uniqueName))
    if (result.truncated) truncatedSheetCount += 1
  })
  const safeSheets = sheets.filter(s => s && s.rows && s.cols)
  if (!safeSheets.length) safeSheets.push(createEmptySheetData('Sheet1'))
  return {
    sheets: safeSheets,
    meta: { sheetCount: safeSheets.length, truncatedSheetCount, skippedHiddenSheetCount: 0, maxRows, maxCols },
  }
}

export const readWorkbookSheetsWithProgress = async (
  arrayBuffer,
  { minRows = DEFAULT_MIN_ROWS, maxRows = DEFAULT_MAX_ROWS, maxCols = DEFAULT_MAX_COLS } = {},
  onProgress
) => {
  const wb = new ExcelJS.Workbook()
  await wb.xlsx.load(arrayBuffer)
  const visibleSheets = wb.worksheets.filter(ws => ws.state !== 'hidden' && ws.state !== 'veryHidden')
  const skippedHiddenSheetCount = wb.worksheets.length - visibleSheets.length
  const sheets = []
  const usedNames = new Set()
  let truncatedSheetCount = 0
  for (let i = 0; i < visibleSheets.length; i++) {
    const ws = visibleSheets[i]
    const uniqueName = makeUniqueSheetName(ws.name || 'Sheet', usedNames)
    const result = ejsWorksheetToSheetData(ws, uniqueName, { minRows, maxRows, maxCols })
    sheets.push(normalizeSheetData(result.sheet, uniqueName))
    if (result.truncated) truncatedSheetCount += 1
    if (typeof onProgress === 'function') onProgress({ index: i + 1, total: visibleSheets.length, name: uniqueName })
  }
  const safeSheets = sheets.filter(s => s && s.rows && s.cols)
  if (!safeSheets.length) safeSheets.push(createEmptySheetData('Sheet1'))
  return {
    sheets: safeSheets,
    meta: { sheetCount: safeSheets.length, truncatedSheetCount, skippedHiddenSheetCount, maxRows, maxCols },
  }
}

export const exportWorkbookFromSheets = (sheets, filename = 'test_case_assistant.xlsx') => {
  const wb = XLSX.utils.book_new()
  ;(sheets || []).forEach((sheetData, idx) => {
    const name = sheetData?.name || `Sheet${idx + 1}`
    const aoa = sheetDataToAoa(sheetData)
    const ws = XLSX.utils.aoa_to_sheet(aoa)
    XLSX.utils.book_append_sheet(wb, ws, name)
  })
  XLSX.writeFile(wb, filename)
}
