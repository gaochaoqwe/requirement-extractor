"""
回归测试文件上传API端点
处理影响域分析报告、策划文档、目录文档的上传
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
import os
import uuid
import shutil
from pathlib import Path
from typing import Optional

try:
    from ..utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.Regression.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

from ..utils.logging_utils.log_utils import setup_logger

router = APIRouter(tags=["文件上传"])
logger = setup_logger(__name__)

# 创建上传目录
UPLOAD_BASE_DIR = Path("uploads/dynamic/regression")
UPLOAD_BASE_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload-impact")
async def upload_impact_analysis(
    impact_file: UploadFile = File(...),
    session_id: Optional[str] = Form(None)
):
    """
    上传影响域分析报告
    """
    try:
        # 如果没有提供session_id，创建新的
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # 创建会话目录
        session_dir = UPLOAD_BASE_DIR / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存影响域分析报告
        file_path = session_dir / f"impact_{impact_file.filename}"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(impact_file.file, buffer)
        
        logger.info(f"影响域分析报告上传成功: {file_path}")
        
        return {
            "status": "success",
            "message": "影响域分析报告上传成功",
            "session_id": session_id,
            "file_path": str(file_path),
            "filename": impact_file.filename,
            "file_size": impact_file.size
        }
        
    except Exception as e:
        logger.error(f"影响域分析报告上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文档上传失败: {str(e)}")


@router.post("/upload-planning")
async def upload_planning_document(
    planning_file: UploadFile = File(...),
    session_id: str = Form(...)
):
    """
    上传策划文档
    """
    try:
        # 检查会话目录是否存在
        session_dir = UPLOAD_BASE_DIR / session_id
        if not session_dir.exists():
            raise HTTPException(status_code=404, detail="会话不存在，请先上传影响域分析报告")
        
        # 保存策划文档
        file_path = session_dir / f"planning_{planning_file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(planning_file.file, buffer)
        
        logger.info(f"策划文档上传成功: {file_path}")
        
        return {
            "status": "success",
            "message": "策划文档上传成功",
            "session_id": session_id,
            "file_path": str(file_path),
            "filename": planning_file.filename,
            "file_size": planning_file.size
        }
        
    except Exception as e:
        logger.error(f"策划文档上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文档上传失败: {str(e)}")


@router.post("/upload-catalog")
async def upload_catalog_document(
    catalog_file: UploadFile = File(...),
    session_id: str = Form(...)
):
    """
    上传需求目录文档
    """
    logger.info(f"[DEBUG] 收到上传目录文档请求")
    logger.info(f"[DEBUG] session_id: {session_id}")
    logger.info(f"[DEBUG] catalog_file.filename: {catalog_file.filename}")
    logger.info(f"[DEBUG] catalog_file.size: {catalog_file.size}")
    logger.info(f"[DEBUG] UPLOAD_BASE_DIR: {UPLOAD_BASE_DIR}")
    
    try:
        # 检查会话目录是否存在
        session_dir = UPLOAD_BASE_DIR / session_id
        logger.info(f"[DEBUG] session_dir: {session_dir}")
        logger.info(f"[DEBUG] session_dir.exists(): {session_dir.exists()}")
        
        if not session_dir.exists():
            logger.error(f"[DEBUG] 会话目录不存在: {session_dir}")
            raise HTTPException(status_code=404, detail="会话不存在，请先上传影响域分析报告")
        
        # 验证文件类型
        if not catalog_file.filename.lower().endswith('.docx'):
            raise HTTPException(status_code=400, detail="需求目录文档必须是docx格式")
        
        # 保存需求目录文档
        file_path = session_dir / f"catalog_{catalog_file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(catalog_file.file, buffer)
        
        logger.info(f"需求目录文档上传成功: {file_path}")
        
        return {
            "status": "success",
            "success": True,
            "message": "需求目录文档上传成功",
            "session_id": session_id,
            "file_path": str(file_path),
            "filename": catalog_file.filename,
            "file_size": catalog_file.size
        }
        
    except Exception as e:
        logger.error(f"需求目录文档上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"需求目录文档上传失败: {str(e)}")


@router.post("/upload-code")
async def upload_code_for_analysis(
    code_file: UploadFile = File(...),
    task_id: Optional[str] = Form(None)
):
    """
    上传代码文件进行行数统计分析
    
    Args:
        code_file: 上传的代码文件（支持.zip压缩包或单个代码文件）
        task_id: 可选的任务ID，如果不提供会自动生成
        
    Returns:
        包含代码统计信息的响应
    """
    try:
        # 导入代码分析功能
        from ..service.software_config.line_count.code_statistics import analyze_code_statistics
        
        # 生成或使用提供的任务ID
        if not task_id:
            task_id = str(uuid.uuid4())
        
        log_info(f"开始处理代码文件上传: {code_file.filename}, 任务ID: {task_id}", "upload_api")
        
        # 验证文件类型
        allowed_extensions = {'.zip', '.py', '.c', '.cpp', '.cc', '.cxx', '.c++', 
                            '.h', '.hpp', '.hxx', '.h++', '.java', '.js', '.ts', 
                            '.go', '.cs', '.php', '.rb', '.swift', '.kt', '.rs', 
                            '.scala', '.m', '.mm', '.f', '.f90', '.f95'}
        
        file_ext = Path(code_file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的文件类型: {file_ext}。支持的类型: {', '.join(sorted(allowed_extensions))}"
            )
        
        # 创建任务目录
        task_dir = UPLOAD_BASE_DIR / task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存上传的文件
        file_path = task_dir / code_file.filename
        with open(file_path, "wb") as buffer:
            content = await code_file.read()
            buffer.write(content)
        
        log_info(f"文件已保存到: {file_path}", "upload_api")
        
        # 分析代码统计
        analysis_result = analyze_code_statistics(
            file_path=str(file_path),
            task_id=task_id,
            upload_dir=str(UPLOAD_BASE_DIR)
        )
        
        log_info(f"代码分析完成: {analysis_result.get('total_lines', 0)} 行代码", "upload_api")
        
        return {
            "status": "success",
            "message": "代码文件上传并分析成功",
            "task_id": task_id,
            "file_info": {
                "filename": code_file.filename,
                "size": len(content),
                "saved_path": str(file_path)
            },
            "analysis_result": analysis_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"代码文件上传失败: {str(e)}", "upload_api")
        raise HTTPException(status_code=500, detail=f"代码文件上传失败: {str(e)}")


def get_upload_base_dir():
    """获取上传基础目录"""
    return UPLOAD_BASE_DIR
