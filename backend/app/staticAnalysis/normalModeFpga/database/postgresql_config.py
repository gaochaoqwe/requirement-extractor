"""
普通模式 FPGA PostgreSQL 数据库配置

使用独立的 fpga_static_analysis_filter 数据库（与工具模式FPGA共用数据库实例）
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# 加载 .env 文件
current_file = Path(__file__).resolve()
backend_dir = current_file.parent.parent.parent.parent.parent
env_path = backend_dir / '.env'
if env_path.exists():
    load_dotenv(env_path)

# FPGA 专用数据库配置（与工具模式FPGA共用数据库）
POSTGRES_HOST = os.getenv("FPGA_POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("FPGA_POSTGRES_PORT", "5432")
POSTGRES_USER = os.getenv("FPGA_POSTGRES_USER", "fpga_analysis")
POSTGRES_PASSWORD = os.getenv("FPGA_POSTGRES_PASSWORD", "123456")
POSTGRES_DB = os.getenv("FPGA_POSTGRES_DB", "fpga_static_analysis_filter")

# 构建数据库URL
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

print(f"[normalModeFpga PostgreSQL] 数据库: {POSTGRES_DB} @ {POSTGRES_HOST}:{POSTGRES_PORT}")
