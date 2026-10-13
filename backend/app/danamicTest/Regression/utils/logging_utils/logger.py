
"""
统一的日志管理工具
为动态测试回归测试目录中的每个回归测试任务创建独立的日志文件
"""
import os
import threading
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# 全局变量存储当前任务的日志信息
_current_task_id: Optional[str] = None
_current_session_id: Optional[str] = None
_current_log_file: Optional[Path] = None
_thread_local = threading.local()

# 日志目录配置
CURRENT_DIR = Path(__file__).parent.parent.parent  # Regression目录
LOGS_DIR = CURRENT_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

def set_current_task(task_id: str, session_id: str):
    """
    设置当前任务的ID，用于创建对应的日志文件
    
    Args:
        task_id: 任务ID
        session_id: 会话ID
    """
    global _current_task_id, _current_session_id, _current_log_file
    _current_task_id = task_id
    _current_session_id = session_id
    
    # 同时设置到线程本地存储
    _thread_local.task_id = task_id
    _thread_local.session_id = session_id
    
    # 创建任务专用日志文件（使用时间戳确保唯一性）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"regression_test_task_{task_id}_{timestamp}.log"
    _current_log_file = LOGS_DIR / log_filename
    _thread_local.log_file = _current_log_file
    
    # 初始化日志文件
    with open(_current_log_file, "w", encoding="utf-8") as f:
        f.write(f"=== 动态测试-回归测试任务日志 ===\n")
        f.write(f"任务ID: {task_id}\n")
        f.write(f"会话ID: {session_id}\n")
        f.write(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"日志文件: {log_filename}\n")
        f.write(f"{'='*50}\n\n")

def get_current_task_info():
    """
    获取当前任务信息
    
    Returns:
        tuple: (task_id, session_id, log_file)
    """
    # 优先从线程本地存储获取
    if hasattr(_thread_local, 'task_id'):
        return _thread_local.task_id, _thread_local.session_id, _thread_local.log_file
    
    # 如果线程本地存储没有，从全局变量获取
    return _current_task_id, _current_session_id, _current_log_file

def finalize_task_log():
    """
    完成任务日志记录
    """
    task_id, session_id, log_file = get_current_task_info()
    
    if task_id is not None and session_id is not None and log_file is not None:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*50}\n")
            f.write(f"任务结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"=== 任务日志结束 ===\n")

def log_info(msg: str, module_name: str = ""):
    """
    统一的信息日志记录函数
    
    Args:
        msg: 日志消息
        module_name: 模块名称（可选）
    """
    try:
        # 获取当前任务信息
        task_id, session_id, log_file = get_current_task_info()
        
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        # 格式化日志消息
        if module_name:
            formatted_msg = f"[{timestamp}] [{module_name}] [INFO] {msg}"
        else:
            formatted_msg = f"[{timestamp}] [INFO] {msg}"
        
        # 如果有当前任务，写入任务专用日志文件
        if task_id is not None and session_id is not None and log_file is not None:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(formatted_msg + "\n")
        else:
            # 如果没有当前任务，写入通用日志文件
            general_log_file = LOGS_DIR / "general.log"
            with open(general_log_file, "a", encoding="utf-8") as f:
                f.write(formatted_msg + "\n")
        
        # 不再输出到控制台，只写入日志文件
        # print(f"[DynamicTest-Regression] {formatted_msg}")
        
    except Exception as e:
        # 如果日志记录失败，至少输出到控制台
        print(f"[LOG_ERROR] 日志记录失败: {e}, 原始消息: {msg}")

def log_warning(msg: str, module_name: str = ""):
    """
    统一的警告日志记录函数
    
    Args:
        msg: 日志消息
        module_name: 模块名称（可选）
    """
    try:
        # 获取当前任务信息
        task_id, session_id, log_file = get_current_task_info()
        
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        # 格式化日志消息
        if module_name:
            formatted_msg = f"[{timestamp}] [{module_name}] [WARNING] {msg}"
        else:
            formatted_msg = f"[{timestamp}] [WARNING] {msg}"
        
        # 如果有当前任务，写入任务专用日志文件
        if task_id is not None and session_id is not None and log_file is not None:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(formatted_msg + "\n")
        else:
            # 如果没有当前任务，写入通用日志文件
            general_log_file = LOGS_DIR / "general.log"
            with open(general_log_file, "a", encoding="utf-8") as f:
                f.write(formatted_msg + "\n")
        
        # 不再输出到控制台，只写入日志文件
        # print(f"[DynamicTest-Regression] {formatted_msg}")
        
    except Exception as e:
        print(f"[LOG_ERROR] 日志记录失败: {e}, 原始消息: {msg}")

def log_error(msg: str, module_name: str = "", exception: Exception = None):
    """
    统一的错误日志记录函数
    
    Args:
        msg: 日志消息
        module_name: 模块名称（可选）
        exception: 异常对象（可选）
    """
    try:
        # 获取当前任务信息
        task_id, session_id, log_file = get_current_task_info()
        
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        # 格式化日志消息
        if module_name:
            formatted_msg = f"[{timestamp}] [{module_name}] [ERROR] {msg}"
        else:
            formatted_msg = f"[{timestamp}] [ERROR] {msg}"
        
        # 如果有异常，添加异常信息
        if exception:
            import traceback
            formatted_msg += f"\n异常详情: {str(exception)}\n"
            formatted_msg += f"异常堆栈:\n{traceback.format_exc()}"
        
        # 如果有当前任务，写入任务专用日志文件
        if task_id is not None and session_id is not None and log_file is not None:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(formatted_msg + "\n")
        else:
            # 如果没有当前任务，写入通用日志文件
            general_log_file = LOGS_DIR / "general.log"
            with open(general_log_file, "a", encoding="utf-8") as f:
                f.write(formatted_msg + "\n")
        
        # 不再输出到控制台，只写入日志文件
        # print(f"[DynamicTest-Regression] {formatted_msg}")
        
    except Exception as e:
        print(f"[LOG_ERROR] 日志记录失败: {e}, 原始消息: {msg}")

def log_debug(msg: str, module_name: str = ""):
    """
    统一的调试日志记录函数
    
    Args:
        msg: 日志消息
        module_name: 模块名称（可选）
    """
    try:
        # 获取当前任务信息
        task_id, session_id, log_file = get_current_task_info()
        
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        # 格式化日志消息
        if module_name:
            formatted_msg = f"[{timestamp}] [{module_name}] [DEBUG] {msg}"
        else:
            formatted_msg = f"[{timestamp}] [DEBUG] {msg}"
        
        # 如果有当前任务，写入任务专用日志文件
        if task_id is not None and session_id is not None and log_file is not None:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(formatted_msg + "\n")
        else:
            # 如果没有当前任务，写入通用日志文件
            general_log_file = LOGS_DIR / "general.log"
            with open(general_log_file, "a", encoding="utf-8") as f:
                f.write(formatted_msg + "\n")
        
        # 调试信息不输出到控制台，避免过多输出
        # log_info(f"[DynamicTest-Regression] {formatted_msg}", Path(__file__).stem)
        
    except Exception as e:
        log_info(f"[LOG_ERROR] 日志记录失败: {e}, 原始消息: {msg}", Path(__file__).stem) 