# DOCX Numbering 使用指南 v0.4.0

## 概述

DOCX Numbering 是一个强大的Python包，用于从DOCX文件中提取和解析自动编号信息。**v0.4.0版本完全修复了编号错误和重复问题**，支持多种编号格式，包括数字编号、中文编号、罗马数字、字母编号等。

## 🚀 新版本特性 (v0.4.0)

- **🔧 修复编号错误**: 解决了 `7.`、`7.1.` 等错误编号显示
- **🚀 消除编号重复**: 修复 `"1.  1. 验证用户名..."` 重复显示
- **⚡ 智能编号提取**: 优先使用段落文本中的可见编号
- **💾 缓存优化**: 确保每次使用最新编号逻辑

## 安装

```bash
# 从源码安装（推荐）
cd docx_numbering
pip install -e .
```

## 🌟 推荐用法 (v0.4.0)

### 1. 获取编号结构 `get_numbering_structure()`

**推荐用于**: 需要编号段落的结构化信息时

```python
from docx_numbering import NumberedDocxReader

reader = NumberedDocxReader("document.docx")
structure = reader.get_numbering_structure()

for item in structure:
    level = item['level']          # 编号级别 (0, 1, 2...)
    numbering = item['numbering']  # 编号文本 ("1.", "1.1", "1.2.1")
    text = item['text']           # 段落文本
    print(f"级别 {level}: {numbering} - {text}")
```

**输出示例**:
```
级别 0: 1. - 范围
级别 1: 1.1 - 标识
级别 1: 1.2 - 系统概述
级别 2: 1.2.1 - 系统组成及功能概述
```

### 2. 获取完整文档内容 `get_full_document_content()`

**推荐用于**: 需要包含所有段落（编号+普通段落）的完整文档时

```python
reader = NumberedDocxReader("document.docx")
content = reader.get_full_document_content()

for item in content:
    if item['has_numbering']:
        # 有编号的段落
        level = item['level']
        numbering = item['formatted_numbering']
        text = item['text']
        print(f"[编号] {'  ' * level}{numbering} {text}")
    else:
        # 普通段落
        print(f"[正文] {item['text']}")
```

**输出示例**:
```
[正文] 以下是根据你的格式要求补充完整后的需求规格说明：
[编号] 1. 范围
[编号]   1.1. 标识
[正文] 在此处填写项目或系统的唯称、编号等
[编号]   1.2. 系统概述
[编号]     1.2.1. 系统组成及功能概述
```

### 3. 获取格式化文档 `get_complete_formatted_document()`

**推荐用于**: 需要直接获取类似Word显示的完整文档文本时

```python
reader = NumberedDocxReader("document.docx")
formatted_doc = reader.get_complete_formatted_document("standard")
print(formatted_doc)
```

**输出示例**:
```
以下是根据你的格式要求补充完整后的需求规格说明：
1. 范围
    1.1. 标识
在此处填写项目或系统的唯称、编号等
    1.2. 系统概述
        1.2.1. 系统组成及功能概述
详细阐述系统的各个组成块及其功能要点
```

## 🔬 算法原理详解

### 编号提取优先级策略

```
显示编号（段落文本开头） > Word自动编号 > 手动编号 > 无编号
```

#### 1. 显示编号提取
```python
# 使用正则表达式匹配段落开头的编号
patterns = [
    r'^(\d+(?:\.\d+)*\.?)\s+',      # 1., 1.1., 1.2.1.
    r'^(\d+\))\s+',                 # 1), 2)
    r'^([(（]\d+[)）])\s+',         # (1), （1）
    r'^([a-zA-Z]\))\s+',            # a), b), A), B)
    r'^([①-⑳])\s*',                # 圆圈数字
]
```

#### 2. 级别推断
```python
def _infer_numbering_level_from_display(numbering):
    # 通过点号数量推断级别
    # "1." -> 级别0, "1.1." -> 级别1, "1.2.1." -> 级别2
    if '.' in numbering:
        return numbering.count('.')
    else:
        return 0  # 单级编号
```

#### 3. 编号重复避免
```python
# 检查段落文本是否已含编号
text_has_numbering = self._extract_displayed_numbering(paragraph.text.strip()) is not None
if text_has_numbering:
    # 段落已含编号，直接使用（只添加缩进）
    word_like_text = f"{indent}{paragraph.text}"
else:
    # 段落无编号，添加自动编号
    word_like_text = f"{indent}{formatted_numbering} {paragraph.text}"
```

### Word文档编号机制

Word文档的自动编号不存储在段落文本中，而是存储在 `numbering.xml` 文件中：

1. **编号定义** (`abstractNum`): 定义编号格式（数字、字母、罗马数字等）
2. **编号实例** (`num`): 将编号定义应用到具体段落
3. **段落关联**: 段落通过 `numPr` 元素关联到编号实例

```xml
<!-- numbering.xml 示例 -->
<w:numbering>
    <w:abstractNum w:abstractNumId="0">
        <w:lvl w:ilvl="0">
            <w:start w:val="1"/>
            <w:numFmt w:val="decimal"/>
            <w:lvlText w:val="%1."/>
        </w:lvl>
    </w:abstractNum>
</w:numbering>
```

## ⚠️ 废弃方法（不推荐使用）

以下方法在v0.4.0中被标记为废弃，建议使用新的推荐方法：

### `get_paragraphs_with_numbering()` ❌ 已废弃

```python
# ❌ 废弃用法
paragraphs = reader.get_paragraphs_with_numbering()

# ✅ 推荐替代
content = reader.get_full_document_content()
```

### `get_numbered_paragraphs_only()` ❌ 已废弃

```python
# ❌ 废弃用法  
numbered = reader.get_numbered_paragraphs_only()

# ✅ 推荐替代
content = reader.get_full_document_content()
numbered = [item for item in content if item['has_numbering']]
```

### `get_enhanced_numbering_info()` ❌ 已废弃

```python
# ❌ 废弃用法
enhanced = reader.get_enhanced_numbering_info()

# ✅ 推荐替代
content = reader.get_full_document_content()
```

## 🔧 高级用法

### 自定义分隔符

```python
# 使用空格作为编号和文本的分隔符
reader = NumberedDocxReader("document.docx", gap_text=" ")
```

### 错误处理

```python
from docx_numbering import NumberedDocxReader, InvalidDocxFileError

try:
    reader = NumberedDocxReader("document.docx")
    structure = reader.get_numbering_structure()
except InvalidDocxFileError as e:
    print(f"文件错误: {e}")
except Exception as e:
    print(f"处理错误: {e}")
```

### 性能优化

```python
# 对于大文档，建议使用缓存
reader = NumberedDocxReader("large_document.docx")

# 首次调用会解析文档
structure = reader.get_numbering_structure()

# 后续调用使用缓存（同一个reader实例）
content = reader.get_full_document_content()
```

## 🧪 测试示例

### 验证编号正确性

```python
reader = NumberedDocxReader("test_document.docx")
structure = reader.get_numbering_structure()

# 检查是否有错误的7.开头编号
seven_errors = [item for item in structure if item['numbering'].startswith('7.')]
assert len(seven_errors) == 0, "发现错误的7.编号"

# 检查是否有正确的1.开头编号
one_correct = [item for item in structure if item['numbering'].startswith('1.')]
assert len(one_correct) > 0, "没有发现正确的1.编号"
```

### 验证编号重复

```python
formatted_doc = reader.get_complete_formatted_document()
lines = formatted_doc.split('\n')

# 检查编号重复模式
import re
duplicate_lines = [line for line in lines if re.search(r'^\s*\d+\.\s+\d+\.', line)]
assert len(duplicate_lines) == 0, f"发现编号重复: {duplicate_lines}"
```

## 🔗 相关文档

- [API参考文档](api_reference.md) - 完整的API文档
- [算法原理文档](algorithm_principles.md) - 深入的算法实现原理

## ❓ 常见问题

**Q: 为什么我的编号显示为7.而不是1.？**  
A: 这是v0.3.0及以前版本的已知问题，已在v0.4.0中完全修复。

**Q: 为什么会出现"1.  1. 验证用户名..."这样的重复编号？**  
A: 这是编号重复问题，已在v0.4.0中修复。新版本会自动检测并避免重复。

**Q: 如何获取与Word文档完全一致的编号？**  
A: 使用v0.4.0的 `get_complete_formatted_document()` 方法，它提供与Word显示完全一致的编号。

**Q: 废弃的方法还能使用吗？**  
A: 可以，但会显示警告。建议迁移到新的推荐方法以获得更好的性能和准确性。
