"""
文档审查并发日志模块

提供线程安全的日志记录功能，支持会话级别的日志管理和多线程环境下的日志写入
"""
import os
import threading
import time
from datetime import datetime
from typing import Optional

# 线程本地存储，用于存储当前线程的会话信息
_thread_local = threading.local()

# 会话级别的锁，用于保护日志文件写入
_session_locks = {}
_locks_lock = threading.Lock()

def get_concurrent_docreview_config() -> int:
    """获取文档审查并发配置"""
    try:
        # 兼容不同的导入方式
        try:
            from ..config import AI_CONCURRENT_REQUESTS
            return AI_CONCURRENT_REQUESTS
        except (ImportError, ValueError):
            # 尝试绝对导入
            import sys
            from pathlib import Path
            parent_dir = Path(__file__).parent.parent
            if str(parent_dir) not in sys.path:
                sys.path.insert(0, str(parent_dir))
            from config import AI_CONCURRENT_REQUESTS
            return AI_CONCURRENT_REQUESTS
    except ImportError:
        return 3  # 默认值

def init_concurrent_docreview_session(session_id: int) -> str:
    """
    初始化并发文档审查会话的日志环境
    
    Args:
        session_id: 会话ID
        
    Returns:
        str: 会话日志文件夹路径
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_folder = f"docreview_session_{session_id}_{timestamp}"
    
    # 创建日志文件夹
    logs_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    session_log_dir = os.path.join(logs_dir, log_folder)
    os.makedirs(session_log_dir, exist_ok=True)
    
    # 创建会话级别的锁
    with _locks_lock:
        _session_locks[session_id] = threading.Lock()
    
    # 写入初始化日志
    summary_log_path = os.path.join(session_log_dir, "docreview_summary.log")
    with open(summary_log_path, 'w', encoding='utf-8') as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INIT] 文档审查会话开始 - 会话ID: {session_id}\n")
    
    return session_log_dir

def set_current_docreview_thread_session(session_id: int, thread_name: str, doc_type: str = ""):
    """
    设置当前线程的文档审查会话信息
    
    Args:
        session_id: 会话ID
        thread_name: 线程名称
        doc_type: 文档类型（taskBook/requirementSpec）
    """
    # 检查是否已经为这个会话设置过线程信息
    if hasattr(_thread_local, 'session_id') and _thread_local.session_id == session_id:
        return  # 避免重复设置
        
    _thread_local.session_id = session_id
    _thread_local.thread_name = thread_name
    _thread_local.doc_type = doc_type
    
    # 创建线程专用的日志文件
    logs_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    
    # 找到对应的会话日志文件夹
    session_log_dir = None
    for folder in os.listdir(logs_dir):
        if folder.startswith(f"docreview_session_{session_id}_"):
            session_log_dir = os.path.join(logs_dir, folder)
            break
    
    if session_log_dir:
        thread_log_path = os.path.join(session_log_dir, f"docreview_worker_{threading.current_thread().ident}.log")
        _thread_local.log_file_path = thread_log_path
        
        # 创建线程日志文件（如果不存在）
        if not os.path.exists(thread_log_path):
            with open(thread_log_path, 'w', encoding='utf-8') as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [THREAD] 线程 {thread_name} 开始处理会话 {session_id} ({doc_type})\n")

def log_docreview_concurrent_info(message: str, component: str):
    """记录信息级别的并发日志"""
    _write_concurrent_docreview_log("INFO", message, component)

def log_docreview_concurrent_debug(message: str, component: str):
    """记录调试级别的并发日志"""
    _write_concurrent_docreview_log("DEBUG", message, component)

def log_docreview_concurrent_warning(message: str, component: str):
    """记录警告级别的并发日志"""
    _write_concurrent_docreview_log("WARNING", message, component)

def log_docreview_concurrent_error(message: str, component: str, exception: Optional[Exception] = None):
    """记录错误级别的并发日志"""
    if exception:
        message = f"{message} - 异常: {str(exception)}"
    _write_concurrent_docreview_log("ERROR", message, component)

def log_docreview_concurrent_ai_result(message: str, component: str):
    """记录AI返回结果的日志"""
    _write_concurrent_docreview_log("AI_RESULT", message, component)

def log_docreview_concurrent_chunk_start(chunk_index: int, chunk_size: int, doc_type: str):
    """记录分块处理开始的日志"""
    message = f"开始处理分块 {chunk_index + 1}，文档类型: {doc_type}，分块大小: {chunk_size} 字符"
    _write_concurrent_docreview_log("CHUNK_START", message, "chunk_processor")

def log_docreview_concurrent_chunk_complete(chunk_index: int, issues_found: int, processing_time: float):
    """记录分块处理完成的日志"""
    message = f"分块 {chunk_index + 1} 处理完成，发现问题: {issues_found} 个，耗时: {processing_time:.2f}秒"
    _write_concurrent_docreview_log("CHUNK_COMPLETE", message, "chunk_processor")

def _write_concurrent_docreview_log(level: str, message: str, component: str):
    """
    写入并发日志
    
    Args:
        level: 日志级别
        message: 日志消息
        component: 组件名称
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    thread_name = getattr(_thread_local, 'thread_name', 'main')
    doc_type = getattr(_thread_local, 'doc_type', '')
    doc_info = f"[{doc_type}]" if doc_type else ""
    
    log_entry = f"[{timestamp}] [{level}] [{component}] [{thread_name}]{doc_info} {message}\n"
    
    # 写入线程专用日志文件
    if hasattr(_thread_local, 'log_file_path') and _thread_local.log_file_path:
        try:
            with open(_thread_local.log_file_path, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception:
            pass  # 忽略日志写入错误
    
    # 写入汇总日志文件
    if hasattr(_thread_local, 'session_id'):
        session_id = _thread_local.session_id
        if session_id in _session_locks:
            with _session_locks[session_id]:
                try:
                    logs_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
                    
                    # 找到对应的会话日志文件夹
                    for folder in os.listdir(logs_dir):
                        if folder.startswith(f"docreview_session_{session_id}_"):
                            summary_log_path = os.path.join(logs_dir, folder, "docreview_summary.log")
                            with open(summary_log_path, 'a', encoding='utf-8') as f:
                                f.write(log_entry)
                            break
                except Exception:
                    pass  # 忽略日志写入错误

def finalize_concurrent_docreview_session(session_id: int, total_chunks: int, total_issues: int):
    """
    完成并发文档审查会话，清理资源并生成最终日志
    
    Args:
        session_id: 会话ID
        total_chunks: 总分块数
        total_issues: 总问题数
    """
    start_time = time.time()
    
    # 等待一小段时间确保所有线程完成日志写入
    time.sleep(0.1)
    
    # 统计线程数量
    logs_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    thread_count = 0
    
    for folder in os.listdir(logs_dir):
        if folder.startswith(f"docreview_session_{session_id}_"):
            session_log_dir = os.path.join(logs_dir, folder)
            worker_files = [f for f in os.listdir(session_log_dir) if f.startswith("docreview_worker_")]
            thread_count = len(worker_files)
            
            # 写入最终日志
            summary_log_path = os.path.join(session_log_dir, "docreview_summary.log")
            elapsed_time = time.time() - start_time
            with open(summary_log_path, 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [COMPLETE] 文档审查会话完成 - 总分块数: {total_chunks}, 总问题数: {total_issues}, 线程数: {thread_count}, 耗时: {elapsed_time:.2f}秒\n")
            
            # 创建日志查看脚本
            _create_docreview_log_viewer(session_log_dir, session_id)
            break
    
    # 清理会话锁
    with _locks_lock:
        if session_id in _session_locks:
            del _session_locks[session_id]

def clear_current_docreview_thread_session():
    """清除当前线程的文档审查会话信息"""
    for attr in ['session_id', 'thread_name', 'doc_type', 'log_file_path']:
        if hasattr(_thread_local, attr):
            delattr(_thread_local, attr)

def _create_docreview_log_viewer(session_log_dir: str, session_id: int):
    """
    创建文档审查日志查看脚本
    
    Args:
        session_log_dir: 会话日志目录
        session_id: 会话ID
    """
    script_content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档审查会话 {session_id} 日志查看器
自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
import os
import sys

def main():
    log_dir = r"{session_log_dir}"
    
    print(f"=== 文档审查会话 {session_id} 日志查看器 ===")
    print(f"日志目录: {{log_dir}}")
    print()
    
    # 显示汇总日志
    summary_log = os.path.join(log_dir, "docreview_summary.log")
    if os.path.exists(summary_log):
        print("=== 汇总日志 (docreview_summary.log) ===")
        with open(summary_log, 'r', encoding='utf-8') as f:
            print(f.read())
        print()
    
    # 显示所有工作线程日志
    worker_logs = [f for f in os.listdir(log_dir) if f.startswith("docreview_worker_")]
    if worker_logs:
        for worker_log in sorted(worker_logs):
            print(f"=== 工作线程日志 ({{worker_log}}) ===")
            worker_path = os.path.join(log_dir, worker_log)
            with open(worker_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # 显示前200行和后100行（如果内容很长）
                lines = content.split('\\n')
                if len(lines) <= 300:
                    print(content)
                else:
                    print('\\n'.join(lines[:200]))
                    print(f"\\n... (省略 {{len(lines) - 300}} 行) ...\\n")
                    print('\\n'.join(lines[-100:]))
            print()
    
    # 显示其他日志文件
    other_logs = [f for f in os.listdir(log_dir) 
                  if f.endswith('.log') and not f.startswith('docreview_') 
                  and not f.startswith('docreview_worker_')]
    if other_logs:
        for other_log in sorted(other_logs):
            print(f"=== 其他日志 ({{other_log}}) ===")
            other_path = os.path.join(log_dir, other_log)
            with open(other_path, 'r', encoding='utf-8') as f:
                print(f.read())
            print()

if __name__ == "__main__":
    main()
'''
    
    script_path = os.path.join(session_log_dir, f"view_docreview_logs_{session_id}.py")
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    # 在Unix系统上设置可执行权限
    try:
        os.chmod(script_path, 0o755)
    except:
        pass  # Windows系统忽略 