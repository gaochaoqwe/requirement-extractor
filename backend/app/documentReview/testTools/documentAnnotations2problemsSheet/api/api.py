"""
测试用例总结工具API
"""
import os
import sys
import logging
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 使用相对导入
from ..config.config import UPLOAD_DIR, SUPPORTED_FORMATS
from ..services.service import DocumentAnnotationService

logger = logging.getLogger(__name__)
router = APIRouter()

# 创建服务实例
service = DocumentAnnotationService()

@router.post("/upload")
async def upload_and_process_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """上传并处理文档文件"""
    try:
        # 验证文件格式
        if not any(file.filename.lower().endswith(fmt) for fmt in SUPPORTED_FORMATS):
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的文件格式，仅支持: {', '.join(SUPPORTED_FORMATS)}"
            )
        
        # 确保上传目录存在
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        
        # 保存上传的文件
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"文件上传成功: {file.filename}")
        
        # 处理文件（异步调用服务）
        success, result = await service.process_uploaded_file(str(file_path), file.filename)
        
        if success:
            return {
                "success": True,
                "message": "文件上传成功，开始处理",
                "session_id": result
            }
        else:
            # 删除上传的文件
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(status_code=400, detail=result)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传文件时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@router.get("/status/{session_id}")
async def get_processing_status(session_id: str):
    """获取处理状态"""
    try:
        result = service.get_session_status(session_id)
        return result
    except Exception as e:
        logger.error(f"获取状态时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")

@router.post("/generate/{session_id}")
async def generate_output_file(session_id: str):
    """生成输出文件"""
    try:
        success, result = service.generate_output_file(session_id)
        
        if success:
            return {
                "success": True,
                "message": "文件生成成功",
                "file_path": result
            }
        else:
            raise HTTPException(status_code=400, detail=result)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成文件时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成文件失败: {str(e)}")

@router.get("/download/{session_id}")
async def download_file(session_id: str):
    """下载结果文件"""
    try:
        success, file_path = service.generate_output_file(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=file_path)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        filename = f"问题报告单_{session_id}.xlsx"
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载文件时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")

@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "document_annotations_to_problems"} 