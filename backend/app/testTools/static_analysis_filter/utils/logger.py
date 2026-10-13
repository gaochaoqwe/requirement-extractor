"""
静态分析问题过滤工具日志工具
"""
import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

from ..config.config import LOG_CONFIG

def setup_session_logger(session_id: str) -> logging.Logger:
    """
    为特定会话设置日志记录器
    
    Args:
        session_id: 会话ID
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    logger_name = f"static_analysis_session_{session_id}"
    logger = logging.getLogger(logger_name)
    
    # 如果已经配置过，直接返回
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # 创建会话专用的日志目录
    session_log_dir = LOG_CONFIG["base_dir"] / session_id
    session_log_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建日志文件路径
    log_filename = f"static_analysis_{session_id}_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_file_path = session_log_dir / log_filename
    
    # 创建文件处理器（带轮转）
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=LOG_CONFIG["max_file_size"],
        backupCount=LOG_CONFIG["backup_count"],
        encoding='utf-8'
    )
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    
    # 设置格式
    formatter = logging.Formatter(LOG_CONFIG["format"])
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_session_logger(session_id: str) -> logging.Logger:
    """
    获取会话日志记录器
    
    Args:
        session_id: 会话ID
        
    Returns:
        logging.Logger: 日志记录器
    """
    logger_name = f"static_analysis_session_{session_id}"
    return logging.getLogger(logger_name) 