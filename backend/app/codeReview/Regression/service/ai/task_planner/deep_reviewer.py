"""
分条目深度审查器
负责对已精确映射的变更条目进行详细的代码质量和回归风险审查
"""
import os
import json
import uuid
import re
from typing import Dict, Any, List, Optional

from ..prompt.deepReviewPrompt import get_deep_review_prompt
# ProblemRepository 将在函数内部导入


def log_debug(msg):
    """记录调试日志"""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.abspath(os.path.join(base_dir, '..', '..', '..', '..', '..', '..'))
        log_dir = os.path.join(backend_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, 'bg_debug.txt')
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        # Suppress logging errors if path resolution or writing fails
        pass


def log_to_task_folder(msg, task_id=None):
    """记录日志到任务特定的文件夹"""
    try:
        # 获取当前任务的日志文件夹路径
        base_dir = os.path.dirname(os.path.abspath(__file__))
        regression_dir = os.path.abspath(os.path.join(base_dir, '..', '..'))
        logs_dir = os.path.join(regression_dir, 'logs')
        
        # 查找最新的任务日志文件夹
        if task_id:
            # 如果提供了task_id，查找包含该ID的文件夹
            task_folders = [f for f in os.listdir(logs_dir) if os.path.isdir(os.path.join(logs_dir, f)) and task_id in f]
        else:
            # 否则查找所有regression_task开头的文件夹
            task_folders = [f for f in os.listdir(logs_dir) if os.path.isdir(os.path.join(logs_dir, f)) and f.startswith('regression_task_')]
        
        if task_folders:
            # 使用最新的文件夹（按文件夹名排序）
            latest_folder = sorted(task_folders)[-1]
            task_log_dir = os.path.join(logs_dir, latest_folder)
            
            # 写入到deep_reviewer_ai.log文件
            log_path = os.path.join(task_log_dir, 'deep_reviewer_ai.log')
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(msg + "\n")
        else:
            # 如果找不到任务文件夹，回退到bg_debug.txt
            log_debug(msg)
    except Exception:
        # 如果出错，回退到bg_debug.txt
        log_debug(msg)


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


def perform_deep_review(
    ai_client,
    task: Dict[str, Any],
    task_mappings: List[Dict[str, Any]],
    impact_report_content: str,
    db,
    task_id: int,
    file_id: int
) -> Dict[str, Any]:
    """
    对特定任务进行深度审查
    
    Args:
        ai_client: AI客户端实例
        task: 任务信息
        task_mappings: 该任务的所有映射结果
        impact_report_content: 影响域分析报告内容
        db: 数据库会话
        task_id: 数据库任务ID
        file_id: 数据库文件ID
        
    Returns:
        Dict[str, Any]: 审查结果
    """
    result = {
        "success": False,
        "message": "",
        "issues_count": 0
    }
    
    try:
        if not task_mappings:
            log_debug(f"[DeepReviewer] 任务 {task.get('task_id')} 没有映射的代码变更")
            result["success"] = True
            return result
        
        log_debug(f"[DeepReviewer] 开始深度审查任务: {task.get('task_id')}")
        
        # 构建深度审查提示词
        prompt = build_deep_review_prompt(
            task,
            task_mappings,
            impact_report_content
        )
        
        # 记录提示词到日志（用于调试）
        timestamp = get_timestamp()
        save_prompt_to_log(prompt, f"deep_review_prompt_{timestamp}.txt")
        
        # 调用AI进行深度审查
        call_id = str(uuid.uuid4())[:8]
        log_debug(f"[AI分析] 开始深度审查 (ID: {call_id}, Task: {task.get('task_id')})")
        
        # 记录完整的AI请求信息到线程日志文件（不省略任何内容）
        from ....utils.concurrent_logger import log_regression_concurrent_debug
        
        log_regression_concurrent_debug(f"[DeepReviewer AI Request {call_id}] === COMPLETE REQUEST START ===", "deep_reviewer")
        log_regression_concurrent_debug(f"[DeepReviewer AI Request {call_id}] Task ID: {task.get('task_id')}", "deep_reviewer")
        log_regression_concurrent_debug(f"[DeepReviewer AI Request {call_id}] Task Name: {task.get('task_name')}", "deep_reviewer")
        log_regression_concurrent_debug(f"[DeepReviewer AI Request {call_id}] Mappings Count: {len(task_mappings)}", "deep_reviewer")
        log_regression_concurrent_debug(f"[DeepReviewer AI Request {call_id}] Prompt Length: {len(prompt)} characters", "deep_reviewer")
        log_regression_concurrent_debug(f"[DeepReviewer AI Request {call_id}] Full Prompt Content:", "deep_reviewer")
        log_regression_concurrent_debug(f"[DeepReviewer AI Request {call_id}] {prompt}", "deep_reviewer")
        log_regression_concurrent_debug(f"[DeepReviewer AI Request {call_id}] === COMPLETE REQUEST END ===", "deep_reviewer")
        
        ai_result, _ = ai_client.call_ai_stream(prompt)
        
        # 记录完整的AI响应信息到线程日志文件（不省略任何内容）
        log_regression_concurrent_debug(f"[DeepReviewer AI Response {call_id}] === COMPLETE RESPONSE START ===", "deep_reviewer")
        log_regression_concurrent_debug(f"[DeepReviewer AI Response {call_id}] Raw Response Type: {type(ai_result)}", "deep_reviewer")
        log_regression_concurrent_debug(f"[DeepReviewer AI Response {call_id}] Raw Response Content:", "deep_reviewer")
        log_regression_concurrent_debug(f"[DeepReviewer AI Response {call_id}] {ai_result}", "deep_reviewer")
        log_regression_concurrent_debug(f"[DeepReviewer AI Response {call_id}] === COMPLETE RESPONSE END ===", "deep_reviewer")
        
        if not isinstance(ai_result, dict):
            result["message"] = f"AI返回的审查结果格式不正确: {ai_result}"
            return result
        
        # 验证AI返回的结果格式 - 使用新的problems格式
        if "problems" not in ai_result:
            result["message"] = "AI返回结果缺少problems字段"
            return result
        
        problems = ai_result["problems"]
        if not isinstance(problems, list):
            result["message"] = "problems字段格式不正确"
            return result
        
        # 提取问题列表
        issues = problems
        if issues:
            # 添加调试信息
            log_debug(f"[DeepReviewer] 任务 {task.get('task_id')} AI返回结果: {ai_result}")
            for i, issue in enumerate(issues):
                issue_level = issue.get("issue_level", "")
                log_debug(f"[DeepReviewer] 问题 {i+1}: issue_level='{issue_level}', issue_name='{issue.get('issue_name', '')}'")
            
            # 保存问题到数据库
            save_review_issues(db, issues, task, task_id, file_id, task_mappings)
            log_debug(f"[DeepReviewer] 任务 {task.get('task_id')} 发现 {len(issues)} 个问题")
        else:
            log_debug(f"[DeepReviewer] 任务 {task.get('task_id')} 未发现问题")
        
        result["success"] = True
        result["issues_count"] = len(issues)
        result["problems"] = problems
        return result
        
    except Exception as e:
        log_debug(f"[ERROR] 深度审查任务 {task.get('task_id')} 时出错: {e}")
        result["message"] = f"深度审查时出错: {str(e)}"
        return result


def build_deep_review_prompt(
    task: Dict[str, Any],
    task_mappings: List[Dict[str, Any]],
    impact_report_content: str = None  # 保留参数兼容性，但不再使用
) -> str:
    """
    构建深度审查提示词，支持智能token管理和内容分片
    现在使用任务中存储的original_report_content而不是完整的影响域分析报告
    
    Args:
        task: 任务信息（包含original_report_content）
        task_mappings: 任务映射结果
        impact_report_content: 影响域分析报告内容（已弃用，保留兼容性）
        
    Returns:
        str: 提示词
    """
    MAX_TOKENS = 15000  # 最大token限制
    
    # 构建基础提示词部分
    task_info = f"""任务ID: {task.get('task_id')}
任务名称: {task.get('task_name')}
任务描述: {task.get('task_description')}
变更类型: {task.get('change_type')}
"""
    
    # 使用任务中存储的原始报告内容
    original_report_content = task.get('original_report_content', '')
    if not original_report_content:
        log_debug(f"[WARNING] 任务 {task.get('task_id')} 没有原始报告内容，将使用空内容")
        original_report_content = "无对应的影响域分析报告内容"
    
    # 构建基础提示词（不包含代码变更）
    base_prompt = get_deep_review_prompt(task_info, original_report_content, "")
    base_tokens = estimate_tokens(base_prompt)
    
    log_debug(f"[TOKEN] 基础提示词token数: {base_tokens}")
    
    # 如果基础提示词已经超过限制，尝试压缩原始报告内容
    if base_tokens >= MAX_TOKENS:
        log_debug(f"[TOKEN] 基础提示词超过限制，尝试压缩原始报告内容")
        # 压缩原始报告内容到最多2000字符
        compressed_content = original_report_content[:2000] if len(original_report_content) > 2000 else original_report_content
        if len(original_report_content) > 2000:
            compressed_content += "\n...(内容过长已截断)"
        
        base_prompt = get_deep_review_prompt(task_info, compressed_content, "")
        base_tokens = estimate_tokens(base_prompt)
        log_debug(f"[TOKEN] 压缩后基础提示词token数: {base_tokens}")
        
        # 如果仍然超过限制，返回降级提示词
        if base_tokens >= MAX_TOKENS:
            log_debug(f"[TOKEN] 基础提示词仍然超过限制，使用降级提示词")
            return _build_fallback_prompt(task, task_mappings)
    
    # 计算可用于代码变更的token数
    available_tokens = MAX_TOKENS - base_tokens
    log_debug(f"[TOKEN] 可用于代码变更的token数: {available_tokens}")
    
    # 按文件组织代码变更，并计算每个变更的token数
    file_changes = {}
    change_tokens = []
    
    for mapping in task_mappings:
        file_path = mapping.get("file_path")
        if file_path not in file_changes:
            file_changes[file_path] = []
        file_changes[file_path].append(mapping)
    
    # 为每个变更计算token数和优先级
    for file_path, mappings in file_changes.items():
        for mapping in mappings:
            change_section = _build_single_change_section(mapping, file_path)
            change_token_count = estimate_tokens(change_section)
            
            # 计算优先级（高置信度的映射优先级更高）
            confidence = mapping.get("mapping_confidence", "low")
            confidence_score = {"high": 3, "medium": 2, "low": 1}.get(confidence, 1)
            
            change_tokens.append({
                "section": change_section,
                "tokens": change_token_count,
                "priority": confidence_score,
                "file_path": file_path,
                "function_name": mapping.get("function_name", "unknown"),
                "mapping": mapping
            })
    
    # 按优先级和token数排序（优先级高的在前，同优先级下token数少的在前）
    change_tokens.sort(key=lambda x: (-x["priority"], x["tokens"]))
    
    # 智能选择代码变更，应用多种策略
    selected_changes = _select_changes_with_strategies(change_tokens, available_tokens)
    
    # 构建最终的代码变更部分
    code_changes_section = "".join([change["section"] for change in selected_changes])
    
    # 构建最终提示词
    final_prompt = get_deep_review_prompt(task_info, original_report_content, code_changes_section)
    final_tokens = estimate_tokens(final_prompt)
    
    log_debug(f"[TOKEN] 最终提示词token数: {final_tokens}, 包含 {len(selected_changes)} 个代码变更")
    
    # 如果仍然超过限制，尝试进一步压缩
    if final_tokens > MAX_TOKENS:
        log_debug(f"[TOKEN] 最终提示词超过限制，尝试进一步压缩")
        return _compress_prompt_further(task, selected_changes, original_report_content, MAX_TOKENS)
    
    return final_prompt


def _build_single_change_section(mapping: Dict[str, Any], file_path: str) -> str:
    """构建单个代码变更的文本部分"""
    function_name = mapping.get("function_name", "unknown")
    change_type = mapping.get("change_type", "unknown")
    mapping_confidence = mapping.get("mapping_confidence", "unknown")
    mapping_reason = mapping.get("mapping_reason", "")
    old_code = mapping.get("old_code", "")
    new_code = mapping.get("new_code", "")
    diff_summary = mapping.get("diff_summary", "")
    
    section = f"### 文件: {file_path}\n"
    section += f"#### 函数: {function_name} ({change_type})\n"
    section += f"**映射置信度**: {mapping_confidence}\n"
    section += f"**映射原因**: {mapping_reason}\n\n"
    
    if old_code:
        section += f"**旧版本代码**:\n```c\n{old_code}\n```\n\n"
    
    if new_code:
        section += f"**新版本代码**:\n```c\n{new_code}\n```\n\n"
    
    if diff_summary:
        section += f"**变更摘要**: {diff_summary}\n\n"
    
    return section


def _select_changes_with_strategies(change_tokens: List[Dict], available_tokens: int) -> List[Dict]:
    """
    使用多种策略智能选择代码变更
    
    策略优先级：
    1. 优先选择高置信度的变更
    2. 确保每个文件至少有一个变更被包含
    3. 在token限制内尽可能包含更多变更
    """
    selected_changes = []
    used_tokens = 0
    included_files = set()
    
    # 策略1: 优先包含高置信度变更
    high_priority_changes = [c for c in change_tokens if c["priority"] == 3]
    for change in high_priority_changes:
        if used_tokens + change["tokens"] <= available_tokens:
            selected_changes.append(change)
            used_tokens += change["tokens"]
            included_files.add(change["file_path"])
            log_debug(f"[TOKEN] 添加高优先级变更 {change['file_path']}::{change['function_name']}, token数: {change['tokens']}")
        else:
            log_debug(f"[TOKEN] 跳过高优先级变更 {change['file_path']}::{change['function_name']}, token数: {change['tokens']}, 会超过限制")
    
    # 策略2: 确保每个文件至少有一个变更
    remaining_changes = [c for c in change_tokens if c not in selected_changes]
    for change in remaining_changes:
        if change["file_path"] not in included_files:
            if used_tokens + change["tokens"] <= available_tokens:
                selected_changes.append(change)
                used_tokens += change["tokens"]
                included_files.add(change["file_path"])
                log_debug(f"[TOKEN] 添加文件覆盖变更 {change['file_path']}::{change['function_name']}, token数: {change['tokens']}")
            else:
                # 如果完整变更太大，尝试压缩版本
                compressed_change = _compress_single_change(change, available_tokens - used_tokens)
                if compressed_change:
                    selected_changes.append(compressed_change)
                    used_tokens += compressed_change["tokens"]
                    included_files.add(change["file_path"])
                    log_debug(f"[TOKEN] 添加压缩的文件覆盖变更 {change['file_path']}::{change['function_name']}")
    
    # 策略3: 在剩余token范围内添加更多变更
    remaining_changes = [c for c in change_tokens if c not in selected_changes]
    for change in remaining_changes:
        if used_tokens + change["tokens"] <= available_tokens:
            selected_changes.append(change)
            used_tokens += change["tokens"]
            log_debug(f"[TOKEN] 添加额外变更 {change['file_path']}::{change['function_name']}, token数: {change['tokens']}")
    
    log_debug(f"[TOKEN] 最终选择了 {len(selected_changes)} 个变更，总token数: {used_tokens}")
    return selected_changes


def _compress_single_change(change: Dict, max_tokens: int) -> Dict:
    """压缩单个代码变更以适应token限制"""
    mapping = change["mapping"]
    file_path = change["file_path"]
    
    # 构建最小化版本
    function_name = mapping.get("function_name", "unknown")
    change_type = mapping.get("change_type", "unknown")
    mapping_confidence = mapping.get("mapping_confidence", "unknown")
    
    # 只保留最重要的信息
    compressed_section = f"### 文件: {file_path}\n"
    compressed_section += f"#### 函数: {function_name} ({change_type}, 置信度: {mapping_confidence})\n"
    
    # 优先保留新版本代码，如果太长则截断
    new_code = mapping.get("new_code", "")
    if new_code:
        # 估算代码部分的token数
        code_prefix = "**新版本代码**:\n```c\n"
        code_suffix = "\n```\n\n"
        overhead_tokens = estimate_tokens(compressed_section + code_prefix + code_suffix)
        
        available_for_code = max_tokens - overhead_tokens
        if available_for_code > 100:  # 至少保留100个token的代码
            # 截断代码以适应token限制
            max_code_chars = available_for_code * 3  # 粗略估算
            if len(new_code) > max_code_chars:
                truncated_code = new_code[:max_code_chars] + "\n// ... (代码过长已截断)"
            else:
                truncated_code = new_code
            
            compressed_section += f"{code_prefix}{truncated_code}{code_suffix}"
            
            final_tokens = estimate_tokens(compressed_section)
            if final_tokens <= max_tokens:
                return {
                    "section": compressed_section,
                    "tokens": final_tokens,
                    "priority": change["priority"],
                    "file_path": file_path,
                    "function_name": function_name,
                    "mapping": mapping
                }
    
    return None


def _compress_prompt_further(
    task: Dict[str, Any], 
    selected_changes: List[Dict], 
    original_report_content: str, 
    max_tokens: int
) -> str:
    """进一步压缩提示词"""
    log_debug(f"[TOKEN] 进一步压缩提示词，当前变更数: {len(selected_changes)}")
    
    # 如果变更太多，只保留最重要的一半
    if len(selected_changes) > 1:
        selected_changes = selected_changes[:len(selected_changes)//2]
        log_debug(f"[TOKEN] 减少变更数量到: {len(selected_changes)}")
    
    # 进一步压缩原始报告内容
    compressed_content = original_report_content[:1000] if len(original_report_content) > 1000 else original_report_content
    if len(original_report_content) > 1000:
        compressed_content += "\n...(内容已大幅压缩)"
    
    # 重新构建
    task_info = f"""任务ID: {task.get('task_id')}
任务名称: {task.get('task_name')}
变更类型: {task.get('change_type')}
"""
    
    code_changes_section = "".join([change["section"] for change in selected_changes])
    final_prompt = get_deep_review_prompt(task_info, compressed_content, code_changes_section)
    
    final_tokens = estimate_tokens(final_prompt)
    log_debug(f"[TOKEN] 进一步压缩后token数: {final_tokens}")
    
    # 如果还是超过限制，使用降级提示词
    if final_tokens > max_tokens:
        log_debug(f"[TOKEN] 仍然超过限制，使用降级提示词")
        return _build_fallback_prompt(task, [change["mapping"] for change in selected_changes[:1]])
    
    return final_prompt


def _build_fallback_prompt(task: Dict[str, Any], task_mappings: List[Dict[str, Any]]) -> str:
    """
    构建降级提示词，当正常提示词超过token限制时使用
    只包含最基本的信息和最重要的一个代码变更
    """
    log_debug(f"[TOKEN] 构建降级提示词")
    
    # 最小化的任务信息
    task_info = f"任务: {task.get('task_name', 'unknown')}"
    
    # 只保留第一个最重要的变更
    code_changes = ""
    if task_mappings:
        mapping = task_mappings[0]
        function_name = mapping.get("function_name", "unknown")
        new_code = mapping.get("new_code", "")
        
        if new_code:
            # 截断代码到最多500个字符
            if len(new_code) > 500:
                new_code = new_code[:500] + "\n// ... (已截断)"
            
            code_changes = f"函数 {function_name} 的新版本代码:\n```c\n{new_code}\n```"
    
    # 构建最简化的提示词
    fallback_prompt = f"""你是代码审查专家。请审查以下代码变更：

{task_info}

{code_changes}

请以JSON格式返回发现的问题：
{{"problems": [...]}}

如果没有问题，返回 {{"problems": []}}
"""
    
    final_tokens = estimate_tokens(fallback_prompt)
    log_debug(f"[TOKEN] 降级提示词token数: {final_tokens}")
    
    return fallback_prompt


def save_review_issues(
    db,
    issues: List[Dict[str, Any]],
    task: Dict[str, Any],
    task_id: int,
    file_id: int,
    task_mappings: List[Dict[str, Any]]
) -> None:
    """
    保存审查问题到数据库
    
    Args:
        db: 数据库会话
        issues: 问题列表
        task: 任务信息
        task_id: 数据库任务ID
        file_id: 数据库文件ID
        task_mappings: 任务映射结果
    """
    from ....db.repository.problem_repo import ProblemRepository
    from ....db.repository.function_repo import FunctionRepository
    
    prob_repo = ProblemRepository(db)
    func_repo = FunctionRepository(db)
    
    # 获取回归测试任务ID
    regression_task_id = task.get("task_id")  # 这是回归测试任务的ID
    
    for issue in issues:
        try:
            # 根据问题位置信息找到对应的文件和函数
            location = issue.get("location", "")
            file_name = ""
            source_code = ""
            
            # 尝试从映射结果中找到相关的代码
            for mapping in task_mappings:
                if mapping.get("function_name") in location or mapping.get("file_path") in location:
                    file_name = mapping.get("file_path", "")
                    # 从diff信息中提取源代码
                    diff_info = mapping.get("diff_info", {})
                    functions = diff_info.get("functions", [])
                    for func_info in functions:
                        if func_info.get("function_name") == mapping.get("function_name"):
                            source_code = func_info.get("new_code", func_info.get("old_code", ""))
                            break
                    break
            
            # 处理violation_rules字段 - 将列表转换为字符串
            violation_rules = issue.get("violation_rules", "")
            if isinstance(violation_rules, list):
                violation_rules = "; ".join(violation_rules)  # 用分号分隔多个规则
            elif not isinstance(violation_rules, str):
                violation_rules = str(violation_rules)
            
            # 创建函数记录
            function_name = issue.get("issue_location", "unknown_function")
            if ":" in function_name:
                function_name = function_name.split(":")[-1]
            
            # 先查找是否已存在该函数
            existing_func = func_repo.get_function_by_file_and_name(file_id, function_name)
            if existing_func:
                function_record = existing_func
            else:
                function_data = {
                    "file_id": file_id,
                    "function_name": function_name,
                    "start_line": 1,  # 默认值
                    "end_line": 10,   # 默认值
                    "source_code": issue.get("source_code", source_code),
                    "analyzed": True,
                    "file_path": issue.get("file_name", file_name)
                }
                function_record = func_repo.create_function(function_data)
            
            # 构建问题数据 - 使用新的JSON格式字段
            problem_data = {
                "task_id": task_id,
                "file_id": file_id,
                "function_id": function_record.id,
                "regression_task_id": regression_task_id,  # 添加回归测试任务ID
                "file_name": issue.get("file_name", file_name),
                "source_code": issue.get("source_code", source_code),
                "violation_rules": violation_rules,
                "issue_level": issue.get("issue_level", ""),
                "issue_name": issue.get("issue_name", ""),
                "issue_location": issue.get("issue_location", location),
                "description_requirement": issue.get("description_requirement", task.get("task_description", "")),
                "description_issue": issue.get("description_issue", ""),
                "description_location": issue.get("description_location", location),
                "description_impact": issue.get("description_impact", "")
            }
            
            log_debug(f"[DeepReviewer] 保存问题数据: issue_level='{issue.get('issue_level', '')}', problem_data={problem_data}")
            
            # 创建问题记录
            prob_repo.create_problem(problem_data)
            
        except Exception as e:
            log_debug(f"[ERROR] 保存问题时出错: {e}")
            continue
    
    db.commit()


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
            "model": "Qwen/Qwen3-32B",
            "temperature": 0.1,
            "max_tokens": 8192,
            "system_prompt": None,
            "prompt": prompt,
            "timestamp": get_timestamp()
        }
        
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(prompt_data, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        log_debug(f"[ERROR] 保存提示词到日志时出错: {e}") 