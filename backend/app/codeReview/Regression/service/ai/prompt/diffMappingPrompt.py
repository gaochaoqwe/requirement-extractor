"""
代码差异映射提示词模板
用于第二阶段：将代码变更映射到影响域分析报告中的任务
"""

def get_diff_mapping_prompt(change_details: str, tasks_section: str, report_content: str) -> str:
    """
    生成代码差异映射提示词
    
    Args:
        change_details: 代码变更详情
        tasks_section: 任务列表信息
        report_content: 影响域分析报告内容（已简化，不再使用）
        
    Returns:
        str: 映射提示词
    """
    return f"""分析以下代码变更，将其映射到相应任务。

## 🚨 重要约束（必须遵守）
1. **只能使用下面列出的任务ID**，不能创建新的任务ID
2. **任务ID必须是纯数字**（如"1", "2", "3"），不能包含其他字符
3. **必须映射到至少一个任务**，不能返回空数组
4. **如果不确定属于哪个任务，映射到最后一个任务ID**

## 输出格式（严格JSON）
```json
{{
  "related_task_ids": ["1"],
  "mapping_confidence": "high|medium|low",
  "mapping_reason": "简要说明映射原因"
}}
```

## 代码变更信息
{change_details}

{tasks_section}

**重要提醒**：任务ID只能从上面的任务列表中选择，必须是纯数字格式！"""


def get_fallback_mapping_prompt(change_details: str, tasks_section: str) -> str:
    """
    生成降级映射提示词（当报告内容过长时使用）
    
    Args:
        change_details: 代码变更详情
        tasks_section: 任务列表信息
        
    Returns:
        str: 降级映射提示词
    """
    return f"""你是一个专业的代码分析专家。请分析以下函数变更并尝试映射到相应任务。

## 分析任务
由于影响域分析报告内容过长，请基于函数名称、变更类型和任务描述进行基础映射。

## 输出格式
请以JSON格式返回分析结果：
```json
{{
  "related_task_ids": ["1"],
  "mapping_confidence": "low",
  "mapping_reason": "基于函数名称和变更类型的基础映射",
  "mentioned_in_report": "unknown",
  "mapping_score": 0.3
}}
```

{change_details}

{tasks_section}

请进行基础映射分析，如果无法确定映射关系，请返回空的related_task_ids数组。
"""


def build_change_details_section(change: dict) -> str:
    """
    构建变更详情部分
    
    Args:
        change: 变更信息字典
        
    Returns:
        str: 变更详情文本
    """
    file_path = change.get("file_path", "unknown")
    function_name = change.get("function_name", "unknown")
    change_type = change.get("change_type", "unknown")
    old_code = change.get("old_code", "")
    new_code = change.get("new_code", "")
    
    section = f"## 代码变更详情\n"
    section += f"- **文件路径**: {file_path}\n"
    section += f"- **函数名称**: {function_name}\n"
    section += f"- **变更类型**: {change_type}\n\n"
    
    if old_code:
        section += f"### 旧版本代码\n```c\n{old_code}\n```\n\n"
    
    if new_code:
        section += f"### 新版本代码\n```c\n{new_code}\n```\n\n"
    
    return section


def build_tasks_section(tasks: list) -> str:
    """
    构建任务列表部分
    
    Args:
        tasks: 任务列表
        
    Returns:
        str: 任务列表文本
    """
    if not tasks:
        return "## 可用任务\n无可用任务\n\n"
    
    section = "## 📋 可用任务（只能使用以下任务ID）\n\n"
    
    for i, task in enumerate(tasks):
        is_last_task = (i == len(tasks) - 1)
        
        if is_last_task and task.task_name == "其他变更":
            section += f"**任务ID: {task.task_id}** ⭐ （其他变更 - 不确定时选此项）\n"
        else:
            section += f"**任务ID: {task.task_id}**\n"
            
        section += f"- 任务名称: {task.task_name}\n"
        section += f"- 任务描述: {task.task_description}\n"
        
        # 只显示任务的原始报告内容，不显示完整报告
        if task.original_report_content and len(task.original_report_content.strip()) > 0:
            # 截取前200个字符避免过长
            content_preview = task.original_report_content[:200]
            if len(task.original_report_content) > 200:
                content_preview += "..."
            section += f"- 相关内容: {content_preview}\n"
        
        section += "\n"
    
    section += "⚠️ **重要**: 任务ID必须是纯数字（如1、2、3），不能包含其他字符！\n\n"
    
    return section 