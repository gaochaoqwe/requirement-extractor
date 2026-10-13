"""
问题过滤规则管理API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from ...db.deps import get_db
from ...db.repository.task_repo import TaskRepository
from ...db.repository.problem_filter_repo import ProblemFilterRepository
from ...utils.logger import log_debug, log_info, log_error

router = APIRouter()


# 请求模型
class CreateFilterRuleRequest(BaseModel):
    """创建过滤规则的请求"""
    filter_name: Optional[str] = None
    keywords: List[str]  # 关键词列表
    logic_type: str = 'AND'  # 逻辑类型：'AND' 或 'OR'
    template_id: Optional[int] = None  # 关联的模板ID
    is_enabled: bool = True


class UpdateFilterRuleRequest(BaseModel):
    """更新过滤规则的请求"""
    filter_name: Optional[str] = None
    keywords: Optional[List[str]] = None
    logic_type: Optional[str] = None  # 逻辑类型：'AND' 或 'OR'
    is_enabled: Optional[bool] = None


# 响应模型
class FilterRuleResponse(BaseModel):
    """过滤规则响应"""
    id: int
    task_id: int
    filter_name: Optional[str]
    keywords: List[str]
    logic_type: str
    template_id: Optional[int]
    is_enabled: bool
    created_at: str
    updated_at: str


@router.post("/{task_id}/problem_filters")
async def create_filter_rule(
    task_id: int,
    request: CreateFilterRuleRequest,
    db: Session = Depends(get_db)
):
    """
    创建过滤规则
    
    Args:
        task_id: 任务ID
        request: 创建请求
        db: 数据库会话
    
    Returns:
        创建的过滤规则
    """
    try:
        # 验证任务是否存在
        task_repo = TaskRepository(db)
        task = task_repo.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 验证关键词列表
        if not request.keywords or len(request.keywords) == 0:
            raise HTTPException(status_code=400, detail="关键词列表不能为空")
        
        # 创建过滤规则
        filter_repo = ProblemFilterRepository(db)
        filter_rule = filter_repo.create_filter(
            task_id=task_id,
            filter_name=request.filter_name,
            keywords=request.keywords,
            logic_type=request.logic_type,
            template_id=request.template_id,
            is_enabled=request.is_enabled
        )
        
        db.commit()
        
        log_info(
            f"创建过滤规则成功: task_id={task_id}, keywords={request.keywords}",
            "problem_filter_api"
        )
        
        return {
            "success": True,
            "message": "过滤规则创建成功",
            "data": filter_rule.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        log_error(f"创建过滤规则失败: task_id={task_id}", "problem_filter_api", e)
        raise HTTPException(status_code=500, detail=f"创建过滤规则失败: {str(e)}")


@router.get("/{task_id}/problem_filters")
async def get_filter_rules(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    获取任务的所有过滤规则
    
    Args:
        task_id: 任务ID
        db: 数据库会话
    
    Returns:
        过滤规则列表
    """
    try:
        # 验证任务是否存在
        task_repo = TaskRepository(db)
        task = task_repo.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 获取过滤规则
        filter_repo = ProblemFilterRepository(db)
        filter_rules = filter_repo.get_filters_by_task(task_id)
        
        log_debug(
            f"获取过滤规则: task_id={task_id}, 数量={len(filter_rules)}",
            "problem_filter_api"
        )
        
        return {
            "success": True,
            "count": len(filter_rules),
            "data": [f.to_dict() for f in filter_rules]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"获取过滤规则失败: task_id={task_id}", "problem_filter_api", e)
        raise HTTPException(status_code=500, detail=f"获取过滤规则失败: {str(e)}")


@router.get("/{task_id}/problem_filters/{filter_id}")
async def get_filter_rule(
    task_id: int,
    filter_id: int,
    db: Session = Depends(get_db)
):
    """
    获取单个过滤规则
    
    Args:
        task_id: 任务ID
        filter_id: 过滤规则ID
        db: 数据库会话
    
    Returns:
        过滤规则详情
    """
    try:
        # 验证任务是否存在
        task_repo = TaskRepository(db)
        task = task_repo.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 获取过滤规则
        filter_repo = ProblemFilterRepository(db)
        filter_rule = filter_repo.get_filter_by_id(filter_id)
        
        if not filter_rule or filter_rule.task_id != task_id:
            raise HTTPException(status_code=404, detail="过滤规则不存在")
        
        return {
            "success": True,
            "data": filter_rule.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"获取过滤规则失败: filter_id={filter_id}", "problem_filter_api", e)
        raise HTTPException(status_code=500, detail=f"获取过滤规则失败: {str(e)}")


@router.put("/{task_id}/problem_filters/{filter_id}")
async def update_filter_rule(
    task_id: int,
    filter_id: int,
    request: UpdateFilterRuleRequest,
    db: Session = Depends(get_db)
):
    """
    更新过滤规则
    
    Args:
        task_id: 任务ID
        filter_id: 过滤规则ID
        request: 更新请求
        db: 数据库会话
    
    Returns:
        更新后的过滤规则
    """
    try:
        # 验证任务是否存在
        task_repo = TaskRepository(db)
        task = task_repo.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 更新过滤规则
        filter_repo = ProblemFilterRepository(db)
        filter_rule = filter_repo.get_filter_by_id(filter_id)
        
        if not filter_rule or filter_rule.task_id != task_id:
            raise HTTPException(status_code=404, detail="过滤规则不存在")
        
        # 准备更新数据
        update_data = {}
        if request.filter_name is not None:
            update_data['filter_name'] = request.filter_name
        if request.keywords is not None:
            if len(request.keywords) == 0:
                raise HTTPException(status_code=400, detail="关键词列表不能为空")
            update_data['keywords'] = request.keywords
        if request.is_enabled is not None:
            update_data['is_enabled'] = request.is_enabled
        
        updated_filter = filter_repo.update_filter(filter_id, update_data)
        db.commit()
        
        log_info(
            f"更新过滤规则成功: filter_id={filter_id}",
            "problem_filter_api"
        )
        
        return {
            "success": True,
            "message": "过滤规则更新成功",
            "data": updated_filter.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        log_error(f"更新过滤规则失败: filter_id={filter_id}", "problem_filter_api", e)
        raise HTTPException(status_code=500, detail=f"更新过滤规则失败: {str(e)}")


@router.delete("/{task_id}/problem_filters/{filter_id}")
async def delete_filter_rule(
    task_id: int,
    filter_id: int,
    db: Session = Depends(get_db)
):
    """
    删除过滤规则
    
    Args:
        task_id: 任务ID
        filter_id: 过滤规则ID
        db: 数据库会话
    
    Returns:
        删除结果
    """
    try:
        # 验证任务是否存在
        task_repo = TaskRepository(db)
        task = task_repo.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 删除过滤规则
        filter_repo = ProblemFilterRepository(db)
        filter_rule = filter_repo.get_filter_by_id(filter_id)
        
        if not filter_rule or filter_rule.task_id != task_id:
            raise HTTPException(status_code=404, detail="过滤规则不存在")
        
        success = filter_repo.delete_filter(filter_id)
        db.commit()
        
        if success:
            log_info(f"删除过滤规则成功: filter_id={filter_id}", "problem_filter_api")
            return {
                "success": True,
                "message": "过滤规则删除成功"
            }
        else:
            return {
                "success": False,
                "message": "删除失败"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        log_error(f"删除过滤规则失败: filter_id={filter_id}", "problem_filter_api", e)
        raise HTTPException(status_code=500, detail=f"删除过滤规则失败: {str(e)}")


@router.post("/{task_id}/problem_filters/apply")
async def apply_filters_to_problems(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    将所有启用的过滤规则应用到问题上，将匹配的问题状态设置为3（已过滤）
    
    Args:
        task_id: 任务ID
        db: 数据库会话
    
    Returns:
        应用结果
    """
    try:
        # 验证任务是否存在
        task_repo = TaskRepository(db)
        task = task_repo.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 获取所有启用的过滤规则
        filter_repo = ProblemFilterRepository(db)
        enabled_filters = filter_repo.get_enabled_filters(task_id)
        
        if not enabled_filters:
            return {
                "success": True,
                "message": "没有启用的过滤规则",
                "filtered_count": 0
            }
        
        # 应用过滤规则
        filtered_count = filter_repo.apply_filters_to_problems(task_id, enabled_filters)
        
        # 更新任务的算法过滤计数（累加）
        if filtered_count > 0:
            current_count = task.algorithm_filtered_count or 0
            task.algorithm_filtered_count = current_count + filtered_count
            db.flush()
        
        db.commit()
        
        log_info(
            f"应用过滤规则成功: task_id={task_id}, 过滤了 {filtered_count} 个问题",
            "problem_filter_api"
        )
        
        return {
            "success": True,
            "message": f"过滤规则应用成功，共过滤了 {filtered_count} 个问题",
            "filtered_count": filtered_count,
            "algorithm_filtered_total": task.algorithm_filtered_count  # 返回累计的算法过滤数
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        log_error(f"应用过滤规则失败: task_id={task_id}", "problem_filter_api", e)
        raise HTTPException(status_code=500, detail=f"应用过滤规则失败: {str(e)}")


# ==================== 全局模板相关API ====================

@router.get("/filter_templates")
async def get_filter_templates(
    include_system: bool = True,
    db: Session = Depends(get_db)
):
    """
    获取所有过滤规则模板
    
    Args:
        include_system: 是否包含系统预设模板
        db: 数据库会话
    
    Returns:
        模板列表
    """
    try:
        from ...db.repository.filter_template_repo import FilterTemplateRepository
        
        template_repo = FilterTemplateRepository(db)
        templates = template_repo.get_all_templates(include_system=include_system)
        
        return {
            "success": True,
            "data": [template.to_dict() for template in templates]
        }
        
    except Exception as e:
        log_error("获取过滤规则模板失败", "problem_filter_api", e)
        raise HTTPException(status_code=500, detail=f"获取过滤规则模板失败: {str(e)}")


@router.post("/{task_id}/problem_filters/copy_from_template/{template_id}")
async def copy_filter_from_template(
    task_id: int,
    template_id: int,
    db: Session = Depends(get_db)
):
    """
    从模板复制过滤规则到任务
    
    Args:
        task_id: 任务ID
        template_id: 模板ID
        db: 数据库会话
    
    Returns:
        创建的过滤规则
    """
    try:
        from ...db.repository.filter_template_repo import FilterTemplateRepository
        
        # 验证任务是否存在
        task_repo = TaskRepository(db)
        task = task_repo.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 从模板复制规则
        template_repo = FilterTemplateRepository(db)
        filter_rule = template_repo.copy_template_to_task(template_id, task_id)
        
        db.commit()
        
        log_info(
            f"从模板复制过滤规则成功: task_id={task_id}, template_id={template_id}",
            "problem_filter_api"
        )
        
        return {
            "success": True,
            "message": "从模板复制规则成功",
            "data": filter_rule.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        log_error(f"从模板复制过滤规则失败: task_id={task_id}, template_id={template_id}", "problem_filter_api", e)
        raise HTTPException(status_code=500, detail=f"从模板复制过滤规则失败: {str(e)}")


@router.post("/{task_id}/problem_filters/init_from_system_templates")
async def init_filters_from_system_templates(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    从系统模板初始化任务的过滤规则
    
    Args:
        task_id: 任务ID
        db: 数据库会话
    
    Returns:
        创建的过滤规则列表
    """
    try:
        from ...db.repository.filter_template_repo import FilterTemplateRepository
        
        # 验证任务是否存在
        task_repo = TaskRepository(db)
        task = task_repo.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 从系统模板批量复制规则
        template_repo = FilterTemplateRepository(db)
        filter_rules = template_repo.copy_all_templates_to_task(task_id)
        
        db.commit()
        
        log_info(
            f"从系统模板初始化过滤规则成功: task_id={task_id}, 创建了 {len(filter_rules)} 条规则",
            "problem_filter_api"
        )
        
        return {
            "success": True,
            "message": f"从系统模板初始化成功，创建了 {len(filter_rules)} 条过滤规则",
            "data": [rule.to_dict() for rule in filter_rules]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        log_error(f"从系统模板初始化过滤规则失败: task_id={task_id}", "problem_filter_api", e)
        raise HTTPException(status_code=500, detail=f"从系统模板初始化过滤规则失败: {str(e)}")

