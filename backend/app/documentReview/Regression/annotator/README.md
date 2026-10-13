# 回归测试文档批注功能

本模块为回归测试的文档审查结果提供批注功能，支持在影响域分析报告中标注AI发现的问题。

## 功能特性

- **Spire.Doc批注支持**：使用Spire.Doc库添加真正的Word批注和高亮
- **智能文本定位**：支持精确匹配和部分匹配来定位问题文本
- **问题等级显示**：在批注中显示问题等级（重要问题、一般问题、建议改进）
- **影响域报告支持**：专门针对影响域分析报告的批注处理

## 模块结构

```
annotator/
├── __init__.py              # 模块初始化文件
├── spire_commenter.py       # Spire.Doc批注实现
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
        doc_type: 文档类型 (impactReport)
        
    Returns:
        批注版文档的路径
    """
```

## 数据结构

### 问题列表格式
```python
issues = [
    {
        'doc_type': 'regression',
        'doc_name': '影响域分析报告',
        'issue_location': '问题定位文本',
        'issue_name': '问题名称',
        'violation_rules': '违反规则',
        'issue_level': '重要问题',  # 重要问题|一般问题|建议改进
        'description_issue': '问题描述',
        'requirement_content': '原始需求内容'
    }
]
```

## 集成方式

### 后端集成
在回归测试审查流程完成后调用批注功能：

```python
# 生成批注版影响域分析报告
from ..annotator.spire_commenter import add_comments_to_document_spire

annotated_path = add_comments_to_document_spire(
    original_impactreport_path, 
    problems, 
    temp_dir, 
    session_id,
    'impactReport'
)

# 存储到数据库
cur.execute("UPDATE review_sessions SET annotated_impactreport_path = ? WHERE id = ?", 
            (annotated_path, session_id))
```

### 前端集成
下载组件提供批注版文档下载：

```vue
<el-button type="success" @click="downloadImpactReport">
  下载批注版影响域分析报告
</el-button>
```

## 下载API

- `/api/download/annotated/impactreport` - 下载影响域分析报告批注版

## 数据库结构

### review_sessions表更新
添加了批注文件路径字段：

```sql
ALTER TABLE review_sessions ADD COLUMN annotated_impactreport_path TEXT;
```

字段说明：
- `annotated_impactreport_path`: 影响域分析报告批注版文件路径

## 依赖要求

- **Spire.Doc**: Python Word文档处理库
- **SQLite**: 批注文件路径存储
- **pathlib**: 路径处理
- **glob**: 文件匹配

## 文件命名规则

批注版文档命名格式：`影响域分析报告_批注版_session_{会话ID}.docx`

示例：`影响域分析报告_批注版_session_456.docx`

## 错误处理

- 如果Spire.Doc不可用，会抛出ImportError
- 如果找不到目标文本，会记录警告并跳过该问题
- 如果找不到原始文档，会记录警告
- 所有错误都会记录到日志中，便于调试

## 工作流程

1. **审查完成**：AI完成影响域分析报告审查
2. **生成批注**：调用批注功能为发现的问题添加批注
3. **存储路径**：将批注文件路径存储到数据库
4. **用户下载**：用户通过前端界面下载批注版文档

## 性能优化

- 使用精确匹配优先，部分匹配作为备选
- 批注添加完成后自动释放文档资源
- 统计成功率，便于监控批注质量
- 支持大文档的分块处理

## 日志记录

所有批注操作都有详细的日志记录：
- 成功添加的批注数量
- 失败的批注及原因
- 文档加载和保存状态
- 文本定位结果

## 与配置项测试模块的区别

- **文档类型**：处理影响域分析报告而非研制任务书/需求规格说明
- **数据结构**：适配回归测试的问题数据格式
- **文件命名**：使用影响域分析报告的命名规则
- **数据库字段**：使用独立的批注路径字段 