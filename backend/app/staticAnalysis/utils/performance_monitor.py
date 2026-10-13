"""
性能监控工具
用于监控静态分析过程中各个步骤的耗时
"""
import time
import functools
from typing import Dict, Any, Optional, List
from datetime import datetime
from .logger import log_info, log_debug, get_current_task_info

# 全局性能统计存储
_performance_stats: Dict[str, Dict[str, Any]] = {}

class PerformanceTimer:
    """性能计时器上下文管理器"""
    
    def __init__(self, step_name: str, category: str = "general", log_immediately: bool = True):
        self.step_name = step_name
        self.category = category
        self.log_immediately = log_immediately
        self.start_time = None
        self.end_time = None
        self.duration = None
        
    def __enter__(self):
        self.start_time = time.time()
        log_debug(f"[性能监控] 开始执行: {self.step_name}", "performance_monitor")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        
        # 记录到全局统计
        self._record_performance()
        
        if self.log_immediately:
            log_info(f"[性能监控] {self.step_name} 完成，耗时: {self.duration:.3f}秒", "performance_monitor")
    
    def _record_performance(self):
        """记录性能数据到全局统计"""
        task_id, file_id, _ = get_current_task_info()
        task_key = f"task_{task_id}_file_{file_id}" if task_id and file_id else "unknown_task"
        
        if task_key not in _performance_stats:
            _performance_stats[task_key] = {
                "task_id": task_id,
                "file_id": file_id,
                "start_time": datetime.now().isoformat(),
                "steps": [],
                "categories": {}
            }
        
        step_data = {
            "step_name": self.step_name,
            "category": self.category,
            "duration": self.duration,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "timestamp": datetime.now().isoformat()
        }
        
        _performance_stats[task_key]["steps"].append(step_data)
        
        # 按类别统计
        if self.category not in _performance_stats[task_key]["categories"]:
            _performance_stats[task_key]["categories"][self.category] = {
                "total_time": 0,
                "count": 0,
                "steps": []
            }
        
        category_stats = _performance_stats[task_key]["categories"][self.category]
        category_stats["total_time"] += self.duration
        category_stats["count"] += 1
        category_stats["steps"].append(step_data)

def performance_monitor(step_name: str, category: str = "general"):
    """
    性能监控装饰器
    
    Args:
        step_name: 步骤名称
        category: 分类名称
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with PerformanceTimer(step_name, category):
                return func(*args, **kwargs)
        return wrapper
    return decorator

def get_performance_summary(task_id: int = None, file_id: int = None) -> Dict[str, Any]:
    """
    获取性能统计摘要
    
    Args:
        task_id: 任务ID，如果为None则获取当前任务
        file_id: 文件ID，如果为None则获取当前任务
    
    Returns:
        Dict: 性能统计摘要
    """
    if task_id is None or file_id is None:
        current_task_id, current_file_id, _ = get_current_task_info()
        task_id = task_id or current_task_id
        file_id = file_id or current_file_id
    
    task_key = f"task_{task_id}_file_{file_id}"
    
    if task_key not in _performance_stats:
        return {"error": "未找到指定任务的性能数据"}
    
    stats = _performance_stats[task_key]
    
    # 计算总耗时
    total_time = sum(step["duration"] for step in stats["steps"])
    
    # 按类别汇总
    category_summary = {}
    for category, data in stats["categories"].items():
        category_summary[category] = {
            "total_time": data["total_time"],
            "count": data["count"],
            "average_time": data["total_time"] / data["count"] if data["count"] > 0 else 0,
            "percentage": (data["total_time"] / total_time * 100) if total_time > 0 else 0
        }
    
    # 找出最耗时的步骤
    slowest_steps = sorted(stats["steps"], key=lambda x: x["duration"], reverse=True)[:5]
    
    return {
        "task_id": task_id,
        "file_id": file_id,
        "total_time": total_time,
        "total_steps": len(stats["steps"]),
        "category_summary": category_summary,
        "slowest_steps": [
            {
                "step_name": step["step_name"],
                "category": step["category"],
                "duration": step["duration"],
                "percentage": (step["duration"] / total_time * 100) if total_time > 0 else 0
            }
            for step in slowest_steps
        ],
        "start_time": stats["start_time"]
    }

def log_performance_summary(task_id: int = None, file_id: int = None):
    """
    记录性能统计摘要到日志
    
    Args:
        task_id: 任务ID
        file_id: 文件ID
    """
    summary = get_performance_summary(task_id, file_id)
    
    if "error" in summary:
        log_info(f"[性能摘要] {summary['error']}", "performance_monitor")
        return
    
    log_lines = [
        "=" * 80,
        f"性能分析摘要 - 任务ID: {summary['task_id']}, 文件ID: {summary['file_id']}",
        "=" * 80,
        f"总耗时: {summary['total_time']:.3f}秒",
        f"总步骤数: {summary['total_steps']}",
        "",
        "各类别耗时统计:",
    ]
    
    # 按耗时排序显示类别统计
    sorted_categories = sorted(
        summary['category_summary'].items(),
        key=lambda x: x[1]['total_time'],
        reverse=True
    )
    
    for category, stats in sorted_categories:
        log_lines.extend([
            f"  {category}:",
            f"    总耗时: {stats['total_time']:.3f}秒 ({stats['percentage']:.1f}%)",
            f"    步骤数: {stats['count']}",
            f"    平均耗时: {stats['average_time']:.3f}秒",
            ""
        ])
    
    log_lines.extend([
        "最耗时的5个步骤:",
    ])
    
    for i, step in enumerate(summary['slowest_steps'], 1):
        log_lines.append(
            f"  {i}. {step['step_name']} ({step['category']}) - "
            f"{step['duration']:.3f}秒 ({step['percentage']:.1f}%)"
        )
    
    log_lines.append("=" * 80)
    
    log_info("\n".join(log_lines), "performance_monitor")

def clear_performance_stats(task_id: int = None, file_id: int = None):
    """
    清除指定任务的性能统计数据
    
    Args:
        task_id: 任务ID，如果为None则清除当前任务
        file_id: 文件ID，如果为None则清除当前任务
    """
    if task_id is None or file_id is None:
        current_task_id, current_file_id, _ = get_current_task_info()
        task_id = task_id or current_task_id
        file_id = file_id or current_file_id
    
    task_key = f"task_{task_id}_file_{file_id}"
    
    if task_key in _performance_stats:
        del _performance_stats[task_key]
        log_debug(f"[性能监控] 已清除任务 {task_id} 文件 {file_id} 的性能统计数据", "performance_monitor")

def get_all_performance_stats() -> Dict[str, Any]:
    """获取所有性能统计数据"""
    return _performance_stats.copy() 