from fastapi import APIRouter, UploadFile, File, Form
from ..utils.file_utils import save_upload_file
import uuid

router = APIRouter()

@router.post("/api/upload")
async def upload(file: UploadFile = File(...), doc_type: str = Form(...)):
    # 生成唯一ID
    file_id = str(uuid.uuid4())
    file_name = file.filename
    if doc_type not in ("requirementSpec", "taskBook"):
        return {"error": "doc_type必须为requirementSpec或taskBook"}
    save_upload_file(file, file_id, doc_type)
    return {"file_id": file_id, "file_name": file_name}
