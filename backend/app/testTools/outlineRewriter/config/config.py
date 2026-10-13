"""
大纲二次编写工具配置
"""
from pathlib import Path

# OfficeCLI 可执行文件路径
OFFICECLI_EXE = Path(__file__).parent.parent / "OfficeCLI-main" / "officecli-win-x64.exe"

# 文件上传目录
MODULE_UPLOAD_DIR = Path(__file__).parent.parent / "uploads" / "outline"
MODULE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 支持的文件类型
ALLOWED_EXTENSIONS = {".docx"}

# 最大文件大小 (50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024

# AI 生成配置
AI_GENERATION_CONFIG = {
    "max_retries": 3,
    "timeout": 300,
}

# 日志配置
LOG_CONFIG = {
    "base_dir": Path(__file__).parent.parent / "logs",
    "max_file_size": 10 * 1024 * 1024,
    "backup_count": 5,
    "format": "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
}
