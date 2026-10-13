
try:
    from ..utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.Regression.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

# config.py
# 大模型的地址和位置
# 注意：远程服务经常不稳定，建议使用本地服务
OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODEL = "qwen3:0.6b"

# 备用远程配置（如果需要使用远程服务，请取消注释）
# OLLAMA_HOST = "https://hpc.613.com/zds"
# OLLAMA_MODEL = "qwen2.5:32b-instruct-q5_1-20k"
