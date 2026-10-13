"""
文件上传API端点
处理需求文档、策划文档、目录文档的上传
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
import os
import uuid
import shutil
import json
import asyncio
from pathlib import Path
from typing import Optional
from fastapi.concurrency import run_in_threadpool

try:
    from ..utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

from ..utils.logging_utils.log_utils import setup_logger

router = APIRouter(tags=["文件上传"])
logger = setup_logger(__name__)

# 创建上传目录 - 修复路径指向backend目录下的uploads
# 获取backend目录的绝对路径
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
UPLOAD_BASE_DIR = BACKEND_DIR / "uploads" / "dynamic" / "configuration"
UPLOAD_BASE_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload-requirement")
async def upload_requirement_document(
    requirement_file: UploadFile = File(...),
    session_id: Optional[str] = Form(None)
):
    """
    上传需求文档并自动提取目录信息
    """
    try:
        # 🚀 使用新的pywin32处理器
        from ..utils.pywin32_processor import process_document_concurrent
        from datetime import datetime
        
        # 如果没有提供session_id，创建新的
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # 创建会话目录
        session_dir = UPLOAD_BASE_DIR / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存需求文档
        file_path = session_dir / f"requirement_{requirement_file.filename}"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(requirement_file.file, buffer)
        
        logger.info(f"需求文档上传成功: {file_path}")
        
        # 🚀 初始化状态文件（先写入基础信息，提取结果由后台任务写入）
        try:
            from ..service.state_manager import GenerationStateManager
            
            state_manager = GenerationStateManager(session_dir)
            
            # 准备需求文档信息
            requirement_doc_info = {
                "original_path": str(file_path.relative_to(session_dir)),
                "standardized_path": "",  # 标准化文档路径将在标准化完成后更新
                "upload_time": datetime.now().isoformat()
            }
            
            # 准备基本信息（初始为空）
            basic_info = {}
            
            # 初始化状态文件
            state_manager.initialize_state(
                requirement_doc_info=requirement_doc_info,
                basic_info=basic_info,
                catalog_items=[]
            )
            
            logger.info(f"状态文件初始化成功: {session_dir / 'generation_state.json'}")
        except Exception as e:
            logger.warning(f"初始化状态文件失败: {str(e)}")
            # 不影响主流程，继续执行

        # ✅ 后台启动：目录提取（落盘catalog_extraction.json + 更新state.catalog_items）
        async def _run_catalog_extraction_background():
            try:
                result = await process_document_concurrent(str(file_path), session_id)
                catalog_extraction = (result or {}).get("catalog_extraction", {}) or {}

                # 写入缓存文件，供轮询接口读取
                cache_path = session_dir / "catalog_extraction.json"
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(catalog_extraction, f, ensure_ascii=False, indent=2)

                # 同步更新状态文件中的catalog_items
                try:
                    from ..service.state_manager import GenerationStateManager
                    sm = GenerationStateManager(session_dir)
                    state = sm.load_state() or {}
                    state["catalog_items"] = catalog_extraction.get("filtered_items", []) or []
                    state["last_updated"] = datetime.now().isoformat()
                    sm.save_state(state)
                except Exception as e:
                    logger.warning(f"更新状态文件catalog_items失败: {e}")

                logger.info(f"[BG] 目录提取完成，缓存已写入: {cache_path}")
            except Exception as e:
                logger.error(f"[BG] 目录提取失败: {e}")
                try:
                    cache_path = session_dir / "catalog_extraction.json"
                    with open(cache_path, "w", encoding="utf-8") as f:
                        json.dump({
                            "status": "error",
                            "message": f"目录提取失败: {str(e)}",
                            "catalog_items": [],
                            "filtered_items": []
                        }, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass

        asyncio.create_task(_run_catalog_extraction_background())

        # ✅ 后台启动：软件信息提取（落盘software_info.json，供轮询接口读取）
        try:
            from ..service.software_config.software_info_extract.software_info_service import get_software_info_service
            software_service = get_software_info_service()
            asyncio.create_task(run_in_threadpool(software_service.extract_software_info_from_session, session_id))
        except Exception as e:
            logger.warning(f"启动后台软件信息提取失败（不影响主流程）: {e}")
        
        return {
            "status": "success",
            "message": "需求文档上传成功，正在后台提取测试需求与软件信息",
            "session_id": session_id,
            "file_path": str(file_path),
            "filename": requirement_file.filename,
            "file_size": requirement_file.size,
            # 🚀 文档标准化信息（后台处理）
            "standardization": {
                "success": True,  # 后台标准化已启动
                "status": "processing",  # 标准化正在后台进行
                "extraction_source": "原始文档（后台标准化进行中）"
            },
            "extraction_status": {
                "catalog": "processing",
                "software": "processing"
            }
        }
        
    except Exception as e:
        logger.error(f"需求文档上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文档上传失败: {str(e)}")


@router.post("/upload-planning")
async def upload_planning_document(
    planning_file: UploadFile = File(...),
    session_id: str = Form(...)
):
    """
    上传策划文档
    """
    try:
        # 检查会话目录是否存在
        session_dir = UPLOAD_BASE_DIR / session_id
        if not session_dir.exists():
            raise HTTPException(status_code=404, detail="会话不存在，请先上传需求文档")
        
        # 保存策划文档
        file_path = session_dir / f"planning_{planning_file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(planning_file.file, buffer)
        
        logger.info(f"策划文档上传成功: {file_path}")
        
        return {
            "status": "success",
            "message": "策划文档上传成功",
            "session_id": session_id,
            "file_path": str(file_path),
            "filename": planning_file.filename,
            "file_size": planning_file.size
        }
        
    except Exception as e:
        logger.error(f"策划文档上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文档上传失败: {str(e)}")


@router.post("/upload-catalog")
async def upload_catalog_document(
    catalog_file: UploadFile = File(...),
    session_id: str = Form(...)
):
    """
    上传需求目录文档
    """
    try:
        # 检查会话目录是否存在
        session_dir = UPLOAD_BASE_DIR / session_id
        if not session_dir.exists():
            raise HTTPException(status_code=404, detail="会话不存在，请先上传需求文档")
        
        # 验证文件类型
        if not catalog_file.filename.lower().endswith('.docx'):
            raise HTTPException(status_code=400, detail="需求目录文档必须是docx格式")
        
        # 保存目录文档
        file_path = session_dir / f"catalog_{catalog_file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(catalog_file.file, buffer)
        
        logger.info(f"需求目录文档上传成功: {file_path}")
        
        return {
            "status": "success",
            "message": "需求目录文档上传成功",
            "session_id": session_id,
            "file_path": str(file_path),
            "filename": catalog_file.filename,
            "file_size": catalog_file.size
        }
        
    except Exception as e:
        logger.error(f"需求目录文档上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文档上传失败: {str(e)}")


@router.post("/upload-code")
async def upload_code_for_analysis(
    code_file: UploadFile = File(...),
    task_id: Optional[str] = Form(None)
):
    """
    上传代码文件进行行数统计分析
    
    Args:
        code_file: 上传的代码文件（支持.zip压缩包或单个代码文件）
        task_id: 可选的任务ID，如果不提供会自动生成
        
    Returns:
        包含代码统计信息的响应
    """
    try:
        # 导入代码分析功能
        from ..service.software_config.line_count.code_statistics import analyze_code_statistics
        
        # 生成或使用提供的任务ID
        if not task_id:
            task_id = str(uuid.uuid4())
        
        log_info(f"开始处理代码文件上传: {code_file.filename}, 任务ID: {task_id}", "upload_api")
        
        # 验证文件类型
        allowed_extensions = {'.zip', '.py', '.c', '.cpp', '.cc', '.cxx', '.c++', 
                            '.h', '.hpp', '.hxx', '.h++', '.java', '.js', '.ts', 
                            '.go', '.cs', '.php', '.rb', '.swift', '.kt', '.rs', 
                            '.scala', '.m', '.mm', '.f', '.f90', '.f95'}
        
        file_ext = Path(code_file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的文件类型: {file_ext}。支持的类型: {', '.join(sorted(allowed_extensions))}"
            )
        
        # 创建任务目录
        task_dir = UPLOAD_BASE_DIR / task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存上传的文件
        file_path = task_dir / code_file.filename
        with open(file_path, "wb") as buffer:
            content = await code_file.read()
            buffer.write(content)
        
        log_info(f"文件已保存到: {file_path}", "upload_api")
        
        # 分析代码统计
        analysis_result = analyze_code_statistics(
            file_path=str(file_path),
            task_id=task_id,
            upload_dir=str(UPLOAD_BASE_DIR)
        )
        
        log_info(f"代码分析完成: {analysis_result.get('total_lines', 0)} 行代码", "upload_api")
        
        return {
            "status": "success",
            "message": "代码文件上传并分析成功",
            "task_id": task_id,
            "file_info": {
                "filename": code_file.filename,
                "size": len(content),
                "saved_path": str(file_path)
            },
            "analysis_result": analysis_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"代码文件上传失败: {str(e)}", "upload_api")
        raise HTTPException(status_code=500, detail=f"代码文件上传失败: {str(e)}")


@router.get("/standardization-status/{session_id}")
async def get_standardization_status(session_id: str):
    """
    查询文档标准化状态（增强版）
    """
    try:
        # 🚀 使用标准化管理器获取详细状态
        from ..utils.standardization_manager import get_standardization_manager
        standardization_manager = get_standardization_manager()
        
        progress_info = standardization_manager.get_standardization_progress_info(session_id)
        
        logger.info(f"查询标准化状态: {session_id}, 状态: {progress_info.get('status')}")
        return progress_info
            
    except Exception as e:
        logger.error(f"查询标准化状态失败: {e}")
        return {
            "status": "error",
            "message": f"查询状态失败: {e}",
            "has_standardized_doc": False
        }


@router.post("/confirm-catalog")
async def confirm_catalog(
    session_id: str = Form(...),
    catalog_content: str = Form(...)
):
    """
    确认并保存用户编辑的目录内容
    """
    try:
        from ..utils.spire_doc import parse_and_validate_catalog
        from datetime import datetime
        
        log_info(f"处理目录确认请求，会话ID: {session_id}", "upload_api")
        
        # 检查会话目录是否存在
        session_dir = UPLOAD_BASE_DIR / session_id
        if not session_dir.exists():
            raise HTTPException(status_code=404, detail="会话不存在，请先上传需求文档")
        
        # 解析和验证目录内容
        parse_result = parse_and_validate_catalog(catalog_content)
        
        if not parse_result['validation']['is_valid']:
            return {
                "status": "error",
                "message": "目录内容验证失败",
                "validation": parse_result['validation'],
                "catalog_items": parse_result['catalog_items']
            }
        
        # 保存目录内容到文件
        catalog_file_path = session_dir / "catalog_confirmed.txt"
        with open(catalog_file_path, "w", encoding="utf-8") as f:
            f.write(catalog_content)
        
        log_info(f"目录内容已保存到: {catalog_file_path}", "upload_api")

        # ✅ 将“需求已确认”写入状态文件，供前端断点续传/步骤条件判断
        try:
            from ..service.state_manager import GenerationStateManager
            state_manager = GenerationStateManager(session_dir)
            state = state_manager.load_state() or {}
            state["catalog_confirmed"] = True
            state["catalog_confirmed_at"] = datetime.now().isoformat()
            state["catalog_confirmed_file"] = str(catalog_file_path)
            state["last_updated"] = datetime.now().isoformat()
            state_manager.save_state(state)
        except Exception as e:
            log_warning(f"写入catalog_confirmed状态失败（不影响主流程）: {e}", "upload_api")
        
        # 🎯 新增：缓存需求位置信息
        position_cache_result = {"success": False, "cached_count": 0}
        try:
            from ..utils.position_cache_manager import get_position_cache_manager
            
            # 查找需求规格说明文档
            requirement_doc_path = None
            for file_path in session_dir.glob("requirement_*.docx"):
                requirement_doc_path = str(file_path)
                break
            
            if requirement_doc_path:
                # 获取需求名称列表
                requirement_names = [item['name'] for item in parse_result['catalog_items']]
                
                # 📌 Step 3: 缓存需求位置信息
                try:
                    position_manager = get_position_cache_manager(debug_mode=False)  # 关闭debug，减少日志输出
                    cache_success = position_manager.cache_requirement_positions(
                        session_id=session_id,
                        requirement_document_path=requirement_doc_path,
                        catalog_items=requirement_names
                    )
                    
                    position_cache_result = {
                        "success": cache_success,
                        "cached_count": len(requirement_names) if cache_success else 0
                    }
                    
                    if cache_success:
                        log_info(f"位置信息缓存成功: {len(requirement_names)} 个需求", "upload_api")
                    else:
                        log_warning(f"位置信息缓存失败", "upload_api")
                except Exception as cache_error:
                    log_error(f"位置信息缓存异常: {str(cache_error)}", "upload_api")
                
            else:
                log_warning(f"未找到需求规格说明文档，跳过位置缓存", "upload_api")
                
        except Exception as cache_error:
            log_error(f"位置信息缓存异常: {str(cache_error)}", "upload_api")
        
        # 🚀 新增：创建标准化需求文档
        standardization_result = {"success": False, "standardized_path": None}
        try:
            from ..utils.spire_doc.document_standardizer import create_standardized_requirement_document
            
            # 查找需求规格说明文档
            requirement_doc_path = None
            for file_path in session_dir.glob("requirement_*.docx"):
                requirement_doc_path = str(file_path)
                break
            
            if requirement_doc_path:
                # 检查是否存在目录确认文件（txt格式）
                catalog_confirmed_path = session_dir / "catalog_confirmed.txt"
                
                if catalog_confirmed_path.exists():
                    log_info("发现目录确认文件，开始创建标准化需求文档", "upload_api")
                    
                    # 使用原始需求文档作为目录和内容来源进行标准化
                    standardized_path = create_standardized_requirement_document(
                        catalog_path=requirement_doc_path,  # 使用原始文档作为目录来源
                        requirement_path=requirement_doc_path,  # 同时作为内容来源
                        debug_mode=False  # 关闭debug，减少日志输出
                    )
                    
                    standardization_result = {
                        "success": True,
                        "standardized_path": standardized_path
                    }
                    
                    log_info(f"标准化文档创建成功: {standardized_path}", "upload_api")
                else:
                    log_warning("未找到目录确认文件(catalog_confirmed.txt)，跳过文档标准化", "upload_api")
            else:
                log_warning("未找到需求规格说明文档，跳过文档标准化", "upload_api")
                
        except Exception as std_error:
            log_error(f"文档标准化异常: {str(std_error)}", "upload_api")
        
        return {
            "status": "success",
            "message": "目录确认成功",
            "session_id": session_id,
            "catalog_file_path": str(catalog_file_path),
            "catalog_items": parse_result['catalog_items'],
            "validation": parse_result['validation'],
            "total_items": len(parse_result['catalog_items']),
            "position_cache": position_cache_result,  # 位置缓存状态
            "standardization": standardization_result  # 新增标准化状态
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"目录确认失败: {str(e)}", "upload_api")
        raise HTTPException(status_code=500, detail=f"目录确认失败: {str(e)}")


@router.get("/extract-catalog/{session_id}")
async def re_extract_catalog(session_id: str, force: bool = False):
    """
    获取/重新提取指定会话的目录信息
    - 轮询场景：默认(force=false)优先读取缓存 catalog_extraction.json；不存在则返回processing
    - 手动“重新提取”：传 force=true 触发重新提取并更新缓存
    """
    try:
        from datetime import datetime
        # 轮询优先：直接读缓存
        session_dir = UPLOAD_BASE_DIR / session_id
        if not session_dir.exists():
            raise HTTPException(status_code=404, detail="会话不存在")

        cache_path = session_dir / "catalog_extraction.json"
        if not force:
            if cache_path.exists():
                with open(cache_path, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                return {
                    "status": "success" if (cached or {}).get("status") != "error" else "error",
                    "message": "获取测试需求成功" if (cached or {}).get("status") != "error" else (cached or {}).get("message", "目录提取失败"),
                    "session_id": session_id,
                    "catalog_extraction": cached
                }
            return {
                "status": "processing",
                "message": "测试需求提取中",
                "session_id": session_id,
                "catalog_extraction": {
                    "status": "processing",
                    "message": "测试需求提取中",
                    "catalog_items": [],
                    "filtered_items": [],
                    "filtered_count": 0
                }
            }

        # ========== force=true：执行重新提取（保留原逻辑） ==========
        from ..utils.spire_doc import extract_testing_requirements_with_spire
        
        log_info(f"重新提取测试需求，会话ID: {session_id}", "upload_api")
        
        # 查找需求文档（优先使用标准化文档）
        standardized_files = list(session_dir.glob("standardized_requirement_*"))
        requirement_files = list(session_dir.glob("requirement_*"))
        
        if standardized_files:
            # 优先使用标准化文档
            extraction_file_path = standardized_files[0]
            extraction_source_type = "标准化文档"
            log_info(f"使用标准化文档进行重新提取: {extraction_file_path}", "upload_api")
        elif requirement_files:
            # 回退到原始文档
            extraction_file_path = requirement_files[0]
            extraction_source_type = "原始文档"
            log_info(f"使用原始文档进行重新提取: {extraction_file_path}", "upload_api")
        else:
            raise HTTPException(status_code=404, detail="未找到需求文档")
        
        # 重新提取测试需求（3.2.x章节过滤）
        # 根据文档类型选择合适的提取算法
        if extraction_source_type == "标准化文档":
            # 使用标准化文档专用算法
            from ..utils.spire_doc.standardized_catalog_extractor import extract_3_2_requirements_from_standardized_docx
            catalog_extraction_result = extract_3_2_requirements_from_standardized_docx(str(extraction_file_path))
            extraction_algorithm = "标准化文档专用算法"
        else:
            # 使用原始文档算法
            catalog_extraction_result = extract_testing_requirements_with_spire(str(extraction_file_path))
            extraction_algorithm = "原始文档算法"
        
        log_info(f"重新提取使用的文档类型: {extraction_source_type}", "upload_api")
        log_info(f"重新提取使用的算法: {extraction_algorithm}", "upload_api")
        
        log_info(f"重新提取测试需求完成: {catalog_extraction_result.get('message', 'Unknown')}", "upload_api")

        # 写入缓存文件（供轮询/前端快速读取）
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(catalog_extraction_result, f, ensure_ascii=False, indent=2)
            # 同步更新状态文件中的catalog_items
            try:
                from ..service.state_manager import GenerationStateManager
                sm = GenerationStateManager(session_dir)
                state = sm.load_state() or {}
                state["catalog_items"] = catalog_extraction_result.get("filtered_items", []) or []
                state["last_updated"] = datetime.now().isoformat()
                sm.save_state(state)
            except Exception:
                pass
        except Exception:
            pass
        
        return {
            "status": "success",
            "message": "测试需求重新提取成功",
            "session_id": session_id,
            "extraction_info": {
                "source_type": extraction_source_type,
                "source_path": str(extraction_file_path),
                "extraction_algorithm": extraction_algorithm
            },
            "catalog_extraction": catalog_extraction_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"重新提取目录失败: {str(e)}", "upload_api")
        raise HTTPException(status_code=500, detail=f"重新提取目录失败: {str(e)}")


def get_upload_base_dir():
    """获取上传基础目录"""
    return UPLOAD_BASE_DIR
