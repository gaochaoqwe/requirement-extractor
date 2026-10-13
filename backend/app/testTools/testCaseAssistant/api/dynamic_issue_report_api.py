"""动态测试问题单生成 API。"""
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from ..services.dynamic_issue_report_service import (
    OUTPUT_DIR,
    DynamicIssueReportService,
)

router = APIRouter()

XLSX_MEDIA_TYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


@router.post('/dynamic-issue-report/generate')
async def generate_dynamic_issue_report(file: UploadFile = File(...)):
    """上传包含“测试用例单”工作表的 Excel，按测试项为不通过用例生成问题单并返回下载地址。"""
    filename = file.filename or ''
    if not filename.lower().endswith(('.xlsx', '.xlsm')):
        raise HTTPException(status_code=400, detail='只支持 Excel 文件(.xlsx, .xlsm)')

    session_id = str(uuid.uuid4())
    service = DynamicIssueReportService(session_id)

    save_path = OUTPUT_DIR / f'{session_id}_source.xlsx'
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
        'test_item_count': result.get('test_item_count', 0),
        'issue_count': result.get('issue_count', 0),
        'errors': result.get('errors', []),
        'download_filename': result.get('download_filename'),
        'download_url': f'/test-tools/test-case-assistant/dynamic-issue-report/download/{result.get("output_filename")}',
    }


@router.get('/dynamic-issue-report/download/{output_filename}')
async def download_dynamic_issue_report(output_filename: str):
    """下载生成后的问题单 Excel 文件。"""
    safe_name = Path(output_filename).name
    file_path = OUTPUT_DIR / safe_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail='文件不存在')

    return FileResponse(path=str(file_path), filename=safe_name, media_type=XLSX_MEDIA_TYPE)
