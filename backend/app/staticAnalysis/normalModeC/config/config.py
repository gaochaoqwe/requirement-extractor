"""普通模式 C/C++ 配置。"""
from pathlib import Path

# 预留：后续可扩展并发数、超时等
MAX_FILE_CHARS_FOR_DIRECT_AI = 120_000

# 上传路径（与历史 staticAnalysis/uploads 对齐）
BASE_DIR = Path(__file__).resolve().parents[4]  # backend
UPLOAD_FOLDER = BASE_DIR / "uploads" / "staticAnalysis"
ZIP_FOLDER = UPLOAD_FOLDER / "zip"
EXTRACT_FOLDER = UPLOAD_FOLDER / "folders"
ALLOWED_EXTENSIONS = {".zip"}
ALLOWED_CODE_EXTENSIONS = {".c", ".cpp", ".h", ".hpp"}
ALL_SUPPORTED_EXTENSIONS = ALLOWED_CODE_EXTENSIONS

ZIP_FOLDER.mkdir(parents=True, exist_ok=True)
EXTRACT_FOLDER.mkdir(parents=True, exist_ok=True)
