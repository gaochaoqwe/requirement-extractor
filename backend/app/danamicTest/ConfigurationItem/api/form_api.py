"""
表单生成API端点
处理配置项测试表单的生成和任务管理
"""

from fastapi import APIRouter, HTTPException, Form, BackgroundTasks, UploadFile, File
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Optional
from datetime import datetime

try:
    from ..utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

from ..utils.logging_utils.log_utils import setup_logger
from ..service.task_runner import (
    run_form_generation_task, get_task_status, clear_all_tasks, generate_task_id,
    run_step1_project_info_task, run_step2_test_issue_task,
    run_step3a_requirement_basic_task, run_step3b_test_items_task,
    run_step3_requirement_analysis_task, run_step4_test_case_task
)
from .upload_api import get_upload_base_dir

router = APIRouter(tags=["表单生成"])
logger = setup_logger(__name__)

# 在模块加载时清理旧的任务状态
clear_all_tasks()

# 获取上传目录
UPLOAD_BASE_DIR = get_upload_base_dir()


@router.post("/generate-forms")
async def generate_configuration_forms(
    background_tasks: BackgroundTasks,
    session_id: str = Form(...),
    test_manager: str = Form(...),
    test_personnel: str = Form(...),
    developer: str = Form(...),
    software_name: str = Form(...),
    software_version: str = Form(...),
    software_id: str = Form(...),
    domain: str = Form(...),
    product_type: str = Form(...),
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
    生成配置项测试表单（异步任务）
    """
    try:
        # 检查会话目录是否存在
        session_dir = UPLOAD_BASE_DIR / session_id
        if not session_dir.exists():
            raise HTTPException(status_code=404, detail="会话不存在，请先上传文档")
        
        # 查找已上传的文件
        requirement_files = list(session_dir.glob("requirement_*"))
        if not requirement_files:
            raise HTTPException(status_code=400, detail="需求文档未上传")
        
        # 查找策划文档或目录文档
        if has_planning:
            planning_files = list(session_dir.glob("planning_*"))
            if not planning_files:
                raise HTTPException(status_code=400, detail="策划文档未上传")
        else:
            catalog_files = list(session_dir.glob("catalog_*"))
            if not catalog_files:
                raise HTTPException(status_code=400, detail="需求目录文档未上传")
        
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
            "product_type": product_type,
            "detector_flag": detector_flag,
            # 可选信息
            "aircraft_model": aircraft_model,
            "project_director": project_director,
            "development_department": development_department,
            "chief_designer": chief_designer,
            # 代码统计信息
            "code_lines": code_lines
        }
        
        # 添加调试日志
        from ..utils.logging_utils.logger import log_debug
        log_debug(f"🔍 [API DEBUG] 接收到的development_department参数: '{development_department}'", "form_api")
        log_debug(f"🔍 [API DEBUG] basic_info中的development_department: '{basic_info['development_department']}'", "form_api")
        
        # 生成任务ID
        task_id = generate_task_id()
        
        # 启动后台任务
        background_tasks.add_task(
            run_form_generation_task,
            session_id=session_id,
            basic_info=basic_info,
            ai_analysis=ai_analysis,
            deep_analysis=deep_analysis,
            task_id=task_id
        )
        
        return {
            "status": "success",
            "message": "任务已启动，正在生成配置项测试表单",
            "task_id": task_id,
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"启动配置项测试表单生成任务失败: {str(e)}")
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
        file_path = UPLOAD_BASE_DIR / session_id / "output" / filename
        
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
            raise HTTPException(status_code=404, detail="会话不存在")
        
        # 检查已上传的文件
        uploaded_files = {
            "requirement": bool(list(session_dir.glob("requirement_*"))),
            "planning": bool(list(session_dir.glob("planning_*"))),
            "catalog": bool(list(session_dir.glob("catalog_*")))
        }
        
        # 检查生成的文件
        output_dir = session_dir / "output"
        generated_files = []
        if output_dir.exists():
            generated_files = [f.name for f in output_dir.iterdir() if f.is_file()]
        
        return {
            "status": "success",
            "session_id": session_id,
            "uploaded_files": uploaded_files,
            "generated_files": generated_files,
            "generation_complete": len(generated_files) > 0
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


# ============================================================================
# 分步生成API端点
# ============================================================================

@router.post("/generate-step1-project-info")
async def generate_step1_project_info(
    background_tasks: BackgroundTasks,
    session_id: str = Form(...),
    test_manager: str = Form(...),
    test_personnel: str = Form(...),
    developer: str = Form(...),
    software_name: str = Form(...),
    software_version: str = Form(...),
    software_id: str = Form(...),
    domain: str = Form(...),
    product_type: str = Form(...),
    detector_flag: str = Form("有检测仪"),
    # 可选信息
    aircraft_model: str = Form(""),
    project_director: str = Form(""),
    development_department: str = Form(""),
    chief_designer: str = Form(""),
    project_manager: str = Form(""),
    # 代码行数
    code_lines: int = Form(None)
):
    """
    步骤1: 生成项目信息表（项目基本信息 + 软件配置项信息）
    """
    try:
        logger.info(f"[步骤1] 接收到生成项目信息表请求，session_id: {session_id}")
        logger.info(f"[步骤1] 基本信息 - 软件名称: {software_name}, 测试主管: {test_manager}, 代码行数: {code_lines}")
        
        # 检查会话目录
        session_dir = UPLOAD_BASE_DIR / session_id
        if not session_dir.exists():
            logger.error(f"[步骤1] 会话目录不存在: {session_dir}")
            raise HTTPException(status_code=404, detail="会话不存在，请先上传需求文档")
        
        # 准备基本信息
        basic_info = {
            "test_manager": test_manager,
            "test_personnel": test_personnel,
            "developer": developer,
            "software_name": software_name,
            "software_version": software_version,
            "software_id": software_id,
            "domain": domain,
            "product_type": product_type,
            "detector_flag": detector_flag
        }
        
        # 准备可选信息
        optional_info = {
            "aircraft_model": aircraft_model,
            "project_director": project_director,
            "development_department": development_department,
            "chief_designer": chief_designer,
            "project_manager": project_manager
        }
        
        # 更新状态文件中的基本信息
        try:
            from ..service.state_manager import GenerationStateManager
            state_manager = GenerationStateManager(session_dir)
            combined_info = {**basic_info, **optional_info, "code_lines": code_lines}
            state_manager.update_basic_info(combined_info)
            logger.info(f"[步骤1] 状态文件基本信息已更新")
        except Exception as e:
            logger.warning(f"[步骤1] 更新状态文件基本信息失败: {str(e)}")
        
        # 生成任务ID
        task_id = generate_task_id()
        logger.info(f"[步骤1] 生成任务ID: {task_id}")
        
        # 启动后台任务
        logger.info(f"[步骤1] 正在启动后台任务...")
        background_tasks.add_task(
            run_step1_project_info_task,
            session_id=session_id,
            basic_info=basic_info,
            optional_info=optional_info,
            code_lines=code_lines,
            task_id=task_id
        )
        logger.info(f"[步骤1] 后台任务已添加到队列，task_id: {task_id}")
        
        return {
            "status": "success",
            "message": "步骤1任务已启动",
            "task_id": task_id,
            "session_id": session_id,
            "step": "step1_project_info"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"[步骤1] 启动任务失败: {str(e)}")
        logger.error(f"[步骤1] 错误详情:\n{error_detail}")
        raise HTTPException(status_code=500, detail=f"任务启动失败: {str(e)}")


@router.post("/upload-step1-result")
async def upload_step1_result(
    session_id: str = Form(...),
    file: UploadFile = File(...)
):
    """
    上传步骤1生成的项目信息表（用户可能已修改）
    """
    try:
        logger.info(f"[步骤2] 接收步骤1结果上传，session_id: {session_id}")
        logger.info(f"[步骤2] 上传文件名: {file.filename}")
        
        # 检查会话目录
        session_dir = UPLOAD_BASE_DIR / session_id
        if not session_dir.exists():
            logger.error(f"[步骤2] 会话目录不存在: {session_dir}")
            raise HTTPException(status_code=404, detail="会话不存在")
        
        # 检查文件类型
        if not file.filename.endswith('.xlsx'):
            raise HTTPException(status_code=400, detail="只支持.xlsx格式的Excel文件")
        
        # 保存上传的文件
        upload_dir = session_dir / "user_uploads"
        upload_dir.mkdir(exist_ok=True)
        
        file_path = upload_dir / "项目信息表_用户版.xlsx"
        
        # 保存文件
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"[步骤2] 文件已保存: {file_path}")
        
        # 更新状态文件
        from ..service.state_manager import GenerationStateManager
        state_manager = GenerationStateManager(session_dir)
        
        # 在状态文件中记录上传信息
        state = state_manager.load_state()
        if state:
            from datetime import datetime
            state["step2_uploaded_file"] = str(file_path)
            state["step2_uploaded_at"] = datetime.now().isoformat()
            state["step2_uploaded_filename"] = file.filename
            state_manager._save_state(state)
            logger.info(f"[步骤2] 状态文件已更新")
        
        return {
            "status": "success",
            "message": "文件上传成功",
            "filename": file.filename,
            "session_id": session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"[步骤2] 上传失败: {str(e)}")
        logger.error(f"[步骤2] 错误详情:\n{error_detail}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/upload-step1-result")
async def upload_step1_result(
    file: UploadFile = File(...),
    session_id: str = Form(...)
):
    """
    上传步骤1生成的项目信息表（用户可能已修改）
    """
    try:
        logger.info(f"[上传步骤1结果] 收到上传请求, session_id: {session_id}, filename: {file.filename}")
        
        # 检查会话目录
        session_dir = UPLOAD_BASE_DIR / session_id
        if not session_dir.exists():
            logger.error(f"[上传步骤1结果] 会话目录不存在: {session_dir}")
            raise HTTPException(status_code=404, detail="会话不存在")
        
        # 检查文件扩展名
        if not file.filename.endswith('.xlsx'):
            raise HTTPException(status_code=400, detail="只支持.xlsx格式的文件")
        
        # 保存上传的文件
        uploaded_file_path = session_dir / "项目信息表_用户上传.xlsx"
        with uploaded_file_path.open("wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"[上传步骤1结果] 文件已保存到: {uploaded_file_path}")
        
        # 更新状态文件
        from ..service.state_manager import GenerationStateManager
        state_manager = GenerationStateManager(session_dir)
        state = state_manager.load_state()
        state["step2_uploaded_file"] = str(uploaded_file_path)
        state["step2_uploaded_at"] = datetime.now().isoformat()
        state_manager.save_state(state)
        
        logger.info(f"[上传步骤1结果] 状态已更新")
        
        return {
            "status": "success",
            "message": "文件上传成功",
            "filename": file.filename,
            "saved_path": str(uploaded_file_path)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"[上传步骤1结果] 上传失败: {str(e)}")
        logger.error(f"[上传步骤1结果] 错误详情:\n{error_detail}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/generate-step2-test-issue")
async def generate_step2_test_issue(
    background_tasks: BackgroundTasks,
    session_id: str = Form(...)
):
    """
    步骤2: 生成策划表与问题单（在用户上传的Excel上添加新sheet）
    """
    try:
        logger.info(f"[步骤2] 接收到生成请求，session_id: {session_id}")
        
        # 检查会话目录
        session_dir = UPLOAD_BASE_DIR / session_id
        if not session_dir.exists():
            logger.error(f"[步骤2] 会话目录不存在: {session_dir}")
            raise HTTPException(status_code=404, detail="会话不存在")
        
        # 从状态文件获取基本信息
        try:
            from ..service.state_manager import GenerationStateManager
            state_manager = GenerationStateManager(session_dir)
            state = state_manager.load_state()
            basic_info = state_manager.get_basic_info()
            
            if not basic_info:
                raise HTTPException(status_code=400, detail="未找到基本信息，请先完成步骤1")
            
            # 检查是否可以开始步骤2
            can_start, reason = state_manager.can_start_step("step2_test_issue")
            if not can_start:
                raise HTTPException(status_code=400, detail=reason)
            
            # ✅ 检查是否已上传步骤1的文件
            uploaded_file = state.get("step2_uploaded_file")
            if not uploaded_file:
                raise HTTPException(status_code=400, detail="请先上传步骤1生成的项目信息表")
            
            if not Path(uploaded_file).exists():
                raise HTTPException(status_code=400, detail="上传的文件不存在，请重新上传")
            
            logger.info(f"[步骤2] 将使用上传的文件: {uploaded_file}")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"检查步骤2前置条件失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"检查前置条件失败: {str(e)}")
        
        # 生成任务ID
        task_id = generate_task_id()
        logger.info(f"[步骤2] 生成任务ID: {task_id}")
        
        # 启动后台任务
        logger.info(f"[步骤2] 正在启动后台任务...")
        background_tasks.add_task(
            run_step2_test_issue_task,
            session_id=session_id,
            task_id=task_id
        )
        logger.info(f"[步骤2] 后台任务已添加到队列，task_id: {task_id}")
        
        return {
            "status": "success",
            "message": "步骤2任务已启动",
            "task_id": task_id,
            "session_id": session_id,
            "step": "step2_test_issue"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"[步骤2] 启动任务失败: {str(e)}")
        logger.error(f"[步骤2] 错误详情:\n{error_detail}")
        raise HTTPException(status_code=500, detail=f"任务启动失败: {str(e)}")


@router.post("/upload-step2-result")
async def upload_step2_result(
    file: UploadFile = File(...),
    session_id: str = Form(...)
):
    """
    上传步骤2生成的表单（用户可能已修改）
    """
    try:
        logger.info(f"[上传步骤2结果] 收到上传请求, session_id: {session_id}, filename: {file.filename}")
        
        # 检查会话目录
        session_dir = UPLOAD_BASE_DIR / session_id
        if not session_dir.exists():
            logger.error(f"[上传步骤2结果] 会话目录不存在: {session_dir}")
            raise HTTPException(status_code=404, detail="会话不存在")
        
        # 检查文件扩展名
        if not file.filename.endswith('.xlsx'):
            raise HTTPException(status_code=400, detail="只支持.xlsx格式的文件")
        
        # 保存上传的文件
        uploaded_file_path = session_dir / "完整表单_步骤2用户上传.xlsx"
        with uploaded_file_path.open("wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"[上传步骤2结果] 文件已保存到: {uploaded_file_path}")
        
        # 更新状态文件
        from ..service.state_manager import GenerationStateManager
        state_manager = GenerationStateManager(session_dir)
        state = state_manager.load_state()
        state["step3_uploaded_file"] = str(uploaded_file_path)
        state["step3_uploaded_at"] = datetime.now().isoformat()
        state_manager.save_state(state)
        
        logger.info(f"[上传步骤2结果] 状态已更新")
        
        return {
            "status": "success",
            "message": "文件上传成功",
            "filename": file.filename,
            "saved_path": str(uploaded_file_path)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"[上传步骤2结果] 上传失败: {str(e)}")
        logger.error(f"[上传步骤2结果] 错误详情:\n{error_detail}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/generate-step3a-requirement-basic")
async def generate_step3a_requirement_basic(
    background_tasks: BackgroundTasks,
    session_id: str = Form(...),
    ai_analysis: bool = Form(True),
    deep_analysis: bool = Form(True)
):
    """
    步骤3a: 生成需求分析表基础信息（除测试项描述和测试方法外的所有列）
    """
    try:
        logger.info(f"[步骤3a] 收到生成请求, session_id: {session_id}")
        
        # 检查会话目录
        session_dir = UPLOAD_BASE_DIR / session_id
        if not session_dir.exists():
            raise HTTPException(status_code=404, detail="会话不存在")
        
        # 从状态文件获取基本信息
        try:
            from ..service.state_manager import GenerationStateManager
            state_manager = GenerationStateManager(session_dir)
            state = state_manager.load_state()
            basic_info = state_manager.get_basic_info()
            
            if not basic_info:
                raise HTTPException(status_code=400, detail="未找到基本信息")
            
            # 检查是否可以开始步骤3a（依赖步骤2完成）
            step2_completed = state.get('completed_steps', {}).get('step2_test_issue', {}).get('completed', False)
            if not step2_completed:
                raise HTTPException(status_code=400, detail="请先完成步骤2")
            
            # ✅ 检查是否已上传步骤2的文件
            uploaded_file = state.get("step3_uploaded_file")
            if not uploaded_file:
                raise HTTPException(status_code=400, detail="请先上传步骤2生成的表单")
            
            if not Path(uploaded_file).exists():
                raise HTTPException(status_code=400, detail="上传的文件不存在，请重新上传")
            
            logger.info(f"[步骤3a] 将使用上传的文件: {uploaded_file}")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"检查步骤3a前置条件失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"检查前置条件失败: {str(e)}")
        
        # 生成任务ID
        task_id = generate_task_id()
        
        # 启动后台任务
        background_tasks.add_task(
            run_step3a_requirement_basic_task,
            session_id=session_id,
            basic_info=basic_info,
            ai_analysis=ai_analysis,
            deep_analysis=deep_analysis,
            task_id=task_id
        )
        
        return {
            "status": "success",
            "message": "步骤3a任务已启动",
            "task_id": task_id,
            "session_id": session_id,
            "step": "step3a_requirement_basic"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动步骤3a任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"任务启动失败: {str(e)}")


@router.post("/upload-step3a-result")
async def upload_step3a_result(
    file: UploadFile = File(...),
    session_id: str = Form(...)
):
    """
    上传步骤3a生成的需求分析表基础版（用户可能已修改）
    """
    try:
        logger.info(f"[上传步骤3a结果] 收到上传请求, session_id: {session_id}, filename: {file.filename}")
        
        # 检查会话目录
        session_dir = UPLOAD_BASE_DIR / session_id
        if not session_dir.exists():
            logger.error(f"[上传步骤3a结果] 会话目录不存在: {session_dir}")
            raise HTTPException(status_code=404, detail="会话不存在")
        
        # 检查文件扩展名
        if not file.filename.endswith('.xlsx'):
            raise HTTPException(status_code=400, detail="只支持.xlsx格式的文件")
        
        # 保存上传的文件
        uploaded_file_path = session_dir / "需求分析表_基础_用户上传.xlsx"
        with uploaded_file_path.open("wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"[上传步骤3a结果] 文件已保存到: {uploaded_file_path}")
        
        # 更新状态文件
        from ..service.state_manager import GenerationStateManager
        state_manager = GenerationStateManager(session_dir)
        state = state_manager.load_state()
        state["step3b_uploaded_file"] = str(uploaded_file_path)
        state["step3b_uploaded_at"] = datetime.now().isoformat()
        state_manager.save_state(state)
        
        logger.info(f"[上传步骤3a结果] 状态已更新")
        
        return {
            "status": "success",
            "message": "文件上传成功",
            "filename": file.filename,
            "saved_path": str(uploaded_file_path)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"[上传步骤3a结果] 上传失败: {str(e)}")
        logger.error(f"[上传步骤3a结果] 错误详情:\n{error_detail}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/generate-step3b-test-items")
async def generate_step3b_test_items(
    background_tasks: BackgroundTasks,
    session_id: str = Form(...),
    ai_analysis: bool = Form(True)
):
    """
    步骤3b: 完善需求分析表（填充测试项描述和测试方法）
    """
    try:
        logger.info(f"[步骤3b] 收到生成请求, session_id: {session_id}")
        
        # 检查会话目录
        session_dir = UPLOAD_BASE_DIR / session_id
        if not session_dir.exists():
            raise HTTPException(status_code=404, detail="会话不存在")
        
        # 从状态文件获取基本信息
        try:
            from ..service.state_manager import GenerationStateManager
            state_manager = GenerationStateManager(session_dir)
            state = state_manager.load_state()
            basic_info = state_manager.get_basic_info()
            
            if not basic_info:
                raise HTTPException(status_code=400, detail="未找到基本信息")
            
            # 检查是否已完成步骤3a
            step3a_completed = state.get('completed_steps', {}).get('step3a_requirement_basic', {}).get('completed', False)
            if not step3a_completed:
                raise HTTPException(status_code=400, detail="请先完成步骤3a")
            
            # ✅ 检查是否已上传步骤3a的文件
            uploaded_file = state.get("step3b_uploaded_file")
            if not uploaded_file:
                raise HTTPException(status_code=400, detail="请先上传步骤3a生成的需求分析表基础版")
            
            if not Path(uploaded_file).exists():
                raise HTTPException(status_code=400, detail="上传的文件不存在，请重新上传")
            
            logger.info(f"[步骤3b] 将使用上传的文件: {uploaded_file}")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"检查步骤3b前置条件失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"检查前置条件失败: {str(e)}")
        
        # 生成任务ID
        task_id = generate_task_id()
        
        # 启动后台任务
        background_tasks.add_task(
            run_step3b_test_items_task,
            session_id=session_id,
            basic_info=basic_info,
            ai_analysis=ai_analysis,
            task_id=task_id
        )
        
        return {
            "status": "success",
            "message": "步骤3b任务已启动",
            "task_id": task_id,
            "session_id": session_id,
            "step": "step3b_test_items"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动步骤3b任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"任务启动失败: {str(e)}")


@router.post("/generate-step3-requirement-analysis")
async def generate_step3_requirement_analysis(
    background_tasks: BackgroundTasks,
    session_id: str = Form(...),
    ai_analysis: bool = Form(True),
    deep_analysis: bool = Form(True)
):
    """
    步骤3: 生成需求分析表（基于项目策划表）
    """
    try:
        # 检查会话目录
        session_dir = UPLOAD_BASE_DIR / session_id
        if not session_dir.exists():
            raise HTTPException(status_code=404, detail="会话不存在")
        
        # 从状态文件获取基本信息
        try:
            from ..service.state_manager import GenerationStateManager
            state_manager = GenerationStateManager(session_dir)
            state = state_manager.load_state()
            basic_info = state_manager.get_basic_info()
            
            if not basic_info:
                raise HTTPException(status_code=400, detail="未找到基本信息")
            
            # 检查是否可以开始步骤3
            can_start, reason = state_manager.can_start_step("step3_requirement_analysis")
            if not can_start:
                raise HTTPException(status_code=400, detail=reason)
            
            # ✅ 检查是否已上传步骤2的文件
            uploaded_file = state.get("step3_uploaded_file")
            if not uploaded_file:
                raise HTTPException(status_code=400, detail="请先上传步骤2生成的表单")
            
            if not Path(uploaded_file).exists():
                raise HTTPException(status_code=400, detail="上传的文件不存在，请重新上传")
            
            logger.info(f"[步骤3] 将使用上传的文件: {uploaded_file}")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"检查步骤3前置条件失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"检查前置条件失败: {str(e)}")
        
        # 生成任务ID
        task_id = generate_task_id()
        
        # 启动后台任务
        background_tasks.add_task(
            run_step3_requirement_analysis_task,
            session_id=session_id,
            basic_info=basic_info,
            ai_analysis=ai_analysis,
            deep_analysis=deep_analysis,
            task_id=task_id
        )
        
        return {
            "status": "success",
            "message": "步骤3任务已启动",
            "task_id": task_id,
            "session_id": session_id,
            "step": "step3_requirement_analysis"
        }
        
    except Exception as e:
        logger.error(f"启动步骤3任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"任务启动失败: {str(e)}")


@router.post("/upload-step3-result")
async def upload_step3_result(
    file: UploadFile = File(...),
    session_id: str = Form(...)
):
    """
    上传步骤3生成的表单（用户可能已修改）
    """
    try:
        logger.info(f"[上传步骤3结果] 收到上传请求, session_id: {session_id}, filename: {file.filename}")
        
        # 检查会话目录
        session_dir = UPLOAD_BASE_DIR / session_id
        if not session_dir.exists():
            logger.error(f"[上传步骤3结果] 会话目录不存在: {session_dir}")
            raise HTTPException(status_code=404, detail="会话不存在")
        
        # 检查文件扩展名
        if not file.filename.endswith('.xlsx'):
            raise HTTPException(status_code=400, detail="只支持.xlsx格式的文件")
        
        # 保存上传的文件
        uploaded_file_path = session_dir / "完整表单_步骤3用户上传.xlsx"
        with uploaded_file_path.open("wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"[上传步骤3结果] 文件已保存到: {uploaded_file_path}")
        
        # 更新状态文件
        from ..service.state_manager import GenerationStateManager
        state_manager = GenerationStateManager(session_dir)
        state = state_manager.load_state()
        state["step4_uploaded_file"] = str(uploaded_file_path)
        state["step4_uploaded_at"] = datetime.now().isoformat()
        state_manager.save_state(state)
        
        logger.info(f"[上传步骤3结果] 状态已更新")
        
        return {
            "status": "success",
            "message": "文件上传成功",
            "filename": file.filename,
            "saved_path": str(uploaded_file_path)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"[上传步骤3结果] 上传失败: {str(e)}")
        logger.error(f"[上传步骤3结果] 错误详情:\n{error_detail}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/generate-step4-test-case")
async def generate_step4_test_case(
    background_tasks: BackgroundTasks,
    session_id: str = Form(...),
    ai_analysis: bool = Form(True)
):
    """
    步骤4: 生成测试用例单（基于需求分析表）
    """
    try:
        # 检查会话目录
        session_dir = UPLOAD_BASE_DIR / session_id
        if not session_dir.exists():
            raise HTTPException(status_code=404, detail="会话不存在")
        
        # 从状态文件获取基本信息
        try:
            from ..service.state_manager import GenerationStateManager
            state_manager = GenerationStateManager(session_dir)
            state = state_manager.load_state()
            basic_info = state_manager.get_basic_info()
            
            if not basic_info:
                raise HTTPException(status_code=400, detail="未找到基本信息")
            
            # 检查是否可以开始步骤4
            can_start, reason = state_manager.can_start_step("step4_test_case")
            if not can_start:
                raise HTTPException(status_code=400, detail=reason)
            
            # ✅ 检查是否已上传步骤3的文件
            uploaded_file = state.get("step4_uploaded_file")
            if not uploaded_file:
                raise HTTPException(status_code=400, detail="请先上传步骤3生成的表单")
            
            if not Path(uploaded_file).exists():
                raise HTTPException(status_code=400, detail="上传的文件不存在，请重新上传")
            
            logger.info(f"[步骤4] 将使用上传的文件: {uploaded_file}")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"检查步骤4前置条件失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"检查前置条件失败: {str(e)}")
        
        # 生成任务ID
        task_id = generate_task_id()
        
        # 启动后台任务
        background_tasks.add_task(
            run_step4_test_case_task,
            session_id=session_id,
            basic_info=basic_info,
            ai_analysis=ai_analysis,
            task_id=task_id
        )
        
        return {
            "status": "success",
            "message": "步骤4任务已启动",
            "task_id": task_id,
            "session_id": session_id,
            "step": "step4_test_case"
        }
        
    except Exception as e:
        logger.error(f"启动步骤4任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"任务启动失败: {str(e)}")


@router.get("/generation-state/{session_id}")
async def get_generation_state(session_id: str):
    """
    获取生成状态
    """
    try:
        session_dir = UPLOAD_BASE_DIR / session_id
        if not session_dir.exists():
            raise HTTPException(status_code=404, detail="会话不存在")
        
        # 加载状态文件
        from ..service.state_manager import GenerationStateManager
        state_manager = GenerationStateManager(session_dir)
        state = state_manager.load_state()
        
        if state is None:
            # 如果状态文件不存在，返回初始状态
            return {
                "status": "success",
                "session_id": session_id,
                "state": {
                    "completed_steps": {
                        "step1_project_info": {"completed": False},
                        "step2_test_issue": {"completed": False},
                        "step3_requirement_analysis": {"completed": False},
                        "step4_test_case": {"completed": False}
                    }
                }
            }
        
        # ✅ 补充“需求是否已确认”信息（兼容老会话：仅通过文件存在判断）
        try:
            confirmed_file = session_dir / "catalog_confirmed.txt"
            state.setdefault("catalog_confirmed", confirmed_file.exists())
        except Exception:
            state.setdefault("catalog_confirmed", False)

        return {
            "status": "success",
            "session_id": session_id,
            "state": state
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取生成状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")
