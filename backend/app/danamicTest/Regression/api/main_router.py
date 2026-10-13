"""
回归测试主路由
整合所有API端点
"""

from fastapi import APIRouter
import sys
from pathlib import Path

# 添加模块路径
current_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(current_dir))

try:
    from ..utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.Regression.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

from ..utils.logging_utils.log_utils import setup_logger

# 导入各个子路由
from .upload_api import router as upload_router
from .form_api import router as form_router
from .dropdown_api import router as dropdown_router
from .ocr_api import router as ocr_router

# 创建主路由
router = APIRouter(tags=["回归测试"])
logger = setup_logger(__name__)

# 包含所有子路由
router.include_router(upload_router, prefix="", tags=["文件上传"])
router.include_router(form_router, prefix="", tags=["表单生成"])
router.include_router(dropdown_router, prefix="", tags=["下拉数据管理"])
router.include_router(ocr_router, prefix="", tags=["OCR功能"])

# 健康检查端点
@router.get("/health")
async def health_check():
    """
    健康检查端点
    """
    try:
        return {
            "status": "success",
            "message": "回归测试服务运行正常",
            "service": "regression_test",
            "version": "1.0.0"
        }
    except Exception as e:
        log_error(f"健康检查失败: {str(e)}", "main_router")
        return {
            "status": "error",
            "message": f"服务异常: {str(e)}",
            "service": "regression_test",
            "version": "1.0.0"
        }


@router.get("/info")
async def get_service_info():
    """
    获取服务信息
    """
    try:
        return {
            "status": "success",
            "data": {
                "service_name": "回归测试服务",
                "service_code": "regression_test",
                "version": "1.0.0",
                "description": "提供回归测试表单生成、文件上传、OCR识别等功能",
                "features": [
                    "影响域分析报告上传",
                    "策划文档上传", 
                    "目录文档上传",
                    "代码文件上传与分析",
                    "回归测试表单生成",
                    "OCR图片文字识别",
                    "下拉数据管理",
                    "任务状态跟踪",
                    "文件下载"
                ],
                "endpoints": {
                    "upload": [
                        "POST /upload-impact - 上传影响域分析报告",
                        "POST /upload-planning - 上传策划文档",
                        "POST /upload-catalog - 上传目录文档",
                        "POST /upload-code - 上传代码文件"
                    ],
                    "form": [
                        "POST /generate-forms - 生成回归测试表单",
                        "GET /task-status/{task_id} - 获取任务状态",
                        "GET /download/{session_id}/{filename} - 下载生成的文件",
                        "GET /status/{session_id} - 获取会话状态"
                    ],
                    "dropdown": [
                        "GET /dropdown-data/* - 获取各种下拉数据",
                        "POST /dropdown-data/* - 添加各种下拉数据"
                    ],
                    "ocr": [
                        "POST /ocr/extract-from-image - 从图片提取数据",
                        "POST /ocr/test-connection - 测试OCR连接",
                        "GET /ocr/status - 获取OCR状态",
                        "POST /ocr/extract-text-only - 纯文字识别"
                    ]
                }
            }
        }
    except Exception as e:
        log_error(f"获取服务信息失败: {str(e)}", "main_router")
        return {
            "status": "error",
            "message": f"获取服务信息失败: {str(e)}"
        }


@router.get("/statistics")
async def get_service_statistics():
    """
    获取服务统计信息
    """
    try:
        from .upload_api import get_upload_base_dir
        
        upload_dir = get_upload_base_dir()
        
        # 统计会话数量
        session_count = 0
        total_files = 0
        
        if upload_dir.exists():
            sessions = [d for d in upload_dir.iterdir() if d.is_dir()]
            session_count = len(sessions)
            
            for session_dir in sessions:
                files = [f for f in session_dir.rglob("*") if f.is_file()]
                total_files += len(files)
        
        return {
            "status": "success",
            "data": {
                "total_sessions": session_count,
                "total_files": total_files,
                "upload_directory": str(upload_dir),
                "service_uptime": "运行中"
            }
        }
        
    except Exception as e:
        log_error(f"获取服务统计信息失败: {str(e)}", "main_router")
        return {
            "status": "error",
            "message": f"获取统计信息失败: {str(e)}"
        }


# 导出主路由
__all__ = ["router"]
