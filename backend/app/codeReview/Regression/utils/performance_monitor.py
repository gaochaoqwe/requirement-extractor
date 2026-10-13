"""
Regression模块性能监控工具
提供计时器、装饰器和性能统计功能
"""
import time
import threading
from contextlib import contextmanager
from typing import Dict, List, Optional, Any
from datetime import datetime
from functools import wraps

# 全局性能统计存储
_performance_stats: Dict[str, List[Dict[str, Any]]] = {}
_stats_lock = threading.Lock()

class PerformanceTimer:
    """性能计时器上下文管理器"""
    
    def __init__(self, step_name: str, category: str = "general", log_immediately: bool = True):
        self.step_name = step_name
        self.category = category
        self.log_immediately = log_immediately
        self.start_time = None
        self.end_time = None
        self.duration = None
        self.metadata = {}
    
    def __enter__(self):
        self.start_time = time.time()
        if self.log_immediately:
            from .logger import log_info
            log_info(f"开始步骤: {self.step_name}", "performance_monitor")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        
        # 记录性能数据
        self._record_performance()
        
        if self.log_immediately:
            from .logger import log_info
            log_info(f"步骤完成: {self.step_name} - 耗时: {self.duration:.2f}s", "performance_monitor")
    
    def add_metadata(self, key: str, value: Any):
        """添加元数据"""
        self.metadata[key] = value
    
    def _record_performance(self):
        """记录性能数据到全局统计"""
        perf_data = {
            "step_name": self.step_name,
            "category": self.category,
            "duration": self.duration,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "timestamp": datetime.now().isoformat(),
            "metadata": self.metadata.copy()
        }
        
        with _stats_lock:
            if self.category not in _performance_stats:
                _performance_stats[self.category] = []
            _performance_stats[self.category].append(perf_data)

def performance_monitor(step_name: str, category: str = "general"):
    """性能监控装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with PerformanceTimer(step_name, category):
                return func(*args, **kwargs)
        return wrapper
    return decorator

def get_performance_summary(category: Optional[str] = None) -> Dict[str, Any]:
    """获取性能统计摘要"""
    with _stats_lock:
        if category:
            stats = _performance_stats.get(category, [])
        else:
            stats = []
            for cat_stats in _performance_stats.values():
                stats.extend(cat_stats)
    
    if not stats:
        return {"total_steps": 0, "total_duration": 0, "average_duration": 0}
    
    total_duration = sum(s["duration"] for s in stats)
    return {
        "total_steps": len(stats),
        "total_duration": total_duration,
        "average_duration": total_duration / len(stats),
        "steps": stats
    }

def log_performance_summary(category: Optional[str] = None):
    """记录性能统计摘要到日志"""
    summary = get_performance_summary(category)
    
    from .logger import log_info
    log_info("=" * 60, "performance_monitor")
    log_info("性能统计摘要", "performance_monitor")
    log_info("=" * 60, "performance_monitor")
    log_info(f"总步骤数: {summary['total_steps']}", "performance_monitor")
    log_info(f"总耗时: {summary['total_duration']:.2f}s", "performance_monitor")
    log_info(f"平均耗时: {summary['average_duration']:.2f}s", "performance_monitor")
    
    if "steps" in summary:
        log_info("详细步骤:", "performance_monitor")
        for step in summary["steps"]:
            log_info(f"  - {step['step_name']}: {step['duration']:.2f}s", "performance_monitor")
    
    log_info("=" * 60, "performance_monitor")

def clear_performance_stats(category: Optional[str] = None):
    """清除性能统计数据"""
    with _stats_lock:
        if category:
            _performance_stats.pop(category, None)
        else:
            _performance_stats.clear()

def get_all_performance_stats() -> Dict[str, List[Dict[str, Any]]]:
    """获取所有性能统计数据"""
    with _stats_lock:
        return _performance_stats.copy() 