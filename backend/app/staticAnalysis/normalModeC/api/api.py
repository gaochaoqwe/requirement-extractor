"""
普通模式 C/C++ 静态分析 API
上传 / 进度 / 下载 / start / code-view
"""
import os
import shutil
import uuid
import zipfile
from io import BytesIO
from typing import List, Literal, Optional

import openpyxl
from fastapi import APIRouter, BackgroundTasks, Body, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from openpyxl.styles import Alignment
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.staticAnalysis.normalModeC.config.config import (
    ALL_SUPPORTED_EXTENSIONS,
    ALLOWED_EXTENSIONS,
    EXTRACT_FOLDER,
    ZIP_FOLDER,
)
from app.staticAnalysis.normalModeC.database import (
    FileRepository,
    ProblemRepository,
    TaskRepository,
    get_db,
    get_scoped_session,
)
from app.staticAnalysis.normalModeC.services.code_view import build_normal_mode_code_view_data
from app.staticAnalysis.normalModeC.services.progress import build_progress_payload
from app.staticAnalysis.normalModeC.services.runner import NormalModeCRunner
from app.staticAnalysis.normalModeC.config.default_rules_config import (
    verify_admin_password as verify_c_password,
    save_default_rules_config as save_c_config,
    load_default_rules_config as load_c_config,
)
from app.staticAnalysis.normalModeC.utils.context import (
    get_normal_mode_c_context,
    set_normal_mode_c_context,
)

router = APIRouter()

EXCEL_COLUMNS = [
    "文件名称",
    "源代码",
    "违反规则",
    "问题等级",
    "问题名称",
    "问题来源",
    "问题描述",
    "修改意见",
]


class StartNormalModeCRequest(BaseModel):
    file_id: int
    selected_rules: List[str] = Field(default_factory=list)
    language_mode: Optional[Literal["c"]] = "c"


@router.get("/health", summary="普通模式C健康检查")
def health():
    return {"status": "ok", "domain": "normalModeC"}


@router.post("/upload", summary="上传 C/C++ 代码 ZIP")
def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    filename = file.filename or ""
    ext = os.path.splitext(filename)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"只允许上传ZIP格式文件，当前文件格式: {ext}")

    unique_id = str(uuid.uuid4())
    zip_save_path = os.path.join(ZIP_FOLDER, f"{unique_id}{ext}")
    extract_path = os.path.join(EXTRACT_FOLDER, unique_id)

    try:
        os.makedirs(os.path.dirname(zip_save_path), exist_ok=True)
        with open(zip_save_path, "wb") as f:
            f.write(file.file.read())

        os.makedirs(extract_path, exist_ok=True)
        with zipfile.ZipFile(zip_save_path, "r") as zip_ref:
            zip_ref.extractall(extract_path)

        valid_files = []
        for root, _, files in os.walk(extract_path):
            for name in files:
                if os.path.splitext(name)[-1].lower() in ALL_SUPPORTED_EXTENSIONS:
                    valid_files.append(os.path.join(root, name))

        if not valid_files:
            shutil.rmtree(extract_path, ignore_errors=True)
            os.remove(zip_save_path)
            raise HTTPException(status_code=400, detail="ZIP文件中未找到有效的C/C++源代码文件")

        db_file = FileRepository(db).create_file({
            "file_name": filename,
            "file_path": zip_save_path,
            "extract_path": extract_path,
            "status": "uploaded",
            "file_count": len(valid_files),
        })
        return {
            "file_id": db_file.id,
            "file_name": filename,
            "file_count": len(valid_files),
        }
    except HTTPException:
        raise
    except zipfile.BadZipFile:
        if os.path.exists(zip_save_path):
            os.remove(zip_save_path)
        if os.path.exists(extract_path):
            shutil.rmtree(extract_path, ignore_errors=True)
        raise HTTPException(status_code=400, detail="无效的ZIP文件")
    except Exception as e:
        if os.path.exists(zip_save_path):
            os.remove(zip_save_path)
        if os.path.exists(extract_path):
            shutil.rmtree(extract_path, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"文件处理错误: {e}")


@router.get("/task_progress/{task_id}", summary="查询普通模式C任务进度")
def get_task_progress(task_id: int, db: Session = Depends(get_db)):
    db_task = TaskRepository(db).get_task(task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    try:
        return build_progress_payload(db, task_id, mode="c")
    except Exception:
        return {"task_id": db_task.id, "status": db_task.status, "progress": db_task.progress}


@router.get("/download_result/{task_id}", summary="下载普通模式C分析结果")
def download_result(task_id: int, db: Session = Depends(get_db)):
    db_task = TaskRepository(db).get_task(task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    problems = ProblemRepository(db).get_problems_by_task(task_id)
    if not problems:
        raise HTTPException(status_code=404, detail="No problems found for this task")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "AnalysisResult"
    ws.append(EXCEL_COLUMNS)
    for item in problems:
        from app.staticAnalysis.normalModeC.services.code_view import _build_source_snippet
        _raw_src = str(item.get("source_code") or "")
        _loc_str = str(item.get("issue_location") or "")
        try:
            import re as _re
            _m = _re.search(r"\d+", _loc_str)
            _line_no = int(_m.group(0)) if _m else 0
        except Exception:
            _line_no = 0
        _snippet = _build_source_snippet(_raw_src, _line_no) if _raw_src and _line_no else ""
        _src_part = f"\n源代码为：\n{_snippet}" if _snippet else ""
        req  = str(item.get('description_requirement', ''))
        iss  = str(item.get('description_issue', ''))
        loc  = str(item.get('description_location', ''))
        imp  = str(item.get('description_impact', ''))
        description = (
            f"需求描述：{req}。\n"
            f"问题描述：{iss}。\n"
            f"问题定位：{loc}{_src_part}\n"
            f"影响分析：{imp}"
        ).replace("。。", "。")
        _issue_name = str(item.get("issue_name") or "该问题")
        _suggestion = f"请针对{_issue_name}对代码进行修改，保证代码实现正确。"
        ws.append([
            item.get("file_name", ""),
            item.get("source_code", ""),
            item.get("violation_rules", ""),
            item.get("issue_level", ""),
            item.get("issue_name", ""),
            item.get("issue_location", ""),
            description,
            _suggestion,
        ])

    wrap_alignment = Alignment(wrapText=True, vertical="top")
    for column_cells in ws.columns:
        max_length = 0
        for cell in column_cells:
            cell.alignment = wrap_alignment
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
        ws.column_dimensions[column_cells[0].column_letter].width = min(max(max_length + 2, 20), 60)

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    filename = f"normal_mode_c_result_task_{task_id}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/code-view/{task_id}", summary="普通模式C代码视图数据")
def get_normal_mode_c_code_view(
    task_id: int,
    rule_type: str = Query("mixed", description="规则类型: gjb / cwe / mixed"),
    db: Session = Depends(get_db),
):
    try:
        data = build_normal_mode_code_view_data(
            db=db,
            task_id=task_id,
            domain="c",
            rule_type=None if rule_type in ("mixed", "all", "") else rule_type,
        )
        return {"success": True, "data": data, "message": "普通模式C代码视图数据获取成功"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取代码视图失败: {e}")


@router.post("/start", summary="启动普通模式 C/C++ 静态分析")
def start_normal_mode_c(
    req: StartNormalModeCRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    if not req.selected_rules:
        raise HTTPException(status_code=400, detail="请至少勾选一条规则")

    file_repo = FileRepository(db)
    db_file = file_repo.get_file(req.file_id)
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    if not db_file.extract_path:
        raise HTTPException(status_code=400, detail="文件尚未解压完成")

    task_repo = TaskRepository(db)
    db_task = task_repo.create_task({
        "task_name": f"普通模式C静态分析-{db_file.file_name}",
        "task_description": f"按勾选规则审查文件 {db_file.file_name}",
        "status": "pending",
        "progress": 0,
        "code_file_id": req.file_id,
    })

    selected_rules = [str(code).strip() for code in req.selected_rules if str(code).strip()]
    set_normal_mode_c_context(db_task.id, {
        "language_mode": "c",
        "domain": "normalModeC",
        "code_file_id": db_file.id,
        "extract_path": db_file.extract_path,
        "file_name": db_file.file_name,
        "selected_rules": selected_rules,
    })

    file_repo.update_file_status(db_file.id, "processing", task_id=db_task.id)
    db.commit()

    def background_task(file_id: int, task_id: int, extract_path: str, rules: List[str]):
        session = get_scoped_session()
        try:
            NormalModeCRunner(session).run(
                task_id=task_id,
                file_id=file_id,
                extract_path=extract_path,
                selected_rules=rules,
            )
        except Exception as e:
            import sys
            sys.stderr.write(f"普通模式C后台任务出错: {e}\n")
            session.rollback()
            TaskRepository(session).update_task_status(task_id, "failed", message=f"任务执行出错: {e}")
            session.commit()
        finally:
            ctx = get_normal_mode_c_context(task_id) or {}
            set_normal_mode_c_context(task_id, {
                "language_mode": "c",
                "domain": "normalModeC",
                "code_file_id": file_id,
                "selected_rules": ctx.get("selected_rules") or rules,
            })
            session.close()

    background_tasks.add_task(
        background_task,
        db_file.id,
        db_task.id,
        db_file.extract_path,
        selected_rules,
    )
    return {"task_id": db_task.id, "status": db_task.status, "domain": "normalModeC"}


@router.post("/rules/config/save", summary="保存普通模式C默认规则配置")
def save_rules_config(payload: dict = Body(...)):
    selected_rules = payload.get("selected_rules", [])
    try:
        from app.staticAnalysis.filter.config.default_rules_config import save_selected_rules_to_database
        gjb_rules = [r for r in selected_rules if not (r.startswith('S_') or r.upper().startswith('CWE'))]
        cwe_rules = [r for r in selected_rules if r.startswith('S_') or r.upper().startswith('CWE')]
        success = save_selected_rules_to_database(gjb_rules, cwe_rules)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存配置失败: {e}")
    if not success:
        raise HTTPException(status_code=500, detail="保存配置失败")
    return {"success": True, "message": "默认规则配置已保存", "rules_count": len(selected_rules)}


@router.get("/rules/config/load", summary="加载普通模式C默认规则配置")
def load_rules_config():
    config = load_c_config()
    return {"success": True, **config}
