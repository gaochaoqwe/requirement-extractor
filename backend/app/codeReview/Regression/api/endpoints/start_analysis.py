"""
回归测试代码审查分析启动API端点
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ...db.deps import get_db
from ...db.repository import FileRepository, TaskRepository
from ...service.ai.task_planner.regression_planner import RegressionTaskPlanner
import uuid
import os
import logging

router = APIRouter()

# 创建请求模型
class StartAnalysisRequest(BaseModel):
    old_file_id: int
    new_file_id: int
    report_file_id: int

# 创建响应模型
class StartAnalysisResponse(BaseModel):
    task_id: str
    message: str

@router.post("/start_analysis", response_model=StartAnalysisResponse, summary="Start regression code review analysis")
def start_analysis(
    request: StartAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    启动回归测试代码审查分析
    
    - **old_file_id**: 上一版本代码文件ID
    - **new_file_id**: 当前版本代码文件ID
    - **report_file_id**: 影响域分析报告文件ID
    """
    # 检查文件是否存在
    file_repo = FileRepository(db)
    
    # 检查旧版本代码文件
    old_file = file_repo.get_file(request.old_file_id)
    if not old_file:
        raise HTTPException(status_code=404, detail=f"上一版本代码文件不存在，ID: {request.old_file_id}")
    if old_file.file_type != 'old':
        raise HTTPException(status_code=400, detail=f"文件类型不匹配，期望'old'，实际为'{old_file.file_type}'")
    
    # 检查新版本代码文件
    new_file = file_repo.get_file(request.new_file_id)
    if not new_file:
        raise HTTPException(status_code=404, detail=f"当前版本代码文件不存在，ID: {request.new_file_id}")
    if new_file.file_type != 'new':
        raise HTTPException(status_code=400, detail=f"文件类型不匹配，期望'new'，实际为'{new_file.file_type}'")
    
    # 检查影响域分析报告文件
    report_file = file_repo.get_file(request.report_file_id)
    if not report_file:
        raise HTTPException(status_code=404, detail=f"影响域分析报告文件不存在，ID: {request.report_file_id}")
    if report_file.file_type != 'report':
        raise HTTPException(status_code=400, detail=f"文件类型不匹配，期望'report'，实际为'{report_file.file_type}'")
    
    # 创建任务
    task_repo = TaskRepository(db)
    task_id = str(uuid.uuid4())
    
    # 保存任务信息
    task_data = {
        "id": task_id,
        "status": "pending",
        "old_file_id": request.old_file_id,
        "new_file_id": request.new_file_id,
        "report_file_id": request.report_file_id,
        "progress": 0
    }
    task = task_repo.create_task(task_data)
    
    # 在后台启动分析任务
    background_tasks.add_task(
        run_analysis_task, 
        task_id=task_id,
        old_file_path=old_file.file_path,
        old_extract_path=old_file.extract_path,
        new_file_path=new_file.file_path,
        new_extract_path=new_file.extract_path,
        report_file_path=report_file.file_path,
        report_extract_path=report_file.extract_path
    )
    
    return {
        "task_id": task_id,
        "message": "回归测试代码审查分析任务已启动"
    }

def run_analysis_task(
    task_id: str, 
    old_file_path: str,
    old_extract_path: str,
    new_file_path: str,
    new_extract_path: str,
    report_file_path: str,
    report_extract_path: str
):
    """
    执行代码审查分析任务
    
    Args:
        task_id: 任务ID
        old_file_path: 上一版本代码文件路径
        old_extract_path: 上一版本代码解压路径
        new_file_path: 当前版本代码文件路径
        new_extract_path: 当前版本代码解压路径
        report_file_path: 影响域分析报告文件路径
        report_extract_path: 影响域分析报告解压路径
    """
    # 获取数据库会话
    from ...db.database import SessionLocal
    db = SessionLocal()
    
    try:
        # 更新任务状态为处理中
        task_repo = TaskRepository(db)
        task_repo.update_task(task_id, {"status": "processing", "progress": 5})
        
        # 准备工作目录（合并新旧代码版本）
        merged_extract_path = prepare_regression_workspace(
            old_extract_path,
            new_extract_path,
            report_extract_path,
            report_file_path
        )
        
        # 创建合并后的文件记录
        file_repo = FileRepository(db)
        merged_file_data = {
            "file_name": f"merged_regression_{task_id}",
            "file_path": "",  # 没有实际的压缩文件
            "extract_path": merged_extract_path,
            "status": "processing",
            "file_type": "merged",
            "task_id": task_id
        }
        merged_file = file_repo.create_file(merged_file_data)
        
        # 使用任务规划器执行回归测试审查
        task_planner = RegressionTaskPlanner(db, task_id, merged_file.id)
        success = task_planner.run_regression_review()
        
        if success:
            # 更新任务状态为完成
            task_repo.update_task(task_id, {"status": "completed", "progress": 100})
        else:
            # 更新任务状态为失败
            task_repo.update_task(task_id, {"status": "failed", "error_message": "任务规划执行失败"})
        
    except Exception as e:
        # 记录错误并更新任务状态
        logging.error(f"回归测试代码审查分析任务失败: {e}")
        task_repo.update_task(task_id, {"status": "failed", "error_message": str(e)})
    
    finally:
        db.commit()
        db.close()

def prepare_regression_workspace(
    old_extract_path: str,
    new_extract_path: str,
    report_extract_path: str,
    report_file_path: str
) -> str:
    """
    准备回归测试工作空间
    
    Args:
        old_extract_path: 旧版本代码解压路径
        new_extract_path: 新版本代码解压路径
        report_extract_path: 报告解压路径
        report_file_path: 报告文件路径
        
    Returns:
        str: 合并后的工作目录路径
    """
    import shutil
    import tempfile
    from pathlib import Path
    
    # 创建临时工作目录
    workspace_id = uuid.uuid4().hex
    workspace_path = os.path.join(tempfile.gettempdir(), f"regression_workspace_{workspace_id}")
    os.makedirs(workspace_path, exist_ok=True)
    
    # 创建v1和v2目录
    v1_dir = os.path.join(workspace_path, "v1.00")
    v2_dir = os.path.join(workspace_path, "v1.01")
    os.makedirs(v1_dir, exist_ok=True)
    os.makedirs(v2_dir, exist_ok=True)
    
    # 复制旧版本代码到v1目录
    if old_extract_path and os.path.exists(old_extract_path):
        for item in os.listdir(old_extract_path):
            src = os.path.join(old_extract_path, item)
            dst = os.path.join(v1_dir, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
    
    # 复制新版本代码到v2目录
    if new_extract_path and os.path.exists(new_extract_path):
        for item in os.listdir(new_extract_path):
            src = os.path.join(new_extract_path, item)
            dst = os.path.join(v2_dir, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
    
    # 复制影响域分析报告到根目录，保持原始文件名
    report_copied = False
    if report_extract_path and os.path.exists(report_extract_path):
        # 如果报告是一个文件而不是目录
        if os.path.isfile(report_extract_path):
            shutil.copy2(report_extract_path, os.path.join(workspace_path, os.path.basename(report_extract_path)))
            report_copied = True
        else:
            # 查找报告文件并复制
            for root, _, files in os.walk(report_extract_path):
                for file in files:
                    if "impact" in file.lower() or "影响域" in file:
                        src = os.path.join(root, file)
                        dst = os.path.join(workspace_path, file)
                        shutil.copy2(src, dst)
                        report_copied = True
                        break
                if report_copied:
                    break

    # 如果extract_path不存在可用报告，尝试直接使用上传的报告文件
    if not report_copied and report_file_path and os.path.exists(report_file_path):
        shutil.copy2(report_file_path, os.path.join(workspace_path, os.path.basename(report_file_path)))
        report_copied = True

    # 调试日志
    debug_path = os.path.join(workspace_path, "__workspace_info.txt")
    with open(debug_path, "w", encoding="utf-8") as debug_f:
        debug_f.write(f"old_extract_path={old_extract_path}\n")
        debug_f.write(f"new_extract_path={new_extract_path}\n")
        debug_f.write(f"report_extract_path={report_extract_path}\n")
        debug_f.write(f"report_file_path={report_file_path}\n")
        debug_f.write(f"report_copied={report_copied}\n")

    return workspace_path
