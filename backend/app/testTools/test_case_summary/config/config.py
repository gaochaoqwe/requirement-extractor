"""
测试用例总结工具配置
"""
import os
from pathlib import Path

# 数据库配置
DATABASE_URL = f"sqlite:///{Path(__file__).parent.parent / 'test_case_summary.db'}"

# 文件上传配置
UPLOAD_DIR = Path("uploads/testTools/test_case_summary")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 支持的文件类型
ALLOWED_EXTENSIONS = {'.xlsx', '.xls'}

# 最大文件大小 (50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024

# Excel配置 - 测试用例单格式
REQUIRED_SHEET_NAME = "测试用例单"
REQUIRED_COLUMNS = {
    "轮次": 4,          # E列 (索引4)  - 轮次（第一轮/第二轮）
    "测试项名称": 6,    # G列 (索引6)  - 测试项名称
    "测试用例编号": 9,  # J列 (索引9)  - 测试用例编号
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