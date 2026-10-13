"""
鉴定测评表单辅助工具日志系统
每个会话都有独立的日志文件夹和日志文件
"""
import logging
import os
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
from ..config.config import LOG_CONFIG

# 全局日志配置
_loggers = {}

def setup_session_logger(session_id: str) -> logging.Logger:
    """
    为指定会话设置独立的日志记录器
    
    Args:
        session_id: 会话ID
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    if session_id in _loggers:
        return _loggers[session_id]
    
    # 创建会话专用的日志目录
    session_log_dir = LOG_CONFIG["base_dir"] / session_id
    session_log_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建日志文件路径
    log_filename = f"assessment_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_file_path = session_log_dir / log_filename
    
    # 创建日志记录器
    logger = logging.getLogger(f"assessment_session_{session_id}")
    logger.setLevel(logging.INFO)
    
    # 清除已有的处理器
    logger.handlers.clear()
    
    # 创建文件处理器
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=LOG_CONFIG["max_file_size"],
        backupCount=LOG_CONFIG["backup_count"],
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 创建格式化器
    formatter = logging.Formatter(LOG_CONFIG["format"])
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # 禁止向父logger传播，避免日志重复打印
    logger.propagate = False
    
    # 缓存日志记录器
    _loggers[session_id] = logger
    
    logger.info(f"会话日志系统初始化完成 - 会话ID: {session_id}")
    logger.info(f"日志文件路径: {log_file_path}")
    
    return logger

def get_session_logger(session_id: str) -> logging.Logger:
    """
    获取指定会话的日志记录器
    
    Args:
        session_id: 会话ID
        
    Returns:
        logging.Logger: 日志记录器
    """
    if session_id not in _loggers:
        return setup_session_logger(session_id)
    return _loggers[session_id]

def cleanup_session_logger(session_id: str):
    """
    清理指定会话的日志记录器
    
    Args:
        session_id: 会话ID
    """
    if session_id in _loggers:
        logger = _loggers[session_id]
        
        # 关闭所有处理器
        for handler in logger.handlers:
            handler.close()
            logger.removeHandler(handler)
        
        # 从缓存中移除
        del _loggers[session_id]

def get_session_log_dir(session_id: str) -> Path:
    """
    获取指定会话的日志目录路径
    
    Args:
        session_id: 会话ID
        
    Returns:
        Path: 日志目录路径
    """
    return LOG_CONFIG["base_dir"] / session_id

def list_session_logs(session_id: str) -> list:
    """
    列出指定会话的所有日志文件
    
    Args:
        session_id: 会话ID
        
    Returns:
        list: 日志文件路径列表
    """
    session_log_dir = get_session_log_dir(session_id)
    if not session_log_dir.exists():
        return []
    
    log_files = []
    for file_path in session_log_dir.glob("*.log*"):
        log_files.append(file_path)
    
    return sorted(log_files, key=lambda x: x.stat().st_mtime, reverse=True) 