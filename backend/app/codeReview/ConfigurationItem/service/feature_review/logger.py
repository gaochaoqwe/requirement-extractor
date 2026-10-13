"""
功能审查专用日志系统
为每个功能审查任务和功能点创建独立的日志文件

日志结构:
logs/
  task_{task_id}/
    logs/
      task_summary.log
      feature_{feature_id}_{feature_name}/
        exploration.log
        review.log
        summary.log
"""
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional
import sys

# 全局变量
_thread_local = threading.local()

# 日志目录配置
CURRENT_DIR = Path(__file__).parent.parent.parent  # ConfigurationItem目录
LOGS_DIR = CURRENT_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)


class FeatureReviewLogger:
    """功能审查日志器"""
    
    def __init__(self, task_id: int, feature_id: int, feature_name: str):
        """
        初始化功能审查日志器
        
        Args:
            task_id: 任务ID
            feature_id: 功能点ID
            feature_name: 功能点名称
        """
        self.task_id = task_id
        self.feature_id = feature_id
        self.feature_name = self._sanitize_filename(feature_name)
        
        # 创建任务目录
        self.task_dir = LOGS_DIR / f"task_{task_id}"
        self.task_logs_dir = self.task_dir / "logs"
        self.task_logs_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建功能点子目录
        feature_dir_name = f"feature_{feature_id}_{self.feature_name}"
        self.feature_dir = self.task_logs_dir / feature_dir_name
        self.feature_dir.mkdir(parents=True, exist_ok=True)
        
        # 日志文件路径
        self.exploration_log = self.feature_dir / "exploration.log"
        self.review_log = self.feature_dir / "review.log"
        self.summary_log = self.feature_dir / "summary.log"
        self.task_summary_log = self.task_logs_dir / "task_summary.log"
        
        # 初始化日志文件
        self._init_logs()
        
        # 保存到线程本地存储
        _thread_local.logger = self
    
    def _sanitize_filename(self, name: str) -> str:
        """清理文件名，移除非法字符"""
        # 移除或替换非法字符
        illegal_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        sanitized = name
        for char in illegal_chars:
            sanitized = sanitized.replace(char, '_')
        # 限制长度
        if len(sanitized) > 50:
            sanitized = sanitized[:50]
        return sanitized
    
    def _init_logs(self):
        """初始化日志文件"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 初始化探索日志
        with open(self.exploration_log, 'w', encoding='utf-8') as f:
            f.write(f"{'='*60}\n")
            f.write(f"功能审查 - 代码探索阶段日志\n")
            f.write(f"{'='*60}\n")
            f.write(f"任务ID: {self.task_id}\n")
            f.write(f"功能ID: {self.feature_id}\n")
            f.write(f"功能名称: {self.feature_name}\n")
            f.write(f"开始时间: {timestamp}\n")
            f.write(f"{'='*60}\n\n")
        
        # 初始化审查日志
        with open(self.review_log, 'w', encoding='utf-8') as f:
            f.write(f"{'='*60}\n")
            f.write(f"功能审查 - 代码审查阶段日志\n")
            f.write(f"{'='*60}\n")
            f.write(f"任务ID: {self.task_id}\n")
            f.write(f"功能ID: {self.feature_id}\n")
            f.write(f"功能名称: {self.feature_name}\n")
            f.write(f"开始时间: {timestamp}\n")
            f.write(f"{'='*60}\n\n")
        
        # 初始化总结日志
        with open(self.summary_log, 'w', encoding='utf-8') as f:
            f.write(f"{'='*60}\n")
            f.write(f"功能审查 - 总结日志\n")
            f.write(f"{'='*60}\n")
            f.write(f"任务ID: {self.task_id}\n")
            f.write(f"功能ID: {self.feature_id}\n")
            f.write(f"功能名称: {self.feature_name}\n")
            f.write(f"开始时间: {timestamp}\n")
            f.write(f"{'='*60}\n\n")
        
        # 初始化或追加任务总结日志
        if not self.task_summary_log.exists():
            with open(self.task_summary_log, 'w', encoding='utf-8') as f:
                f.write(f"{'='*60}\n")
                f.write(f"功能审查任务 - 总日志\n")
                f.write(f"{'='*60}\n")
                f.write(f"任务ID: {self.task_id}\n")
                f.write(f"开始时间: {timestamp}\n")
                f.write(f"{'='*60}\n\n")
    
    def _format_message(self, message: str, level: str = "INFO") -> str:
        """格式化日志消息"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        return f"[{timestamp}] [{level}] {message}\n"
    
    def log_exploration(self, message: str, level: str = "INFO"):
        """记录探索阶段日志"""
        formatted = self._format_message(message, level)
        with open(self.exploration_log, 'a', encoding='utf-8') as f:
            f.write(formatted)
        print(f"[探索] {message}")  # 同时输出到控制台
    
    def log_review(self, message: str, level: str = "INFO"):
        """记录审查阶段日志"""
        formatted = self._format_message(message, level)
        with open(self.review_log, 'a', encoding='utf-8') as f:
            f.write(formatted)
        print(f"[审查] {message}")  # 同时输出到控制台
    
    def log_summary(self, message: str, level: str = "INFO"):
        """记录总结日志"""
        formatted = self._format_message(message, level)
        with open(self.summary_log, 'a', encoding='utf-8') as f:
            f.write(formatted)
        # 也追加到任务总结日志
        with open(self.task_summary_log, 'a', encoding='utf-8') as f:
            f.write(f"[Feature_{self.feature_id}] {formatted}")
        print(f"[总结] {message}")  # 同时输出到控制台
    
    def log_task_summary(self, message: str, level: str = "INFO"):
        """记录任务总结日志"""
        formatted = self._format_message(message, level)
        with open(self.task_summary_log, 'a', encoding='utf-8') as f:
            f.write(formatted)
        print(f"[任务] {message}")  # 同时输出到控制台
    
    def log_error(self, message: str, exception: Exception = None):
        """记录错误"""
        error_msg = message
        if exception:
            import traceback
            error_msg += f"\n异常详情: {str(exception)}\n"
            error_msg += f"堆栈跟踪:\n{traceback.format_exc()}"
        
        # 记录到所有日志文件
        formatted = self._format_message(error_msg, "ERROR")
        for log_file in [self.exploration_log, self.review_log, self.summary_log]:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(formatted)
        
        # 也记录到任务总结
        with open(self.task_summary_log, 'a', encoding='utf-8') as f:
            f.write(f"[Feature_{self.feature_id}] {formatted}")
        
        print(f"[ERROR] {message}")  # 输出到控制台
    
    def finalize(self, status: str = "completed", problems_count: int = 0):
        """完成日志记录"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        summary = f"\n{'='*60}\n"
        summary += f"功能审查完成\n"
        summary += f"状态: {status}\n"
        summary += f"发现问题数: {problems_count}\n"
        summary += f"结束时间: {timestamp}\n"
        summary += f"{'='*60}\n"
        
        # 写入到总结日志
        with open(self.summary_log, 'a', encoding='utf-8') as f:
            f.write(summary)
        
        # 写入到任务总结
        with open(self.task_summary_log, 'a', encoding='utf-8') as f:
            f.write(f"\n[Feature_{self.feature_id}_{self.feature_name}] {summary}")
        
        print(f"[完成] 功能 '{self.feature_name}' 审查完成，状态: {status}, 问题数: {problems_count}")


class TaskLogger:
    """任务级别的日志器（用于任务开始和结束）"""
    
    def __init__(self, task_id: int):
        self.task_id = task_id
        self.task_dir = LOGS_DIR / f"task_{task_id}"
        self.task_logs_dir = self.task_dir / "logs"
        self.task_logs_dir.mkdir(parents=True, exist_ok=True)
        self.task_summary_log = self.task_logs_dir / "task_summary.log"
        
        # 初始化任务日志
        if not self.task_summary_log.exists():
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(self.task_summary_log, 'w', encoding='utf-8') as f:
                f.write(f"{'='*60}\n")
                f.write(f"功能审查任务日志\n")
                f.write(f"{'='*60}\n")
                f.write(f"任务ID: {task_id}\n")
                f.write(f"开始时间: {timestamp}\n")
                f.write(f"{'='*60}\n\n")
    
    def log(self, message: str, level: str = "INFO"):
        """记录任务级别日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        formatted = f"[{timestamp}] [{level}] {message}\n"
        with open(self.task_summary_log, 'a', encoding='utf-8') as f:
            f.write(formatted)
        print(f"[任务{self.task_id}] {message}")
    
    def finalize(self, total_features: int, status: str = "completed"):
        """完成任务日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        summary = f"\n{'='*60}\n"
        summary += f"功能审查任务完成\n"
        summary += f"总功能数: {total_features}\n"
        summary += f"状态: {status}\n"
        summary += f"结束时间: {timestamp}\n"
        summary += f"{'='*60}\n"
        
        with open(self.task_summary_log, 'a', encoding='utf-8') as f:
            f.write(summary)
        print(f"[任务{self.task_id}] 审查任务完成，共处理 {total_features} 个功能")


def get_current_logger() -> Optional[FeatureReviewLogger]:
    """获取当前线程的日志器"""
    return getattr(_thread_local, 'logger', None)

