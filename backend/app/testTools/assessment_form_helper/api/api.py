"""
鉴定测评表单辅助工具API
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Dict, Any
import uuid
import os
from pathlib import Path
import asyncio
import logging

from ..database.database import get_db_session
from ..models.models import AssessmentSession, RequirementItem
from ..services.service import AssessmentFormService
from ..config.config import UPLOAD_DIR

router = APIRouter()

# 设置日志
logger = logging.getLogger(__name__)

# 全局服务实例缓存
_active_services: Dict[str, AssessmentFormService] = {}

def get_service(session_id: str) -> AssessmentFormService:
    """获取或创建服务实例"""
    if session_id not in _active_services:
        _active_services[session_id] = AssessmentFormService(session_id)
    return _active_services[session_id]

async def save_uploaded_file(file: UploadFile, session_id: str) -> str:
    """
    保存上传的Excel文件
    """
    upload_dir = UPLOAD_DIR / "testTools" / "assessment_form_helper"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = __import__('datetime').datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{session_id}_{timestamp}_{file.filename}"
    file_path = upload_dir / safe_filename
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    return str(file_path)

@router.post("/upload")
async def upload_and_process_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
) -> Dict[str, Any]:
    """
    上传Excel文件并开始处理
    """
    session_id = str(uuid.uuid4())
    
    try:
        # 创建服务实例
        service = AssessmentFormService(session_id)
        logger = service.logger
        
        logger.info(f"开始处理文件上传: {file.filename}")
        
        # 保存上传的文件
        file_path = await save_uploaded_file(file, session_id)
        logger.info(f"文件保存成功: {file_path}")
        
        # 处理上传的文件（解析Excel，保存到数据库）
        result = service.process_uploaded_file(file_path, file.filename)
        
        if result["success"]:
            # 将服务实例加入全局缓存
            _active_services[session_id] = service
            
            logger.info(f"文件上传成功，开始后台处理 - 会话ID: {session_id}")
            
            # 使用asyncio.create_task创建真正的异步任务，不阻塞主线程
            asyncio.create_task(process_session_in_background(session_id))
            
            return {
                "success": True,
                "session_id": session_id,
                "message": "文件上传成功，正在处理中",
                "status": "processing"
            }
        else:
            logger.error(f"文件上传失败: {result.get('error')}")
            return result
            
    except Exception as e:
        error_msg = f"文件上传失败: {str(e)}"
        print(f"❌ [API] {error_msg}")
        return {"success": False, "error": error_msg}

async def process_session_in_background(session_id: str):
    """后台处理会话"""
    try:
        service = get_service(session_id)
        logger = service.logger

        logger.info(f"开始后台处理会话: {session_id}")

        # 异步处理会话
        result = await service.process_session()

        if result["success"]:
            logger.info(f"会话处理完成: {session_id} - {result['message']}")
        else:
            logger.error(f"会话处理失败: {session_id} - {result.get('error')}")

    except Exception as e:
        if session_id in _active_services:
            logger = _active_services[session_id].logger
            logger.error(f"后台处理会话时出错: {str(e)}")

@router.get("/status/{session_id}")
def get_processing_status(session_id: str) -> Dict[str, Any]:
    """
    获取处理状态 - 使用内存变量，快速无阻塞
    """
    try:
        print(f"🔍 [API] 收到状态查询请求 - 会话ID: {session_id}")
        logger.info(f"收到状态查询请求 - 会话ID: {session_id}")
        
        # 获取服务实例
        if session_id not in _active_services:
            print(f"❌ [API] 会话不存在: {session_id}")
            logger.warning(f"会话不存在: {session_id}")
            raise HTTPException(status_code=404, detail="会话不存在")
        
        service = _active_services[session_id]
        print(f"✅ [API] 找到服务实例，会话ID: {session_id}")
        
        # 使用内存状态，快速响应
        status_result = service.get_memory_status()
        print(f"📊 [API] 内存状态: {status_result}")
        logger.info(f"返回状态: {status_result}")
        
        return status_result
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"获取状态失败: {str(e)}"
        print(f"❌ [API] {error_msg}")
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/download/{session_id}")
async def generate_and_download(session_id: str) -> Dict[str, Any]:
    """
    准备下载文件
    """
    try:
        service = get_service(session_id)
        
        # 检查会话状态
        status_result = service.get_session_status_simple()
        if not status_result["success"]:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        if status_result["status"] not in ["completed"]:
            raise HTTPException(status_code=400, detail="处理尚未完成，无法下载文件")
        
        # 检查是否已经有生成的文件
        if status_result.get("output_filename"):
            return {
                "success": True,
                "filename": status_result["output_filename"],
                "message": "文件已准备就绪，可以下载",
                "total_items": status_result.get("total_items", 0),
                "completed_items": status_result.get("completed_items", 0)
            }
        
        # 如果文件还没生成，现在生成
        generate_result = service.generate_output_file()
        
        if not generate_result["success"]:
            raise HTTPException(status_code=500, detail=generate_result.get("error", "生成文件失败"))
        
        # 更新会话记录中的输出文件名
        service._update_session_with_output_file("completed", generate_result["filename"])
        
        return {
            "success": True,
            "filename": generate_result["filename"],
            "message": "文件生成成功，可以下载",
            "total_items": generate_result.get("total_items", 0),
            "updated_items": generate_result.get("updated_items", 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"准备下载文件失败: {str(e)}")

@router.get("/download/{session_id}/{filename}")
async def download_file(session_id: str, filename: str):
    """
    下载生成的文件
    """
    try:
        # 构建文件路径
        file_path = UPLOAD_DIR / "outputs" / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载文件失败: {str(e)}") 