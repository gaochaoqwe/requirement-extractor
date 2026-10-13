# 回归测试文件上传模块
from fastapi import APIRouter, UploadFile, File
import uuid
import os

from pathlib import Path
# 修正 BASE_DIR 计算 - 需要上溯到 backend 目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
UPLOAD_ROOT = str(BASE_DIR / 'uploads' / 'regression')
import sys
sys.stderr.write(f"[DEBUG] 上传目录: {UPLOAD_ROOT}\n")
os.makedirs(UPLOAD_ROOT, exist_ok=True)

router = APIRouter()

@router.post("/api/regression/upload")
async def upload(file: UploadFile = File(...)):
    # 生成唯一ID
    file_id = str(uuid.uuid4())
    file_name = file.filename
    save_path = os.path.join(UPLOAD_ROOT, f"{file_id}_{file_name}")
    with open(save_path, "wb") as f:
        f.write(await file.read())
    return {"file_id": file_id, "file_name": file_name}
