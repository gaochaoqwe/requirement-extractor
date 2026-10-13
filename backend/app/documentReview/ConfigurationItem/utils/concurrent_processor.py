"""
文档审查并发处理核心模块

提供分块级别的并发处理，包括线程安全的任务分发和结果收集
"""
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Callable, Optional
from datetime import datetime

from .concurrent_logger import (
    get_concurrent_docreview_config,
    set_current_docreview_thread_session,
    log_docreview_concurrent_info,
    log_docreview_concurrent_debug,
    log_docreview_concurrent_error,
    log_docreview_concurrent_chunk_start,
    log_docreview_concurrent_chunk_complete
)

def process_chunks_concurrently(
    chunks: List[str],
    session_id: int,
    doc_type: str,
    chunk_processor_func: Callable,
    max_workers: Optional[int] = None,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    并发处理文档分块的通用框架
    
    Args:
        chunks: 文档分块列表
        session_id: 会话ID
        doc_type: 文档类型（taskBook/requirementSpec）
        chunk_processor_func: 处理单个分块的函数
        max_workers: 最大并发工作线程数
        **kwargs: 传递给chunk_processor_func的额外参数
        
    Returns:
        list: 所有分块的处理结果列表
    """
    if not chunks:
        log_docreview_concurrent_info("没有分块需要处理", "concurrent_processor")
        return []
    
    # 获取并发配置
    if max_workers is None:
        max_workers = get_concurrent_docreview_config()
    
    total_chunks = len(chunks)
    processed_counter = {'count': 0}
    progress_lock = threading.Lock()
    
    log_docreview_concurrent_info(
        f"开始并发处理: 文档类型={doc_type}, 总分块数={total_chunks}, 并发数={max_workers}", 
        "concurrent_processor"
    )
    
    all_results = []
    
    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有分块任务
            future_to_chunk = {}
            for chunk_index, chunk_content in enumerate(chunks):
                future = executor.submit(
                    _process_single_chunk_with_safety,
                    chunk_index, chunk_content, session_id, doc_type,
                    chunk_processor_func, total_chunks, processed_counter, progress_lock,
                    **kwargs
                )
                future_to_chunk[future] = (chunk_index, chunk_content)
            
            # 收集结果
            for future in as_completed(future_to_chunk):
                chunk_index, chunk_content = future_to_chunk[future]
                try:
                    result = future.result()
                    if result:
                        all_results.extend(result)  # 假设返回的是问题列表
                except Exception as e:
                    log_docreview_concurrent_error(
                        f"处理分块 {chunk_index + 1} 时发生异常: {e}", 
                        "concurrent_processor", e
                    )
    
    except Exception as e:
        log_docreview_concurrent_error(f"并发处理框架异常: {e}", "concurrent_processor", e)
    
    log_docreview_concurrent_info(
        f"并发处理完成: 文档类型={doc_type}, 总分块数={total_chunks}, 总问题数={len(all_results)}", 
        "concurrent_processor"
    )
    return all_results

def _process_single_chunk_with_safety(
    chunk_index: int,
    chunk_content: str,
    session_id: int,
    doc_type: str,
    chunk_processor_func: Callable,
    total_chunks: int,
    processed_counter: Dict[str, int],
    progress_lock: threading.Lock,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    线程安全地处理单个分块
    
    Args:
        chunk_index: 分块索引
        chunk_content: 分块内容
        session_id: 会话ID
        doc_type: 文档类型
        chunk_processor_func: 处理函数
        total_chunks: 总分块数
        processed_counter: 处理计数器
        progress_lock: 进度锁
        **kwargs: 传递给处理函数的额外参数
        
    Returns:
        list: 处理结果（问题列表）
    """
    thread_name = f"chunk_worker_{threading.current_thread().ident}"
    start_time = time.time()
    
    try:
        # 设置当前线程的日志上下文（避免重复设置）
        set_current_docreview_thread_session(session_id, thread_name, doc_type)
        
        # 记录分块处理开始
        log_docreview_concurrent_chunk_start(chunk_index, len(chunk_content), doc_type)
        
        # 线程安全地更新进度
        with progress_lock:
            processed_counter['count'] += 1
            progress = (processed_counter['count'] / total_chunks) * 100
            log_docreview_concurrent_debug(
                f"处理进度: {processed_counter['count']}/{total_chunks} ({progress:.1f}%)",
                "progress_tracker"
            )
        
        # 调用具体的处理函数
        result = chunk_processor_func(
            chunk_index, chunk_content, session_id, doc_type, **kwargs
        )
        
        # 记录分块处理完成
        processing_time = time.time() - start_time
        issues_found = len(result) if result else 0
        log_docreview_concurrent_chunk_complete(chunk_index, issues_found, processing_time)
        
        return result if result else []
        
    except Exception as e:
        processing_time = time.time() - start_time
        log_docreview_concurrent_error(
            f"分块 {chunk_index + 1} 处理失败，耗时: {processing_time:.2f}秒，错误: {e}",
            "chunk_processor", e
        )
        log_docreview_concurrent_debug(traceback.format_exc(), "chunk_processor")
        return []

def process_taskbook_chunk(
    chunk_index: int,
    chunk_content: str,
    session_id: int,
    doc_type: str,
    rules: str,
    template: str,
    prompt: str
) -> List[Dict[str, Any]]:
    """
    处理任务书分块
    
    Args:
        chunk_index: 分块索引
        chunk_content: 分块内容
        session_id: 会话ID
        doc_type: 文档类型
        rules: 审查规则
        template: 模板
        prompt: 提示词
        
    Returns:
        list: 问题列表
    """
    import json
    import asyncio
    from ..reviewer.prompt.compose_taskbook_prompt import compose_taskbook_prompt
    from ..reviewer.openai.openai_api import ModelCaller
    from ..reviewer.analysis.analysis_taskbook import parse_taskbook_model_output
    
    try:
        log_docreview_concurrent_debug(
            f"开始处理任务书分块 {chunk_index + 1}，内容长度: {len(chunk_content)} 字符",
            "taskbook_processor"
        )
        
        # 显示分块内容预览
        if len(chunk_content) > 300:
            preview = chunk_content[:300] + "..."
            log_docreview_concurrent_debug(f"分块内容预览: {preview}", "taskbook_processor")
        else:
            log_docreview_concurrent_debug(f"分块内容: {chunk_content}", "taskbook_processor")
        
        # 构建提示词
        chunk_prompt = compose_taskbook_prompt(
            chunk_content,
            rules,
            template,
            prompt,
            chunk_index=chunk_index,
            total_chunks=1  # 在并发模式下，每个分块独立处理
        )
        
        log_docreview_concurrent_debug(f"提示词构建完成，长度: {len(chunk_prompt)} 字符", "taskbook_processor")
        
        # 调用AI进行审查
        model_output = ModelCaller.call_model(prompt=chunk_prompt)
        msg = model_output.choices[0].message
        
        log_docreview_concurrent_debug("AI模型调用成功", "taskbook_processor")
        
        # 解析AI响应
        issues = []
        if getattr(msg, 'json_content', None):
            data = msg.json_content
            issues = data.get("problems", [])
        else:
            raw_content = msg.content or ''
            try:
                # 直接尝试解析 JSON 字符串
                data = json.loads(raw_content)
                issues = data.get("problems", [])
            except Exception:
                # 回退到专用解析器
                try:
                    issues = parse_taskbook_model_output(raw_content)
                except Exception as parse_e:
                    log_docreview_concurrent_error(
                        f"解析AI响应失败: {parse_e}",
                        "taskbook_processor", parse_e
                    )
                    return []
        
        log_docreview_concurrent_info(
            f"任务书分块 {chunk_index + 1} 处理完成，发现问题: {len(issues)} 个",
            "taskbook_processor"
        )
        
        return issues
        
    except Exception as e:
        log_docreview_concurrent_error(
            f"任务书分块 {chunk_index + 1} 处理异常: {e}",
            "taskbook_processor", e
        )
        return []

def process_requirementspec_chunk(
    chunk_index: int,
    chunk_content: str,
    session_id: int,
    doc_type: str,
    rules: str,
    template: str,
    prompt: str,
    taskbook_content: str = ""
) -> List[Dict[str, Any]]:
    """
    处理需求规格说明分块
    
    Args:
        chunk_index: 分块索引
        chunk_content: 分块内容
        session_id: 会话ID
        doc_type: 文档类型
        rules: 审查规则
        template: 模板
        prompt: 提示词
        taskbook_content: 任务书内容（可选）
        
    Returns:
        list: 问题列表
    """
    import json
    import asyncio
    from ..reviewer.prompt.compose_requirementspec_prompt import compose_requirementspec_prompt
    from ..reviewer.openai.openai_api import ModelCaller
    from ..reviewer.analysis.analysis_requirementspec import parse_violation_rules_model_output
    
    try:
        log_docreview_concurrent_debug(
            f"开始处理需求规格说明分块 {chunk_index + 1}，内容长度: {len(chunk_content)} 字符",
            "requirementspec_processor"
        )
        
        # 显示分块内容预览
        if len(chunk_content) > 300:
            preview = chunk_content[:300] + "..."
            log_docreview_concurrent_debug(f"分块内容预览: {preview}", "requirementspec_processor")
        else:
            log_docreview_concurrent_debug(f"分块内容: {chunk_content}", "requirementspec_processor")
        
        # 构建提示词
        chunk_prompt = compose_requirementspec_prompt(
            chunk_content,
            taskbook_content,
            rules,
            template,
            prompt,
            chunk_index=chunk_index,
            total_chunks=1  # 在并发模式下，每个分块独立处理
        )
        
        log_docreview_concurrent_debug(f"提示词构建完成，长度: {len(chunk_prompt)} 字符", "requirementspec_processor")
        
        # 调用AI进行审查
        model_output = ModelCaller.call_model(prompt=chunk_prompt)
        msg = model_output.choices[0].message
        
        log_docreview_concurrent_debug("AI模型调用成功", "requirementspec_processor")
        
        # 解析AI响应
        issues = []
        if getattr(msg, 'json_content', None):
            data = msg.json_content
            issues = data.get("problems", [])
        else:
            raw_content = msg.content or ''
            try:
                # 直接尝试解析 JSON 字符串
                data = json.loads(raw_content)
                issues = data.get("problems", [])
            except Exception:
                # 回退到专用解析器
                try:
                    issues = parse_violation_rules_model_output(raw_content)
                except Exception as parse_e:
                    log_docreview_concurrent_error(
                        f"解析AI响应失败: {parse_e}",
                        "requirementspec_processor", parse_e
                    )
                    return []
        
        log_docreview_concurrent_info(
            f"需求规格说明分块 {chunk_index + 1} 处理完成，发现问题: {len(issues)} 个",
            "requirementspec_processor"
        )
        
        return issues
        
    except Exception as e:
        log_docreview_concurrent_error(
            f"需求规格说明分块 {chunk_index + 1} 处理异常: {e}",
            "requirementspec_processor", e
        )
        return []

def update_progress_callback(session_id: int, stage: str, percent: int, desc: str):
    """
    更新进度的回调函数
    
    Args:
        session_id: 会话ID
        stage: 当前阶段
        percent: 完成百分比
        desc: 描述信息
    """
    # 这个函数需要与原有的进度更新系统集成
    # 导入原有的进度字典
    try:
        from ..reviewer.router import review_progress_dict
        review_progress_dict[session_id] = {
            "stage": stage,
            "percent": percent,
            "desc": desc
        }
        log_docreview_concurrent_debug(
            f"进度更新: {stage} - {percent}% - {desc}",
            "progress_updater"
        )
    except ImportError:
        log_docreview_concurrent_debug(
            f"无法更新进度: {stage} - {percent}% - {desc}",
            "progress_updater"
        ) 