# API 参考文档 v0.4.0

## 主要类

### NumberedDocxReader

主要的DOCX编号读取器类，用于从Word文档中提取编号信息。

#### 构造函数

```python
NumberedDocxReader(docx_path, gap_text="\t")
```

**参数:**
- `docx_path` (str | Path): DOCX文件路径
- `gap_text` (str, 可选): 编号和文本之间的分隔符，默认为制表符

**异常:**
- `InvalidDocxFileError`: 文件不存在、不是文件或不是.docx格式

**示例:**
```python
from docx_numbering import NumberedDocxReader

# 使用默认分隔符
reader = NumberedDocxReader("document.docx")

# 使用自定义分隔符
reader = NumberedDocxReader("document.docx", gap_text=" ")
```

---

## ✅ 推荐方法 (v0.4.0)

### get_numbering_structure()

```python
def get_numbering_structure() -> List[Dict[str, Union[str, int]]]
```

获取文档的编号结构信息，只包含有编号的段落。

**返回:**
- `List[Dict]`: 编号信息列表，每个字典包含：
  - `level` (int): 编号级别（0开始）
  - `numbering` (str): 编号文本（如"1.", "1.1", "1.2.1"）
  - `text` (str): 段落文本内容
  - `full_text` (str): 完整文本（编号+分隔符+文本）

**示例:**
```python
reader = NumberedDocxReader("doc.docx")
structure = reader.get_numbering_structure()

for item in structure:
    print(f"级别 {item['level']}: {item['numbering']} - {item['text']}")

# 输出:
# 级别 0: 1. - 范围
# 级别 1: 1.1 - 标识
# 级别 1: 1.2 - 系统概述
```

**使用场景:**
- 需要分析文档结构
- 生成目录或大纲
- 只关心有编号的段落

---

### get_full_document_content()

```python
def get_full_document_content() -> List[Dict[str, Union[str, int, bool]]]
```

获取文档的所有内容，包括有编号和无编号的段落。

**返回:**
- `List[Dict]`: 段落信息列表，每个字典包含：
  - `level` (int): 编号级别（0开始，无编号段落为0）
  - `numbering` (str): 原始编号文本
  - `formatted_numbering` (str): 格式化后的编号文本
  - `text` (str): 段落文本内容
  - `word_like_text` (str): Word样式的完整文本
  - `has_numbering` (bool): 是否有编号

**示例:**
```python
reader = NumberedDocxReader("doc.docx")
content = reader.get_full_document_content()

for item in content:
    if item['has_numbering']:
        print(f"[编号] {item['formatted_numbering']} {item['text']}")
    else:
        print(f"[正文] {item['text']}")

# 输出:
# [正文] 以下是需求规格说明：
# [编号] 1. 范围
# [编号] 1.1. 标识
# [正文] 在此处填写项目信息
```

**使用场景:**
- 需要完整的文档内容
- 保持文档结构完整性
- 区分编号段落和普通段落

---

### get_complete_formatted_document()

```python
def get_complete_formatted_document(format_style: str = "standard") -> str
```

获取格式化的完整文档字符串，类似Word中的显示效果。

**参数:**
- `format_style` (str, 可选): 格式样式
  - `"standard"`: 标准格式（默认）
  - `"compact"`: 紧凑格式（无缩进）
  - `"detailed"`: 详细格式（额外间距）

**返回:**
- `str`: 格式化后的完整文档文本

**示例:**
```python
reader = NumberedDocxReader("doc.docx")

# 标准格式
formatted_doc = reader.get_complete_formatted_document("standard")
print(formatted_doc)

# 输出:
# 以下是需求规格说明：
# 1. 范围
#     1.1. 标识
# 在此处填写项目信息
#     1.2. 系统概述
```

**使用场景:**
- 需要直接显示或输出文档
- 生成报告或日志
- 与Word显示效果一致的文本

---

## ⚠️ 废弃方法（不推荐使用）

> **警告**: 以下方法在v0.4.0中被标记为废弃，调用时会显示警告。建议使用新的推荐方法。

### get_paragraphs_with_numbering() ❌ 已废弃

```python
def get_paragraphs_with_numbering() -> List[str]
```

**替代方法**: 使用 `get_full_document_content()`

**原功能**: 获取所有段落，编号段落包含编号文本。

**迁移示例:**
```python
# ❌ 废弃用法
paragraphs = reader.get_paragraphs_with_numbering()

# ✅ 推荐替代
content = reader.get_full_document_content()
paragraphs = [item['word_like_text'] for item in content]
```

---

### get_numbered_paragraphs_only() ❌ 已废弃

```python
def get_numbered_paragraphs_only() -> List[str]
```

**替代方法**: 使用 `get_full_document_content()` + 过滤

**原功能**: 只获取有编号的段落。

**迁移示例:**
```python
# ❌ 废弃用法
numbered = reader.get_numbered_paragraphs_only()

# ✅ 推荐替代
content = reader.get_full_document_content()
numbered = [item['word_like_text'] for item in content if item['has_numbering']]
```

---

### get_enhanced_numbering_info() ❌ 已废弃

```python
def get_enhanced_numbering_info() -> List[Dict[str, Union[str, int, bool]]]
```

**替代方法**: 使用 `get_full_document_content()`

**原功能**: 获取增强的编号信息，包括样式信息。

**迁移示例:**
```python
# ❌ 废弃用法
enhanced = reader.get_enhanced_numbering_info()

# ✅ 推荐替代
content = reader.get_full_document_content()
# content 包含了更准确和完整的信息
```

---

### get_word_like_content() ❌ 已废弃

```python
def get_word_like_content(indent_style: str = "space", numbering_separator: str = " ") -> List[str]
```

**替代方法**: 使用 `get_full_document_content()`

**迁移示例:**
```python
# ❌ 废弃用法
word_like = reader.get_word_like_content()

# ✅ 推荐替代
content = reader.get_full_document_content()
word_like = [item['word_like_text'] for item in content if item['has_numbering']]
```

---

### get_formatted_document() ❌ 已废弃

```python
def get_formatted_document(format_style: str = "standard") -> str
```

**替代方法**: 使用 `get_complete_formatted_document()`

**迁移示例:**
```python
# ❌ 废弃用法
formatted = reader.get_formatted_document()

# ✅ 推荐替代
formatted = reader.get_complete_formatted_document()
```

---

### get_enhanced_word_like_content() ❌ 已废弃

```python
def get_enhanced_word_like_content() -> List[Dict[str, Union[str, int]]]
```

**替代方法**: 使用 `get_full_document_content()`

**迁移示例:**
```python
# ❌ 废弃用法
enhanced_content = reader.get_enhanced_word_like_content()

# ✅ 推荐替代
content = reader.get_full_document_content()
# content 提供了更丰富和准确的信息
```

---

## 内部方法

### _extract_displayed_numbering()

```python
def _extract_displayed_numbering(text: str) -> Optional[str]
```

从段落文本中提取显示的编号。

**参数:**
- `text` (str): 段落文本

**返回:**
- `Optional[str]`: 提取的编号，如果没有则返回None

**支持的编号格式:**
- 数字编号: `1.`, `1.1.`, `1.2.1.`
- 括号编号: `1)`, `(1)`, `（1）`
- 字母编号: `a)`, `A)`, `b)`, `B)`
- 圆圈数字: `①`, `②`, `③`

---

### _infer_numbering_level_from_display()

```python
def _infer_numbering_level_from_display(numbering: str) -> int
```

根据显示的编号推断级别。

**参数:**
- `numbering` (str): 编号文本

**返回:**
- `int`: 推断的级别（0开始）

**级别推断规则:**
- `1.` → 级别0
- `1.1.` → 级别1  
- `1.2.1.` → 级别2
- `(1)`, `a)` → 级别0

---

## 异常类

### InvalidDocxFileError

```python
class InvalidDocxFileError(Exception)
```

当DOCX文件无效时抛出的异常。

**常见原因:**
- 文件不存在
- 文件不是.docx格式
- 文件损坏无法读取

**示例:**
```python
try:
    reader = NumberedDocxReader("invalid.docx")
except InvalidDocxFileError as e:
    print(f"文件错误: {e}")
```

---

### NumberingNotFoundError

```python
class NumberingNotFoundError(Exception)
```

当文档中找不到编号信息时抛出的异常。

**常见原因:**
- 文档不包含自动编号
- 编号信息损坏

---

### NumberFormatError

```python
class NumberFormatError(Exception)
```

当编号格式不支持时抛出的异常。

---

## 数据类型定义

### 编号结构字典

```python
{
    "level": int,           # 编号级别（0开始）
    "numbering": str,       # 编号文本（如"1.", "1.1"）
    "text": str,           # 段落文本内容
    "full_text": str       # 完整文本（编号+分隔符+文本）
}
```

### 完整内容字典

```python
{
    "level": int,                    # 编号级别
    "numbering": str,                # 原始编号
    "formatted_numbering": str,      # 格式化编号
    "text": str,                    # 段落文本
    "word_like_text": str,          # Word样式文本
    "has_numbering": bool           # 是否有编号
}
```

---

## 使用建议

### 性能优化

1. **重用Reader实例**: 对同一文档的多次操作使用同一个Reader实例
2. **选择合适的方法**: 根据需要选择最合适的方法，避免过度处理
3. **异常处理**: 始终包含适当的异常处理

```python
# 推荐的使用模式
try:
    reader = NumberedDocxReader("document.docx")
    
    # 根据需要选择方法
    if need_structure_only:
        data = reader.get_numbering_structure()
    else:
        data = reader.get_full_document_content()
        
except InvalidDocxFileError:
    # 处理文件错误
    pass
except Exception as e:
    # 处理其他错误
    pass
```

### 版本迁移

从旧版本迁移到v0.4.0时，请注意：

1. **更新方法调用**: 使用新的推荐方法
2. **调整数据处理**: 新方法返回的数据结构更丰富
3. **处理警告**: 废弃方法会显示警告，建议及时迁移

```python
# v0.3.0 及以前版本
paragraphs = reader.get_paragraphs_with_numbering()
for paragraph in paragraphs:
    print(paragraph)

# v0.4.0 推荐方式
content = reader.get_full_document_content()
for item in content:
    print(item['word_like_text'])
```

---

## 相关文档

- [使用指南](usage_guide.md) - 详细的使用说明和示例
- [算法原理](algorithm_principles.md) - 深入的算法实现原理
