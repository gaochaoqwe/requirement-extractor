"""问题报告单归零意见生成 API。"""
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from ..services.generation_progress import (
    get_progress,
    resolve_session_id,
    sanitize_session_id,
    start_progress,
)
from ..services.issue_report_opinion_service import (
    OPINION_OUTPUT_DIR,
    IssueReportOpinionService,
)

router = APIRouter()

XLSX_MEDIA_TYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


@router.post('/issue-report/generate-opinions')
async def generate_issue_report_opinions(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
):
    """上传包含“问题报告单”工作表的 Excel，生成问题确认意见/归零说明并返回下载地址。

    前端可传入自生成的 session_id，用于在生成过程中轮询 `/issue-report/progress/{session_id}`。
    """
    filename = file.filename or ''
    if not filename.lower().endswith(('.xlsx', '.xlsm')):
        raise HTTPException(status_code=400, detail='只支持 Excel 文件(.xlsx, .xlsm)')

    session_id = resolve_session_id(session_id)
    start_progress(session_id, message='正在接收上传的 Excel 文件…')

    service = IssueReportOpinionService(session_id)

    save_path = OPINION_OUTPUT_DIR / f'{session_id}_source.xlsx'
    try:
        content = await file.read()
        with open(save_path, 'wb') as buffer:
            buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'保存上传文件失败: {e}')

    result = await service.process_file(str(save_path), filename)
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('error') or '处理失败')

    return {
        'success': True,
        'session_id': session_id,
        'sheet_name': result.get('sheet_name'),
        'updated_rows': result.get('updated_rows', 0),
        'skipped_rows': result.get('skipped_rows', 0),
        'errors': result.get('errors', []),
        'download_filename': result.get('download_filename'),
        'download_url': f'/test-tools/test-case-assistant/issue-report/download/{result.get("output_filename")}',
    }


@router.get('/issue-report/progress/{session_id}')
async def get_issue_report_opinion_progress(session_id: str):
    """查询归零意见生成进度（供前端轮询）。

    返回 status: running / done / error / not_found。
    """
    return get_progress(sanitize_session_id(session_id))


@router.get('/issue-report/download/{output_filename}')
async def download_issue_report_opinion(output_filename: str):
    """下载生成后的 Excel 文件。"""
    safe_name = Path(output_filename).name
    file_path = OPINION_OUTPUT_DIR / safe_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail='文件不存在')

    return FileResponse(path=str(file_path), filename=safe_name, media_type=XLSX_MEDIA_TYPE)
