from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any
import logging

from ..services.service import TestEnvironmentService

logger = logging.getLogger(__name__)

router = APIRouter()

# 创建服务实例
test_environment_service = TestEnvironmentService()

class DeviceInfoRequest(BaseModel):
    软件名称: str
    检测仪名称: str
    软件运行设备: str
    接口1: str
    接口2: str
    目标模拟器: str = ""  # 可选字段
    主控软件名称: str = ""  # 分系统模式下使用
    主控与被测软件接口类型: str = ""  # 分系统模式下使用

@router.post("/create")
async def create_environment_diagram(device_info: DeviceInfoRequest):
    """创建测试环境图"""
    try:
        logger.info(f"收到创建测试环境图请求: {device_info.软件名称}")
        
        device_dict = device_info.dict()
        session_id = test_environment_service.create_environment_diagram(device_dict)
        
        return {
            "success": True,
            "session_id": session_id,
            "message": "测试环境图创建成功"
        }
        
    except Exception as e:
        logger.error(f"创建测试环境图失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")

@router.get("/status/{session_id}")
async def get_session_status(session_id: str):
    """获取会话状态"""
    try:
        logger.info(f"查询会话状态: {session_id}")
        
        status_info = test_environment_service.get_session_status(session_id)
        
        return {
            "success": True,
            "data": status_info
        }
        
    except Exception as e:
        logger.error(f"获取会话状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")

@router.get("/result/{session_id}")
async def get_diagram_result(session_id: str):
    """获取图表结果"""
    try:
        logger.info(f"获取图表结果: {session_id}")
        
        result = test_environment_service.get_diagram_result(session_id)
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"获取图表结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取结果失败: {str(e)}")

@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "test_environment_diagram"
    } 