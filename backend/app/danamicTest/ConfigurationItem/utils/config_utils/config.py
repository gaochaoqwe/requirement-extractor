
try:
    from ..utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

# config.py
# 大模型的地址和位置
OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODEL = "qwen3:0.6b"
