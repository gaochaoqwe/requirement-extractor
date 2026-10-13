"""
数据库管理API
提供数据库数据的查询、统计和管理接口
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional, Any
import sqlite3
from datetime import datetime, timedelta

from ..db.database_service import get_database_service, DatabaseIntegrationService

router = APIRouter(prefix="/database", tags=["Database Management"])

def get_db_service() -> DatabaseIntegrationService:
    """依赖注入：获取数据库服务"""
    service = get_database_service()
    if not service:
        raise HTTPException(status_code=500, detail="数据库服务不可用")
    return service

@router.get("/tasks", summary="获取任务列表")
async def get_tasks(
    status: Optional[str] = Query(None, description="任务状态过滤"),
    limit: int = Query(20, description="返回数量限制"),
    db_service: DatabaseIntegrationService = Depends(get_db_service)
):
    """获取任务列表"""
    try:
        # 直接查询数据库
        with sqlite3.connect(db_service.db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if status:
                cursor.execute("""
                    SELECT * FROM tasks WHERE status = ? 
                    ORDER BY created_at DESC LIMIT ?
                """, (status, limit))
            else:
                cursor.execute("""
                    SELECT * FROM tasks 
                    ORDER BY created_at DESC LIMIT ?
                """, (limit,))
            
            tasks = [dict(row) for row in cursor.fetchall()]
            return {"success": True, "data": tasks, "count": len(tasks)}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询任务失败: {str(e)}")

@router.get("/tasks/{task_id}", summary="获取任务详情")
async def get_task_detail(
    task_id: str,
    db_service: DatabaseIntegrationService = Depends(get_db_service)
):
    """获取指定任务的详细信息"""
    try:
        task_info = db_service.get_task_summary(task_id)
        if not task_info:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 获取关联的详细数据
        with sqlite3.connect(db_service.db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 获取项目信息
            cursor.execute("SELECT * FROM project_info WHERE task_id = ?", (task_id,))
            project_info = dict(cursor.fetchone()) if cursor.fetchone() else None
            cursor.execute("SELECT * FROM project_info WHERE task_id = ?", (task_id,))  # 重新查询
            project_info = dict(cursor.fetchone()) if cursor.fetchone() else None
            
            # 获取软件配置
            cursor.execute("SELECT * FROM software_config WHERE task_id = ?", (task_id,))
            software_config = dict(cursor.fetchone()) if cursor.fetchone() else None
            cursor.execute("SELECT * FROM software_config WHERE task_id = ?", (task_id,))  # 重新查询
            software_config = dict(cursor.fetchone()) if cursor.fetchone() else None
            
            # 获取需求分析
            cursor.execute("SELECT * FROM requirement_analysis WHERE task_id = ?", (task_id,))
            requirements = [dict(row) for row in cursor.fetchall()]
            
            # 获取测试用例
            cursor.execute("SELECT * FROM test_cases WHERE task_id = ?", (task_id,))
            test_cases = [dict(row) for row in cursor.fetchall()]
            
            # 获取项目策划
            cursor.execute("SELECT * FROM project_plan WHERE task_id = ?", (task_id,))
            project_plans = [dict(row) for row in cursor.fetchall()]
        
        return {
            "success": True,
            "data": {
                "task_info": task_info,
                "project_info": project_info,
                "software_config": software_config,
                "requirements": requirements,
                "test_cases": test_cases,
                "project_plans": project_plans,
                "statistics": {
                    "requirement_count": len(requirements),
                    "test_case_count": len(test_cases),
                    "plan_count": len(project_plans)
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务详情失败: {str(e)}")

@router.get("/statistics", summary="获取数据库统计信息")
async def get_statistics(
    days: int = Query(7, description="统计天数"),
    db_service: DatabaseIntegrationService = Depends(get_db_service)
):
    """获取数据库统计信息"""
    try:
        with sqlite3.connect(db_service.db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 计算时间范围
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
            
            # 任务统计
            cursor.execute("SELECT status, COUNT(*) as count FROM tasks GROUP BY status")
            task_stats = {row['status']: row['count'] for row in cursor.fetchall()}
            
            # 最近天数的任务统计
            cursor.execute("""
                SELECT status, COUNT(*) as count FROM tasks 
                WHERE created_at >= ? GROUP BY status
            """, (start_date,))
            recent_task_stats = {row['status']: row['count'] for row in cursor.fetchall()}
            
            # 需求分析统计
            cursor.execute("SELECT COUNT(*) as count FROM requirement_analysis")
            requirement_count = cursor.fetchone()['count']
            
            # 测试用例统计
            cursor.execute("SELECT COUNT(*) as count FROM test_cases")
            test_case_count = cursor.fetchone()['count']
            
            # 测试用例状态统计
            cursor.execute("SELECT test_status, COUNT(*) as count FROM test_cases GROUP BY test_status")
            test_case_status_stats = {row['test_status']: row['count'] for row in cursor.fetchall()}
            
            # 软件配置统计
            cursor.execute("SELECT COUNT(*) as count FROM software_config")
            config_count = cursor.fetchone()['count']
            
            # 项目策划统计
            cursor.execute("SELECT COUNT(*) as count FROM project_plan")
            plan_count = cursor.fetchone()['count']
        
        return {
            "success": True,
            "data": {
                "time_range": f"最近 {days} 天",
                "task_statistics": {
                    "total": task_stats,
                    "recent": recent_task_stats
                },
                "data_statistics": {
                    "requirements": requirement_count,
                    "test_cases": test_case_count,
                    "software_configs": config_count,
                    "project_plans": plan_count
                },
                "test_case_status": test_case_status_stats,
                "generated_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

@router.get("/base-data", summary="获取基础数据")
async def get_base_data(
    category: Optional[str] = Query(None, description="数据类别"),
    db_service: DatabaseIntegrationService = Depends(get_db_service)
):
    """获取基础数据（人员、领域、组件等）"""
    try:
        if category:
            data = db_service.db.get_base_data_by_category(category)
        else:
            data = db_service.get_base_data_for_frontend()
        
        return {"success": True, "data": data}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取基础数据失败: {str(e)}")

@router.post("/base-data", summary="添加基础数据")
async def add_base_data(
    category: str,
    name: str,
    description: Optional[str] = None,
    db_service: DatabaseIntegrationService = Depends(get_db_service)
):
    """添加新的基础数据"""
    try:
        success = db_service.db.add_base_data(category, name, description)
        if success:
            return {"success": True, "message": f"成功添加{category}数据: {name}"}
        else:
            raise HTTPException(status_code=400, detail="数据已存在或添加失败")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加基础数据失败: {str(e)}")

@router.get("/search", summary="搜索数据")
async def search_data(
    q: str = Query(..., description="搜索关键词"),
    table: Optional[str] = Query(None, description="指定搜索的表"),
    limit: int = Query(10, description="返回数量限制"),
    db_service: DatabaseIntegrationService = Depends(get_db_service)
):
    """在数据库中搜索数据"""
    try:
        results = {}
        
        with sqlite3.connect(db_service.db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            search_term = f"%{q}%"
            
            # 搜索任务
            if not table or table == 'tasks':
                cursor.execute("""
                    SELECT * FROM tasks 
                    WHERE task_id LIKE ? OR session_id LIKE ? OR error_message LIKE ?
                    ORDER BY created_at DESC LIMIT ?
                """, (search_term, search_term, search_term, limit))
                results['tasks'] = [dict(row) for row in cursor.fetchall()]
            
            # 搜索需求分析
            if not table or table == 'requirement_analysis':
                cursor.execute("""
                    SELECT * FROM requirement_analysis 
                    WHERE requirement_name LIKE ? OR requirement_description LIKE ? 
                    OR test_item_name LIKE ?
                    ORDER BY created_at DESC LIMIT ?
                """, (search_term, search_term, search_term, limit))
                results['requirements'] = [dict(row) for row in cursor.fetchall()]
            
            # 搜索测试用例
            if not table or table == 'test_cases':
                cursor.execute("""
                    SELECT * FROM test_cases 
                    WHERE test_case_name LIKE ? OR test_case_description LIKE ?
                    ORDER BY created_at DESC LIMIT ?
                """, (search_term, search_term, limit))
                results['test_cases'] = [dict(row) for row in cursor.fetchall()]
            
            # 搜索基础数据
            if not table or table == 'base_data':
                cursor.execute("""
                    SELECT * FROM base_data 
                    WHERE name LIKE ? OR description LIKE ?
                    ORDER BY category, name LIMIT ?
                """, (search_term, search_term, limit))
                results['base_data'] = [dict(row) for row in cursor.fetchall()]
        
        return {"success": True, "data": results, "search_term": q}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@router.delete("/tasks/{task_id}", summary="删除任务")
async def delete_task(
    task_id: str,
    db_service: DatabaseIntegrationService = Depends(get_db_service)
):
    """删除指定任务及其相关数据"""
    try:
        with sqlite3.connect(db_service.db.db_path) as conn:
            cursor = conn.cursor()
            
            # 检查任务是否存在
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE task_id = ?", (task_id,))
            if cursor.fetchone()[0] == 0:
                raise HTTPException(status_code=404, detail="任务不存在")
            
            # 删除相关数据（外键约束会自动处理）
            tables = ['test_cases', 'requirement_analysis', 'project_plan', 
                     'software_config', 'project_info', 'tasks']
            
            for table in tables:
                cursor.execute(f"DELETE FROM {table} WHERE task_id = ?", (task_id,))
            
            conn.commit()
        
        return {"success": True, "message": f"任务 {task_id} 及其相关数据已删除"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除任务失败: {str(e)}")

@router.get("/export/{task_id}", summary="导出任务数据")
async def export_task_data(
    task_id: str,
    format: str = Query("json", description="导出格式: json, csv"),
    db_service: DatabaseIntegrationService = Depends(get_db_service)
):
    """导出指定任务的完整数据"""
    try:
        # 获取任务详情
        task_detail_response = await get_task_detail(task_id, db_service)
        task_data = task_detail_response["data"]
        
        if format.lower() == "json":
            return JSONResponse(
                content=task_data,
                headers={"Content-Disposition": f"attachment; filename=task_{task_id}.json"}
            )
        elif format.lower() == "csv":
            # 这里可以实现CSV导出逻辑
            raise HTTPException(status_code=501, detail="CSV导出功能暂未实现")
        else:
            raise HTTPException(status_code=400, detail="不支持的导出格式")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出任务数据失败: {str(e)}") 