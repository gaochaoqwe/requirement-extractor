"""
测试用例总结工具API
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import uuid
import os
from pathlib import Path
import asyncio
import logging

from ..database.database import get_db_session
from ..models.models import TestCaseSummarySession, TestItem
from ..services.service import TestCaseSummaryService
from ..config.config import UPLOAD_DIR
from app.auth.db.database import UserModel
from app.auth.routes import verify_token


router = APIRouter()
def _get_tester_name(request: Request) -> str:
    """从 session 或 Bearer token 中获取当前用户名"""
    try:
        user_id = request.session.get("user_id")
        if user_id:
            user = UserModel.get_user_by_id(user_id)
            if user:
                return str(user.get("display_name") or user.get("username") or "").strip()
    except Exception:
        pass
    try:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
            payload = verify_token(token)
            if payload:
                return str(payload.get("display_name") or payload.get("username") or payload.get("sub") or "").strip()
    except Exception:
        pass
    return ""

# 设置日志
logger = logging.getLogger(__name__)

# 全局服务实例缓存
_active_services: Dict[str, TestCaseSummaryService] = {}

def get_service(session_id: str) -> TestCaseSummaryService:
    """获取或创建服务实例"""
    if session_id not in _active_services:
        _active_services[session_id] = TestCaseSummaryService(session_id)
    return _active_services[session_id]

async def save_uploaded_file(file: UploadFile, session_id: str) -> str:
    """
    保存上传的Excel文件
    """
    upload_dir = UPLOAD_DIR / "testTools" / "test_case_summary"
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
    request: Request,
    file: UploadFile = File(...)
) -> Dict[str, Any]:
    """
    上传测试用例Excel文件并开始处理
    """
    session_id = str(uuid.uuid4())
    
    try:
        # 创建服务实例
        service = TestCaseSummaryService(session_id)
        logger = service.logger
        
        logger.info(f"开始处理文件上传: {file.filename}")
        
        # 保存上传的文件
        file_path = await save_uploaded_file(file, session_id)
        logger.info(f"文件保存成功: {file_path}")
        
        # 处理上传的文件（解析Excel，保存到数据库）
        tester_name = _get_tester_name(request)
        result = service.process_uploaded_file(file_path, file.filename, tester_name=tester_name)
        
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
        
        if session_id not in _active_services:
            print(f"❌ [API] 会话不存在: {session_id}")
            logger.warning(f"会话不存在: {session_id}")
            raise HTTPException(status_code=404, detail="会话不存在")
        
        service = _active_services[session_id]
        print(f"✅ [API] 找到服务实例，会话ID: {session_id}")
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

@router.get("/failed-items/{session_id}")
def get_failed_items(session_id: str) -> Dict[str, Any]:
    """获取失败测试项详情"""
    try:
        service = get_service(session_id)
        return service.get_failed_items()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取失败测试项详情失败: {str(e)}")

@router.post("/retry/{session_id}/{item_id}")
async def retry_single_item(session_id: str, item_id: int) -> Dict[str, Any]:
    """手动重试单个测试项"""
    try:
        service = get_service(session_id)
        return await service.retry_single_item(item_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"手动重试测试项失败: {str(e)}")

@router.post("/download/{session_id}")
async def generate_and_download(session_id: str) -> Dict[str, Any]:
    """
    准备下载文件
    """
    try:
        service = get_service(session_id)
        
        # 检查是否已经有生成的文件
        if service.output_filename:
            return {
                "success": True,
                "filename": service.output_filename,
                "message": "文件已准备就绪，可以下载"
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
            "message": "文件生成成功，可以下载"
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


@router.get("/admin/tasks")
def get_admin_tasks(limit: int = 500) -> Dict[str, Any]:
    """管理员统计：获取所有测试用例总结会话记录"""
    try:
        from sqlalchemy import func as sqlfunc
        db = get_db_session()
        try:
            sessions = (
                db.query(TestCaseSummarySession)
                .order_by(TestCaseSummarySession.id.desc())
                .limit(limit)
                .all()
            )

            # 统计每个 session 的测试项数（取 total_test_items 字段即可）
            tasks = []
            for sess in sessions:
                tasks.append({
                    "id": sess.id,
                    "session_id": sess.session_id,
                    "original_filename": sess.original_filename,
                    "status": sess.status,
                    "total_test_items": sess.total_test_items or 0,
                    "tester_name": sess.tester_name or "",
                    "created_at": sess.created_at.isoformat() if sess.created_at else None,
                    "updated_at": sess.updated_at.isoformat() if sess.updated_at else None,
                })

            return {"success": True, "tasks": tasks, "total": len(tasks)}
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计数据失败: {str(e)}")

@router.get("/health")
def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "test_case_summary"} 