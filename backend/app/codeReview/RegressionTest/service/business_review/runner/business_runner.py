import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List
from pathlib import Path
import os
import glob
import json

from ...ai.openai.client import AIClient
from ....config_database_chain import get_chain_db_session, get_chain_db  # 使用链路审查数据库切换模块
from ....db.sync_task_data import sync_task_to_chain_db
from ....db.repository.task_repo import TaskRepository
from ....db.repository.function_repo import FunctionRepository
from ....db.repository.problem_repo import ProblemRepository
from ....db.repository.file_repo import FileRepository
# ChainRepository已被删除，不再需要导入
# 导入并发日志系统
from ....utils.concurrent_logger import init_concurrent_task, set_current_thread_task, clear_current_thread_task
from ....utils.concurrent_logger import log_concurrent_info, log_concurrent_warning, log_concurrent_error, log_concurrent_debug

# 导入文件扫描相关的工具
from ...ai.parser import function_parser as fp
from ...ai.parser.function_parser import read_file_with_encoding
from ....config import ALLOWED_CODE_EXTENSIONS

from .prompt_business import build_business_prompt
from ..kb.loader import load_kb
from ..index.hierarchy_indexer import build_hierarchy_index
from ..retrieval.retriever import two_stage_retrieve
from ..planner.chain_planner import plan_chains

# 从配置文件导入业务审查并发度
from ....config import BUSINESS_CONCURRENT_REQUESTS

# 业务审查进度缓存（进程内）
_BUSINESS_PROGRESS: Dict[int, Dict[str, Any]] = {}
_PROGRESS_LOCK = threading.Lock()


def _init_progress(task_id: int, total: int):
    with _PROGRESS_LOCK:
        _BUSINESS_PROGRESS[task_id] = {
            "status": "processing",
            "total": total,
            "completed": 0,
            "message": "",
        }


def _update_progress(task_id: int, inc: int = 0, message: str = None):
    with _PROGRESS_LOCK:
        p = _BUSINESS_PROGRESS.get(task_id)
        if not p:
            return
        p["completed"] = min(p["total"], p.get("completed", 0) + inc)
        if message is not None:
            p["message"] = message


def _finalize_progress(task_id: int, status: str, message: str = ""):
    with _PROGRESS_LOCK:
        p = _BUSINESS_PROGRESS.get(task_id)
        if not p:
            _BUSINESS_PROGRESS[task_id] = {"status": status, "total": 0, "completed": 0, "message": message}
            return
        p["status"] = status
        p["message"] = message


def get_progress(task_id: int) -> Dict[str, Any]:
    # 如果内存中有进度数据，直接返回
    with _PROGRESS_LOCK:
        if task_id in _BUSINESS_PROGRESS:
            return _BUSINESS_PROGRESS[task_id]
    
    # 如果内存中没有数据，检查是否是已完成的业务审查任务
    try:
        from ....db.deps import get_db
        from ....db.repository import TaskRepository
        
        db = next(get_chain_db())
        try:
            task_repo = TaskRepository(db)
            db_task = task_repo.get_task(task_id)
            
            if db_task:
                # 检查是否是业务审查任务
                is_business_review = False
                if db_task.task_name and "项目功能级别" in db_task.task_name:
                    is_business_review = True
                elif db_task.task_description and ("软件类型" in db_task.task_description or "入口函数" in db_task.task_description):
                    is_business_review = True
                
                if is_business_review and db_task.status == "completed":
                    # 业务审查任务且已完成，检查是否有业务审查结果
                    from ....db.models.chain_problem import ChainReviewProblem
                    from ....db.models.file_problem import FileReviewProblem
                    
                    chain_problems = db.query(ChainReviewProblem).filter(
                        ChainReviewProblem.task_id == task_id
                    ).count()
                    
                    file_problems = db.query(FileReviewProblem).filter(
                        FileReviewProblem.task_id == task_id
                    ).count()
                    
                    total_problems = chain_problems + file_problems
                    
                    if total_problems > 0:
                        # 有结果表示已完成
                        return {
                            "status": "completed", 
                            "total": 100, 
                            "completed": 100, 
                            "message": f"业务审查已完成，发现{total_problems}个问题",
                            "show_action_buttons": True,
                            "actions": [
                                {
                                    "type": "download",
                                    "label": "下载审查结果",
                                    "url": f"/api/code-review/business/download/{task_id}"
                                },
                                {
                                    "type": "view_code",
                                    "label": "代码视图",
                                    "action": "navigate_to_codemap"
                                }
                            ]
                        }
                    else:
                        # 任务已完成但没有业务问题，可能是没发现问题或保存失败
                        return {
                            "status": "completed", 
                            "total": 100, 
                            "completed": 100, 
                            "message": "业务审查已完成",
                            "show_action_buttons": True,
                            "actions": [
                                {
                                    "type": "download",
                                    "label": "下载审查结果",
                                    "url": f"/api/code-review/business/download/{task_id}"
                                },
                                {
                                    "type": "view_code",
                                    "label": "代码视图",
                                    "action": "navigate_to_codemap"
                                }
                            ]
                        }
                elif is_business_review:
                    # 业务审查任务但未完成
                    return {"status": "processing", "total": 100, "completed": 0, "message": "业务审查进行中"}
        finally:
            db.close()
    except Exception as e:
        # 数据库查询失败，返回默认值
        print(f"查询业务审查进度失败: {e}")
    
    return {"status": "idle", "total": 0, "completed": 0, "message": ""}


def _scan_and_extract_functions(task_id: int, project_root: str):
    """扫描项目文件并提取函数到数据库中"""
    log_concurrent_info(f"开始扫描项目文件并提取函数: {project_root}", "business_runner")
    
    with get_chain_db_session() as db:
        task_repo = TaskRepository(db)
        func_repo = FunctionRepository(db)
        file_repo = FileRepository(db)
        
        # 查找所有源文件
        source_files = []
        for ext in ALLOWED_CODE_EXTENSIONS:
            pattern = f"{project_root}/**/*{ext}"
            found_files = glob.glob(pattern, recursive=True)
            source_files.extend(found_files)
        
        log_concurrent_info(f"找到 {len(source_files)} 个源文件", "business_runner")
        
        if not source_files:
            log_concurrent_warning("未找到任何源文件", "business_runner")
            return
            
        # 获取任务记录
        task = task_repo.get_task(task_id)
        if not task:
            log_concurrent_error(f"任务不存在: {task_id}", "business_runner")
            return
            
        # 查找或创建AnalysisFile记录
        from ....db.models.file import AnalysisFile
        
        # 尝试通过code_file_id找到对应的AnalysisFile记录
        analysis_file = None
        if task.code_file_id:
            analysis_file = file_repo.get_file(task.code_file_id)
        
        if not analysis_file:
            # 如果没找到，创建一个新的AnalysisFile记录
            file_record = {
                "task_id": task_id,
                "file_path": project_root,
                "extract_path": project_root,
                "file_name": os.path.basename(project_root),
                "file_type": "folder",
                "status": "processing"
            }
            analysis_file = file_repo.create_file(file_record)
            db.commit()
            log_concurrent_info(f"创建新的AnalysisFile记录: {analysis_file.id}", "business_runner")
        else:
            # 确保文件记录与当前任务关联
            if analysis_file.task_id != task_id:
                analysis_file.task_id = task_id
                db.commit()
                log_concurrent_info(f"更新AnalysisFile记录的任务关联: {analysis_file.id}", "business_runner")
        
        task_file_id = analysis_file.id
        
        total_functions = 0
        
        # 扫描每个文件并提取函数
        for source_file in source_files:
            try:
                rel_path = os.path.relpath(source_file, project_root)
                log_concurrent_debug(f"处理文件: {rel_path}", "business_runner")
                
                # 读取文件内容
                code, _ = read_file_with_encoding(source_file)
                if code is None:
                    log_concurrent_warning(f"无法读取文件: {source_file}", "business_runner")
                    continue
                
                # 确定语言类型
                ext = os.path.splitext(source_file)[1].lower()
                lang = "cpp" if ext in {".cpp", ".cc", ".cxx", ".hpp", ".hxx"} else "c"
                
                # 提取函数
                functions_in_file = fp.extract_functions_from_code(code, language=lang)
                log_concurrent_debug(f"在 {rel_path} 中找到 {len(functions_in_file)} 个函数", "business_runner")
                
                # 保存函数到数据库
                for func_data in functions_in_file:
                    func_name = func_data.get("function_name", "unknown")
                    func_body = func_data.get("source_code", "")
                    
                    # 检查函数是否已存在（通过file_id和函数名）
                    from ....db.models.function import AnalysisFunction
                    existing_func = db.query(AnalysisFunction).filter(
                        AnalysisFunction.file_id == task_file_id,
                        AnalysisFunction.function_name == func_name,
                        AnalysisFunction.file_path == rel_path
                    ).first()
                    
                    if not existing_func:
                        func_record = {
                            "file_id": task_file_id,  # 使用主任务的file_id
                            "function_name": func_name,
                            "start_line": func_data.get("start_line", 1),  # 函数开始行
                            "end_line": func_data.get("end_line", 1),      # 函数结束行
                            "source_code": func_body,
                            "file_path": rel_path,                         # 文件相对路径
                            "function_description": "",                    # 将在后续步骤中填充
                            "commented_code": func_body
                        }
                        func_repo.create_function(func_record)
                        total_functions += 1
                        log_concurrent_debug(f"保存函数: {func_name} 从文件 {rel_path}", "business_runner")
                
            except Exception as e:
                log_concurrent_error(f"处理文件 {source_file} 时出错", "business_runner", e)
        
        # 提交事务
        db.commit()
        log_concurrent_info(f"函数扫描完成，总共提取了 {total_functions} 个函数", "business_runner")


def _collect_dir_context(project_root: str, max_items: int = 300) -> List[str]:
    root = Path(project_root)
    items: List[str] = []
    for p in root.rglob("*"):
        if len(items) >= max_items:
            break
        try:
            rel = p.relative_to(root)
            items.append(str(rel))
        except Exception:
            continue
    return items


def _prepare_problem_records(task_id: int, func_item, file_name: str, ai_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    problems = ai_result.get("problems", []) or []
    records: List[Dict[str, Any]] = []
    for prob in problems:
        problem_reason = prob.get("problem_reason") or "[Business] 未指明规则"
        issue_level = prob.get("issue_level") or "建议改进"
        issue_name = prob.get("issue_name") or "业务问题"
        issue_location = prob.get("issue_location") or file_name
        description_requirement = prob.get("description_requirement") or ""
        description_issue = prob.get("description_issue") or ""
        description_location = prob.get("description_location") or ""
        description_impact = prob.get("description_impact") or ""

        record = {
            "task_id": task_id,
            "file_id": func_item.file_id,
            "function_id": func_item.id,
            "file_name": file_name,
            "source_code": getattr(func_item, "source_code", "") or "",
            "problem_reason": problem_reason,
            "issue_level": issue_level,
            "issue_name": issue_name,
            "issue_location": issue_location,
            "description_requirement": description_requirement,
            "description_issue": description_issue,
            "description_location": description_location,
            "description_impact": description_impact,
        }
        records.append(record)
    return records


def _compose_query(software_type: str, kb: Dict[str, Any], file_name: str, function_name: str) -> str:
    domain = kb.get("domain") or ""
    defect = (kb.get("defect_text") or "")[:200]
    return f"{software_type} {domain} {file_name} {function_name} {defect}"


def _assemble_rag_context(retrieved: Dict[str, List[Dict[str, Any]]], budget_chars: int = 4000) -> str:
    parts: List[str] = []
    used = 0
    for d in retrieved.get("functions", []):
        snippet = (d.get("text") or "")[:800]
        head = f"# {d.get('file')}::{d.get('function')}\n"
        add = head + snippet + "\n\n"
        if used + len(add) > budget_chars:
            break
        parts.append(add)
        used += len(add)
    for f in retrieved.get("files", []):
        line = f"// {f.get('file')}: {f.get('summary')}\n"
        if used + len(line) > budget_chars:
            break
        parts.append(line)
        used += len(line)
    return "".join(parts)


def _summarize_files(task_id: int, software_type: str, kb: Dict[str, Any], ai_client: AIClient):
    """为任务中的源文件生成功能概述，并发处理多个文件"""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from collections import defaultdict
    
    # 获取业务审查并发数
    from ....config import BUSINESS_CONCURRENT_REQUESTS
    
    # 准备知识库文本（用于AI提示词）
    kb_text = (kb.get('knowledge_text') or '')[:3000]
    typical_defects = (kb.get('typical_defects_text') or '')[:2000]
    
    with get_chain_db_session() as db:
        task_repo = TaskRepository(db)
        func_repo = FunctionRepository(db)
        
        task = task_repo.get_task(task_id)
        if not task:
            return
        
        # 获取任务的所有函数，按file_path分组
        log_concurrent_info(f"[文件概述] 开始收集任务 {task_id} 的函数信息", "business_runner")
        
        all_functions = []
        for file_record in task.files:
            all_functions.extend(file_record.functions)
        
        if not all_functions:
            log_concurrent_warning(f"[文件概述] 任务 {task_id} 未找到任何函数", "business_runner")
            return
        
        # 按源文件路径分组函数
        files_functions = defaultdict(list)
        unknown_count = 0
        for func in all_functions:
            file_path = func.file_path or "unknown"
            if file_path == "unknown":
                unknown_count += 1
            files_functions[file_path].append(func)
        
        log_concurrent_info(f"[文件概述] 找到 {len(files_functions)} 个文件路径，总共 {len(all_functions)} 个函数", "business_runner")
        log_concurrent_info(f"[文件概述] 其中 {unknown_count} 个函数的file_path为空", "business_runner")
        
        # 详细记录所有文件路径
        for file_path, funcs in files_functions.items():
            log_concurrent_debug(f"[文件概述] 文件路径: '{file_path}' -> {len(funcs)} 个函数", "business_runner")
        
        # 过滤有效的源文件（只处理.c/.cpp文件，并尝试找到对应的.h文件）
        valid_files = {}
        invalid_files = {}
        
        # 建立文件路径映射，便于查找配对的头文件
        all_file_paths = set(files_functions.keys())
        
        for file_path, functions in files_functions.items():
            if file_path == "unknown":
                invalid_files[file_path] = f"文件路径为空 ({len(functions)} 个函数)"
            elif file_path.endswith('.zip'):
                invalid_files[file_path] = f"ZIP压缩文件 ({len(functions)} 个函数)"
            elif not (file_path.endswith('.c') or file_path.endswith('.cpp') or file_path.endswith('.cc') or file_path.endswith('.cxx') or file_path.endswith('.C') or file_path.endswith('.CPP')):
                invalid_files[file_path] = f"不是C/C++源文件 ({len(functions)} 个函数)"
            else:
                # 这是一个C/C++源文件，尝试找到对应的头文件
                valid_files[file_path] = {
                    'functions': functions,
                    'header_file': None,
                    'header_functions': []
                }
                
                # 查找对应的头文件
                base_name = file_path.rsplit('.', 1)[0]  # 去除扩展名
                possible_headers = [
                    f"{base_name}.h",
                    f"{base_name}.hpp",
                    f"{base_name}.H",
                    f"{base_name}.HPP"
                ]
                
                for header_path in possible_headers:
                    if header_path in all_file_paths:
                        valid_files[file_path]['header_file'] = header_path
                        valid_files[file_path]['header_functions'] = files_functions[header_path]
                        log_concurrent_info(f"[文件概述] 找到配对头文件: {file_path} <-> {header_path}", "business_runner")
                        break
                
                log_concurrent_info(f"[文件概述] 有效源文件: {file_path} ({len(functions)} 个函数){' [有配对头文件]' if valid_files[file_path]['header_file'] else ' [无配对头文件]'}", "business_runner")
        
        # 记录无效文件
        for file_path, reason in invalid_files.items():
            log_concurrent_warning(f"[文件概述] 跳过文件: {file_path} - {reason}", "business_runner")
        
        log_concurrent_info(f"[文件概述] 过滤结果: 有效源文件 {len(valid_files)} 个，跳过文件 {len(invalid_files)} 个", "business_runner")
        
        if not valid_files:
            log_concurrent_warning(f"[文件概述] 未找到有效的源文件", "business_runner")
            return
        
        # 检查已有概述的缓存
        file_summaries_cache = {}
        
        def _process_single_file(file_path_and_file_info):
            """处理单个源文件的概述生成和业务审查"""
            file_path, file_info = file_path_and_file_info
            functions = file_info['functions']
            header_file = file_info['header_file']
            header_functions = file_info['header_functions']
            thread_id = threading.current_thread().ident
            thread_name = f"business_file_{thread_id}"
            
            # 设置线程任务信息
            set_current_thread_task(task_id, task_id, thread_name)
            
            try:
                log_concurrent_info(f"[线程 {thread_id}] 开始为源文件生成概述并进行业务审查: {file_path}", "business_runner")
                
                # 获取完整文件内容而不是函数片段
                func_count = len(functions)
                
                try:
                    # 获取项目根目录中的真实文件路径
                    # 需要从task中获取项目路径
                    from ....db.repository.task_repo import TaskRepository
                    task_repo = TaskRepository(db)
                    task = task_repo.get_task(task_id)
                    if not task or not task.files:
                        raise Exception("无法获取任务或项目信息")
                    
                    # 从第一个文件记录中获取extract_path作为项目根目录
                    project_root = task.files[0].extract_path
                    if not project_root:
                        raise Exception("无法获取项目根目录")
                    
                    # 读取源文件完整内容
                    log_concurrent_debug(f"[线程 {thread_id}] project_root: {project_root}", "business_runner")
                    log_concurrent_debug(f"[线程 {thread_id}] file_path: {file_path}", "business_runner")
                    
                    source_file_path = os.path.join(project_root, file_path)
                    log_concurrent_debug(f"[线程 {thread_id}] 尝试读取文件: {source_file_path}", "business_runner")
                    
                    source_content = ""
                    if os.path.exists(source_file_path):
                        with open(source_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            source_content = f.read()
                        log_concurrent_debug(f"[线程 {thread_id}] 成功读取源文件: {len(source_content)} 字符", "business_runner")
                    else:
                        log_concurrent_warning(f"[线程 {thread_id}] 源文件不存在: {source_file_path}", "business_runner")
                        source_content = "// 源文件不存在或无法读取"
                    
                    # 读取头文件内容（如果有）
                    header_content = ""
                    if header_file:
                        header_file_path = os.path.join(project_root, header_file)
                        if os.path.exists(header_file_path):
                            with open(header_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                header_content = f.read()
                            log_concurrent_info(f"[线程 {thread_id}] 成功读取配对头文件: {header_file}", "business_runner")
                        else:
                            log_concurrent_warning(f"[线程 {thread_id}] 配对头文件不存在: {header_file_path}", "business_runner")
                    
                    # 组合文件内容
                    if header_content:
                        functions_code_section = f"""## 头文件: {header_file}
```c
{header_content}
```

## 源文件: {file_path}
```c
{source_content}
```"""
                    else:
                        functions_code_section = f"""## 源文件: {file_path}
```c
{source_content}
```"""
                    
                    log_concurrent_info(f"[线程 {thread_id}] 成功读取文件内容: {file_path} (源文件: {len(source_content)} 字符, 头文件: {len(header_content)} 字符)", "business_runner")
                    
                except Exception as e:
                    log_concurrent_error(f"[线程 {thread_id}] 读取文件内容失败: {file_path} - {e}", "business_runner")
                    # 回退到函数片段模式
                    functions_code = []
                    for func in functions[:20]:
                        if func.source_code:
                            functions_code.append(f"## 函数: {func.function_name}\n```c\n{func.source_code}\n```\n")
                        else:
                            functions_code.append(f"## 函数: {func.function_name}\n// 源代码不可用\n")
                    functions_code_section = "\n".join(functions_code) if functions_code else "// 无法获取文件源代码"
                
                # 构建AI提示词（JSON输出）
                prompt = f"""你是资深的{software_type}领域专家。请对以下源文件进行业务功能分析和审查。

【文件信息】
文件路径：{file_path}
函数数量：{func_count}个

【完整文件源代码】
{functions_code_section}

【领域知识】
{kb_text}

【典型缺陷模式】
{typical_defects}

【任务要求】
1. 分析文件的整体业务功能和用途
2. 基于真实文件源代码进行深入的业务审查
3. 重点关注业务逻辑正确性、领域规则符合性
4. 检查代码实现与业务需求的匹配度
5. 结合配对的头文件内容进行整体分析

【输出格式】
严格按照以下JSON格式输出：
{{
  "file_function_summary": "文件实现的业务功能概述，1-3段简洁描述，专注于业务功能而非实现细节",
  "problems": [
    {{
      "file_name": "{os.path.basename(file_path)}",
      "source_code": "从上述源代码中提取的相关代码片段（尽量大段完整，无关代码可用...省略）",
      "problem_reason": "为什么要提出这个问题的原因", 
      "issue_level": "建议改进|一般问题|重要问题",
      "issue_name": "问题名称",
      "issue_location": "{os.path.basename(file_path)}文件的xxx函数",
      "description_requirement": "解释当前代码段实现了什么功能（根据代码分析需求）",
      "description_issue": "详细问题描述",
      "description_location": "首先列出{os.path.basename(file_path)}文件的xxx函数，然后结合大段源代码详细解释问题，源代码段要完整，无关部分用...省略", 
      "description_impact": "可能造成的影响"
    }}
  ]
}}

重要提醒：
- file_function_summary要专注于业务功能概述，避免实现细节
- source_code必须来自上述提供的真实文件源代码，要大段完整
- issue_level必须严格使用"建议改进"、"一般问题"、"重要问题"三个值之一
- issue_location格式必须是"xxx文件的xxx函数"
- description_location必须首先列出具体的文件和函数，然后结合大段源代码解释问题
- 如果没有发现问题，problems数组可以为空
- 基于真实代码进行准确的业务逻辑分析"""
            
                # 记录AI输入
                log_concurrent_info(f"[线程 {thread_id}] 文件 {file_path} 包含 {func_count} 个函数，已获取完整文件源代码{' 和配对头文件' if header_file else ''}", "business_runner")
                log_concurrent_debug(f"[线程 {thread_id}] AI输入提示词（长度: {len(prompt)} 字符）:\n{prompt}", "business_runner")
                
                # 调用AI生成概述和审查
                result, raw = ai_client.call_ai_stream(prompt)
            
                # 记录AI输出
                log_concurrent_info(f"[线程 {thread_id}] AI响应完成: {file_path}", "business_runner")
                log_concurrent_debug(f"[线程 {thread_id}] AI原始响应（长度: {len(raw)} 字符）:\n{raw}", "business_runner")
                
                # 解析AI响应的JSON格式
                try:
                    # 先尝试解析result字典
                    if isinstance(result, dict):
                        ai_response = result
                    else:
                        # 如果result不是字典，尝试解析raw字符串
                        ai_response = json.loads(raw.strip())
                    
                    # 提取文件概述（使用新的合并字段）
                    file_function_summary = ai_response.get('file_function_summary', '').strip()
                    problems_data = ai_response.get('problems', [])
                    
                    # 使用新的合并字段
                    summary_text = file_function_summary
                    
                    if summary_text:
                        # 限制长度并保存到缓存
                        summary_text = summary_text[:4000]
                        file_summaries_cache[file_path] = summary_text
                        log_concurrent_info(f"[线程 {thread_id}] 生成文件概述成功: {file_path}（概述长度: {len(summary_text)} 字符）", "business_runner")
                    
                    # 保存审查问题到数据库
                    if problems_data:
                        _save_file_review_problems(task_id, file_path, problems_data, thread_id)
                        
                    return (file_path, summary_text, len(problems_data))
                    
                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    log_concurrent_error(f"[线程 {thread_id}] 解析AI响应JSON失败: {e}", "business_runner")
                    log_concurrent_debug(f"[线程 {thread_id}] 失败的响应内容:\n{raw}", "business_runner")
                    
                    # 降级处理：提取纯文本概述
                    summary_text = raw.strip() if raw else ""
                    if summary_text:
                        summary_text = summary_text[:4000]
                        file_summaries_cache[file_path] = summary_text
                        log_concurrent_info(f"[线程 {thread_id}] 降级处理-生成文件概述: {file_path}（概述长度: {len(summary_text)} 字符）", "business_runner")
                        return (file_path, summary_text, 0)
                    else:
                        log_concurrent_warning(f"[线程 {thread_id}] 未能生成有效概述: {file_path}", "business_runner")
                        return (file_path, "", 0)
                
            except Exception as e:
                log_concurrent_error(f"[线程 {thread_id}] 处理文件概述失败: {file_path}", "business_runner", e)
                return file_path, "", 0
            finally:
                clear_current_thread_task()
        
        # 并发处理文件概述生成
        log_concurrent_info(f"[文件概述] 启动 {BUSINESS_CONCURRENT_REQUESTS} 个线程并发处理文件概述", "business_runner")
        
        with ThreadPoolExecutor(max_workers=BUSINESS_CONCURRENT_REQUESTS) as executor:
            # 提交任务
            futures = [executor.submit(_process_single_file, item) for item in valid_files.items()]
            
            # 收集结果
            completed_count = 0
            total_problems_found = 0
            for future in as_completed(futures):
                try:
                    file_path, summary, problems_count = future.result()
                    completed_count += 1
                    total_problems_found += problems_count
                    if summary:
                        log_concurrent_info(f"[文件概述] 完成 {completed_count}/{len(valid_files)}: {file_path}（发现 {problems_count} 个问题）", "business_runner")
                    else:
                        log_concurrent_warning(f"[文件概述] 失败 {completed_count}/{len(valid_files)}: {file_path}", "business_runner")
                except Exception as e:
                    log_concurrent_error(f"[文件概述] 任务执行异常", "business_runner", e)
        
        log_concurrent_info(f"[文件概述] 所有文件概述和审查完成，成功: {len([s for s in file_summaries_cache.values() if s])}/{len(valid_files)}，总共发现 {total_problems_found} 个业务问题", "business_runner")

        # 将概述信息存储到数据库（暂时存储到主文件记录的file_summary字段）
        # TODO: 考虑创建专门的源文件概述表
        if file_summaries_cache and task.files:
            main_file = task.files[0]  # 使用主文件记录
            combined_summary = "\n\n".join([f"[{path}]\n{summary}" for path, summary in file_summaries_cache.items() if summary])
            if combined_summary:
                file_repo = FileRepository(db)
                file_repo.update_file(main_file.id, {"file_function_summary": combined_summary[:4000]})
                log_concurrent_info(f"[文件概述] 合并概述已保存到数据库（总长度: {len(combined_summary)} 字符）", "business_runner")


# _save_chains函数已废弃，不再需要保存链路到数据库


# _perform_chain_based_review函数已废弃，现在使用_perform_algorithm_chain_review


def _build_chain_context(task_id: int, chain_data: Dict, project_root: str) -> str:
    """构建链路的完整上下文信息"""
    from ....db.models.function import AnalysisFunction
    
    functions = chain_data.get("functions", [])
    call_edges = chain_data.get("call_edges", [])
    
    context_parts = []
    
    # 添加链路基本信息
    context_parts.append("=== 链路基本信息 ===")
    context_parts.append(f"链路名称: {chain_data.get('name', '未命名链路')}")
    context_parts.append(f"入口点: {chain_data.get('entry_point', '未知')}")
    context_parts.append(f"功能描述: {chain_data.get('rationale', '无描述')}")
    context_parts.append(f"覆盖范围: {chain_data.get('coverage_description', '无描述')}")
    context_parts.append("")
    
    # 添加函数列表
    context_parts.append("=== 链路包含的函数 ===")
    for i, func in enumerate(functions, 1):
        context_parts.append(f"{i}. 文件: {func.get('file', 'unknown')}")
        context_parts.append(f"   函数: {func.get('function', 'unknown')}")
    context_parts.append("")
    
    # 添加调用关系
    if call_edges:
        context_parts.append("=== 函数调用关系 ===")
        for i, edge in enumerate(call_edges, 1):
            caller = edge.get('caller', {})
            callee = edge.get('callee', {})
            context_parts.append(f"{i}. {caller.get('function', 'unknown')} -> {callee.get('function', 'unknown')}")
    context_parts.append("")
    
    # 获取函数的详细代码（从数据库）
    with get_chain_db_session() as db:
        context_parts.append("=== 函数源代码 ===")
        
        for func in functions:
            func_name = func.get('function', 'unknown')
            file_path = func.get('file', 'unknown')
            
            # 从数据库中查找函数代码
            db_func = db.query(AnalysisFunction).filter(
                AnalysisFunction.function_name == func_name,
                AnalysisFunction.file_path == file_path
            ).first()
            
            if db_func and db_func.source_code:
                context_parts.append(f"// 函数: {func_name} 来自文件: {file_path}")
                context_parts.append(db_func.source_code)
                context_parts.append("")
            else:
                context_parts.append(f"// 函数: {func_name} 来自文件: {file_path}")
                context_parts.append("// 代码未找到")
                context_parts.append("")
    
    return "\n".join(context_parts)


def _build_chain_review_prompt(software_type: str, kb: Dict, chain_name: str, 
                              chain_data: Dict, chain_context: str, 
                              dir_context: List[str]) -> str:
    """构建链路审查的AI提示词"""
    
    # 不再使用kb知识库内容
    dir_preview = "\n".join(dir_context[:50])
    
    return f"""
你是资深的软件架构和代码审查专家。请对以下业务功能链路进行深入的业务级审查。

【审查目标】
请从业务功能角度审查整个链路，重点关注：
1. 业务逻辑的正确性和完整性
2. 函数间调用关系的合理性
3. 业务流程的一致性和连贯性
4. 异常处理的完备性
5. 潜在的逻辑错误和边界条件问题

【项目结构概览】
{dir_preview}

【当前审查链路】
{chain_context}

【输出要求】
请以JSON格式输出审查结果：
{{
  "problems": [
    {{
      "file_name": "具体文件名（如main.c）",
      "source_code": "相关的源代码片段",
      "problem_reason": "为什么要提出这个问题的原因",
      "issue_level": "建议改进|一般问题|重要问题", 
      "issue_name": "问题名称",
      "issue_location": "xxx文件的xxx函数",
      "description_requirement": "解释当前代码段实现了什么功能（根据代码分析需求）",
      "description_issue": "详细问题描述",
      "description_location": "首先列出xxx文件的xxx函数，然后结合大段源代码详细解释问题，源代码段要完整，无关部分用...省略",
      "description_impact": "可能造成的影响"
    }}
  ]
}}

注意：
1. 重点关注业务逻辑的正确性和完整性
2. problem_reason应该说明为什么认为这是一个问题，而不是违反了什么规则
3. description_requirement要根据代码分析出实际实现的功能需求
4. 每个问题要包含具体的source_code片段
5. 确保从业务功能角度发现潜在问题
"""


def _perform_algorithm_chain_review(task_id: int, project_root: str, software_type: str, kb: Dict[str, Any], 
                                   entry_function: str, dir_context: List[str], files_docs: List[Dict[str, Any]], 
                                   funcs_docs: List[Dict[str, Any]], ai_client: AIClient, concurrency: int):
    """执行基于算法的链路审查：使用传统算法拆分审查链路，然后让AI审查每个链路"""
    from ..planner.chain_planner import _compact_call_graph
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    log_concurrent_info(f"[链路审查] 开始基于算法的链路审查，入口函数: {entry_function}", "business_runner")
    
    # 获取完整的函数调用关系图
    call_graph = _compact_call_graph(project_root)
    
    log_concurrent_info(f"[链路审查] 获得调用关系图: {len(call_graph.get('nodes', []))} 个节点, {len(call_graph.get('edges', []))} 条边", "business_runner")
    
    # 使用算法生成审查链路
    algorithm_chains = _generate_algorithm_chains(call_graph, entry_function, project_root)
    
    if not algorithm_chains:
        log_concurrent_warning(f"[链路审查] 算法未能生成有效的审查链路", "business_runner")
        return
    
    log_concurrent_info(f"[链路审查] 算法生成了 {len(algorithm_chains)} 个审查链路", "business_runner")
    
    # 不再使用kb知识库，保留变量以保持API兼容性
    kb_text = ""
    typical_defects = ""
    
    # 生成文件概述摘要
    files_summary = "\n".join([f"• {doc['file']}: {doc['summary'][:200]}..." if len(doc['summary']) > 200 
                              else f"• {doc['file']}: {doc['summary']}" 
                              for doc in files_docs[:20]])
    
    total_problems_found = 0
    
    # 遍历算法生成的每个链路进行审查
    reviewed_chains = []
    
    for chain_index, algorithm_chain in enumerate(algorithm_chains, 1):
        chain_name = algorithm_chain.get("name", f"算法链路{chain_index}")
        chain_functions = algorithm_chain.get("functions", [])
        
        log_concurrent_info(f"[链路审查] 开始审查第 {chain_index}/{len(algorithm_chains)} 个链路: {chain_name}，包含 {len(chain_functions)} 个函数", "business_runner")
        
        try:
            # 获取链路中所有函数的真实源代码
            functions_code = _get_chain_functions_code(task_id, chain_functions, project_root)
            
            if not functions_code:
                log_concurrent_warning(f"[链路审查] 无法获取链路 {chain_name} 的函数源代码", "business_runner")
                continue
            
            # 构建包含真实代码的审查提示词（包含"链路实现的功能"字段）
            review_prompt = _build_algorithm_chain_review_prompt(
                software_type, kb_text, typical_defects, algorithm_chain, functions_code
            )
            
            log_concurrent_debug(f"[链路审查] 链路 {chain_name} 审查提示词（长度: {len(review_prompt)} 字符）:\n{review_prompt}", "business_runner")
            
            # 调用AI进行基于真实代码的审查
            review_result, review_raw = ai_client.call_ai_stream(review_prompt)
            log_concurrent_info(f"[链路审查] 链路 {chain_name} 审查完成", "business_runner")
            log_concurrent_debug(f"[链路审查] 链路 {chain_name} 原始响应（长度: {len(review_raw)} 字符）:\n{review_raw}", "business_runner")
            
            # 解析审查结果
            if isinstance(review_result, dict):
                review_data = review_result
            else:
                try:
                    review_data = json.loads(review_raw)
                except json.JSONDecodeError as e:
                    log_concurrent_error(f"[链路审查] 链路 {chain_name} 审查JSON解析失败: {e}", "business_runner")
                    continue
            
            # 处理发现的问题
            problems = review_data.get("problems", [])
            chain_name_ai = review_data.get("chain_name", "")
            chain_function_description = review_data.get("chain_function_description", review_data.get("chain_function", "未描述功能"))
            
            if problems:
                log_concurrent_info(f"[链路审查] 链路 {chain_name} 发现 {len(problems)} 个业务问题", "business_runner")
                
                # 保存问题到数据库（包含链路功能描述）
                _save_algorithm_chain_problems(task_id, algorithm_chain, problems, software_type, chain_index, chain_function_description, chain_name_ai)
                total_problems_found += len(problems)
            else:
                log_concurrent_info(f"[链路审查] 链路 {chain_name} 未发现业务问题", "business_runner")
            
            # 记录已审查的链路
            reviewed_chains.append({
                "name": chain_name,
                "description": algorithm_chain.get("description", ""),
                "function_description": chain_function_description,
                "functions": chain_functions,
                "chain_index": chain_index,
                "problems_count": len(problems)
            })
            
        except Exception as e:
            log_concurrent_error(f"[链路审查] 链路 {chain_name} 审查过程异常: {e}", "business_runner")
            continue
    
    # 审查完成总结
    log_concurrent_info(f"[链路审查] 算法链路审查完成！", "business_runner")
    log_concurrent_info(f"[链路审查] 总共审查了 {len(reviewed_chains)} 个算法生成的链路", "business_runner")
    log_concurrent_info(f"[链路审查] 发现了 {total_problems_found} 个业务问题", "business_runner")
    
    # 详细总结已审查的链路
    for chain in reviewed_chains:
        log_concurrent_info(f"[链路审查] 链路{chain['chain_index']}: {chain['name']} - {chain['problems_count']} 个问题（功能: {chain['function_description']}）", "business_runner")


def _generate_algorithm_chains(call_graph: Dict[str, Any], entry_function: str, project_root: str) -> List[Dict[str, Any]]:
    """使用传统算法生成审查链路"""
    
    log_concurrent_info(f"[算法链路] 开始使用算法生成审查链路，入口函数: {entry_function}", "business_runner")
    
    # 详细调试调用图结构
    log_concurrent_debug(f"[算法链路] 调用图结构: {list(call_graph.keys())}", "business_runner")
    
    nodes = call_graph.get('nodes', [])
    edges = call_graph.get('edges', [])
    
    log_concurrent_debug(f"[算法链路] 节点数量: {len(nodes)}, 边数量: {len(edges)}", "business_runner")
    
    # 调试前几个节点和边的结构
    if nodes:
        log_concurrent_debug(f"[算法链路] 前3个节点示例: {nodes[:3]}", "business_runner")
    if edges:
        log_concurrent_debug(f"[算法链路] 前3个边示例: {edges[:3]}", "business_runner")
    
    if not nodes:
        log_concurrent_warning(f"[算法链路] 调用图为空，无法生成链路", "business_runner")
        return []
    
    # 构建调用关系字典
    call_map = {}  # caller -> [callees]
    reverse_call_map = {}  # callee -> [callers]
    
    # 添加边处理的详细调试
    valid_edges = 0
    invalid_edges = 0
    
    for edge in edges:
        # 尝试多种可能的边字段名称
        caller = edge.get('caller', '') or edge.get('from', '') or edge.get('source', '')
        callee = edge.get('callee', '') or edge.get('to', '') or edge.get('target', '')
        
        if not caller or not callee:
            # 如果使用标准字段找不到，尝试逐个检查
            if 'source' in edge and 'target' in edge:
                caller = edge['source']
                callee = edge['target']
            elif 'from' in edge and 'to' in edge:
                caller = edge['from']
                callee = edge['to']
        
        log_concurrent_debug(f"[算法链路] 处理边: {edge} -> caller={caller}, callee={callee}", "business_runner")
        
        if caller and callee:
            valid_edges += 1
            if caller not in call_map:
                call_map[caller] = []
            call_map[caller].append(callee)
            
            if callee not in reverse_call_map:
                reverse_call_map[callee] = []
            reverse_call_map[callee].append(caller)
        else:
            invalid_edges += 1
            log_concurrent_warning(f"[算法链路] 无效边: {edge}", "business_runner")
    
    log_concurrent_info(f"[算法链路] 边处理结果: 有效边 {valid_edges} 个, 无效边 {invalid_edges} 个", "business_runner")
    
    # 创建函数节点映射
    node_map = {}
    for node in nodes:
        # 尝试多种可能的节点ID字段
        func_name = node.get('id', '') or node.get('name', '') or node.get('function', '')
        if func_name:
            node_map[func_name] = node
            log_concurrent_debug(f"[算法链路] 添加节点: {func_name} -> {node}", "business_runner")
        else:
            log_concurrent_warning(f"[算法链路] 节点缺少ID: {node}", "business_runner")
    
    log_concurrent_info(f"[算法链路] 节点映射: {len(node_map)} 个函数节点", "business_runner")
    log_concurrent_info(f"[算法链路] 调用关系映射: {len(call_map)} 个调用者, {len(reverse_call_map)} 个被调用者", "business_runner")
    
    # 调试入口函数
    log_concurrent_debug(f"[算法链路] 入口函数 '{entry_function}' 是否在节点映射中: {entry_function in node_map}", "business_runner")
    if entry_function not in node_map:
        log_concurrent_warning(f"[算法链路] 入口函数 '{entry_function}' 不在调用图中，可用函数: {list(node_map.keys())[:10]}", "business_runner")
    
    # 算法1：从入口函数开始的深度优先遍历链路
    chains = []
    visited_global = set()
    
    def dfs_chain(start_func, visited_local, path, max_depth=6):
        """深度优先搜索生成链路"""
        if len(path) >= max_depth or start_func in visited_local:
            return
        
        visited_local.add(start_func)
        path.append(start_func)
        
        # 如果路径长度达到3-6个函数，且包含有意义的调用关系，创建一个链路
        if len(path) >= 3:
            chain_functions = []
            for func_name in path:
                if func_name in node_map:
                    node = node_map[func_name]
                    chain_functions.append({
                        "file": node.get('file', 'unknown'),
                        "function": func_name
                    })
            
            if chain_functions:
                # 构建调用边信息
                call_edges = []
                for i in range(len(path) - 1):
                    caller = path[i]
                    callee = path[i + 1]
                    caller_node = node_map.get(caller, {})
                    callee_node = node_map.get(callee, {})
                    call_edges.append({
                        "caller": {
                            "function": caller,
                            "file": caller_node.get('file', 'unknown')
                        },
                        "callee": {
                            "function": callee,
                            "file": callee_node.get('file', 'unknown')
                        }
                    })
                
                chain_name = f"从{path[0]}开始的调用链路{len(chains)+1}"
                chains.append({
                    "name": chain_name,
                    "description": f"从{path[0]}开始，经过{len(path)}个函数的调用链路",
                    "entry_point": start_func,
                    "functions": chain_functions,
                    "call_edges": call_edges,
                    "call_flow": " -> ".join(path)
                })
        
        # 继续深度遍历
        callees = call_map.get(start_func, [])
        for callee in callees:
            if callee not in visited_global:
                dfs_chain(callee, visited_local.copy(), path.copy(), max_depth)
    
    # 从入口函数开始遍历
    if entry_function in node_map:
        dfs_chain(entry_function, set(), [], max_depth=6)
        visited_global.update([entry_function])
    
    # 算法2：识别独立的功能模块（强连通组件的简化版本）
    def find_function_modules():
        """查找相互调用较多的函数组，形成功能模块"""
        module_chains = []
        processed = set()
        
        for func_name in node_map:
            if func_name in processed or func_name in visited_global:
                continue
            
            # 找到与该函数相关联的函数集合
            related_funcs = set([func_name])
            queue = [func_name]
            
            while queue and len(related_funcs) < 8:
                current = queue.pop(0)
                
                # 添加被调用的函数
                callees = call_map.get(current, [])
                for callee in callees:
                    if callee not in related_funcs and callee in node_map:
                        related_funcs.add(callee)
                        if len(related_funcs) < 6:
                            queue.append(callee)
                
                # 添加调用该函数的函数
                callers = reverse_call_map.get(current, [])
                for caller in callers:
                    if caller not in related_funcs and caller in node_map:
                        related_funcs.add(caller)
                        if len(related_funcs) < 6:
                            queue.append(caller)
            
            # 如果找到了一个有意义的模块（3个以上函数）
            if len(related_funcs) >= 3:
                chain_functions = []
                for func_name in related_funcs:
                    node = node_map[func_name]
                    chain_functions.append({
                        "file": node.get('file', 'unknown'),
                        "function": func_name
                    })
                
                # 构建模块内的调用边信息
                call_edges = []
                for func in related_funcs:
                    callees = call_map.get(func, [])
                    for callee in callees:
                        if callee in related_funcs:
                            caller_node = node_map.get(func, {})
                            callee_node = node_map.get(callee, {})
                            call_edges.append({
                                "caller": {
                                    "function": func,
                                    "file": caller_node.get('file', 'unknown')
                                },
                                "callee": {
                                    "function": callee,
                                    "file": callee_node.get('file', 'unknown')
                                }
                            })
                
                module_name = f"功能模块{len(module_chains)+1}"
                module_chains.append({
                    "name": module_name,
                    "description": f"包含{len(related_funcs)}个相互关联函数的功能模块",
                    "entry_point": list(related_funcs)[0],
                    "functions": chain_functions,
                    "call_edges": call_edges,
                    "call_flow": f"模块包含: {', '.join(list(related_funcs)[:5])}"
                })
                
                processed.update(related_funcs)
        
        return module_chains
    
    # 添加功能模块链路
    module_chains = find_function_modules()
    chains.extend(module_chains)
    
    # 限制链路数量，优先保留较长的链路
    chains.sort(key=lambda x: len(x['functions']), reverse=True)
    chains = chains[:10]  # 最多10个链路
    
    log_concurrent_info(f"[算法链路] 算法生成了 {len(chains)} 个审查链路", "business_runner")
    
    for i, chain in enumerate(chains, 1):
        log_concurrent_info(f"[算法链路] 链路{i}: {chain['name']} - {len(chain['functions'])} 个函数", "business_runner")
    
    return chains


def _order_functions_by_calls(functions: List[Dict[str, Any]], call_edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """根据调用关系对函数进行排序（简单的拓扑排序）"""
    if not call_edges:
        return functions
    
    # 构建函数名到函数信息的映射
    func_map = {func.get("function", ""): func for func in functions}
    
    # 构建图
    graph = {}
    in_degree = {}
    
    # 初始化
    for func in functions:
        func_name = func.get("function", "")
        graph[func_name] = []
        in_degree[func_name] = 0
    
    # 构建边
    for edge in call_edges:
        caller = edge.get("caller", {})
        callee = edge.get("callee", {})
        caller_name = caller.get("function", "") if isinstance(caller, dict) else str(caller)
        callee_name = callee.get("function", "") if isinstance(callee, dict) else str(callee)
        
        if caller_name in graph and callee_name in graph:
            graph[caller_name].append(callee_name)
            in_degree[callee_name] += 1
    
    # 拓扑排序
    queue = [func for func in in_degree if in_degree[func] == 0]
    result = []
    
    while queue:
        current = queue.pop(0)
        if current in func_map:
            result.append(func_map[current])
        
        for neighbor in graph.get(current, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    # 如果还有未处理的函数，添加到结果末尾
    processed_names = {func.get("function", "") for func in result}
    for func in functions:
        if func.get("function", "") not in processed_names:
            result.append(func)
    
    return result


def _build_algorithm_chain_review_prompt(software_type: str, kb_text: str, typical_defects: str, 
                                       algorithm_chain: Dict[str, Any], functions_code: Dict[str, str]) -> str:
    """构建算法链路的审查提示词，包含'链路实现的功能'字段和调用关系信息"""
    
    chain_name = algorithm_chain.get("name", "未知链路")
    chain_description = algorithm_chain.get("description", "")
    chain_functions = algorithm_chain.get("functions", [])
    call_edges = algorithm_chain.get("call_edges", [])
    
    # 构建调用关系信息
    call_relationships = []
    if call_edges:
        for edge in call_edges:
            caller = edge.get("caller", {})
            callee = edge.get("callee", {})
            caller_func = caller.get("function", "unknown") if isinstance(caller, dict) else str(caller)
            callee_func = callee.get("function", "unknown") if isinstance(callee, dict) else str(callee)
            call_relationships.append(f"{caller_func} -> {callee_func}")
    
    call_relationships_text = "\n".join(call_relationships) if call_relationships else "无调用关系信息"
    
    # 尝试按调用关系排序函数（简单的拓扑排序）
    ordered_functions = _order_functions_by_calls(chain_functions, call_edges)
    
    # 构建函数代码段（按调用顺序）
    functions_code_section = ""
    for func_info in ordered_functions:
        func_name = func_info.get("function", "unknown")
        file_name = func_info.get("file", "unknown")
        code = functions_code.get(f"{file_name}::{func_name}", functions_code.get(f"{file_name}:{func_name}", "// 代码不可用"))
        functions_code_section += f"\n## 文件: {file_name} 函数: {func_name}\n```c\n{code}\n```\n"
    
    prompt = f"""你是资深的{software_type}领域专家。请对以下业务功能链路进行深入的代码审查。

【链路信息】
链路名称：{chain_name}
链路描述：{chain_description}
包含函数：{len(chain_functions)}个

【函数调用关系】
{call_relationships_text}

【链路函数源代码】（按调用顺序排列）
{functions_code_section}

【审查要求】
1. 分析整个链路实现的业务功能和用途
2. 基于真实函数源代码进行深入的业务逻辑审查
3. 重点关注函数间的协作关系和数据流
4. 检查业务逻辑正确性、领域规则符合性
5. 识别潜在的功能缺陷和业务风险
6. **注意函数调用顺序**：上述函数已按调用关系排序，请按此顺序理解代码执行流程

【输出格式】
严格按照以下JSON格式输出：
{{
  "chain_name": "为这个链路起一个简短的中文名称",
  "chain_function_description": "详细描述这个链路实现的具体业务功能（中文）",
  "problems": [
    {{
      "file_name": "文件名",
      "source_code": "从上述源代码中提取的相关代码片段（尽量大段完整，无关代码可用...省略）",
      "problem_reason": "为什么要提出这个问题的原因（中文）", 
      "issue_level": "建议改进|一般问题|重要问题",
      "issue_name": "问题名称（中文）",
      "issue_location": "xxx文件的xxx函数",
      "description_requirement": "解释当前代码段实现了什么功能（根据代码分析需求，中文）",
      "description_issue": "详细问题描述（中文）",
      "description_location": "首先列出xxx文件的xxx函数，然后结合大段源代码详细解释问题，源代码段要完整，无关部分用...省略（中文）", 
      "description_impact": "可能造成的影响（中文）"
    }}
  ]
}}

重要提醒：
- chain_name必须是简短的中文名称，能够概括链路的核心功能
- chain_function_description必须基于真实代码分析，详细描述链路的完整业务功能（中文）
- 所有问题描述字段（problem_reason、issue_name、description_requirement、description_issue、description_location、description_impact）都必须使用中文
- source_code必须来自上述提供的真实函数源代码
- 如果没有发现问题，problems数组可以为空
- 重点关注链路级别的业务逻辑问题，而非单个函数的实现细节"""

    return prompt


def _save_algorithm_chain_problems(task_id: int, algorithm_chain: Dict[str, Any], problems: List[Dict[str, Any]], 
                                 software_type: str, chain_index: int, chain_function_description: str, chain_name_ai: str = ""):
    """保存算法链路审查发现的问题到数据库，包含链路功能描述"""
    from ....db.repository.chain_problem_repo import ChainProblemRepository
    
    # 使用AI生成的链路名称，如果没有则使用默认名称
    chain_name = chain_name_ai or algorithm_chain.get("name", f"算法链路{chain_index}")
    chain_functions = algorithm_chain.get("functions", [])
    affected_functions = [f"{func.get('file', 'unknown')}:{func.get('function', 'unknown')}" 
                        for func in chain_functions]
    
    # 构建调用链（使用箭头连接函数名）
    call_chain = algorithm_chain.get("call_chain", "")
    if not call_chain and chain_functions:
        func_names = [func.get('function', 'unknown') for func in chain_functions]
        call_chain = " → ".join(func_names)
    
    # 提取领域信息
    domain = software_type.split('/')[0] if '/' in software_type else '未知领域'
    
    log_concurrent_info(f"[算法链路] 为链路 {chain_name} 保存 {len(problems)} 个业务问题", "business_runner")
    
    with get_chain_db_session() as db:
        chain_problem_repo = ChainProblemRepository(db)
        
        for problem in problems:
            # 准备问题记录
            # AI返回的file_name现在是链路名称（如"信号采集与处理链路"）
            ai_file_name = problem.get("file_name") or chain_name
            
            record = {
                "task_id": task_id,
                "chain_name": chain_name,
                "chain_function_description": chain_function_description,
                "entry_function": algorithm_chain.get("entry_function"),
                "affected_functions": json.dumps(affected_functions, ensure_ascii=False),
                "call_chain": call_chain,
                "software_type": software_type,
                "domain": domain,
                
                # 必需字段（不能为空）
                "issue_name": problem.get("issue_name") or f"链路问题{len(problems)}",
                "issue_level": problem.get("issue_level") or "一般问题",  # 默认值改为"一般问题"
                "issue_location": problem.get("issue_location") or problem.get("description_location") or chain_name,
                
                # 问题详细信息
                "file_name": ai_file_name,  # 使用AI返回的链路名称
                "source_code": problem.get("source_code") or "",
                "problem_reason": problem.get("problem_reason") or "未指明原因",
                "description_requirement": problem.get("description_requirement") or "",
                "description_issue": problem.get("description_issue") or "",
                "description_location": problem.get("description_location") or "",
                "description_impact": problem.get("description_impact") or "",
                
                # 业务相关信息
                "business_rule": f"链路功能: {chain_function_description}",
                "suggestion": f"针对{problem.get('issue_name', '业务问题')}的改进建议"
            }
            
            try:
                chain_problem_repo.create_problem(record)
                log_concurrent_debug(f"[算法链路] 保存问题: {problem.get('issue_name', '业务问题')}", "business_runner")
            except Exception as e:
                log_concurrent_error(f"[算法链路] 保存问题失败: {e}", "business_runner")
        
        try:
            db.commit()
            log_concurrent_info(f"[算法链路] 成功保存 {len(problems)} 个链路审查问题到数据库", "business_runner")
        except Exception as e:
            db.rollback()
            log_concurrent_error(f"[算法链路] 提交数据库事务失败: {e}", "business_runner")


def _get_chain_functions_code(task_id: int, chain_functions: List[Dict[str, Any]], project_root: str) -> Dict[str, str]:
    """获取链路中所有函数的真实源代码"""
    from ....db.models.function import AnalysisFunction
    from ....db.models.file import AnalysisFile
    
    log_concurrent_info(f"[代码获取] 开始获取 {len(chain_functions)} 个函数的源代码", "business_runner")
    
    functions_code = {}
    
    with get_chain_db_session() as db:
        for func_info in chain_functions:
            file_path = func_info.get("file", "")
            function_name = func_info.get("function", "")
            
            if not file_path or not function_name:
                log_concurrent_warning(f"[代码获取] 函数信息不完整: {func_info}", "business_runner")
                continue
                
            try:
                log_concurrent_debug(f"[代码获取] 查找函数: {function_name} in {file_path}", "business_runner")
                
                # 从数据库中查询函数 - 修复：通过联表查询获取指定任务下的函数
                # AnalysisFunction 没有 task_id 字段，需要通过 AnalysisFile 关联
                function_records = db.query(AnalysisFunction).join(AnalysisFile).filter(
                    AnalysisFile.task_id == task_id,
                    AnalysisFunction.function_name == function_name
                ).all()
                
                log_concurrent_debug(f"[代码获取] 数据库查询结果: 找到 {len(function_records)} 个同名函数", "business_runner")
                
                # 在结果中找到文件路径匹配的记录
                function_record = None
                for record in function_records:
                    log_concurrent_debug(f"[代码获取] 检查记录: {record.function_name} in {record.file_path}", "business_runner")
                    if record.file_path and (record.file_path.endswith(file_path) or file_path in record.file_path):
                        function_record = record
                        log_concurrent_debug(f"[代码获取] 找到匹配的函数记录", "business_runner")
                        break
                
                # 如果没找到，尝试直接匹配
                if not function_record:
                    log_concurrent_debug(f"[代码获取] 未找到路径匹配的函数，尝试直接匹配", "business_runner")
                    function_record = db.query(AnalysisFunction).join(AnalysisFile).filter(
                        AnalysisFile.task_id == task_id,
                        AnalysisFunction.function_name == function_name
                    ).first()
                
                if function_record and function_record.source_code:
                    # 使用数据库中的函数源代码
                    functions_code[f"{file_path}::{function_name}"] = function_record.source_code
                    log_concurrent_debug(f"[代码获取] 从数据库获取函数: {file_path}::{function_name} ({len(function_record.source_code)} 字符)", "business_runner")
                elif function_record:
                    log_concurrent_warning(f"[代码获取] 数据库中函数无源代码: {function_name}", "business_runner")
                    # 如果数据库中没有源代码，尝试从文件中读取
                    full_path = os.path.join(project_root, file_path)
                    if os.path.exists(full_path):
                        try:
                            with open(full_path, 'r', encoding='utf-8') as f:
                                file_content = f.read()
                                functions_code[f"{file_path}::{function_name}"] = f"// 从文件 {file_path} 读取的内容\n{file_content}"
                                log_concurrent_debug(f"[代码获取] 从文件读取: {file_path} ({len(file_content)} 字符)", "business_runner")
                        except Exception as e:
                            log_concurrent_error(f"[代码获取] 读取文件失败: {full_path} - {e}", "business_runner")
                            functions_code[f"{file_path}::{function_name}"] = f"// 无法读取文件 {file_path}\n// 错误: {e}"
                    else:
                        log_concurrent_warning(f"[代码获取] 文件不存在: {full_path}", "business_runner")
                        functions_code[f"{file_path}::{function_name}"] = f"// 文件不存在: {file_path}"
                else:
                    log_concurrent_warning(f"[代码获取] 数据库中未找到函数: {function_name}", "business_runner")
                    # 如果数据库中没有，尝试从文件中读取
                    full_path = os.path.join(project_root, file_path)
                    if os.path.exists(full_path):
                        try:
                            with open(full_path, 'r', encoding='utf-8') as f:
                                file_content = f.read()
                                functions_code[f"{file_path}::{function_name}"] = f"// 从文件 {file_path} 读取的内容\n{file_content}"
                                log_concurrent_debug(f"[代码获取] 从文件读取: {file_path} ({len(file_content)} 字符)", "business_runner")
                        except Exception as e:
                            log_concurrent_error(f"[代码获取] 读取文件失败: {full_path} - {e}", "business_runner")
                            functions_code[f"{file_path}::{function_name}"] = f"// 无法读取文件 {file_path}\n// 错误: {e}"
                    else:
                        log_concurrent_warning(f"[代码获取] 文件不存在: {full_path}", "business_runner")
                        functions_code[f"{file_path}::{function_name}"] = f"// 文件不存在: {file_path}"
                        
            except Exception as e:
                log_concurrent_error(f"[代码获取] 获取函数 {function_name} 失败: {e}", "business_runner")
                functions_code[f"{file_path}::{function_name}"] = f"// 获取函数源代码失败: {e}"
    
    log_concurrent_info(f"[代码获取] 成功获取 {len(functions_code)} 个函数的源代码", "business_runner")
    return functions_code


def _build_chain_review_prompt_with_code(software_type: str, kb_text: str, typical_defects: str, 
                                        selected_chain: Dict[str, Any], functions_code: Dict[str, str]) -> str:
    """构建包含真实代码的链路审查提示词"""
    
    chain_name = selected_chain.get("name", "未知链路")
    chain_description = selected_chain.get("description", "")
    chain_functions = selected_chain.get("functions", [])
    call_flow = selected_chain.get("call_flow", "")
    
    # 构建函数代码部分
    functions_code_section = "\n".join([
        f"## 函数: {func_key}\n```c\n{code}\n```\n"
        for func_key, code in functions_code.items()
    ])
    
    prompt = f"""你是资深的软件架构和代码审查专家。请基于真实的函数源代码对选定的业务功能链路进行深入审查。

【选定的审查链路】
名称: {chain_name}
描述: {chain_description}
调用流程: {call_flow}
包含函数: {len(chain_functions)} 个

【真实函数源代码】
{functions_code_section}

【审查要求】
1. 基于上述真实源代码进行深入分析
2. 重点关注业务逻辑正确性、调用关系合理性、领域规则符合性
3. 检查代码实现与业务需求的匹配度
4. 识别潜在的技术风险和业务风险
5. source_code 字段必须是真实代码片段，不能编造

【输出格式】
严格按照以下JSON格式输出：
{{
  "problems": [
    {{
      "file_name": "具体文件名（如main.c）",
      "source_code": "从上述真实代码中提取的相关代码片段",
      "problem_reason": "为什么要提出这个问题的原因", 
      "issue_level": "建议改进|一般问题|重要问题",
      "issue_name": "问题名称",
      "issue_location": "xxx文件的xxx函数",
      "description_requirement": "解释当前代码段实现了什么功能（根据代码分析需求）",
      "description_issue": "详细问题描述",
      "description_location": "首先列出xxx文件的xxx函数，然后结合大段源代码详细解释问题，源代码段要完整，无关部分用...省略", 
      "description_impact": "可能造成的影响"
}}
  ]
}}

重要提醒：
- 所有 source_code 必须来自上述提供的真实函数源代码
- 不要编造或推测代码内容
- 如果发现问题，请引用具体的代码行
- 基于真实代码进行准确的业务逻辑分析"""

    return prompt


def _save_file_review_problems(task_id: int, file_path: str, problems: List[Dict[str, Any]], thread_id: int):
    """保存文件审查发现的问题到数据库"""
    from ....db.repository.file_problem_repo import FileProblemRepository
    
    log_concurrent_info(f"[线程 {thread_id}] 为文件 {file_path} 保存 {len(problems)} 个业务问题", "business_runner")
    
    try:
        with get_chain_db_session() as db:
            file_problem_repo = FileProblemRepository(db)
            
            for i, problem in enumerate(problems):
                # 准备问题记录
                record = {
                    "task_id": task_id,
                    "file_name": problem.get("file_name") or os.path.basename(file_path),
                    "file_path": file_path,
                    "software_type": "文件级审查",
                    "domain": "文件级审查",
                    
                    # 必需字段（不能为空）
                    "issue_name": problem.get("issue_name") or f"文件问题{i+1}",
                    "issue_level": problem.get("issue_level") or "建议",
                    "issue_location": problem.get("issue_location") or problem.get("description_location") or file_path,
                    
                    # 问题详细信息
                    "source_code": problem.get("source_code") or "",
                    "problem_reason": problem.get("problem_reason") or "未指明原因",
                    "description_requirement": problem.get("description_requirement") or "",
                    "description_issue": problem.get("description_issue") or "",
                    "description_location": problem.get("description_location") or problem.get("issue_location", ""),
                    "description_impact": problem.get("description_impact") or "",
                    
                    # 业务相关信息
                    "business_rule": None,
                    "suggestion": f"针对{problem.get('issue_name', '业务问题')}的改进建议"
                }
                
                try:
                    file_problem_repo.create_problem(record)
                    log_concurrent_debug(f"[线程 {thread_id}] 保存文件问题: {problem.get('issue_name', '业务问题')}", "business_runner")
                except Exception as e:
                    log_concurrent_error(f"[线程 {thread_id}] 保存文件问题失败: {e}", "business_runner")
            
            try:
                db.commit()
                log_concurrent_info(f"[线程 {thread_id}] 成功保存 {len(problems)} 个文件审查问题到数据库", "business_runner")
            except Exception as e:
                db.rollback()
                log_concurrent_error(f"[线程 {thread_id}] 提交数据库事务失败: {e}", "business_runner")
                
    except Exception as e:
        log_concurrent_error(f"[线程 {thread_id}] 保存文件审查问题时发生异常: {e}", "business_runner")


def _save_iterative_problems(task_id: int, selected_chain: Dict[str, Any], problems: List[Dict[str, Any]], 
                           software_type: str, iteration: int):
    """保存迭代审查发现的问题到数据库"""
    from ....db.repository.chain_problem_repo import ChainProblemRepository
    
    chain_name = selected_chain.get("name", f"第{iteration}轮链路")
    chain_functions = selected_chain.get("functions", [])
    affected_functions = [f"{func.get('file', 'unknown')}:{func.get('function', 'unknown')}" 
                        for func in chain_functions]
    
    # 构建调用链
    call_chain = selected_chain.get("call_chain", "")
    if not call_chain and chain_functions:
        func_names = [func.get('function', 'unknown') for func in chain_functions]
        call_chain = " → ".join(func_names)
    
    # 提取领域信息
    domain = software_type.split('/')[0] if '/' in software_type else '未知领域'
    
    log_concurrent_info(f"[迭代审查] 为链路 {chain_name} 保存 {len(problems)} 个业务问题", "business_runner")
    
    with get_chain_db_session() as db:
        chain_problem_repo = ChainProblemRepository(db)
        
        for problem in problems:
            # 准备问题记录
            # AI返回的file_name现在是链路名称
            ai_file_name = problem.get("file_name") or chain_name
            
            record = {
                "task_id": task_id,
                "chain_name": chain_name,
                "entry_function": selected_chain.get("entry_function"),
                "affected_functions": json.dumps(affected_functions, ensure_ascii=False),
                "call_chain": call_chain,
                "software_type": software_type,
                "domain": domain,
                
                # 必需字段
                "issue_name": problem.get("issue_name") or f"迭代问题{iteration}",
                "issue_level": problem.get("issue_level") or "一般问题",  # 默认值改为"一般问题"
                "issue_location": problem.get("issue_location") or problem.get("description_location") or chain_name,
                
                # 问题详细信息
                "file_name": ai_file_name,  # 使用AI返回的链路名称
                "source_code": problem.get("source_code") or "",
                "problem_reason": problem.get("problem_reason") or "未指明原因",
                "description_requirement": problem.get("description_requirement") or "",
                "description_issue": problem.get("description_issue") or "",
                "description_location": problem.get("description_location") or "",
                "description_impact": problem.get("description_impact") or "",
                
                # 业务相关信息
                "business_rule": None,
                "suggestion": f"针对{problem.get('issue_name', '业务问题')}的改进建议"
            }
            
            try:
                chain_problem_repo.create_problem(record)
                log_concurrent_debug(f"[迭代审查] 保存问题: {problem.get('issue_name', '业务问题')}", "business_runner")
            except Exception as e:
                log_concurrent_error(f"[迭代审查] 保存问题失败: {e}", "business_runner")
        
        try:
            db.commit()
            log_concurrent_info(f"[迭代审查] 成功保存 {len(problems)} 个业务问题到数据库", "business_runner")
        except Exception as e:
            db.rollback()
            log_concurrent_error(f"[迭代审查] 提交数据库事务失败: {e}", "business_runner")


def _prepare_chain_problem_records(task_id: int, chain, ai_result: Dict[str, Any], software_type: str) -> List[Dict[str, Any]]:
    """处理链路审查结果并准备业务问题数据库记录"""
    
    problems = ai_result.get("problems", []) or []
    records: List[Dict[str, Any]] = []
    
    chain_name = chain.chain_name or f"链路{chain.chain_index}"
    
    # 解析链路数据获取涉及的函数列表
    affected_functions = []
    call_chain = ""
    try:
        chain_data = json.loads(chain.chain_json) if chain.chain_json else {}
        functions = chain_data.get("functions", [])
        affected_functions = [f"{func.get('file', 'unknown')}:{func.get('function', 'unknown')}" 
                            for func in functions]
        # 构建调用链
        if functions:
            func_names = [func.get('function', 'unknown') for func in functions]
            call_chain = " → ".join(func_names)
    except Exception as e:
        log_concurrent_warning(f"[链路审查] 解析链路数据失败: {e}", "business_runner")
    
    # 提取领域信息
    domain = software_type.split('/')[0] if '/' in software_type else '未知领域'
    
    log_concurrent_info(f"[链路审查] 为链路 {chain_name} 准备 {len(problems)} 个业务问题记录", "business_runner")
    
    for problem in problems:
        # 新格式字段
        # AI返回的file_name现在是链路名称（如"信号采集与处理链路"）
        file_name = problem.get("file_name") or chain_name
        source_code = problem.get("source_code") or ""
        problem_reason = problem.get("problem_reason") or "未指明原因"
        issue_level = problem.get("issue_level") or "一般问题"  # 默认值改为"一般问题"
        issue_name = problem.get("issue_name") or "业务问题"
        issue_location = problem.get("issue_location") or chain_name
        description_requirement = problem.get("description_requirement") or ""
        description_issue = problem.get("description_issue") or ""
        description_location = problem.get("description_location") or ""
        description_impact = problem.get("description_impact") or ""

        record = {
            "task_id": task_id,
            "chain_id": chain.id,
            # 新格式字段
            "file_name": file_name,
            "source_code": source_code,
            "problem_reason": problem_reason,
            "issue_level": issue_level,
            "issue_name": issue_name,
            "issue_location": issue_location,
            "description_requirement": description_requirement,
            "description_issue": description_issue,
            "description_location": description_location,
            "description_impact": description_impact,
            # 元数据字段
            "chain_name": chain_name,
            "affected_functions": json.dumps(affected_functions, ensure_ascii=False),
            "call_chain": call_chain,
            "software_type": software_type,
            "domain": domain,
        }
        records.append(record)
    
    return records




def run(task_id: int, project_root: str, software_type: str, entry_function: str = "main", options: Dict[str, Any] = None):
    options = options or {}
    concurrency = int(options.get("concurrency", BUSINESS_CONCURRENT_REQUESTS))

    # 初始化业务审查的并发日志系统
    # 注意：由于业务审查处理的是整个项目而不是单个文件，我们使用task_id作为file_id
    task_folder = init_concurrent_task(task_id, task_id)
    
    # 设置当前线程的任务信息（这是关键！）
    try:
        main_thread_id = threading.current_thread().ident
        main_thread_name = f"business_main_{main_thread_id}"
        set_current_thread_task(task_id, task_id, main_thread_name)

        log_concurrent_info(f"业务审查启动 | task_id={task_id} type={software_type} entry={entry_function}", "business_runner")
        log_concurrent_info(f"业务审查并发日志系统已初始化，任务文件夹: {task_folder.name}", "business_runner")
    except Exception as e:
        # 如果并发日志系统失败，至少输出到控制台和文件
        print(f"❌ 业务审查日志系统初始化失败: {e}")
        import traceback
        traceback.print_exc()
        # 尝试写入general.log
        try:
            with open("backend/logs/general.log", "a", encoding="utf-8") as f:
                f.write(f"[ERROR] 业务审查日志系统初始化失败: {e}\n")
                f.write(traceback.format_exc())
        except:
            pass
        raise

    try:
        # 初始化进度系统
        _init_progress(task_id, total=100)  # 总进度100，按阶段分配
        _update_progress(task_id, inc=0, message="开始业务审查...")
        
        # 阶段0a：构建调用图（供AI工具使用）
        log_concurrent_info("[功能审查] ========== 阶段0a：构建调用图 ==========", "business_runner")
        _update_progress(task_id, inc=2, message="构建调用图...")
        
        project_path = Path(project_root)
        call_graph_dir = project_path.parent / "call_graph"
        call_graph_file = call_graph_dir / "call_graph.json"
        
        # 检查是否已存在调用图
        if not call_graph_file.exists():
            try:
                log_concurrent_info(f"[调用图构建] 开始构建项目调用图...", "business_runner")
                
                # 创建调用图目录
                call_graph_dir.mkdir(parents=True, exist_ok=True)
                
                # 构建调用图
                from ..tools.call_graph_builder import CallGraphBuilder
                builder = CallGraphBuilder(project_root, language='c')
                call_graph_data = builder.build()
                
                # 保存调用图
                builder.save_to_file(call_graph_file)
                
                log_concurrent_info(
                    f"[调用图构建] 完成！函数: {call_graph_data['project']['total_functions']}, "
                    f"文件: {call_graph_data['project']['total_files']}, "
                    f"调用边: {call_graph_data['project']['total_call_edges']}",
                    "business_runner"
                )
            except Exception as e:
                log_concurrent_error(f"[调用图构建] 失败，但继续执行审查", "business_runner", e)
        else:
            log_concurrent_info(f"[调用图构建] 使用已存在的调用图: {call_graph_file}", "business_runner")
        
        # 阶段0b：扫描项目文件并提取函数到数据库（如果尚未扫描）
        log_concurrent_info("阶段0b：开始文件扫描和函数提取", "business_runner")
        _update_progress(task_id, inc=3, message="扫描项目文件...")
        _scan_and_extract_functions(task_id, project_root)

        # 不再加载kb知识库，改为空字典以保持API兼容性
        kb = {}
        dir_context = _collect_dir_context(project_root)

        ai_client = AIClient()
        _update_progress(task_id, inc=10, message="准备AI客户端...")

        # 阶段A：文件级功能概述（写入DB，供RAG/规划使用）
        log_concurrent_info("阶段A：开始文件功能概述生成", "business_runner")
        _update_progress(task_id, inc=5, message="开始文件概述生成...")
        _summarize_files(task_id, software_type, kb, ai_client)
        _update_progress(task_id, inc=30, message="文件概述生成完成")

        # 重建分层索引（优先使用 file_summary）
        log_concurrent_info("阶段A2：开始重建分层索引", "business_runner")
        _update_progress(task_id, inc=5, message="重建分层索引...")
        index = build_hierarchy_index(task_id)
        files_docs = index.get("files", [])
        funcs_docs = index.get("functions", [])

        # 阶段B：算法链路审查（替代AI链路选择）
        log_concurrent_info("阶段B：开始基于算法的链路审查", "business_runner")
        _update_progress(task_id, inc=5, message="开始链路审查...")
        _perform_algorithm_chain_review(task_id, project_root, software_type, kb, entry_function, dir_context, files_docs, funcs_docs, ai_client, concurrency)
        _update_progress(task_id, inc=40, message="链路审查完成")
        
        # 完成所有阶段
        _finalize_progress(task_id, "completed", "业务审查已完成")

    except Exception as e:
        # 出现异常时标记为失败
        log_concurrent_error(f"业务审查执行失败: {e}", "business_runner")
        _finalize_progress(task_id, "failed", f"业务审查失败: {str(e)}")
        raise
    finally:
        # 清理并发日志系统
        log_concurrent_info("业务审查完成，清理日志系统", "business_runner")
        clear_current_thread_task()


def run_in_background(task_id: int, project_root: str, software_type: str, entry_function: str = "main", options: Dict[str, Any] = None):
    th = threading.Thread(target=run, args=(task_id, project_root, software_type, entry_function, options or {}), daemon=True)
    th.start() 