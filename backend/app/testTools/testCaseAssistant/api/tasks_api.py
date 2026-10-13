from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import uuid
from pathlib import Path
import zipfile
import shutil
from datetime import datetime

from ..database.database import get_db_session, init_database
from ..models.models import CaseDesignTask, CaseDesignRepo
from ..config.config import REPO_UPLOAD_DIR, REPO_EXTRACT_DIR


router = APIRouter()


class CreateTaskRequest(BaseModel):
    name: str = Field(..., description="任务名称")
    excel_filename: Optional[str] = Field(None, description="导入的Excel文件名")
    product_type: Optional[str] = Field(None, description="产品类别")
    software_type: Optional[str] = Field(None, description="软件类型")


class UpdateTaskContextRequest(BaseModel):
    product_type: Optional[str] = Field(None, description="产品类别")
    software_type: Optional[str] = Field(None, description="软件类型")


class TaskResponse(BaseModel):
    task_id: str
    name: str
    status: str
    excel_filename: Optional[str] = None
    product_type: Optional[str] = None
    software_type: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    repo: Optional[Dict[str, Any]] = None


def _db() -> Session:
    db = get_db_session()
    try:
        yield db
    finally:
        db.close()


def _safe_extract_zip(zip_path: Path, extract_to: Path) -> None:
    extract_to.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for member in zf.infolist():
            member_path = Path(member.filename)
            if member_path.is_absolute() or '..' in member_path.parts:
                raise HTTPException(status_code=400, detail=f"非法zip条目路径: {member.filename}")

            target_path = extract_to / member_path
            target_path_parent = target_path.parent
            target_path_parent.mkdir(parents=True, exist_ok=True)

            if member.is_dir():
                target_path.mkdir(parents=True, exist_ok=True)
                continue

            with zf.open(member, 'r') as src, open(target_path, 'wb') as dst:
                shutil.copyfileobj(src, dst)


def _task_to_response(task: CaseDesignTask, repo: Optional[CaseDesignRepo]) -> Dict[str, Any]:
    return {
        "task_id": task.task_id,
        "name": task.name,
        "status": task.status,
        "excel_filename": task.excel_filename,
        "product_type": getattr(task, "product_type", None),
        "software_type": getattr(task, "software_type", None),
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        "repo": None
        if repo is None
        else {
            "id": repo.id,
            "zip_path": repo.zip_path,
            "extract_path": repo.extract_path,
            "file_count": repo.file_count,
            "total_size": repo.total_size,
            "index_status": repo.index_status,
            "created_at": repo.created_at.isoformat() if repo.created_at else None,
            "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
        },
    }


@router.post("/tasks", response_model=TaskResponse)
def create_task(payload: CreateTaskRequest, db: Session = Depends(_db)):
    init_database()

    task_id = str(uuid.uuid4())
    task = CaseDesignTask(
        task_id=task_id,
        name=payload.name,
        excel_filename=payload.excel_filename,
        status="created",
        product_type=payload.product_type,
        software_type=payload.software_type,
    )
    db.add(task)
    db.commit()

    return _task_to_response(task, None)


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
def update_task_context(task_id: str, payload: UpdateTaskContextRequest, db: Session = Depends(_db)):
    init_database()

    task = db.query(CaseDesignTask).filter(CaseDesignTask.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if payload.product_type is not None:
        task.product_type = payload.product_type
    if payload.software_type is not None:
        task.software_type = payload.software_type

    db.commit()

    repo = (
        db.query(CaseDesignRepo)
        .filter(CaseDesignRepo.task_id == task_id)
        .order_by(CaseDesignRepo.id.desc())
        .first()
    )
    return _task_to_response(task, repo)


@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: str, db: Session = Depends(_db)):
    init_database()

    task = db.query(CaseDesignTask).filter(CaseDesignTask.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    repo = (
        db.query(CaseDesignRepo)
        .filter(CaseDesignRepo.task_id == task_id)
        .order_by(CaseDesignRepo.id.desc())
        .first()
    )

    return _task_to_response(task, repo)


@router.post("/tasks/{task_id}/repo/upload")
def upload_repo(task_id: str, file: UploadFile = File(...), db: Session = Depends(_db)):
    init_database()

    print(f"[test-case-assistant] upload_repo called: task_id={task_id}, filename={getattr(file, 'filename', None)}")

    task = db.query(CaseDesignTask).filter(CaseDesignTask.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    filename = (file.filename or "").lower()
    if not filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="仅支持zip格式")

    task_upload_dir = REPO_UPLOAD_DIR / task_id
    task_upload_dir.mkdir(parents=True, exist_ok=True)

    zip_path = task_upload_dir / f"repo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    with open(zip_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    print(f"[test-case-assistant] zip saved: {zip_path}")

    extract_dir = REPO_EXTRACT_DIR / task_id / datetime.now().strftime('%Y%m%d_%H%M%S')
    _safe_extract_zip(zip_path, extract_dir)

    print(f"[test-case-assistant] zip extracted: {extract_dir}")

    file_count = 0
    total_size = 0
    for p in extract_dir.rglob("*"):
        if p.is_file():
            file_count += 1
            try:
                total_size += p.stat().st_size
            except Exception:
                pass

    repo = CaseDesignRepo(
        task_id=task_id,
        zip_path=str(zip_path),
        extract_path=str(extract_dir),
        file_count=file_count,
        total_size=total_size,
        index_status="not_indexed",
    )
    db.add(repo)

    task.status = "repo_uploaded"

    db.commit()

    return {
        "success": True,
        "task": _task_to_response(task, repo),
        "repo": {
            "zip_path": str(zip_path),
            "extract_path": str(extract_dir),
            "file_count": file_count,
            "total_size": total_size,
        },
    }
