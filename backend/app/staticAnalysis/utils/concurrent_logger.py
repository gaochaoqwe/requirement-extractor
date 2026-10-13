"""
静态分析并发日志模块

提供线程安全的日志记录功能，支持任务级别的日志管理和多线程环境下的日志写入
"""
import os
import threading
import time
from datetime import datetime
from typing import Optional

# 线程本地存储，用于存储当前线程的任务信息
_thread_local = threading.local()

# 任务级别的锁，用于保护日志文件写入
_task_locks = {}
_locks_lock = threading.Lock()

def get_concurrent_static_config() -> int:
    """获取静态分析并发配置"""
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
        return 5  # 默认值

def init_concurrent_static_task(task_id: int, file_id: int) -> str:
    """
    初始化并发静态分析任务的日志环境
    
    Args:
        task_id: 任务ID
        file_id: 文件ID
        
    Returns:
        str: 任务日志文件夹路径
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_folder = f"static_task_{task_id}_{timestamp}"
    
    # 创建日志文件夹
    logs_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    task_log_dir = os.path.join(logs_dir, log_folder)
    os.makedirs(task_log_dir, exist_ok=True)
    
    # 创建任务级别的锁
    with _locks_lock:
        _task_locks[task_id] = threading.Lock()
    
    # 写入初始化日志
    summary_log_path = os.path.join(task_log_dir, "static_summary.log")
    with open(summary_log_path, 'w', encoding='utf-8') as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INIT] 静态分析任务开始 - 任务ID: {task_id}, 文件ID: {file_id}\n")
    
    return task_log_dir

def set_current_static_thread_task(task_id: int, file_id: int, thread_name: str):
    """
    设置当前线程的静态分析任务信息
    
    Args:
        task_id: 任务ID
        file_id: 文件ID
        thread_name: 线程名称
    """
    # 检查是否已经为这个任务设置过线程信息
    if hasattr(_thread_local, 'task_id') and _thread_local.task_id == task_id:
        return  # 避免重复设置
        
    _thread_local.task_id = task_id
    _thread_local.file_id = file_id
    _thread_local.thread_name = thread_name
    
    # 创建线程专用的日志文件
    logs_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    
    # 找到对应的任务日志文件夹
    task_log_dir = None
    for folder in os.listdir(logs_dir):
        if folder.startswith(f"static_task_{task_id}_"):
            task_log_dir = os.path.join(logs_dir, folder)
            break
    
    if task_log_dir:
        thread_log_path = os.path.join(task_log_dir, f"static_worker_{threading.current_thread().ident}.log")
        _thread_local.log_file_path = thread_log_path
        
        # 创建线程日志文件（如果不存在）
        if not os.path.exists(thread_log_path):
            with open(thread_log_path, 'w', encoding='utf-8') as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [THREAD] 线程 {thread_name} 开始处理任务 {task_id}\n")

def log_static_concurrent_info(message: str, component: str):
    """记录信息级别的并发日志"""
    _write_concurrent_static_log("INFO", message, component)

def log_static_concurrent_debug(message: str, component: str):
    """记录调试级别的并发日志"""
    _write_concurrent_static_log("DEBUG", message, component)

def log_static_concurrent_warning(message: str, component: str):
    """记录警告级别的并发日志"""
    _write_concurrent_static_log("WARNING", message, component)

def log_static_concurrent_error(message: str, component: str, exception: Optional[Exception] = None):
    """记录错误级别的并发日志"""
    if exception:
        message = f"{message} - 异常: {str(exception)}"
    _write_concurrent_static_log("ERROR", message, component)

def log_static_concurrent_ai_result(message: str, component: str):
    """记录AI返回结果的日志"""
    _write_concurrent_static_log("AI_RESULT", message, component)

def _write_concurrent_static_log(level: str, message: str, component: str):
    """
    写入并发日志
    
    Args:
        level: 日志级别
        message: 日志消息
        component: 组件名称
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] [{level}] [{component}] {message}\n"
    
    # 写入线程专用日志文件
    if hasattr(_thread_local, 'log_file_path') and _thread_local.log_file_path:
        try:
            with open(_thread_local.log_file_path, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception:
            pass  # 忽略日志写入错误
    
    # 写入汇总日志文件
    if hasattr(_thread_local, 'task_id'):
        task_id = _thread_local.task_id
        if task_id in _task_locks:
            with _task_locks[task_id]:
                try:
                    logs_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
                    
                    # 找到对应的任务日志文件夹
                    for folder in os.listdir(logs_dir):
                        if folder.startswith(f"static_task_{task_id}_"):
                            summary_log_path = os.path.join(logs_dir, folder, "static_summary.log")
                            with open(summary_log_path, 'a', encoding='utf-8') as f:
                                f.write(log_entry)
                            break
                except Exception:
                    pass  # 忽略日志写入错误

def finalize_concurrent_static_task(task_id: int):
    """
    完成并发静态分析任务，清理资源并生成最终日志
    
    Args:
        task_id: 任务ID
    """
    start_time = time.time()
    
    # 等待一小段时间确保所有线程完成日志写入
    time.sleep(0.1)
    
    # 统计线程数量
    logs_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    thread_count = 0
    
    for folder in os.listdir(logs_dir):
        if folder.startswith(f"static_task_{task_id}_"):
            task_log_dir = os.path.join(logs_dir, folder)
            worker_files = [f for f in os.listdir(task_log_dir) if f.startswith("static_worker_")]
            thread_count = len(worker_files)
            
            # 写入最终日志
            summary_log_path = os.path.join(task_log_dir, "static_summary.log")
            elapsed_time = time.time() - start_time
            with open(summary_log_path, 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [COMPLETE] 静态分析任务完成 - 耗时: {elapsed_time:.2f}秒, 线程数: {thread_count}\n")
            
            # 创建日志查看脚本
            _create_static_log_viewer(task_log_dir, task_id)
            break
    
    # 清理任务锁
    with _locks_lock:
        if task_id in _task_locks:
            del _task_locks[task_id]

def clear_current_static_thread_task():
    """清除当前线程的静态分析任务信息"""
    if hasattr(_thread_local, 'task_id'):
        del _thread_local.task_id
    if hasattr(_thread_local, 'file_id'):
        del _thread_local.file_id
    if hasattr(_thread_local, 'thread_name'):
        del _thread_local.thread_name
    if hasattr(_thread_local, 'log_file_path'):
        del _thread_local.log_file_path

def _create_static_log_viewer(task_log_dir: str, task_id: int):
    """
    创建静态分析日志查看脚本
    
    Args:
        task_log_dir: 任务日志目录
        task_id: 任务ID
    """
    script_content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
静态分析任务 {task_id} 日志查看器
自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
import os
import sys

def main():
    log_dir = r"{task_log_dir}"
    
    print(f"=== 静态分析任务 {task_id} 日志查看器 ===")
    print(f"日志目录: {{log_dir}}")
    print()
    
    # 显示汇总日志
    summary_log = os.path.join(log_dir, "static_summary.log")
    if os.path.exists(summary_log):
        print("=== 汇总日志 (static_summary.log) ===")
        with open(summary_log, 'r', encoding='utf-8') as f:
            print(f.read())
        print()
    
    # 显示所有工作线程日志
    worker_logs = [f for f in os.listdir(log_dir) if f.startswith("static_worker_")]
    if worker_logs:
        for worker_log in sorted(worker_logs):
            print(f"=== 工作线程日志 ({{worker_log}}) ===")
            worker_path = os.path.join(log_dir, worker_log)
            with open(worker_path, 'r', encoding='utf-8') as f:
                print(f.read())
            print()
    
    # 显示其他日志文件
    other_logs = [f for f in os.listdir(log_dir) 
                  if f.endswith('.log') and not f.startswith('static_') 
                  and not f.startswith('static_worker_')]
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
    
    script_path = os.path.join(task_log_dir, f"view_static_logs_{task_id}.py")
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    # 在Unix系统上设置可执行权限
    try:
        os.chmod(script_path, 0o755)
    except:
        pass  # Windows系统忽略 