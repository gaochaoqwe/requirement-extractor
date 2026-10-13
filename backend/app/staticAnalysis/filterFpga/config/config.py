"""
静态分析问题过滤工具配置
"""
import os
from pathlib import Path

# ==================== 数据库配置 ====================
# 检测是否使用PostgreSQL（通过环境变量）
# 默认使用PostgreSQL（已完全迁移）
USE_POSTGRESQL = os.getenv("USE_STATIC_POSTGRESQL", "true").lower() in ["true", "1", "yes"]

if USE_POSTGRESQL:
    # PostgreSQL配置（从环境变量读取）
    POSTGRES_HOST = os.getenv("STATIC_POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("STATIC_POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("STATIC_POSTGRES_DB", "static_analysis_filter")
    POSTGRES_USER = os.getenv("STATIC_POSTGRES_USER", "static_analysis")
    POSTGRES_PASSWORD = os.getenv("STATIC_POSTGRES_PASSWORD", "123456")
    
    DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    DATABASE_TYPE = "postgresql"
else:
    # SQLite配置（默认）
    DATABASE_URL = f"sqlite:///{Path(__file__).parent.parent / 'database' / 'static_analysis_filter.db'}"
    DATABASE_TYPE = "sqlite"

print(f"[静态分析过滤工具] 使用数据库类型: {DATABASE_TYPE}")
print(f"[静态分析过滤工具] 数据库URL: {DATABASE_URL.split('@')[0]}...")  # 隐藏密码部分
# ================================================

# 文件上传配置
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 支持的文件类型
ALLOWED_EXTENSIONS = {'.xlsx', '.xls'}

# 最大文件大小 (50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024

# Excel配置 - 静态分析工具输出格式
REQUIRED_SHEET_NAME = "Sheet1"  # 默认sheet名，实际会处理多个sheet
TARGET_SHEET_PATTERN = "GJB_8114"  # 目标sheet名称模式
SKIP_SHEETS = ["项目详情", "你的问题汇总"]  # 跳过的sheet名称
REQUIRED_COLUMNS = {
    "编号": 0,            # A列 (索引0) - 编号
    "缺陷名称": 3,        # D列 (索引3) - 缺陷名称（用于规则匹配）
    "问题文件": 10,       # K列 (索引10) - 文件路径
    "问题行数": 11,       # L列 (索引11) - 行号
    "问题描述": 12,       # M列 (索引12) - 缺陷说明
}

# 问题过滤配置
FILTER_CONFIG = {
    "exclude_keywords": ["建议"],  # 排除包含这些关键字的问题
    "min_name_length": 3,          # 问题名称最小长度
    "include_keywords": [           # 需要包含的关键字（用户可配置）
        "不规范", "不清晰", "不符合", "不充分", "不一致", "混乱", 
        "不对", "缺失", "缺少", "错误", "没有", "不全", "同名",
        "存在未初始化变量", "存在死循环", "存在空语句", 
        "数组边界没有界定", "存在数组越界", "重定义", "不匹配",
        "无法", "未", "没", "数组越界"
    ]
}

# 输出Excel配置 - 根据原始项目的12列格式
OUTPUT_COLUMNS = [
    "问题名称",      # 第1列
    "问题来源",      # 第2列
    "问题复现",      # 第3列
    "问题解释",      # 第4列
    "测试活动",      # 第5列
    "问题类型",      # 第6列
    "问题等级",      # 第7列
    "问题数目",      # 第8列
    "问题名称",      # 第9列 (重复)
    "问题来源",      # 第10列 (重复)
    "问题描述",      # 第11列
    "测评单位意见"   # 第12列
]

# 批处理性能优化配置
BATCH_PROCESSING_CONFIG = {
    "db_insert_batch_size": 1000,     # 数据库插入批次大小
    "processing_batch_size": 500,     # 问题处理批次大小
    "max_concurrent_batches": 2,      # 最大并发批次数
    "progress_report_interval": 100,   # 每处理多少个问题报告一次进度
}

# 日志配置
LOG_CONFIG = {
    "base_dir": Path(__file__).parent.parent / "logs",  # 相对于当前文件的logs目录
    "max_file_size": 10 * 1024 * 1024,  # 10MB
    "backup_count": 5,
    "format": "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
} 

# ==================== 并发控制配置（FPGA专用） ====================
# FPGA增强版AI审查的最大并发会话数（达到该数量时，后续新任务将跳过AI审查，仅提供“未经AI过滤”的问题单）
# 优先读取 FPGA 专用环境变量；若未设置则回退到通用变量，再回退到默认 3
MAX_FPGA_ENHANCED_CONCURRENT_SESSIONS = int(
    os.getenv("STATIC_FPGA_MAX_ENHANCED_CONCURRENT_SESSIONS",
              os.getenv("STATIC_MAX_ENHANCED_CONCURRENT_SESSIONS", "1"))
)