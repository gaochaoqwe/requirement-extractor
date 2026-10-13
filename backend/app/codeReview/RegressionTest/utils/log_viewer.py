"""
日志查看工具
用于监控和查看ConfigurationItem的任务日志
"""
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

from .logger import LOGS_DIR, get_all_task_logs

def list_recent_logs(limit: int = 10) -> List[Dict]:
    """
    列出最近的任务日志文件
    
    Args:
        limit: 返回的日志文件数量限制
        
    Returns:
        List[Dict]: 日志文件信息列表
    """
    log_files = get_all_task_logs()
    
    # 按修改时间排序（最新的在前）
    log_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    
    result = []
    for log_file in log_files[:limit]:
        # 解析文件名获取任务信息
        filename = log_file.name
        parts = filename.replace('.log', '').split('_')
        
        task_id = "unknown"
        file_id = "unknown"
        timestamp = "unknown"
        
        if len(parts) >= 6 and parts[0] == 'task' and parts[2] == 'file':
            task_id = parts[1]
            file_id = parts[3]
            timestamp = f"{parts[4]}_{parts[5]}"
        
        # 获取文件信息
        stat = log_file.stat()
        modified_time = datetime.fromtimestamp(stat.st_mtime)
        size = stat.st_size
        
        result.append({
            'file_path': str(log_file),
            'filename': filename,
            'task_id': task_id,
            'file_id': file_id,
            'timestamp': timestamp,
            'modified_time': modified_time.strftime('%Y-%m-%d %H:%M:%S'),
            'size_bytes': size,
            'size_kb': round(size / 1024, 2)
        })
    
    return result

def get_log_content(log_file_path: str, tail_lines: Optional[int] = None) -> str:
    """
    获取日志文件内容
    
    Args:
        log_file_path: 日志文件路径
        tail_lines: 只返回最后N行（可选）
        
    Returns:
        str: 日志内容
    """
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            if tail_lines:
                lines = f.readlines()
                return ''.join(lines[-tail_lines:])
            else:
                return f.read()
    except Exception as e:
        return f"读取日志文件失败: {e}"

def find_logs_by_task_id(task_id: str) -> List[Path]:
    """
    根据任务ID查找相关的日志文件
    
    Args:
        task_id: 任务ID
        
    Returns:
        List[Path]: 匹配的日志文件路径列表
    """
    pattern = f"task_{task_id}_*.log"
    return list(LOGS_DIR.glob(pattern))

def find_logs_by_file_id(file_id: str) -> List[Path]:
    """
    根据文件ID查找相关的日志文件
    
    Args:
        file_id: 文件ID
        
    Returns:
        List[Path]: 匹配的日志文件路径列表
    """
    pattern = f"task_*_file_{file_id}_*.log"
    return list(LOGS_DIR.glob(pattern))

def search_logs(keyword: str, recent_count: int = 20) -> List[Dict]:
    """
    在日志中搜索关键词
    
    Args:
        keyword: 搜索关键词
        recent_count: 搜索最近的N个日志文件
        
    Returns:
        List[Dict]: 包含关键词的日志条目
    """
    log_files = get_all_task_logs()
    log_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    
    results = []
    
    for log_file in log_files[:recent_count]:
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            for line_num, line in enumerate(lines, 1):
                if keyword.lower() in line.lower():
                    results.append({
                        'file': str(log_file),
                        'filename': log_file.name,
                        'line_number': line_num,
                        'content': line.strip(),
                        'timestamp': line.split(']')[0].replace('[', '') if ']' in line else 'unknown'
                    })
        except Exception as e:
            continue
    
    return results

def get_log_statistics() -> Dict:
    """
    获取日志统计信息
    
    Returns:
        Dict: 统计信息
    """
    log_files = get_all_task_logs()
    
    if not log_files:
        return {
            'total_logs': 0,
            'total_size': 0,
            'oldest_log': None,
            'newest_log': None
        }
    
    total_size = sum(f.stat().st_size for f in log_files)
    
    # 按时间排序
    log_files.sort(key=lambda f: f.stat().st_mtime)
    
    oldest = log_files[0]
    newest = log_files[-1]
    
    return {
        'total_logs': len(log_files),
        'total_size_bytes': total_size,
        'total_size_mb': round(total_size / (1024 * 1024), 2),
        'oldest_log': {
            'filename': oldest.name,
            'date': datetime.fromtimestamp(oldest.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        },
        'newest_log': {
            'filename': newest.name,
            'date': datetime.fromtimestamp(newest.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        }
    }

def print_log_summary(use_console: bool = True):
    """
    打印日志摘要信息（用于命令行）
    
    Args:
        use_console: 是否输出到控制台，默认为True
    """
    from .logger import log_info
    
    summary_lines = []
    summary_lines.append("=== ConfigurationItem 任务日志摘要 ===")
    
    # 统计信息
    stats = get_log_statistics()
    summary_lines.append(f"总日志文件数: {stats['total_logs']}")
    summary_lines.append(f"总大小: {stats['total_size_mb']} MB")
    
    if stats['total_logs'] > 0:
        summary_lines.append(f"最早日志: {stats['oldest_log']['filename']} ({stats['oldest_log']['date']})")
        summary_lines.append(f"最新日志: {stats['newest_log']['filename']} ({stats['newest_log']['date']})")
    
    summary_lines.append("\n=== 最近的10个任务日志 ===")
    recent_logs = list_recent_logs(10)
    
    for log in recent_logs:
        summary_lines.append(f"任务{log['task_id']}_文件{log['file_id']} | {log['modified_time']} | {log['size_kb']}KB | {log['filename']}")
    
    # 记录到日志系统
    summary_text = "\n".join(summary_lines)
    log_info(f"日志摘要查询:\n{summary_text}", "log_viewer")
    
    # 可选的控制台输出
    if use_console:
        for line in summary_lines:
            print(line)

if __name__ == "__main__":
    print_log_summary() 