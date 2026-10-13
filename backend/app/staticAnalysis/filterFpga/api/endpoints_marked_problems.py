"""
标记问题管理API端点
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from ..database.database import get_db
from ..repositories.marked_problem_repo import MarkedProblemRepository
from ..database.postgresql_models import StaticAnalysisSession

router = APIRouter()


def get_session_id_from_task_id(db: Session, task_id: str) -> str:
    """
    将task_id（数字ID或UUID）转换为session_id（UUID）
    
    Args:
        db: 数据库会话
        task_id: 任务ID（数字ID或session_id）
    
    Returns:
        session_id: UUID格式的session_id
    
    Raises:
        HTTPException: 如果任务不存在
    """
    # 首先尝试作为数字ID查询
    session = None
    try:
        numeric_id = int(task_id)
        session = db.query(StaticAnalysisSession).filter(
            StaticAnalysisSession.id == numeric_id
        ).first()
    except (ValueError, TypeError):
        pass
    
    # 如果不是数字ID或没找到，尝试作为session_id查询
    if not session:
        session = db.query(StaticAnalysisSession).filter(
            StaticAnalysisSession.session_id == task_id
        ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return session.session_id


# 请求模型
class SaveMarkedProblemRequest(BaseModel):
    """保存标记问题的请求"""
    rule_type: str  # 'gjb' 或 'cwe'
    problem_key: str
    problem_data: Dict[str, Any]
    marked_by: Optional[str] = None


class RemoveMarkedProblemRequest(BaseModel):
    """移除标记问题的请求"""
    rule_type: str
    problem_key: str


# 响应模型
class MarkedProblemResponse(BaseModel):
    """标记问题响应"""
    id: int
    session_id: str
    rule_type: str
    problem_key: str
    problem_data: Dict[str, Any]
    marked_by: Optional[str]
    marked_at: str


@router.post("/{task_id}/marked-problems")
async def save_marked_problem(
    task_id: str,
    request: SaveMarkedProblemRequest,
    db: Session = Depends(get_db)
):
    """
    保存标记的问题
    
    Args:
        task_id: 任务ID（可以是数字ID或session_id）
        request: 保存请求
        db: 数据库会话
    
    Returns:
        标记的问题信息
    """
    try:
        # 将task_id转换为session_id（UUID）
        real_session_id = get_session_id_from_task_id(db, task_id)
        
        # 保存标记的问题
        marked_repo = MarkedProblemRepository(db)
        marked_problem = marked_repo.save_marked_problem(
            session_id=real_session_id,  # 使用UUID格式的session_id
            rule_type=request.rule_type,
            problem_key=request.problem_key,
            problem_data=request.problem_data,
            marked_by=request.marked_by
        )
        
        db.commit()
        
        print(f"[API] 保存标记问题成功: task_id={task_id}, session_id={real_session_id}, type={request.rule_type}")
        
        return {
            "success": True,
            "message": "标记问题保存成功",
            "data": marked_problem.to_dict()
        }
        
    except Exception as e:
        db.rollback()
        print(f"[API] 保存标记问题失败: {e}")
        raise HTTPException(status_code=500, detail=f"保存标记问题失败: {str(e)}")


@router.delete("/{task_id}/marked-problems")
async def remove_marked_problem(
    task_id: str,
    request: RemoveMarkedProblemRequest,
    db: Session = Depends(get_db)
):
    """
    移除标记的问题
    
    Args:
        task_id: 任务ID（可以是数字ID或session_id）
        request: 移除请求
        db: 数据库会话
    
    Returns:
        操作结果
    """
    try:
        # 将task_id转换为session_id（UUID）
        real_session_id = get_session_id_from_task_id(db, task_id)
        
        # 移除标记的问题
        marked_repo = MarkedProblemRepository(db)
        success = marked_repo.remove_marked_problem(
            session_id=real_session_id,  # 使用UUID格式的session_id
            rule_type=request.rule_type,
            problem_key=request.problem_key
        )
        
        db.commit()
        
        if success:
            print(f"[API] 移除标记问题成功: task_id={task_id}, session_id={real_session_id}, type={request.rule_type}")
            return {
                "success": True,
                "message": "标记问题移除成功"
            }
        else:
            return {
                "success": False,
                "message": "未找到要移除的标记问题"
            }
        
    except Exception as e:
        db.rollback()
        print(f"[API] 移除标记问题失败: {e}")
        raise HTTPException(status_code=500, detail=f"移除标记问题失败: {str(e)}")


@router.get("/{task_id}/marked-problems")
async def get_marked_problems(
    task_id: str,
    rule_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取任务的所有标记问题
    
    Args:
        task_id: 任务ID（可以是数字ID或session_id）
        rule_type: 规则类型（可选）
        db: 数据库会话
    
    Returns:
        标记的问题列表
    """
    try:
        # 将task_id转换为session_id（UUID）
        real_session_id = get_session_id_from_task_id(db, task_id)
        
        # 获取标记的问题
        marked_repo = MarkedProblemRepository(db)
        marked_problems = marked_repo.get_marked_problems(real_session_id, rule_type)
        
        print(f"[API] 获取标记问题: task_id={task_id}, session_id={real_session_id}, type={rule_type}, 数量={len(marked_problems)}")
        
        return {
            "success": True,
            "count": len(marked_problems),
            "data": [mp.to_dict() for mp in marked_problems]
        }
        
    except Exception as e:
        print(f"[API] 获取标记问题失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取标记问题失败: {str(e)}")


@router.get("/{task_id}/marked-problems/files")
async def get_marked_problem_files(
    task_id: str,
    rule_type: str,
    db: Session = Depends(get_db)
):
    """
    获取已标记问题所在的文件
    用于在代码树中高亮显示
    
    Args:
        task_id: 任务ID（可以是数字ID或session_id）
        rule_type: 规则类型
        db: 数据库会话
    
    Returns:
        文件信息
    """
    try:
        # 将task_id转换为session_id（UUID）
        real_session_id = get_session_id_from_task_id(db, task_id)
        
        # 获取标记文件
        marked_repo = MarkedProblemRepository(db)
        files_info = marked_repo.get_marked_files(real_session_id, rule_type)
        
        print(f"[API] 获取标记文件: task_id={task_id}, type={rule_type}, 文件数={len(files_info['files'])}")
        
        return {
            "success": True,
            "data": files_info
        }
        
    except Exception as e:
        print(f"[API] 获取标记文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取标记文件失败: {str(e)}")


@router.get("/{task_id}/marked-problems/count")
async def get_marked_problem_count(
    task_id: str,
    rule_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取标记问题的数量
    
    Args:
        task_id: 任务ID
        rule_type: 规则类型（可选）
        db: 数据库会话
    
    Returns:
        标记问题的数量
    """
    try:
        # 获取数量
        marked_repo = MarkedProblemRepository(db)
        count = marked_repo.get_marked_problem_count(task_id, rule_type)
        
        return {
            "success": True,
            "count": count
        }
        
    except Exception as e:
        print(f"[API] 获取标记问题数量失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取标记问题数量失败: {str(e)}")

