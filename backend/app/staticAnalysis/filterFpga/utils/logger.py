"""
FPGA静态分析过滤工具日志工具
"""
import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

# FPGA专用日志配置
LOG_CONFIG = {
    "base_dir": Path(__file__).parent.parent / "logs",  # E:\code\requirement_extractor\backend\app\staticAnalysis\filterFpga\logs
    "max_file_size": 10 * 1024 * 1024,  # 10MB
    "backup_count": 5,
    "format": "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
}

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
    
    # 如果已经配置过，清理非文件处理器并返回
    if logger.handlers:
        for handler in list(logger.handlers):
            if not isinstance(handler, RotatingFileHandler):
                logger.removeHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
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
    
    # 设置格式
    formatter = logging.Formatter(LOG_CONFIG["format"])
    file_handler.setFormatter(formatter)
    
    # 只添加文件处理器，不添加控制台处理器
    logger.addHandler(file_handler)
    logger.propagate = False

    return logger


def setup_module_logger(name: str, filename: Optional[str] = None) -> logging.Logger:
    """为模块设置日志记录器，输出到通用日志文件"""
    logger = logging.getLogger(name)

    if logger.handlers:
        logger.setLevel(logging.INFO)
        logger.propagate = False
        return logger

    log_dir = LOG_CONFIG["base_dir"] / "system"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_filename = filename or f"{name.replace('.', '_')}.log"
    log_path = log_dir / log_filename

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=LOG_CONFIG["max_file_size"],
        backupCount=LOG_CONFIG["backup_count"],
        encoding='utf-8'
    )
    formatter = logging.Formatter(LOG_CONFIG["format"])
    file_handler.setFormatter(formatter)

    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.propagate = False
    
    return logger


# 初始化常用第三方日志器，避免输出到终端
setup_module_logger("httpx", "httpx.log")

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