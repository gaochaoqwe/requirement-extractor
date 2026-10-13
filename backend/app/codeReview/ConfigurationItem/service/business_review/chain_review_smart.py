"""
智能链路审查 - 渐进式功能发现

核心流程：
1. 渐进式功能发现（多轮迭代）
   - Round 1: 目录结构分析
   - Round 2: 函数签名分析
   - Round 3: main函数验证
2. 分批审查每个功能模块
3. 生成问题单
4. 支持实时进度推送

使用外部记忆文件支持多轮迭代和进度追踪
"""
import json
import shutil
import inspect
from typing import Dict, Any, List, cast, Literal
from pathlib import Path

from .planner.progressive_discovery import ProgressiveDiscovery
from .executor.smart_chain_executor import SmartChainExecutor
from .function_comment_runner import start_function_comment_task_async
from .tools.call_graph_builder import CallGraphBuilder
from .tools.fpga_support import detect_chain_review_language, save_fpga_call_graph
from ..ai.parser.function_parser import extract_functions_from_code, read_file_with_encoding
from .memory.memory_manager import MemoryManager
from ...config_database_chain import get_chain_db_session  # 使用链路审查数据库切换模块
from ...db.sync_task_data import sync_task_to_chain_db
from ...db.repository.problem_repo import ProblemRepository
from ...utils.concurrent_logger import log_concurrent_info, log_concurrent_warning, log_concurrent_debug, log_concurrent_error, init_concurrent_task


def run_smart_chain_review(
    task_id: int,
    project_root: str,
    file_id: int,
    entry_function: str,
    kb: Dict[str, Any],
    requirement_text: str = None
) -> Dict[str, Any]:
    """
    运行智能链路审查
    
    Args:
        task_id: 任务ID
        project_root: 项目根目录
        file_id: 文件ID
        entry_function: 入口函数
        kb: 知识库
        
    Returns:
        审查结果统计
    """
    # 初始化日志文件夹
    log_folder = init_concurrent_task(task_id, file_id)
    
    log_concurrent_info(f"[智能链路审查] 任务 {task_id} 开始", "smart_chain_review")
    log_concurrent_info(f"[智能链路审查] 日志文件夹: {log_folder}", "smart_chain_review")
    log_concurrent_info(f"[智能链路审查] 入口函数: {entry_function}", "smart_chain_review")
    
    # 同步任务数据到链路审查数据库
    log_concurrent_info(f"[智能链路审查] 同步任务数据到链路审查数据库...", "smart_chain_review")
    if not sync_task_to_chain_db(task_id):
        log_concurrent_error(f"[智能链路审查] 任务数据同步失败", "smart_chain_review")
        return {
            "status": "sync_failed",
            "features_count": 0,
            "problems_count": 0
        }
    log_concurrent_info(f"[智能链路审查] 任务数据同步成功", "smart_chain_review")
    
    # 阶段0：构建调用图（预处理）
    log_concurrent_info(f"[智能链路审查] ========== 阶段0：构建调用图 ==========", "smart_chain_review")
    
    project_path = Path(project_root)
    review_language = detect_chain_review_language(project_root)
    call_graph_dir = project_path / "call_graph"
    call_graph_file = call_graph_dir / "call_graph.json"
    log_concurrent_info(f"[智能链路审查] 自动识别项目语言: {review_language}", "smart_chain_review")

    should_build_call_graph = True
    if call_graph_file.exists():
        try:
            with open(call_graph_file, 'r', encoding='utf-8') as f:
                existing_call_graph = json.load(f)
            existing_root = (existing_call_graph.get('project') or {}).get('root')
            if existing_root == str(project_path):
                should_build_call_graph = False
        except Exception:
            should_build_call_graph = True

    # 检查是否已存在调用图
    if should_build_call_graph:
        try:
            try:
                builder_impl_file = inspect.getsourcefile(CallGraphBuilder) or ""
            except Exception:
                builder_impl_file = ""
            log_concurrent_info(
                f"[调用图构建] CallGraphBuilder 实现: {CallGraphBuilder.__module__} ({builder_impl_file})",
                "smart_chain_review",
            )
            log_concurrent_info(f"[调用图构建] 开始构建项目调用图...", "smart_chain_review")
            log_concurrent_info(f"[调用图构建] 输出路径: {call_graph_file}", "smart_chain_review")
            
            # 创建调用图目录
            call_graph_dir.mkdir(parents=True, exist_ok=True)
            
            # 构建调用图
            if review_language == 'fpga':
                call_graph_data = save_fpga_call_graph(project_root, call_graph_file)
                log_concurrent_info("[调用图构建] FPGA项目使用模块级调用图摘要", "smart_chain_review")
            else:
                builder = CallGraphBuilder(project_root, language='c')
                log_concurrent_info(
                    f"[调用图构建] tree_sitter_enabled={getattr(builder, 'ts_enabled', False)}",
                    "smart_chain_review",
                )
                call_graph_data = builder.build()
                
                # 保存调用图
                builder.save_to_file(call_graph_file)
            
            log_concurrent_info(
                f"[调用图构建] 完成！函数: {call_graph_data['project']['total_functions']}, "
                f"文件: {call_graph_data['project']['total_files']}, "
                f"调用边: {call_graph_data['project']['total_call_edges']}",
                "smart_chain_review"
            )

            try:
                func_names = []
                for _fid, f in (call_graph_data.get('functions') or {}).items():
                    name = (f or {}).get('name')
                    if name:
                        func_names.append(name)
                sample = ", ".join(func_names[:12])
                log_concurrent_info(
                    f"[调用图构建] 函数名抽样(前12个): {sample}",
                    "smart_chain_review",
                )
            except Exception as e:
                log_concurrent_warning(
                    f"[调用图构建] 函数名抽样失败: {e}",
                    "smart_chain_review",
                )
        except Exception as e:
            log_concurrent_error(f"[调用图构建] 失败，但继续执行审查", "smart_chain_review", e)
    else:
        log_concurrent_info(f"[调用图构建] 使用已存在的调用图: {call_graph_file}", "smart_chain_review")

    try:
        memory_manager = MemoryManager(task_id, project_root)
        memory_call_graph_file = memory_manager.memory_dir / "call_graph.json"
        if call_graph_file.exists():
            shutil.copy2(call_graph_file, memory_call_graph_file)
            log_concurrent_info(
                f"[调用图构建] 已同步调用图到记忆目录: {memory_call_graph_file}",
                "smart_chain_review",
            )
        else:
            log_concurrent_warning(
                f"[调用图构建] 调用图文件不存在，无法同步到记忆目录: {call_graph_file}",
                "smart_chain_review",
            )
    except Exception as e:
        log_concurrent_warning(f"[调用图构建] 同步调用图到记忆目录失败", "smart_chain_review", e)
    
    # 并行启动函数注释任务（不阻塞链路审查）
    log_concurrent_info(f"[智能链路审查] 启动并行函数注释任务...", "smart_chain_review")
    if review_language != 'fpga':
        start_function_comment_task_async(task_id, project_root)

    # 阶段1：渐进式功能发现
    log_concurrent_info(f"[智能链路审查] ========== 阶段1：渐进式功能发现 ==========", "smart_chain_review")
    
    log_concurrent_info(f"[智能链路审查] 使用渐进式多轮发现模式", "smart_chain_review")
    
    # 创建渐进式发现器
    progressive = ProgressiveDiscovery(
        task_id=task_id,
        project_root=project_root,
        language='fpga' if review_language == 'fpga' else 'c',
        entry_function=entry_function,
        requirement_text=requirement_text
    )
    
    # 运行渐进式发现
    discovery_result = progressive.run_discovery()
    
    # 从记忆中提取功能列表
    memory = progressive.memory.load_latest()
    features = memory.get("features", []) if memory else []
    
    log_concurrent_info(
        f"[智能链路审查] 渐进式发现完成，共 {discovery_result.get('total_rounds')} 轮",
        "smart_chain_review"
    )
    log_concurrent_info(
        f"[智能链路审查] 记忆文件: {discovery_result.get('memory_path')}",
        "smart_chain_review"
    )
    
    if not features:
        log_concurrent_warning(f"[智能链路审查] 未发现任何功能模块，审查终止", "smart_chain_review")
        return {
            "status": "no_features",
            "features_count": 0,
            "problems_count": 0
        }
    
    log_concurrent_info(f"[智能链路审查] 发现 {len(features)} 个功能模块", "smart_chain_review")
    
    # 阶段2：逐个审查功能模块
    log_concurrent_info(f"[智能链路审查] ========== 阶段2：分批审查 ==========", "smart_chain_review")
    
    # 标记发现阶段完成，审查阶段开始
    progressive.memory.mark_discovery_complete()
    progressive.memory.start_review()
    
    # 扁平化功能列表（包含所有子功能），有子章节时跳过父章节
    def flatten_features(features_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """递归扁平化功能列表：若某节点有子功能，则只审查子功能，跳过该父节点本身"""
        flattened = []
        for feature in features_list:
            sub_features = feature.get('sub_features', []) or []
            if sub_features:
                # 有子章节：只递归审查子章节，跳过父章节本身
                flattened.extend(flatten_features(sub_features))
            else:
                # 叶子节点：直接审查
                flattened.append(feature)
        return flattened
    
    all_features = flatten_features(features)
    log_concurrent_info(
        f"[智能链路审查] 扁平化后共 {len(all_features)} 个叶子功能（有子章节的父章节已跳过）",
        "smart_chain_review"
    )
    
    # 更新审查阶段的总功能数
    progressive.memory.set_review_total_features(len(all_features))
    
    executor = SmartChainExecutor(project_root, session_id=f"task_{task_id}", language='fpga' if review_language == 'fpga' else 'c')
    
    total_problems = 0
    feature_results = []
    
    for i, feature in enumerate(all_features, 1):
        feature_name = feature.get('name', f'功能{i}')
        log_concurrent_info(
            f"[智能链路审查] 审查功能 {i}/{len(all_features)}: {feature_name}",
            "smart_chain_review"
        )
        
        # 审查单个功能
        problems, ai_feature_description = executor.review_feature(feature, kb)
        # 记录AI原始输出，方便定位为何没有问题
        log_concurrent_debug(
            f"[智能链路审查] 功能 {feature_name} AI原始输出: {json.dumps(problems, ensure_ascii=False)}",
            "smart_chain_review"
        )
        log_concurrent_info(
            f"[智能链路审查] 功能 {feature_name} AI功能描述: {ai_feature_description}",
            "smart_chain_review"
        )
        
        log_concurrent_info(
            f"[智能链路审查] 功能 {feature_name} 发现 {len(problems)} 个问题",
            "smart_chain_review"
        )
        
        # 保存问题到数据库（有问题时保存，同时保存功能描述；无问题时也单独保存功能描述）
        if problems:
            _save_chain_problems(task_id, feature, problems, ai_feature_description, project_root)
            total_problems += len(problems)
        elif ai_feature_description:
            # 即使没有问题，也保存一条仅含功能描述的占位记录，供前端显示
            _save_chain_description_only(task_id, feature, ai_feature_description)
        
        feature_results.append({
            "feature_name": feature_name,
            "problems_count": len(problems)
        })
        
        # 更新审查进度到memory
        progressive.memory.update_review_progress(i)
    
    # 标记审查阶段完成
    progressive.memory.mark_review_complete()
    
    # 阶段3：生成总结
    log_concurrent_info(f"[智能链路审查] ========== 审查完成 ==========", "smart_chain_review")
    log_concurrent_info(f"[智能链路审查] 共审查 {len(all_features)} 个功能模块（包含子功能）", "smart_chain_review")
    log_concurrent_info(f"[智能链路审查] 共发现 {total_problems} 个问题", "smart_chain_review")
    
    return {
        "status": "completed",
        "features_count": len(all_features),
        "problems_count": total_problems,
        "feature_results": feature_results
    }


def _build_function_aware_chain_snippet(function_code: str, line_no: int = 0, context: int = 3) -> str:
    source = (function_code or '').strip('\n')
    if not source:
        return ''

    lines = source.splitlines()
    if not lines:
        return ''

    if line_no <= 0 or line_no > len(lines):
        line_no = 1

    target_idx = line_no - 1
    open_idx = 0
    for idx, line in enumerate(lines):
        if '{' in line:
            open_idx = idx
            break

    close_idx = len(lines) - 1
    depth = 0
    seen_open = False
    for idx in range(open_idx, len(lines)):
        for char in lines[idx]:
            if char == '{':
                depth += 1
                seen_open = True
            elif char == '}' and seen_open:
                depth -= 1
                if depth == 0:
                    close_idx = idx
                    break
        if seen_open and depth == 0:
            break

    context_start = max(open_idx + 1, target_idx - context)
    context_end = min(close_idx - 1, target_idx + context)

    snippet = []
    snippet.extend(lines[:open_idx + 1])
    if context_start > open_idx + 1:
        snippet.append('......')
    if context_start <= context_end:
        snippet.extend(lines[context_start:context_end + 1])
    if context_end < close_idx - 1:
        snippet.append('......')
    if close_idx > open_idx:
        snippet.append(lines[close_idx])

    return '\n'.join(snippet)


def _extract_chain_location_info(description_location: str) -> Dict[str, Any]:
    location = description_location or ''
    result: Dict[str, Any] = {'file_path': '', 'function_name': '', 'line_no': 0}

    file_match = __import__('re').search(r'(.+?)文件的(.+?)函数的(\d+)(?:\s*-\s*\d+)?\s*行', location)
    if file_match:
        result['file_path'] = file_match.group(1).strip()
        result['function_name'] = file_match.group(2).strip()
        result['line_no'] = int(file_match.group(3))
        return result

    line_match = __import__('re').search(r'(\d+)(?:\s*-\s*\d+)?\s*行', location)
    if line_match:
        result['line_no'] = int(line_match.group(1))
    return result


def _resolve_chain_function_source(project_root: str, description_location: str, fallback_source: str) -> Dict[str, Any]:
    info = _extract_chain_location_info(description_location)
    fallback = (fallback_source or '').strip('\n')
    if fallback and '{' in fallback and '}' in fallback:
        return {'source_code': fallback, 'start_line': 1, 'line_no': info.get('line_no') or 1}

    root = Path(project_root) if project_root else None
    file_hint = str(info.get('file_path') or '').replace('\\', '/').strip()
    function_name = str(info.get('function_name') or '').strip()
    if not root or not root.exists() or not file_hint or not function_name:
        return {'source_code': fallback, 'start_line': 1, 'line_no': info.get('line_no') or 1}

    candidates = []
    direct = root / file_hint
    if direct.exists():
        candidates.append(direct)
    else:
        for path in root.rglob(Path(file_hint).name):
            normalized = str(path.relative_to(root)).replace('\\', '/')
            if normalized.endswith(file_hint) or file_hint.endswith(normalized) or path.name == Path(file_hint).name:
                candidates.append(path)

    for path in candidates:
        try:
            code, _ = read_file_with_encoding(str(path))
            ext = path.suffix.lower()
            language = 'cpp' if ext in {'.cpp', '.cc', '.cxx', '.hpp', '.hxx'} else 'c'
            for func in extract_functions_from_code(code, language=language):
                if (func.get('function_name') or func.get('name')) == function_name:
                    return {
                        'source_code': func.get('source_code') or fallback,
                        'start_line': func.get('start_line') or 1,
                        'line_no': info.get('line_no') or 1,
                    }
        except Exception as exc:
            log_concurrent_warning(f"[链路源码片段] 解析函数源码失败: {path}, {exc}", "smart_chain_review")

    return {'source_code': fallback, 'start_line': 1, 'line_no': info.get('line_no') or 1}


def _ensure_description_location_source(description_location: str, source_code: str, project_root: str = '') -> str:
    location = (description_location or '').strip()
    if not location:
        return location

    if any(marker in location for marker in ('源代码为：', '源程序为：', '源代码为:', '源程序为:')):
        return location

    code = (source_code or '').strip('\n')
    if not code:
        return location

    return f"{location}源代码为：\n{code}"


def _ensure_description_location_source(description_location: str, source_code: str, project_root: str = '') -> str:
    location = (description_location or '').strip()
    if not location:
        return location

    marker_match = __import__('re').search(r'(源代码为：|源程序为：|源代码为:|源程序为:)', location)
    prefix = location[:marker_match.start()].rstrip() if marker_match else location
    marker = marker_match.group(1) if marker_match else '源代码为：'

    resolved = _resolve_chain_function_source(project_root, location, source_code)
    code = (resolved.get('source_code') or source_code or '').strip('\n')
    if not code:
        return location

    line_no = int(resolved.get('line_no') or 1)
    start_line = int(resolved.get('start_line') or 1)
    relative_line = line_no - start_line + 1
    snippet_line = relative_line if relative_line > 0 else line_no
    snippet = _build_function_aware_chain_snippet(code, snippet_line)
    if not snippet:
        return location

    return f"{prefix}{marker}\n{snippet}"


def _save_chain_problems(task_id: int, feature: Dict[str, Any], problems: List[Dict[str, Any]], ai_feature_description: str = '', project_root: str = ''):
    """保存链路审查问题到数据库"""
    try:
        feature_name = feature.get('name', '未命名功能')
        # 优先使用 AI 审查后生成的功能描述，其次 fallback 到 feature 的 description 字段
        feature_description = ai_feature_description or feature.get('description', f"智能发现的功能模块: {feature_name}")
        call_chain = feature.get('call_chain', '')  # 提取调用链路
        
        with get_chain_db_session() as db:
            from ...db.models_chain import ChainReviewProblem
            
            for problem in problems:
                # AI返回的file_name现在是链路名称（如"信号采集与处理链路"）
                # 如果AI没有返回file_name，使用feature_name作为备用
                ai_file_name = problem.get('file_name', feature_name)
                source_code = problem.get('source_code', '')
                description_location = _ensure_description_location_source(
                    problem.get('description_location', ''),
                    source_code,
                    project_root,
                )
                
                chain_problem = ChainReviewProblem(
                    task_id=task_id,
                    chain_name=feature_name,
                    chain_function_description=feature_description,
                    call_chain=call_chain,
                    file_name=ai_file_name,  # 使用AI返回的链路名称
                    source_code=source_code,
                    problem_reason=problem.get('problem_reason', ''),
                    issue_level=problem.get('issue_level', '一般问题'),  # 默认值改为"一般问题"
                    issue_name=problem.get('issue_name', '业务问题'),
                    issue_location=problem.get('issue_location', ''),
                    description_requirement=problem.get('description_requirement', ''),
                    description_issue=problem.get('description_issue', ''),
                    description_location=description_location,
                    description_impact=problem.get('description_impact', '')
                )
                db.add(chain_problem)
            
            db.commit()
            log_concurrent_info(f"[数据库] 保存 {len(problems)} 个链路问题: {feature_name}", "smart_chain_review")
            
    except Exception as e:
        log_concurrent_warning(f"[数据库] 保存链路问题失败: {e}", "smart_chain_review")


def _save_chain_description_only(task_id: int, feature: Dict[str, Any], ai_feature_description: str):
    """当功能无问题时，保存一条仅含功能描述的占位记录，供前端第四栏显示功能介绍"""
    try:
        feature_name = feature.get('name', '未命名功能')
        call_chain = feature.get('call_chain', '')

        with get_chain_db_session() as db:
            from ...db.models_chain import ChainReviewProblem

            placeholder = ChainReviewProblem(
                task_id=task_id,
                chain_name=feature_name,
                chain_function_description=ai_feature_description,
                call_chain=call_chain,
                issue_name='无问题',
                issue_level='建议改进',
                file_name=feature_name,
            )
            db.add(placeholder)
            db.commit()
            log_concurrent_info(
                f"[数据库] 保存功能描述占位记录: {feature_name}",
                "smart_chain_review"
            )
    except Exception as e:
        log_concurrent_warning(f"[数据库] 保存功能描述占位记录失败: {e}", "smart_chain_review")


def get_chain_review_progress(task_id: int) -> Dict[str, Any]:
    """
    获取链路审查进度（用于前端实时显示）
    
    Args:
        task_id: 任务ID
        
    Returns:
        进度信息字典
    """
    from .memory.memory_manager import MemoryManager
    
    try:
        # 尝试加载记忆文件
        # 需要从链路审查数据库获取项目路径
        from ...config_database_chain import get_chain_db_session
        from ...db.models_chain import ChainAnalysisTask, ChainAnalysisFile
        
        with get_chain_db_session() as db:
            task = db.query(ChainAnalysisTask).filter(ChainAnalysisTask.id == task_id).first()
            if not task:
                return {"status": "not_found", "message": "Task not found"}
            
            # 通过code_file_id查找文件记录
            if not task.code_file_id:
                return {"status": "error", "message": "Task has no associated file"}
            
            file_record = db.query(ChainAnalysisFile).filter(ChainAnalysisFile.id == task.code_file_id).first()
            if not file_record:
                return {"status": "error", "message": f"File {task.code_file_id} not found"}
            
            project_root = file_record.extract_path
        
        memory_manager = MemoryManager(task_id, project_root)
        memory = memory_manager.load_latest()
        
        if not memory:
            return {
                "status": "not_started",
                "message": "链路审查尚未开始或未启用",
                "progress": 0
            }
        
        discovery_status = memory.get("discovery", {}).get("status", "in_progress")
        current_round = memory.get("discovery", {}).get("current_round", 0)
        total_rounds = memory.get("discovery", {}).get("total_rounds", 3)
        
        # 获取审查状态（从memory.review字段）
        review_info = memory.get("review", {})
        review_status = review_info.get("status", "not_started")
        total_features = review_info.get("total_features", len(memory.get("features", [])))
        reviewed_features = review_info.get("reviewed_features", 0)
        
        # 判断整体状态（基于两个阶段的状态）
        if discovery_status == "completed" and review_status == "completed":
            overall_status = "completed"  # 全部完成
        elif discovery_status == "completed" and review_status == "in_progress":
            overall_status = "reviewing"  # 功能发现完成，正在审查
        elif discovery_status == "completed" and review_status == "not_started":
            overall_status = "reviewing"  # 功能发现完成，准备开始审查
        else:
            overall_status = "discovering"  # 正在发现功能
        
        # 重新设计进度计算：
        # 功能发现阶段（前50%）：分为3个round，每个占 50%/3 ≈ 16.67%
        # 功能审查阶段（后50%）：根据功能点数量动态计算
        
        # 1. 功能发现进度（0-50%）
        if discovery_status == "completed":
            discovery_progress = 50.0  # 完成时固定为50%
        else:
            # 每个round完成后增加 16.67%
            discovery_progress = (current_round / 3.0) * 50.0
        
        # 2. 功能审查进度（50-100%）
        if review_status == "completed":
            review_progress = 100.0
        elif review_status == "in_progress" and total_features > 0:
            # 从50%开始，根据已审查功能占比增加到100%
            review_progress = 50.0 + (reviewed_features / total_features) * 50.0
        else:
            review_progress = discovery_progress  # 审查未开始时，使用发现进度
        
        # 总进度
        overall_progress = review_progress
        
        # 为features附加问题统计
        enhanced_memory = _enhance_memory_with_issues(memory, task_id)
        
        # 构建结构化的Round信息（用于前端横向显示）
        rounds_info = _build_rounds_info(memory, discovery_status, current_round)
        
        # 获取当前正在审查的功能点名称（用于审查阶段显示）
        # 注意：需要使用扁平化后的功能列表，因为审查时是对扁平化列表进行的
        current_reviewing_feature = None
        if overall_status == "reviewing" and reviewed_features < total_features:
            features = memory.get("features", [])
            
            # 扁平化功能列表（与审查时保持一致：有子功能的父节点跳过）
            def flatten_features(features_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
                """递归扁平化功能列表，有子章节时只审查子章节，跳过父节点"""
                flattened = []
                for feature in features_list:
                    sub_features = feature.get('sub_features', []) or []
                    if sub_features:
                        flattened.extend(flatten_features(sub_features))
                    else:
                        flattened.append(feature)
                return flattened
            
            all_features = flatten_features(features)
            
            # 从扁平化列表中获取当前正在审查的功能
            if reviewed_features < len(all_features):
                current_reviewing_feature = all_features[reviewed_features].get('name', f'功能{reviewed_features + 1}')
        
        # 构建基本返回数据
        result: Dict[str, Any] = {
            "status": overall_status,
            "discovery_status": discovery_status,
            "current_round": current_round,
            "total_rounds": total_rounds,
            "discovery_progress": min(discovery_progress, 50.0),  # 最大50%
            "review_progress": min(review_progress, 100.0),        # 最大100%
            "overall_progress": min(overall_progress, 100.0),
            "features_count": total_features,
            "reviewed_features": reviewed_features,
            "current_activity": _get_current_activity(memory, overall_status, reviewed_features, total_features),
            "rounds_history": memory.get("metadata", {}).get("rounds_history", []),
            "memory": enhanced_memory,  # 增强后的记忆数据（包含问题统计）
            
            # 新增：结构化的显示信息
            "rounds_info": rounds_info,  # Round 1-3 的详细状态（用于前半段横向显示）
            "current_reviewing_feature": current_reviewing_feature,  # 当前审查的功能点名称（用于后半段显示）
            "current_feature": current_reviewing_feature,  # 别名，供前端使用
        }
        
        # 如果审查已完成，添加操作按钮信息
        if overall_status == "completed":
            result["show_action_buttons"] = True
            result["actions"] = [
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
        
        return result
    
    except Exception as e:
        log_concurrent_warning(f"获取链路审查进度失败: {e}", "smart_chain_review")
        return {
            "status": "error",
            "message": str(e),
            "progress": 0
        }


def _enhance_memory_with_issues(memory: Dict[str, Any], task_id: int) -> Dict[str, Any]:
    """
    为memory中的features附加问题统计
    
    从数据库查询每个功能的问题数量，并添加到feature对象中
    """
    import copy
    enhanced_memory = copy.deepcopy(memory)
    
    try:
        # 从链路审查数据库查询所有链路问题
        with get_chain_db_session() as db:
            from ...db.models_chain import ChainReviewProblem
            
            # 获取该任务的所有问题
            problems = db.query(ChainReviewProblem).filter(
                ChainReviewProblem.task_id == task_id
            ).all()
            
            # 统计每个链路名称的问题数量
            problem_counts = {}
            for problem in problems:
                chain_name = problem.chain_name
                if chain_name not in problem_counts:
                    problem_counts[chain_name] = 0
                problem_counts[chain_name] += 1
        
        # 为每个feature添加问题统计（递归处理sub_features）
        def add_issues_count(feature: Dict[str, Any]) -> None:
            feature_name = str(feature.get('name', ''))
            sub_features = cast(List[Dict[str, Any]], feature.get('sub_features') or [])
            
            if sub_features:
                # 有子功能的父节点：问题数显示为0（父节点不参与审查）
                feature['issues_count'] = 0
                for sub_feature in sub_features:
                    add_issues_count(sub_feature)
            else:
                # 叶子节点：从数据库取实际问题数
                feature['issues_count'] = problem_counts.get(feature_name, 0)
        
        # 处理所有顶层features
        features = cast(List[Dict[str, Any]], enhanced_memory.get('features', []))
        for feature in features:
            add_issues_count(feature)
        
        log_concurrent_info(
            f"[进度统计] 为 {len(features)} 个功能附加了问题统计",
            "smart_chain_review"
        )
        
    except Exception as e:
        log_concurrent_warning(f"[进度统计] 附加问题统计失败: {e}", "smart_chain_review")
        # 失败时返回原始memory
        return memory
    
    return enhanced_memory


def _build_rounds_info(memory: Dict[str, Any], discovery_status: str, current_round: int) -> List[Dict[str, Any]]:
    """
    构建结构化的Round信息（用于前端横向显示）
    
    返回示例：
    [
        {
            "round": 1,
            "title": "目录结构分析",
            "description": "基于目录结构的粗粒度划分",
            "status": "completed",  # completed | in_progress | pending
            "timestamp": "2025/10/26 21:30:23"
        },
        ...
    ]
    """
    # Round 定义（固定2个round）
    rounds_definition = [
        {
            "round": 1,
            "title": "需求文档解析",
            "description": "解析用户上传的需求文档，构建功能层级树"
        },
        {
            "round": 2,
            "title": "代码路径探索",
            "description": "AI智能体根据call_graph为每个功能定位代码路径"
        }
    ]
    
    # 从 rounds_history 中获取时间戳
    rounds_history = cast(List[Dict[str, Any]], memory.get("metadata", {}).get("rounds_history", []))
    round_timestamps: Dict[int, str] = {}
    for history in rounds_history:
        round_num = history.get("round")
        timestamp = history.get("timestamp", "")
        if isinstance(round_num, int) and timestamp:
            # 格式化时间戳为 YYYY/MM/DD HH:MM:SS
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(str(timestamp))
                round_timestamps[round_num] = dt.strftime("%Y/%m/%d %H:%M:%S")
            except Exception:
                round_timestamps[round_num] = str(timestamp)
    
    # 构建结果
    rounds_info: List[Dict[str, Any]] = []
    for round_def in rounds_definition:
        round_num = cast(int, round_def["round"])
        title = str(round_def["title"])
        description = str(round_def["description"])
        status: Literal["completed", "in_progress", "pending"]
        
        # 确定状态
        if discovery_status == "completed":
            # 功能发现已完成，所有round都是completed
            status = "completed"
        elif current_round > round_num:
            # 当前轮次已超过该round
            status = "completed"
        elif current_round == round_num:
            # 正在进行该round
            status = "in_progress"
        else:
            # 尚未开始该round
            status = "pending"
        
        rounds_info.append({
            "round": round_num,
            "title": title,
            "description": description,
            "status": status,
            "timestamp": round_timestamps.get(round_num, "")
        })
    
    return rounds_info


def _get_current_activity(memory: Dict[str, Any], overall_status: str, reviewed_features: int, total_features: int) -> str:
    """根据记忆状态推断当前活动"""
    discovery = cast(Dict[str, Any], memory.get("discovery", {}))
    current_round = int(discovery.get("current_round", 0) or 0)
    discovery_status = str(discovery.get("status", "in_progress"))
    
    if overall_status == "completed":
        return f"✅ 审查完成！共发现 {total_features} 个功能模块"
    
    if overall_status == "reviewing":
        if reviewed_features < total_features:
            return f"🔍 正在审查功能模块 ({reviewed_features}/{total_features})"
        else:
            return f"✅ 功能审查完成，正在汇总结果..."
    
    # discovering 状态
    if discovery_status == "completed":
        return "✅ 功能发现完成，准备开始审查..."
    elif current_round == 1:
        return "📊 Round 1: 正在分析目录结构..."
    elif current_round == 2:
        return "🔍 Round 2: 正在分析函数签名..."
    elif current_round == 3:
        return "✔️ Round 3: 正在验证main函数..."
    else:
        return f"🔄 Round {current_round}: 正在进行深度分析..."

