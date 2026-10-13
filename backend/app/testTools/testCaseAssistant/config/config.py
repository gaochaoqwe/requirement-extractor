"""
测试用例反向推导工具配置
"""
import os
from pathlib import Path

# 数据库配置
DATABASE_URL = f"sqlite:///{Path(__file__).parent.parent / 'case_design.db'}"

# 文件上传配置
UPLOAD_DIR = Path("uploads/testTools/test_case_reverse")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 代码库（zip）上传与解压目录：按 task_id 隔离
MODULE_UPLOAD_DIR = Path(__file__).parent.parent / 'uploads'
MODULE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

REPO_UPLOAD_DIR = MODULE_UPLOAD_DIR / 'repos_zip'
REPO_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

REPO_EXTRACT_DIR = MODULE_UPLOAD_DIR / 'repos_extract'
REPO_EXTRACT_DIR.mkdir(parents=True, exist_ok=True)

# 支持的文件类型
ALLOWED_EXTENSIONS = {'.xlsx', '.xls'}

# 最大文件大小 (50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024

# Excel配置 - 测试用例单格式
REQUIRED_SHEET_NAME = "测试用例单"
REQUIRED_COLUMNS = {
    "测试项名称": 6,    # G列 (索引6) - 测试项名称
    "输入条件": 15,     # P列 (索引15) - 输入条件  
    "测试结果": 25,     # Z列 (索引25) - 测试结果
}

# AI生成配置
AI_GENERATION_CONFIG = {
    "batch_size": 3,   # 每批处理的测试项数
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