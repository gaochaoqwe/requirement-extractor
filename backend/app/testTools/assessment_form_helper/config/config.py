"""
鉴定测评表单辅助工具配置
"""
import os
from pathlib import Path

# 数据库配置
DATABASE_URL = "sqlite:///./assessment_form_helper.db"

# 文件上传配置
UPLOAD_DIR = Path("uploads/testTools/assessment_form_helper")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 支持的文件类型
ALLOWED_EXTENSIONS = {'.xlsx', '.xls'}

# 最大文件大小 (50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024

# Excel配置
REQUIRED_SHEET_NAME = "需求分析表"
REQUIRED_COLUMNS = {
    "需求子项描述": None,  # 需要生成的列
    "充分性要求": None,    # 需要生成的列
    "通过准则": None,      # 需要生成的列
    "测试项描述": None,    # 输入列
    "测试方法": None,      # 输入列
    "软件需求描述": None,  # 需要被覆盖的列
}

# AI生成配置
AI_GENERATION_CONFIG = {
    "batch_size": 5,  # 每批处理的行数
    "max_retries": 3,  # 最大重试次数
    "timeout": 300,    # 超时时间(秒)
} 

# 日志配置
LOG_CONFIG = {
    "base_dir": Path(__file__).parent.parent / "logs",  # 相对于当前文件的logs目录
    "max_file_size": 10 * 1024 * 1024,  # 10MB
    "backup_count": 5,
    "format": "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
} 