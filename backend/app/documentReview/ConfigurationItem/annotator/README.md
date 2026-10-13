# 文档批注功能

本模块提供了为文档审查结果添加批注的功能，支持在原始文档中标注AI发现的问题。

## 功能特性

- **Spire.Doc批注支持**：使用Spire.Doc库添加真正的Word批注和高亮
- **智能文本定位**：采用多层次匹配策略，优先使用原始需求内容进行定位
- **避免目录匹配**：通过优先匹配正文内容，避免批注被错误地添加到目录部分
- **多级部分匹配**：支持完整匹配、短语匹配、关键词匹配等多种策略
- **问题等级显示**：在批注中显示问题等级（重要问题、一般问题、建议改进）
- **双文档支持**：支持研制任务书和需求规格说明两种文档类型

## 智能匹配策略

### 匹配优先级
1. **优先使用 `requirement_content`（原始需求内容）**：避免匹配到目录和章节标题
2. **备选使用 `issue_location`（问题位置）**：仅在需求内容匹配失败时使用

### 部分匹配算法
1. **完整匹配**：首先尝试完整文本匹配（去除多余空白字符）
2. **短语匹配**：提取3-5个连续关键词组成的短语进行匹配
3. **关键词匹配**：匹配长度≥4的单个关键词
4. **编号内容匹配**：对于数字编号开头的内容，匹配编号后的主要内容
5. **停用词过滤**：自动过滤常见停用词，提高匹配准确性

### 匹配示例
```python
# 原始需求内容（优先匹配）
requirement_content = "本项目旨在开发一个高性能的软件系统，该系统应具备良好的可扩展性和稳定性"

# 问题位置（备选匹配）
issue_location = "1.1 项目概述"

# 匹配策略：
# 1. 首先尝试匹配完整的requirement_content
# 2. 如果失败，尝试匹配关键短语如"高性能的软件系统"
# 3. 如果仍然失败，尝试匹配关键词如"软件系统"
# 4. 最后才尝试匹配issue_location
```

## 模块结构

```
annotator/
├── __init__.py              # 模块初始化文件
├── spire_commenter.py       # Spire.Doc批注实现（含智能匹配）
└── README.md               # 本文档
```

## API接口

### spire_commenter.py

```python
def add_comments_to_document_spire(document_path: str, issues: List[Dict], output_dir: str, session_id: int, doc_type: str) -> str:
    """
    使用Spire.Doc为文档添加批注
    
    Args:
        document_path: 原始文档文件路径
        issues: AI分析出的问题列表
        output_dir: 输出目录
        session_id: 会话ID
        doc_type: 文档类型 (taskBook 或 requirementSpec)
        
    Returns:
        批注版文档的路径
    """

def _add_comment_to_text_correct(doc: Document, target_text: str, comment_text: str, author: str = "AI", use_partial_match: bool = False) -> bool:
    """
    使用正确的Spire.Doc API添加批注并高亮文本
    
    Args:
        doc: Spire.Doc文档对象
        target_text: 要匹配的目标文本
        comment_text: 批注内容
        author: 批注作者
        use_partial_match: 是否使用部分匹配策略
    """

def _find_text_with_partial_match(doc: Document, target_text: str):
    """
    使用改进的部分匹配策略查找文本
    
    实现多层次匹配算法，包括完整匹配、短语匹配、关键词匹配等
    """
```

## 数据结构

### 问题列表格式
```python
issues = [
    {
        'requirement_content': '原始需求内容（优先用于匹配）',  # 新增：优先匹配字段
        'issue_location': '问题定位文本（备选匹配）',
        'issue_name': '问题名称',
        'violation_rules': '违反规则',
        'issue_level': '重要问题',  # 重要问题|一般问题|建议改进
        'description_issue': '问题描述'
    }
]
```

## 集成方式

### 后端集成
在审查流程完成后调用批注功能：

```python
# 生成批注版文档
from ..annotator.spire_commenter import add_comments_to_document_spire

annotated_path = add_comments_to_document_spire(
    original_document_path, 
    problems, 
    temp_dir, 
    session_id,
    'taskBook'  # 或 'requirementSpec'
)

# 存储到数据库
cur.execute("UPDATE review_sessions SET annotated_taskbook_path = ? WHERE id = ?", 
            (annotated_path, session_id))
```

### 前端集成
下载组件提供批注版文档下载：

```vue
<el-button type="success" @click="downloadTaskBook">
  下载批注版研制任务书
</el-button>
```

## 下载API

- `/api/download/annotated/taskbook` - 下载研制任务书批注版
- `/api/download/annotated/requirementspec` - 下载需求规格说明批注版

## 依赖要求

- **Spire.Doc**: Python Word文档处理库
- **python-docx**: 备用文档处理（已移除）
- **SQLite**: 批注文件路径存储

## 文件命名规则

批注版文档命名格式：`{文档类型}_批注版_session_{会话ID}.docx`

示例：
- `研制任务书_批注版_session_123.docx`
- `需求规格说明_批注版_session_123.docx`

## 错误处理

- 如果Spire.Doc不可用，会抛出ImportError
- 如果找不到目标文本，会记录警告并跳过该问题
- 所有错误都会记录到日志中，便于调试
- 详细的匹配过程日志，便于排查匹配问题

## 性能优化

- **智能匹配优先级**：优先使用需求内容匹配，避免无效的目录匹配
- **多层次部分匹配**：从长到短的短语匹配，提高匹配成功率
- **停用词过滤**：减少无意义词汇的匹配尝试
- **批注添加完成后自动释放文档资源**
- **统计成功率，便于监控批注质量**

## 改进说明

### v2.0 更新（当前版本）
- ✅ **解决目录匹配问题**：优先使用`requirement_content`进行匹配
- ✅ **多层次部分匹配**：实现智能的短语和关键词匹配
- ✅ **匹配策略优化**：避免批注被错误添加到目录部分
- ✅ **详细日志记录**：提供完整的匹配过程日志

### v1.0 已知问题（已解决）
- ❌ 批注经常被添加到目录部分
- ❌ 匹配策略过于简单，容易匹配失败
- ❌ 缺少智能的部分匹配算法 