"""
测试用例总结工具配置
"""
import os
from pathlib import Path

# 数据库配置
DATABASE_URL = f"sqlite:///{Path(__file__).parent.parent / 'document_annotations.db'}"

# 上传目录配置
UPLOAD_DIR = Path("uploads/testTools/document_annotations")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 输出目录配置
OUTPUT_DIR = Path("outputs/testTools/document_annotations")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 支持的文件格式
SUPPORTED_FORMATS = ['.docx']

# 日志配置
LOG_CONFIG = {
    "base_dir": Path(__file__).parent.parent / "logs",
    "max_file_size": 10 * 1024 * 1024,  # 10MB
    "backup_count": 5,
    "format": "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
}

# 问题报告单输出列配置
OUTPUT_COLUMNS = [
    "测试活动", "问题类型", "问题等级", "问题数目", 
    "问题名称", "问题来源", "问题描述", "测评单位意见"
]

# 批注解析配置
ANNOTATION_CONFIG = {
    "位置标识": ["位置:", "位置："],
    "说明标识": ["说明:", "说明："]
} 