"""
大纲二次编写工具日志系统
"""
import logging
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
from ..config.config import LOG_CONFIG

_loggers = {}

def setup_session_logger(session_id: str) -> logging.Logger:
    if session_id in _loggers:
        return _loggers[session_id]

    session_log_dir = LOG_CONFIG["base_dir"] / session_id
    session_log_dir.mkdir(parents=True, exist_ok=True)

    log_filename = f"outline_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_file_path = session_log_dir / log_filename

    logger = logging.getLogger(f"outline_session_{session_id}")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=LOG_CONFIG["max_file_size"],
        backupCount=LOG_CONFIG["backup_count"],
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(LOG_CONFIG["format"])
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    _loggers[session_id] = logger
    logger.info(f"会话日志初始化完成 - session_id: {session_id}, 路径: {log_file_path}")
    return logger


def get_session_logger(session_id: str) -> logging.Logger:
    if session_id not in _loggers:
        return setup_session_logger(session_id)
    return _loggers[session_id]
