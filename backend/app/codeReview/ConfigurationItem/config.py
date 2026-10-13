"""
配置模块

注意：此模块不再包含数据库配置，数据库配置已迁移到PostgreSQL


"""
import os
from pathlib import Path

# 基础路径
BASE_DIR = Path(__file__).parent.parent.parent  # 修改为backend目录

# 数据库配置已迁移到 config_database.py 和 db/database*.py
# 不再使用 SQLite

# 上传文件配置
UPLOAD_FOLDER = BASE_DIR / "uploads" / "codeReview" # 修改为codeReview专用上传目录
ZIP_FOLDER = UPLOAD_FOLDER / "zip"  # ZIP文件存储目录
EXTRACT_FOLDER = UPLOAD_FOLDER / "folders"  # 解压后的代码存储目录
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
MAX_ZIP_SIZE_MB = 15  # 压缩包大小警告阈值（MB），超过此大小会提示用户清理非源码文件
ALLOWED_EXTENSIONS = {".zip"}  # 只允许上传ZIP文件
ALLOWED_CODE_EXTENSIONS = {".c", ".cpp", ".h", ".hpp"}  # 解压后允许分析的代码文件扩展名

# FPGA代码文件扩展名
FPGA_CODE_EXTENSIONS = {".v", ".vhd", ".vhdl"}  # FPGA代码文件扩展名

# 所有支持的代码文件扩展名
ALL_SUPPORTED_EXTENSIONS = ALLOWED_CODE_EXTENSIONS | FPGA_CODE_EXTENSIONS

# AI代码审查并发设置
# 建议值：
# - 本地Ollama: 1-2 (受GPU显存限制)
# - 云服务API: 4-8 (ModelScope/SiliconFlow/Qwen等)
# - OpenAI: 8-16 (根据限流和预算)
AI_CONCURRENT_REQUESTS = 1  # 函数级别审查AI模型并发请求数量，可以根据服务器能力调整

# 函数审查任务级并发限制（最大同时执行/排队的函数审查任务数）
MAX_FUNCTION_REVIEW_CONCURRENT_TASKS = 3

# 业务功能级别审查并发设置
BUSINESS_CONCURRENT_REQUESTS = 1  # 业务功能级别审查并发请求数量，独立于函数级别审查

# 功能点审查并发设置
FEATURE_CONCURRENT_REQUESTS = 1  # 功能点审查并发请求数量，每个功能点都使用Agent独立探索

# Agent审查模式开关
ENABLE_FUNCTION_REVIEW_AGENT = os.getenv("ENABLE_FUNCTION_REVIEW_AGENT", "true").lower() == "true"
# 可以通过环境变量启用：export ENABLE_FUNCTION_REVIEW_AGENT=true
# 默认启用Agent模式，可通过环境变量 ENABLE_FUNCTION_REVIEW_AGENT=false 禁用

# 管理员取消任务配置
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "123456")  # 管理员密码，用于取消任务等敏感操作
# 可以通过环境变量设置：export ADMIN_PASSWORD=your_password

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
