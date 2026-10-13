"""
AI代码审查主模块

提供代码审查的核心功能，包括函数提取、AI分析和问题入库。

支持两种审查模式：
1. 传统模式：一次性给AI所有依赖函数和全局变量
2. Agent模式：AI自主调用工具获取需要的信息（更灵活、更节省token）
"""
import os
import json
import glob
import time
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
import traceback  # 添加traceback模块用于详细错误日志
import uuid
import re
from pathlib import Path
import sys
from collections import defaultdict
from datetime import datetime

# 添加父目录到路径，以便导入其他模块
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入统一的日志系统
from ...utils.logger import log_debug, log_info, log_warning, log_error, log_ai_result, clear_current_task

# 导入并发日志系统
from ...utils.concurrent_logger import (
    init_concurrent_task, set_current_thread_task, clear_current_thread_task,
    log_concurrent_debug, log_concurrent_info, log_concurrent_warning, 
    log_concurrent_error, log_concurrent_ai_result, finalize_concurrent_task
)

# 导入性能分析器
from ...utils.performance_analyzer import performance_analyzer

# 更新导入路径以匹配项目结构
from .parser import function_parser as fp
from .parser.function_parser import read_file_with_encoding, _CHARDET_AVAILABLE
from .parser.global_var_parser import extract_globals_from_code, extract_macros_from_code, extract_arrays_from_code
from ...db.repository.file_repo import FileRepository
from ...db.repository.function_repo import FunctionRepository
from ...db.repository.problem_repo import ProblemRepository
from ...db.repository.task_repo import TaskRepository
from ...config import ALLOWED_CODE_EXTENSIONS, FPGA_CODE_EXTENSIONS, ALL_SUPPORTED_EXTENSIONS, get_file_type, AI_CONCURRENT_REQUESTS, ENABLE_FUNCTION_REVIEW_AGENT
# 导入更新后的AIClient
from .openai.client import AIClient
from .prompt.codeReviewPrompt import get_prompt_template, get_fpga_prompt_template
from .rules.codeReview import get_rules, fpga_get_rules
# 导入FPGA解析器
from .parser.fpga.fpga_parser import extract_fpga_files_from_code, read_file_with_encoding as fpga_read_file
# 导入Agent审查
from .function_review_agent import FunctionReviewAgent
from .fpga_review_agent import FPGAReviewAgent

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

# ---------------------------------------------------------------------------
# Prompt builder with dependency expansion
# ---------------------------------------------------------------------------

from .parser import collect_function_with_dependencies  # noqa: E402

def _build_prompt(
    code: str,
    file_name: str,
    function_name: str,
    project_root: str,
    language: str,
    global_var_map: Dict[str, Dict[str, Any]],
) -> str:
    with performance_analyzer.measure_step("提示词构建-获取模板和规则"):
        # 系统提示词 & 规则
        system_prompt = get_prompt_template()
        rules = get_rules()

    with performance_analyzer.measure_step("提示词构建-检测全局变量使用"):
        # 使用智能检测器找出在代码中实际使用的全局变量（排除局部变量遮蔽）
        from .parser.global_var_parser import detect_actual_global_usage
        used_globals: List[str] = detect_actual_global_usage(code, global_var_map, language)

    # ---- 收集依赖函数 ----
    with performance_analyzer.measure_step("提示词构建-收集依赖函数") as deps_step:
        try:
            deps = collect_function_with_dependencies(
                entry_function=function_name,
                project_root=project_root,
                language=language,
                max_depth=1,
            )
        except Exception as _err:
            log_warning(f"collect dependencies failed for {function_name}: {_err}", "dependency_collector")
            deps = {}

        deps.pop(function_name, None)
        deps_step.add_metadata("dependencies_found", len(deps))
    
    with performance_analyzer.measure_step("提示词构建-构建基础提示词"):
        # 构建基础提示词（不包含依赖函数）
        base_prompt = f"""{system_prompt}

以下是禁止在结果中报告的问题类型（如遇到这些问题请忽略，不要在输出中包含）：
{rules}

请对文件 `{file_name}` 中的以下代码进行代码审查：
```{language}
{code}
```
"""
        
        # 添加全局变量信息
        globals_section = ""
        if used_globals:
            globals_section = "\n该代码块使用的全局项目及其定义如下：\n"
            for gv in used_globals:
                meta = global_var_map[gv]
                item_type = meta.get('type', 'variable')
                if item_type == 'macro':
                    globals_section += f"\n宏定义 {gv} 在文件 {meta['file']} 第 {meta['line']} 行定义：\n```{language}\n{meta['code']}\n```\n"
                elif item_type == 'array':
                    globals_section += f"\n数组变量 {gv} 在文件 {meta['file']} 第 {meta['line']} 行定义/声明：\n```{language}\n{meta['code']}\n```\n"
                else:
                    globals_section += f"\n变量 {gv} 在文件 {meta['file']} 第 {meta['line']} 行定义/声明：\n```{language}\n{meta['code']}\n```\n"
        else:
            globals_section = "\n该代码块未使用全局变量、宏定义或数组。\n"
    
    with performance_analyzer.measure_step("提示词构建-Token计算和优化") as token_step:
        # 计算基础提示词的token数
        base_tokens = estimate_tokens(base_prompt + globals_section + "\n/nothink")
        log_debug(f"基础提示词token数: {base_tokens}", "token_manager")
        token_step.add_metadata("base_tokens", base_tokens)
        
        # 如果基础提示词已经超过限制，直接返回
        MAX_TOKENS = 15000
        if base_tokens >= MAX_TOKENS:
            log_warning(f"基础提示词已超过限制，直接返回", "token_manager")
            return base_prompt + globals_section + "\n/nothink"
        
        # 计算可用于依赖函数的token数
        available_tokens = MAX_TOKENS - base_tokens
        log_debug(f"可用于依赖函数的token数: {available_tokens}", "token_manager")
        token_step.add_metadata("available_tokens", available_tokens)
        
        # 按依赖函数的token数量排序（从大到小）
        deps_with_tokens = []
        for dep_name, dep_info in deps.items():
            dep_section = f"\n### 被调用函数 {dep_name}\n```{language}\n{dep_info['source_code']}\n```\n"
            dep_tokens = estimate_tokens(dep_section)
            deps_with_tokens.append((dep_name, dep_info, dep_section, dep_tokens))
        
        # 按token数量从大到小排序
        deps_with_tokens.sort(key=lambda x: x[3], reverse=True)
        
        # 依次添加依赖函数，直到超过token限制
        selected_deps = []
        used_tokens = 0
        
        for dep_name, dep_info, dep_section, dep_tokens in deps_with_tokens:
            if used_tokens + dep_tokens <= available_tokens:
                selected_deps.append(dep_section)
                used_tokens += dep_tokens
                log_debug(f"添加依赖函数 {dep_name}, token数: {dep_tokens}, 累计: {used_tokens}", "token_manager")
            else:
                log_debug(f"跳过依赖函数 {dep_name}, token数: {dep_tokens}, 会超过限制", "token_manager")
        
        token_step.add_metadata("selected_deps_count", len(selected_deps))
        token_step.add_metadata("used_tokens", used_tokens)
        
        # 构建最终提示词
        deps_section = "".join(selected_deps)
        final_prompt = base_prompt + deps_section + globals_section + "\n/nothink"
        
        final_tokens = estimate_tokens(final_prompt)
        log_debug(f"最终提示词token数: {final_tokens}, 包含 {len(selected_deps)} 个依赖函数", "token_manager")
        token_step.add_metadata("final_tokens", final_tokens)
        
        performance_analyzer.add_step_metadata("final_prompt_length", len(final_prompt))
        performance_analyzer.add_step_metadata("used_globals_count", len(used_globals))
    
    return final_prompt

def _build_fpga_prompt(
    code: str,
    file_name: str,
    language: str,
) -> str:
    """
    构建FPGA代码审查的提示词
    FPGA代码不需要依赖函数分析，所以提示词构建比较简单
    """
    # FPGA专用系统提示词 & 规则
    system_prompt = get_fpga_prompt_template()
    rules = fpga_get_rules()
    
    # 构建FPGA专用提示词
    fpga_prompt = f"""{system_prompt}

以下是FPGA代码审查的专用规则：
{rules}

请对文件 `{file_name}` 中的以下{language.upper()}代码进行代码审查：
```{language}
{code}
```

请根据FPGA设计的特点，重点关注语法正确性、设计规范性、时序逻辑、可综合性等方面。

/nothink"""
    
    # 计算token数量
    final_tokens = estimate_tokens(fpga_prompt)
    log_debug(f"FPGA提示词token数: {final_tokens}", "fpga_prompt_builder")
    
    return fpga_prompt

def identify_project_type(extract_path: str) -> str:
    """
    识别项目类型：c_cpp、fpga 或 mixed
    """
    c_cpp_files = []
    fpga_files = []
    
    log_info(f"🔍 开始扫描项目类型，路径: {extract_path}", "project_scanner")
    log_info(f"📂 支持的扩展名: {ALL_SUPPORTED_EXTENSIONS}", "project_scanner")
    
    # 扫描所有支持的文件
    for ext in ALL_SUPPORTED_EXTENSIONS:
        files = glob.glob(f"{extract_path}/**/*{ext}", recursive=True)
        # 🔧 修复：对文件列表排序，确保每次顺序一致
        files.sort()
        log_info(f"扫描 {ext} 文件: 找到 {len(files)} 个", "project_scanner")
        for file_path in files:
            file_type = get_file_type(file_path)
            rel_path = os.path.relpath(file_path, extract_path)
            log_info(f"文件 {rel_path} -> 类型: {file_type}", "project_scanner")
            if file_type == "c_cpp":
                c_cpp_files.append(file_path)
            elif file_type == "fpga":
                fpga_files.append(file_path)
    
    log_info(f"📊 项目类型识别结果: C/C++文件 {len(c_cpp_files)} 个, FPGA文件 {len(fpga_files)} 个", "project_scanner")
    if c_cpp_files:
        log_info(f"C/C++文件列表: {[os.path.basename(f) for f in c_cpp_files]}", "project_scanner")
    if fpga_files:
        log_info(f"FPGA文件列表: {[os.path.basename(f) for f in fpga_files]}", "project_scanner")
    
    if c_cpp_files and fpga_files:
        return "mixed"
    elif c_cpp_files:
        return "c_cpp"
    elif fpga_files:
        return "fpga"
    else:
        return "unknown"

# --- 解决 Windows 控制台编码问题 -----------------------------------------
# 在某些中文 Windows 环境下，sys.stdout 默认为 cp936/GBK，打印包含特殊字符
# 的字符串时会抛出 `UnicodeEncodeError: 'gbk' codec cannot encode character ...`。
# 这里将 stdout / stderr 重新包装为 UTF-8 编码并忽略无法编码的字符，
# 以确保所有 `print()` 调用不会因编码问题中断执行。
import sys, io
if sys.stdout and sys.stdout.encoding.lower() != 'utf-8':  # 避免重复包裹
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='ignore')
if sys.stderr and sys.stderr.encoding.lower() != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='ignore')
# ---------------------------------------------------------------------------

def _process_single_function_concurrent(func_data_dict: dict, file_id: int, task_id: int, db: Session, 
                           extract_path: str, all_global_vars: dict, ai_client, 
                           func_repo, prob_repo, task_repo, total_functions: int, 
                           processed_counter: dict, progress_lock: threading.Lock = None) -> None:
    """
    处理单个函数的AI分析
    
    Args:
        func_data_dict: 函数数据字典
        file_id: 文件ID
        task_id: 任务ID
        db: 数据库会话
        extract_path: 解压路径
        all_global_vars: 全局变量字典
        ai_client: AI客户端
        func_repo: 函数仓储
        prob_repo: 问题仓储
        task_repo: 任务仓储
        total_functions: 总函数数
        processed_counter: 已处理计数器（线程安全字典）
    """
    # 检查任务是否被取消
    from ...utils.task_cancel_manager import task_cancel_manager
    if task_cancel_manager.is_cancelled(task_id):
        log_concurrent_warning(f"任务 {task_id} 已被取消，停止处理函数: {func_data_dict['function_name']}", "task_cancel")
        return  # 提前退出
    
    try:
        with performance_analyzer.measure_step(f"分析函数: {func_data_dict['function_name']}", 
                                             function_name=func_data_dict['function_name'],
                                             file_path=func_data_dict['file_path']) as func_step:
            
            # 数据库操作
            with performance_analyzer.measure_step("数据库-创建函数记录"):
                function_data = {
                    "file_id": file_id,
                    "function_name": func_data_dict['function_name'],
                    "source_code": func_data_dict['source_code'],
                    "file_path": func_data_dict['file_path'],
                    "start_line": func_data_dict['start_line'],
                    "end_line": func_data_dict['end_line']
                }
                db_func = func_repo.create_function(function_data)
                db.flush()

            # 语言推断
            ext = os.path.splitext(func_data_dict['file_path'])[1].lower()
            lang_current = 'cpp' if ext in {'.cpp', '.cc', '.cxx', '.hpp', '.hxx'} else 'c'

            call_id = str(uuid.uuid4())[:8]
            log_concurrent_info(f"开始分析函数: {func_data_dict['function_name']} in {func_data_dict['file_path']} (ID: {call_id})", "ai_analyzer")
            
            # AI调用 - 支持Agent模式
            problems = []
            function_info = None
            try:
                # 检查是否启用Agent模式
                if ENABLE_FUNCTION_REVIEW_AGENT:
                    log_concurrent_info(f"[Agent模式] 使用Agent审查函数: {func_data_dict['function_name']}", "ai_analyzer")
                    
                    with performance_analyzer.measure_step("AI Agent审查") as ai_call_step:
                        # 创建Agent
                        agent = FunctionReviewAgent(
                            project_root=extract_path,
                            language=lang_current
                        )
                        
                        # 使用Agent审查
                        result = agent.review_function(
                            function_code=func_data_dict['source_code'],
                            function_name=func_data_dict['function_name'],
                            file_path=func_data_dict['file_path'],
                            global_var_map=all_global_vars,
                            forbidden_rules=get_rules()
                        )
                        
                        # 检查Agent是否遇到上下文超出
                        if result.get('_context_overflow'):
                            log_concurrent_warning(
                                f"[Agent模式] 检测到上下文超出，切换到简化模式",
                                "ai_analyzer"
                            )
                            
                            # 降级到简化模式
                            from .context_overflow_handler import review_with_simplified_mode
                            result = review_with_simplified_mode(
                                function_code=func_data_dict['source_code'],
                                function_name=func_data_dict['function_name'],
                                file_path=func_data_dict['file_path'],
                                forbidden_rules=get_rules(),
                                ai_client=ai_client
                            )
                            ai_call_step.add_metadata("mode", "agent_fallback_simplified")
                        else:
                            ai_call_step.add_metadata("mode", "agent")
                        
                        problems = result.get("problems", [])
                        function_info = result.get("function_info", {})
                        
                        ai_call_step.add_metadata("problems_found", len(problems))
                        
                        log_concurrent_ai_result(result, func_data_dict['function_name'], "ai_analyzer")
                else:
                    # 传统模式：构建包含依赖函数的prompt
                    log_concurrent_debug(f"[传统模式] 使用传统prompt审查函数: {func_data_dict['function_name']}", "ai_analyzer")
                    
                    with performance_analyzer.measure_step("构建传统模式提示词") as prompt_step:
                        prompt = _build_prompt(
                            func_data_dict['source_code'],
                            func_data_dict['file_path'],
                            func_data_dict['function_name'],
                            extract_path,
                            lang_current,
                            all_global_vars,
                        )
                        prompt_step.add_metadata("prompt_length", len(prompt))
                        prompt_step.add_metadata("token_count", estimate_tokens(prompt))
                    
                    log_concurrent_debug(f"构建的Prompt内容:\n{prompt}", "prompt_builder")
                    
                    with performance_analyzer.measure_step("AI模型调用") as ai_call_step:
                        result, _ = ai_client.call_ai_stream(prompt)
                        problems = result.get("problems", [])
                        function_info = result.get("function_info", {})
                        
                        ai_call_step.add_metadata("problems_found", len(problems))
                        ai_call_step.add_metadata("mode", "traditional")
                        
                        # 使用新的格式化AI结果记录
                        log_concurrent_ai_result(result, func_data_dict['function_name'], "ai_analyzer")
                    
            except Exception as e:
                # 检查是否是上下文超出错误
                from .context_overflow_handler import is_context_overflow_error, review_with_simplified_mode
                
                if is_context_overflow_error(e):
                    log_concurrent_warning(
                        f"检测到上下文超出错误，切换到简化模式审查 (ID: {call_id})",
                        "ai_analyzer"
                    )
                    
                    try:
                        # 使用简化模式重试（不包含工具和依赖）
                        result = review_with_simplified_mode(
                            function_code=func_data_dict['source_code'],
                            function_name=func_data_dict['function_name'],
                            file_path=func_data_dict['file_path'],
                            forbidden_rules=get_rules(),
                            ai_client=ai_client
                        )
                        
                        problems = result.get("problems", [])
                        function_info = result.get("function_info", {})
                        
                        log_concurrent_info(
                            f"简化模式审查成功，发现 {len(problems)} 个问题 (ID: {call_id})",
                            "ai_analyzer"
                        )
                    except Exception as retry_error:
                        log_concurrent_error(
                            f"简化模式审查也失败了 (ID: {call_id})",
                            "ai_analyzer",
                            retry_error
                        )
                else:
                    log_concurrent_error(f"AI分析失败 (ID: {call_id})", "ai_analyzer", e)

            # 保存函数信息
            with performance_analyzer.measure_step("保存函数信息"):
                if function_info and isinstance(function_info, dict) and (function_info.get("function_description") or function_info.get("commented_code")):
                    # 确保至少有一个字段不为空才保存
                    description = function_info.get("function_description")
                    commented_code = function_info.get("commented_code")
                    
                    # 过滤掉空字符串和None值
                    if description and description.strip():
                        description = description.strip()
                    else:
                        description = None
                        
                    if commented_code and commented_code.strip():
                        commented_code = commented_code.strip()
                    else:
                        commented_code = None
                    
                    # 只有在至少有一个有效字段时才更新
                    if description or commented_code:
                        func_repo.update_function_info(
                            db_func.id,
                            function_description=description,
                            commented_code=commented_code
                        )
                        log_concurrent_info(f"函数 {func_data_dict['function_name']} 信息已保存: description={description is not None}, commented_code={commented_code is not None}", "function_info_saver")
                    else:
                        log_concurrent_debug(f"函数 {func_data_dict['function_name']} function_info为空，未保存", "function_info_saver")
                else:
                    log_concurrent_debug(f"函数 {func_data_dict['function_name']} 未返回有效的function_info", "function_info_saver")

            # 保存问题
            if problems:
                with performance_analyzer.measure_step("保存问题到数据库", problem_count=len(problems)):
                    log_concurrent_info(f"函数 {func_data_dict['function_name']} 分析完成，发现 {len(problems)} 个问题", "problem_analyzer")
                    
                    # ===== 已禁用问题过滤功能 =====
                    # 不再过滤包含"可能"、"潜在"、"风险"等关键词的问题
                    # 所有AI返回的问题都将被保存
                    # uncertain_keywords = ["可能", "潜在", "风险", "建议", "应该检查", "需要检查", "缺少检查", "缺乏检查"]
                    # ================================
                    
                    # 直接使用所有问题，不进行过滤
                    filtered_problems = problems
                    
                    # 保存所有问题
                    for i, problem in enumerate(filtered_problems):
                        # 调试：检查问题等级
                        issue_level = problem.get("issue_level", "")
                        log_concurrent_debug(f"保存问题 {i+1}: issue_level='{issue_level}', issue_name='{problem.get('issue_name', '')}'", "problem_analyzer")
                        
                        problem_data = {
                            "task_id": task_id,
                            "file_id": file_id,
                            "function_id": db_func.id,
                            "file_name": func_data_dict['file_path'],
                            "source_code": func_data_dict['source_code'],
                            "problem_reason": problem.get("problem_reason", ""),
                            "issue_level": issue_level,
                            "issue_name": problem.get("issue_name", ""),
                            "issue_location": problem.get("issue_location", ""),
                            "description_requirement": problem.get("description_requirement", ""),
                            "description_issue": problem.get("description_issue", ""),
                            "description_location": problem.get("description_location", ""),
                            "description_impact": problem.get("description_impact", "")
                        }
                        log_concurrent_debug(f"保存问题数据: {problem_data}", "problem_saver")
                        prob_repo.create_problem(problem_data)
            else:
                log_concurrent_info(f"函数 {func_data_dict['function_name']} 分析完成，未发现问题.", "problem_analyzer")
            
            # ⚠️ 修复：无论是否有问题，都必须commit以确保函数记录被保存
            # 这是修复大型项目部分文件未被审查的关键！
            db.commit()
            log_concurrent_debug(f"函数 {func_data_dict['function_name']} 的数据库事务已提交", "db_transaction")
            
            # 🔧 进度更新：移到函数处理完成后（避免任务恢复时进度突变）
            # 只有当函数真正处理完成并提交到数据库后，才更新进度
            if progress_lock:
                with progress_lock:
                    processed_counter['count'] += 1
                    progress = (processed_counter['count'] / total_functions) * 100
                    task_repo.update_task_progress(task_id, min(progress, 99))
                    db.commit()
                    log_concurrent_debug(
                        f"进度已更新: {processed_counter['count']}/{total_functions} ({progress:.1f}%)",
                        "progress_updater"
                    )
            else:
                # 单线程模式
                processed_counter['count'] += 1
                progress = (processed_counter['count'] / total_functions) * 100
                task_repo.update_task_progress(task_id, min(progress, 99))
                db.commit()
                log_concurrent_debug(
                    f"进度已更新: {processed_counter['count']}/{total_functions} ({progress:.1f}%)",
                    "progress_updater"
                )

    except Exception as e:
        db.rollback()
        log_concurrent_error(f"处理函数 {func_data_dict.get('function_name')} 时发生严重错误", "function_analyzer", e)


def _process_single_function_with_new_db(func_data_dict: dict, file_id: int, task_id: int, 
                                       extract_path: str, all_global_vars: dict,
                                       total_functions: int, processed_counter: dict, 
                                       progress_lock: threading.Lock, 
                                       thread_index: int = 0) -> None:
    """
    使用新数据库会话处理单个函数的AI分析（线程安全版本）
    
    Args:
        func_data_dict: 函数数据字典
        file_id: 文件ID
        task_id: 任务ID
        extract_path: 解压路径
        all_global_vars: 全局变量字典
        total_functions: 总函数数
        processed_counter: 已处理计数器（线程安全字典）
        progress_lock: 进度更新锁
    """
    from ...config_database import get_db
    from ...db.repository.file_repo import FileRepository
    from ...db.repository.function_repo import FunctionRepository
    from ...db.repository.problem_repo import ProblemRepository
    from ...db.repository.task_repo import TaskRepository
    
    # 为每个线程创建独立的数据库会话
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # 使用实际线程ID设置线程专用日志，避免重复创建
        actual_thread_id = threading.current_thread().ident
        thread_name = f"worker_{actual_thread_id}"
        
        # 检查是否已经设置过线程任务（避免重复初始化）
        from ...utils.concurrent_logger import get_current_thread_info
        current_task_id, current_file_id, current_log_file, current_thread_name = get_current_thread_info()
        
        if current_task_id != task_id or current_thread_name != thread_name:
            set_current_thread_task(task_id, file_id, thread_name)
            log_concurrent_info(f"线程 {thread_name} 初始化完成", "thread_manager")
        
        log_concurrent_info(f"线程 {thread_name} 开始处理函数: {func_data_dict['function_name']}", "function_processor")
        
        # 创建仓储对象
        func_repo = FunctionRepository(db)
        prob_repo = ProblemRepository(db)
        task_repo = TaskRepository(db)
        ai_client = AIClient()
        
        # 调用原始处理函数
        _process_single_function_concurrent(
            func_data_dict, file_id, task_id, db, extract_path, all_global_vars,
            ai_client, func_repo, prob_repo, task_repo, total_functions, processed_counter, progress_lock
        )
        
        log_concurrent_info(f"线程 {thread_name} 完成函数处理: {func_data_dict['function_name']}", "function_processor")
        
    finally:
        # 注意：不在这里清除线程日志上下文，因为同一线程可能处理多个函数
        # 线程日志上下文会在线程真正结束时自动清除
        
        # 确保数据库会话被正确关闭
        try:
            db.close()
        except Exception as e:
            print(f"关闭数据库会话时出错: {e}")  # 使用print避免日志系统问题


def _process_functions_concurrently(all_functions_to_process: list, file_id: int, task_id: int, 
                                  db: Session, extract_path: str, all_global_vars: dict,
                                  func_repo, prob_repo, task_repo,
                                  already_processed_count: int = 0,
                                  total_project_functions: int = 0) -> None:
    """
    并发处理所有函数的AI分析
    
    Args:
        all_functions_to_process: 待处理的函数列表
        file_id: 文件ID
        task_id: 任务ID
        db: 数据库会话（主会话，用于进度更新）
        extract_path: 解压路径
        all_global_vars: 全局变量字典
        func_repo: 函数仓储
        prob_repo: 问题仓储
        task_repo: 任务仓储
    """
    from ...config_database import get_db
    
    # total_functions 用于进度计算：优先使用调用方提供的项目总函数数；
    # 若未提供，则退化为“已处理 + 本批次”总数
    if total_project_functions and total_project_functions > 0:
        total_functions = total_project_functions
    else:
        total_functions = len(all_functions_to_process) + max(already_processed_count, 0)

    processed_counter = {'count': max(already_processed_count, 0)}
    progress_lock = threading.Lock()
    
    # 使用线程池执行器进行并发处理
    with ThreadPoolExecutor(max_workers=AI_CONCURRENT_REQUESTS) as executor:
        log_info(f"启动并发处理，最大并发数: {AI_CONCURRENT_REQUESTS}, 总函数数: {total_functions}", "concurrent_processor")
        
        # 提交所有任务到线程池
        futures = []
        for i, func_data_dict in enumerate(all_functions_to_process):
            future = executor.submit(
                _process_single_function_with_new_db,
                func_data_dict, file_id, task_id, extract_path, all_global_vars,
                total_functions, processed_counter, progress_lock, i
            )
            futures.append(future)
        
        # 等待所有任务完成
        for future in as_completed(futures):
            try:
                future.result()  # 获取结果，如果有异常会在这里抛出
            except Exception as e:
                log_error(f"并发处理函数时发生错误", "concurrent_processor", e)
        
        # 线程池执行完成后，清理所有活跃的线程上下文
        log_info(f"并发处理完成，清理线程上下文", "concurrent_processor")


def _process_single_fpga_file_with_new_db(
    fpga_file: str, file_id: int, task_id: int, extract_path: str,
    total_files: int, processed_counter: dict, progress_lock: threading.Lock, index: int,
    thread_id_pool = None
):
    """
    在独立数据库会话中处理单个FPGA文件（用于并发处理）
    
    Args:
        fpga_file: FPGA文件路径
        file_id: 文件ID
        task_id: 任务ID
        extract_path: 解压路径
        total_files: 总文件数
        processed_counter: 处理计数器（共享字典）
        progress_lock: 进度锁
        index: 文件索引
        thread_id_pool: 线程ID池（用于复用线程ID）
    """
    # 检查任务是否被取消
    from ...utils.task_cancel_manager import task_cancel_manager
    if task_cancel_manager.is_cancelled(task_id):
        log_concurrent_warning(f"任务 {task_id} 已被取消，停止处理FPGA文件: {os.path.basename(fpga_file)}", "task_cancel")
        if thread_id_pool is not None:
            # 归还线程ID
            worker_id = index
            thread_id_pool.put(worker_id)
        return  # 提前退出
    
    from ...config_database import get_db
    
    # 从线程ID池获取一个可用的线程ID
    if thread_id_pool is not None:
        worker_id = thread_id_pool.get()  # 阻塞等待直到有可用ID
    else:
        worker_id = index  # 降级处理：如果没有线程ID池，使用文件索引
    
    # 设置线程级别的并发日志
    thread_name = f"fpga_worker_{worker_id}"
    set_current_thread_task(task_id, file_id, thread_name)
    
    # 创建独立的数据库会话
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        log_concurrent_info(f"开始处理FPGA文件 {index+1}/{total_files}: {os.path.basename(fpga_file)}", "fpga_worker")
        
        # 初始化仓储
        func_repo = FunctionRepository(db)
        prob_repo = ProblemRepository(db)
        task_repo = TaskRepository(db)
        
        rel_path = os.path.relpath(fpga_file, extract_path)
        log_concurrent_debug(f"处理文件相对路径: {rel_path}", "fpga_worker")

        # 读取文件内容
        try:
            code, encoding = fpga_read_file(fpga_file)
            log_concurrent_debug(f"文件读取成功，编码: {encoding}", "fpga_worker")
        except Exception as e:
            log_concurrent_error(f"读取文件失败: {fpga_file}", "fpga_worker", e)
            return

        # 使用FPGA解析器解析文件
        try:
            file_info_list = extract_fpga_files_from_code(code, fpga_file)
            if not file_info_list:
                log_concurrent_warning(f"文件解析结果为空: {rel_path}", "fpga_worker")
                return
            
            file_info = file_info_list[0]  # FPGA解析器返回单个文件信息
            log_concurrent_debug(f"文件解析成功: {file_info['function_name']}", "fpga_worker")
        except Exception as e:
            log_concurrent_error(f"文件解析失败: {fpga_file}", "fpga_worker", e)
            return

        # 创建"函数"记录（实际上是文件记录）
        function_data = {
            "file_id": file_id,
            "function_name": file_info['function_name'],
            "source_code": file_info['source_code'],
            "file_path": rel_path,
            "start_line": file_info['start_line'],
            "end_line": file_info['end_line']
        }
        db_func = func_repo.create_function(function_data)
        db.flush()

        call_id = str(uuid.uuid4())[:8]
        log_concurrent_info(f"开始AI分析文件: {rel_path} (ID: {call_id})", "fpga_worker")
        
        problems = []
        function_info = None
        try:
            # 默认使用Agent模式（FPGA Agent）
            log_concurrent_info(f"[FPGA Agent模式] 使用Agent审查模块: {file_info['function_name']}", "fpga_worker")
            
            # 创建FPGA Agent
            fpga_agent = FPGAReviewAgent(
                project_root=extract_path,
                language=file_info['language']
            )
            
            # 使用Agent审查
            result = fpga_agent.review_module(
                module_code=file_info['source_code'],
                module_name=file_info['function_name'],
                file_path=rel_path,
                forbidden_rules=fpga_get_rules()
            )
            
            problems = result.get("problems", [])
            function_info = result.get("function_info", {})
            
            # 使用并发日志记录AI结果
            log_concurrent_ai_result(result, file_info['function_name'], "fpga_worker")
            
        except Exception as e:
            log_concurrent_error(f"AI分析失败 (ID: {call_id})", "fpga_worker", e)

        # 保存函数信息（描述和注释后代码）
        if function_info and isinstance(function_info, dict) and (function_info.get("function_description") or function_info.get("commented_code")):
            # 确保至少有一个字段不为空才保存
            description = function_info.get("function_description")
            commented_code = function_info.get("commented_code")
            
            # 过滤掉空字符串和None值
            if description and description.strip():
                description = description.strip()
            else:
                description = None
                
            if commented_code and commented_code.strip():
                commented_code = commented_code.strip()
            else:
                commented_code = None
            
            # 只有在至少有一个有效字段时才更新
            if description or commented_code:
                func_repo.update_function_info(
                    db_func.id,
                    function_description=description,
                    commented_code=commented_code
                )
                log_concurrent_info(f"文件 {rel_path} 信息已保存: description={description is not None}, commented_code={commented_code is not None}", "fpga_worker")
            else:
                log_concurrent_debug(f"文件 {rel_path} function_info为空，未保存", "fpga_worker")
        else:
            log_concurrent_debug(f"文件 {rel_path} 未返回有效的function_info", "fpga_worker")

        if problems:
            log_concurrent_info(f"文件 {rel_path} 分析完成，发现 {len(problems)} 个问题", "fpga_worker")
            
            # ===== 已禁用FPGA问题过滤功能 =====
            # 不再过滤包含"可能"、"潜在"、"风险"等关键词的问题
            # 所有AI返回的问题都将被保存
            # uncertain_keywords = ["可能", "潜在", "风险", "建议", "应该检查", "需要检查", "缺少检查", "缺乏检查"]
            # ================================
            
            # 直接使用所有问题，不进行过滤
            filtered_problems = problems
            
            # 保存所有问题
            for i, problem in enumerate(filtered_problems):
                # 调试：检查问题等级
                issue_level = problem.get("issue_level", "")
                log_concurrent_debug(f"保存FPGA问题 {i+1}: issue_level='{issue_level}', issue_name='{problem.get('issue_name', '')}'", "fpga_worker")
                
                problem_data = {
                    "task_id": task_id,
                    "file_id": file_id,
                    "function_id": db_func.id,
                    "file_name": rel_path,
                    "source_code": file_info['source_code'],
                    "problem_reason": problem.get("problem_reason", ""),
                    "issue_level": issue_level,
                    "issue_name": problem.get("issue_name", ""),
                    "issue_location": problem.get("issue_location", ""),
                    "description_requirement": problem.get("description_requirement", ""),
                    "description_issue": problem.get("description_issue", ""),
                    "description_location": problem.get("description_location", ""),
                    "description_impact": problem.get("description_impact", "")
                }
                log_concurrent_debug(f"保存问题数据: {problem_data}", "fpga_worker")
                prob_repo.create_problem(problem_data)
            db.commit()
        else:
            log_concurrent_info(f"文件 {rel_path} 分析完成，未发现问题.", "fpga_worker")

        # 更新进度
        with progress_lock:
            processed_counter['count'] += 1
            progress = (processed_counter['count'] / total_files) * 100
            # 注意：这里我们不能使用主会话的task_repo，需要创建新的会话来更新进度
            # 但为了避免数据库冲突，我们在主线程中统一更新进度
            log_concurrent_info(f"FPGA文件处理完成 ({processed_counter['count']}/{total_files}) - {progress:.1f}%", "fpga_worker")

    except Exception as e:
        db.rollback()
        log_concurrent_error(f"处理FPGA文件时发生严重错误: {fpga_file}", "fpga_worker", e)
    finally:
        # 清理数据库会话
        db.close()
        # 清理线程本地存储
        clear_current_thread_task()
        # 归还线程ID到池中（重要！确保ID可以被重用）
        if thread_id_pool is not None:
            thread_id_pool.put(worker_id)


def _process_all_fpga_files_concurrently(
    all_fpga_files: List[str], file_id: int, task_id: int, db: Session, extract_path: str
):
    """
    并发处理所有FPGA文件
    
    Args:
        all_fpga_files: 所有FPGA文件路径列表
        file_id: 文件ID
        task_id: 任务ID
        db: 数据库会话（主会话，用于进度更新）
        extract_path: 解压路径
    """
    log_info(f"🚀 进入FPGA并发处理函数: file_id={file_id}, task_id={task_id}, 文件数={len(all_fpga_files)}", "fpga_concurrent_processor")
    from ...config_database import get_db
    import queue
    
    total_files = len(all_fpga_files)
    processed_counter = {'count': 0}
    progress_lock = threading.Lock()
    
    # 创建线程ID池（0 到 AI_CONCURRENT_REQUESTS-1）
    thread_id_pool = queue.Queue()
    for worker_id in range(AI_CONCURRENT_REQUESTS):
        thread_id_pool.put(worker_id)
    
    log_info(f"📝 FPGA文件列表: {[os.path.basename(f) for f in all_fpga_files]}", "fpga_concurrent_processor")
    log_info(f"🔢 线程ID池初始化: {AI_CONCURRENT_REQUESTS} 个线程ID (0-{AI_CONCURRENT_REQUESTS-1})", "fpga_concurrent_processor")
    
    # 使用线程池执行器进行并发处理
    with ThreadPoolExecutor(max_workers=AI_CONCURRENT_REQUESTS) as executor:
        log_info(f"🔄 启动FPGA并发处理，最大并发数: {AI_CONCURRENT_REQUESTS}, 总文件数: {total_files}", "fpga_concurrent_processor")
        
        # 提交所有任务到线程池
        futures = []
        for i, fpga_file in enumerate(all_fpga_files):
            future = executor.submit(
                _process_single_fpga_file_with_new_db,
                fpga_file, file_id, task_id, extract_path,
                total_files, processed_counter, progress_lock, i, thread_id_pool
            )
            futures.append(future)
        
        # 等待所有任务完成并定期更新进度
        task_repo = TaskRepository(db)
        completed_futures = 0
        
        for future in as_completed(futures):
            try:
                future.result()  # 获取结果，如果有异常会在这里抛出
                completed_futures += 1
                
                # 更新进度（在主线程中安全地更新）
                progress = (completed_futures / total_files) * 100
                task_repo.update_task_progress(task_id, min(progress, 99))
                if completed_futures % max(1, total_files // 10) == 0:  # 每10%输出一次
                    log_info(f"FPGA并发处理进度: {completed_futures}/{total_files} ({progress:.1f}%)", "fpga_concurrent_processor")
                
            except Exception as e:
                log_error(f"并发处理FPGA文件时发生错误", "fpga_concurrent_processor", e)
        
        # 线程池执行完成后，清理所有活跃的线程上下文
        log_info(f"FPGA并发处理完成，清理线程上下文", "fpga_concurrent_processor")


def run_fpga_code_review(file_id: int, task_id: int, db: Session, tester_name: str = None):
    """
    FPGA代码审查流程：文件级别的审查，支持并发处理
    
    Args:
        file_id: 文件ID
        task_id: 任务ID
        db: 数据库会话
        tester_name: 测试人员姓名
    """
    # 初始化并发日志系统
    task_folder = init_concurrent_task(task_id, file_id, tester_name=tester_name)
    log_info(f"FPGA并发日志系统已初始化，任务文件夹: {task_folder.name}", "fpga_concurrent_logger")
    set_current_thread_task(task_id, file_id, thread_name="fpga_main")
    log_concurrent_info("主线程日志上下文已初始化，用于记录FPGA解析详情", "fpga_concurrent_logger")
    
    try:
        log_info(f"开始执行FPGA代码审查, file_id={file_id}, task_id={task_id}", "fpga_reviewer")
        file_repo = FileRepository(db)
        task_repo = TaskRepository(db)

        db_file = file_repo.get_file(file_id)
        if not db_file or not db_file.extract_path or not os.path.exists(db_file.extract_path):
            log_error(f"文件或解压路径无效. file_id: {file_id}", "fpga_reviewer")
            task_repo.update_task_status(task_id, "failed")
            db.commit()
            return
        extract_path = db_file.extract_path

        # 1. 查找所有FPGA源文件
        fpga_files = []
        for ext in FPGA_CODE_EXTENSIONS:
            fpga_files.extend(glob.glob(f"{extract_path}/**/*{ext}", recursive=True))
        
        # 🔧 修复：对文件列表排序，确保每次审查顺序一致
        fpga_files.sort()
        
        if not fpga_files:
            log_error("未找到有效的FPGA源代码文件", "fpga_reviewer")
            task_repo.update_task_status(task_id, "failed")
            db.commit()
            return
        log_info(f"找到 {len(fpga_files)} 个FPGA源文件.", "fpga_reviewer")

        directory_file_map: Dict[str, List[str]] = defaultdict(list)
        modules_by_file: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        total_fpga_files = len(fpga_files)

        for fpga_file in fpga_files:
            rel_path = os.path.relpath(fpga_file, extract_path)
            directory = os.path.dirname(rel_path) or "."
            directory_file_map[directory].append(os.path.basename(rel_path))

        directory_count = len(directory_file_map)
        log_concurrent_info(
            f"FPGA源代码目录统计: {directory_count} 个目录覆盖 {total_fpga_files} 个文件",
            "fpga_reviewer"
        )

        if directory_count:
            directory_preview_limit = 30
            file_preview_limit = 8
            preview_dirs = sorted(directory_file_map.keys())[:10]
            log_concurrent_info(f"目录示例（最多10个）: {preview_dirs}", "fpga_reviewer")

            for index, dir_path in enumerate(sorted(directory_file_map.keys())):
                if index >= directory_preview_limit:
                    break
                files_in_dir = directory_file_map[dir_path]
                file_preview = files_in_dir[:file_preview_limit]
                more_suffix = " ...更多" if len(files_in_dir) > file_preview_limit else ""
                current_dir_label = dir_path or "."
                log_concurrent_debug(
                    f"[FPGA目录扫描] {current_dir_label}: {len(files_in_dir)} 个文件 -> {file_preview}{more_suffix}",
                    "fpga_reviewer"
                )

            if directory_count > directory_preview_limit:
                log_concurrent_info(
                    f"其余 {directory_count - directory_preview_limit} 个目录的明细将写入FPGA解析摘要文件",
                    "fpga_reviewer"
                )

        # 预解析模块信息用于生成摘要
        module_preview_limit = 10
        file_module_log_limit = 50
        for fpga_file in fpga_files:
            rel_path = os.path.relpath(fpga_file, extract_path)
            module_list = modules_by_file[rel_path]

            try:
                code, encoding = fpga_read_file(fpga_file)
                log_concurrent_debug(
                    f"[FPGA预解析] 读取文件成功: {rel_path}, 编码: {encoding}",
                    "fpga_reviewer"
                )
            except Exception as read_err:
                log_concurrent_warning(
                    f"[FPGA预解析] 读取文件失败，跳过: {rel_path}, error={read_err}",
                    "fpga_reviewer"
                )
                continue

            try:
                module_infos = extract_fpga_files_from_code(code, fpga_file)
            except Exception as parse_err:
                log_concurrent_warning(
                    f"[FPGA预解析] 解析文件结构失败: {rel_path}, error={parse_err}",
                    "fpga_reviewer"
                )
                module_infos = []

            preview_names: List[str] = []
            for module_info in module_infos:
                module_name = (
                    module_info.get("function_name")
                    or module_info.get("module_name")
                    or module_info.get("name")
                    or "<unknown>"
                )
                module_list.append(
                    {
                        "name": module_name,
                        "start_line": module_info.get("start_line"),
                        "end_line": module_info.get("end_line"),
                    }
                )
                if len(preview_names) < module_preview_limit:
                    preview_names.append(module_name)

            if module_infos:
                more_suffix = " ...更多" if len(module_infos) > len(preview_names) else ""
                log_concurrent_debug(
                    f"[FPGA模块预览] {rel_path}: 发现 {len(module_infos)} 个模块 -> {preview_names}{more_suffix}",
                    "fpga_reviewer"
                )
            else:
                log_concurrent_debug(
                    f"[FPGA模块预览] {rel_path}: 未检测到解析模块",
                    "fpga_reviewer"
                )

        total_modules = sum(len(items) for items in modules_by_file.values())
        log_concurrent_info(
            f"FPGA模块统计: 共识别 {total_modules} 个模块/实体，覆盖 {len(modules_by_file)} 个文件",
            "fpga_reviewer"
        )

        logged_files = 0
        for file_path in sorted(modules_by_file.keys()):
            if logged_files >= file_module_log_limit:
                break
            modules = modules_by_file[file_path]
            if modules:
                preview_names = [item["name"] for item in modules[:module_preview_limit]]
                more_suffix = " ...更多" if len(modules) > module_preview_limit else ""
                log_concurrent_debug(
                    f"[FPGA模块清单] {file_path}: {len(modules)} 个模块 -> {preview_names}{more_suffix}",
                    "fpga_reviewer"
                )
            else:
                log_concurrent_debug(
                    f"[FPGA模块清单] {file_path}: 未检测到解析模块",
                    "fpga_reviewer"
                )
            logged_files += 1

        if len(modules_by_file) > file_module_log_limit:
            log_concurrent_info(
                f"其余 {len(modules_by_file) - file_module_log_limit} 个文件的模块列表已写入FPGA解析摘要文件",
                "fpga_reviewer"
            )

        # 写入解析摘要文件
        try:
            logs_subfolder = task_folder / "logs"
            logs_subfolder.mkdir(exist_ok=True)
            parse_summary_path = logs_subfolder / "fpga_parse_summary.json"
            directory_entries = [
                {
                    "path": dir_path or ".",
                    "file_count": len(files),
                    "files": sorted(files),
                }
                for dir_path, files in sorted(directory_file_map.items())
            ]
            file_entries = [
                {
                    "path": file_path,
                    "module_count": len(modules),
                    "modules": [
                        {
                            "name": module.get("name"),
                            "start_line": module.get("start_line"),
                            "end_line": module.get("end_line"),
                        }
                        for module in modules
                    ],
                }
                for file_path, modules in sorted(modules_by_file.items())
            ]
            parse_summary_payload = {
                "generated_at": datetime.now().isoformat(),
                "task_id": task_id,
                "file_id": file_id,
                "project_root": extract_path,
                "total_directories": len(directory_entries),
                "total_fpga_files": total_fpga_files,
                "total_modules": total_modules,
                "directories": directory_entries,
                "files": file_entries,
            }
            with open(parse_summary_path, "w", encoding="utf-8") as summary_fp:
                json.dump(parse_summary_payload, summary_fp, ensure_ascii=False, indent=2)
            log_concurrent_info(
                f"FPGA解析摘要已生成，可在 {parse_summary_path} 查看目录与模块明细",
                "fpga_reviewer"
            )
        except Exception as fpga_summary_error:
            log_concurrent_warning(
                f"写入FPGA解析摘要文件失败: {fpga_summary_error}",
                "fpga_reviewer"
            )

        # 2. 检查是否启用并发处理
        log_info(f"FPGA并发处理条件检查: AI_CONCURRENT_REQUESTS={AI_CONCURRENT_REQUESTS}, fpga_files数量={len(fpga_files)}", "fpga_reviewer")
        if AI_CONCURRENT_REQUESTS > 0 and len(fpga_files) > 0:
            log_info(f"✅ 启用FPGA并发处理模式，并发数: {AI_CONCURRENT_REQUESTS}, 文件数: {len(fpga_files)}", "fpga_reviewer")
            _process_all_fpga_files_concurrently(fpga_files, file_id, task_id, db, extract_path)
        else:
            log_info(f"❌ 跳过FPGA并发处理 (并发数={AI_CONCURRENT_REQUESTS}, 文件数={len(fpga_files)})", "fpga_reviewer")
            # 如果AI_CONCURRENT_REQUESTS为0，说明禁用了AI审查，直接跳过

        # 最终化并发任务日志
        finalize_concurrent_task(task_id)
        
        log_info("更新FPGA任务状态为completed", "fpga_task_manager")
        task_repo.update_task_status(task_id, "completed")
        db.commit()
        log_info(f"FPGA任务 {task_id} 已完成，总共分析了 {len(fpga_files)} 个FPGA文件", "fpga_task_manager")
        
        # 从取消管理器中移除任务
        from ...utils.task_cancel_manager import task_cancel_manager
        task_cancel_manager.unregister_task(task_id)
        log_info(f"FPGA任务 {task_id} 已从取消管理器中移除", "fpga_task_manager")
        
    finally:
        clear_current_thread_task()
        # 清除当前任务的日志设置
        clear_current_task()


# 顺序处理函数已移除，统一使用并发处理

def run_code_review(file_id: int, task_id: int, db: Session, tester_name: str = None):
    """
    主流程：识别项目类型并调用相应的审查函数
    
    Args:
        file_id: 文件ID
        task_id: 任务ID
        db: 数据库会话
        tester_name: 测试人员姓名
    """
    # 开始性能分析会话
    performance_analyzer.start_session(task_id, file_id)
    
    try:
        with performance_analyzer.measure_step("项目类型识别"):
            log_info(f"开始执行代码审查, file_id={file_id}, task_id={task_id}", "main_reviewer")
            file_repo = FileRepository(db)
            task_repo = TaskRepository(db)

            db_file = file_repo.get_file(file_id)
            if not db_file or not db_file.extract_path or not os.path.exists(db_file.extract_path):
                log_error(f"文件或解压路径无效. file_id: {file_id}", "main_reviewer")
                task_repo.update_task_status(task_id, "failed")
                db.commit()
                return
            extract_path = db_file.extract_path

            # 1. 识别项目类型
            project_type = identify_project_type(extract_path)
            log_info(f"🔍 项目类型识别结果: {project_type}, 路径: {extract_path}", "project_type_detector")

            if project_type == "unknown":
                log_error("未找到任何支持的源代码文件", "project_type_detector")
                task_repo.update_task_status(task_id, "failed")
                db.commit()
                return
            elif project_type == "fpga":
                log_info("检测到FPGA项目，使用FPGA审查流程", "project_type_detector")
                # 清除当前日志设置，因为run_fpga_code_review会重新设置
                clear_current_task()
                run_fpga_code_review(file_id, task_id, db, tester_name=tester_name)
                return
            elif project_type == "mixed":
                log_info("检测到混合项目，优先使用C/C++审查流程", "project_type_detector")
                # 对于混合项目，我们可以选择分别处理或者优先处理某种类型
                # 这里选择优先处理C/C++，后续可以扩展为同时处理两种类型
                # 清除当前日志设置，因为run_c_cpp_code_review会重新设置
                clear_current_task()
                run_c_cpp_code_review(file_id, task_id, db, tester_name=tester_name)
                return
            else:  # c_cpp
                log_info("检测到C/C++项目，使用C/C++审查流程", "project_type_detector")
                # 清除当前日志设置，因为run_c_cpp_code_review会重新设置
                clear_current_task()
                run_c_cpp_code_review(file_id, task_id, db, tester_name=tester_name)
                return
                
    finally:
        # 确保清除当前任务的日志设置
        clear_current_task()
        # 记录性能摘要
        performance_analyzer.log_session_summary()
        performance_analyzer.clear_session()

def run_c_cpp_code_review(file_id: int, task_id: int, db: Session, tester_name: str = None):
    """
    C/C++代码审查流程：原有的函数级别审查逻辑
    
    Args:
        file_id: 文件ID
        task_id: 任务ID
        db: 数据库会话
        tester_name: 测试人员姓名
    """
    # 初始化并发日志系统
    task_folder = init_concurrent_task(task_id, file_id, tester_name=tester_name)
    log_info(f"并发日志系统已初始化，任务文件夹: {task_folder.name}", "concurrent_logger")
    set_current_thread_task(task_id, file_id, thread_name="function_main")
    log_concurrent_info("主线程日志上下文已初始化，用于记录解析详情", "concurrent_logger")
    
    # 开始性能分析会话（如果还没有开始）
    performance_analyzer.start_session(task_id, file_id)
    
    try:
        log_info(f"开始执行C/C++代码审查, file_id={file_id}, task_id={task_id}", "cpp_reviewer")
        
        with performance_analyzer.measure_step("数据库初始化"):
            file_repo = FileRepository(db)
            func_repo = FunctionRepository(db)
            prob_repo = ProblemRepository(db)
            task_repo = TaskRepository(db)

            db_file = file_repo.get_file(file_id)
            if not db_file or not db_file.extract_path or not os.path.exists(db_file.extract_path):
                log_error(f"文件或解压路径无效. file_id: {file_id}", "cpp_reviewer")
                task_repo.update_task_status(task_id, "failed")
                db.commit()
                return
            extract_path = db_file.extract_path
        
        directory_file_map: Dict[str, List[str]] = defaultdict(list)
        functions_by_file: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        total_source_files = 0
        
        # 阶段0：构建调用图（用于Agent模式）
        if ENABLE_FUNCTION_REVIEW_AGENT:
            with performance_analyzer.measure_step("调用图构建"):
                log_concurrent_info(f"[函数审查] ========== 阶段0：构建调用图 ==========", "cpp_reviewer")
                
                project_path = Path(extract_path)
                # 将调用图存放在项目自身的根目录下，避免跨项目覆盖
                call_graph_dir = project_path
                call_graph_file = call_graph_dir / "call_graph.json"
                
                # 检查是否已存在调用图
                if not call_graph_file.exists():
                    try:
                        log_concurrent_info(f"[调用图构建] 开始构建项目调用图...", "cpp_reviewer")
                        
                        # 创建调用图目录
                        call_graph_dir.mkdir(parents=True, exist_ok=True)
                        
                        # 构建调用图
                        from ..business_review.tools.call_graph_builder import CallGraphBuilder
                        builder = CallGraphBuilder(extract_path, language='c')
                        call_graph_data = builder.build()
                        
                        # 保存调用图
                        builder.save_to_file(call_graph_file)
                        
                        log_concurrent_info(
                            f"[调用图构建] 完成！函数: {call_graph_data['project']['total_functions']}, "
                            f"文件: {call_graph_data['project']['total_files']}, "
                            f"调用边: {call_graph_data['project']['total_call_edges']}",
                            "cpp_reviewer"
                        )
                    except Exception as e:
                        log_concurrent_error(f"[调用图构建] 失败，但继续执行审查", "cpp_reviewer", e)
                else:
                    log_concurrent_info(f"[调用图构建] 使用已存在的调用图: {call_graph_file}", "cpp_reviewer")

        # 1. Find all C/C++ source files
        with performance_analyzer.measure_step("源文件发现") as step:
            source_files = []
            for ext in ALLOWED_CODE_EXTENSIONS:
                source_files.extend(glob.glob(f"{extract_path}/**/*{ext}", recursive=True))
            
            # 🔧 修复：对文件列表排序，确保每次审查顺序一致
            source_files.sort()
            
            source_file_count = len(source_files)
            total_source_files = source_file_count
            step.add_metadata("file_count", source_file_count)
            
            if not source_files:
                log_error("未找到有效的C/C++源代码文件", "cpp_reviewer")
                task_repo.update_task_status(task_id, "failed")
                db.commit()
                return
            log_info(f"找到 {source_file_count} 个C/C++源文件.", "cpp_reviewer")

            for source_file in source_files:
                rel_path = os.path.relpath(source_file, extract_path)
                directory = os.path.dirname(rel_path) or "."
                directory_file_map[directory].append(os.path.basename(rel_path))

            directory_count = len(directory_file_map)
            step.add_metadata("directory_count", directory_count)
            log_info(f"源代码目录统计: {directory_count} 个目录覆盖 {source_file_count} 个文件", "cpp_reviewer")

            if directory_count:
                preview_dirs = sorted(directory_file_map.keys())[:10]
                log_info(f"目录示例（最多10个）: {preview_dirs}", "cpp_reviewer")

                directory_preview_limit = 30
                file_preview_limit = 8
                for index, dir_path in enumerate(sorted(directory_file_map.keys())):
                    if index >= directory_preview_limit:
                        break
                    files_in_dir = directory_file_map[dir_path]
                    file_preview = files_in_dir[:file_preview_limit]
                    more_suffix = " ...更多" if len(files_in_dir) > file_preview_limit else ""
                    current_dir_label = dir_path or "."
                    log_debug(
                        f"[目录扫描] {current_dir_label}: {len(files_in_dir)} 个文件 -> {file_preview}{more_suffix}",
                        "cpp_reviewer"
                    )

                if directory_count > directory_preview_limit:
                    log_info(
                        f"其余 {directory_count - directory_preview_limit} 个目录的明细将写入解析摘要文件",
                        "cpp_reviewer"
                    )

        # --- PASS 1: Extract all global variables from all files ---
        with performance_analyzer.measure_step("全局变量提取", file_count=len(source_files)) as step:
            log_info("--- Pass 1: 开始提取所有全局变量、宏定义和数组变量 ---", "global_var_extractor")
            all_global_vars: Dict[str, Dict[str, Any]] = {}
            
            for source_file in source_files:
                try:
                    with performance_analyzer.measure_step(f"处理文件: {os.path.basename(source_file)}"):
                        rel_path = os.path.relpath(source_file, extract_path)
                        code, _ = read_file_with_encoding(source_file)
                        if code is None:
                            log_warning(f"读取文件失败，跳过: {source_file}", "global_var_extractor")
                            continue
                        
                        lang = "cpp" if os.path.splitext(source_file)[1].lower() in {".cpp", ".cc", ".cxx", ".hpp", ".hxx"} else "c"
                        
                        # 提取全局变量
                        globals_in_file = extract_globals_from_code(code, language=lang)
                        log_debug(f"在 {rel_path} 中找到 {len(globals_in_file)} 个全局变量.", "global_var_extractor")

                        for g_var in globals_in_file:
                            var_name = g_var['name']
                            if var_name not in all_global_vars:
                                all_global_vars[var_name] = {
                                    'file': rel_path,
                                    'line': g_var['line'],
                                    'code': g_var['code'],
                                    'type': 'variable'
                                }
                        
                        # 提取宏定义
                        macros_in_file = extract_macros_from_code(code, language=lang)
                        log_debug(f"在 {rel_path} 中找到 {len(macros_in_file)} 个宏定义.", "global_var_extractor")

                        for macro in macros_in_file:
                            macro_name = macro['name']
                            if macro_name not in all_global_vars:
                                all_global_vars[macro_name] = {
                                    'file': rel_path,
                                    'line': macro['line'],
                                    'code': macro['code'],
                                    'type': 'macro'
                                }
                        
                        # 提取数组变量
                        arrays_in_file = extract_arrays_from_code(code, language=lang)
                        log_debug(f"在 {rel_path} 中找到 {len(arrays_in_file)} 个数组变量.", "global_var_extractor")

                        for array in arrays_in_file:
                            array_name = array['name']
                            if array_name not in all_global_vars:
                                all_global_vars[array_name] = {
                                    'file': rel_path,
                                    'line': array['line'],
                                    'code': array['code'],
                                    'type': 'array'
                                }
                                
                except Exception as e:
                    log_error(f"Pass 1: 处理文件 {source_file} 时出错", "global_var_extractor", e)

            step.add_metadata("global_vars_count", len(all_global_vars))
            
            log_info(f"--- Pass 1 完成: 共找到 {len(all_global_vars)} 个唯一的全局项目 ---", "global_var_extractor")
            if all_global_vars:
                # 按类型分组统计
                var_count = sum(1 for item in all_global_vars.values() if item['type'] == 'variable')
                macro_count = sum(1 for item in all_global_vars.values() if item['type'] == 'macro')
                array_count = sum(1 for item in all_global_vars.values() if item['type'] == 'array')
                log_info(f"全局项目统计: 变量 {var_count} 个, 宏定义 {macro_count} 个, 数组 {array_count} 个", "global_var_extractor")
                log_debug(f"全局项目列表: {list(all_global_vars.keys())}", "global_var_extractor")

        # --- PASS 2: Extract functions and run AI analysis ---
        with performance_analyzer.measure_step("函数提取") as step:
            log_info("--- Pass 2: 开始提取函数并进行AI分析 ---", "function_analyzer")
            
            all_functions_to_process = []
            function_preview_limit = 10
            file_function_log_limit = 50
            for source_file in source_files:
                try:
                    with performance_analyzer.measure_step(f"提取函数: {os.path.basename(source_file)}"):
                        rel_path = os.path.relpath(source_file, extract_path)
                        file_function_list = functions_by_file[rel_path]

                        code, _ = read_file_with_encoding(source_file)
                        if code is None:
                            log_warning(f"读取文件失败，跳过函数提取: {source_file}", "function_analyzer")
                            continue
                        lang = "cpp" if os.path.splitext(source_file)[1].lower() in {".cpp", ".cc", ".cxx", ".hpp", ".hxx"} else "c"
                        
                        functions_in_file = fp.extract_functions_from_code(code, language=lang)
                        preview_names: List[str] = []
                        for func_data in functions_in_file:
                            func_name = func_data.get('function_name') or func_data.get('name') or "<unknown>"
                            file_function_list.append({
                                "name": func_name,
                                "start_line": func_data.get('start_line'),
                                "end_line": func_data.get('end_line')
                            })
                            if 'function_name' not in func_data and func_name != "<unknown>":
                                func_data['function_name'] = func_name
                            func_data['file_path'] = rel_path
                            all_functions_to_process.append(func_data)
                            if len(preview_names) < function_preview_limit:
                                preview_names.append(func_name)

                        if functions_in_file:
                            more_suffix = " ...更多" if len(functions_in_file) > len(preview_names) else ""
                            log_debug(
                                f"[函数提取] {rel_path}: 发现 {len(functions_in_file)} 个函数 -> {preview_names}{more_suffix}",
                                "function_analyzer"
                            )
                        else:
                            log_debug(f"[函数提取] {rel_path}: 未检测到函数定义", "function_analyzer")

                except Exception as e:
                    log_error(f"Pass 2 (Function Collection): 处理文件 {source_file} 时出错", "function_analyzer", e)

            total_functions = len(all_functions_to_process)
            files_with_functions = len(functions_by_file)
            step.add_metadata("function_count", total_functions)
            step.add_metadata("files_with_functions", files_with_functions)
            
            log_info(f"共找到 {total_functions} 个函数进行分析，覆盖 {files_with_functions} 个源文件。", "function_analyzer")

            logged_files = 0
            for file_path in sorted(functions_by_file.keys()):
                if logged_files >= file_function_log_limit:
                    break
                funcs = functions_by_file[file_path]
                if funcs:
                    preview_names = [func['name'] for func in funcs[:function_preview_limit]]
                    more_suffix = " ...更多" if len(funcs) > function_preview_limit else ""
                    log_debug(
                        f"[函数清单] {file_path}: {len(funcs)} 个函数 -> {preview_names}{more_suffix}",
                        "function_analyzer"
                    )
                else:
                    log_debug(f"[函数清单] {file_path}: 未检测到函数定义", "function_analyzer")
                logged_files += 1
            if len(functions_by_file) > file_function_log_limit:
                log_info(
                    f"其余 {len(functions_by_file) - file_function_log_limit} 个文件的函数列表已写入解析摘要文件",
                    "function_analyzer"
                )

            try:
                logs_subfolder = task_folder / "logs"
                logs_subfolder.mkdir(exist_ok=True)
                parse_summary_path = logs_subfolder / "parse_summary.json"
                directory_entries = [
                    {
                        "path": dir_path or ".",
                        "file_count": len(files),
                        "files": sorted(files)
                    }
                    for dir_path, files in sorted(directory_file_map.items())
                ]
                file_entries = [
                    {
                        "path": file_path,
                        "function_count": len(funcs),
                        "functions": [
                            {
                                "name": func.get("name"),
                                "start_line": func.get("start_line"),
                                "end_line": func.get("end_line")
                            }
                            for func in funcs
                        ]
                    }
                    for file_path, funcs in sorted(functions_by_file.items())
                ]
                parse_summary_payload = {
                    "generated_at": datetime.now().isoformat(),
                    "task_id": task_id,
                    "file_id": file_id,
                    "project_root": extract_path,
                    "total_directories": len(directory_entries),
                    "total_source_files": total_source_files,
                    "total_functions": total_functions,
                    "directories": directory_entries,
                    "files": file_entries
                }
                with open(parse_summary_path, "w", encoding="utf-8") as summary_fp:
                    json.dump(parse_summary_payload, summary_fp, ensure_ascii=False, indent=2)
                log_info(
                    f"解析摘要已生成，可在 {parse_summary_path} 查看详细目录与函数列表",
                    "function_analyzer"
                )
            except Exception as summary_error:
                log_warning(f"写入解析摘要文件失败: {summary_error}", "function_analyzer")
            
            if total_functions == 0:
                log_warning("未找到任何函数进行分析。", "function_analyzer")
                task_repo.update_task_status(task_id, "completed")
                db.commit()
                return

        # AI分析阶段 - 使用并发处理
        with performance_analyzer.measure_step("AI分析阶段", function_count=total_functions) as ai_phase_step:
            log_info(f"开始并发AI分析，最大并发数: {AI_CONCURRENT_REQUESTS}", "concurrent_analyzer")
            _process_functions_concurrently(
                all_functions_to_process,
                file_id,
                task_id,
                db,
                extract_path,
                all_global_vars,
                func_repo,
                prob_repo,
                task_repo,
                already_processed_count=0,
                total_project_functions=total_functions,
            )

        # 完成任务
        with performance_analyzer.measure_step("任务完成"):
            log_info("更新任务状态为completed", "task_manager")
            task_repo.update_task_status(task_id, "completed")
            task_repo.update_task_progress(task_id, 100)  # 设置进度为100%
            db.commit()
            log_info(f"任务 {task_id} 已完成，总共分析了 {total_functions} 个函数", "task_manager")
            
            # 从取消管理器中移除任务
            from ...utils.task_cancel_manager import task_cancel_manager
            task_cancel_manager.unregister_task(task_id)
            log_info(f"任务 {task_id} 已从取消管理器中移除", "task_manager")
        
    finally:
        # 结束主线程日志上下文并写入收尾信息
        clear_current_thread_task()
        # 结束并发任务日志
        finalize_concurrent_task(task_id)
        
        # 清除当前任务的日志设置
        clear_current_task()

# 提供统一的问题结构规范化函数，供功能审查、链路审查等模块复用

def normalize_problem(problem: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "issue_name": problem.get("issue_name") or problem.get("problem_name"),
        "issue_level": problem.get("issue_level"),
        "issue_location": problem.get("issue_location"),
        "file_name": problem.get("file_name"),
        "function_name": problem.get("function_name"),
        "source_code": problem.get("source_code"),
        "problem_reason": problem.get("problem_reason"),
        "description_requirement": problem.get("description_requirement"),
        "description_issue": problem.get("description_issue"),
        "description_location": problem.get("description_location"),
        "description_impact": problem.get("description_impact"),
        "business_rule": problem.get("business_rule"),
        "suggestion": problem.get("suggestion")
    }
