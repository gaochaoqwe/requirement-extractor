"""
启动功能点审查的API端点
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from ....db.deps import get_db
from ....db.repository.task_repo import TaskRepository
from ....db.repository.file_repo import FileRepository
from ....service.feature_review import feature_runner

router = APIRouter()


class FeatureInput(BaseModel):
    """单个功能点输入"""
    name: str
    description: str


class StartFeatureReviewRequest(BaseModel):
    """启动功能点审查请求"""
    file_id: int  # 改为基于文件ID
    features: List[FeatureInput]
    software_type: str
    domain: str
    entry_function: str = "main"


class SingleFeatureReviewRequest(BaseModel):
    """单个功能审查请求"""
    feature_name: str
    feature_description: str
    entry_function: str = "main"
    software_type: str = "通用软件"
    domain: str = "通用"


@router.post("/start")
async def start_feature_review(request: StartFeatureReviewRequest, db: Session = Depends(get_db)):
    """
    启动功能点审查
    
    请求体:
    {
        "file_id": 123,
        "features": [
            {"name": "用户登录", "description": "用户通过用户名密码登录系统"},
            {"name": "数据导出", "description": "将数据导出为Excel文件"}
        ],
        "software_type": "分色滤光软件",
        "domain": "光电",
        "entry_function": "main"
    }
    """
    try:
        # 验证文件存在
        file_repo = FileRepository(db)
        file_obj = file_repo.get_file(request.file_id)
        if not file_obj:
            raise HTTPException(status_code=404, detail=f"文件 {request.file_id} 不存在")
        
        # 获取项目根目录
        project_root = file_obj.extract_path
        
        # 创建功能点审查任务
        task_repo = TaskRepository(db)
        task_data = {
            "task_name": f"功能点审查-{request.features[0].name}",
            "task_description": f"功能点审查任务：{request.features[0].description[:100]}...",
            "status": "pending",
            "progress": 0,
            "analysis_type": "feature_review",
            "total_files": 1,
            "processed_files": 0,
            "total_problems": 0,
            "code_file_id": request.file_id
        }
        feature_task = task_repo.create_task(task_data)
        
        # 关联文件到任务
        file_obj.task_id = feature_task.id
        db.commit()
        
        # 转换功能点列表
        features_list = [{"name": f.name, "description": f.description} for f in request.features]
        
        # 构建软件类型（领域/软件类型）
        full_software_type = f"{request.domain}/{request.software_type}" if request.domain else request.software_type
        
        # 启动后台功能点审查
        feature_runner.run_in_background(
            task_id=feature_task.id,
            project_root=project_root,
            features=features_list,
            software_type=full_software_type,
            entry_function=request.entry_function
        )
        
        return {
            "success": True,
            "message": f"功能点审查已启动，共 {len(features_list)} 个功能点",
            "task_id": feature_task.id,
            "feature_count": len(features_list)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动功能点审查失败: {str(e)}")


@router.post("/start/{file_id}")
async def start_single_feature_review(
    file_id: int,
    request: SingleFeatureReviewRequest,
    db: Session = Depends(get_db)
):
    """
    启动单个功能审查
    
    路径参数:
        file_id: 代码库文件ID
    
    请求体:
    {
        "feature_name": "用户登录",
        "feature_description": "用户通过用户名密码登录系统",
        "entry_function": "main",
        "software_type": "通用软件",
        "domain": "通用"
    }
    
    响应:
    {
        "task_id": 123,
        "message": "功能审查任务已创建",
        "feature_name": "用户登录"
    }
    """
    try:
        # 验证文件存在
        file_repo = FileRepository(db)
        file_obj = file_repo.get_file(file_id)
        if not file_obj:
            raise HTTPException(status_code=404, detail=f"代码库文件 {file_id} 不存在")
        
        # 获取项目根目录
        project_root = file_obj.extract_path
        
        # 创建功能审查任务
        task_repo = TaskRepository(db)
        task_data = {
            "task_name": f"功能审查-{request.feature_name}",
            "task_description": request.feature_description[:200] if len(request.feature_description) > 200 else request.feature_description,
            "status": "pending",
            "progress": 0,
            "analysis_type": "feature",
            "total_files": 1,
            "processed_files": 0,
            "total_problems": 0,
            "code_file_id": file_id
        }
        feature_task = task_repo.create_task(task_data)
        db.commit()
        
        # 构建功能列表
        features_list = [{
            "name": request.feature_name,
            "description": request.feature_description
        }]
        
        # 构建软件类型
        full_software_type = f"{request.domain}/{request.software_type}" if request.domain and request.domain != "通用" else request.software_type
        
        # 启动后台功能审查
        feature_runner.run_in_background(
            task_id=feature_task.id,
            project_root=project_root,
            features=features_list,
            software_type=full_software_type,
            entry_function=request.entry_function
        )
        
        return {
            "task_id": feature_task.id,
            "message": "功能审查任务已创建",
            "feature_name": request.feature_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"启动功能审查失败: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=500, detail=f"启动功能审查失败: {str(e)}")

