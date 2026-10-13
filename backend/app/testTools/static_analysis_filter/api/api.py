"""
静态分析问题过滤工具API - 增强版本
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File, Form, Body, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import uuid
import os
import zipfile
import shutil
from pathlib import Path
import asyncio
import logging

from ..database.database import get_db_session
from ..database.rules_database import get_rules_database
from ..database.cwe_rules_database import get_cwe_rules_database
from ..models.models import StaticAnalysisSession, StaticAnalysisIssue
from ..services.service import StaticAnalysisFilterService
from ..services.enhanced_service import EnhancedStaticAnalysisFilterService
from ..config.config import UPLOAD_DIR
from ..config.default_rules_config import (
    save_default_rules_config,
    load_default_rules_config,
    has_default_config,
    verify_admin_password
)

router = APIRouter()

# 设置日志
logger = logging.getLogger(__name__)

# 全局数据库实例
_gjb_db = get_rules_database()
_cwe_db = get_cwe_rules_database()

# 全局服务实例缓存
_active_services: Dict[str, StaticAnalysisFilterService] = {}
_enhanced_services: Dict[str, EnhancedStaticAnalysisFilterService] = {}

def get_service(session_id: str) -> StaticAnalysisFilterService:
    """获取或创建服务实例"""
    if session_id not in _active_services:
        _active_services[session_id] = StaticAnalysisFilterService(session_id)
    return _active_services[session_id]

def get_enhanced_service(session_id: str) -> EnhancedStaticAnalysisFilterService:
    """获取或创建增强服务实例"""
    if session_id not in _enhanced_services:
        _enhanced_services[session_id] = EnhancedStaticAnalysisFilterService(session_id)
    return _enhanced_services[session_id]

async def save_uploaded_file(file: UploadFile, session_id: str) -> str:
    """
    保存上传的Excel文件
    """
    upload_dir = UPLOAD_DIR / "testTools" / "static_analysis_filter"
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
    upload_dir = UPLOAD_DIR / "testTools" / "static_analysis_filter" / "codebases"
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
            # 将服务实例加入全局缓存
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
        
        # 获取服务实例
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
        logger.info(f"[下载API] 当前增强服务数量: {len(_enhanced_services)}, 会话列表: {list(_enhanced_services.keys())}")
        logger.info(f"[下载API] 当前普通服务数量: {len(_active_services)}, 会话列表: {list(_active_services.keys())}")
        
        # 优先检查增强服务
        service = None
        if session_id in _enhanced_services:
            service = _enhanced_services[session_id]
            logger.info(f"[下载API] 在增强服务中找到会话: {session_id}")
        elif session_id in _active_services:
            service = _active_services[session_id]
            logger.info(f"[下载API] 在普通服务中找到会话: {session_id}")
        else:
            logger.error(f"[下载API] 会话不存在: {session_id}")
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
    background_tasks: BackgroundTasks,
    excel_file: UploadFile = File(..., description="静态分析结果Excel文件"),
    codebase_file: UploadFile = File(None, description="代码库压缩文件（可选）"),
    selected_rules: str = Form("[]", description="选中的规则列表（JSON格式）"),
    filter_keywords: Optional[str] = Form(None, description="过滤关键字")
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
        
        # 将服务实例加入全局缓存
        _enhanced_services[session_id] = service
        
        logger.info(f"增强版文件上传成功，开始后台处理 - 会话ID: {session_id}")
        
        # 🔧 使用FastAPI的BackgroundTasks确保真正在后台执行
        background_tasks.add_task(
            process_enhanced_session_in_background_sync,
            session_id, excel_path, excel_file.filename, codebase_path, rules, keywords
        )
        
        # 🔧 立即返回响应，避免前端超时
        response_data = {
            "success": True,
            "session_id": session_id,
            "message": "文件上传成功，正在进行增强处理中",
            "status": "uploading",
            "total_issues": 0,  # 初始为0，后台处理后更新
            "has_codebase": codebase_path is not None
        }
        
        logger.info(f"🚀 立即返回响应，任务将在后台执行 - 会话ID: {session_id}")
        
        return response_data
            
    except Exception as e:
        error_msg = f"增强版文件上传失败: {str(e)}"
        print(f"❌ [API] {error_msg}")
        return {"success": False, "error": error_msg}

def process_enhanced_session_in_background_sync(
    session_id: str, 
    excel_path: str, 
    original_filename: str, 
    codebase_path: str, 
    rules: list, 
    keywords: list
):
    """后台处理增强会话（同步版本，用于FastAPI BackgroundTasks）"""
    try:
        service = get_enhanced_service(session_id)
        logger = service.logger

        logger.info(f"开始后台增强处理会话: {session_id}")
        
        # 🔧 在后台任务中处理上传文件（同步操作，但在异步任务中执行）
        result = service.process_uploaded_files(excel_path, original_filename, codebase_path, rules, keywords)
        
        if not result["success"]:
            logger.error(f"处理上传文件失败: {result.get('error')}")
            return

        logger.info(f"上传文件处理完成，发现{result.get('total_issues', 0)}个问题")

        # 🔧 同步处理会话（在后台任务中执行）
        # 因为process_session_enhanced是async函数，需要用asyncio.run
        import asyncio
        result = asyncio.run(service.process_session_enhanced())

        if result["success"]:
            logger.info(f"增强会话处理完成: {session_id} - {result['message']}")
        else:
            logger.error(f"增强会话处理失败: {session_id} - {result.get('error')}")

    except Exception as e:
        if session_id in _enhanced_services:
            logger = _enhanced_services[session_id].logger
            logger.error(f"后台增强处理会话时出错: {str(e)}")
        import traceback
        print(f"❌ [后台任务] 处理会话{session_id}时出错: {str(e)}")
        print(traceback.format_exc())

@router.get("/status-enhanced/{session_id}")
def get_enhanced_processing_status(session_id: str) -> Dict[str, Any]:
    """
    获取增强处理状态
    """
    try:
        print(f"🔍 [API] 收到增强状态查询请求 - 会话ID: {session_id}")
        logger.info(f"收到增强状态查询请求 - 会话ID: {session_id}")
        
        # 获取增强服务实例
        if session_id not in _enhanced_services:
            print(f"❌ [API] 增强会话不存在: {session_id}")
            logger.warning(f"增强会话不存在: {session_id}")
            raise HTTPException(status_code=404, detail="会话不存在")
        
        service = _enhanced_services[session_id]
        print(f"✅ [API] 找到增强服务实例，会话ID: {session_id}")
        
        # 使用增强内存状态，快速响应
        status_result = service.get_enhanced_memory_status()
        print(f"📊 [API] 增强内存状态: {status_result}")
        logger.info(f"返回增强状态: {status_result}")
        
        return status_result
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"获取增强状态失败: {str(e)}"
        print(f"❌ [API] {error_msg}")
        logger.error(error_msg)
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

@router.get("/status/{session_id}/detailed")
def get_detailed_status(session_id: str) -> Dict[str, Any]:
    """
    获取详细状态（GJB和CWE两部分）
    
    Returns:
        {
            "success": true,
            "session_id": "xxx",
            "gjb": {
                "total_issues": 10,
                "processed_issues": 5,
                "current_analyzing_issue": "...",
                "tool_calls_count": 15,
                "progress": 50,
                "status": "processing"
            },
            "cwe": {
                "total_issues": 20,
                "processed_issues": 10,
                "current_analyzing_issue": "...",
                "tool_calls_count": 25,
                "progress": 50,
                "status": "processing"
            }
        }
    """
    try:
        # 从增强服务获取状态
        service = get_enhanced_service(session_id)
        if not service:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        # 获取详细状态
        detailed_status = service.get_detailed_status()
        
        # 调试日志：打印详细状态
        logger.info(f"[详细状态API] Session: {session_id}")
        logger.info(f"[详细状态API] GJB Status: {detailed_status.get('gjb', {}).get('status', 'N/A')}")
        logger.info(f"[详细状态API] CWE Status: {detailed_status.get('cwe', {}).get('status', 'N/A')}")
        
        result = {
            "success": True,
            "session_id": session_id,
            **detailed_status
        }
        
        logger.info(f"[详细状态API] 返回数据包含status字段: GJB={('status' in result.get('gjb', {}))}, CWE={('status' in result.get('cwe', {}))}")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取详细状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取详细状态失败: {str(e)}")

# === 默认规则配置管理API ===

@router.post("/rules/config/save")
def save_default_config(
    password: str = Body(..., embed=True),
    gjb_rules: List[str] = Body(..., embed=True),
    cwe_rules: List[str] = Body(..., embed=True)
) -> Dict[str, Any]:
    """
    保存默认规则配置（需要管理员密码）
    
    请求体:
    {
        "password": "159357",
        "gjb_rules": ["GJB_R_01_01_01", ...],
        "cwe_rules": ["S_01_01", ...]
    }
    """
    try:
        logger.info(f"[配置API] 收到保存默认规则配置请求")
        logger.info(f"[配置API] GJB规则数: {len(gjb_rules)}, CWE规则数: {len(cwe_rules)}")
        
        # 验证管理员密码
        if not verify_admin_password(password):
            logger.warning(f"[配置API] 管理员密码验证失败")
            raise HTTPException(status_code=403, detail="管理员密码错误")
        
        # 保存配置
        success = save_default_rules_config(gjb_rules, cwe_rules)
        
        if success:
            logger.info(f"[配置API] 默认规则配置保存成功")
            return {
                "success": True,
                "message": "默认规则配置已保存",
                "gjb_rules_count": len(gjb_rules),
                "cwe_rules_count": len(cwe_rules)
            }
        else:
            raise HTTPException(status_code=500, detail="保存配置失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[配置API] 保存配置时出错: {str(e)}")
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
        "cwe_rules": [...]
    }
    """
    try:
        logger.info(f"[配置API] 收到加载默认规则配置请求")
        
        config = load_default_rules_config()
        has_config = has_default_config()
        
        logger.info(f"[配置API] 配置存在: {has_config}, GJB规则数: {len(config['gjb_rules'])}, CWE规则数: {len(config['cwe_rules'])}")
        
        return {
            "success": True,
            "has_config": has_config,
            "gjb_rules": config["gjb_rules"],
            "cwe_rules": config["cwe_rules"]
        }
    except Exception as e:
        logger.error(f"[配置API] 加载配置时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"加载配置失败: {str(e)}") 