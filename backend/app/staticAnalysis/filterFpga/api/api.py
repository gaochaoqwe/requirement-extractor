"""
静态分析问题过滤工具API - 增强版本
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File, Form, Body, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import uuid
import os
import zipfile
import shutil
from pathlib import Path
import asyncio
import logging
from datetime import datetime  # [FIX] 添加datetime导入

from app.staticAnalysis.filter.database.database import get_db  # 仍然复用通用的 get_db（如有需要）
from app.staticAnalysis.filter.database.rules_database_factory import get_rules_database, get_cwe_rules_database
from app.staticAnalysis.filter.services.service import StaticAnalysisFilterService
from app.staticAnalysis.filter.services.enhanced_service import EnhancedStaticAnalysisFilterService
from app.staticAnalysis.filter.config.config import UPLOAD_DIR

# ⚠️ FPGA 代码视图和相关服务需要使用 FPGA 自己的 PostgreSQL 会话/问题表
from app.staticAnalysis.filterFpga.database.postgresql_database import get_db_session
from app.staticAnalysis.filterFpga.database.postgresql_models import StaticAnalysisSession, StaticAnalysisIssue, FPGARule  # [FIX] 提前导入FPGARule
from app.staticAnalysis.filterFpga.config.default_rules_config import (
    save_default_rules_config,
    load_default_rules_config,
    has_default_config,
    verify_admin_password
)

# 导入新的端点路由
from app.staticAnalysis.filterFpga.api.endpoints_marked_problems import router as marked_problems_router
from app.staticAnalysis.filterFpga.api.endpoints_problem_status import router as problem_status_router
from app.staticAnalysis.filterFpga.api.fpga_rules import router as fpga_rules_router
from app.staticAnalysis.filterFpga.api.fpga_processing_api import router as fpga_processing_router
from app.staticAnalysis.filter.utils.logger import setup_module_logger

router = APIRouter()

# 包含子路由
router.include_router(marked_problems_router, tags=["marked-problems"])
router.include_router(problem_status_router, tags=["problem-status"])
router.include_router(fpga_rules_router, tags=["fpga-rules"])
router.include_router(fpga_processing_router, tags=["fpga-processing"])

# 设置日志
logger = setup_module_logger(__name__, "api.log")

# 全局数据库实例
_gjb_db = get_rules_database()
_cwe_db = get_cwe_rules_database()

# 全局服务实例缓存（线程安全）
_active_services: Dict[str, StaticAnalysisFilterService] = {}
_enhanced_services: Dict[str, EnhancedStaticAnalysisFilterService] = {}

# 线程锁保护服务实例缓存
import threading
_services_lock = threading.RLock()  # 可重入锁

def get_service(session_id: str) -> StaticAnalysisFilterService:
    """获取或创建服务实例（线程安全）"""
    with _services_lock:
        if session_id not in _active_services:
            _active_services[session_id] = StaticAnalysisFilterService(session_id)
        return _active_services[session_id]

def get_enhanced_service(session_id: str) -> EnhancedStaticAnalysisFilterService:
    """获取或创建增强服务实例（线程安全）"""
    with _services_lock:
        if session_id not in _enhanced_services:
            _enhanced_services[session_id] = EnhancedStaticAnalysisFilterService(session_id)
        return _enhanced_services[session_id]

async def save_uploaded_file(file: UploadFile, session_id: str) -> str:
    """
    保存上传的Excel文件
    """
    upload_dir = UPLOAD_DIR / "staticAnalysis" / "filter"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = __import__('datetime').datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{session_id}_{timestamp}_{file.filename}"
    file_path = upload_dir / safe_filename
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    return str(file_path)

async def save_and_extract_codebase(file: UploadFile, session_id: str) -> str:
    """
    保存并解压代码库文件
    """
    upload_dir = UPLOAD_DIR / "staticAnalysis" / "filter" / "codebases"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = __import__('datetime').datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 保存压缩文件
    zip_filename = f"{session_id}_{timestamp}_{file.filename}"
    zip_path = upload_dir / zip_filename
    
    with open(zip_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # 解压到专用目录
    extract_dir = upload_dir / f"{session_id}_{timestamp}_extracted"
    extract_dir.mkdir(exist_ok=True)
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # 删除压缩文件以节省空间
        zip_path.unlink()
        
        return str(extract_dir)
    except Exception as e:
        # 如果解压失败，清理文件
        if zip_path.exists():
            zip_path.unlink()
        if extract_dir.exists():
            shutil.rmtree(extract_dir)
        raise Exception(f"解压代码库失败: {str(e)}")

@router.post("/upload")
async def upload_and_process_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    filter_keywords: Optional[str] = Form(None)
) -> Dict[str, Any]:
    """
    上传静态分析Excel文件并开始过滤处理
    """
    session_id = str(uuid.uuid4())
    
    try:
        # 创建服务实例
        service = StaticAnalysisFilterService(session_id)
        logger = service.logger
        
        logger.info(f"开始处理文件上传: {file.filename}")
        
        # 保存上传的文件
        file_path = await save_uploaded_file(file, session_id)
        logger.info(f"文件保存成功: {file_path}")
        
        # 解析过滤关键字
        keywords = []
        if filter_keywords:
            keywords = [kw.strip() for kw in filter_keywords.split(',') if kw.strip()]
        
        # 处理上传的文件（解析Excel，保存到数据库）
        result = service.process_uploaded_file(file_path, file.filename, keywords)
        
        if result["success"]:
            # 将服务实例加入全局缓存（线程安全）
            with _services_lock:
                _active_services[session_id] = service
            
            logger.info(f"文件上传成功，开始后台处理 - 会话ID: {session_id}")
            
            # 使用asyncio.create_task创建真正的异步任务，不阻塞主线程
            asyncio.create_task(process_session_in_background(session_id))
            
            return {
                "success": True,
                "session_id": session_id,
                "message": "文件上传成功，正在过滤处理中",
                "status": "processing"
            }
        else:
            logger.error(f"文件上传失败: {result.get('error')}")
            return result
            
    except Exception as e:
        error_msg = f"文件上传失败: {str(e)}"
        print(f"❌ [API] {error_msg}")
        return {"success": False, "error": error_msg}

async def process_session_in_background(session_id: str):
    """后台处理会话"""
    try:
        service = get_service(session_id)
        logger = service.logger

        logger.info(f"开始后台处理会话: {session_id}")

        # 异步处理会话
        result = await service.process_session()

        if result["success"]:
            logger.info(f"会话处理完成: {session_id} - {result['message']}")
        else:
            logger.error(f"会话处理失败: {session_id} - {result.get('error')}")

    except Exception as e:
        with _services_lock:
            if session_id in _active_services:
                logger = _active_services[session_id].logger
                logger.error(f"后台处理会话时出错: {str(e)}")

@router.get("/status/{session_id}")
def get_processing_status(session_id: str) -> Dict[str, Any]:
    """
    获取处理状态 - 使用内存变量，快速无阻塞
    """
    try:
        print(f"🔍 [API] 收到状态查询请求 - 会话ID: {session_id}")
        logger.info(f"收到状态查询请求 - 会话ID: {session_id}")
        
        # 获取服务实例（线程安全）
        with _services_lock:
            if session_id not in _active_services:
                print(f"❌ [API] 会话不存在: {session_id}")
                logger.warning(f"会话不存在: {session_id}")
                raise HTTPException(status_code=404, detail="会话不存在")
            
            service = _active_services[session_id]
        print(f"✅ [API] 找到服务实例，会话ID: {session_id}")
        
        # 使用内存状态，快速响应
        status_result = service.get_memory_status()
        print(f"📊 [API] 内存状态: {status_result}")
        logger.info(f"返回状态: {status_result}")
        
        return status_result
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"获取状态失败: {str(e)}"
        print(f"❌ [API] {error_msg}")
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/download/{session_id}")
def generate_output_file(
    session_id: str,
    rule_type: str = Body('all', embed=True),      # 'all', 'gjb', 'cwe'
    content_type: str = Body('all', embed=True)    # 'all', 'accurate', 'uncertain'
) -> Dict[str, Any]:
    """
    生成输出文件（如果尚未生成）- 支持普通和增强版
    
    请求体示例:
    {
        "rule_type": "gjb",  // 'all', 'gjb', 'cwe'
        "content_type": "accurate"  // 'all', 'accurate', 'uncertain'
    }
    """
    try:
        # 调试日志
        logger.info(f"[下载API] 请求生成输出文件: {session_id}, 规则类型:{rule_type}, 内容类型:{content_type}")
        
        # 如果传入的是数字ID，先从数据库查询真正的session_id
        resolved_session_id = session_id
        try:
            numeric_id = int(session_id)
            logger.info(f"[下载API] 检测到数字ID: {numeric_id}，尝试从数据库查询session_id")
            db = get_db_session()
            try:
                session = db.query(StaticAnalysisSession).filter(
                    StaticAnalysisSession.id == numeric_id
                ).first()
                if session:
                    resolved_session_id = session.session_id
                    logger.info(f"[下载API] 通过数字ID {numeric_id} 找到session_id: {resolved_session_id}")
                else:
                    logger.error(f"[下载API] 数字ID {numeric_id} 对应的会话不存在")
                    raise HTTPException(status_code=404, detail=f"任务ID {numeric_id} 不存在")
            finally:
                db.close()
        except (TypeError, ValueError):
            # 不是数字，直接使用原session_id
            pass
        
        # 优先检查增强服务（线程安全）
        service = None
        with _services_lock:
            logger.info(f"[下载API] 当前增强服务数量: {len(_enhanced_services)}, 会话列表: {list(_enhanced_services.keys())}")
            logger.info(f"[下载API] 当前普通服务数量: {len(_active_services)}, 会话列表: {list(_active_services.keys())}")
            
            if resolved_session_id in _enhanced_services:
                service = _enhanced_services[resolved_session_id]
                logger.info(f"[下载API] 在增强服务中找到会话: {resolved_session_id}")
            elif resolved_session_id in _active_services:
                service = _active_services[resolved_session_id]
                logger.info(f"[下载API] 在普通服务中找到会话: {resolved_session_id}")
            else:
                logger.error(f"[下载API] 会话不存在: {resolved_session_id}")
                logger.error(f"[下载API] 可用的增强会话: {list(_enhanced_services.keys())}")
                logger.error(f"[下载API] 可用的普通会话: {list(_active_services.keys())}")
                raise HTTPException(status_code=404, detail="会话不存在")
        
        # 注意：不缓存文件名，因为不同的rule_type和content_type会生成不同的文件
        
        # 生成输出文件（传递参数）
        result = service.generate_output_file(rule_type=rule_type, content_type=content_type)
        
        if result["success"]:
            service.output_filename = result["filename"]
            return {
                "success": True,
                "filename": result["filename"],
                "session_id": resolved_session_id,  # 返回真实的session_id用于构建下载URL
                "message": "输出文件生成成功"
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "生成文件失败"))
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成输出文件失败: {str(e)}")

@router.get("/download/{session_id}/{filename}")
def download_file(session_id: str, filename: str):
    """
    下载生成的文件
    """
    try:
        # 构建文件路径
        file_path = UPLOAD_DIR / "outputs" / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载文件失败: {str(e)}")

# 新增增强版API端点

@router.post("/upload-enhanced")
async def upload_enhanced_files(
    excel_file: UploadFile = File(..., description="静态分析结果Excel文件"),
    codebase_file: UploadFile = File(None, description="代码库压缩文件（可选）"),
    selected_rules: str = Form("[]", description="选中的规则列表（JSON格式）"),
    filter_keywords: Optional[str] = Form(None, description="过滤关键字"),
    custom_filters: str = Form("{}", description="自定义关键词过滤规则（JSON格式）"),
    max_issues_per_rule: int = Form(0, description="每个规则最多保留的问题数量（0表示不限制）")
) -> Dict[str, Any]:
    """
    增强版上传 - 支持Excel文件和代码库
    """
    session_id = str(uuid.uuid4())
    
    try:
        # 创建增强服务实例
        service = EnhancedStaticAnalysisFilterService(session_id)
        logger = service.logger
        
        codebase_filename = codebase_file.filename if codebase_file else "无"
        logger.info(f"开始增强版文件上传: Excel={excel_file.filename}, 代码库={codebase_filename}")
        
        # 保存Excel文件
        excel_path = await save_uploaded_file(excel_file, session_id)
        logger.info(f"Excel文件保存成功: {excel_path}")
        
        # 保存并解压代码库（如果提供）
        codebase_path = None
        if codebase_file:
            try:
                codebase_path = await save_and_extract_codebase(codebase_file, session_id)
                logger.info(f"代码库解压成功: {codebase_path}")
            except Exception as e:
                logger.error(f"代码库处理失败: {str(e)}")
                return {"success": False, "error": f"代码库处理失败: {str(e)}"}
        else:
            logger.info("未提供代码库文件，将跳过AI分析阶段")
        
        # 解析选中的规则
        rules = []
        if selected_rules:
            try:
                import json
                rules = json.loads(selected_rules)
            except Exception as e:
                logger.warning(f"解析选中规则失败: {str(e)}")
        
        # 解析过滤关键字
        keywords = []
        if filter_keywords:
            keywords = [kw.strip() for kw in filter_keywords.split(',') if kw.strip()]
        
        # 解析自定义过滤规则
        filters = {}
        if custom_filters:
            try:
                import json
                filters = json.loads(custom_filters)
                logger.info(f"解析自定义过滤规则成功: {len(filters)} 条规则")
            except Exception as e:
                logger.warning(f"解析自定义过滤规则失败: {str(e)}")
        
        # 记录问题数量限制配置
        if max_issues_per_rule > 0:
            logger.info(f"每个规则最多保留 {max_issues_per_rule} 个问题")
        else:
            logger.info("不限制每个规则的问题数量")
        
        # 将服务实例加入全局缓存（线程安全）
        with _services_lock:
            _enhanced_services[session_id] = service
        
        logger.info(f"增强版文件上传成功，开始后台处理 - 会话ID: {session_id}")
        
        # [OK] 使用asyncio.create_task创建真正的异步后台任务
        # 这样GJB和CWE可以并行处理，不会相互阻塞
        asyncio.create_task(
            process_enhanced_session_in_background_async(
                session_id, excel_path, excel_file.filename, codebase_path, rules, keywords, filters, max_issues_per_rule
            )
        )
        
        # [INFO] 立即返回响应，避免前端超时
        response_data = {
            "success": True,
            "session_id": session_id,
            "message": "文件上传成功，正在进行增强处理中",
            "status": "uploading",
            "total_issues": 0,  # 初始为0，后台处理后更新
            "has_codebase": codebase_path is not None
        }
        
        logger.info(f"[START] 立即返回响应，任务将在后台执行 - 会话ID: {session_id}")
        
        return response_data
            
    except Exception as e:
        error_msg = f"增强版文件上传失败: {str(e)}"
        print(f"[ERROR] [API] {error_msg}")
        return {"success": False, "error": error_msg}

async def process_enhanced_session_in_background_async(
    session_id: str, 
    excel_path: str, 
    original_filename: str, 
    codebase_path: Optional[str], 
    rules: list, 
    keywords: list,
    custom_filters: dict = None,
    max_issues_per_rule: int = 0
):
    """后台处理增强会话（异步版本，用于FastAPI BackgroundTasks）"""
    try:
        service = get_enhanced_service(session_id)
        logger = service.logger

        logger.info(f"开始后台增强处理会话: {session_id}")
        
        # 在后台任务中处理上传文件（同步操作）
        result = service.process_uploaded_files(excel_path, original_filename, codebase_path, rules, keywords, custom_filters, max_issues_per_rule)
        
        if not result["success"]:
            logger.error(f"处理上传文件失败: {result.get('error')}")
            return

        logger.info(f"上传文件处理完成，发现{result.get('total_issues', 0)}个问题")

        # [OK] 直接await异步函数，不使用asyncio.run
        # 这样可以保持事件循环的一致性，确保并行处理正常工作
        result = await service.process_session_enhanced()

        if result["success"]:
            logger.info(f"增强会话处理完成: {session_id} - {result['message']}")
        else:
            logger.error(f"增强会话处理失败: {session_id} - {result.get('error')}")

    except Exception as e:
        with _services_lock:
            if session_id in _enhanced_services:
                logger = _enhanced_services[session_id].logger
                logger.error(f"后台增强处理会话时出错: {str(e)}")
        import traceback
        print(f"[ERROR] [后台任务] 处理会话{session_id}时出错: {str(e)}")
        print(traceback.format_exc())

@router.get("/status-enhanced/{session_id}")
def get_enhanced_processing_status(session_id: str) -> Dict[str, Any]:
    """
    获取增强处理状态
    """
    try:
        logger.info(f"[详细状态API] Session: {session_id}")
        
        # 获取增强服务实例（线程安全）
        with _services_lock:
            if session_id not in _enhanced_services:
                logger.warning(f"[详细状态API] 会话不存在: {session_id}")
                raise HTTPException(status_code=404, detail="会话不存在")
            
            service = _enhanced_services[session_id]
        
        # 使用get_detailed_status()获取GJB和CWE的分离状态
        detailed_status = service.get_detailed_status()
        
        logger.info(f"[详细状态API] GJB Status: {detailed_status['gjb']['status']}")
        logger.info(f"[详细状态API] CWE Status: {detailed_status['cwe']['status']}")
        
        # 验证返回数据格式
        if 'gjb' in detailed_status and 'cwe' in detailed_status:
            logger.info(f"[详细状态API] 返回数据包含status字段: GJB={detailed_status['gjb'].get('status')}, CWE={detailed_status['cwe'].get('status')}")
        
        return detailed_status
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"获取增强状态失败: {str(e)}"
        logger.error(f"[详细状态API] {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/rules/statistics")
def get_rules_statistics() -> Dict[str, Any]:
    """
    获取规则统计信息
    """
    try:
        rules_db = get_rules_database()
        stats = rules_db.get_statistics()
        
        return {
            "success": True,
            "statistics": stats
        }
    except Exception as e:
        error_msg = f"获取规则统计失败: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/rules/{accuracy_type}")
def get_rules_by_type(accuracy_type: str) -> Dict[str, Any]:
    """
    根据准确性类型获取规则列表
    """
    try:
        if accuracy_type not in ['accurate', 'uncertain', 'all']:
            raise HTTPException(status_code=400, detail="无效的准确性类型")
        
        rules_db = get_rules_database()
        
        if accuracy_type == 'all':
            rules = rules_db.get_all_rules()
        else:
            rules = rules_db.get_all_rules(accuracy_type)
        
        return {
            "success": True,
            "rules": rules,
            "count": len(rules)
        }
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"获取规则列表失败: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/health")
def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "static_analysis_filter"}

# ==================== CWE规则相关API ====================

@router.get("/rules/cwe/{accuracy_type}")
def get_cwe_rules_by_type(accuracy_type: str) -> Dict[str, Any]:
    """
    获取CWE规则列表
    
    Args:
        accuracy_type: 'accurate' 或 'uncertain'
    """
    try:
        if accuracy_type not in ['accurate', 'uncertain']:
            raise HTTPException(status_code=400, detail="accuracy_type必须是'accurate'或'uncertain'")
        
        rules = _cwe_db.get_rules_by_type(accuracy_type)
        
        return {
            "success": True,
            "rules": rules,
            "count": len(rules),
            "accuracy_type": accuracy_type
        }
    except Exception as e:
        logger.error(f"获取CWE规则失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取CWE规则失败: {str(e)}")

@router.get("/rules/cwe/statistics")
def get_cwe_statistics() -> Dict[str, Any]:
    """获取CWE规则统计信息"""
    try:
        stats = _cwe_db.get_statistics()
        return {
            "success": True,
            **stats
        }
    except Exception as e:
        logger.error(f"获取CWE统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取CWE统计信息失败: {str(e)}")

@router.get("/session/{session_id}/task-id")
def get_task_id_by_session(session_id: str) -> Dict[str, Any]:
    """
    通过session_id获取对应的task_id
    
    Args:
        session_id: 会话ID (UUID)
    
    Returns:
        包含task_id的响应
    """
    try:
        db = get_db_session()
        try:
            # 先尝试作为UUID查询
            session = db.query(StaticAnalysisSession).filter(
                StaticAnalysisSession.session_id == session_id
            ).first()
            
            if not session:
                # 尝试作为数字ID查询
                try:
                    numeric_id = int(session_id)
                    session = db.query(StaticAnalysisSession).filter(
                        StaticAnalysisSession.id == numeric_id
                    ).first()
                except (TypeError, ValueError):
                    pass
            
            if not session:
                raise HTTPException(status_code=404, detail="会话不存在")
            
            return {
                "success": True,
                "session_id": session.session_id,
                "task_id": session.id,
                "message": "获取任务ID成功"
            }
            
        finally:
            db.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务ID失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取任务ID失败: {str(e)}")

@router.get("/task/{task_id}/session")
def get_session_by_task_id(task_id: int) -> Dict[str, Any]:
    """
    通过task_id获取对应的session_id（反向查询）
    
    Args:
        task_id: 任务ID (数字)
        
    Returns:
        {
            "success": True,
            "session_id": "uuid-string",
            "task_id": 123,
            "message": "获取会话ID成功"
        }
    """
    try:
        db = get_db_session()
        try:
            session = db.query(StaticAnalysisSession).filter(
                StaticAnalysisSession.id == task_id
            ).first()
            
            if not session:
                raise HTTPException(status_code=404, detail="任务不存在")
            
            return {
                "success": True,
                "session_id": session.session_id,
                "task_id": session.id,
                "message": "获取会话ID成功"
            }
            
        finally:
            db.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话ID失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取会话ID失败: {str(e)}")

@router.get("/status/{session_id}/detailed")
def get_detailed_status(session_id: str) -> Dict[str, Any]:
    """
    获取FPGA详细状态
    
    Returns:
        {
            "success": true,
            "session_id": "xxx",
            "fpga": {
                "status": "completed",
                "progress": 100,
                "total_issues": 10,
                "accurate_issues": 6,
                "uncertain_issues": 4,
                "processed_issues": 4,
                "filtered_issues": 2,
                "current_analyzing_issue": "...",
                "tool_calls_count": 15,
                "accurate_ready": true
            }
        }
    """
    try:
        logger.info(f"[DEBUG][详细状态API] 收到请求: session_id={session_id}")
        
        # 尝试获取增强服务
        service = None
        actual_session_id = session_id
        resolved_session_id = None
        numeric_id = None

        with _services_lock:
            service = _enhanced_services.get(session_id)
            logger.info(f"[DEBUG][详细状态API] 直接查询内存缓存: service={'找到' if service else '未找到'}")

        if service is None:
            try:
                numeric_id = int(session_id)
                logger.info(f"[DEBUG][详细状态API] 解析为数字ID: numeric_id={numeric_id}")
            except (TypeError, ValueError):
                numeric_id = None
                logger.info(f"[DEBUG][详细状态API] 不是数字ID，跳过数字查询")

            if numeric_id is not None:
                db = get_db_session()
                logger.info(f"[DEBUG][详细状态API] 数据库连接对象: {db}")
                try:
                    logger.info(f"[DEBUG][详细状态API] 尝试用数字ID查询数据库: id={numeric_id}")
                    
                    # 先查询所有会话看看数据库中有什么
                    all_sessions = db.query(StaticAnalysisSession).all()
                    logger.info(f"[DEBUG][详细状态API] 数据库中所有会话: {[(s.id, s.session_id[:8]) for s in all_sessions]}")
                    
                    session_obj = db.query(StaticAnalysisSession).filter(
                        StaticAnalysisSession.id == numeric_id
                    ).first()
                    if session_obj:
                        resolved_session_id = session_obj.session_id
                        logger.info(f"[DEBUG][详细状态API] 数据库查询成功: session_id={resolved_session_id}")
                    else:
                        logger.info(f"[DEBUG][详细状态API] 数据库查询失败: 未找到id={numeric_id}的记录")
                finally:
                    db.close()

            if resolved_session_id:
                actual_session_id = resolved_session_id
                with _services_lock:
                    service = _enhanced_services.get(resolved_session_id)
                    logger.info(f"[DEBUG][详细状态API] 用UUID查询内存缓存: service={'找到' if service else '未找到'}")

        if not service:
            # 如果内存中没有服务实例，尝试从数据库读取已完成任务的状态
            logger.info(f"[DEBUG][详细状态API] 内存中没有服务实例，尝试从数据库读取")
            db = get_db_session()
            try:
                session_obj = None
                
                # 优先用数字ID查询（如果传入的是数字）
                if numeric_id is not None:
                    logger.info(f"[DEBUG][详细状态API] 第二次数据库查询（数字ID）: id={numeric_id}")
                    session_obj = db.query(StaticAnalysisSession).filter(
                        StaticAnalysisSession.id == numeric_id
                    ).first()
                    if session_obj:
                        logger.info(f"[DEBUG][详细状态API] 第二次查询成功: session_id={session_obj.session_id}, status={session_obj.status}")
                    else:
                        logger.info(f"[DEBUG][详细状态API] 第二次数字ID查询失败")
                
                # 如果数字ID查询失败，尝试用UUID查询
                if not session_obj:
                    query_session_id = resolved_session_id if resolved_session_id else session_id
                    logger.info(f"[DEBUG][详细状态API] 尝试UUID查询: session_id={query_session_id}")
                    session_obj = db.query(StaticAnalysisSession).filter(
                        StaticAnalysisSession.session_id == query_session_id
                    ).first()
                    if session_obj:
                        logger.info(f"[DEBUG][详细状态API] UUID查询成功: id={session_obj.id}")
                    else:
                        logger.info(f"[DEBUG][详细状态API] UUID查询失败")
                
                if not session_obj:
                    logger.error(f"[DEBUG][详细状态API] 数据库中未找到会话: session_id={session_id}, numeric_id={numeric_id}")
                    raise HTTPException(status_code=404, detail="会话不存在")
                
                # 从数据库构建静态状态（已完成FPGA任务）
                # 先从session表读取基础数据
                total = session_obj.total_issues or 0
                filtered = session_obj.filtered_issues or 0
                
                # 从Issue表实时统计问题数（更准确）
                from app.staticAnalysis.filterFpga.database.postgresql_models import StaticAnalysisIssue
                try:
                    # 统计accurate问题数
                    accurate = db.query(StaticAnalysisIssue).filter(
                        StaticAnalysisIssue.task_id == session_obj.id,
                        StaticAnalysisIssue.rule_accuracy_type == 'accurate'
                    ).count()
                    
                    # 统计uncertain问题总数
                    uncertain = db.query(StaticAnalysisIssue).filter(
                        StaticAnalysisIssue.task_id == session_obj.id,
                        StaticAnalysisIssue.rule_accuracy_type == 'uncertain'
                    ).count()
                    
                    # 统计AI已审查的不确定问题数（关键！只统计uncertain类型的）
                    ai_analyzed_count = db.query(StaticAnalysisIssue).filter(
                        StaticAnalysisIssue.task_id == session_obj.id,
                        StaticAnalysisIssue.rule_accuracy_type == 'uncertain',
                        StaticAnalysisIssue.ai_analyzed == True
                    ).count()
                    
                    logger.info(f"[DEBUG][详细状态API] 从Issue表统计: accurate={accurate}, uncertain={uncertain}, "
                               f"ai_analyzed={ai_analyzed_count}")
                except Exception as count_error:
                    logger.error(f"[DEBUG][详细状态API] 统计问题数失败: {count_error}")
                    # 回退到session表的值
                    accurate = session_obj.accurate_issues or 0
                    uncertain = session_obj.uncertain_issues or 0
                    ai_analyzed_count = session_obj.ai_analyzed_issues or 0
                
                # processed_issues = accurate + ai_analyzed的不确定问题数
                # 注意：确定问题不需要AI审查，直接算已处理；不确定问题需要AI审查才算已处理
                processed = accurate + ai_analyzed_count
                
                logger.info(f"[DEBUG][详细状态API] 构建FPGA状态: total={total}, accurate={accurate}, "
                           f"uncertain={uncertain}, ai_analyzed={ai_analyzed_count}, processed={processed}, filtered={filtered}")
                
                # FPGA只有一种规则类型（FPGA规则），分为accurate和uncertain
                detailed_status = {
                    "fpga": {
                        "status": "completed",
                        "progress": 0,  # 前端会重新计算
                        "total_issues": total,
                        "accurate_issues": accurate,
                        "uncertain_issues": uncertain,
                        "processed_issues": processed,  # accurate + AI已审查的不确定问题数
                        "filtered_issues": filtered,
                        "current_analyzing_issue": "",
                        "tool_calls_count": 0,
                        "accurate_ready": True,
                        "ai_processing_total": uncertain,
                        "uncertain_selected_issues": uncertain
                    }
                }
                logger.info(f"[DEBUG][详细状态API] 构建完成，准备返回")
            finally:
                db.close()
        else:
            # 获取详细状态（从内存服务实例）
            # FPGA使用get_progress()方法，返回单个进度对象
            fpga_progress = service.get_progress()
            detailed_status = {
                "fpga": fpga_progress
            }
            logger.info(f"[DEBUG][详细状态API] 从内存获取FPGA进度: {fpga_progress}")
        
        # 调试日志：打印详细状态
        logger.info(f"[详细状态API] Session: {actual_session_id}")
        logger.info(f"[详细状态API] FPGA Status: {detailed_status.get('fpga', {}).get('status', 'N/A')}")
        
        result = {
            "success": True,
            "session_id": session_id,
            **detailed_status
        }
        
        logger.info(f"[详细状态API] 返回数据包含status字段: FPGA={('status' in result.get('fpga', {}))}")
        logger.info(f"[详细状态API] FPGA进度: {result.get('fpga', {}).get('progress', 0)}%")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取详细状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取详细状态失败: {str(e)}")

# === 默认规则配置管理API ===

@router.post("/rules/config/save")
def save_default_config(
    gjb_rules: List[str] = Body(..., embed=True),
    cwe_rules: List[str] = Body(..., embed=True),
    rule_overrides: Dict[str, Dict[str, str]] = Body(None, embed=True),
    custom_filters: Dict[str, List[str]] = Body(None, embed=True),
    max_issues_per_rule: int = Body(0, embed=True)
) -> Dict[str, Any]:
    """
    保存默认规则配置（需要管理员密码）
    
    请求体:
    {
        "password": "159357",
        "gjb_rules": ["GJB_R_01_01_01", ...],
        "cwe_rules": ["S_01_01", ...],
        "rule_overrides": {
            "gjb": {"GJB_R_01_07_11": "uncertain"},
            "cwe": {"S_01_01": "accurate"}
        }
    }
    """
    try:
        logger.info(f"[配置API] 收到保存默认规则配置请求")
        logger.info(f"[配置API] GJB规则数: {len(gjb_rules)}, CWE规则数: {len(cwe_rules)}")
        
        if rule_overrides:
            gjb_override_count = len(rule_overrides.get("gjb", {}))
            cwe_override_count = len(rule_overrides.get("cwe", {}))
            logger.info(f"[配置API] 规则分类覆盖: GJB={gjb_override_count}, CWE={cwe_override_count}")
        
        if custom_filters:
            logger.info(f"[配置API] 自定义过滤规则数: {len(custom_filters)}")
            for rule_code, keywords in custom_filters.items():
                logger.info(f"[配置API] 自定义过滤: {rule_code} -> {keywords}")
        
        if max_issues_per_rule > 0:
            logger.info(f"[配置API] 问题数量限制: 每个规则最多保留 {max_issues_per_rule} 个问题")
        else:
            logger.info(f"[配置API] 问题数量限制: 不限制")
        
        # 如果有规则覆盖，先应用到数据库（FPGA专用）
        if rule_overrides:
            from app.staticAnalysis.filterFpga.config.default_rules_config import apply_rule_overrides_to_database
            logger.info(f"[配置API] 开始应用规则分类覆盖到数据库")
            
            db_success = apply_rule_overrides_to_database(rule_overrides)
            if not db_success:
                logger.error(f"[配置API] 应用规则覆盖到数据库失败")
                raise HTTPException(status_code=500, detail="应用规则分类覆盖到数据库失败")
            
            logger.info(f"[配置API] 规则分类覆盖已应用到数据库")
        
        # 保存配置到JSON文件
        success = save_default_rules_config(gjb_rules, cwe_rules, rule_overrides, custom_filters, max_issues_per_rule)
        
        # [NEW] 保存勾选状态到数据库（FPGA专用）
        logger.info(f"[配置API] 开始保存勾选状态到数据库")
        from app.staticAnalysis.filterFpga.config.default_rules_config import save_selected_rules_to_database
        db_save_success = save_selected_rules_to_database(gjb_rules)
        if db_save_success:
            logger.info(f"[配置API] 勾选状态已保存到数据库: {len(gjb_rules)} 条规则")
        else:
            logger.error(f"[配置API] 保存勾选状态到数据库失败")
        
        if success:
            logger.info(f"[配置API] 默认规则配置保存成功")
            
            response = {
                "success": True,
                "message": "默认规则配置已保存",
                "gjb_rules_count": len(gjb_rules),
                "cwe_rules_count": len(cwe_rules),
                "db_saved": db_save_success
            }
            
            if rule_overrides:
                response["rule_overrides_applied"] = {
                    "gjb": len(rule_overrides.get("gjb", {})),
                    "cwe": len(rule_overrides.get("cwe", {}))
                }
            
            if custom_filters:
                response["custom_filters_count"] = len(custom_filters)
            
            if max_issues_per_rule > 0:
                response["max_issues_per_rule"] = max_issues_per_rule
            
            return response
        else:
            raise HTTPException(status_code=500, detail="保存配置失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[配置API] 保存配置时出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"保存配置失败: {str(e)}")

@router.get("/rules/config/load")
def load_default_config() -> Dict[str, Any]:
    """
    加载默认规则配置
    
    返回:
    {
        "success": true,
        "has_config": true,
        "gjb_rules": [...],
        "cwe_rules": [...],
        "rule_overrides": {...}
    }
    """
    try:
        logger.info(f"[配置API] 收到加载默认规则配置请求")
        
        config = load_default_rules_config()
        has_config = has_default_config()
        
        rule_overrides = config.get("rule_overrides", {"gjb": {}, "cwe": {}})
        gjb_override_count = len(rule_overrides.get("gjb", {}))
        cwe_override_count = len(rule_overrides.get("cwe", {}))
        
        custom_filters = config.get("custom_filters", {})
        max_issues_per_rule = config.get("max_issues_per_rule", 0)
        
        # [NEW] 优先从数据库加载勾选状态（FPGA专用）
        logger.info(f"[配置API] 尝试从数据库加载勾选状态")
        from app.staticAnalysis.filterFpga.config.default_rules_config import load_selected_rules_from_database
        db_selected_rules = load_selected_rules_from_database()
        
        if db_selected_rules:
            # 如果数据库有勾选数据，优先使用数据库的
            logger.info(f"[配置API] 使用数据库勾选状态: {len(db_selected_rules)} 条规则")
            gjb_rules = db_selected_rules
            source = "database"
        else:
            # 数据库没有数据，回退到配置文件
            logger.info(f"[配置API] 数据库无勾选数据，使用配置文件")
            gjb_rules = config["gjb_rules"]
            source = "config_file"
        
        logger.info(f"[配置API] 配置存在: {has_config}, GJB规则数: {len(gjb_rules)}, CWE规则数: {len(config['cwe_rules'])}, 来源: {source}")
        logger.info(f"[配置API] 规则分类覆盖: GJB={gjb_override_count}, CWE={cwe_override_count}")
        logger.info(f"[配置API] 自定义过滤规则数: {len(custom_filters)}")
        logger.info(f"[配置API] 问题数量限制: {max_issues_per_rule if max_issues_per_rule > 0 else '不限制'}")
        
        return {
            "success": True,
            "has_config": has_config,
            "gjb_rules": gjb_rules,
            "cwe_rules": config["cwe_rules"],
            "rule_overrides": rule_overrides,
            "custom_filters": custom_filters,
            "max_issues_per_rule": max_issues_per_rule,
            "source": source
        }
    except Exception as e:
        logger.error(f"[配置API] 加载配置时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"加载配置失败: {str(e)}")

# === 代码视图API ===

@router.get("/code-view/{task_id}")
def get_code_view_data(
    task_id: str,
    rule_type: str = Query('fpga', description="规则类型: fpga")
) -> Dict[str, Any]:
    """
    获取代码视图数据（文件树、问题列表、规则信息）
    
    Args:
        task_id: 任务ID（支持UUID或整数ID）
        rule_type: 规则类型，默认为'fpga'
    
    Returns:
        {
            "success": bool,
            "data": {
                "files": [...],
                "problems": [...],
                "selected_rules": [...],
                "rules": [...]
                    {
                        "id": 1,
                        "issue_name": "...",
                        "issue_file": "...",
                        "issue_line": "...",
                        "issue_description": "...",
                        "rule_code": "...",
                        "rule_type": "gjb",
                        "rule_accuracy_type": "accurate",
                        ...
                    },
                    ...
                ]
            }
        }
    """
    print(f"[FPGA代码视图API] ===== 收到请求 ===== task_id={task_id}")
    try:
        logger.info(f"[代码视图API] 获取代码视图数据: task_id={task_id}, rule_type={rule_type}")
        print(f"[FPGA代码视图API] 开始处理...")
        
        # 1. 查询session信息
        db = get_db_session()
        try:
            session = None
            numeric_task_id: Optional[int] = None
            try:
                numeric_task_id = int(task_id)
            except (TypeError, ValueError):
                numeric_task_id = None

            if numeric_task_id is not None:
                session = db.query(StaticAnalysisSession).filter(
                    StaticAnalysisSession.id == numeric_task_id
                ).first()

            if not session:
                session = db.query(StaticAnalysisSession).filter(
                    StaticAnalysisSession.session_id == task_id
                ).first()
            
            if not session:
                raise HTTPException(status_code=404, detail="任务不存在")
            
            # 获取任务ID（用于查询issues）
            db_task_id = session.id
            
            if not session.codebase_path:
                raise HTTPException(status_code=400, detail="该会话没有上传代码库")
            
            codebase_path = session.codebase_path
            logger.info(f"[代码视图API] 代码库路径: {codebase_path}")
            
            # 2. 扫描代码库zip中的文件（FPGA: Verilog/VHDL）
            files_data = []
            try:
                import zipfile
                supported_extensions = {'.v', '.sv', '.vh', '.svh', '.vhd', '.vhdl'}
                with zipfile.ZipFile(codebase_path, 'r') as z:
                    entries = z.namelist()
                    for entry in entries:
                        # 忽略目录
                        if entry.endswith('/'):
                            continue
                        # 过滤扩展名
                        import os as _os
                        ext = _os.path.splitext(entry)[1].lower()
                        if ext not in supported_extensions:
                            continue
                        # 尝试多种编码解码文件内容
                        content = None
                        raw_bytes = z.read(entry)
                        encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin-1']
                        
                        for encoding in encodings:
                            try:
                                content = raw_bytes.decode(encoding)
                                # 如果成功解码，跳出循环
                                break
                            except (UnicodeDecodeError, LookupError):
                                continue
                        
                        # 如果所有编码都失败，使用UTF-8并替换错误字符
                        if content is None:
                            try:
                                content = raw_bytes.decode('utf-8', errors='replace')
                            except Exception:
                                # 跳过无法解码的文件
                                continue
                        file_name = entry.split('/')[-1]
                        rel_path = entry  # zip内相对路径
                        files_data.append({
                            "file_name": file_name,
                            "file_path": rel_path,
                            "source_code": content
                        })
                logger.info(f"[代码视图API] 扫描到 {len(files_data)} 个FPGA代码文件")
            except Exception as zerr:
                logger.error(f"[代码视图API] 读取代码库zip失败: {zerr}")
                files_data = []
            
            # 3. 查询所有问题（包括AI过滤的问题，在前端用特殊颜色标记）
            # FPGA问题的rule_type实际上是'gjb'，因为FPGA复用了GJB规则体系
            issues = db.query(StaticAnalysisIssue).filter(
                StaticAnalysisIssue.task_id == db_task_id
            ).all()
            
            # [NEW] 为每个问题组装问题单格式（四段式）
            def strip_leading_suggestion_fpga(s: str) -> str:
                """去除建议前缀"""
                t = (s or '').strip()
                if t.startswith('建议'):
                    return t[2:].lstrip('：: \u3000')
                if t.startswith('修改意见：'):
                    return t[5:]
                if t.startswith('修改意见:'):
                    return t[4:]
                return t
            
            # 转换为字典格式，并添加问题单内容
            problems_data = []
            for issue in issues:
                # 查询规则库获取规则详情
                rule_problem_name = ''
                rule_requirement = ''
                rule_impact = ''
                rule_suggestion = ''
                
                if issue.rule_code:
                    try:
                        r = db.query(FPGARule).filter(FPGARule.rule_code == issue.rule_code).first()
                        if r:
                            # [FIX] FPGA规则表使用不同的字段名
                            rule_problem_name = getattr(r, 'issue_title', '') or ''
                            rule_requirement = getattr(r, 'rule_content', '') or ''  # FPGA用rule_content作为需求描述
                            rule_impact = getattr(r, 'impact_analysis', '') or ''
                            rule_suggestion = getattr(r, 'fix_suggestion', '') or ''  # FPGA用fix_suggestion
                        else:
                            print(f"[DEBUG FPGA规则库] 未找到规则: rule_code={issue.rule_code}")
                    except Exception as e:
                        logger.warning(f"[FPGA代码视图API] 查询规则失败: {issue.rule_code}, {e}")
                
                # 组装问题单内容
                issue_name = rule_problem_name or issue.issue_name or ''
                file_path = issue.issue_file or ''
                line_number = issue.issue_line or ''
                defect_desc = issue.issue_description or ''
                problem_source = f"{file_path}文件{line_number}行" if file_path and line_number else "代码文件"
                
                # 四段式
                guifan = 'FPGA'
                xuqiu_miaoshu = f"根据{guifan}编码规范要求{issue.rule_code}条规定：{rule_requirement}".strip()
                four_part = (
                    f"需求描述：{xuqiu_miaoshu}。\n"
                    f"问题描述：{issue_name}。\n"
                    f"问题定位：{problem_source}，具体内容如下：\"{defect_desc}\"。\n"
                    f"影响分析：{rule_impact}"
                ).replace('。。', '。')
                
                # 测评单位意见
                sug_core = strip_leading_suggestion_fpga(rule_suggestion)
                test_unit_opinion = (
                    "1.请确认是否是问题\n"
                    f"2. 若是问题，建议{sug_core}"
                )
                
                problems_data.append({
                    "id": issue.id,
                    "issue_name": issue_name,  # [FIXED] 使用规则库的问题名称
                    "issue_file": issue.issue_file,
                    "issue_line": issue.issue_line,
                    "issue_description": issue.issue_description,
                    "rule_code": issue.rule_code,
                    "rule_type": issue.rule_type,
                    "rule_accuracy_type": issue.rule_accuracy_type,
                    "is_filtered": issue.is_filtered,
                    "ai_analyzed": issue.ai_analyzed,
                    "ai_is_real_issue": issue.ai_is_real_issue,
                    "ai_confidence": issue.ai_confidence,
                    "ai_analysis_result": issue.ai_analysis_result,
                    # [NEW] 问题单格式内容
                    "problem_sheet": {
                        "issue_name": issue_name,  # 问题名称
                        "four_part_description": four_part,  # 问题描述（四段式）
                        "test_unit_opinion": test_unit_opinion  # 测评单位意见
                    }
                })
            
            logger.info(f"[代码视图API] 查询到 {len(problems_data)} 个问题（包含AI过滤的）")
            print(f"[FPGA代码视图API] 查询到 {len(problems_data)} 个问题（包含AI过滤的）")
            
            # 统计问题的accuracy_type和AI过滤情况
            problem_accuracy_stats = {}
            ai_filtered_count = 0
            for p in problems_data:
                acc_type = p.get('rule_accuracy_type', 'unknown')
                problem_accuracy_stats[acc_type] = problem_accuracy_stats.get(acc_type, 0) + 1
                # 统计AI过滤的问题
                if p.get('rule_accuracy_type') == 'uncertain' and p.get('ai_analyzed') and not p.get('ai_is_real_issue'):
                    ai_filtered_count += 1
            logger.info(f"[代码视图API] 问题accuracy_type统计: {problem_accuracy_stats}, AI过滤: {ai_filtered_count}")
            print(f"[FPGA代码视图API] 问题统计 - accuracy: {problem_accuracy_stats}, AI过滤: {ai_filtered_count}")
            
            # 4. 获取用户选中的规则列表（从数据库读取）
            # [FIX] 改为从数据库读取勾选状态，而不是配置文件
            # [NOTE] 使用全局导入的 FPGARule
            db_selected_rules = db.query(FPGARule.rule_code).filter(
                FPGARule.is_selected == True
            ).all()
            selected_rules = set([r[0] for r in db_selected_rules])
            
            logger.info(f"[代码视图API] 从数据库读取勾选规则数量: {len(selected_rules)}")
            
            # 5. 提取当前问题涉及的所有规则，并获取规则详细信息
            rule_codes_in_problems = set(problem.get('rule_code') for problem in problems_data if problem.get('rule_code'))
            
            # 从FPGA规则数据库获取规则详情
            from ..database.postgresql_rules_database import PostgreSQLFPGARulesDatabase
            rules_db = PostgreSQLFPGARulesDatabase()
            rules_info = []
            
            # 统计每个规则对应的问题数量
            rule_problem_count = {}
            for problem in problems_data:
                rule_code = problem.get('rule_code')
                if rule_code:
                    rule_problem_count[rule_code] = rule_problem_count.get(rule_code, 0) + 1
            
            # [NEW] 统计每个规则下AI确认的问题数量（用于过滤后问题分类）
            rule_ai_confirmed_count = {}
            for problem in problems_data:
                rule_code = problem.get('rule_code')
                if rule_code and problem.get('rule_accuracy_type') == 'uncertain' and problem.get('ai_is_real_issue') is True:
                    rule_ai_confirmed_count[rule_code] = rule_ai_confirmed_count.get(rule_code, 0) + 1
            
            logger.info(f"[代码视图API] 需要查询的规则: {rule_codes_in_problems}")
            print(f"[FPGA代码视图API] 需要查询的规则: {rule_codes_in_problems}")
            
            for rule_code in rule_codes_in_problems:
                rule_info = rules_db.get_rule_by_code(rule_code)
                
                if rule_info:
                    accuracy = rule_info.get('accuracy_type', 'uncertain')
                    is_selected = rule_info.get('is_selected', True)  # 从数据库获取勾选状态
                    problem_count = rule_problem_count.get(rule_code, 0)
                    ai_confirmed_count = rule_ai_confirmed_count.get(rule_code, 0)
                    
                    # [NEW] 判断该规则是否属于过滤后问题：
                    # 1. 确定规则且被勾选
                    # 2. 不确定规则、被勾选且有AI确认的问题
                    is_in_filtered = False
                    filtered_badge = None  # 标记类型: 'accurate' 或 'ai_confirmed'
                    
                    if is_selected:
                        if accuracy == 'accurate':
                            is_in_filtered = True
                            filtered_badge = 'accurate'
                        elif accuracy == 'uncertain' and ai_confirmed_count > 0:
                            is_in_filtered = True
                            filtered_badge = 'ai_confirmed'
                    
                    rules_info.append({
                        'rule_code': rule_info.get('rule_code'),
                        'rule_name': rule_info.get('rule_name') or rule_info.get('rule_description', ''),
                        'rule_description': rule_info.get('rule_description', ''),
                        'rule_type': 'gjb',  # FPGA使用GJB规则
                        'accuracy_type': accuracy,
                        'is_selected': is_selected,  # 新增：返回勾选状态
                        'problem_count': problem_count,
                        'ai_confirmed_count': ai_confirmed_count,  # [NEW] AI确认的问题数
                        'is_in_filtered': is_in_filtered,  # [NEW] 是否属于过滤后问题
                        'filtered_badge': filtered_badge  # [NEW] 过滤后问题的标记类型
                    })
                    print(f"[FPGA代码视图API] ✓ 规则 {rule_code}: accuracy_type={accuracy}, is_in_filtered={is_in_filtered}, badge={filtered_badge}")
                else:
                    # 如果数据库中没有该规则，使用基本信息
                    logger.warning(f"[代码视图API] 规则数据库中未找到规则: {rule_code}")
                    print(f"[FPGA代码视图API] ✗ 规则 {rule_code} 未找到，使用默认值")
                    rules_info.append({
                        'rule_code': rule_code,
                        'rule_name': rule_code,
                        'rule_description': '',
                        'rule_type': 'gjb',
                        'accuracy_type': 'uncertain',
                        'is_selected': True,  # 默认勾选
                        'problem_count': rule_problem_count.get(rule_code, 0),
                        'ai_confirmed_count': 0,
                        'is_in_filtered': False,
                        'filtered_badge': None
                    })
            
            # 统计规则类型
            accurate_count = sum(1 for r in rules_info if r['accuracy_type'] == 'accurate')
            uncertain_count = sum(1 for r in rules_info if r['accuracy_type'] == 'uncertain')
            logger.info(f"[代码视图API] 规则统计: 总数={len(rules_info)}, accurate={accurate_count}, uncertain={uncertain_count}")
            print(f"[FPGA代码视图API] 规则统计: 总数={len(rules_info)}, accurate={accurate_count}, uncertain={uncertain_count}")
            
            return {
                "success": True,
                "data": {
                    "files": files_data,
                    "problems": problems_data,
                    "selected_rules": list(selected_rules),  # 返回用户勾选的规则列表
                    "rules": rules_info  # 返回规则详细信息列表
                },
                "message": "代码视图数据获取成功"
            }
            
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[代码视图API] 获取代码视图数据失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"获取代码视图数据失败: {str(e)}")

@router.post("/export-marked-problems/{task_id}")
def export_marked_problems(
    task_id: str,
    request_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
) -> FileResponse:
    """
    导出已标记的问题到Excel文件
    
    Args:
        task_id: 任务ID
        request_data: 请求体数据，包含：
            - rule_type: 规则类型
            - problems: 已标记的问题列表
        db: 数据库会话
    
    Returns:
        Excel文件响应
    """
    try:
        from datetime import datetime
        import tempfile
        try:
            from openpyxl import Workbook
            from openpyxl.utils import get_column_letter
        except ImportError:
            raise HTTPException(status_code=500, detail="导出失败: 服务器缺少openpyxl依赖")
        
        rule_type = request_data.get('rule_type', 'gjb')
        problems = request_data.get('problems', [])
        
        logger.info(f"[导出已标记问题] task_id={task_id}, rule_type={rule_type}, problems_count={len(problems)}")
        
        if not problems:
            raise HTTPException(status_code=400, detail="没有已标记的问题")
        
        # 准备Excel数据
        headers = [
            '序号', '问题名称', '问题文件', '问题行号', '规则编号',
            '规则类型', '规则准确性', '问题描述', 'AI判断', 'AI置信度', 'AI分析结果'
        ]

        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = '已标记问题'
        worksheet.append(headers)

        for idx, problem in enumerate(problems, 1):
            worksheet.append([
                idx,
                problem.get('issue_name', ''),
                problem.get('issue_file', ''),
                problem.get('issue_line', ''),
                problem.get('rule_code', ''),
                problem.get('rule_type', ''),
                '确定规则' if problem.get('rule_accuracy_type') == 'accurate' else '不确定规则',
                problem.get('issue_description', ''),
                ('真实问题' if problem.get('ai_is_real_issue') else '误报') if problem.get('ai_analyzed') else '',
                f"{problem.get('ai_confidence', 0) * 100:.0f}%" if problem.get('ai_analyzed') and problem.get('ai_confidence') else '',
                problem.get('ai_analysis_result', '') if problem.get('ai_analyzed') else ''
            ])

        # 自动调整列宽
        for column_cells in worksheet.columns:
            max_length = 0
            column_letter = get_column_letter(column_cells[0].column)
            for cell in column_cells:
                try:
                    cell_value = str(cell.value) if cell.value is not None else ''
                    max_length = max(max_length, len(cell_value))
                except Exception:
                    continue
            worksheet.column_dimensions[column_letter].width = min(max_length + 2, 50)

        # 生成临时文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_file = tempfile.NamedTemporaryFile(
            mode='w+b',
            suffix='.xlsx',
            delete=False
        )

        workbook.save(temp_file.name)
        workbook.close()
        
        filename = f"marked_problems_{task_id}_{rule_type}_{timestamp}.xlsx"
        
        logger.info(f"[导出已标记问题] 导出成功: {filename}")
        
        # [NEW] 标记任务已导出过标记问题（类比函数审查）
        try:
            # 首先尝试作为数字ID查询session
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
            
            if session:
                session.marked_problems_exported = True
                db.commit()
                logger.info(f"[导出已标记问题] 任务导出状态已更新: session_id={session.session_id}")
        except Exception as e:
            logger.warning(f"[导出已标记问题] 更新导出状态失败: {e}")
            # 导出状态更新失败不影响导出功能
        
        return FileResponse(
            path=temp_file.name,
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[导出已标记问题] 导出失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


# ==================== 管理员API ====================

@router.get("/admin/tasks")
def get_all_static_analysis_fpga_tasks(
    status: str = None,
    limit: int = 500,
    db: Session = Depends(get_db_session)
):
    """
    获取所有静态分析FPGA任务列表（管理员功能）
    包含问题检出准确率和问题单准确率字段
    """
    try:
        print("[DEBUG FPGA admin/tasks] 开始导入模型")
        from ..database.postgresql_models import StaticAnalysisSession, StaticAnalysisIssue, StaticAnalysisMarkedProblem, FPGARule
        print("[DEBUG FPGA admin/tasks] 模型导入成功")

        print(f"[DEBUG FPGA admin/tasks] 开始查询任务, status={status}, limit={limit}")
        query = db.query(StaticAnalysisSession)

        # 状态过滤
        if status:
            query = query.filter(StaticAnalysisSession.status == status)

        # 按创建时间倒序排列
        tasks = query.order_by(StaticAnalysisSession.created_at.desc()).limit(limit).all()
        print(f"[DEBUG FPGA admin/tasks] 查询到 {len(tasks)} 个任务")

        task_list = []
        print(f"[DEBUG FPGA admin/tasks] 开始遍历 {len(tasks)} 个任务")
        for idx, task in enumerate(tasks):
            print(f"[DEBUG FPGA admin/tasks] 处理任务 {idx+1}/{len(tasks)}: id={task.id}, session_id={task.session_id}")
            try:
                # [NEW] 四分类统计：确定勾选/确定不勾选/不确定勾选/不确定不勾选
                print(f"[DEBUG FPGA admin/tasks] 任务 {task.id}: 开始四分类统计...")
                
                # 1. 确定规则勾选的问题数量
                accurate_selected = db.query(StaticAnalysisIssue).filter(
                    StaticAnalysisIssue.task_id == task.id,
                    StaticAnalysisIssue.rule_accuracy_type == 'accurate',
                    StaticAnalysisIssue.is_filtered == False
                ).filter(
                    StaticAnalysisIssue.rule_code.in_(
                        db.query(FPGARule.rule_code).filter(FPGARule.is_selected == True)
                    )
                ).count()
                print(f"[DEBUG FPGA admin/tasks] 任务 {task.id}: accurate_selected={accurate_selected}")
                
                # 2. 确定规则未勾选的问题数量
                accurate_unselected = db.query(StaticAnalysisIssue).filter(
                    StaticAnalysisIssue.task_id == task.id,
                    StaticAnalysisIssue.rule_accuracy_type == 'accurate',
                    StaticAnalysisIssue.is_filtered == False
                ).filter(
                    ~StaticAnalysisIssue.rule_code.in_(
                        db.query(FPGARule.rule_code).filter(FPGARule.is_selected == True)
                    )
                ).count()
                print(f"[DEBUG FPGA admin/tasks] 任务 {task.id}: accurate_unselected={accurate_unselected}")
                
                # 3. 不确定规则勾选的问题数量
                uncertain_selected = db.query(StaticAnalysisIssue).filter(
                    StaticAnalysisIssue.task_id == task.id,
                    StaticAnalysisIssue.rule_accuracy_type == 'uncertain',
                    StaticAnalysisIssue.is_filtered == False
                ).filter(
                    StaticAnalysisIssue.rule_code.in_(
                        db.query(FPGARule.rule_code).filter(FPGARule.is_selected == True)
                    )
                ).count()
                print(f"[DEBUG FPGA admin/tasks] 任务 {task.id}: uncertain_selected={uncertain_selected}")
                
                # 4. 不确定规则未勾选的问题数量
                uncertain_unselected = db.query(StaticAnalysisIssue).filter(
                    StaticAnalysisIssue.task_id == task.id,
                    StaticAnalysisIssue.rule_accuracy_type == 'uncertain',
                    StaticAnalysisIssue.is_filtered == False
                ).filter(
                    ~StaticAnalysisIssue.rule_code.in_(
                        db.query(FPGARule.rule_code).filter(FPGARule.is_selected == True)
                    )
                ).count()
                print(f"[DEBUG FPGA admin/tasks] 任务 {task.id}: uncertain_unselected={uncertain_unselected}")
                
                # 总问题数（四分类之和）
                total_four_category = accurate_selected + accurate_unselected + uncertain_selected + uncertain_unselected
                
                # 过滤后问题数：确定勾选 + 不确定勾选中AI确认的
                uncertain_selected_ai_confirmed = db.query(StaticAnalysisIssue).filter(
                    StaticAnalysisIssue.task_id == task.id,
                    StaticAnalysisIssue.rule_accuracy_type == 'uncertain',
                    StaticAnalysisIssue.is_filtered == False,
                    StaticAnalysisIssue.ai_is_real_issue == True
                ).filter(
                    StaticAnalysisIssue.rule_code.in_(
                        db.query(FPGARule.rule_code).filter(FPGARule.is_selected == True)
                    )
                ).count()
                filtered_problems_count = accurate_selected + uncertain_selected_ai_confirmed
                print(f"[DEBUG FPGA admin/tasks] 任务 {task.id}: filtered_problems_count={filtered_problems_count}")
                
                # 标记问题数量
                marked_count = db.query(StaticAnalysisMarkedProblem).filter(
                    StaticAnalysisMarkedProblem.session_id == task.session_id
                ).count()
                print(f"[DEBUG FPGA admin/tasks] 任务 {task.id}: marked_count={marked_count}")
                
                # 问题检出准确率
                accuracy = 0.0
                if filtered_problems_count > 0 and marked_count > 0:
                    accuracy = round(marked_count / filtered_problems_count, 4)
                print(f"[DEBUG FPGA admin/tasks] 任务 {task.id}: accuracy={accuracy}")
                
                # 获取最新标记时间
                latest_marked = db.query(StaticAnalysisMarkedProblem).filter(
                    StaticAnalysisMarkedProblem.session_id == task.session_id
                ).order_by(StaticAnalysisMarkedProblem.marked_at.desc()).first()
                latest_marked_at = latest_marked.marked_at if latest_marked else None
                
                print(f"[DEBUG FPGA admin/tasks] 任务 {task.id}: marked_problems_exported={task.marked_problems_exported}")
                
                task_dict = {
                    'id': task.id,
                    'session_id': task.session_id,
                    'task_name': task.original_filename,
                    'operator_name': task.operator_name,
                    'status': task.status,
                    'created_at': task.created_at.isoformat() if task.created_at else None,
                    'updated_at': task.updated_at.isoformat() if task.updated_at else None,
                    # [NEW] 四分类统计
                    'accurate_selected': accurate_selected,
                    'accurate_unselected': accurate_unselected,
                    'uncertain_selected': uncertain_selected,
                    'uncertain_unselected': uncertain_unselected,
                    'total_four_category': total_four_category,
                    # [NEW] 过滤后和标记相关
                    'filtered_problems_count': filtered_problems_count,
                    'marked_problem_count': marked_count,
                    'has_marked_problems': marked_count > 0,
                    'marked_problems_exported': task.marked_problems_exported,  # [FIXED] 直接从任务表读取
                    'latest_marked_at': latest_marked_at.isoformat() if latest_marked_at else None,
                    # [NEW] 准确率相关
                    'accuracy': accuracy,
                    'problem_sheet_accuracy_rate': task.problem_sheet_accuracy_rate,
                }
                task_list.append(task_dict)
                print(f"[DEBUG FPGA admin/tasks] 任务 {task.id}: 成功添加到列表")
            except Exception as task_e:
                print(f"[DEBUG FPGA admin/tasks] 任务 {task.id}: 处理失败: {task_e}")
                import traceback
                print(f"[DEBUG FPGA admin/tasks] 任务 {task.id}: 错误详情: {traceback.format_exc()}")
                # 添加基础信息，避免整个列表为空
                task_dict = {
                    'id': task.id,
                    'session_id': task.session_id,
                    'task_name': task.original_filename,
                    'operator_name': task.operator_name,
                    'status': task.status,
                    'created_at': task.created_at.isoformat() if task.created_at else None,
                    'updated_at': task.updated_at.isoformat() if task.updated_at else None,
                    'accurate_selected': 0,
                    'accurate_unselected': 0,
                    'uncertain_selected': 0,
                    'uncertain_unselected': 0,
                    'total_four_category': 0,
                    'filtered_problems_count': 0,
                    'marked_problem_count': 0,
                    'has_marked_problems': False,
                    'marked_problems_exported': task.marked_problems_exported,  # [FIXED] 直接从任务表读取
                    'latest_marked_at': None,
                    'accuracy': 0.0,
                    'problem_sheet_accuracy_rate': task.problem_sheet_accuracy_rate,
                }
                task_list.append(task_dict)
        
        print(f"[DEBUG FPGA admin/tasks] 最终返回 {len(task_list)} 个任务")
        logger.info(f"[静态分析FPGA管理员] 返回任务列表: 共 {len(task_list)} 个任务")

        return {
            "success": True,
            "tasks": task_list,
            "total": len(task_list)
        }

    except Exception as e:
        error_msg = f"获取静态分析FPGA任务列表失败: {str(e)}"
        print(f"[DEBUG FPGA admin/tasks] 外层异常: {error_msg}")
        logger.error(error_msg)
        import traceback
        print(f"[DEBUG FPGA admin/tasks] 异常详情: {traceback.format_exc()}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_msg)


# ==================== 问题单准确率反馈API ====================

class ProblemSheetAccuracyFeedbackRequestFpga(BaseModel):
    """问题单准确率反馈请求"""
    accuracy_rate: str  # 50%以下、50%-70%、70%-85%、85%-95%、95%-100%


@router.post("/{task_id}/problem_sheet_accuracy_feedback")
def submit_problem_sheet_accuracy_feedback_fpga(
    task_id: str,  # [FIX] 改为字符串类型，支持UUID和数字ID
    request: ProblemSheetAccuracyFeedbackRequestFpga,
    db: Session = Depends(get_db_session)
):
    """
    提交问题单准确率反馈（类比函数审查的注释准确率反馈）
    """
    try:
        from ..database.postgresql_models import StaticAnalysisSession
        
        # [FIX] 尝试将task_id转换为整数（如果是数字ID）
        try:
            task_id_int = int(task_id)
            task = db.query(StaticAnalysisSession).filter(StaticAnalysisSession.id == task_id_int).first()
        except (ValueError, TypeError):
            # 如果不是数字，尝试按字符串查询session_id
            task = db.query(StaticAnalysisSession).filter(StaticAnalysisSession.session_id == task_id).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 验证准确率选项
        valid_rates = ["50%以下", "50%-70%", "70%-85%", "85%-95%", "95%-100%"]
        if request.accuracy_rate not in valid_rates:
            raise HTTPException(status_code=400, detail="无效的准确率选项")
        
        # 更新任务的问题单准确率
        task.problem_sheet_accuracy_rate = request.accuracy_rate
        task.problem_sheet_feedback_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"[FPGA问题单准确率反馈] 成功: task_id={task_id}, rate={request.accuracy_rate}")
        
        return {
            "success": True,
            "message": "感谢您的反馈！",
            "data": {
                "task_id": task_id,
                "accuracy_rate": request.accuracy_rate,
                "feedback_at": task.problem_sheet_feedback_at.isoformat() if task.problem_sheet_feedback_at else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"[FPGA问题单准确率反馈] 失败: task_id={task_id}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"提交反馈失败: {str(e)}")


@router.get("/{task_id}/problem_sheet_accuracy_status")
def get_problem_sheet_accuracy_status_fpga(
    task_id: str,  # [FIX] 改为字符串类型，支持UUID和数字ID
    db: Session = Depends(get_db_session)
):
    """
    获取问题单准确率反馈状态
    """
    try:
        from ..database.postgresql_models import StaticAnalysisSession
        
        # [FIX] 尝试将task_id转换为整数（如果是数字ID）
        try:
            task_id_int = int(task_id)
            task = db.query(StaticAnalysisSession).filter(StaticAnalysisSession.id == task_id_int).first()
        except (ValueError, TypeError):
            # 如果不是数字，尝试按字符串查询session_id
            task = db.query(StaticAnalysisSession).filter(StaticAnalysisSession.session_id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return {
            "success": True,
            "data": {
                "task_id": task_id,
                "problem_sheet_accuracy_rate": task.problem_sheet_accuracy_rate,
                "feedback_at": task.problem_sheet_feedback_at.isoformat() if task.problem_sheet_feedback_at else None,
                "has_feedback": task.problem_sheet_accuracy_rate is not None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[FPGA问题单准确率状态] 失败: task_id={task_id}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}") 