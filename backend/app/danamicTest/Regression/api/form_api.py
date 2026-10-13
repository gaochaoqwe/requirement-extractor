"""
回归测试表单生成API端点
处理回归测试表单的生成和任务管理
"""

from fastapi import APIRouter, HTTPException, Form, BackgroundTasks
from fastapi.responses import FileResponse
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
from ..service.task_runner import run_regression_test_task, get_task_status, clear_all_tasks, generate_task_id
from .upload_api import get_upload_base_dir

router = APIRouter(tags=["表单生成"])
logger = setup_logger(__name__)

# 在模块加载时清理旧的任务状态
clear_all_tasks()

# 获取上传目录
UPLOAD_BASE_DIR = get_upload_base_dir()


@router.post("/generate-forms")
async def generate_regression_forms(
    background_tasks: BackgroundTasks,
    session_id: str = Form(...),
    test_manager: str = Form(...),
    test_personnel: str = Form(...),
    developer: str = Form(...),
    software_name: str = Form(...),
    software_version: str = Form(...),
    software_id: str = Form(...),
    domain: str = Form(...),
    detector_flag: str = Form("有检测仪"),
    ai_analysis: bool = Form(True),
    deep_analysis: bool = Form(True),
    has_planning: bool = Form(False),
    # 可选信息字段
    aircraft_model: str = Form(""),
    project_director: str = Form(""),
    development_department: str = Form(""),
    chief_designer: str = Form(""),
    # 代码行数统计
    code_lines: int = Form(None)
):
    """
    生成回归测试表单（异步任务）
    """
    try:
        # 检查会话目录是否存在
        session_dir = UPLOAD_BASE_DIR / session_id
        if not session_dir.exists():
            raise HTTPException(status_code=404, detail="会话不存在，请先上传文档")
        
        # 查找已上传的影响域分析报告
        impact_files = list(session_dir.glob("impact_*"))
        if not impact_files:
            raise HTTPException(status_code=400, detail="影响域分析报告未上传")
        
        # 创建输出目录
        output_dir = session_dir / "output"
        output_dir.mkdir(exist_ok=True)
        
        # 准备基本信息
        basic_info = {
            "test_manager": test_manager,
            "test_personnel": test_personnel,
            "developer": developer,
            "software_name": software_name,
            "software_version": software_version,
            "software_id": software_id,
            "domain": domain,
            "detector_flag": detector_flag,
            # 可选信息
            "aircraft_model": aircraft_model,
            "project_director": project_director,
            "development_department": development_department,
            "chief_designer": chief_designer,
            # 代码统计信息
            "code_lines": code_lines
        }
        
        # 生成任务ID
        task_id = generate_task_id()
        
        # 启动后台任务
        background_tasks.add_task(
            run_regression_test_task,
            session_id=session_id,
            basic_info=basic_info,
            ai_analysis=ai_analysis,
            deep_analysis=deep_analysis,
            task_id=task_id
        )
        
        return {
            "status": "success",
            "message": "任务已启动，正在生成回归测试表单",
            "task_id": task_id,
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"启动回归测试表单生成任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"任务启动失败: {str(e)}")


@router.get("/task-status/{task_id}")
async def get_task_status_api(task_id: str):
    """
    获取任务状态
    """
    try:
        status = get_task_status(task_id)
        return {
            "status": "success",
            "task_status": status
        }
    except Exception as e:
        logger.error(f"获取任务状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取任务状态失败: {str(e)}")


@router.get("/download/{session_id}/{filename}")
async def download_generated_file(session_id: str, filename: str):
    """
    下载生成的文件
    """
    try:
        # 构建文件路径
        session_dir = UPLOAD_BASE_DIR / session_id
        output_dir = session_dir / "output"
        file_path = output_dir / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='application/octet-stream'
        )
        
    except Exception as e:
        logger.error(f"文件下载失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件下载失败: {str(e)}")


@router.get("/status/{session_id}")
async def get_session_status(session_id: str):
    """
    获取会话状态
    """
    try:
        session_dir = UPLOAD_BASE_DIR / session_id
        if not session_dir.exists():
            return {"status": "not_found", "message": "会话不存在"}
        
        # 检查已上传的文件
        impact_files = list(session_dir.glob("impact_*"))
        planning_files = list(session_dir.glob("planning_*"))
        
        # 检查输出文件
        output_dir = session_dir / "output"
        output_files = []
        if output_dir.exists():
            output_files = [f.name for f in output_dir.iterdir() if f.is_file()]
        
        return {
            "status": "active",
            "session_id": session_id,
            "uploaded_files": {
                "impact_analysis": len(impact_files) > 0,
                "planning": len(planning_files) > 0
            },
            "generated_files": output_files
        }
        
    except Exception as e:
        logger.error(f"获取会话状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


@router.get("/code-analysis/{task_id}")
async def get_code_analysis_result(task_id: str):
    """
    获取代码分析结果
    
    Args:
        task_id: 任务ID
        
    Returns:
        代码分析结果
    """
    try:
        from ..service.software_config.line_count.code_statistics import analyze_code_statistics
        
        task_dir = UPLOAD_BASE_DIR / task_id
        
        if not task_dir.exists():
            raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")
        
        # 查找上传的代码文件
        code_files = list(task_dir.glob("*"))
        code_files = [f for f in code_files if f.is_file() and f.name != 'extracted_code']
        
        if not code_files:
            raise HTTPException(status_code=404, detail=f"任务 {task_id} 中未找到代码文件")
        
        # 重新分析（如果需要）
        file_path = code_files[0]  # 使用第一个找到的文件
        analysis_result = analyze_code_statistics(
            file_path=str(file_path),
            task_id=task_id,
            upload_dir=str(UPLOAD_BASE_DIR)
        )
        
        return {
            "status": "success",
            "message": "获取代码分析结果成功",
            "task_id": task_id,
            "analysis_result": analysis_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"获取代码分析结果失败: {str(e)}", "form_api")
        raise HTTPException(status_code=500, detail=f"获取代码分析结果失败: {str(e)}")


@router.delete("/code-analysis/{task_id}")
async def delete_code_analysis(task_id: str):
    """
    删除代码分析任务和相关文件
    
    Args:
        task_id: 任务ID
        
    Returns:
        删除结果
    """
    try:
        import shutil
        
        task_dir = UPLOAD_BASE_DIR / task_id
        
        if not task_dir.exists():
            raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")
        
        # 删除任务目录及所有文件
        shutil.rmtree(task_dir)
        log_info(f"已删除代码分析任务: {task_id}", "form_api")
        
        return {
            "status": "success",
            "message": f"代码分析任务 {task_id} 已删除",
            "task_id": task_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"删除代码分析任务失败: {str(e)}", "form_api")
        raise HTTPException(status_code=500, detail=f"删除代码分析任务失败: {str(e)}")


# 数据模型
from pydantic import BaseModel

class CodeAnalysisResponse(BaseModel):
    """代码分析响应模型"""
    status: str
    message: str
    task_id: str
    analysis_result: dict
