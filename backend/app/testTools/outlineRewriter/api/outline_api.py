"""
大纲二次编写工具 API
"""
import uuid
from pathlib import Path
from typing import Dict, Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import Response
from pydantic import BaseModel

from ..config.config import MODULE_UPLOAD_DIR, ALLOWED_EXTENSIONS, MAX_FILE_SIZE, OFFICECLI_EXE
from ..services.outline_service import OutlineRewriterService
from ..utils.logger import get_session_logger

router = APIRouter()


class ParseResponse(BaseModel):
    success: bool
    session_id: str
    local_docx_path: str
    document_title: str
    total_sections: int
    sections: list


class GenerateRequest(BaseModel):
    session_id: str
    local_docx_path: str
    section_extras: Dict[str, str] = {}


@router.post("/parse", response_model=ParseResponse)
async def parse_outline(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
):
    """上传大纲 docx，解析章节结构，返回给前端展示"""
    sid = session_id or str(uuid.uuid4())
    logger = get_session_logger(sid)

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"仅支持 .docx 文件，当前文件类型: {suffix}")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小超过 50MB 限制")

    save_dir = MODULE_UPLOAD_DIR / sid
    save_dir.mkdir(parents=True, exist_ok=True)
    local_path = save_dir / file.filename
    with open(local_path, "wb") as f:
        f.write(content)

    logger.info(f"文件已保存: {local_path}")

    try:
        service = OutlineRewriterService(sid)
        parse_result = await service.parse_outline(str(local_path))

        if not parse_result.get("success"):
            raise HTTPException(status_code=500, detail=parse_result.get("error", "解析失败"))

        data = parse_result["data"]
        return {
            "success": True,
            "session_id": sid,
            "local_docx_path": str(local_path),
            "document_title": data["documentTitle"],
            "total_sections": data["totalSections"],
            "sections": data["sections"],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"解析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate")
async def generate_outline(payload: GenerateRequest):
    """
    根据章节结构和用户填写的额外信息，调用 AI 生成并填充输出新 docx
    section_extras 的 key 为 paragraphIndex 字符串，value 为用户填写的额外说明
    """
    sid = payload.session_id
    logger = get_session_logger(sid)

    section_extras = {int(k): v for k, v in payload.section_extras.items()}

    try:
        service = OutlineRewriterService(sid)

        parse_result = await service.parse_outline(payload.local_docx_path)
        if not parse_result.get("success"):
            raise HTTPException(status_code=500, detail="重新解析失败")

        data = parse_result["data"]
        sections = data["sections"]
        document_title = data["documentTitle"]

        fill_data = await service.generate_all_sections(sections, section_extras, document_title)
        docx_bytes = await service.fill_docx(payload.local_docx_path, fill_data)

        logger.info(f"大纲生成完成，输出大小: {len(docx_bytes)} bytes")

        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": "attachment; filename=outline_rewritten.docx"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health():
    """检查 OfficeCLI 是否可用"""
    import subprocess
    cli_ok = False
    cli_version = ""
    try:
        r = subprocess.run(
            [str(OFFICECLI_EXE), "--version"],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0:
            cli_ok = True
            cli_version = r.stdout.strip()
    except Exception:
        pass

    return {
        "python_service": "UP",
        "officecli": "UP" if cli_ok else "DOWN",
        "officecli_version": cli_version,
        "officecli_path": str(OFFICECLI_EXE),
    }
