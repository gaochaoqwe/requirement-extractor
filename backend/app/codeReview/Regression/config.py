"""
配置模块
"""
import os
from pathlib import Path

# 基础路径 (定位到 backend 目录)
BASE_DIR = Path(__file__).parent.parent.parent.parent  # Regression/config.py -> Regression -> codeReview -> app -> backend

# 数据库配置
DATABASE_URL = f"sqlite:///{Path(__file__).parent / 'db' / 'codeReview.db'}" # 修改为使用db目录下的数据库文件

# 上传文件配置（回归测试专用）
UPLOAD_FOLDER = BASE_DIR / "uploads" / "codeReviewRegression"  # 回归测试上传根目录
ZIP_FOLDER = UPLOAD_FOLDER / "zip"  # ZIP文件存储目录
EXTRACT_FOLDER = UPLOAD_FOLDER / "folders"  # 解压后的代码存储目录
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {".zip"}  # 只允许上传ZIP文件
ALLOWED_CODE_EXTENSIONS = {".c", ".cpp", ".h", ".hpp"}  # 解压后允许分析的代码文件扩展名
ALLOWED_REPORT_EXTENSIONS = {".doc", ".docx", ".pdf", ".txt"}  # 允许上传的影响域分析报告文件扩展名

# FPGA代码文件扩展名
FPGA_CODE_EXTENSIONS = {".v", ".vhd", ".vhdl"}  # FPGA代码文件扩展名

# 所有支持的代码文件扩展名
ALL_SUPPORTED_EXTENSIONS = ALLOWED_CODE_EXTENSIONS | FPGA_CODE_EXTENSIONS

# AI回归测试并发设置
AI_CONCURRENT_REQUESTS = 3  # AI模型并发请求数量，可以根据服务器能力调整

# 文件类型识别
def get_file_type(file_path: str) -> str:
    """根据文件扩展名识别文件类型"""
    ext = Path(file_path).suffix.lower()
    if ext in ALLOWED_CODE_EXTENSIONS:
        return "c_cpp"
    elif ext in FPGA_CODE_EXTENSIONS:
        return "fpga"
    else:
        return "unknown"

# 确保上传目录存在
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
ZIP_FOLDER.mkdir(parents=True, exist_ok=True)
EXTRACT_FOLDER.mkdir(parents=True, exist_ok=True)
