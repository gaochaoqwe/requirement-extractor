import os
from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...db.models import OptoKnowledgeAsset, OptoKnowledgeNode
from ...schemas.schemas import AssetOut


router = APIRouter()

UPLOAD_BASE_DIR = Path(__file__).resolve().parents[6] / "uploads" / "opto_knowledge"
os.makedirs(UPLOAD_BASE_DIR, exist_ok=True)


@router.post("/asset/upload", response_model=AssetOut)
async def upload_asset(
    node_id: UUID,
    asset_type: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    node = db.query(OptoKnowledgeNode).filter(OptoKnowledgeNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    node_dir = UPLOAD_BASE_DIR / str(node_id)
    os.makedirs(node_dir, exist_ok=True)

    filename = file.filename or "file"
    safe_filename = filename.replace("..", "_").replace("/", "_").replace("\\", "_")
    file_path = node_dir / safe_filename

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    asset = OptoKnowledgeAsset(
        node_id=node_id,
        asset_type=asset_type,
        filename=safe_filename,
        content_type=file.content_type,
        file_path=str(file_path),
        meta_json=None,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    return AssetOut.model_validate(asset)


@router.get("/asset/{asset_id}")
def download_asset(asset_id: UUID, db: Session = Depends(get_db)):
    asset = db.query(OptoKnowledgeAsset).filter(OptoKnowledgeAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if not asset.file_path or not os.path.exists(asset.file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        asset.file_path,
        media_type=asset.content_type or "application/octet-stream",
        filename=asset.filename,
    )
