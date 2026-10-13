# DOCX Numbering v0.4.0

一个强大的Python包，用于从DOCX文件中提取和解析编号信息。**v0.4.0版本完全修复了编号错误和重复问题！**

## 🎯 主要特性

### ✨ 新版本亮点 (v0.4.0)
- 🔧 **完全修复编号错误**: 解决了 `7.`、`7.1.` 等错误编号显示问题
- 🚀 **消除编号重复**: 修复 `"1.  1. 验证用户名..."` 这样的重复显示
- ⚡ **智能编号提取**: 优先使用段落文本中的可见编号
- 🎯 **精准级别推断**: 根据编号结构自动推断层级关系
- 💾 **缓存优化**: 确保每次都使用最新的编号逻辑

### 📋 核心功能
- **多种编号格式**: 数字编号(`1.`, `1.1.`)、括号编号(`(1)`)、字母编号(`a)`)、圆圈数字(`①`)
- **智能检测**: 自动区分标题和正文，过滤无关内容
- **结构化输出**: 提供层级结构和详细编号信息
- **完整文档支持**: 提取所有段落（编号+普通段落）
- **灵活配置**: 支持自定义分隔符和输出格式

## 🚀 快速开始

### 基本用法 (推荐方法)

```python
from docx_numbering import NumberedDocxReader

# 创建读取器
reader = NumberedDocxReader("document.docx")

# 🌟 获取编号结构 (推荐)
structure = reader.get_numbering_structure()
for item in structure:
    print(f"级别 {item['level']}: {item['numbering']} - {item['text']}")

# 🌟 获取完整文档内容 (推荐)
content = reader.get_full_document_content()
for item in content:
    if item['has_numbering']:
        print(f"[编号] {item['formatted_numbering']} {item['text']}")
    else:
        print(f"[正文] {item['text']}")

# 🌟 获取格式化文档 (推荐)
formatted_doc = reader.get_complete_formatted_document()
print(formatted_doc)
```

### 输出示例

**修复前的错误显示**：
```
❌ 7. 范围
❌     7.1. 标识
❌ 1.  1. 验证用户名和密码...  (编号重复)
```

**修复后的正确显示**：
```
✅ 1. 范围
✅     1.1. 标识
✅     1.2. 系统概述
✅         1.2.1. 系统组成及功能概述
✅ 1. 验证用户名和密码是否匹配数据库记录。
✅ 2. 向用户注册设备发送动态验证码。
```

## 🔬 算法原理

### 多层级编号提取策略

```
显示编号（段落文本开头的"1."） > Word自动编号 > 手动编号 > 无编号
```

1. **显示编号提取**: 使用正则表达式提取段落开头的可见编号
2. **自动编号解析**: 解析Word内部的编号定义（numbering.xml）
3. **手动编号识别**: 识别手动输入的编号格式
4. **级别推断**: 根据编号结构（如点号数量）推断层级

### 编号重复避免机制

```python
# 核心逻辑：检查段落文本是否已包含编号
if text_has_numbering:
    # 段落已含编号，直接使用（只添加缩进）
    output = f"{indent}{paragraph.text}"
else:
    # 段落无编号，添加自动编号
    output = f"{indent}{formatted_numbering} {paragraph.text}"
```

### 缓存重置优化

每次调用核心方法时都会重置计数器缓存，确保使用最新的编号逻辑：

```python
def get_full_document_content(self):
    self.counters.clear()      # 清空编号计数器
    self.number_cache.clear()  # 清空编号缓存
    # ... 编号提取逻辑
```

## 📚 API 方法

### ✅ 推荐方法 (v0.4.0)

| 方法 | 用途 | 返回类型 |
|------|------|----------|
| `get_numbering_structure()` | 获取编号结构 | `List[Dict]` |
| `get_full_document_content()` | 获取完整文档内容 | `List[Dict]` |
| `get_complete_formatted_document()` | 获取格式化文档 | `str` |

### ⚠️ 废弃方法

| 废弃方法 | 替代方法 |
|----------|----------|
| `get_paragraphs_with_numbering()` | `get_full_document_content()` |
| `get_numbered_paragraphs_only()` | `get_full_document_content()` + 过滤 |
| `get_enhanced_numbering_info()` | `get_full_document_content()` |

## 📦 安装

```bash
# 从源码安装（推荐）
cd docx_numbering
pip install -e .
```

## 🔧 系统要求

- Python 3.7+
- python-docx >= 0.8.11

## 📖 文档

- [使用指南](docs/usage_guide.md) - 详细的使用说明和示例
- [API参考](docs/api_reference.md) - 完整的API文档
- [算法原理](docs/algorithm_principles.md) - 深入的算法实现原理

## 🧪 测试验证

### 编号正确性
- ✅ 没有 `7.` 开头的错误编号
- ✅ 正确显示 `1.`、`1.1.`、`1.2.1.` 等编号
- ✅ 多级编号结构完全正确

### 编号重复检查
- ✅ 完全消除编号重复问题
- ✅ 段落内容编号显示正常
- ✅ 自动检测并避免重复

### 性能和兼容性
- ✅ 缓存机制优化，性能提升
- ✅ 新旧API兼容（废弃方法会有警告）
- ✅ 与requirement_analysis模块完全兼容

## 🔄 版本历史

- **v0.4.0** (最新): 修复编号重复问题和算法优化
- **v0.3.0**: 新增完整文档内容读取功能
- **v0.2.0**: 新增Word样式内容组合功能  
- **v0.1.0**: 基础编号提取功能

## 📄 许可证

MIT License

---

**🎯 现在可以完美处理Word文档的自动编号，与原文档显示完全一致！**
