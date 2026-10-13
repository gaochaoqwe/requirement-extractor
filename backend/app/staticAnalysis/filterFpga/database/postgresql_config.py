"""
PostgreSQL数据库配置

用于FPGA静态分析过滤工具的PostgreSQL数据库配置
"""
import os

# PostgreSQL配置（从环境变量读取）
POSTGRES_HOST = os.getenv("FPGA_POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("FPGA_POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("FPGA_POSTGRES_DB", "fpga_static_analysis_filter")
POSTGRES_USER = os.getenv("FPGA_POSTGRES_USER", "fpga_analysis")
POSTGRES_PASSWORD = os.getenv("FPGA_POSTGRES_PASSWORD", "123456")

# PostgreSQL管理员配置（用于创建数据库）
POSTGRES_ADMIN_USER = os.getenv("POSTGRES_ADMIN_USER", "postgres")
POSTGRES_ADMIN_PASSWORD = os.getenv("POSTGRES_ADMIN_PASSWORD", "123456")

# 构建数据库URL
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# 数据库配置
DB_CONFIG = {
    "host": POSTGRES_HOST,
    "port": POSTGRES_PORT,
    "database": POSTGRES_DB,
    "user": POSTGRES_USER,
    "password": POSTGRES_PASSWORD,
}

# 管理员数据库配置
ADMIN_DB_CONFIG = {
    "host": POSTGRES_HOST,
    "port": POSTGRES_PORT,
    "database": "postgres",  # 连接到默认数据库
    "user": POSTGRES_ADMIN_USER,
    "password": POSTGRES_ADMIN_PASSWORD,
}

