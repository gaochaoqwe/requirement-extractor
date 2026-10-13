"""
并发版本的AI文档审查函数

支持多线程并发处理文档分块，提供高效的审查能力
"""
import asyncio
import traceback
from typing import List, Dict, Any
from pathlib import Path

# 导入配置和并发处理模块
from ..config import (
    AI_CONCURRENT_REQUESTS, DEFAULT_CHUNK_SIZE, DOC_TYPE_TASKBOOK, DOC_TYPE_REQUIREMENTSPEC
)
from ..utils.concurrent_logger import (
    init_concurrent_docreview_session,
    finalize_concurrent_docreview_session,
    log_docreview_concurrent_info,
    log_docreview_concurrent_debug,
    log_docreview_concurrent_error
)
from ..utils.concurrent_processor import (
    process_chunks_concurrently,
    process_taskbook_chunk,
    process_requirementspec_chunk,
    update_progress_callback
)

# 导入原有的模块
from ..utils.document_splitter import split_document, merge_issues

# 获取规则、模板和提示词（需要从原文件导入）
def _load_review_constants():
    """加载审查所需的常量"""
    try:
        # 这些常量需要从原有的router.py文件中导入
        from .router import RULES_TASKBOOK, TEMPLATE_TASKBOOK, PROMPT_TASKBOOK
        from .router import RULES_REQUIREMENTSPEC, TEMPLATE_REQUIREMENTSPEC, PROMPT_REQUIREMENTSPEC
        
        return {
            'taskbook': {
                'rules': RULES_TASKBOOK,
                'template': TEMPLATE_TASKBOOK,
                'prompt': PROMPT_TASKBOOK
            },
            'requirementspec': {
                'rules': RULES_REQUIREMENTSPEC,
                'template': TEMPLATE_REQUIREMENTSPEC,
                'prompt': PROMPT_REQUIREMENTSPEC
            }
        }
    except ImportError as e:
        log_docreview_concurrent_error(f"无法加载审查常量: {e}", "constants_loader", e)
        return None

async def ai_review_taskbook_concurrent(taskbook_content: str, session_id: int) -> List[Dict[str, Any]]:
    """
    对研制任务书进行并发AI审查
    
    Args:
        taskbook_content: 任务书内容
        session_id: 会话ID
        
    Returns:
        list: 问题列表
    """
    log_docreview_concurrent_info(f"开始并发审查研制任务书，会话ID: {session_id}", "ai_review_taskbook_concurrent")
    
    try:
        # 初始化并发审查会话
        init_concurrent_docreview_session(session_id)
        
        # 更新进度
        update_progress_callback(session_id, "taskbook_chunking", 25, "正在分割任务书文档...")
        
        # 1. 按标题分块
        chunks = split_document(taskbook_content, chunk_size=DEFAULT_CHUNK_SIZE)
        total_chunks = len(chunks)
        log_docreview_concurrent_info(f"任务书总分块数: {total_chunks}", "ai_review_taskbook_concurrent")
        
        if not chunks:
            log_docreview_concurrent_error("任务书分块结果为空", "ai_review_taskbook_concurrent")
            return []
        
        # 2. 加载审查常量
        constants = _load_review_constants()
        if not constants or 'taskbook' not in constants:
            log_docreview_concurrent_error("无法加载任务书审查常量", "ai_review_taskbook_concurrent")
            return []
        
        taskbook_constants = constants['taskbook']
        
        # 更新进度
        update_progress_callback(session_id, "taskbook_processing", 30, f"正在并发处理 {total_chunks} 个分块...")
        
        # 3. 并发处理所有分块
        all_issues = process_chunks_concurrently(
            chunks=chunks,
            session_id=session_id,
            doc_type=DOC_TYPE_TASKBOOK,
            chunk_processor_func=process_taskbook_chunk,
            max_workers=AI_CONCURRENT_REQUESTS,
            rules=taskbook_constants['rules'],
            template=taskbook_constants['template'],
            prompt=taskbook_constants['prompt']
        )
        
        # 更新进度
        update_progress_callback(session_id, "taskbook_merging", 35, "正在合并和去重问题...")
        
        # 4. 合并和去重问题
        final_issues = merge_issues(all_issues)
        
        log_docreview_concurrent_info(
            f"任务书并发审查完成，处理了 {total_chunks} 个分块，发现 {len(final_issues)} 个问题", 
            "ai_review_taskbook_concurrent"
        )
        
        return final_issues
        
    except Exception as e:
        log_docreview_concurrent_error(f"任务书并发审查异常: {e}", "ai_review_taskbook_concurrent", e)
        log_docreview_concurrent_debug(traceback.format_exc(), "ai_review_taskbook_concurrent")
        return []

async def ai_review_requirementspec_concurrent(
    requirementspec_content: str, 
    taskbook_content: str,
    session_id: int
) -> List[Dict[str, Any]]:
    """
    对需求规格说明进行并发AI审查
    
    Args:
        requirementspec_content: 需求规格说明内容
        taskbook_content: 任务书内容
        session_id: 会话ID
        
    Returns:
        list: 问题列表
    """
    log_docreview_concurrent_info(f"开始并发审查需求规格说明，会话ID: {session_id}", "ai_review_requirementspec_concurrent")
    
    try:
        # 更新进度
        update_progress_callback(session_id, "requirementspec_chunking", 55, "正在分割需求规格说明文档...")
        
        # 1. 按标题分块
        chunks = split_document(requirementspec_content, chunk_size=DEFAULT_CHUNK_SIZE)
        total_chunks = len(chunks)
        log_docreview_concurrent_info(f"需求规格说明总分块数: {total_chunks}", "ai_review_requirementspec_concurrent")
        
        if not chunks:
            log_docreview_concurrent_error("需求规格说明分块结果为空", "ai_review_requirementspec_concurrent")
            return []
        
        # 2. 加载审查常量
        constants = _load_review_constants()
        if not constants or 'requirementspec' not in constants:
            log_docreview_concurrent_error("无法加载需求规格说明审查常量", "ai_review_requirementspec_concurrent")
            return []
        
        requirementspec_constants = constants['requirementspec']
        
        # 更新进度
        update_progress_callback(session_id, "requirementspec_processing", 60, f"正在并发处理 {total_chunks} 个分块...")
        
        # 3. 并发处理所有分块
        all_issues = process_chunks_concurrently(
            chunks=chunks,
            session_id=session_id,
            doc_type=DOC_TYPE_REQUIREMENTSPEC,
            chunk_processor_func=process_requirementspec_chunk,
            max_workers=AI_CONCURRENT_REQUESTS,
            rules=requirementspec_constants['rules'],
            template=requirementspec_constants['template'],
            prompt=requirementspec_constants['prompt'],
            taskbook_content=taskbook_content  # 传递任务书内容供参考
        )
        
        # 更新进度
        update_progress_callback(session_id, "requirementspec_merging", 75, "正在合并和去重问题...")
        
        # 4. 合并和去重问题
        final_issues = merge_issues(all_issues)
        
        log_docreview_concurrent_info(
            f"需求规格说明并发审查完成，处理了 {total_chunks} 个分块，发现 {len(final_issues)} 个问题", 
            "ai_review_requirementspec_concurrent"
        )
        
        return final_issues
        
    except Exception as e:
        log_docreview_concurrent_error(f"需求规格说明并发审查异常: {e}", "ai_review_requirementspec_concurrent", e)
        log_docreview_concurrent_debug(traceback.format_exc(), "ai_review_requirementspec_concurrent")
        return []

async def ai_review_documents_concurrent(
    taskbook_content: str = "",
    requirementspec_content: str = "",
    session_id: int = 0
) -> List[Dict[str, Any]]:
    """
    并发审查多个文档的统一接口
    
    Args:
        taskbook_content: 任务书内容
        requirementspec_content: 需求规格说明内容
        session_id: 会话ID
        
    Returns:
        list: 所有问题的合并列表
    """
    log_docreview_concurrent_info(f"开始并发文档审查，会话ID: {session_id}", "ai_review_documents_concurrent")
    
    all_problems = []
    total_chunks = 0
    
    try:
        # 初始化并发审查会话
        init_concurrent_docreview_session(session_id)
        
        # 审查任务书
        if taskbook_content:
            log_docreview_concurrent_info("开始并发审查任务书", "ai_review_documents_concurrent")
            taskbook_problems = await ai_review_taskbook_concurrent(taskbook_content, session_id)
            all_problems.extend(taskbook_problems)
            
            # 计算分块数
            taskbook_chunks = split_document(taskbook_content, chunk_size=DEFAULT_CHUNK_SIZE)
            total_chunks += len(taskbook_chunks)
        
        # 审查需求规格说明
        if requirementspec_content:
            log_docreview_concurrent_info("开始并发审查需求规格说明", "ai_review_documents_concurrent")
            requirementspec_problems = await ai_review_requirementspec_concurrent(
                requirementspec_content, taskbook_content, session_id
            )
            all_problems.extend(requirementspec_problems)
            
            # 计算分块数
            requirementspec_chunks = split_document(requirementspec_content, chunk_size=DEFAULT_CHUNK_SIZE)
            total_chunks += len(requirementspec_chunks)
        
        # 完成审查会话
        finalize_concurrent_docreview_session(session_id, total_chunks, len(all_problems))
        
        log_docreview_concurrent_info(
            f"并发文档审查完成，总分块数: {total_chunks}，总问题数: {len(all_problems)}", 
            "ai_review_documents_concurrent"
        )
        
        return all_problems
        
    except Exception as e:
        log_docreview_concurrent_error(f"并发文档审查异常: {e}", "ai_review_documents_concurrent", e)
        log_docreview_concurrent_debug(traceback.format_exc(), "ai_review_documents_concurrent")
        
        # 确保会话被正确完成
        try:
            finalize_concurrent_docreview_session(session_id, total_chunks, len(all_problems))
        except:
            pass
        
        return all_problems  # 返回已处理的部分结果 