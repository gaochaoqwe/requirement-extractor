"""
回归测试代码审查文件上传API端点
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from sqlalchemy.orm import Session
import os
import zipfile
import uuid
import shutil
from pathlib import Path
from ...config import ZIP_FOLDER, EXTRACT_FOLDER, ALLOWED_EXTENSIONS, ALLOWED_CODE_EXTENSIONS, ALLOWED_REPORT_EXTENSIONS
from ...db.deps import get_db
from ...db.repository import FileRepository

# 创建路由器并添加标签
router = APIRouter(tags=["回归测试文件上传"])

# 添加健康检查端点
@router.get("/health", summary="Health check for regression code review API")
async def health_check():
    """
    健康检查端点，用于测试回归测试代码审查API是否正常工作
    """
    return {
        "status": "ok",
        "module": "regression_code_review",
        "message": "回归测试代码审查API正常工作"
    }

# 确保注册路由使用正确的路径
@router.post("/upload_file", summary="Upload files for regression code review")
async def upload_file(
    file: UploadFile = File(...),
    version: str = Query(..., description="File version: 'old', 'new', or 'report'"),
    db: Session = Depends(get_db)
):
    """
    上传回归测试代码审查需要的文件：
    
    - version=old: 旧版本代码（ZIP格式）
    - version=new: 新版本代码（ZIP格式）
    - version=report: 影响域分析报告（DOCX格式）
    """
    # 验证版本类型
    if version not in ['old', 'new', 'report']:
        raise HTTPException(status_code=400, detail=f"无效的版本类型: {version}，必须是 'old', 'new', 或 'report'")
    
    # 检查文件扩展名
    filename = file.filename
    ext = os.path.splitext(filename)[-1].lower()
    
    # 根据版本类型检查文件格式
    if version in ['old', 'new']:
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"代码文件只允许上传ZIP格式，当前文件格式: {ext}")
    elif version == 'report':
        if ext not in ALLOWED_REPORT_EXTENSIONS:
            allowed_exts = ', '.join(ALLOWED_REPORT_EXTENSIONS)
            raise HTTPException(status_code=400, detail=f"影响域分析报告只允许上传以下格式: {allowed_exts}，当前文件格式: {ext}")

    # 生成唯一ID
    unique_id = str(uuid.uuid4())
    
    # 构建保存路径
    zip_save_path = os.path.join(ZIP_FOLDER, f"{unique_id}{ext}")
    extract_path = os.path.join(EXTRACT_FOLDER, unique_id)
    
    try:
        # 保存文件
        os.makedirs(os.path.dirname(zip_save_path), exist_ok=True)
        with open(zip_save_path, "wb") as f:
            f.write(await file.read())
        
        # 如果是代码文件（ZIP），则解压并验证
        if version in ['old', 'new']:
            # 创建解压目录
            os.makedirs(extract_path, exist_ok=True)
            
            # 解压ZIP文件
            with zipfile.ZipFile(zip_save_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            
            # 检查是否有有效的源文件
            valid_files = []
            for root, _, files in os.walk(extract_path):
                for file in files:
                    file_ext = os.path.splitext(file)[-1].lower()
                    if file_ext in ALLOWED_CODE_EXTENSIONS:
                        valid_files.append(os.path.join(root, file))
            
            if not valid_files:
                # 如果没有有效文件，清理并报错
                shutil.rmtree(extract_path, ignore_errors=True)
                os.remove(zip_save_path)
                raise HTTPException(status_code=400, detail="ZIP文件中未找到有效的C/C++代码文件")
            
            file_count = len(valid_files)
        else:
            # 报告文件不需要解压
            extract_path = None
            file_count = 1
        
        # 创建数据库记录
        file_repo = FileRepository(db)
        file_data = {
            "file_name": filename,
            "file_path": zip_save_path,
            "extract_path": extract_path,
            "status": "uploaded",
            "file_count": file_count,
            "file_type": version  # 添加文件类型字段
        }
        db_file = file_repo.create_file(file_data)

        return {"message": "文件上传成功", "file_id": db_file.id}
    except Exception as e:
        import sys
        sys.stderr.write(f"文件上传失败: {str(e)}\n")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

# 记录路由注册信息到stderr
import sys
sys.stderr.write(f"回归测试文件上传路由注册: {router.routes[0].path} - 方法: {router.routes[0].methods}\n")
