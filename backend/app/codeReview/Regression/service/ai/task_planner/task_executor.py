# Task Executor
"""
任务执行器模块
负责执行回归测试的单个审查任务
"""
import os
import json
import uuid
from typing import Dict, Any, List

# 修复导入路径，使用绝对导入而不是相对导入
from app.codeReview.Regression.db.repository.analysis_task_repo import AnalysisTaskRepository
from app.codeReview.Regression.db.repository.regression_task_repo import RegressionTaskRepository
from app.codeReview.Regression.db.repository.diff_mapping_repo import DiffMappingRepository
from app.codeReview.Regression.service.ai.prompt.deepReviewPrompt import get_deep_review_prompt
from app.codeReview.Regression.service.ai.rules.codeReview import get_rules
from app.codeReview.Regression.service.ai.parser import collect_function_with_dependencies  # noqa: E402
from app.utils.log_utils import log_debug


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


def execute_review_task(
    ai_client, 
    task: Dict[str, Any], 
    extract_path: str, 
    impact_report_content: str,
    db,
    task_id: int,
    file_id: int,
    all_tasks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    执行单个审查任务
    
    Args:
        ai_client: AI客户端实例
        task: 任务信息
        extract_path: 解压路径
        impact_report_content: 影响域分析报告内容
        db: 数据库会话
        task_id: 任务ID
        file_id: 文件ID
        all_tasks: 所有任务列表
        
    Returns:
        Dict[str, Any]: 包含执行结果的字典
    """
    result = {
        "success": False,
        "message": "",
        "problems": []
    }
    
    try:
        # 1. 获取需要的文件和函数映射
        file_functions_map = get_required_files(ai_client, task, impact_report_content, all_tasks)
        if not file_functions_map:
            log_debug(f"[WARNING] 任务 {task.get('task_id')} 没有需要审查的文件")
            result["success"] = True  # 没有文件也视为成功
            return result
        
        # 2. 获取文件的代码差异
        from app.codeReview.Regression.service.ai.ai_tools.diff_analyzer import DiffAnalyzer
        diff_analyzer = DiffAnalyzer(db)
        file_diffs = diff_analyzer.get_file_diffs(
            extract_path, 
            file_functions_map, 
            task.get("related_change", "")
        )
        
        if not file_diffs:
            log_debug(f"[WARNING] 任务 {task.get('task_id')} 没有找到代码差异")
            result["success"] = True  # 没有差异也视为成功
            return result
        
        # 3. 执行代码审查
        problems = perform_code_review(ai_client, task, impact_report_content, file_diffs, extract_path)
        
        if problems:
            # 4. 保存问题
            save_problems(db, problems, task, task_id, file_id)
            log_debug(f"任务 {task.get('task_id')} 发现 {len(problems)} 个问题")
        else:
            log_debug(f"任务 {task.get('task_id')} 未发现问题")
        
        result["success"] = True
        result["problems"] = problems
        return result
        
    except Exception as e:
        log_debug(f"[ERROR] 执行任务 {task.get('task_id')} 时出错: {e}")
        result["message"] = f"执行任务时出错: {str(e)}"
        return result


def get_required_files(
    ai_client, 
    task: Dict[str, Any], 
    impact_report_content: str,
    all_tasks: List[Dict[str, Any]]
) -> Dict[str, List[str]]:
    """
    获取任务所需的文件和函数列表
    
    Args:
        ai_client: AI客户端实例
        task: 任务信息
        impact_report_content: 影响域分析报告内容
        all_tasks: 所有任务列表
        
    Returns:
        Dict[str, List[str]]: 文件路径到函数列表的映射
    """
    # 如果任务中已包含code_elements，直接使用
    if "code_elements" in task and task["code_elements"]:
        # 转换为文件到函数列表的映射
        result = {}
        for element in task["code_elements"]:
            if "file_path" in element:
                result[element["file_path"]] = element.get("functions", [])
        return result
    
    # 兼容旧格式 - 如果有files_needed但没有code_elements
    if "files_needed" in task and task["files_needed"]:
        return {file_path: [] for file_path in task["files_needed"]}
    
    # 否则，请求AI确定所需文件和函数
    from app.codeReview.Regression.service.ai.prompt.taskPlanningPrompt import get_task_planning_prompt
    system_prompt = get_task_planning_prompt()
    
    prompt = f"""{system_prompt}

# 文件与函数确认阶段

当前你正在执行以下任务：
任务ID: {task.get('task_id', 'unknown')}
任务名称: {task.get('task_name', 'unknown')}
任务描述: {task.get('task_description', 'unknown')}
相关变更: {task.get('related_change', 'unknown')}

## 影响域分析报告内容：
{impact_report_content}

## 所有任务列表：
{json.dumps(all_tasks, indent=2, ensure_ascii=False)}

请基于以上任务和影响域分析报告，确定完成此审查任务所需的代码文件和函数列表。

请以JSON格式输出文件和函数列表：
```json
{{
  "code_elements": [
    {{
      "file_path": "完整的文件路径1",
      "functions": ["函数名1", "函数名2"]
    }},
    {{
      "file_path": "完整的文件路径2",
      "functions": ["函数名3"]
    }}
  ],
  "explanation": "简要说明为什么需要审查这些特定文件和函数"
}}
```

请确保文件路径尽可能精确，并考虑影响域分析报告中提到的相关文件和函数。
"""
    
    try:
        # 记录提示词到日志（用于调试）
        timestamp = get_timestamp()
        save_prompt_to_log(prompt, f"file_list_prompt_{timestamp}.txt")
        
        # 调用AI获取文件列表
        call_id = str(uuid.uuid4())[:8]
        log_debug(f"[AI分析] 开始获取文件和函数列表 (ID: {call_id})")
        
        ai_result, _ = ai_client.call_ai_stream(prompt)
        
        if isinstance(ai_result, dict) and "code_elements" in ai_result:
            code_elements = ai_result["code_elements"]
            if code_elements:
                # 转换为文件到函数列表的映射
                result = {}
                for element in code_elements:
                    if "file_path" in element:
                        result[element["file_path"]] = element.get("functions", [])
                
                log_debug(f"AI确定的文件和函数列表: {result}")
                return result
        
        # 兼容旧格式响应
        if isinstance(ai_result, dict) and "files_needed" in ai_result:
            files = ai_result["files_needed"]
            if files:
                result = {file_path: [] for file_path in files}
                log_debug(f"AI确定的文件列表(旧格式): {files}")
                return result
        
        log_debug(f"[WARNING] 获取文件和函数列表失败，使用空字典")
        return {}
            
    except Exception as e:
        log_debug(f"[ERROR] 获取文件和函数列表时出错: {e}")
        return {}


def perform_code_review(
    ai_client, 
    task: Dict[str, Any], 
    impact_report_content: str,
    file_diffs: Dict[str, Any],
    extract_path: str,
) -> List[Dict[str, Any]]:
    """
    执行代码审查
    
    Args:
        ai_client: AI客户端实例
        task: 任务信息
        impact_report_content: 影响域分析报告内容
        file_diffs: 文件差异信息
        extract_path: 解压路径
        
    Returns:
        List[Dict[str, Any]]: 发现的问题列表
    """
    # 构建代码审查提示词
    prompt = build_code_review_prompt(task, impact_report_content, file_diffs, extract_path)
    
    try:
        # 记录提示词到日志（用于调试）
        timestamp = get_timestamp()
        save_prompt_to_log(prompt, f"code_review_prompt_{timestamp}.txt")
        
        # 调用AI进行代码审查
        call_id = str(uuid.uuid4())[:8]
        log_debug(f"[AI分析] 开始代码审查 (ID: {call_id})")
        
        ai_result, _ = ai_client.call_ai_stream(prompt)
        
        if isinstance(ai_result, dict) and "problems" in ai_result:
            return ai_result["problems"]
        else:
            log_debug(f"[WARNING] 代码审查结果格式不正确: {ai_result}")
            return []
            
    except Exception as e:
        log_debug(f"[ERROR] 执行代码审查时出错: {e}")
        return []


def build_code_review_prompt(
    task: Dict[str, Any], 
    impact_report_content: str,
    file_diffs: Dict[str, Any],
    extract_path: str,
) -> str:
    """
    构建代码审查提示词
    
    Args:
        task: 任务信息
        impact_report_content: 影响域分析报告内容
        file_diffs: 文件差异信息
        extract_path: 解压路径
        
    Returns:
        str: 提示词
    """
    # 构建任务信息
    task_info = f"""任务ID: {task.get('task_id')}
任务名称: {task.get('task_name')}
任务描述: {task.get('task_description')}
变更类型: {task.get('change_type')}
"""
    
    # 从影响域分析报告中提取与当前任务相关的变更描述
    related_change_description = extract_related_change_description(
        impact_report_content, 
        task.get("related_change", "")
    )
    
    # 构建代码差异的展示部分
    code_diff_section = ""
    
    for file_path, diff_info in file_diffs.items():
        code_diff_section += f"\n## 文件: {file_path}\n"
        
        for func_info in diff_info["functions"]:
            code_diff_section += f"\n### 函数: {func_info['function_name']} ({func_info['change_type']})\n"
            
            if func_info.get("old_code"):
                code_diff_section += f"\n#### 旧版本代码:\n```c\n{func_info['old_code']}\n```\n"
            
            if func_info.get("new_code"):
                code_diff_section += f"\n#### 新版本代码:\n```{diff_info['file_type']}\n{func_info['new_code']}\n```\n"
            
            # 追加依赖函数体（仅针对新版本）
            try:
                new_version_dir = os.path.join(extract_path, "v1.01")
                deps = collect_function_with_dependencies(
                    entry_function=func_info['function_name'],
                    project_root=new_version_dir,
                    language=diff_info['file_type'],
                    max_depth=1,
                )
                deps.pop(func_info['function_name'], None)
                for dep_name, dep_info in deps.items():
                    code_diff_section += f"\n##### 依赖函数 {dep_name} (新版本，仅供参考)\n```{diff_info['file_type']}\n{dep_info['source_code']}\n```\n"
            except Exception as _dep_err:
                log_debug(f"[WARN] collect deps failed for {func_info['function_name']}: {_dep_err}")
    
    # 使用统一的深度审查提示词
    return get_deep_review_prompt(task_info, related_change_description, code_diff_section)


def extract_related_change_description(impact_report_content: str, related_change: str) -> str:
    """
    从影响域分析报告中提取与当前任务相关的变更描述
    
    Args:
        impact_report_content: 影响域分析报告内容
        related_change: 相关变更ID或描述
        
    Returns:
        str: 变更描述
    """
    if not related_change or not impact_report_content:
        return ""
        
    report_lines = impact_report_content.split("\n")
    relevant_sections = []
    current_section = []
    is_relevant_section = False
    current_level = 0
    section_start_level = 0
    
    for line in report_lines:
        stripped_line = line.strip()
        
        # 检查是否是章节标题
        if stripped_line.startswith("#"):
            # 计算标题级别
            level = len(line) - len(line.lstrip("#"))
            
            # 如果找到了相关章节，并且当前是同级或更高级别的标题，结束当前章节
            if is_relevant_section and level <= section_start_level:
                if current_section:
                    relevant_sections.extend(current_section)
                    current_section = []
                is_relevant_section = False
            
            current_level = level
            
            # 检查当前章节标题是否包含相关变更
            if related_change in line:
                is_relevant_section = True
                section_start_level = level
        else:
            # 检查非标题行是否包含相关变更
            if not is_relevant_section and related_change in line:
                is_relevant_section = True
                section_start_level = current_level
        
        # 如果在相关章节中，收集内容
        if is_relevant_section:
            current_section.append(line)
    
    # 处理最后一个部分
    if is_relevant_section and current_section:
        relevant_sections.extend(current_section)
    
    # 如果没有找到相关内容，尝试模糊匹配
    if not relevant_sections and related_change:
        # 尝试通过关键词匹配
        keywords = related_change.split()
        for line in report_lines:
            if any(keyword in line for keyword in keywords if len(keyword) > 2):
                # 找到包含关键词的行，提取上下文
                line_index = report_lines.index(line)
                start_index = max(0, line_index - 5)
                end_index = min(len(report_lines), line_index + 10)
                relevant_sections = report_lines[start_index:end_index]
                break
    
    return "\n".join(relevant_sections)


def save_problems(
    db, 
    problems: List[Dict[str, Any]], 
    task: Dict[str, Any], 
    task_id: int, 
    file_id: int
) -> None:
    """
    保存审查问题
    
    Args:
        db: 数据库会话
        problems: 问题列表
        task: 任务信息
        task_id: 任务ID
        file_id: 文件ID
    """
    from ..db.repository.problem_repo import ProblemRepository
    from ..db.repository.function_repo import FunctionRepository
    
    prob_repo = ProblemRepository(db)
    func_repo = FunctionRepository(db)
    
    for problem in problems:
        try:
            # 处理violation_rules字段 - 将列表转换为字符串
            violation_rules = problem.get("violation_rules", "")
            if isinstance(violation_rules, list):
                violation_rules = "; ".join(violation_rules)  # 用分号分隔多个规则
            elif not isinstance(violation_rules, str):
                violation_rules = str(violation_rules)
            
            # 创建函数记录
            function_name = problem.get("issue_location", "unknown_function")
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
                    "source_code": problem.get("source_code", ""),
                    "analyzed": True,
                    "file_path": problem.get("file_name", "")
                }
                function_record = func_repo.create_function(function_data)
            
            # 构建问题数据
            problem_data = {
                "task_id": task_id,
                "file_id": file_id,
                "function_id": function_record.id,
                "file_name": problem.get("file_name", ""),
                "source_code": problem.get("source_code", ""),
                "violation_rules": violation_rules,
                "issue_level": problem.get("issue_level", ""),
                "issue_name": problem.get("issue_name", ""),
                "issue_location": problem.get("issue_location", ""),
                "description_requirement": problem.get("description_requirement", ""),
                "description_issue": problem.get("description_issue", ""),
                "description_location": problem.get("description_location", ""),
                "description_impact": problem.get("description_impact", "")
            }
            
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
        log_debug(f"[ERROR] 保存提示词到日志时出错: {e}")