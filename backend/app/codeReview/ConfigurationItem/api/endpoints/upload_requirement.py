"""
需求文档上传 API - 接收 .docx 文件并解析为纯文本
"""
import os
import uuid
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path

from ...utils.logger import log_info, log_warning, log_error

router = APIRouter()

# 需求文档临时存储目录
REQ_FOLDER = Path("uploads") / "requirements"
REQ_FOLDER.mkdir(parents=True, exist_ok=True)


def _parse_docx(file_path: str) -> str:
    """
    从 .docx 文件提取纯文本。
    优先使用 python-docx，失败时降级为 zipfile 提取 XML 文本。
    """
    try:
        import docx  # python-docx
        doc = docx.Document(file_path)
        lines = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n".join(lines)
    except ImportError:
        log_warning("[需求上传] python-docx 未安装，尝试 zipfile 降级解析", "upload_requirement")
    except Exception as e:
        log_warning(f"[需求上传] python-docx 解析失败: {e}，尝试降级", "upload_requirement")

    # 降级：直接从 docx 的 XML 中提取文字
    try:
        import zipfile
        import re
        with zipfile.ZipFile(file_path, 'r') as z:
            with z.open('word/document.xml') as f:
                xml = f.read().decode('utf-8', errors='ignore')
        # 去掉所有 XML 标签，保留文字
        text = re.sub(r'<[^>]+>', '', xml)
        # 压缩多余空白
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
    except Exception as e2:
        log_error(f"[需求上传] 降级解析也失败: {e2}", "upload_requirement")
        raise HTTPException(status_code=422, detail=f"无法解析 .docx 文件内容: {e2}")


@router.post("/upload_requirement", summary="上传需求文档(.docx)并解析为文本")
def upload_requirement(file: UploadFile = File(...)):
    """
    接收 .docx 格式的需求文档，解析后返回纯文本内容。
    前端将该文本随 start_analysis 请求一起发送。
    """
    filename = file.filename or ""
    log_info(f"[需求上传] 收到文件: {filename}", "upload_requirement")

    if not filename.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="只支持 .docx 格式的需求文档")

    unique_id = str(uuid.uuid4())
    save_path = REQ_FOLDER / f"{unique_id}.docx"

    try:
        with open(save_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        log_info(f"[需求上传] 文件已保存: {save_path}", "upload_requirement")

        text = _parse_docx(str(save_path))
        log_info(f"[需求上传] 解析完成，文本长度: {len(text)} 字符", "upload_requirement")

        # 解析完即可删除临时文件（文本已在内存中）
        save_path.unlink(missing_ok=True)

        if not text.strip():
            raise HTTPException(status_code=422, detail="需求文档内容为空，请检查文件")

        return {
            "success": True,
            "filename": filename,
            "text": text,
            "char_count": len(text),
        }

    except HTTPException:
        raise
    except Exception as e:
        save_path.unlink(missing_ok=True)
        log_error(f"[需求上传] 处理失败: {e}", "upload_requirement")
        raise HTTPException(status_code=500, detail=f"需求文档处理失败: {e}")

