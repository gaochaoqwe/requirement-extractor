import os
import logging
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse

from backend.app.databaseManage.dynamicDatabaseManage.db.database import SessionLocal
from backend.app.databaseManage.dynamicDatabaseManage.db.models import ExportTask

from .service import AssetReuseExportService, ensure_output_dir

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/asset-reuse-export")


@router.post("/start")
async def start_asset_reuse_export(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    selected_type: str = Form(...),
    selected_software_type: str = Form(...),
):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="只支持Excel文件格式(.xlsx, .xls)")

    valid_types = ["转塔", "对抗告警", "光雷", "吊舱"]
    if selected_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Unsupported type, valid types: {valid_types}")

    file_content = await file.read()

    db = SessionLocal()
    try:
        task = ExportTask(status="processing", progress=0, message="开始处理...")
        db.add(task)
        db.commit()
        db.refresh(task)
        task_id = task.id
    finally:
        db.close()

    background_tasks.add_task(
        process_export_background,
        task_id,
        file_content,
        selected_type,
        selected_software_type,
    )

    return {"task_id": task_id, "message": "Export started"}


@router.get("/progress/{task_id}")
async def get_progress(task_id: int):
    db = SessionLocal()
    try:
        task = db.query(ExportTask).filter(ExportTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return {
            "status": task.status,
            "progress": task.progress,
            "message": task.message,
            "error": task.error,
            "file_path": task.file_path,
            "filename": task.filename,
        }
    finally:
        db.close()


@router.get("/download/{task_id}")
async def download_result(task_id: int):
    db = SessionLocal()
    try:
        task = db.query(ExportTask).filter(ExportTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        if task.status != "completed":
            raise HTTPException(status_code=400, detail="Export not completed yet")
        if not task.file_path or not os.path.exists(task.file_path):
            raise HTTPException(status_code=404, detail="Export result file not found")

        def gen():
            with open(task.file_path, "rb") as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    yield chunk

        filename = os.path.basename(task.file_path)
        return StreamingResponse(
            gen(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    finally:
        db.close()


def process_export_background(task_id: int, file_content: bytes, selected_type: str, selected_software_type: str):
    def update_progress(progress: int, message: str):
        db_local = SessionLocal()
        try:
            task = db_local.query(ExportTask).filter(ExportTask.id == task_id).first()
            if task:
                task.progress = progress
                task.message = message
                db_local.commit()
        finally:
            db_local.close()

    update_progress(1, "后台任务开始处理...")

    db = SessionLocal()
    try:
        result = AssetReuseExportService.run_export(
            db=db,
            file_content=file_content,
            selected_type=selected_type,
            selected_software_type=selected_software_type,
            progress_callback=update_progress,
        )

        update_progress(95, "正在保存结果文件...")

        import datetime
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"asset_reuse_export_{task_id}_{ts}.xlsx"
        file_path = os.path.join("uploads", "testCaseAssistant", filename)
        ensure_output_dir(file_path)

        with open(file_path, "wb") as f:
            f.write(result)

        task = db.query(ExportTask).filter(ExportTask.id == task_id).first()
        if task:
            task.status = "completed"
            task.progress = 100
            task.message = "导出完成，可以下载"
            task.file_path = file_path
            task.filename = filename
            db.commit()

        update_progress(100, "导出完成！")

    except Exception as e:
        logger.error(f"Asset reuse export task {task_id} failed: {str(e)}", exc_info=True)
        db_local = SessionLocal()
        try:
            task = db_local.query(ExportTask).filter(ExportTask.id == task_id).first()
            if task:
                task.status = "error"
                task.progress = 0
                task.message = f"导出失败: {str(e)}"
                task.error = str(e)
                db_local.commit()
        finally:
            db_local.close()
    finally:
        db.close()
