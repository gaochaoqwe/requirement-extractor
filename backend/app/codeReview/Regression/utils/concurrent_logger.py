"""
回归测试模块并发日志系统

每个回归测试任务创建独立文件夹，并发任务创建独立日志文件，
同时提供汇总日志和便捷的查看工具。
"""
import os
import threading
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import uuid

# 线程本地存储
_thread_local = threading.local()

# 日志目录配置
CURRENT_DIR = Path(__file__).parent.parent  # Regression目录
LOGS_DIR = CURRENT_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# 全局任务信息
_task_folders: Dict[int, Path] = {}  # task_id -> 文件夹路径
_task_summary_files: Dict[int, Path] = {}  # task_id -> 汇总日志文件
_task_locks: Dict[int, threading.Lock] = {}  # task_id -> 汇总日志锁


def init_concurrent_regression_task(task_id: int, file_id: int) -> Path:
    """
    初始化并发回归测试任务的日志系统
    
    Args:
        task_id: 任务ID
        file_id: 文件ID
        
    Returns:
        Path: 任务日志文件夹路径
    """
    # 创建任务专用文件夹
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    task_folder = LOGS_DIR / f"regression_task_{task_id}_{timestamp}"
    task_folder.mkdir(exist_ok=True)
    
    # 创建汇总日志文件
    summary_file = task_folder / "regression_summary.log"
    
    # 保存到全局字典
    _task_folders[task_id] = task_folder
    _task_summary_files[task_id] = summary_file
    _task_locks[task_id] = threading.Lock()
    
    # 初始化汇总日志文件
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write(f"=== 回归测试任务汇总日志 ===\n")
        f.write(f"任务ID: {task_id}\n")
        f.write(f"文件ID: {file_id}\n")
        f.write(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"日志文件夹: {task_folder.name}\n")
        f.write(f"并发设置: {get_concurrent_requests()}\n")
        f.write(f"{'='*60}\n\n")
    
    return task_folder


def set_current_regression_thread_task(task_id: int, file_id: int, thread_name: str = None):
    """
    为当前线程设置回归测试任务信息
    
    Args:
        task_id: 任务ID
        file_id: 文件ID  
        thread_name: 线程名称（可选）
    """
    if thread_name is None:
        thread_name = f"regression_thread_{threading.current_thread().ident}"
    
    # 设置线程本地存储
    _thread_local.task_id = task_id
    _thread_local.file_id = file_id
    _thread_local.thread_name = thread_name
    
    # 获取任务文件夹
    task_folder = _task_folders.get(task_id)
    if task_folder is None:
        # 如果任务文件夹不存在，先初始化
        task_folder = init_concurrent_regression_task(task_id, file_id)
    
    # 创建线程专用日志文件
    log_filename = f"{thread_name}.log"
    thread_log_file = task_folder / log_filename
    _thread_local.log_file = thread_log_file
    
    # 初始化线程日志文件
    with open(thread_log_file, "w", encoding="utf-8") as f:
        f.write(f"=== 回归测试线程日志 - {thread_name} ===\n")
        f.write(f"任务ID: {task_id}\n")
        f.write(f"文件ID: {file_id}\n")
        f.write(f"线程ID: {threading.current_thread().ident}\n")
        f.write(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'='*50}\n\n")


def get_current_regression_thread_info():
    """
    获取当前线程的回归测试任务信息
    
    Returns:
        tuple: (task_id, file_id, log_file, thread_name)
    """
    if not hasattr(_thread_local, 'task_id'):
        return None, None, None, None
    
    return (
        _thread_local.task_id,
        _thread_local.file_id, 
        _thread_local.log_file,
        _thread_local.thread_name
    )


def log_regression_concurrent_debug(msg: str, module_name: str = ""):
    """
    回归测试并发安全的调试日志记录函数
    
    Args:
        msg: 日志消息
        module_name: 模块名称
    """
    try:
        task_id, file_id, log_file, thread_name = get_current_regression_thread_info()
        
        if not task_id or not log_file:
            # 回退到普通日志
            _fallback_regression_log(msg, module_name)
            return
        
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        # 格式化消息
        if module_name:
            formatted_msg = f"[{timestamp}] [{thread_name}] [{module_name}] {msg}"
        else:
            formatted_msg = f"[{timestamp}] [{thread_name}] {msg}"
        
        # 写入线程专用日志文件
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(formatted_msg + "\n")
        
        # 同时写入汇总日志（需要加锁）
        _write_to_regression_summary_log(task_id, formatted_msg)
        
    except Exception as e:
        print(f"[REGRESSION_CONCURRENT_LOG_ERROR] 日志记录失败: {e}, 原始消息: {msg}")


def log_regression_concurrent_info(msg: str, module_name: str = ""):
    """回归测试并发安全的信息日志"""
    log_regression_concurrent_debug(f"[INFO] {msg}", module_name)


def log_regression_concurrent_warning(msg: str, module_name: str = ""):
    """回归测试并发安全的警告日志"""
    log_regression_concurrent_debug(f"[WARNING] {msg}", module_name)


def log_regression_concurrent_error(msg: str, module_name: str = "", exception: Exception = None):
    """回归测试并发安全的错误日志"""
    error_msg = f"[ERROR] {msg}"
    if exception:
        import traceback
        error_msg += f" - 异常详情: {str(exception)}"
        error_msg += f"\n堆栈跟踪:\n{traceback.format_exc()}"
    log_regression_concurrent_debug(error_msg, module_name)


def log_regression_concurrent_ai_result(ai_result: Dict[str, Any], task_name: str = "", module_name: str = "ai_analyzer"):
    """
    回归测试并发安全的AI结果日志记录
    
    Args:
        ai_result: AI返回的结果字典
        task_name: 任务名称
        module_name: 模块名称
    """
    try:
        # 构建格式化的AI结果日志
        log_lines = []
        log_lines.append("=" * 60)
        log_lines.append(f"回归测试AI分析结果 - 任务: {task_name}")
        log_lines.append("=" * 60)
        
        # 处理问题列表
        issues = ai_result.get("issues", [])
        if issues:
            log_lines.append(f"发现问题数量: {len(issues)}")
            for i, issue in enumerate(issues, 1):
                log_lines.append(f"问题 {i}:")
                log_lines.append(f"  等级: {issue.get('issue_level', 'N/A')}")
                log_lines.append(f"  名称: {issue.get('issue_name', 'N/A')}")
                log_lines.append(f"  位置: {issue.get('issue_location', 'N/A')}")
                log_lines.append(f"  描述: {issue.get('description_issue', 'N/A')}")
                log_lines.append(f"  影响: {issue.get('description_impact', 'N/A')}")
        else:
            log_lines.append("未发现问题")
        
        # 处理任务状态
        if "success" in ai_result:
            log_lines.append(f"任务状态: {'成功' if ai_result['success'] else '失败'}")
        
        log_lines.append("=" * 60)
        formatted_result = "\n".join(log_lines)
        log_regression_concurrent_debug(formatted_result, module_name)
        
    except Exception as e:
        log_regression_concurrent_error(f"格式化AI结果失败，记录原始结果: {ai_result}", module_name, e)


def finalize_concurrent_regression_task(task_id: int):
    """
    结束并发回归测试任务，生成汇总信息
    
    Args:
        task_id: 任务ID
    """
    try:
        if task_id not in _task_folders:
            return
        
        task_folder = _task_folders[task_id]
        summary_file = _task_summary_files[task_id]
        
        # 收集统计信息
        thread_logs = list(task_folder.glob("regression_thread_*.log"))
        
        # 写入汇总信息
        with _task_locks[task_id]:
            with open(summary_file, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"回归测试任务完成统计\n")
                f.write(f"{'='*60}\n")
                f.write(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"并发线程数量: {len(thread_logs)}\n")
                f.write(f"线程日志文件: {[log.name for log in thread_logs]}\n")
                f.write(f"=== 回归测试任务日志结束 ===\n")
        
        # 生成查看脚本
        _generate_regression_log_viewer(task_folder, task_id)
        
        # 清理全局变量
        _task_folders.pop(task_id, None)
        _task_summary_files.pop(task_id, None)
        _task_locks.pop(task_id, None)
        
    except Exception as e:
        print(f"[REGRESSION_FINALIZE_ERROR] 结束任务时出错: {e}")


def clear_current_regression_thread_task():
    """清除当前线程的回归测试任务信息"""
    task_id, file_id, log_file, thread_name = get_current_regression_thread_info()
    
    if task_id and log_file and log_file.exists():
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*50}\n")
                f.write(f"线程结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"=== 回归测试线程日志结束 ===\n")
        except Exception:
            pass
    
    # 清除线程本地存储
    for attr in ['task_id', 'file_id', 'log_file', 'thread_name']:
        if hasattr(_thread_local, attr):
            delattr(_thread_local, attr)


def _write_to_regression_summary_log(task_id: int, message: str):
    """写入回归测试汇总日志（线程安全）"""
    try:
        if task_id in _task_summary_files and task_id in _task_locks:
            with _task_locks[task_id]:
                with open(_task_summary_files[task_id], "a", encoding="utf-8") as f:
                    f.write(message + "\n")
    except Exception:
        pass  # 汇总日志失败不影响主要功能


def _fallback_regression_log(msg: str, module_name: str):
    """回归测试回退日志函数"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    formatted_msg = f"[{timestamp}] [{module_name}] {msg}"
    
    general_log_file = LOGS_DIR / "regression_general.log"
    with open(general_log_file, "a", encoding="utf-8") as f:
        f.write(formatted_msg + "\n")


def _generate_regression_log_viewer(task_folder: Path, task_id: int):
    """生成回归测试日志查看脚本"""
    viewer_script = task_folder / "view_regression_logs.py"
    with open(viewer_script, "w", encoding="utf-8") as f:
        f.write(f'''#!/usr/bin/env python3
"""
回归测试任务 {task_id} 日志查看工具
"""
import os
from pathlib import Path

def main():
    folder = Path(__file__).parent
    print(f"=== 回归测试任务 {task_id} 日志查看器 ===")
    
    # 显示汇总日志
    summary_file = folder / "regression_summary.log"
    if summary_file.exists():
        print("\\n📋 汇总日志:")
        print("-" * 50)
        with open(summary_file, "r", encoding="utf-8") as f:
            print(f.read())
    
    # 显示各线程日志
    thread_logs = sorted(folder.glob("regression_thread_*.log"))
    for log_file in thread_logs:
        print(f"\\n🧵 {{log_file.name}}:")
        print("-" * 50)
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            # 只显示前50行，避免输出过长
            for line in lines[:50]:
                print(line.rstrip())
            if len(lines) > 50:
                print(f"... (还有 {{len(lines)-50}} 行，请直接打开文件查看)")

if __name__ == "__main__":
    main()
''')


def get_concurrent_requests():
    """获取并发请求数配置"""
    try:
        from ..config import AI_CONCURRENT_REQUESTS
        return AI_CONCURRENT_REQUESTS
    except:
        return 3  # 默认值 