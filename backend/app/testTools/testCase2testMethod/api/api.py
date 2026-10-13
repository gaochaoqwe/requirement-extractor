"""
测试用例反向推导工具API
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Dict, Any
import uuid
import os
from pathlib import Path
import asyncio
import logging

from ..database.database import get_db_session
from ..models.models import TestCaseReverseSession, TestItem
from ..services.service import TestCaseReverseService
from ..config.config import UPLOAD_DIR

router = APIRouter()

# 设置日志
logger = logging.getLogger(__name__)

# 全局服务实例字典
service_instances = {}

@router.post("/upload")
async def upload_and_process_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    processing_mode: str = Form("normal")
) -> Dict[str, Any]:
    """上传测试用例Excel文件并开始处理"""
    try:
        logger.info(f"收到文件上传请求: {file.filename}, 处理模式: {processing_mode}")
        
        # 验证文件类型
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="只支持Excel文件(.xlsx, .xls)")
        
        # 验证处理模式
        if processing_mode not in ["normal", "template"]:
            processing_mode = "normal"
            logger.warning(f"无效的处理模式，使用默认值: normal")
        
        # 生成会话ID
        session_id = str(uuid.uuid4())
        
        # 创建服务实例
        service = TestCaseReverseService(session_id)
        service_instances[session_id] = service
        
        # 保存上传的文件
        upload_dir = UPLOAD_DIR / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / f"{session_id}_{file.filename}"
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"文件保存成功: {file_path}")
        
        # 处理上传的文件
        result = service.process_uploaded_file(str(file_path), file.filename)
        
        if result["success"]:
            # 在后台启动AI处理任务
            background_tasks.add_task(process_session_background, session_id, processing_mode)
            
            logger.info(f"文件上传成功，会话ID: {session_id}, 处理模式: {processing_mode}")
            
            return {
                "success": True,
                "session_id": session_id,
                "message": f"文件上传成功，正在进行反向推导 (模式: {processing_mode})",
                "status": "processing",
                "processing_mode": processing_mode
            }
        else:
            # 清理失败的服务实例
            if session_id in service_instances:
                del service_instances[session_id]
            
            logger.error(f"文件处理失败: {result.get('error')}")
            raise HTTPException(status_code=400, detail=result.get("error", "文件处理失败"))
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"上传文件时出错: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

async def process_session_background(session_id: str, processing_mode: str = "normal"):
    """后台处理会话"""
    try:
        service = service_instances.get(session_id)
        if service:
            logger.info(f"开始后台处理会话: {session_id} (模式: {processing_mode})")
            await service.process_session(session_id, processing_mode)
            logger.info(f"会话处理完成: {session_id}")
        else:
            logger.error(f"未找到会话服务实例: {session_id}")
    except Exception as e:
        logger.error(f"后台处理会话失败: {session_id}, 错误: {str(e)}")

@router.get("/status/{session_id}")
async def get_processing_status(session_id: str) -> Dict[str, Any]:
    """获取处理状态"""
    try:
        logger.info(f"收到状态查询请求 - 会话ID: {session_id}")
        
        # 优先从内存中获取状态
        service = service_instances.get(session_id)
        if service:
            logger.info(f"找到服务实例，会话ID: {session_id}")
            status = service.get_memory_status()
            logger.info(f"内存状态: {status}")
            return status
        else:
            # 从数据库获取状态
            logger.info(f"未找到服务实例，从数据库查询状态: {session_id}")
            temp_service = TestCaseReverseService()
            status = temp_service.get_session_status(session_id)
            logger.info(f"数据库状态: {status}")
            return status
            
    except Exception as e:
        error_msg = f"获取状态时出错: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}

@router.post("/generate_output_file/{session_id}")
async def generate_output_file(session_id: str) -> Dict[str, Any]:
    """生成输出Excel文件"""
    try:
        logger.info(f"收到生成输出文件请求 - 会话ID: {session_id}")
        
        # 获取或创建服务实例
        service = service_instances.get(session_id)
        if not service:
            service = TestCaseReverseService(session_id)
        
        # 生成输出文件
        result = service.generate_output_file(session_id)
        
        if result["success"]:
            logger.info(f"输出文件生成成功: {result['filename']}")
            return result
        else:
            logger.error(f"输出文件生成失败: {result.get('error')}")
            raise HTTPException(status_code=500, detail=result.get("error", "生成输出文件失败"))
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"生成输出文件时出错: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/download/{session_id}")
async def download_result(session_id: str):
    """下载生成的Excel文件"""
    try:
        logger.info(f"收到下载请求 - 会话ID: {session_id}")
        
        # 获取会话信息
        with get_db_session() as db:
            session = db.query(TestCaseReverseSession).filter(
                TestCaseReverseSession.session_id == session_id
            ).first()
            
            if not session:
                raise HTTPException(status_code=404, detail="会话不存在")
            
            if not session.output_filename:
                raise HTTPException(status_code=404, detail="输出文件不存在")
            
            # 构建文件路径
            file_path = UPLOAD_DIR / "outputs" / session.output_filename
            
            if not file_path.exists():
                raise HTTPException(status_code=404, detail="文件不存在")
            
            logger.info(f"开始下载文件: {file_path}")
            
            return FileResponse(
                path=str(file_path),
                filename=session.output_filename,
                media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"下载文件时出错: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "test-case-reverse"} 