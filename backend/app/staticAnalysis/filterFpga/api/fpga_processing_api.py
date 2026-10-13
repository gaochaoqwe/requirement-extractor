"""
FPGA静态分析处理API端点
"""
import uuid
import asyncio
import shutil
import zipfile
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException, Query, Request
from datetime import datetime

from app.staticAnalysis.filterFpga.services.fpga_enhanced_service import FpgaEnhancedService
from app.staticAnalysis.filterFpga.services.fpga_output_generator import FpgaOutputGenerator
from app.staticAnalysis.filterFpga.utils.logger import setup_module_logger
from app.staticAnalysis.filter.config.config import UPLOAD_DIR
from app.staticAnalysis.filterFpga.config.config import MAX_FPGA_ENHANCED_CONCURRENT_SESSIONS

router = APIRouter(tags=["fpga-processing"])
logger = setup_module_logger(__name__, "fpga_api.log")

# 全局服务实例缓存
_fpga_services: Dict[str, FpgaEnhancedService] = {}


def get_fpga_service(session_id: str, task_id: int = None) -> FpgaEnhancedService:
    """获取或创建FPGA服务实例"""
    if session_id not in _fpga_services:
        _fpga_services[session_id] = FpgaEnhancedService(session_id, task_id)
    return _fpga_services[session_id]


async def save_uploaded_file(file: UploadFile, session_id: str, file_type: str) -> str:
    """保存上传的文件"""
    upload_dir = UPLOAD_DIR / "staticAnalysis" / "fpga" / file_type
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{session_id}_{timestamp}_{file.filename}"
    file_path = upload_dir / safe_filename
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    return str(file_path)


async def save_and_extract_codebase(file: UploadFile, session_id: str) -> str:
    """保存并解压代码库文件，返回解压后的文件夹路径"""
    # 1. 保存ZIP到codebase目录
    codebase_dir = UPLOAD_DIR / "staticAnalysis" / "fpga" / "codebase"
    codebase_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{session_id}_{timestamp}_{file.filename}"
    zip_path = codebase_dir / safe_filename
    
    with open(zip_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    logger.info(f"代码库ZIP已保存: {zip_path}")
    
    # 2. 解压到folders目录
    folders_dir = UPLOAD_DIR / "staticAnalysis" / "fpga" / "folders"
    folders_dir.mkdir(parents=True, exist_ok=True)
    
    # 解压目录名：去掉.zip后缀
    extract_folder_name = safe_filename.rsplit('.', 1)[0]
    extract_path = folders_dir / extract_folder_name
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        logger.info(f"代码库已解压到: {extract_path}")
        return str(extract_path)
    except Exception as e:
        logger.error(f"解压代码库失败: {str(e)}", exc_info=True)
        # 解压失败时返回ZIP路径（回退方案）
        return str(zip_path)


@router.post("/start-processing")
async def start_fpga_processing(
    request: Request,
    background_tasks: BackgroundTasks,
    excel_file: UploadFile = File(...),
    codebase_file: UploadFile = File(...),
    selected_rules: str = Form(...)
) -> Dict[str, Any]:
    """
    开始FPGA静态分析处理
    
    Args:
        excel_file: FPGA静态分析结果Excel文件
        codebase_file: 代码库zip文件
        selected_rules: 选中的规则列表，JSON格式字符串
    """
    session_id = str(uuid.uuid4())
    
    try:
        logger.info(f"开始FPGA静态分析 - session_id: {session_id}")
        logger.info(f"Excel文件: {excel_file.filename}, 代码库: {codebase_file.filename}")

        # 从session获取当前登录用户信息
        try:
            session_data = dict(request.session)
        except Exception:
            session_data = {}
        logger.info(f"[FPGA][上传API] request.session内容: {session_data}")

        operator_name = request.session.get('display_name') or request.session.get('username') or '未知用户'
        logger.info(f"[FPGA][上传API] 当前登录用户: {operator_name}")
        
        # 解析选中的规则
        import json
        try:
            rules_list = json.loads(selected_rules)
        except:
            return {
                "success": False,
                "error": "规则列表格式错误"
            }
        
        logger.info(f"选中规则数量: {len(rules_list)}")
        
        # 保存上传的文件
        excel_path = await save_uploaded_file(excel_file, session_id, "excel")
        # 代码库需要解压到folders目录，供Agent访问
        codebase_path = await save_and_extract_codebase(codebase_file, session_id)
        
        logger.info(f"文件保存完成 - Excel: {excel_path}, 代码库: {codebase_path}")
        
        # 创建服务实例
        service = get_fpga_service(session_id)
        # 记录操作人员（写入日志 + 保存到服务对象，在创建会话记录时写入数据库）
        try:
            service.operator_name = operator_name
            service.logger.info(f"操作人员: {operator_name}")
        except Exception:
            pass
        service.original_filename = excel_file.filename
        
        # 并发保护：达到阈值则跳过AI审查，仅提供未经AI过滤的问题单
        # 修复：只统计正在AI审查的任务（ai_analyzing），不包括刚上传的（processing）
        active_processing = sum(1 for s in _fpga_services.values() if getattr(s, 'current_status', 'pending') == 'ai_analyzing')
        logger.info(f"[并发检查] 当前AI审查中的任务数: {active_processing}/{MAX_FPGA_ENHANCED_CONCURRENT_SESSIONS}")
        if active_processing >= MAX_FPGA_ENHANCED_CONCURRENT_SESSIONS:
            try:
                result = await service.process_files(
                    excel_path=excel_path,
                    codebase_zip_path=codebase_path,
                    selected_rules=rules_list,
                    skip_ai=True
                )
                # 标记确定规则已就绪，前端可直接下载“未经AI过滤”
                result = result or {}
                result.update({"ai_disabled": True})
                logger.info(f"FPGA并发达上限，跳过AI审查，session_id={session_id}")
                return {
                    "success": True,
                    "session_id": session_id,
                    "message": "文件上传成功。当前用户数量过多，已关闭AI审查，仅支持下载未经AI过滤的问题单。",
                    "status": "processing",
                    "ai_disabled": True
                }
            except Exception as e:
                logger.error(f"FPGA无AI模式处理失败 - session_id: {session_id}, 错误: {str(e)}", exc_info=True)
                return {"success": False, "error": str(e)}

        # [FIX] 设置初始状态，让前端能立即获取到基本信息
        service.current_status = "processing"
        
        # 获取task_id（需要等待数据库记录创建）
        # 先启动后台任务，task_id会在process_files中创建
        def process_task_sync():
            """同步包装函数，用于FastAPI的BackgroundTasks"""
            import asyncio
            try:
                # 在新的事件循环中运行异步函数
                result = asyncio.run(service.process_files(
                    excel_path=excel_path,
                    codebase_zip_path=codebase_path,
                    selected_rules=rules_list
                ))
                logger.info(f"FPGA处理完成 - session_id: {session_id}, task_id: {service.task_id}, 结果: {result}")
            except Exception as e:
                logger.error(f"FPGA处理失败 - session_id: {session_id}, 错误: {str(e)}", exc_info=True)
                service.current_status = "failed"
        
        # 启动后台任务
        background_tasks.add_task(process_task_sync)
        
        # 返回session_id和task_id（task_id初期为None，前端可以通过session_id查询）
        return {
            "success": True,
            "session_id": session_id,
            "task_id": None,  # 初期为None，需要等待后台任务创建数据库记录
            "message": "FPGA静态分析已启动，正在后台处理",
            "status": "processing"
        }
        
    except Exception as e:
        error_msg = f"启动FPGA处理失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "error": error_msg
        }


@router.get("/progress/{session_id}")
async def get_fpga_progress(session_id: str) -> Dict[str, Any]:
    """获取FPGA处理进度（支持UUID或数字ID）"""
    try:
        # 尝试直接用UUID查找
        service = _fpga_services.get(session_id)
        
        # 如果找不到，尝试将session_id当作数字ID查询数据库获取UUID
        if service is None:
            try:
                numeric_id = int(session_id)
                # 从数据库查询UUID
                from app.staticAnalysis.filterFpga.database.postgresql_database import get_db_session
                from app.staticAnalysis.filterFpga.database.postgresql_models import StaticAnalysisSession
                
                db = get_db_session()
                try:
                    session_obj = db.query(StaticAnalysisSession).filter(
                        StaticAnalysisSession.id == numeric_id
                    ).first()
                    
                    if session_obj:
                        resolved_uuid = session_obj.session_id
                        logger.info(f"[FPGA进度API] 数字ID {numeric_id} 解析为UUID: {resolved_uuid}")
                        service = _fpga_services.get(resolved_uuid)
                finally:
                    db.close()
            except (TypeError, ValueError):
                pass
        
        if service is None:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        progress = service.get_progress()
        
        # [DEBUG] 添加详细日志
        logger.info(f"[FPGA进度API] session_id={session_id}, task_id={service.task_id}")
        logger.info(f"[FPGA进度API] total_issues={progress['total_issues']}, accurate_issues={progress['accurate_issues']}")
        logger.info(f"[FPGA进度API] uncertain_issues={progress['uncertain_issues']}, ai_processing_total={progress['ai_processing_total']}")
        logger.info(f"[FPGA进度API] processed_issues={progress['processed_issues']}, status={progress['status']}")
        
        return {
            "success": True,
            "task_id": service.task_id,  # 返回task_id供前端使用
            "session_id": session_id,  # 保留session_id以兼容
            "progress": progress
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取进度失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/download-accurate/{session_id}")
async def download_fpga_accurate_issues(session_id: str):
    """下载FPGA确定规则问题单"""
    try:
        # 验证会话存在（从数据库）
        from app.staticAnalysis.filterFpga.database.postgresql_database import get_db_session
        from app.staticAnalysis.filterFpga.database.postgresql_models import StaticAnalysisSession
        
        db = get_db_session()
        try:
            session_obj = db.query(StaticAnalysisSession).filter(
                StaticAnalysisSession.session_id == session_id
            ).first()
            
            if not session_obj:
                try:
                    numeric_id = int(session_id)
                    session_obj = db.query(StaticAnalysisSession).filter(
                        StaticAnalysisSession.id == numeric_id
                    ).first()
                except (TypeError, ValueError):
                    pass
            
            if not session_obj:
                raise HTTPException(status_code=404, detail="会话不存在")
            
            real_session_id = session_obj.session_id
        finally:
            db.close()
        
        # 生成问题单
        output_dir = Path(UPLOAD_DIR) / "staticAnalysis" / "fpga" / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_filename = "FPGA_准确问题单（AI过滤后）.xlsx"
        output_path = output_dir / output_filename
        logger.info(f"[DOWNLOAD-ACCURATE] session={real_session_id}, 输出路径={output_path}")
        generator = FpgaOutputGenerator(real_session_id)
        result = generator.generate_output_file(
            str(output_path),
            rule_type="fpga",
            accuracy="accurate"
        )
        logger.info(f"[DOWNLOAD-ACCURATE] 生成结果: {result}")
        # 校验文件是否生成
        try:
            if Path(output_path).exists():
                size = Path(output_path).stat().st_size
                logger.info(f"[DOWNLOAD-ACCURATE] 文件已生成: {output_path} (size={size} bytes)")
            else:
                logger.error(f"[DOWNLOAD-ACCURATE] 文件未找到: {output_path}")
        except Exception as fe:
            logger.warning(f"[DOWNLOAD-ACCURATE] 检查输出文件失败: {fe}")

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        from fastapi.responses import FileResponse
        return FileResponse(
            path=str(output_path),
            filename=output_filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载确定规则问题单失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download-split/{session_id}")
async def download_fpga_split(session_id: str, highlight_ai: bool = Query(False, description="是否在不确定(勾选)sheet高亮AI确认问题")):
    """下载四分分类（确定/不确定 × 勾选/未勾选）问题单。
    当 highlight_ai=True 时，仅在"不确定规则（勾选）"sheet 中高亮 ai_is_real_issue=True 的条目。
    """
    try:
        # 如果服务实例存在，优先使用
        if session_id in _fpga_services:
            service = _fpga_services[session_id]
        else:
            # 服务实例不存在（已完成并清理），从数据库重新创建
            logger.info(f"[下载API] 服务实例不存在，尝试从数据库查询: {session_id}")
            from app.staticAnalysis.filterFpga.database.postgresql_database import get_db_session
            from app.staticAnalysis.filterFpga.database.postgresql_models import StaticAnalysisSession
            
            db = get_db_session()
            try:
                # 先尝试作为UUID查询
                session_obj = db.query(StaticAnalysisSession).filter(
                    StaticAnalysisSession.session_id == session_id
                ).first()
                
                if not session_obj:
                    # 尝试作为数字ID查询
                    try:
                        numeric_id = int(session_id)
                        session_obj = db.query(StaticAnalysisSession).filter(
                            StaticAnalysisSession.id == numeric_id
                        ).first()
                    except (TypeError, ValueError):
                        pass
                
                if not session_obj:
                    raise HTTPException(status_code=404, detail="会话不存在")
                
                # 使用真实的UUID session_id重新创建服务实例
                real_session_id = session_obj.session_id
                task_id = session_obj.id
                logger.info(f"[下载API] 从数据库找到会话: session_id={real_session_id}, task_id={task_id}")
                
                # 重新创建服务实例（仅用于生成下载文件）
                service = get_fpga_service(real_session_id, task_id)
                session_id = real_session_id  # 使用真实的session_id
            finally:
                db.close()
        
        # [FIX] 检查是否有预生成的缓存文件（仅限未经AI过滤的四分分类文件）
        if not highlight_ai and hasattr(service, 'cached_filename') and service.cached_filename:
            # 使用预生成的缓存文件
            cached_filename = service.cached_filename
            logger.info(f"[下载API] 使用FPGA预生成缓存文件: {cached_filename}")
            
            # 构建缓存文件路径
            output_dir = Path(UPLOAD_DIR) / "staticAnalysis" / "fpga" / "output"
            cached_file_path = output_dir / cached_filename
            
            if cached_file_path.exists():
                from fastapi.responses import FileResponse
                return FileResponse(
                    path=str(cached_file_path),
                    filename=cached_filename,
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                logger.warning(f"[下载API] 缓存文件不存在，重新生成: {cached_filename}")
        
        # 没有缓存或缓存文件不存在，重新生成
        result = service.generate_split_output_file(highlight_ai=highlight_ai)
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "生成文件失败"))

        from fastapi.responses import FileResponse
        return FileResponse(
            path=str(result["output_path"]),
            filename=result["filename"],
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载四分分类问题单失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download-full/{session_id}")
async def download_fpga_full_issues(session_id: str):
    """下载FPGA完整问题单（包含确定和不确定规则）"""
    try:
        # 验证会话存在（从数据库）
        from app.staticAnalysis.filterFpga.database.postgresql_database import get_db_session
        from app.staticAnalysis.filterFpga.database.postgresql_models import StaticAnalysisSession
        
        db = get_db_session()
        try:
            session_obj = db.query(StaticAnalysisSession).filter(
                StaticAnalysisSession.session_id == session_id
            ).first()
            
            if not session_obj:
                try:
                    numeric_id = int(session_id)
                    session_obj = db.query(StaticAnalysisSession).filter(
                        StaticAnalysisSession.id == numeric_id
                    ).first()
                except (TypeError, ValueError):
                    pass
            
            if not session_obj:
                raise HTTPException(status_code=404, detail="会话不存在")
            
            real_session_id = session_obj.session_id
        finally:
            db.close()
        
        # 生成问题单
        output_dir = Path(UPLOAD_DIR) / "staticAnalysis" / "fpga" / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_filename = "FPGA_全部问题单（未经AI过滤）.xlsx"
        output_path = output_dir / output_filename
        logger.info(f"[DOWNLOAD-FULL] session={real_session_id}, 输出路径={output_path}")
        generator = FpgaOutputGenerator(real_session_id)
        result = generator.generate_output_file(
            str(output_path),
            rule_type="fpga",
            accuracy="all"
        )
        logger.info(f"[DOWNLOAD-FULL] 生成结果: {result}")
        try:
            if Path(output_path).exists():
                size = Path(output_path).stat().st_size
                logger.info(f"[DOWNLOAD-FULL] 文件已生成: {output_path} (size={size} bytes)")
            else:
                logger.error(f"[DOWNLOAD-FULL] 文件未找到: {output_path}")
        except Exception as fe:
            logger.warning(f"[DOWNLOAD-FULL] 检查输出文件失败: {fe}")

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        from fastapi.responses import FileResponse
        return FileResponse(
            path=str(output_path),
            filename=output_filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载完整问题单失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def cleanup_fpga_session(session_id: str):
    """清理FPGA会话"""
    try:
        if session_id in _fpga_services:
            del _fpga_services[session_id]
        
        # 清理临时文件
        upload_dir = Path(UPLOAD_DIR) / "staticAnalysis" / "fpga"
        for subdir in ["excel", "codebase", "folders", "output"]:
            dir_path = upload_dir / subdir
            if dir_path.exists():
                for file in dir_path.glob(f"{session_id}_*"):
                    try:
                        if file.is_file():
                            file.unlink()
                        elif file.is_dir():
                            shutil.rmtree(file)
                    except Exception as e:
                        logger.warning(f"清理文件失败: {file}, 错误: {str(e)}")
        
        return {
            "success": True,
            "message": "会话已清理"
        }
        
    except Exception as e:
        logger.error(f"清理会话失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
