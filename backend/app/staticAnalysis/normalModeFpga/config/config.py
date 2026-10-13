"""普通模式 FPGA 配置。"""
from pathlib import Path

MAX_FILE_CHARS_FOR_DIRECT_AI = 120_000

BASE_DIR = Path(__file__).resolve().parents[4]  # backend
UPLOAD_FOLDER = BASE_DIR / "uploads" / "staticAnalysis"
ZIP_FOLDER = UPLOAD_FOLDER / "zip"
EXTRACT_FOLDER = UPLOAD_FOLDER / "folders"
ALLOWED_EXTENSIONS = {".zip"}
FPGA_CODE_EXTENSIONS = {".v", ".vhd", ".vhdl"}
ALL_SUPPORTED_EXTENSIONS = FPGA_CODE_EXTENSIONS

ZIP_FOLDER.mkdir(parents=True, exist_ok=True)
EXTRACT_FOLDER.mkdir(parents=True, exist_ok=True)
