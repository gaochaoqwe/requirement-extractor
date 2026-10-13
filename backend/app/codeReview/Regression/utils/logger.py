"""
统一的日志管理工具
为回归测试模块中的每个分析任务创建独立的日志文件
"""
import os
import threading
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# 全局变量存储当前任务的日志信息
_current_task_id: Optional[int] = None
_current_file_id: Optional[int] = None
_current_log_file: Optional[Path] = None
_thread_local = threading.local()

# 日志目录配置
CURRENT_DIR = Path(__file__).parent.parent  # Regression目录
LOGS_DIR = CURRENT_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

def set_current_task(task_id: int, file_id: int):
    """
    设置当前任务的ID，用于创建对应的日志文件
    
    Args:
        task_id: 任务ID
        file_id: 文件ID
    """
    global _current_task_id, _current_file_id, _current_log_file
    _current_task_id = task_id
    _current_file_id = file_id
    
    # 同时设置到线程本地存储
    _thread_local.task_id = task_id
    _thread_local.file_id = file_id
    
    # 创建任务专用日志文件（使用时间戳确保唯一性）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"regression_task_{task_id}_file_{file_id}_{timestamp}.log"
    _current_log_file = LOGS_DIR / log_filename
    _thread_local.log_file = _current_log_file
    
    # 初始化日志文件
    with open(_current_log_file, "w", encoding="utf-8") as f:
        f.write(f"=== 回归测试任务日志 ===\n")
        f.write(f"任务ID: {task_id}\n")
        f.write(f"文件ID: {file_id}\n")
        f.write(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"日志文件: {log_filename}\n")
        f.write(f"{'='*50}\n\n")

def get_current_task_info():
    """
    获取当前任务信息，优先从线程本地存储获取
    
    Returns:
        tuple: (task_id, file_id, log_file)
    """
    # 优先从线程本地存储获取
    if (hasattr(_thread_local, 'task_id') and 
        hasattr(_thread_local, 'file_id') and 
        hasattr(_thread_local, 'log_file')):
        return _thread_local.task_id, _thread_local.file_id, _thread_local.log_file
    
    # 回退到全局变量
    return _current_task_id, _current_file_id, _current_log_file

def log_debug(msg: str, module_name: str = ""):
    """
    统一的调试日志记录函数
    
    Args:
        msg: 日志消息
        module_name: 模块名称（可选）
    """
    try:
        # 获取当前任务信息
        task_id, file_id, log_file = get_current_task_info()
        
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        # 格式化日志消息
        if module_name:
            formatted_msg = f"[{timestamp}] [{module_name}] {msg}"
        else:
            formatted_msg = f"[{timestamp}] {msg}"
        
        # 如果有当前任务，写入任务专用日志文件
        if task_id is not None and file_id is not None and log_file is not None:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(formatted_msg + "\n")
        else:
            # 如果没有当前任务，写入通用日志文件
            general_log_file = LOGS_DIR / "general.log"
            with open(general_log_file, "a", encoding="utf-8") as f:
                f.write(formatted_msg + "\n")
        
    except Exception as e:
        # 如果日志记录失败，至少输出到控制台
        print(f"[LOG_ERROR] 回归测试日志记录失败: {e}, 原始消息: {msg}")

def log_info(msg: str, module_name: str = ""):
    """信息级别日志"""
    log_debug(f"[INFO] {msg}", module_name)

def log_warning(msg: str, module_name: str = ""):
    """警告级别日志"""
    log_debug(f"[WARNING] {msg}", module_name)

def log_error(msg: str, module_name: str = "", exception: Exception = None):
    """错误级别日志"""
    error_msg = f"[ERROR] {msg}"
    if exception:
        import traceback
        error_msg += f" - 异常详情: {str(exception)}"
        error_msg += f"\n堆栈跟踪:\n{traceback.format_exc()}"
    log_debug(error_msg, module_name)

def log_ai_result(ai_result: Dict[str, Any], function_name: str = "", module_name: str = "ai_analyzer"):
    """
    格式化记录AI分析结果
    
    Args:
        ai_result: AI返回的结果字典
        function_name: 被分析的函数名
        module_name: 模块名称
    """
    try:
        # 构建格式化的AI结果日志
        log_lines = []
        log_lines.append("=" * 60)
        log_lines.append(f"AI分析结果 - 函数: {function_name}")
        log_lines.append("=" * 60)
        
        # 处理问题列表
        problems = ai_result.get("problems", [])
        if problems:
            log_lines.append(f"发现问题数量: {len(problems)}")
            log_lines.append("")
            
            for i, problem in enumerate(problems, 1):
                log_lines.append(f"问题 {i}:")
                log_lines.append(f"  文件名: {problem.get('file_name', 'N/A')}")
                log_lines.append(f"  问题等级: {problem.get('issue_level', 'N/A')}")
                log_lines.append(f"  问题名称: {problem.get('issue_name', 'N/A')}")
                log_lines.append(f"  问题位置: {problem.get('issue_location', 'N/A')}")
                log_lines.append(f"  问题描述: {problem.get('description_issue', 'N/A')}")
                log_lines.append(f"  影响描述: {problem.get('description_impact', 'N/A')}")
                
                # 显示相关源代码（如果有的话）
                source_code = problem.get('source_code', '')
                if source_code:
                    # 限制源代码显示长度，避免日志过长
                    if len(source_code) > 200:
                        source_code = source_code[:200] + "..."
                    log_lines.append(f"  相关代码: {source_code}")
                log_lines.append("")
        else:
            log_lines.append("未发现问题")
            log_lines.append("")
        
        # 处理函数信息
        function_info = ai_result.get("function_info", {})
        if function_info:
            log_lines.append("函数信息:")
            func_desc = function_info.get('function_description', '')
            if func_desc:
                log_lines.append(f"  函数描述: {func_desc}")
            
            commented_code = function_info.get('commented_code', '')
            if commented_code:
                # 限制注释代码显示长度
                if len(commented_code) > 300:
                    commented_code = commented_code[:300] + "..."
                log_lines.append(f"  注释后代码: {commented_code}")
            log_lines.append("")
        
        # 处理错误信息
        if "error" in ai_result:
            log_lines.append(f"AI分析错误: {ai_result['error']}")
            log_lines.append("")
        
        log_lines.append("=" * 60)
        
        # 将格式化的结果写入日志
        formatted_result = "\n".join(log_lines)
        log_debug(formatted_result, module_name)
        
    except Exception as e:
        # 如果格式化失败，记录原始结果
        log_error(f"格式化AI结果失败，记录原始结果: {ai_result}", module_name, e)

def clear_current_task():
    """清除当前任务信息"""
    global _current_task_id, _current_file_id, _current_log_file
    
    # 记录任务结束
    if _current_log_file and _current_log_file.exists():
        try:
            with open(_current_log_file, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*50}\n")
                f.write(f"任务结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"=== 回归测试任务日志结束 ===\n")
        except Exception:
            pass
    
    _current_task_id = None
    _current_file_id = None
    _current_log_file = None
    
    # 清除线程本地存储
    if hasattr(_thread_local, 'task_id'):
        delattr(_thread_local, 'task_id')
    if hasattr(_thread_local, 'file_id'):
        delattr(_thread_local, 'file_id')
    if hasattr(_thread_local, 'log_file'):
        delattr(_thread_local, 'log_file')

def get_all_task_logs():
    """
    获取所有任务日志文件列表
    
    Returns:
        list: 日志文件路径列表
    """
    return list(LOGS_DIR.glob("regression_task_*.log"))

def cleanup_old_logs(days: int = 7):
    """
    清理指定天数前的日志文件
    
    Args:
        days: 保留天数
    """
    try:
        import time
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        
        cleaned_count = 0
        for log_file in LOGS_DIR.glob("*.log"):
            if log_file.stat().st_mtime < cutoff_time:
                log_file.unlink()
                cleaned_count += 1
                
        if cleaned_count > 0:
            log_info(f"已清理 {cleaned_count} 个过期日志文件", "log_cleaner")
                
    except Exception as e:
        log_error(f"清理日志文件时出错", "log_cleaner", e)

def get_current_log_file():
    """
    获取当前任务的日志文件路径
    
    Returns:
        Path: 当前日志文件路径，如果没有当前任务则返回None
    """
    _, _, log_file = get_current_task_info()
    return log_file 