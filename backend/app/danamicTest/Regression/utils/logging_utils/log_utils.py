
try:
    from ..utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.Regression.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

"""
全局日志工具模块

提供全局日志去重和过滤功能，避免重复日志问题
"""
import os
import logging
import time
from typing import Dict, Any, Callable, Optional, Set, List

# 全局日志缓存，用于去重
_GLOBAL_LOG_CACHE: Set[str] = set()

# 最后日志时间记录，用于基于时间间隔的控制
_LAST_LOG_TIME: Dict[str, float] = {}

# 禁用特定类型的日志（如进度查询日志）
_DISABLED_LOG_PATTERNS: Set[str] = set()

# 已经配置过的日志器
_CONFIGURED_LOGGERS: Set[str] = set()

# 已添加的日志处理器记录
_HANDLER_PATHS: Set[str] = set()


def log_once(logger_func: Callable, message: str, cache_key: Optional[str] = None,
            reset_after: int = 0) -> None:
    """
    确保相同的日志消息只打印一次
    
    Args:
        logger_func: 日志记录函数 (logger.info, logger.warning 等)
        message: 日志消息
        cache_key: 用于去重的缓存键，默认使用消息本身
        reset_after: 重置缓存的时间(秒)，0表示永不重置
    """
    global _GLOBAL_LOG_CACHE
    
    # 如果没有提供缓存键，则使用消息本身作为键
    if cache_key is None:
        cache_key = message
    
    # 检查消息是否已经打印过
    if cache_key not in _GLOBAL_LOG_CACHE:
        # 如果包含禁用的模式，则不打印
        if any(pattern in message for pattern in _DISABLED_LOG_PATTERNS):
            return
            
        logger_func(message)
        _GLOBAL_LOG_CACHE.add(cache_key)
        
        # 如果设置了重置时间，添加重置定时器
        if reset_after > 0:
            # 这里简化处理，实际可能需要使用定时器或线程来处理
            # 当前简单记录时间，在下次调用时检查是否超时
            _LAST_LOG_TIME[cache_key] = time.time() + reset_after


def log_with_interval(logger_func: Callable, message: str, cache_key: str, 
                     interval_seconds: int = 30) -> None:
    """
    基于时间间隔的日志控制，同一缓存键的日志每X秒最多输出一次
    
    Args:
        logger_func: 日志记录函数
        message: 日志消息
        cache_key: 缓存键，用于识别同类日志
        interval_seconds: 最小间隔秒数
    """
    current_time = time.time()
    
    # 如果该缓存键的日志已经打印过，并且距上次过去的时间不超过指定间隔，则不再输出
    if cache_key in _LAST_LOG_TIME and (current_time - _LAST_LOG_TIME[cache_key] < interval_seconds):
        return
    
    # 更新该缓存键的最后日志时间
    _LAST_LOG_TIME[cache_key] = current_time
    logger_func(message)


def disable_log_pattern(pattern: str) -> None:
    """
    添加日志禁用模式，包含此模式的日志将被过滤掉不会输出
    
    Args:
        pattern: 要禁用的日志模式
    """
    _DISABLED_LOG_PATTERNS.add(pattern)


def enable_log_pattern(pattern: str) -> None:
    """
    移除日志禁用模式，使包含此模式的日志可以正常输出
    
    Args:
        pattern: 要启用的日志模式
    """
    if pattern in _DISABLED_LOG_PATTERNS:
        _DISABLED_LOG_PATTERNS.remove(pattern)


def reset_log_cache() -> None:
    """重置全局日志缓存，通常用于测试或重启应用"""
    global _GLOBAL_LOG_CACHE, _LAST_LOG_TIME
    _GLOBAL_LOG_CACHE.clear()
    _LAST_LOG_TIME.clear()


def setup_logger(logger_name: str, log_file: Optional[str] = None, 
                level=logging.INFO, console_output: bool = True) -> logging.Logger:
    """
    全局日志器配置函数，确保每个日志器只被配置一次
    
    Args:
        logger_name: 日志器名称
        log_file: 日志文件路径，如果不提供则只输出到控制台
        level: 日志级别
        console_output: 是否同时输出到控制台
    
    Returns:
        配置好的日志器对象
    """
    global _CONFIGURED_LOGGERS, _HANDLER_PATHS
    
    # 检查是否已经配置过该日志器
    if logger_name in _CONFIGURED_LOGGERS:
        return logging.getLogger(logger_name)
    
    # 添加到已配置日志器集合
    _CONFIGURED_LOGGERS.add(logger_name)
    
    # 获取日志器
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    
    # 清除所有处理器，确保不会有重复
    if logger.handlers:
        logger.handlers.clear()
    
    # 如果指定了日志文件，添加文件处理器
    if log_file:
        # 检查是否已经为该文件路径添加过处理器
        if log_file not in _HANDLER_PATHS:
            # 创建日志目录
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
                
            # 添加文件处理器
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'))
            logger.addHandler(file_handler)
            
            # 记录已添加的处理器路径
            _HANDLER_PATHS.add(log_file)
    
    # 如果需要控制台输出，添加控制台处理器
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'))
        logger.addHandler(console_handler)
    
    return logger


# 默认禁用一些常见的轮询日志
disable_log_pattern("[进度查询]")
disable_log_pattern("创建OpenAI客户端")
disable_log_pattern("[Stream] OpenAI API 调用开始")
disable_log_pattern("[Stream] 模型:")
disable_log_pattern("[Stream] 系统提示")
disable_log_pattern("[Stream] 用户提示")
disable_log_pattern("[Stream] 开始流式请求")
disable_log_pattern("[Stream] 收到终止原因")
disable_log_pattern("OpenAI API 流式调用完成")
disable_log_pattern("完整原始响应")
disable_log_pattern("等待重试")
disable_log_pattern("达到最大重试次数")
disable_log_pattern("流式请求失败")
