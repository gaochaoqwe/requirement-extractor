"""
改进的并发日志系统

每个任务创建独立文件夹，并发请求创建独立日志文件，
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
CURRENT_DIR = Path(__file__).parent.parent  # ConfigurationItem目录
LOGS_DIR = CURRENT_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)  # 添加parents=True以创建父目录

# 全局任务信息
_task_folders: Dict[int, Path] = {}  # task_id -> 文件夹路径
_task_summary_files: Dict[int, Path] = {}  # task_id -> 汇总日志文件
_task_locks: Dict[int, threading.Lock] = {}  # task_id -> 汇总日志锁


def init_concurrent_task(task_id: int, file_id: int, tester_name: str = None) -> Path:
    """
    初始化并发任务的日志系统
    
    Args:
        task_id: 任务ID
        file_id: 文件ID
        tester_name: 测试人员姓名
        
    Returns:
        Path: 任务日志文件夹路径
    """
    # 检查是否已存在该任务的文件夹（避免重复创建）
    if task_id in _task_folders:
        return _task_folders[task_id]
    
    # 创建任务专用文件夹（只使用task_id，不带时间戳，避免重复）
    task_folder = LOGS_DIR / f"task_{task_id}"
    task_folder.mkdir(parents=True, exist_ok=True)
    
    # 创建logs子文件夹存储日志文件
    logs_subfolder = task_folder / "logs"
    logs_subfolder.mkdir(parents=True, exist_ok=True)
    
    # 创建汇总日志文件（放在logs子文件夹内）
    summary_file = logs_subfolder / "task_summary.log"
    
    # 保存到全局字典
    _task_folders[task_id] = task_folder
    _task_summary_files[task_id] = summary_file
    _task_locks[task_id] = threading.Lock()
    
    # 保存测试人员信息到全局字典（用于后续线程日志创建）
    if not hasattr(_thread_local, 'task_testers'):
        _thread_local.task_testers = {}
    if tester_name:
        globals()[f'_task_tester_{task_id}'] = tester_name
    
    # 初始化汇总日志文件
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write(f"=== 代码审查任务汇总日志 ===\n")
        f.write(f"任务ID: {task_id}\n")
        f.write(f"文件ID: {file_id}\n")
        if tester_name:
            f.write(f"测试人员: {tester_name}\n")
        f.write(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"日志文件夹: {task_folder.name}\n")
        f.write(f"并发设置: {get_concurrent_requests()}\n")
        f.write(f"{'='*60}\n\n")
    
    return task_folder


def set_current_thread_task(task_id: int, file_id: int, thread_name: str = None):
    """
    为当前线程设置任务信息
    
    Args:
        task_id: 任务ID
        file_id: 文件ID  
        thread_name: 线程名称（可选）
    """
    if thread_name is None:
        thread_name = f"thread_{threading.current_thread().ident}"
    
    # 设置线程本地存储
    _thread_local.task_id = task_id
    _thread_local.file_id = file_id
    _thread_local.thread_name = thread_name
    
    # 获取任务文件夹
    task_folder = _task_folders.get(task_id)
    if task_folder is None:
        # 如果任务文件夹不存在，先初始化
        task_folder = init_concurrent_task(task_id, file_id)
    
    # 确定logs子文件夹
    logs_subfolder = task_folder / "logs"
    logs_subfolder.mkdir(parents=True, exist_ok=True)
    
    # 创建线程专用日志文件（根据线程名称前缀区分审查类型）
    if thread_name.startswith('function_') or thread_name.startswith('worker_'):
        log_filename = f"function_{thread_name}.log"
        review_type = "FUNCTION_REVIEW"
    elif thread_name.startswith('business_'):
        log_filename = f"business_{thread_name}.log"
        review_type = "BUSINESS_REVIEW"
    elif thread_name.startswith('fpga_worker_'):
        log_filename = f"fpga_{thread_name}.log"
        review_type = "FPGA_REVIEW"
    else:
        log_filename = f"{thread_name}.log"
        review_type = "UNKNOWN"
    
    # 线程日志文件放在logs子文件夹内
    thread_log_file = logs_subfolder / log_filename
    _thread_local.log_file = thread_log_file
    
    # 初始化线程日志文件（只在文件不存在时创建头部）
    if not thread_log_file.exists():
        # 获取测试人员信息
        tester_name = globals().get(f'_task_tester_{task_id}', None)
        
        with open(thread_log_file, "w", encoding="utf-8") as f:
            f.write(f"=== {review_type} 线程日志 - {thread_name} ===\n")
            f.write(f"任务ID: {task_id}\n")
            f.write(f"文件ID: {file_id}\n")
            if tester_name:
                f.write(f"测试人员: {tester_name}\n")
            f.write(f"线程ID: {threading.current_thread().ident}\n")
            f.write(f"审查类型: {review_type}\n")
            f.write(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*50}\n\n")


def get_current_thread_info():
    """
    获取当前线程的任务信息
    
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


def _append_jsonl(task_id: int, obj: Dict[str, Any], filename: str):
    """将JSON对象追加写入到当前task的logs子目录中的jsonl文件（一行一个JSON）。"""
    try:
        task_folder = _task_folders.get(task_id)
        if task_folder is None:
            # 尽量容错：如果没初始化，创建一个最低限度目录
            task_folder = LOGS_DIR / f"task_{task_id}"
            task_folder.mkdir(parents=True, exist_ok=True)
            _task_folders[task_id] = task_folder

        logs_subfolder = task_folder / "logs"
        logs_subfolder.mkdir(parents=True, exist_ok=True)
        target = logs_subfolder / filename

        # 与summary共用task锁，保证多线程写文件不交叉
        lock = _task_locks.get(task_id)
        if lock is None:
            _task_locks[task_id] = threading.Lock()
            lock = _task_locks[task_id]

        line = json.dumps(obj, ensure_ascii=False)
        with lock:
            with open(target, "a", encoding="utf-8") as f:
                f.write(line + "\n")
    except Exception as e:
        print(f"[CONCURRENT_LOG_ERROR] JSONL写入失败: {e}")


def log_concurrent_jsonl(obj: Dict[str, Any], filename: str = "ai_requests.jsonl"):
    """把结构化数据写入当前任务的jsonl文件（默认 ai_requests.jsonl）。"""
    task_id, file_id, log_file, thread_name = get_current_thread_info()
    if not task_id:
        # 没有task上下文就无法归档到task目录
        return
    _append_jsonl(task_id, obj, filename)


def log_concurrent_pretty(obj: Dict[str, Any], filename: str = "ai_requests_pretty.log"):
    """把结构化数据写入当前任务的多行pretty日志文件，便于人工查看。"""
    task_id, file_id, log_file, thread_name = get_current_thread_info()
    if not task_id:
        return

    try:
        task_folder = _task_folders.get(task_id)
        if task_folder is None:
            task_folder = LOGS_DIR / f"task_{task_id}"
            task_folder.mkdir(parents=True, exist_ok=True)
            _task_folders[task_id] = task_folder

        logs_subfolder = task_folder / "logs"
        logs_subfolder.mkdir(parents=True, exist_ok=True)
        target = logs_subfolder / filename

        lock = _task_locks.get(task_id)
        if lock is None:
            _task_locks[task_id] = threading.Lock()
            lock = _task_locks[task_id]

        pretty = json.dumps(obj, ensure_ascii=False, indent=2)
        with lock:
            with open(target, "a", encoding="utf-8") as f:
                f.write("\n" + ("=" * 120) + "\n")
                f.write(pretty + "\n")
    except Exception as e:
        print(f"[CONCURRENT_LOG_ERROR] pretty日志写入失败: {e}")


def log_concurrent_text(text: str, filename: str = "ai_prompts_readable.log"):
    """把长文本按原始换行写入当前任务日志文件（适合查看prompt全文）。"""
    task_id, file_id, log_file, thread_name = get_current_thread_info()
    if not task_id:
        return

    try:
        task_folder = _task_folders.get(task_id)
        if task_folder is None:
            task_folder = LOGS_DIR / f"task_{task_id}"
            task_folder.mkdir(parents=True, exist_ok=True)
            _task_folders[task_id] = task_folder

        logs_subfolder = task_folder / "logs"
        logs_subfolder.mkdir(parents=True, exist_ok=True)
        target = logs_subfolder / filename

        lock = _task_locks.get(task_id)
        if lock is None:
            _task_locks[task_id] = threading.Lock()
            lock = _task_locks[task_id]

        with lock:
            with open(target, "a", encoding="utf-8") as f:
                f.write(text)
                if not text.endswith("\n"):
                    f.write("\n")
    except Exception as e:
        print(f"[CONCURRENT_LOG_ERROR] text日志写入失败: {e}")


def log_concurrent_debug(msg: str, module_name: str = ""):
    """
    并发安全的调试日志记录函数
    
    Args:
        msg: 日志消息
        module_name: 模块名称
    """
    try:
        task_id, file_id, log_file, thread_name = get_current_thread_info()
        
        if not task_id or not log_file:
            # 回退到普通日志
            _fallback_log(msg, module_name)
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
        _write_to_summary_log(task_id, formatted_msg)
        
    except Exception as e:
        print(f"[CONCURRENT_LOG_ERROR] 日志记录失败: {e}, 原始消息: {msg}")


def log_concurrent_info(msg: str, module_name: str = ""):
    """并发安全的信息日志"""
    log_concurrent_debug(f"[INFO] {msg}", module_name)


def log_concurrent_warning(msg: str, module_name: str = ""):
    """并发安全的警告日志"""
    log_concurrent_debug(f"[WARNING] {msg}", module_name)


def log_concurrent_error(msg: str, module_name: str = "", exception: Exception = None):
    """并发安全的错误日志"""
    error_msg = f"[ERROR] {msg}"
    if exception:
        import traceback
        error_msg += f" - 异常详情: {str(exception)}"
        error_msg += f"\n堆栈跟踪:\n{traceback.format_exc()}"
    log_concurrent_debug(error_msg, module_name)


def log_concurrent_ai_result(ai_result: Dict[str, Any], function_name: str = "", module_name: str = "ai_analyzer"):
    """
    并发安全的AI结果日志记录
    
    Args:
        ai_result: AI返回的结果字典
        function_name: 函数名
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
            for i, problem in enumerate(problems, 1):
                log_lines.append(f"问题 {i}:")
                log_lines.append(f"  等级: {problem.get('issue_level', 'N/A')}")
                log_lines.append(f"  名称: {problem.get('issue_name', 'N/A')}")
                log_lines.append(f"  位置: {problem.get('issue_location', 'N/A')}")
                log_lines.append(f"  描述: {problem.get('description_issue', 'N/A')}")
        else:
            log_lines.append("未发现问题")
        
        log_lines.append("=" * 60)
        formatted_result = "\n".join(log_lines)
        log_concurrent_debug(formatted_result, module_name)
        
    except Exception as e:
        log_concurrent_error(f"格式化AI结果失败，记录原始结果: {ai_result}", module_name, e)


def finalize_concurrent_task(task_id: int):
    """
    结束并发任务，生成汇总信息
    
    Args:
        task_id: 任务ID
    """
    try:
        if task_id not in _task_folders:
            return
        
        task_folder = _task_folders[task_id]
        summary_file = _task_summary_files[task_id]
        
        # 收集统计信息（从logs子文件夹）
        logs_subfolder = task_folder / "logs"
        thread_logs = list(logs_subfolder.glob("*.log"))
        thread_logs = [log for log in thread_logs if log.name != "task_summary.log"]
        
        # 写入汇总信息
        with _task_locks[task_id]:
            with open(summary_file, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"任务完成统计\n")
                f.write(f"{'='*60}\n")
                f.write(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"并发线程数量: {len(thread_logs)}\n")
                f.write(f"线程日志文件: {[log.name for log in thread_logs]}\n")
                f.write(f"=== 任务日志结束 ===\n")
        
        # 生成查看脚本
        _generate_log_viewer(task_folder, task_id)
        
        # 清理全局变量
        _task_folders.pop(task_id, None)
        _task_summary_files.pop(task_id, None)
        _task_locks.pop(task_id, None)
        
    except Exception as e:
        print(f"[FINALIZE_ERROR] 结束任务时出错: {e}")


def clear_current_thread_task():
    """清除当前线程的任务信息"""
    task_id, file_id, log_file, thread_name = get_current_thread_info()
    
    if task_id and log_file and log_file.exists():
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*50}\n")
                f.write(f"线程结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"=== 线程日志结束 ===\n")
        except Exception:
            pass
    
    # 清除线程本地存储
    for attr in ['task_id', 'file_id', 'log_file', 'thread_name']:
        if hasattr(_thread_local, attr):
            delattr(_thread_local, attr)


def _write_to_summary_log(task_id: int, message: str):
    """写入汇总日志（线程安全）"""
    try:
        if task_id in _task_summary_files and task_id in _task_locks:
            with _task_locks[task_id]:
                with open(_task_summary_files[task_id], "a", encoding="utf-8") as f:
                    f.write(message + "\n")
    except Exception:
        pass  # 汇总日志失败不影响主要功能


def _fallback_log(msg: str, module_name: str):
    """回退日志函数"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    formatted_msg = f"[{timestamp}] [{module_name}] {msg}"
    
    general_log_file = LOGS_DIR / "general.log"
    with open(general_log_file, "a", encoding="utf-8") as f:
        f.write(formatted_msg + "\n")


def _generate_log_viewer(task_folder: Path, task_id: int):
    """生成日志查看脚本"""
    viewer_script = task_folder / "view_logs.py"
    with open(viewer_script, "w", encoding="utf-8") as f:
        f.write(f'''#!/usr/bin/env python3
"""
任务 {task_id} 日志查看工具
"""
import os
from pathlib import Path

def main():
    task_folder = Path(__file__).parent
    logs_folder = task_folder / "logs"
    memory_folder = task_folder / "memory"
    
    print(f"=== 任务 {task_id} 日志查看器 ===")
    print(f"任务文件夹: {{task_folder}}")
    print(f"日志文件夹: {{logs_folder}}")
    print(f"记忆文件夹: {{memory_folder}}")
    print("=" * 60)
    
    # 显示汇总日志
    summary_file = logs_folder / "task_summary.log"
    if summary_file.exists():
        print("\\n📋 汇总日志:")
        print("-" * 50)
        with open(summary_file, "r", encoding="utf-8") as f:
            print(f.read())
    else:
        print("\\n⚠️ 未找到汇总日志文件")
    
    # 显示各线程日志
    if logs_folder.exists():
        thread_logs = sorted([f for f in logs_folder.glob("*.log") if f.name != "task_summary.log"])
        if thread_logs:
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
        else:
            print("\\n⚠️ 未找到线程日志文件")
    
    # 显示记忆文件
    if memory_folder.exists():
        memory_files = sorted(memory_folder.glob("*.json"))
        if memory_files:
            print("\\n🧠 渐进式发现记忆文件:")
            print("-" * 50)
            for mem_file in memory_files:
                print(f"  - {{mem_file.name}}")
        else:
            print("\\n⚠️ 未找到记忆文件")

if __name__ == "__main__":
    main()
''')


def get_task_folder(task_id: int) -> Optional[Path]:
    """
    获取指定任务的文件夹路径
    
    Args:
        task_id: 任务ID
        
    Returns:
        Path: 任务文件夹路径，如果不存在返回None
    """
    return _task_folders.get(task_id)


def get_concurrent_requests():
    """获取并发请求数配置"""
    try:
        from ..config import AI_CONCURRENT_REQUESTS
        return AI_CONCURRENT_REQUESTS
    except:
        return 3  # 默认值 