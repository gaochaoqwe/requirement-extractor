"""
回归测试任务生成器
负责从影响域分析报告中提取任务列表并存储到数据库
"""
import os
import json
import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from ..prompt.taskPlanningPrompt import get_task_planning_prompt
from ....db.repository.regression_task_repo import RegressionTaskRepository

# 导入回归测试的标准化日志系统
from ....utils.concurrent_logger import (
    log_regression_concurrent_debug,
    log_regression_concurrent_info,
    log_regression_concurrent_error
)


# 简单快速的token估算函数
def estimate_tokens(text: str) -> int:
    """
    使用简单快速的方法估算文本的token数量
    基于经验：1个token约等于3个字符（对于中英文混合文本）
    这个方法虽然不如tiktoken精确，但速度快且稳定
    """
    if not text:
        return 0
    return len(text) // 3


def generate_tasks(ai_client, impact_report_content: str, db: Optional[Session] = None, analysis_task_id: Optional[str] = None) -> Dict[str, Any]:
    """
    调用AI生成任务列表并存储到数据库
    
    Args:
        ai_client: AI客户端实例
        impact_report_content: 影响域分析报告内容
        db: 数据库会话（可选）
        analysis_task_id: 分析任务ID（可选）
        
    Returns:
        Dict[str, Any]: 包含生成结果的字典
    """
    result = {
        "success": False,
        "message": "",
        "tasks": []
    }
    
    # 构建提示词
    prompt = build_task_list_prompt(impact_report_content)
    
    try:
        # 记录提示词到日志（用于调试）
        timestamp = get_timestamp()
        save_prompt_to_log(prompt, f"task_list_prompt_{timestamp}.txt")
        
        # 调试：打印原始 prompt（截断 2000 字）
        try:
            log_regression_concurrent_debug(f"[TaskGenerator] 开始生成任务列表，analysis_task_id={analysis_task_id}")
        except Exception:
            pass
        
        # 调用AI获取任务列表
        call_id = str(uuid.uuid4())[:8]
        log_regression_concurrent_debug(f"[AI分析] 开始生成任务列表 (ID: {call_id})")
        
        try:
            ai_result, raw_response = ai_client.call_ai_stream(prompt)
            
            # 记录AI的原始响应用于调试
            log_regression_concurrent_debug(f"[AI分析] AI原始响应 (ID: {call_id}): {raw_response}")
            log_regression_concurrent_debug(f"[AI分析] AI解析结果 (ID: {call_id}): {ai_result}")
            
        except Exception as e:
            result["message"] = f"调用AI时出错: {str(e)}"
            log_regression_concurrent_error(f"[ERROR] 调用AI时出错 (ID: {call_id}): {e}")
            return result
        
        # 检查AI返回结果是否包含错误信息
        if isinstance(ai_result, dict) and "error" in ai_result:
            error_details = []
            error_details.append(f"AI返回错误: {ai_result.get('error', 'unknown error')}")
            
            if "json_error" in ai_result:
                error_details.append(f"JSON解析错误: {ai_result['json_error']}")
            
            if "raw_content" in ai_result:
                raw_content = ai_result["raw_content"]
                error_details.append(f"原始响应长度: {len(raw_content)} 字符")
                error_details.append(f"原始响应内容: {raw_content[:200]}..." if len(raw_content) > 200 else f"原始响应内容: {raw_content}")
            
            result["message"] = "; ".join(error_details)
            log_regression_concurrent_error(f"[ERROR] AI返回包含错误信息 (ID: {call_id}): {result['message']}")
            return result
        
        # 检查AI返回结果的类型和格式
        if ai_result is None:
            result["message"] = "AI返回结果为None"
            log_regression_concurrent_error(f"[ERROR] AI返回结果为None (ID: {call_id})")
            return result
            
        if not isinstance(ai_result, dict):
            result["message"] = f"AI返回的结果不是字典格式: {type(ai_result)}, 内容: {ai_result}"
            log_regression_concurrent_error(f"[ERROR] AI返回结果类型错误 (ID: {call_id}): {type(ai_result)}, 内容: {ai_result}")
            return result
            
        if "tasks" not in ai_result:
            result["message"] = f"AI返回的结果中缺少'tasks'字段: {list(ai_result.keys())}"
            log_regression_concurrent_error(f"[ERROR] AI返回结果缺少tasks字段 (ID: {call_id}): {ai_result}")
            return result
        
        tasks = ai_result["tasks"]
        log_regression_concurrent_debug(f"[AI分析] 提取到任务列表 (ID: {call_id}): {len(tasks) if isinstance(tasks, list) else 'not a list'} 个任务")
        
        if not isinstance(tasks, list):
            result["message"] = f"AI返回的'tasks'字段不是列表格式: {type(tasks)}"
            log_regression_concurrent_error(f"[ERROR] tasks字段类型错误 (ID: {call_id}): {type(tasks)}, 内容: {tasks}")
            return result
        
        if not tasks:
            result["message"] = "AI返回的任务列表为空"
            result["success"] = True  # 空任务列表也视为成功，但会在日志中警告
            log_regression_concurrent_debug(f"[WARNING] AI返回空任务列表 (ID: {call_id})")
            return result
        
        # 验证任务列表的格式
        validated_tasks = []
        for i, task in enumerate(tasks):
            # 验证必需字段
            if not all(key in task for key in ["task_id", "task_name", "task_description", "change_type"]):
                log_regression_concurrent_debug(f"[WARNING] 任务 {i+1} 缺少必需字段，跳过")
                continue
            
            # 验证change_type
            if task["change_type"] not in ["requirement", "design", "code", "combined"]:
                log_regression_concurrent_debug(f"[WARNING] 任务 {i+1} 的change_type无效: {task['change_type']}，设置为'combined'")
                task["change_type"] = "combined"
            
            validated_task = {
                "task_id": str(task["task_id"]),
                "task_name": task["task_name"],
                "task_description": task["task_description"],
                "change_type": task["change_type"],
                "original_report_content": task.get("original_report_content", "")  # 新增字段
            }
            
            # 兼容旧格式的额外字段
            if "related_change" in task:
                validated_task["related_change"] = task["related_change"]
            if "code_elements" in task:
                validated_task["code_elements"] = task.get("code_elements", [])
            
            validated_tasks.append(validated_task)
        
        # 自动添加一个"其他变更"任务，用于处理不属于已知任务的代码变更
        if validated_tasks:
            # 找到最大的任务ID
            max_task_id = 0
            for task in validated_tasks:
                try:
                    task_id_num = int(task["task_id"])
                    if task_id_num > max_task_id:
                        max_task_id = task_id_num
                except ValueError:
                    # 如果任务ID不是数字，跳过
                    pass
            
            # 创建"其他变更"任务
            other_task_id = str(max_task_id + 1)
            other_task = {
                "task_id": other_task_id,
                "task_name": "其他变更",
                "task_description": "不属于上述任务的其他代码变更，包括未明确分类的修改、重构、优化等",
                "change_type": "combined",
                "original_report_content": "此任务用于收集不属于影响域分析报告中明确提及的其他代码变更"
            }
            validated_tasks.append(other_task)
            log_regression_concurrent_debug(f"[TaskGenerator] 自动添加'其他变更'任务，ID: {other_task_id}")
        
        # 如果提供了数据库会话和分析任务ID，则存储任务到数据库
        if db and analysis_task_id:
            try:
                regression_task_repo = RegressionTaskRepository(db)
                
                # 准备存储到数据库的任务数据
                db_tasks_data = []
                for task in validated_tasks:
                    db_task_data = {
                        "analysis_task_id": analysis_task_id,
                        "task_id": task["task_id"],
                        "task_name": task["task_name"],
                        "task_description": task["task_description"],
                        "change_type": task["change_type"],
                        "original_report_content": task["original_report_content"]  # 新增字段
                    }
                    db_tasks_data.append(db_task_data)
                
                # 批量创建任务
                created_tasks = regression_task_repo.batch_create_tasks(db_tasks_data)
                db.commit()
                
                log_regression_concurrent_debug(f"[TaskGenerator] 成功存储 {len(created_tasks)} 个任务到数据库")
                
            except Exception as e:
                log_regression_concurrent_error(f"[ERROR] 存储任务到数据库时出错: {e}")
                db.rollback()
                # 不影响主要功能，继续返回任务列表
        
        result["tasks"] = validated_tasks
        result["success"] = True
        log_regression_concurrent_debug(f"[TaskGenerator] 成功生成 {len(validated_tasks)} 个任务")
        return result
        
    except Exception as e:
        result["message"] = f"生成任务列表时出错: {str(e)}"
        log_regression_concurrent_error(f"[ERROR] 生成任务列表时出错: {e}")
        return result


def build_task_list_prompt(impact_report_content: str) -> str:
    """
    构建任务列表生成提示词，支持智能token管理和内容分片
    
    Args:
        impact_report_content: 影响域分析报告内容
        
    Returns:
        str: 提示词
    """
    MAX_TOKENS = 15000  # 最大token限制
    
    # 获取基础提示词模板
    base_template = get_task_planning_prompt()
    
    # 计算基础模板的token数（不包含报告内容）
    template_without_content = base_template.replace("{report_content}", "")
    base_tokens = estimate_tokens(template_without_content)
    
    log_regression_concurrent_debug(f"[TOKEN] 基础模板token数: {base_tokens}")
    
    # 计算可用于报告内容的token数
    available_tokens = MAX_TOKENS - base_tokens
    log_regression_concurrent_debug(f"[TOKEN] 可用于报告内容的token数: {available_tokens}")
    
    # 如果基础模板已经超过限制，使用降级模板
    if base_tokens >= MAX_TOKENS:
        log_regression_concurrent_debug(f"[TOKEN] 基础模板超过限制，使用降级模板")
        return _build_fallback_task_prompt(impact_report_content)
    
    # 处理报告内容
    processed_content = _process_report_content(impact_report_content, available_tokens)
    
    # 构建最终提示词 - 使用replace方法避免大括号冲突
    final_prompt = base_template.replace("{report_content}", processed_content)
    final_tokens = estimate_tokens(final_prompt)
    
    log_regression_concurrent_debug(f"[TOKEN] 最终任务生成提示词token数: {final_tokens}")
    
    # 如果仍然超过限制，进一步压缩
    if final_tokens > MAX_TOKENS:
        log_regression_concurrent_debug(f"[TOKEN] 最终提示词超过限制，进一步压缩")
        compressed_content = _compress_report_content(impact_report_content, available_tokens // 2)
        final_prompt = base_template.replace("{report_content}", compressed_content)
        
        final_tokens = estimate_tokens(final_prompt)
        log_regression_concurrent_debug(f"[TOKEN] 压缩后提示词token数: {final_tokens}")
        
        # 如果还是超过限制，使用降级提示词
        if final_tokens > MAX_TOKENS:
            log_regression_concurrent_debug(f"[TOKEN] 仍然超过限制，使用降级提示词")
            return _build_fallback_task_prompt(impact_report_content)
    
    return final_prompt


def _process_report_content(report_content: str, max_tokens: int) -> str:
    """
    智能处理报告内容，确保在token限制内
    
    策略：
    1. 优先保留章节标题和结构
    2. 保留关键的变更描述
    3. 压缩重复或冗余内容
    """
    if not report_content:
        return ""
    
    # 估算当前内容的token数
    current_tokens = estimate_tokens(report_content)
    
    if current_tokens <= max_tokens:
        log_regression_concurrent_debug(f"[TOKEN] 报告内容在限制内，token数: {current_tokens}")
        return report_content
    
    log_regression_concurrent_debug(f"[TOKEN] 报告内容超过限制，当前: {current_tokens}, 限制: {max_tokens}")
    
    # 按行分割内容
    lines = report_content.split('\n')
    
    # 识别重要行（章节标题、变更描述等）
    important_lines = []
    section_lines = []
    content_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 章节标题（包含数字编号的行）
        if any(pattern in line for pattern in ['3.1', '3.2', '3.3', '需求变更', '设计变更', '代码变更']):
            important_lines.append(line)
        # 子标题
        elif line.startswith('**') and line.endswith('**'):
            section_lines.append(line)
        # 普通内容
        else:
            content_lines.append(line)
    
    # 按优先级组装内容
    result_lines = []
    
    # 1. 首先添加重要的章节标题
    result_lines.extend(important_lines)
    
    # 2. 计算剩余可用token
    current_content = '\n'.join(result_lines)
    used_tokens = estimate_tokens(current_content)
    remaining_tokens = max_tokens - used_tokens
    
    # 3. 按优先级添加子标题和内容
    for line in section_lines + content_lines:
        line_tokens = estimate_tokens(line + '\n')
        if used_tokens + line_tokens <= max_tokens:
            result_lines.append(line)
            used_tokens += line_tokens
        else:
            break
    
    processed_content = '\n'.join(result_lines)
    
    # 如果内容被截断，添加说明
    if len(result_lines) < len(lines):
        processed_content += '\n\n...(报告内容过长，已智能截断，保留了关键章节和变更信息)'
    
    final_tokens = estimate_tokens(processed_content)
    log_regression_concurrent_debug(f"[TOKEN] 处理后报告内容token数: {final_tokens}")
    
    return processed_content


def _compress_report_content(report_content: str, max_tokens: int) -> str:
    """
    进一步压缩报告内容
    只保留最核心的变更信息
    """
    if not report_content:
        return ""
    
    lines = report_content.split('\n')
    essential_lines = []
    
    # 只保留包含关键词的行
    keywords = ['变更', '需求', '设计', '代码', '3.1', '3.2', '3.3', '新增', '修改', '删除']
    
    for line in lines:
        line = line.strip()
        if any(keyword in line for keyword in keywords):
            essential_lines.append(line)
    
    # 如果压缩后的内容仍然太长，进一步截断
    compressed_content = '\n'.join(essential_lines)
    current_tokens = estimate_tokens(compressed_content)
    
    if current_tokens > max_tokens:
        # 按字符数截断
        max_chars = max_tokens * 3  # 粗略估算
        compressed_content = compressed_content[:max_chars]
        compressed_content += '\n\n...(内容已大幅压缩)'
    
    final_tokens = estimate_tokens(compressed_content)
    log_regression_concurrent_debug(f"[TOKEN] 压缩后报告内容token数: {final_tokens}")
    
    return compressed_content


def _build_fallback_task_prompt(report_content: str) -> str:
    """
    构建降级任务提示词，当正常提示词超过token限制时使用
    使用最简化的提示词格式
    """
    log_regression_concurrent_debug(f"[TOKEN] 构建降级任务提示词")
    
    # 提取报告中最重要的信息
    essential_info = _extract_essential_changes(report_content)
    
    # 构建最简化的提示词
    fallback_prompt = f"""请分析以下变更信息并提取任务：

{essential_info}

请以JSON格式返回任务列表：
{{
  "tasks": [
    {{
      "task_id": "1",
      "task_name": "任务名称",
      "task_description": "任务描述",
      "change_type": "requirement|design|code|combined"
    }}
  ]
}}

如果没有明确的变更，返回空数组。
"""
    
    final_tokens = estimate_tokens(fallback_prompt)
    log_regression_concurrent_debug(f"[TOKEN] 降级任务提示词token数: {final_tokens}")
    
    return fallback_prompt


def _extract_essential_changes(report_content: str) -> str:
    """
    从报告中提取最核心的变更信息
    """
    if not report_content:
        return "无变更信息"
    
    lines = report_content.split('\n')
    essential_lines = []
    
    # 查找包含具体变更的行
    change_keywords = ['新增', '修改', '删除', '变更', '增加', '改进', '优化']
    
    for line in lines:
        line = line.strip()
        if any(keyword in line for keyword in change_keywords) and len(line) > 10:
            essential_lines.append(line)
            
            # 限制提取的行数
            if len(essential_lines) >= 20:
                break
    
    if not essential_lines:
        # 如果没有找到具体变更，返回前500字符
        return report_content[:500] + "...(已截断)"
    
    result = '\n'.join(essential_lines)
    
    # 确保不超过1000字符
    if len(result) > 1000:
        result = result[:1000] + "...(已截断)"
    
    return result


def extract_files_from_code_elements(code_elements: List[Dict[str, Any]]) -> List[str]:
    """
    从code_elements结构中提取文件路径列表
    
    Args:
        code_elements: 代码元素列表，包含文件路径和函数名
        
    Returns:
        List[str]: 文件路径列表
    """
    return [element["file_path"] for element in code_elements if "file_path" in element]


def get_timestamp() -> str:
    """获取时间戳"""
    import datetime
    now = datetime.datetime.now()
    return now.strftime("%Y%m%d_%H%M%S_%f")


def save_prompt_to_log(prompt: str, filename: str) -> None:
    """保存提示词到日志文件"""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.abspath(os.path.join(base_dir, '..', '..', '..', '..', '..', '..'))
        log_dir = os.path.join(backend_dir, 'app', 'logs', 'prompts')
        os.makedirs(log_dir, exist_ok=True)
        
        log_path = os.path.join(log_dir, filename)
        
        # 构建JSON结构
        prompt_data = {
            "model": "Qwen/Qwen3-32B",  # 假设使用此模型，根据实际情况修改
            "temperature": 0.1,
            "max_tokens": 8192,
            "system_prompt": None,
            "prompt": prompt,
            "timestamp": get_timestamp()
        }
        
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(prompt_data, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        log_regression_concurrent_error(f"[ERROR] 保存提示词到日志时出错: {e}") 