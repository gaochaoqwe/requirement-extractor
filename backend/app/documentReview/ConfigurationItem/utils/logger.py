"""
统一的日志管理工具
为文档审查-配置项测试模块中的每个审查任务创建独立的日志文件
"""
import os
import threading
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# 全局变量存储当前任务的日志信息
_current_session_id: Optional[str] = None
_current_log_file: Optional[Path] = None
_thread_local = threading.local()

# 日志目录配置
CURRENT_DIR = Path(__file__).parent.parent  # ConfigurationItem目录
LOGS_DIR = CURRENT_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

def set_current_session(session_id: str):
    """
    设置当前审查会话的ID，用于创建对应的日志文件
    
    Args:
        session_id: 审查会话ID
    """
    global _current_session_id, _current_log_file
    _current_session_id = session_id
    
    # 同时设置到线程本地存储
    _thread_local.session_id = session_id
    
    # 创建会话专用日志文件（使用时间戳确保唯一性）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"doc_review_session_{session_id}_{timestamp}.log"
    _current_log_file = LOGS_DIR / log_filename
    _thread_local.log_file = _current_log_file
    
    # 初始化日志文件
    with open(_current_log_file, "w", encoding="utf-8") as f:
        f.write(f"=== 文档审查配置项任务日志 ===\n")
        f.write(f"会话ID: {session_id}\n")
        f.write(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"日志文件: {log_filename}\n")
        f.write(f"{'='*50}\n\n")

def get_current_session_info():
    """
    获取当前会话信息，优先从线程本地存储获取
    
    Returns:
        tuple: (session_id, log_file)
    """
    # 优先从线程本地存储获取
    if (hasattr(_thread_local, 'session_id') and 
        hasattr(_thread_local, 'log_file')):
        return _thread_local.session_id, _thread_local.log_file
    
    # 回退到全局变量
    return _current_session_id, _current_log_file

def log_debug(msg: str, module_name: str = ""):
    """
    统一的调试日志记录函数
    
    Args:
        msg: 日志消息
        module_name: 模块名称（可选）
    """
    try:
        # 获取当前会话信息
        session_id, log_file = get_current_session_info()
        
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        # 格式化日志消息
        if module_name:
            formatted_msg = f"[{timestamp}] [{module_name}] {msg}"
        else:
            formatted_msg = f"[{timestamp}] {msg}"
        
        # 如果有当前会话，写入会话专用日志文件
        if session_id is not None and log_file is not None:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(formatted_msg + "\n")
        else:
            # 如果没有当前会话，写入通用日志文件
            general_log_file = LOGS_DIR / "general.log"
            with open(general_log_file, "a", encoding="utf-8") as f:
                f.write(formatted_msg + "\n")
        
    except Exception as e:
        # 如果日志记录失败，至少输出到控制台
        print(f"[LOG_ERROR] 文档审查日志记录失败: {e}, 原始消息: {msg}")

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

def log_ai_result(ai_result: Dict[str, Any], document_name: str = "", module_name: str = "ai_reviewer"):
    """
    格式化记录AI审查结果
    
    Args:
        ai_result: AI返回的结果字典
        document_name: 被审查的文档名称
        module_name: 模块名称
    """
    try:
        # 构建格式化的AI结果日志
        log_lines = []
        log_lines.append("=" * 60)
        log_lines.append(f"AI审查结果 - 文档: {document_name}")
        log_lines.append("=" * 60)
        
        # 处理审查结果列表
        issues = ai_result.get("issues", [])
        if issues:
            log_lines.append(f"发现问题数量: {len(issues)}")
            log_lines.append("")
            
            for i, issue in enumerate(issues, 1):
                log_lines.append(f"问题 {i}:")
                log_lines.append(f"  问题类型: {issue.get('issue_type', 'N/A')}")
                log_lines.append(f"  严重程度: {issue.get('severity', 'N/A')}")
                log_lines.append(f"  问题位置: {issue.get('issue_location', 'N/A')}")
                log_lines.append(f"  问题描述: {issue.get('issue_description', 'N/A')}")
                log_lines.append(f"  修改建议: {issue.get('suggestion', 'N/A')}")
                
                # 显示相关内容（如果有的话）
                requirement_content = issue.get('requirement_content', '')
                if requirement_content:
                    # 限制内容显示长度，避免日志过长
                    if len(requirement_content) > 200:
                        requirement_content = requirement_content[:200] + "..."
                    log_lines.append(f"  需求内容: {requirement_content}")
                log_lines.append("")
        else:
            log_lines.append("未发现问题")
            log_lines.append("")
        
        # 处理审查摘要
        summary = ai_result.get("summary", {})
        if summary:
            log_lines.append("审查摘要:")
            total_issues = summary.get('total_issues', 0)
            if total_issues:
                log_lines.append(f"  总问题数: {total_issues}")
            
            severity_breakdown = summary.get('severity_breakdown', {})
            if severity_breakdown:
                log_lines.append("  严重程度分布:")
                for severity, count in severity_breakdown.items():
                    log_lines.append(f"    {severity}: {count}")
            log_lines.append("")
        
        # 处理错误信息
        if "error" in ai_result:
            log_lines.append(f"AI审查错误: {ai_result['error']}")
            log_lines.append("")
        
        log_lines.append("=" * 60)
        
        # 将格式化的结果写入日志
        formatted_result = "\n".join(log_lines)
        log_debug(formatted_result, module_name)
        
    except Exception as e:
        # 如果格式化失败，记录原始结果
        log_error(f"格式化AI结果失败，记录原始结果: {ai_result}", module_name, e)

def clear_current_session():
    """清除当前会话信息"""
    global _current_session_id, _current_log_file
    
    # 记录会话结束
    if _current_log_file and _current_log_file.exists():
        try:
            with open(_current_log_file, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*50}\n")
                f.write(f"会话结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"=== 文档审查配置项任务日志结束 ===\n")
        except Exception:
            pass
    
    _current_session_id = None
    _current_log_file = None
    
    # 清除线程本地存储
    if hasattr(_thread_local, 'session_id'):
        delattr(_thread_local, 'session_id')
    if hasattr(_thread_local, 'log_file'):
        delattr(_thread_local, 'log_file')

def get_all_session_logs():
    """
    获取所有会话日志文件列表
    
    Returns:
        list: 日志文件路径列表
    """
    return list(LOGS_DIR.glob("doc_review_session_*.log"))

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
    获取当前会话的日志文件路径
    
    Returns:
        Path: 当前日志文件路径，如果没有当前会话则返回None
    """
    _, log_file = get_current_session_info()
    return log_file 