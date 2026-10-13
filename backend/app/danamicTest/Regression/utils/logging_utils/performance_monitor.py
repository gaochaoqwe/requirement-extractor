
try:
    from ..utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.Regression.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

"""
动态测试-回归测试性能监控工具
监控每个任务步骤的执行时间并记录到日志中
"""
import time
import threading
from typing import Dict, Any, Optional
from functools import wraps
from .logger import log_info, log_warning, get_current_task_info

# 线程本地存储，用于存储每个任务的性能数据
_thread_local = threading.local()

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """重置性能数据"""
        self.step_times = {}
        self.step_start_times = {}
        self.total_start_time = None
        self.total_end_time = None
    
    def start_total_timing(self, task_name: str = "回归测试任务"):
        """开始总体计时"""
        self.total_start_time = time.time()
        log_info(f"开始执行{task_name}，启动性能监控", "performance_monitor")
    
    def end_total_timing(self, task_name: str = "回归测试任务"):
        """结束总体计时"""
        if self.total_start_time is None:
            log_warning("总体计时未开始，无法结束计时", "performance_monitor")
            return
        
        self.total_end_time = time.time()
        total_time = self.total_end_time - self.total_start_time
        
        log_info(f"{task_name}执行完成，总耗时: {total_time:.3f}秒", "performance_monitor")
        self._log_performance_summary()
    
    def start_step(self, step_name: str):
        """开始步骤计时"""
        if step_name in self.step_start_times:
            log_warning(f"步骤 '{step_name}' 已经开始计时，将重新开始", "performance_monitor")
        
        self.step_start_times[step_name] = time.time()
        log_info(f"开始执行步骤: {step_name}", "performance_monitor")
    
    def end_step(self, step_name: str, details: str = ""):
        """结束步骤计时"""
        if step_name not in self.step_start_times:
            log_warning(f"步骤 '{step_name}' 未开始计时，无法结束", "performance_monitor")
            return
        
        end_time = time.time()
        start_time = self.step_start_times[step_name]
        duration = end_time - start_time
        
        self.step_times[step_name] = duration
        del self.step_start_times[step_name]
        
        details_str = f" - {details}" if details else ""
        log_info(f"完成步骤: {step_name}，耗时: {duration:.3f}秒{details_str}", "performance_monitor")
    
    def _log_performance_summary(self):
        """记录性能总结"""
        if not self.step_times:
            log_info("无步骤性能数据", "performance_monitor")
            return
        
        log_info("=== 性能监控总结 ===", "performance_monitor")
        
        # 按执行时间排序
        sorted_steps = sorted(self.step_times.items(), key=lambda x: x[1], reverse=True)
        
        for step_name, duration in sorted_steps:
            percentage = (duration / (self.total_end_time - self.total_start_time)) * 100 if self.total_start_time and self.total_end_time else 0
            log_info(f"  {step_name}: {duration:.3f}秒 ({percentage:.1f}%)", "performance_monitor")
        
        log_info("=== 性能监控结束 ===", "performance_monitor")

def get_performance_monitor() -> PerformanceMonitor:
    """获取当前线程的性能监控器"""
    if not hasattr(_thread_local, 'monitor'):
        _thread_local.monitor = PerformanceMonitor()
    return _thread_local.monitor

def performance_step(step_name: str, details: str = ""):
    """性能监控装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            monitor.start_step(step_name)
            try:
                result = func(*args, **kwargs)
                monitor.end_step(step_name, details)
                return result
            except Exception as e:
                monitor.end_step(step_name, f"执行失败: {str(e)}")
                raise
        return wrapper
    return decorator

def start_task_monitoring(task_name: str = "回归测试任务"):
    """开始任务监控"""
    monitor = get_performance_monitor()
    monitor.reset()
    monitor.start_total_timing(task_name)

def end_task_monitoring(task_name: str = "回归测试任务"):
    """结束任务监控"""
    monitor = get_performance_monitor()
    monitor.end_total_timing(task_name)

def monitor_step(step_name: str, details: str = ""):
    """手动记录步骤性能"""
    class StepContext:
        def __init__(self, step_name: str, details: str = ""):
            self.step_name = step_name
            self.details = details
            self.monitor = get_performance_monitor()
        
        def __enter__(self):
            self.monitor.start_step(self.step_name)
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is not None:
                self.monitor.end_step(self.step_name, f"{self.details} - 执行失败: {str(exc_val)}")
            else:
                self.monitor.end_step(self.step_name, self.details)
    
    return StepContext(step_name, details)

# 预定义的回归测试步骤
class RegressionTestSteps:
    """回归测试步骤常量"""
    INIT = "任务初始化"
    VALIDATE_INPUT = "输入验证"
    LOAD_RESOURCES = "加载资源文件"
    PARSE_IMPACT_ANALYSIS = "解析影响域分析报告"
    PARSE_PLANNING = "解析策划文档"
    AI_ANALYSIS = "AI深度分析"
    DETERMINE_REGRESSION_SCOPE = "确定回归测试范围"
    GENERATE_TEST_CASES = "生成测试用例"
    BUILD_FORMS = "构建测试表单"
    FILL_FORMS = "填充表单数据"
    GENERATE_ISSUES = "生成问题单"
    SAVE_RESULTS = "保存结果文件"
    CLEANUP = "清理资源" 