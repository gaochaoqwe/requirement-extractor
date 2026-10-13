"""
静态分析问题过滤工具API - 增强版本
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File, Form, Body, Query, Request
from fastapi.responses import FileResponse, StreamingResponse
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
import time
from datetime import datetime  # [FIX] 添加datetime导入

from app.staticAnalysis.filter.database.database import get_db_session, get_db
from app.staticAnalysis.filter.database.rules_database_factory import get_rules_database, get_cwe_rules_database
from app.staticAnalysis.filter.models.models import StaticAnalysisSession, StaticAnalysisIssue
from app.staticAnalysis.filter.database.postgresql_models import GJB8114Rule, CWERule  # [FIX] 提前导入规则模型
from app.staticAnalysis.filter.services.service import StaticAnalysisFilterService
from app.staticAnalysis.filter.services.enhanced_service import EnhancedStaticAnalysisFilterService
from app.staticAnalysis.filter.config.config import UPLOAD_DIR, MAX_ENHANCED_CONCURRENT_SESSIONS
from app.staticAnalysis.filter.config.default_rules_config import (
    save_default_rules_config,
    load_default_rules_config,
    has_default_config,
    verify_admin_password
)

# 导入新的端点路由
from app.staticAnalysis.filter.api.endpoints_marked_problems import router as marked_problems_router
from app.staticAnalysis.filter.api.endpoints_problem_status import router as problem_status_router
from app.staticAnalysis.filter.api.endpoints_fix import router as fix_router
from app.staticAnalysis.filter.utils.logger import setup_module_logger

router = APIRouter()

# 包含子路由
router.include_router(marked_problems_router, tags=["marked-problems"])
router.include_router(problem_status_router, tags=["problem-status"])
router.include_router(fix_router, tags=["auto-fix"])


def build_function_aware_source_snippet(source_code: str, line_no: int, context: int = 3) -> str:
    if not source_code:
        return ''

    lines = source_code.splitlines()
    if line_no <= 0 or line_no > len(lines):
        return source_code[:2000]

    target_idx = line_no - 1

    def is_control_signature(text: str) -> bool:
        stripped = text.strip()
        control_prefixes = ('if ', 'if(', 'for ', 'for(', 'while ', 'while(', 'switch ', 'switch(', 'catch ', 'catch(', 'else', 'do ', 'do{')
        type_prefixes = ('struct ', 'enum ', 'union ', 'typedef ')
        return stripped.startswith(control_prefixes) or stripped.startswith(type_prefixes)

    brace_stack = []
    for idx, line in enumerate(lines[:target_idx + 1]):
        for char in line:
            if char == '{':
                brace_stack.append(idx)
            elif char == '}' and brace_stack:
                brace_stack.pop()

    def signature_start(open_idx: int) -> int:
        start = open_idx
        while start > 0:
            prev = lines[start - 1].strip()
            if not prev or prev.startswith('#') or prev.endswith(';') or prev.endswith('}') or prev.endswith('{'):
                break
            start -= 1
        return start

    function_open_idx = None
    function_sig_start = None
    for open_idx in reversed(brace_stack):
        sig_start = signature_start(open_idx)
        signature = ' '.join(line.strip() for line in lines[sig_start:open_idx + 1])
        if '(' in signature and ')' in signature and not is_control_signature(signature):
            function_open_idx = open_idx
            function_sig_start = sig_start
            break

    if function_open_idx is None:
        start = max(0, target_idx - context)
        end = min(len(lines) - 1, target_idx + context)
        snippet = []
        if start > 0:
            snippet.append('......')
        snippet.extend(lines[start:end + 1])
        if end < len(lines) - 1:
            snippet.append('......')
        return '\n'.join(snippet)

    depth = 0
    function_close_idx = len(lines) - 1
    for idx in range(function_open_idx, len(lines)):
        for char in lines[idx]:
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    function_close_idx = idx
                    break
        if depth == 0 and idx >= function_open_idx:
            break

    context_start = max(function_open_idx + 1, target_idx - context)
    context_end = min(function_close_idx - 1, target_idx + context)

    snippet = []
    snippet.extend(lines[function_sig_start:function_open_idx + 1])
    if context_start > function_open_idx + 1:
        snippet.append('......')
    if context_start <= context_end:
        snippet.extend(lines[context_start:context_end + 1])
    if context_end < function_close_idx - 1:
        snippet.append('......')
    if function_close_idx > function_open_idx:
        snippet.append(lines[function_close_idx])

    return '\n'.join(snippet)

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
        logger.info(f"收到状态查询请求 - 会话ID: {session_id}")
        
        # 获取服务实例（线程安全）
        with _services_lock:
            if session_id not in _active_services:
                logger.warning(f"会话不存在: {session_id}")
                raise HTTPException(status_code=404, detail="会话不存在")
            
            service = _active_services[session_id]
        # 使用内存状态，快速响应
        status_result = service.get_memory_status()
        logger.info(f"返回状态: {status_result}")
        
        return status_result
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"获取状态失败: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

# 旧版端点已删除，使用后面包含 success 字段的新版本

@router.post("/download/{session_id}")
async def generate_output_file(session_id: str, request: Request,
                               rule_type: str = Body('all'),
                               content_type: str = Body('all'),
                               include_unselected: bool = Body(False),
                               split: bool = Body(False),
                               highlight_ai: bool = Body(False),
                               background: bool = Body(False),
                               background_tasks: BackgroundTasks = None):
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
        
        def _run_generate(service_inst,
                          rule_type_v,
                          content_type_v,
                          include_unselected_v,
                          split_v,
                          highlight_ai_v):
            try:
                gen_result = service_inst.generate_output_file(
                    rule_type=rule_type_v,
                    content_type=content_type_v,
                    include_unselected=include_unselected_v,
                    split=split_v,
                    highlight_ai=highlight_ai_v,
                )
                if gen_result.get("success"):
                    service_inst.output_filename = gen_result["filename"]
                    logger.info(f"[下载API] 后台生成完成: {gen_result['filename']}")
                else:
                    logger.error(f"[下载API] 后台生成失败: {gen_result}")
            except Exception as ex:
                logger.error(f"[下载API] 后台生成异常: {str(ex)}")

        # 后台模式：不阻塞请求线程
        if background:
            if background_tasks is None:
                # FastAPI 会注入 BackgroundTasks，此处保底
                raise HTTPException(status_code=400, detail="后台任务不可用")
            background_tasks.add_task(
                _run_generate,
                service,
                rule_type,
                content_type,
                include_unselected,
                split,
                highlight_ai,
            )
            return {
                "success": True,
                "pending": True,
                "message": "已开始后台生成，稍后可通过状态或下载接口获取文件"
            }

        # 同步模式：保持向后兼容
        # [FIX] 检查是否有预生成的缓存文件（仅限未经AI过滤的四分分类文件）
        cached_filename = None
        if split and content_type == 'all' and not include_unselected and not highlight_ai:
            # 这是未经AI过滤的四分分类文件请求，检查缓存
            if rule_type == 'gjb' and hasattr(service, 'gjb_cached_filename') and service.gjb_cached_filename:
                cached_filename = service.gjb_cached_filename
                logger.info(f"[下载API] 使用GJB预生成缓存文件: {cached_filename}")
            elif rule_type == 'cwe' and hasattr(service, 'cwe_cached_filename') and service.cwe_cached_filename:
                cached_filename = service.cwe_cached_filename
                logger.info(f"[下载API] 使用CWE预生成缓存文件: {cached_filename}")
        
        if cached_filename:
            # 使用缓存文件
            # 验证文件是否存在
            cached_file_path = UPLOAD_DIR / "outputs" / cached_filename
            if cached_file_path.exists():
                service.output_filename = cached_filename
                return {
                    "success": True,
                    "filename": cached_filename,
                    "message": "使用缓存文件"
                }
            else:
                logger.warning(f"[下载API] 缓存文件不存在，重新生成: {cached_filename}")
        
        # 没有缓存或缓存文件不存在，重新生成
        result = service.generate_output_file(
            rule_type=rule_type,
            content_type=content_type,
            include_unselected=include_unselected,
            split=split,
            highlight_ai=highlight_ai,
        )

        if result.get("success"):
            # [FIX] 确保文件已落盘存在后再返回，避免前端立刻下载 404
            filename = result["filename"]
            output_path = UPLOAD_DIR / "outputs" / filename
            if not output_path.exists():
                try:
                    # 最长等待约 5 秒（0.2 * 25），应对磁盘I/O延迟
                    for _ in range(25):
                        if output_path.exists():
                            break
                        await asyncio.sleep(0.2)
                except Exception as wait_ex:
                    logger.warning(f"[下载API] 等待文件落盘时异常: {str(wait_ex)}")

            if not output_path.exists():
                logger.warning(f"[下载API] 生成已返回成功但文件仍不存在: {filename}")

            service.output_filename = filename
            return {
                "success": True,
                "filename": filename,
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
    request: Request,  # 添加Request参数以访问session
    background_tasks: BackgroundTasks,  # [FIX] 添加FastAPI的BackgroundTasks参数
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
        # 调试：打印请求头和 Cookie，确认是否带上 session_id
        headers_dict = dict(request.headers)
        logger.info(f"[上传API] 开始处理上传请求 - Session ID: {session_id}")
        logger.info(f"[上传API] 请求头: {headers_dict}")
        logger.info(f"[上传API] Cookie 头: {headers_dict.get('cookie', '')}")

        # 从session中获取当前登录用户信息
        logger.info(f"[上传API] request.session内容: {dict(request.session)}")
        
        operator_name = request.session.get('display_name', None)
        if not operator_name:
            # 如果没有登录，使用username作为备选
            operator_name = request.session.get('username', '未知用户')
        
        logger.info(f"[上传API] 当前登录用户: {operator_name}")
        
        # 创建增强服务实例
        service = EnhancedStaticAnalysisFilterService(session_id)
        service.operator_name = operator_name
        logger.info(f"[上传API] 已设置service.operator_name = {service.operator_name}")
        
        codebase_filename = codebase_file.filename if codebase_file else "无"
        logger.info(f"[上传API] 开始增强版文件上传: Excel={excel_file.filename}, 代码库={codebase_filename}")
        # [FIX] 将Excel文件也读到内存，避免同步文件I/O阻塞
        excel_content = await excel_file.read()
        excel_data = {
            'filename': excel_file.filename,
            'content': excel_content
        }
        logger.info(f"Excel文件已读取到内存: {excel_file.filename}, 大小: {len(excel_content)} bytes")
        # [FIX] 将UploadFile对象转换为可传递的字典
        # 直接读取到内存（FastAPI已经将文件缓存在SpooledTemporaryFile中）
        codebase_data = None
        if codebase_file:
            logger.info(f"开始读取代码库文件: {codebase_file.filename}")
            
            # 一次性读取文件（FastAPI的UploadFile已经优化了大文件处理）
            content = await codebase_file.read()
            codebase_data = {
                'filename': codebase_file.filename,
                'content': content
            }
            
            logger.info(f"代码库文件已读取到内存: {codebase_file.filename}, 大小: {len(content)} bytes")
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
        
        # [并发控制] 检查当前正在处理的会话数
        ai_disabled = False
        with _services_lock:
            # 统计正在处理中的会话数（已有task_id的会话视为正在处理）
            active_sessions = sum(1 for s in _enhanced_services.values() if hasattr(s, 'task_id') and s.task_id is not None and hasattr(s, 'current_status') and s.current_status in ['processing', 'ai_analyzing'])
            
            logger.info(f"[并发控制] 当前活跃会话数: {active_sessions}/{MAX_ENHANCED_CONCURRENT_SESSIONS}")
            logger.info(f"[并发控制] 总会话数: {len(_enhanced_services)}, 活跃状态会话: {sum(1 for s in _enhanced_services.values() if hasattr(s, 'current_status') and s.current_status in ['processing', 'ai_analyzing'])}")
            if active_sessions >= MAX_ENHANCED_CONCURRENT_SESSIONS:
                ai_disabled = True
                logger.warning(f"[并发控制] 已达到最大并发数({MAX_ENHANCED_CONCURRENT_SESSIONS})，跳过AI审查")
                # 即使跳过AI审查，也要移除代码库数据，避免不必要的处理
                codebase_data = None
        
        # 将服务实例加入全局缓存（线程安全）
        with _services_lock:
            _enhanced_services[session_id] = service
        logger.info(f"增强版文件上传成功，开始后台处理 - 会话ID: {session_id}")
        # [FIX] 使用FastAPI的BackgroundTasks机制，确保HTTP响应在后台任务执行前发送
        # BackgroundTasks会在单独的线程中执行同步函数，完全不阻塞HTTP响应
        background_tasks.add_task(
            process_enhanced_session_in_background_sync,
            session_id, excel_data, codebase_data, rules, keywords, filters, max_issues_per_rule
        )
        # [INFO] 立即返回响应，避免前端超时
        response_data = {
            "success": True,
            "session_id": session_id,
            "message": "文件上传成功，正在进行增强处理中" if not ai_disabled else "文件上传成功，受模型并发限制，跳过AI审查",
            "status": "uploading",
            "total_issues": 0,  # 初始为0，后台处理后更新
            "has_codebase": codebase_data is not None,
            "ai_disabled": ai_disabled  # 并发控制标志
        }
        logger.info(f"[START] 立即返回响应，任务将在后台执行 - 会话ID: {session_id}")
        return response_data
            
    except Exception as e:
        error_msg = f"增强版文件上传失败: {str(e)}"
        import traceback
        return {"success": False, "error": error_msg}

def process_enhanced_session_in_background_sync(
    session_id: str, 
    excel_data: dict,  # [FIX] 改为接收Excel数据字典
    codebase_data: Optional[dict],
    rules: list, 
    keywords: list,
    custom_filters: dict = None,
    max_issues_per_rule: int = 0
):
    """后台处理增强会话（同步版本，用于FastAPI BackgroundTasks在单独线程中执行）"""
    try:
        service = get_enhanced_service(session_id)
        # [重要] 使用临时logger，等创建task_id后才使用service的专属logger
        temp_logger = logger

        temp_logger.info(f"开始后台增强处理会话: {session_id}")
        # [FIX] 在后台任务中保存Excel文件（不阻塞HTTP响应）
        temp_logger.info(f"开始保存Excel文件: {excel_data['filename']}")
        
        upload_dir = UPLOAD_DIR / "staticAnalysis" / "filter"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = __import__('datetime').datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{session_id}_{timestamp}_{excel_data['filename']}"
        excel_path = upload_dir / safe_filename
        
        # 保存Excel文件
        with open(excel_path, "wb") as f:
            f.write(excel_data['content'])
        
        excel_path = str(excel_path)
        temp_logger.info(f"Excel文件保存成功: {excel_path}")
        # [FIX] 在后台任务中执行代码库保存和解压操作（不阻塞HTTP响应）
        codebase_path = None
        codebase_info = {}  # 保存代码库信息，稍后写入日志
        
        if codebase_data:
            try:
                temp_logger.info(f"开始处理代码库文件: {codebase_data['filename']}")
                
                # 保存代码库文件并解压
                upload_dir = UPLOAD_DIR / "staticAnalysis" / "filter" / "codebases"
                upload_dir.mkdir(parents=True, exist_ok=True)
                
                timestamp = __import__('datetime').datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # 保存ZIP文件
                zip_filename = f"{session_id}_{timestamp}_{codebase_data['filename']}"
                zip_path = upload_dir / zip_filename
                
                extract_start_time = time.time()
                
                # 写入文件
                with open(zip_path, "wb") as f:
                    f.write(codebase_data['content'])
                
                # 解压到专用目录
                extract_dir = upload_dir / f"{session_id}_{timestamp}_extracted"
                extract_dir.mkdir(exist_ok=True)
                
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    # 统计代码库信息
                    file_list = zip_ref.namelist()
                    total_files = len(file_list)
                    zip_ref.extractall(extract_dir)
                
                extract_time = time.time() - extract_start_time
                
                # 统计代码文件数量
                c_files = len([f for f in file_list if f.endswith(('.c', '.C'))])
                cpp_files = len([f for f in file_list if f.endswith(('.cpp', '.CPP', '.cc', '.cxx'))])
                h_files = len([f for f in file_list if f.endswith(('.h', '.H', '.hpp'))])
                
                # 删除临时ZIP文件
                zip_path.unlink()
                
                codebase_path = str(extract_dir)
                
                # 保存代码库信息
                codebase_info = {
                    'filename': codebase_data['filename'],
                    'path': codebase_path,
                    'total_files': total_files,
                    'c_files': c_files,
                    'cpp_files': cpp_files,
                    'h_files': h_files,
                    'extract_time': f"{extract_time:.2f}秒"
                }
                
                temp_logger.info(f"代码库解压成功: {codebase_path}")
                temp_logger.info(f"代码库统计: 总文件数={total_files}, C文件={c_files}, C++文件={cpp_files}, 头文件={h_files}")
                temp_logger.info(f"解压耗时: {extract_time:.2f}秒")
            except Exception as e:
                error_msg = f"解压代码库失败: {str(e)}"
                temp_logger.error(error_msg)
                import traceback
                temp_logger.error(traceback.format_exc())
                # 继续执行，但不使用代码库
                codebase_path = None
        
        # [FIX] 直接调用同步函数（因为当前函数已经在BackgroundTasks的线程池中执行）
        # process_uploaded_files 是同步函数，包含大量阻塞I/O（Excel读取、数据库写入）
        result = service.process_uploaded_files(
            excel_path, excel_data['filename'], codebase_path, rules, keywords, custom_filters, max_issues_per_rule
        )
        if not result["success"]:
            # 现在service已有task_id和专属logger
            service.gjb_logger.error(f"处理上传文件失败: {result.get('error')}")
            service.cwe_logger.error(f"处理上传文件失败: {result.get('error')}")
            return

        # [新增] 在创建task_id后，将代码库信息写入任务专属日志
        if codebase_info:
            service.gjb_logger.info("=" * 100)
            service.gjb_logger.info("代码库信息")
            service.gjb_logger.info(
                "=" * 100)
            service.gjb_logger.info(f"代码库文件名: {codebase_info['filename']}")
            service.gjb_logger.info(f"解压路径: {codebase_info['path']}")
            service.gjb_logger.info(f"总文件数: {codebase_info['total_files']}")
            service.gjb_logger.info(f"C源文件: {codebase_info['c_files']}")
            service.gjb_logger.info(f"C++源文件: {codebase_info['cpp_files']}")
            service.gjb_logger.info(f"头文件: {codebase_info['h_files']}")
            service.gjb_logger.info(f"解压耗时: {codebase_info['extract_time']}")
            service.gjb_logger.info("=" * 100)
            
            service.cwe_logger.info("=" * 100)
            service.cwe_logger.info("代码库信息")
            service.cwe_logger.info("=" * 100)
            service.cwe_logger.info(f"代码库文件名: {codebase_info['filename']}")
            service.cwe_logger.info(f"解压路径: {codebase_info['path']}")
            service.cwe_logger.info(f"总文件数: {codebase_info['total_files']}")
            service.cwe_logger.info(f"C源文件: {codebase_info['c_files']}")
            service.cwe_logger.info(f"C++源文件: {codebase_info['cpp_files']}")
            service.cwe_logger.info(f"头文件: {codebase_info['h_files']}")
            service.cwe_logger.info(f"解压耗时: {codebase_info['extract_time']}")
            service.cwe_logger.info("=" * 100)
        service.gjb_logger.info(f"上传文件处理完成，发现{result.get('total_issues', 0)}个问题")
        service.cwe_logger.info(f"上传文件处理完成，发现{result.get('total_issues', 0)}个问题")

        # [FIX] 在同步函数中使用asyncio.run()调用异步函数
        # 因为process_session_enhanced是async函数，需要在新的事件循环中运行
        result = asyncio.run(service.process_session_enhanced())

        if result["success"]:
            service.gjb_logger.info(f"增强会话处理完成 - {result['message']}")
            service.cwe_logger.info(f"增强会话处理完成 - {result['message']}")
        else:
            service.gjb_logger.error(f"增强会话处理失败 - {result.get('error')}")
            service.cwe_logger.error(f"增强会话处理失败 - {result.get('error')}")

    except Exception as e:
        # 获取service的logger来记录错误
        try:
            service = None
            with _services_lock:
                if session_id in _enhanced_services:
                    service = _enhanced_services[session_id]
            
            if service and service.gjb_logger:
                service.gjb_logger.error(f"后台增强处理会话时出错: {str(e)}")
                service.cwe_logger.error(f"后台增强处理会话时出错: {str(e)}")
                import traceback
                service.gjb_logger.error(traceback.format_exc())
                service.cwe_logger.error(traceback.format_exc())
        except:
            pass
            
        import traceback
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
        # 首先尝试从内存中的处理服务获取
        with _services_lock:
            service = _enhanced_services.get(session_id)
            if service and getattr(service, 'task_id', None):
                return {
                    "success": True,
                    "session_id": session_id,
                    "task_id": service.task_id,
                    "message": "获取任务ID成功"
                }
        
        # 如果内存中没有，从数据库查询
        db = get_db_session()
        try:
            session = db.query(StaticAnalysisSession).filter(
                StaticAnalysisSession.session_id == session_id
            ).first()
            
            if not session:
                raise HTTPException(status_code=404, detail="会话不存在")
            return {
                "success": True,
                "session_id": session_id,
                "task_id": session.id,
                "message": "获取任务ID成功"
            }
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"获取任务ID失败: {str(e)}"
        raise HTTPException(status_code=500, detail=error_msg)

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
        
        # [FIX] 包装成标准格式，包含 success 字段
        result = {
            "success": True,
            "session_id": session_id,
            **detailed_status
        }
        return result
            
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

# ==================== 管理员API ====================

@router.get("/admin/tasks")
def get_all_static_analysis_tasks(
    status: str = None,
    limit: int = 500,
    db: Session = Depends(get_db_session)
):
    """
    获取所有静态分析任务列表（管理员功能）
    包含问题检出准确率和问题单准确率字段
    """
    try:
        print("[DEBUG admin/tasks] 开始导入模型")
        from ..database.postgresql_models import StaticAnalysisSession, StaticAnalysisIssue, StaticAnalysisMarkedProblem
        from ..database.postgresql_models import GJB8114Rule, CWERule
        print("[DEBUG admin/tasks] 模型导入成功")
        
        print(f"[DEBUG admin/tasks] 开始查询任务, status={status}, limit={limit}")
        query = db.query(StaticAnalysisSession)
        
        # 状态过滤
        if status:
            query = query.filter(StaticAnalysisSession.status == status)
        
        # 按创建时间倒序排列
        tasks = query.order_by(StaticAnalysisSession.created_at.desc()).limit(limit).all()
        print(f"[DEBUG admin/tasks] 查询到 {len(tasks)} 个任务")
        
        task_list = []
        print(f"[DEBUG admin/tasks] 开始遍历 {len(tasks)} 个任务")
        for idx, task in enumerate(tasks):
            print(f"[DEBUG admin/tasks] 处理任务 {idx+1}/{len(tasks)}: id={task.id}, session_id={task.session_id}")
            try:
                # [NEW] 四分类统计：确定勾选/确定不勾选/不确定勾选/不确定不勾选
                # 1. 确定规则勾选的问题数量
                print(f"[DEBUG admin/tasks] 任务 {task.id}: 开始查询确定勾选...")
                accurate_selected = db.query(StaticAnalysisIssue).filter(
                    StaticAnalysisIssue.task_id == task.id,
                    StaticAnalysisIssue.rule_accuracy_type == 'accurate',
                    StaticAnalysisIssue.is_filtered == False
                ).filter(
                    StaticAnalysisIssue.rule_code.in_(
                        db.query(GJB8114Rule.rule_code).filter(GJB8114Rule.is_selected == True)
                        .union(db.query(CWERule.rule_code).filter(CWERule.is_selected == True))
                    )
                ).count()
                print(f"[DEBUG admin/tasks] 任务 {task.id}: accurate_selected={accurate_selected}")
                
                # 2. 确定规则未勾选的问题数量
                print(f"[DEBUG admin/tasks] 任务 {task.id}: 开始查询确定不勾选...")
                accurate_unselected = db.query(StaticAnalysisIssue).filter(
                    StaticAnalysisIssue.task_id == task.id,
                    StaticAnalysisIssue.rule_accuracy_type == 'accurate',
                    StaticAnalysisIssue.is_filtered == False
                ).filter(
                    ~StaticAnalysisIssue.rule_code.in_(
                        db.query(GJB8114Rule.rule_code).filter(GJB8114Rule.is_selected == True)
                        .union(db.query(CWERule.rule_code).filter(CWERule.is_selected == True))
                    )
                ).count()
                print(f"[DEBUG admin/tasks] 任务 {task.id}: accurate_unselected={accurate_unselected}")
                
                # 3. 不确定规则勾选的问题数量
                print(f"[DEBUG admin/tasks] 任务 {task.id}: 开始查询不确定勾选...")
                uncertain_selected = db.query(StaticAnalysisIssue).filter(
                    StaticAnalysisIssue.task_id == task.id,
                    StaticAnalysisIssue.rule_accuracy_type == 'uncertain',
                    StaticAnalysisIssue.is_filtered == False
                ).filter(
                    StaticAnalysisIssue.rule_code.in_(
                        db.query(GJB8114Rule.rule_code).filter(GJB8114Rule.is_selected == True)
                        .union(db.query(CWERule.rule_code).filter(CWERule.is_selected == True))
                    )
                ).count()
                print(f"[DEBUG admin/tasks] 任务 {task.id}: uncertain_selected={uncertain_selected}")
                
                # 4. 不确定规则未勾选的问题数量
                print(f"[DEBUG admin/tasks] 任务 {task.id}: 开始查询不确定不勾选...")
                uncertain_unselected = db.query(StaticAnalysisIssue).filter(
                    StaticAnalysisIssue.task_id == task.id,
                    StaticAnalysisIssue.rule_accuracy_type == 'uncertain',
                    StaticAnalysisIssue.is_filtered == False
                ).filter(
                    ~StaticAnalysisIssue.rule_code.in_(
                        db.query(GJB8114Rule.rule_code).filter(GJB8114Rule.is_selected == True)
                        .union(db.query(CWERule.rule_code).filter(CWERule.is_selected == True))
                    )
                ).count()
                print(f"[DEBUG admin/tasks] 任务 {task.id}: uncertain_unselected={uncertain_unselected}")
                
                # 总问题数（四分类之和）
                total_four_category = accurate_selected + accurate_unselected + uncertain_selected + uncertain_unselected
                print(f"[DEBUG admin/tasks] 任务 {task.id}: total_four_category={total_four_category}")
                
                # 过滤后问题数：确定勾选 + 不确定勾选中AI确认的
                print(f"[DEBUG admin/tasks] 任务 {task.id}: 开始查询AI确认...")
                uncertain_selected_ai_confirmed = db.query(StaticAnalysisIssue).filter(
                    StaticAnalysisIssue.task_id == task.id,
                    StaticAnalysisIssue.rule_accuracy_type == 'uncertain',
                    StaticAnalysisIssue.is_filtered == False,
                    StaticAnalysisIssue.ai_is_real_issue == True
                ).filter(
                    StaticAnalysisIssue.rule_code.in_(
                        db.query(GJB8114Rule.rule_code).filter(GJB8114Rule.is_selected == True)
                        .union(db.query(CWERule.rule_code).filter(CWERule.is_selected == True))
                    )
                ).count()
                filtered_problems_count = accurate_selected + uncertain_selected_ai_confirmed
                print(f"[DEBUG admin/tasks] 任务 {task.id}: filtered_problems_count={filtered_problems_count}")
                
                # 标记问题数量
                print(f"[DEBUG admin/tasks] 任务 {task.id}: 开始查询标记问题...")
                marked_count = db.query(StaticAnalysisMarkedProblem).filter(
                    StaticAnalysisMarkedProblem.session_id == task.session_id
                ).count()
                print(f"[DEBUG admin/tasks] 任务 {task.id}: marked_count={marked_count}")
                
                # 问题检出准确率
                accuracy = 0.0
                if filtered_problems_count > 0 and marked_count > 0:
                    accuracy = round(marked_count / filtered_problems_count, 4)
                print(f"[DEBUG admin/tasks] 任务 {task.id}: accuracy={accuracy}")
                
                # 获取最新标记时间
                latest_marked = db.query(StaticAnalysisMarkedProblem).filter(
                    StaticAnalysisMarkedProblem.session_id == task.session_id
                ).order_by(StaticAnalysisMarkedProblem.marked_at.desc()).first()
                latest_marked_at = latest_marked.marked_at if latest_marked else None
                
                print(f"[DEBUG admin/tasks] 任务 {task.id}: marked_problems_exported={task.marked_problems_exported}")
                
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
                    'total_four_category': total_four_category,  # 总问题数（四分类之和）
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
                print(f"[DEBUG admin/tasks] 任务 {task.id}: 成功添加到列表")
            except Exception as task_e:
                print(f"[DEBUG admin/tasks] 任务 {task.id}: 处理失败: {task_e}")
                import traceback
                print(f"[DEBUG admin/tasks] 任务 {task.id}: 错误详情: {traceback.format_exc()}")
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
        
        print(f"[DEBUG admin/tasks] 最终返回 {len(task_list)} 个任务")
        logger.info(f"[静态分析管理员] 返回任务列表: 共 {len(task_list)} 个任务")
        
        return {
            "success": True,
            "tasks": task_list,
            "total": len(task_list)
        }
        
    except Exception as e:
        error_msg = f"获取静态分析任务列表失败: {str(e)}"
        print(f"[DEBUG admin/tasks] 外层异常: {error_msg}")
        logger.error(error_msg)
        import traceback
        print(f"[DEBUG admin/tasks] 异常详情: {traceback.format_exc()}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_msg)

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
            session = db.query(StaticAnalysisSession).filter(
                StaticAnalysisSession.session_id == session_id
            ).first()
            
            if not session:
                raise HTTPException(status_code=404, detail="会话不存在")
            
            return {
                "success": True,
                "session_id": session_id,
                "task_id": session.id,
                "message": "获取任务ID成功"
            }
            
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] 获取任务ID失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务ID失败: {str(e)}")

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
        logger.info(f"[详细状态API] 收到请求: session_id={session_id}")
        
        # 尝试获取增强服务
        service = None
        actual_session_id = session_id
        resolved_session_id = None
        numeric_id = None

        with _services_lock:
            service = _enhanced_services.get(session_id)
            logger.info(f"[详细状态API] 直接查询内存缓存: service={'找到' if service else '未找到'}")

        if service is None:
            try:
                numeric_id = int(session_id)
                logger.info(f"[详细状态API] 解析为数字ID: numeric_id={numeric_id}")
            except (TypeError, ValueError):
                numeric_id = None
                logger.info(f"[详细状态API] 不是数字ID，按UUID处理")

            if numeric_id is not None:
                db = get_db_session()
                try:
                    logger.info(f"[详细状态API] 尝试用数字ID查询数据库: id={numeric_id}")
                    session_obj = db.query(StaticAnalysisSession).filter(
                        StaticAnalysisSession.id == numeric_id
                    ).first()
                    if session_obj:
                        resolved_session_id = session_obj.session_id
                        logger.info(f"[详细状态API] 数据库查询成功: session_id={resolved_session_id}")
                    else:
                        logger.warning(f"[详细状态API] 数据库查询失败: 未找到id={numeric_id}的记录")
                except Exception as e:
                    logger.error(f"[详细状态API] 数据库查询出错: {e}")
                finally:
                    db.close()

            if resolved_session_id:
                actual_session_id = resolved_session_id
                with _services_lock:
                    service = _enhanced_services.get(resolved_session_id)
                    logger.info(f"[详细状态API] 用UUID查询内存缓存: service={'找到' if service else '未找到'}")

        if not service:
            # 如果内存中没有服务实例，尝试从数据库读取已完成任务的状态
            logger.info(f"[详细状态API] 内存中没有服务实例，尝试从数据库读取")
            db = get_db_session()
            try:
                session_obj = None
                
                # 优先用数字ID查询（如果传入的是数字）
                if numeric_id is not None:
                    logger.info(f"[详细状态API] 第二次数据库查询（数字ID）: id={numeric_id}")
                    try:
                        session_obj = db.query(StaticAnalysisSession).filter(
                            StaticAnalysisSession.id == numeric_id
                        ).first()
                        if session_obj:
                            logger.info(f"[详细状态API] 第二次数字ID查询成功: session_id={session_obj.session_id}, status={session_obj.status}")
                        else:
                            logger.warning(f"[详细状态API] 第二次数字ID查询失败: 未找到id={numeric_id}")
                    except Exception as e:
                        logger.error(f"[详细状态API] 数字ID查询出错: {e}")
                
                # 如果数字ID查询失败，尝试用UUID查询
                if not session_obj:
                    query_session_id = resolved_session_id if resolved_session_id else session_id
                    logger.info(f"[详细状态API] 尝试UUID查询: session_id={query_session_id}")
                    try:
                        session_obj = db.query(StaticAnalysisSession).filter(
                            StaticAnalysisSession.session_id == query_session_id
                        ).first()
                        if session_obj:
                            logger.info(f"[详细状态API] UUID查询成功: id={session_obj.id}, status={session_obj.status}")
                        else:
                            logger.warning(f"[详细状态API] UUID查询失败: 未找到session_id={query_session_id}")
                    except Exception as e:
                        logger.error(f"[详细状态API] UUID查询出错: {e}")
                
                if not session_obj:
                    # [FIX] 多worker环境下，任务可能正在其他worker处理中，返回一个友好状态而不是404
                    logger.warning(f"[详细状态API] 数据库中未找到会话: session_id={session_id}, numeric_id={numeric_id}")
                    logger.info(f"[详细状态API] 可能是多worker环境，任务正在其他worker处理中")
                    
                    # 返回一个"处理中"的状态，让前端继续轮询
                    return {
                        "success": True,
                        "session_id": session_id,
                        "gjb": {
                            "total_issues": 0,
                            "accurate_issues": 0,
                            "uncertain_issues": 0,
                            "filtered_issues": 0,
                            "retained_issues": 0,
                            "ai_processing_total": 0,
                            "ai_processed_issues": 0,
                            "current_analyzing_issue": "",
                            "tool_calls_count": 0,
                            "progress": 0,
                            "status": "processing",
                            "accurate_ready": False
                        },
                        "cwe": {
                            "total_issues": 0,
                            "accurate_issues": 0,
                            "uncertain_issues": 0,
                            "filtered_issues": 0,
                            "retained_issues": 0,
                            "ai_processing_total": 0,
                            "ai_processed_issues": 0,
                            "current_analyzing_issue": "",
                            "tool_calls_count": 0,
                            "progress": 0,
                            "status": "processing",
                            "accurate_ready": False
                        }
                    }
                
                logger.info(f"[详细状态API] 从数据库构建状态: total_issues={session_obj.total_issues}, "
                           f"accurate={session_obj.accurate_issues}, uncertain={session_obj.uncertain_issues}, "
                           f"filtered={session_obj.filtered_issues}, status={session_obj.status}")
                
                # 计算retained_issues（保留的问题数）
                total = session_obj.total_issues or 0
                filtered = session_obj.filtered_issues or 0
                retained = total - filtered
                accurate = session_obj.accurate_issues or 0
                uncertain = session_obj.uncertain_issues or 0
                
                # 假设GJB和CWE各占一半
                gjb_total = total // 2
                cwe_total = total - gjb_total
                gjb_accurate = accurate // 2
                cwe_accurate = accurate - gjb_accurate
                gjb_uncertain = uncertain // 2
                cwe_uncertain = uncertain - gjb_uncertain
                gjb_filtered = filtered // 2
                cwe_filtered = filtered - gjb_filtered
                gjb_retained = gjb_total - gjb_filtered
                cwe_retained = cwe_total - cwe_filtered
                
                detailed_status = {
                    "gjb": {
                        "total_issues": gjb_total,
                        "accurate_issues": gjb_accurate,
                        "uncertain_issues": gjb_uncertain,
                        "filtered_issues": gjb_filtered,
                        "retained_issues": gjb_retained,
                        "ai_processing_total": gjb_uncertain,
                        "ai_processed_issues": gjb_uncertain,
                        "current_analyzing_issue": "",
                        "tool_calls_count": 0,
                        "progress": 100,
                        "status": "completed",
                        "accurate_ready": True
                    },
                    "cwe": {
                        "total_issues": cwe_total,
                        "accurate_issues": cwe_accurate,
                        "uncertain_issues": cwe_uncertain,
                        "filtered_issues": cwe_filtered,
                        "retained_issues": cwe_retained,
                        "ai_processing_total": cwe_uncertain,
                        "ai_processed_issues": cwe_uncertain,
                        "current_analyzing_issue": "",
                        "tool_calls_count": 0,
                        "progress": 100,
                        "status": "completed",
                        "accurate_ready": True
                    }
                }
            finally:
                db.close()
        else:
            # 获取详细状态（从内存服务实例）
            detailed_status = service.get_detailed_status()
        
        # 调试日志：打印详细状态
        logger.info(f"[详细状态API] Session: {actual_session_id}")
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
        import traceback
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
        
        # 如果有规则覆盖，先应用到数据库
        if rule_overrides:
            from app.staticAnalysis.filter.config.default_rules_config import apply_rule_overrides_to_database
            logger.info(f"[配置API] 开始应用规则分类覆盖到数据库")
            
            db_success = apply_rule_overrides_to_database(rule_overrides)
            if not db_success:
                logger.error(f"[配置API] 应用规则覆盖到数据库失败")
                raise HTTPException(status_code=500, detail="应用规则分类覆盖到数据库失败")
            
            logger.info(f"[配置API] 规则分类覆盖已应用到数据库")
        
        # 保存配置到JSON文件
        success = save_default_rules_config(gjb_rules, cwe_rules, rule_overrides, custom_filters, max_issues_per_rule)
        
        # [NEW] 保存勾选状态到数据库
        logger.info(f"[配置API] 开始保存勾选状态到数据库")
        from app.staticAnalysis.filter.config.default_rules_config import save_selected_rules_to_database
        db_save_success = save_selected_rules_to_database(gjb_rules, cwe_rules)
        if db_save_success:
            logger.info(f"[配置API] 勾选状态已保存到数据库: GJB={len(gjb_rules)}条, CWE={len(cwe_rules)}条")
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
        
        # [NEW] 优先从数据库加载勾选状态
        logger.info(f"[配置API] 尝试从数据库加载勾选状态")
        from app.staticAnalysis.filter.config.default_rules_config import load_selected_rules_from_database
        db_selected_rules = load_selected_rules_from_database()
        
        if db_selected_rules["gjb_rules"] or db_selected_rules["cwe_rules"]:
            # 如果数据库有勾选数据，优先使用数据库的
            logger.info(f"[配置API] 使用数据库勾选状态: GJB={len(db_selected_rules['gjb_rules'])}条, CWE={len(db_selected_rules['cwe_rules'])}条")
            gjb_rules = db_selected_rules["gjb_rules"]
            cwe_rules = db_selected_rules["cwe_rules"]
            source = "database"
        else:
            # 数据库没有数据，回退到配置文件
            logger.info(f"[配置API] 数据库无勾选数据，使用配置文件")
            gjb_rules = config["gjb_rules"]
            cwe_rules = config["cwe_rules"]
            source = "config_file"
        
        logger.info(f"[配置API] 配置存在: {has_config}, GJB规则数: {len(gjb_rules)}, CWE规则数: {len(cwe_rules)}, 来源: {source}")
        logger.info(f"[配置API] 规则分类覆盖: GJB={gjb_override_count}, CWE={cwe_override_count}")
        logger.info(f"[配置API] 自定义过滤规则数: {len(custom_filters)}")
        logger.info(f"[配置API] 问题数量限制: {max_issues_per_rule if max_issues_per_rule > 0 else '不限制'}")
        
        return {
            "success": True,
            "has_config": has_config,
            "gjb_rules": gjb_rules,
            "cwe_rules": cwe_rules,
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
    rule_type: str = Query('gjb', description="规则类型: gjb 或 cwe")
) -> Dict[str, Any]:
    """
    获取代码视图所需的数据
    
    Args:
        task_id: 任务ID
        rule_type: 规则类型 ('gjb' 或 'cwe')
    
    Returns:
        {
            "success": true,
            "data": {
                "files": [
                    {
                        "file_name": "xxx.c",
                        "file_path": "path/to/xxx.c",
                        "source_code": "..."
                    },
                    ...
                ],
                "problems": [
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
    try:
        logger.info(f"[代码视图API] 获取代码视图数据: task_id={task_id}, rule_type={rule_type}")
        
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
            
            # 2. 扫描代码库中的文件
            import glob
            files_data = []
            
            # 支持的文件扩展名
            supported_extensions = ['.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.hxx']
            
            for ext in supported_extensions:
                pattern = os.path.join(codebase_path, "**", f"*{ext}")
                matching_files = glob.glob(pattern, recursive=True)
                
                for file_path in matching_files:
                    try:
                        # 尝试多种编码读取文件源代码，优先UTF-8，然后GBK、GB2312等
                        source_code = None
                        encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin-1']
                        
                        for encoding in encodings:
                            try:
                                with open(file_path, 'r', encoding=encoding) as f:
                                    source_code = f.read()
                                # 如果成功读取，跳出循环
                                break
                            except (UnicodeDecodeError, LookupError):
                                continue
                        
                        # 如果所有编码都失败，使用UTF-8并替换错误字符
                        if source_code is None:
                            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                                source_code = f.read()
                        
                        # 计算相对路径
                        rel_path = os.path.relpath(file_path, codebase_path)
                        file_name = os.path.basename(file_path)
                        
                        files_data.append({
                            "file_name": file_name,
                            "file_path": rel_path,
                            "source_code": source_code
                        })
                        
                    except Exception as e:
                        logger.warning(f"[代码视图API] 读取文件失败: {file_path}, 错误: {str(e)}")
                        continue
            
            logger.info(f"[代码视图API] 扫描到 {len(files_data)} 个代码文件")
            file_source_map = {
                item.get("file_path"): item.get("source_code", "")
                for item in files_data
                if item.get("file_path")
            }
            file_source_map.update({
                item.get("file_name"): item.get("source_code", "")
                for item in files_data
                if item.get("file_name")
            })
            
            # 3. 查询保留的问题（未被过滤的问题）
            issues = db.query(StaticAnalysisIssue).filter(
                StaticAnalysisIssue.task_id == db_task_id,
                StaticAnalysisIssue.is_filtered == False,
                StaticAnalysisIssue.rule_type == rule_type
            ).all()
            
            # [NEW] 为每个问题组装问题单格式（四段式）
            def strip_leading_suggestion(s: str) -> str:
                """去除建议前缀"""
                t = (s or '').strip()
                if t.startswith('建议'):
                    return t[2:].lstrip('：: \u3000')
                if t.startswith('修改意见：'):
                    return t[5:]
                if t.startswith('修改意见:'):
                    return t[4:]
                return t
            
            def resolve_issue_source_code(issue_file: str, issue_line: str, context: int = 3) -> str:
                """从代码库源码中提取问题行附近上下文。"""
                if not issue_file:
                    return ''

                normalized_issue_file = str(issue_file).replace('\\', '/').strip()
                source_code = file_source_map.get(normalized_issue_file) or file_source_map.get(os.path.basename(normalized_issue_file))

                if not source_code:
                    for file_key, code in file_source_map.items():
                        normalized_key = str(file_key or '').replace('\\', '/')
                        if normalized_key.endswith(normalized_issue_file) or normalized_issue_file.endswith(normalized_key):
                            source_code = code
                            break

                if not source_code:
                    return ''

                lines = source_code.splitlines()
                try:
                    line_no_match = __import__('re').search(r'\d+', str(issue_line or ''))
                    line_no = int(line_no_match.group(0)) if line_no_match else 0
                except Exception:
                    line_no = 0

                return build_function_aware_source_snippet(source_code, line_no, context)

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
                        # [FIX] 规则代码格式转换：GJB_R_01_08_02 -> R-1-8-2
                        db_rule_code = issue.rule_code
                        if issue.rule_type == 'gjb' and issue.rule_code.startswith('GJB_R_'):
                            # 提取数字部分 GJB_R_01_08_02 -> 01, 08, 02 -> R-1-8-2
                            parts = issue.rule_code.split('_')
                            if len(parts) == 5:
                                db_rule_code = f"R-{int(parts[2])}-{int(parts[3])}-{int(parts[4])}"
                                print(f"[DEBUG 规则库] 格式转换: {issue.rule_code} -> {db_rule_code}")
                        
                        if issue.rule_type == 'gjb':
                            r = db.query(GJB8114Rule).filter(GJB8114Rule.rule_code == db_rule_code).first()
                        else:
                            r = db.query(CWERule).filter(CWERule.rule_code == db_rule_code).first()
                        
                        if r:
                            rule_problem_name = getattr(r, 'problem_name', '') or ''
                            rule_requirement = getattr(r, 'requirement_description', '') or ''
                            rule_impact = getattr(r, 'impact_analysis', '') or ''
                            rule_suggestion = getattr(r, 'improvement_suggestion', '') or ''
                            
                            # [DEBUG] 打印规则库查询结果（仅在字段为空时警告）
                            if not rule_impact or not rule_suggestion:
                                print(f"[DEBUG 规则库警告] rule_code={db_rule_code}, impact为空={not rule_impact}, suggestion为空={not rule_suggestion}")
                        else:
                            print(f"[DEBUG 规则库] 未找到规则: rule_code={db_rule_code}(原始={issue.rule_code}), rule_type={issue.rule_type}")
                    except Exception as e:
                        logger.warning(f"[代码视图API] 查询规则失败: {issue.rule_code}, {e}")
                        print(f"[DEBUG 规则库] 查询异常: {e}")
                
                # 组装问题单内容
                issue_name = rule_problem_name or issue.issue_name or ""
                file_path = issue.issue_file or ""
                line_number = issue.issue_line or ""
                defect_desc = issue.issue_description or ""
                problem_source = f"{file_path}文件{line_number}行" if file_path and line_number else "代码文件"
                issue_source_code = resolve_issue_source_code(file_path, line_number)
                source_code_part = f"\n源代码为：\n{issue_source_code}" if issue_source_code else ""
                
                # 四段式
                guifan = "GJB8114" if issue.rule_type == "gjb" else "CWE"
                xuqiu_miaoshu = f"根据{guifan}编码规范要求{issue.rule_code}条规定：{rule_requirement}".strip()
                four_part = (
                    f"需求描述：{xuqiu_miaoshu}。\n"
                    f"问题描述：{issue_name}。\n"
                    f"问题定位：{problem_source}，具体内容如下：\"{defect_desc}\"。{source_code_part}\n"
                    f"影响分析：{rule_impact}"
                ).replace("。。", "。")
                
                # 测评单位意见
                sug_core = strip_leading_suggestion(rule_suggestion)
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
                    "ai_analyzed": issue.ai_analyzed,
                    "ai_is_real_issue": issue.ai_is_real_issue,
                    "ai_confidence": issue.ai_confidence,
                    "ai_analysis_result": issue.ai_analysis_result,
                    # [NEW] 自动修复状态：0=未修复 1=已生成待确认 2=已应用 3=已忽略
                    "fix_status": issue.fix_status or 0,
                    "fix_id": issue.fix_id,
                    # [NEW] 问题单格式内容
                    "problem_sheet": {
                        "issue_name": issue_name,  # 问题名称
                        "four_part_description": four_part,  # 问题描述（四段式）
                        "test_unit_opinion": test_unit_opinion  # 测评单位意见
                    }
                })
            
            logger.info(f"[代码视图API] 查询到 {len(problems_data)} 个保留问题")
            
            # [NEW] 统计每个规则下AI确认的问题数量（用于过滤后问题分类）
            # 需要查询所有不确定规则的问题，包括AI确认的
            all_uncertain_issues = db.query(StaticAnalysisIssue).filter(
                StaticAnalysisIssue.task_id == db_task_id,
                StaticAnalysisIssue.rule_type == rule_type,
                StaticAnalysisIssue.rule_accuracy_type == 'uncertain'
            ).all()
            
            rule_ai_confirmed_count = {}
            for issue in all_uncertain_issues:
                rule_code = issue.rule_code
                if rule_code and issue.ai_is_real_issue is True:
                    rule_ai_confirmed_count[rule_code] = rule_ai_confirmed_count.get(rule_code, 0) + 1
            
            # 4. 获取用户选中的规则列表（从数据库读取）
            # [FIX] 改为从数据库读取勾选状态，而不是配置文件
            # [NOTE] 使用全局导入的 GJB8114Rule, CWERule
            if rule_type == 'gjb':
                db_selected = db.query(GJB8114Rule.rule_code).filter(GJB8114Rule.is_selected == True).all()
                # 转换回原始格式（如 A-1-2）
                selected_rules = set()
                for r in db_selected:
                    parts = r[0].split('_')
                    if len(parts) == 5 and parts[0] == 'GJB' and parts[1] == 'R':
                        original_code = f"{parts[2]}-{parts[3]}-{parts[4]}"
                        selected_rules.add(original_code)
                    else:
                        selected_rules.add(r[0])
            else:  # cwe
                db_selected = db.query(CWERule.rule_code).filter(CWERule.is_selected == True).all()
                selected_rules = set([r[0] for r in db_selected])
            
            logger.info(f"[代码视图API] 从数据库读取勾选规则数量: {len(selected_rules)}")
            
            # 5. 提取当前问题涉及的所有规则，并获取规则详细信息
            rule_codes_in_problems = set()
            for problem in problems_data:
                if problem.get('rule_code'):
                    rule_codes_in_problems.add(problem['rule_code'])
            
            logger.info(f"[代码视图API] 问题中涉及的规则数量: {len(rule_codes_in_problems)}")
            
            # 获取规则详细信息
            rules_info = []
            rules_db = _gjb_db if rule_type == 'gjb' else _cwe_db
            
            # 统计每个规则对应的问题数量
            rule_problem_count = {}
            for problem in problems_data:
                rule_code = problem.get('rule_code')
                if rule_code:
                    rule_problem_count[rule_code] = rule_problem_count.get(rule_code, 0) + 1
            
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
                        'rule_type': rule_type,
                        'accuracy_type': accuracy,
                        'is_selected': is_selected,  # 新增：返回勾选状态
                        'problem_count': problem_count,
                        'ai_confirmed_count': ai_confirmed_count,  # [NEW] AI确认的问题数
                        'is_in_filtered': is_in_filtered,  # [NEW] 是否属于过滤后问题
                        'filtered_badge': filtered_badge  # [NEW] 过滤后问题的标记类型
                    })
                else:
                    # 如果数据库中没有该规则，使用基本信息
                    logger.warning(f"[代码视图API] 规则数据库中未找到规则: {rule_code}")
                    rules_info.append({
                        'rule_code': rule_code,
                        'rule_name': rule_code,
                        'rule_description': '',
                        'rule_type': rule_type,
                        'accuracy_type': 'uncertain',
                        'is_selected': True,  # 默认勾选
                        'problem_count': rule_problem_count.get(rule_code, 0),
                        'ai_confirmed_count': 0,
                        'is_in_filtered': False,
                        'filtered_badge': None
                    })
            
            logger.info(f"[代码视图API] 获取到 {len(rules_info)} 条规则详情")
            
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
    db: Session = Depends(get_db_session)
) -> StreamingResponse:
    """
    导出已标记的问题到Excel文件
    
    Args:
        task_id: 任务ID
        request_data: 请求体数据，包含：
            - rule_type: 规则类型 (gjb/cwe)
            - problems: 已标记的问题列表
        db: 数据库会话
    
    Returns:
        Excel文件响应
    """
    try:
        from datetime import datetime
        from io import BytesIO
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Alignment
        except ImportError:
            raise HTTPException(status_code=500, detail="导出失败: 服务器缺少openpyxl依赖")
        
        rule_type = request_data.get('rule_type', 'gjb')
        problems = request_data.get('problems', [])
        
        print(f"[DEBUG导出] 开始处理, task_id={task_id}, rule_type={rule_type}, problems_count={len(problems)}")
        logger.info(f"[导出已标记问题] task_id={task_id}, rule_type={rule_type}, problems_count={len(problems)}")
        
        if not problems:
            raise HTTPException(status_code=400, detail="没有已标记的问题")
        
        # A-H列表头
        columns = [
            "测试活动", "问题类型", "问题等级", "问题数目", "问题名称",
            "问题来源", "问题描述（四段式）", "测评单位意见"
        ]

        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = '已标记问题'
        worksheet.append(columns)

        # 去除建议前缀，避免重复“建议”
        def strip_leading_suggestion(s: str) -> str:
            t = (s or '').strip()
            if t.startswith('建议'):
                return t[2:].lstrip('：: \u3000')
            if t.startswith('修改意见：'):
                return t[5:]
            if t.startswith('修改意见:'):
                return t[4:]
            return t

        def get_source_code(problem_data: Dict[str, Any]) -> str:
            return (
                problem_data.get('source_code')
                or problem_data.get('code_snippet')
                or problem_data.get('code_context')
                or ""
            )

        def get_problem_level(problem_data: Dict[str, Any]) -> str:
            # 固定为“一般问题”按新格式要求
            return '一般问题'

        def get_rule(problem_data: Dict[str, Any]) -> str:
            return problem_data.get('rule_code') or problem_data.get('gjb_rule_code') or ''

        # DB 取规则文本
        from ..database.postgresql_database import get_db_session as _get_db_session
        from ..database.postgresql_models import CWERule as _CWERule, GJB8114Rule as _GJBRule
        db_rules = _get_db_session()
        file_source_map = {}
        export_session = None
        try:
            numeric_task_id = int(task_id)
        except (TypeError, ValueError):
            numeric_task_id = None

        if numeric_task_id is not None:
            export_session = db_rules.query(StaticAnalysisSession).filter(
                StaticAnalysisSession.id == numeric_task_id
            ).first()
        if not export_session:
            export_session = db_rules.query(StaticAnalysisSession).filter(
                StaticAnalysisSession.session_id == task_id
            ).first()

        if export_session and export_session.codebase_path:
            supported_extensions = ['.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.hxx']
            for ext in supported_extensions:
                pattern = os.path.join(export_session.codebase_path, "**", f"*{ext}")
                for source_file_path in __import__('glob').glob(pattern, recursive=True):
                    try:
                        source_code = None
                        for encoding in ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin-1']:
                            try:
                                with open(source_file_path, 'r', encoding=encoding) as f:
                                    source_code = f.read()
                                break
                            except (UnicodeDecodeError, LookupError):
                                continue
                        if source_code is None:
                            with open(source_file_path, 'r', encoding='utf-8', errors='replace') as f:
                                source_code = f.read()
                        rel_path = os.path.relpath(source_file_path, export_session.codebase_path)
                        file_source_map[rel_path.replace('\\', '/')] = source_code
                        file_source_map[os.path.basename(source_file_path)] = source_code
                    except Exception as e:
                        logger.warning(f"[export_marked_problems] read source failed: {source_file_path}, {e}")

        def resolve_export_source_code(issue_file: str, issue_line: str, context: int = 3) -> str:
            if not issue_file:
                return ''
            normalized_issue_file = str(issue_file).replace('\\', '/').strip()
            source_code = file_source_map.get(normalized_issue_file) or file_source_map.get(os.path.basename(normalized_issue_file))
            if not source_code:
                for file_key, code in file_source_map.items():
                    normalized_key = str(file_key or '').replace('\\', '/')
                    if normalized_key.endswith(normalized_issue_file) or normalized_issue_file.endswith(normalized_key):
                        source_code = code
                        break
            if not source_code:
                return ''
            source_lines = source_code.splitlines()
            try:
                line_no_match = __import__('re').search(r'\d+', str(issue_line or ''))
                line_no = int(line_no_match.group(0)) if line_no_match else 0
            except Exception:
                line_no = 0
            return build_function_aware_source_snippet(source_code, line_no, context)
        try:
            for problem in problems:
                # 来源字段（K/L/M）
                file_path = problem.get('issue_file') or ''
                line_number = problem.get('issue_line') or ''
                defect_desc = problem.get('issue_description') or ''
                problem_source = f"{file_path}文件{line_number}行" if file_path and line_number else "代码文件"

                issue_source_code = get_source_code(problem) or resolve_export_source_code(file_path, line_number)
                source_code_part = f"\n源代码为：\n{issue_source_code}" if issue_source_code else ""

                rule_code = get_rule(problem)
                rt = (problem.get('rule_type') or rule_type or '').lower()

                # 规则库四列
                rule_problem_name = ''
                rule_requirement = ''
                rule_impact = ''
                rule_suggestion = ''
                if rt == 'gjb':
                    r = db_rules.query(_GJBRule).filter(_GJBRule.rule_code == rule_code).first()
                else:
                    r = db_rules.query(_CWERule).filter(_CWERule.rule_code == rule_code).first()
                if r:
                    rule_problem_name = getattr(r, 'problem_name', '') or ''
                    rule_requirement = getattr(r, 'requirement_description', '') or ''
                    rule_impact = getattr(r, 'impact_analysis', '') or ''
                    rule_suggestion = getattr(r, 'improvement_suggestion', '') or ''

                # E：问题名称（优先规则库）
                issue_name = rule_problem_name or problem.get('issue_name', '')

                # G：四段式
                guifan = 'GJB8114' if rt == 'gjb' else 'CWE'
                xuqiu_miaoshu = f"根据{guifan}编码规范要求{rule_code}条规定：{rule_requirement}".strip()
                four_part = (
                    f"需求描述：{xuqiu_miaoshu}。\n"
                    f"问题描述：{issue_name}。\n"
                    f"问题定位：{problem_source}，具体内容如下：\"{defect_desc}\"。{source_code_part}\n"
                    f"影响分析：{rule_impact}"
                ).replace('。。', '。')

                # H：测评单位意见
                sug_core = strip_leading_suggestion(rule_suggestion)
                test_unit_opinion = (
                    "1.请确认是否是问题\n"
                    f"2. 若是问题，建议{sug_core}"
                )

                row = [
                    '静态分析',                   # A 测试活动
                    '程序问题',                   # B 问题类型
                    get_problem_level(problem),  # C 问题等级
                    '1',                         # D 问题数目
                    issue_name,                   # E 问题名称
                    problem_source,               # F 问题来源
                    four_part,                    # G 问题描述（四段式）
                    test_unit_opinion             # H 测评单位意见
                ]
                worksheet.append(row)
        finally:
            db_rules.close()

        wrap_alignment = Alignment(wrapText=True, vertical="top")
        # A-H 列宽
        column_widths = [12, 12, 12, 10, 30, 28, 70, 50]

        for idx, column_cells in enumerate(worksheet.columns, start=1):
            for cell in column_cells:
                cell.alignment = wrap_alignment
            width = column_widths[idx - 1] if idx - 1 < len(column_widths) else 20
            worksheet.column_dimensions[column_cells[0].column_letter].width = width

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"marked_problems_task_{task_id}_{timestamp}.xlsx"
        buffer = BytesIO()
        workbook.save(buffer)
        workbook.close()
        buffer.seek(0)

        logger.info(f"[导出已标记问题] 导出成功: {filename}")
        
        # [NEW] 标记任务已导出过标记问题（类比函数审查）
        print(f"[DEBUG导出] 开始更新导出状态, task_id={task_id}, type={type(task_id)}")
        try:
            # 首先尝试作为数字ID查询session
            session = None
            try:
                numeric_id = int(task_id)
                print(f"[DEBUG导出] 尝试作为数字ID查询: {numeric_id}")
                session = db.query(StaticAnalysisSession).filter(
                    StaticAnalysisSession.id == numeric_id
                ).first()
                print(f"[DEBUG导出] 数字ID查询结果: {session}")
            except (ValueError, TypeError) as e:
                print(f"[DEBUG导出] 不是数字ID: {e}")
                pass
            
            # 如果不是数字ID或没找到，尝试作为session_id查询
            if not session:
                print(f"[DEBUG导出] 尝试作为session_id查询: {task_id}")
                session = db.query(StaticAnalysisSession).filter(
                    StaticAnalysisSession.session_id == task_id
                ).first()
                print(f"[DEBUG导出] session_id查询结果: {session}")
            
            if session:
                print(f"[DEBUG导出] 找到session: id={session.id}, session_id={session.session_id}, 当前导出状态={session.marked_problems_exported}")
                session.marked_problems_exported = True
                db.commit()
                print(f"[DEBUG导出] 导出状态已更新为True, session_id={session.session_id}")
                logger.info(f"[导出已标记问题] 任务导出状态已更新: session_id={session.session_id}")
            else:
                print(f"[DEBUG导出] 未找到session, task_id={task_id}")
        except Exception as e:
            print(f"[DEBUG导出] 更新导出状态异常: {e}")
            import traceback
            print(f"[DEBUG导出] 异常详情: {traceback.format_exc()}")
            logger.warning(f"[导出已标记问题] 更新导出状态失败: {e}")
            # 导出状态更新失败不影响导出功能

        headers = {"Content-Disposition": f"attachment; filename={filename}"}
        return StreamingResponse(
            buffer,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers=headers
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[导出已标记问题] 导出失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


# ==================== 问题单准确率反馈API ====================

class ProblemSheetAccuracyFeedbackRequest(BaseModel):
    """问题单准确率反馈请求"""
    accuracy_rate: str  # 50%以下、50%-70%、70%-85%、85%-95%、95%-100%


@router.post("/{task_id}/problem_sheet_accuracy_feedback")
def submit_problem_sheet_accuracy_feedback(
    task_id: str,  # [FIX] 改为字符串类型，支持UUID和数字ID
    request: ProblemSheetAccuracyFeedbackRequest,
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
        
        logger.info(f"[问题单准确率反馈] 成功: task_id={task_id}, rate={request.accuracy_rate}")
        
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
        logger.error(f"[问题单准确率反馈] 失败: task_id={task_id}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"提交反馈失败: {str(e)}")


@router.get("/{task_id}/problem_sheet_accuracy_status")
def get_problem_sheet_accuracy_status(
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
        logger.error(f"[问题单准确率状态] 失败: task_id={task_id}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}") 
