#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
软件信息API端点
处理软件名称、版本、标识的提取和管理

功能：
1. 从需求规格说明文档提取软件信息
2. 获取和更新软件信息
3. 管理软件信息相关的会话数据
"""

from fastapi import APIRouter, HTTPException, Form
from pydantic import BaseModel
from typing import Dict, List, Optional, Any

try:
    from ..utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

from ..utils.logging_utils.log_utils import setup_logger
from ..service.software_config.software_info_extract.software_info_service import get_software_info_service

router = APIRouter(tags=["软件信息"])
logger = setup_logger(__name__)


class SoftwareInfo(BaseModel):
    """软件信息数据模型"""
    software_name: str = ""
    software_version: str = ""
    software_id: str = ""


class SoftwareInfoResponse(BaseModel):
    """软件信息响应模型"""
    status: str
    message: str
    session_id: str
    software_info: SoftwareInfo


@router.post("/extract-software-info/{session_id}")
async def extract_software_info(session_id: str):
    """
    从指定会话的需求文档中提取软件信息
    
    Args:
        session_id: 会话ID
        
    Returns:
        软件信息提取结果
    """
    try:
        log_info(f"收到软件信息提取请求，会话ID: {session_id}", "software_info_api")
        
        service = get_software_info_service()
        result = service.extract_software_info_from_session(session_id)
        
        if result['status'] == 'error':
            raise HTTPException(status_code=404, detail=result['message'])
        
        log_info(f"软件信息提取完成: {result['status']}", "software_info_api")
        
        return {
            "status": result['status'],
            "message": result['message'],
            "session_id": session_id,
            "software_info": result['software_info'],
            "extraction_details": result.get('extraction_details', {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"软件信息提取失败: {str(e)}", "software_info_api")
        raise HTTPException(status_code=500, detail=f"提取软件信息失败: {str(e)}")


@router.get("/software-info/{session_id}")
async def get_software_info(session_id: str):
    """
    获取指定会话的软件信息
    
    Args:
        session_id: 会话ID
        
    Returns:
        软件信息
    """
    try:
        log_info(f"获取软件信息，会话ID: {session_id}", "software_info_api")
        
        service = get_software_info_service()
        result = service.get_software_info(session_id)

        # 轮询友好：未提取时返回processing而不是empty
        if result.get("status") == "empty":
            return {
                "status": "processing",
                "message": "软件信息提取中",
                "session_id": session_id,
                "software_info": result.get("software_info", {})
            }

        return {
            "status": result.get('status', 'error'),
            "message": result.get('message', ''),
            "session_id": session_id,
            "software_info": result.get('software_info', {})
        }
        
    except Exception as e:
        log_error(f"获取软件信息失败: {str(e)}", "software_info_api")
        raise HTTPException(status_code=500, detail=f"获取软件信息失败: {str(e)}")


@router.post("/update-software-info/{session_id}")
async def update_software_info(
    session_id: str,
    software_name: str = Form(""),
    software_version: str = Form(""),
    software_id: str = Form("")
):
    """
    更新软件信息
    
    Args:
        session_id: 会话ID
        software_name: 软件名称
        software_version: 软件版本
        software_id: 软件标识
        
    Returns:
        更新结果
    """
    try:
        log_info(f"更新软件信息，会话ID: {session_id}", "software_info_api")
        
        software_info = {
            'software_name': software_name,
            'software_version': software_version,
            'software_id': software_id
        }
        
        service = get_software_info_service()
        result = service.update_software_info(session_id, software_info)
        
        if result['status'] == 'error':
            raise HTTPException(status_code=400, detail=result['message'])
        
        log_info(f"软件信息更新成功", "software_info_api")
        
        return {
            "status": result['status'],
            "message": result['message'],
            "session_id": session_id,
            "software_info": result['software_info']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"更新软件信息失败: {str(e)}", "software_info_api")
        raise HTTPException(status_code=500, detail=f"更新软件信息失败: {str(e)}")


@router.get("/sessions-with-software-info")
async def list_sessions_with_software_info():
    """
    列出所有包含软件信息的会话
    
    Returns:
        会话列表和软件信息
    """
    try:
        log_info("获取所有包含软件信息的会话", "software_info_api")
        
        service = get_software_info_service()
        result = service.list_sessions_with_software_info()
        
        return {
            "status": result['status'],
            "message": result['message'],
            "sessions": result.get('sessions', []),
            "total_count": result.get('total_count', 0)
        }
        
    except Exception as e:
        log_error(f"获取会话列表失败: {str(e)}", "software_info_api")
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {str(e)}")


@router.post("/auto-extract-from-upload/{session_id}")
async def auto_extract_from_upload(session_id: str):
    """
    在文档上传后自动提取软件信息（供内部调用）
    
    Args:
        session_id: 会话ID
        
    Returns:
        自动提取结果
    """
    try:
        log_info(f"自动提取软件信息，会话ID: {session_id}", "software_info_api")
        
        service = get_software_info_service()
        result = service.extract_software_info_from_session(session_id)
        
        # 即使提取失败也不抛出异常，只记录日志
        if result['status'] == 'error':
            log_warning(f"自动提取软件信息失败: {result['message']}", "software_info_api")
        else:
            log_info(f"自动提取软件信息完成: {result['status']}", "software_info_api")
        
        return {
            "auto_extraction": True,
            "status": result['status'],
            "message": result['message'],
            "session_id": session_id,
            "software_info": result['software_info']
        }
        
    except Exception as e:
        log_error(f"自动提取软件信息失败: {str(e)}", "software_info_api")
        # 自动提取失败不应该影响主流程，返回默认结果
        return {
            "auto_extraction": True,
            "status": "error",
            "message": f"自动提取失败: {str(e)}",
            "session_id": session_id,
            "software_info": {
                "software_name": "",
                "software_version": "",
                "software_id": ""
            }
        }


@router.delete("/software-info/{session_id}")
async def delete_software_info(session_id: str):
    """
    删除指定会话的软件信息
    
    Args:
        session_id: 会话ID
        
    Returns:
        删除结果
    """
    try:
        from pathlib import Path
        
        log_info(f"删除软件信息，会话ID: {session_id}", "software_info_api")
        
        service = get_software_info_service()
        session_dir = service.upload_base_dir / session_id
        software_info_file = session_dir / "software_info.json"
        
        if software_info_file.exists():
            software_info_file.unlink()
            log_info(f"软件信息文件已删除: {software_info_file}", "software_info_api")
            message = "软件信息删除成功"
        else:
            message = "软件信息文件不存在"
        
        return {
            "status": "success",
            "message": message,
            "session_id": session_id
        }
        
    except Exception as e:
        log_error(f"删除软件信息失败: {str(e)}", "software_info_api")
        raise HTTPException(status_code=500, detail=f"删除软件信息失败: {str(e)}")


# 响应模型
class ExtractionDetailsModel(BaseModel):
    """提取详情模型"""
    found_table: bool
    table_index: Optional[int] = None
    document_path: str


class SoftwareInfoExtractionResponse(BaseModel):
    """软件信息提取响应模型"""
    status: str
    message: str
    session_id: str
    software_info: SoftwareInfo
    extraction_details: Optional[ExtractionDetailsModel] = None


class SessionsListResponse(BaseModel):
    """会话列表响应模型"""
    status: str
    message: str
    sessions: List[Dict[str, Any]]
    total_count: int 