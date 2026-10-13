from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, Response, Form, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
import logging
from datetime import datetime
import asyncio
import uuid
import io
import os

# 创建占位符服务类
class PlaceholderService:
    def __getattr__(self, name):
        def placeholder(*args, **kwargs):
            raise RuntimeError(f"服务模块未正确加载，方法 {name} 不可用")
        return placeholder

# 初始化服务变量
RequirementService = None
IntelligentImportService = None
crud = None
get_db = None
schemas = None

try:
    from ..db import crud, get_db
    from ..schemas import schemas
    from ..services import RequirementService, IntelligentImportService, IntelligentExportService
    
    logger = logging.getLogger(__name__)
    
    router = APIRouter(prefix="/requirements")
    
    @router.post("/import/preview-intelligent", response_model=List[schemas.IntelligentImportSuggestion])
    async def preview_intelligent_import(
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
    ):
        """上传Excel进行预览：返回逐行的AI/规则建议(仅后两列追加 or 新建)。"""
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只支持Excel文件格式(.xlsx, .xls)"
            )
        
        try:
            content = await file.read()
            suggestions = IntelligentImportService.preview_from_excel(db=db, file_content=content)
            return suggestions
        except Exception as e:
            logger.error(f"智能导入预览失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"预览失败: {str(e)}"
            )
    
    
    @router.post("/import/commit-intelligent")
    def commit_intelligent_import(
        decisions: List[schemas.IntelligentImportDecision],
        db: Session = Depends(get_db)
    ):
        """接收前端确认后的决策，执行入库/列追加。"""
        try:
            result = IntelligentImportService.commit(db=db, decisions=decisions)
            return result
        except Exception as e:
            logger.error(f"智能导入提交失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"提交失败: {str(e)}")
    
    @router.post("/intelligent-export")
    async def intelligent_export(
        file: UploadFile = File(...),
        selected_type: str = Form(..., description="选择的类型：转塔、对抗告警、光雷、吊舱"),
        db: Session = Depends(get_db)
    ):
        """
        智能导出功能
        
        Args:
            file: 上传的Excel文件
            selected_type: 用户选择的类型
            db: 数据库会话
            
        Returns:
            处理后的Excel文件
        """
        # 验证文件格式
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只支持Excel文件格式(.xlsx, .xls)"
            )
        
        # 验证选择的类型
        valid_types = ["转塔", "对抗告警", "光雷", "吊舱"]
        if selected_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported type, valid types: turret, countermeasure, optoradar, pod"
            )
        
        try:
            # 读取文件内容
            file_content = await file.read()
            
            # 处理智能导出
            processed_content = IntelligentExportService.process_intelligent_export(
                db=db,
                file_content=file_content,
                selected_type=selected_type
            )
            
            # 生成文件名（完全使用英文避免编码问题）
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            # 将中文类型转换为英文
            type_mapping = {
                "转塔": "turret",
                "对抗告警": "countermeasure", 
                "光雷": "optoradar",
                "吊舱": "pod"
            }
            english_type = type_mapping.get(selected_type, "unknown")
            output_filename = f"intelligent_export_{english_type}_{timestamp}.xlsx"
            
            # 返回处理后的文件
            import io
            return StreamingResponse(
                io.BytesIO(processed_content),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename={output_filename}"
                }
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Intelligent export failed: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Intelligent export failed: {error_msg}"
            )

    @router.post("/intelligent-export-async")
    async def intelligent_export_async(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        selected_type: str = Form(..., description="选择的类型：转塔、对抗告警、光雷、吊舱"),
        selected_software_type: str = Form(..., description="选择的软件类型"),
        db: Session = Depends(get_db)
    ):
        """异步智能导出"""
        try:
            # 验证文件格式
            if not file.filename.endswith(('.xlsx', '.xls')):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="只支持Excel文件格式(.xlsx, .xls)"
                )
            
            # 验证选择的类型
            valid_types = ["转塔", "对抗告警", "光雷", "吊舱"]
            if selected_type not in valid_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported type, valid types: {valid_types}"
                )
            
            # 读取文件内容
            file_content = await file.read()

            from ..db.models import ExportTask

            task = ExportTask(
                status="processing",
                progress=0,
                message="开始处理...",
            )
            db.add(task)
            db.commit()
            db.refresh(task)
            task_id = task.id

            # 启动后台任务
            background_tasks.add_task(
                process_export_background,
                task_id,
                file_content,
                selected_type,
                selected_software_type
            )

            return {"task_id": task_id, "message": "Export started"}
            
        except Exception as e:
            logger.error(f"Failed to start intelligent export: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/export-progress/{task_id}")
    async def get_export_progress(task_id: int, db: Session = Depends(get_db)):
        """获取导出进度"""
        from ..db.models import ExportTask

        task = db.query(ExportTask).filter(ExportTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        return {
            "status": task.status,
            "progress": task.progress,
            "message": task.message,
            "result": None,
            "error": task.error,
            "file_path": task.file_path,
            "filename": task.filename,
        }

    @router.get("/download-export/{task_id}")
    async def download_export_result(task_id: int, db: Session = Depends(get_db)):
        """下载导出结果"""
        from ..db.models import ExportTask

        task = db.query(ExportTask).filter(ExportTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if task.status != "completed":
            raise HTTPException(status_code=400, detail="Export not completed yet")

        if not task.file_path:
            raise HTTPException(status_code=404, detail="Export result file not found")

        file_path = task.file_path
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Export result file not found on disk")
        
        # 从文件路径读取并返回文件流
        def file_generator():
            with open(file_path, "rb") as file:
                while True:
                    chunk = file.read(8192)  # 8KB chunks
                    if not chunk:
                        break
                    yield chunk
        
        # 获取文件名
        filename = os.path.basename(file_path)
        
        return StreamingResponse(
            file_generator(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    def process_export_background(task_id: int, file_content: bytes, selected_type: str, selected_software_type: str):
        """后台处理导出任务"""
        try:
            # 更新进度回调
            def update_progress(progress: int, message: str):
                from ..db.database import SessionLocal
                from ..db.models import ExportTask

                db_local = SessionLocal()
                try:
                    task = db_local.query(ExportTask).filter(ExportTask.id == task_id).first()
                    if task:
                        task.progress = progress
                        task.message = message
                        db_local.commit()
                        logger.info(f"Progress updated for task {task_id}: {progress}% - {message}")
                finally:
                    db_local.close()
            
            # 初始进度更新
            update_progress(1, "后台任务开始处理...")
            
            from ..db.database import SessionLocal
            from ..db.models import ExportTask

            db = SessionLocal()
            
            try:
                update_progress(3, "数据库连接已建立...")
                
                # 调用智能导出服务（带进度回调）
                result = IntelligentExportService.process_intelligent_export_with_progress(
                    db,
                    file_content,
                    selected_type,
                    selected_software_type,
                    update_progress
                )
                
                update_progress(95, "正在保存结果文件...")
                
                # 生成文件名和路径
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"intelligent_export_{task_id}_{timestamp}.xlsx"
                file_path = os.path.join("uploads", "databaseManage", filename)
                
                # 确保目录存在
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                # 保存文件到磁盘
                with open(file_path, "wb") as f:
                    f.write(result)
                
                update_progress(100, "导出完成！")
                
                task = db.query(ExportTask).filter(ExportTask.id == task_id).first()
                if task:
                    task.status = "completed"
                    task.progress = 100
                    task.message = "导出完成，可以下载"
                    task.file_path = file_path
                    task.filename = filename
                    db.commit()
                
                logger.info(f"Export task {task_id} completed successfully")
                
            finally:
                # 确保数据库会话被关闭
                db.close()
            
        except Exception as e:
            logger.error(f"Export task {task_id} failed: {str(e)}", exc_info=True)
            from ..db.database import SessionLocal
            from ..db.models import ExportTask

            db_local = SessionLocal()
            try:
                task = db_local.query(ExportTask).filter(ExportTask.id == task_id).first()
                if task:
                    task.status = "error"
                    task.progress = 0
                    task.message = f"导出失败: {str(e)}"
                    task.error = str(e)
                    db_local.commit()
            finally:
                db_local.close()
    
    @router.get("/export/excel")
    def export_requirements_excel(
        software_category: Optional[str] = Query(None, description="软件类别筛选"),
        db: Session = Depends(get_db)
    ):
        """导出需求记录为Excel文件"""
        try:
            requirements = crud.get_requirements(
                db=db,
                skip=0,
                limit=10000,  # 导出时获取所有数据
                software_category=software_category
            )
            
            if not requirements:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="没有找到需求记录"
                )
            
            excel_content = RequirementService.export_to_excel(
                db=db,
                software_category=software_category
            )
            
            return Response(
                content=excel_content,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=optoelectronic_requirements.xlsx"}
            )
            
        except Exception as e:
            logger.error(f"导出Excel文件失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"导出Excel文件失败: {str(e)}"
            ) 
    
    
    # ===================== 标准 CRUD =====================
    @router.get("/list", response_model=List[schemas.OptoelectronicRequirement])
    def list_requirements(
        page: int = Query(1, ge=1),
        page_size: int = Query(50, ge=1, le=200),
        software_category: Optional[str] = Query(None),
        db: Session = Depends(get_db)
    ):
        items, total = RequirementService.get_requirements_with_pagination(
            db=db, page=page, page_size=page_size, software_category=software_category
        )
        # 附带 total 通过 header 传递，前端可读取 X-Total-Count
        # FastAPI 直接返回列表，若需要更复杂结构可切换为 dict
        return items
    
    
    @router.get("/list/sorted", response_model=List[schemas.OptoelectronicRequirement])
    def list_requirements_sorted(
        db: Session = Depends(get_db)
    ):
        """获取按软件类别自动排序的需求记录列表"""
        try:
            # 直接查询数据库，完全不依赖其他模块
            from ..db.models import OptoelectronicRequirement
            return db.query(OptoelectronicRequirement).order_by(
                OptoelectronicRequirement.category_order,
                OptoelectronicRequirement.item_order
            ).all()
        except Exception as e:
            logger.error(f"获取排序后的需求记录失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取排序后的需求记录失败: {str(e)}"
            )
    
    
    @router.post("/", response_model=schemas.OptoelectronicRequirement)
    def create_requirement(
        data: schemas.OptoelectronicRequirementCreate,
        db: Session = Depends(get_db)
    ):
        return RequirementService.create_requirement(db=db, requirement_data=data)
    
    
    @router.put("/{requirement_id}", response_model=schemas.OptoelectronicRequirement)
    def update_requirement(
        requirement_id: int,
        data: schemas.OptoelectronicRequirementUpdate,
        db: Session = Depends(get_db)
    ):
        updated = RequirementService.update_requirement(db=db, requirement_id=requirement_id, update_data=data)
        if not updated:
            raise HTTPException(status_code=404, detail="记录不存在")
        return updated
    
    
    @router.delete("/{requirement_id}")
    def delete_requirement(requirement_id: int, db: Session = Depends(get_db)):
        ok = RequirementService.delete_requirement(db=db, requirement_id=requirement_id)
        if not ok:
            raise HTTPException(status_code=404, detail="记录不存在或删除失败")
        return {"success": True}
    
    
    @router.post("/batch-delete")
    def batch_delete(payload: schemas.RequirementBatchDelete, db: Session = Depends(get_db)):
        count = 0
        for rid in payload.ids:
            if RequirementService.delete_requirement(db=db, requirement_id=rid):
                count += 1
        return {"deleted": count}
    
    
    # ===================== Excel 导入/校验 =====================
    @router.post("/import", response_model=List[schemas.OptoelectronicRequirement])
    async def import_excel(
        file: UploadFile = File(...),
        clear_existing: bool = Query(False),
        db: Session = Depends(get_db)
    ):
        """智能导入Excel文件（原有功能）"""
        if not file.filename.endswith((".xlsx", ".xls")):
            raise HTTPException(status_code=400, detail="只支持Excel文件(.xlsx, .xls)")
        try:
            content = await file.read()
            imported, _msg = RequirementService.import_from_excel(db=db, file_content=content, clear_existing=clear_existing)
            return imported
        except Exception as e:
            logger.error(f"导入失败: {e}")
            raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")
    
    
    @router.post("/import/normal")
    async def normal_import_excel(
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
    ):
        """普通导入Excel文件，支持模糊匹配和追加功能"""
        if not file.filename.endswith((".xlsx", ".xls")):
            raise HTTPException(status_code=400, detail="只支持Excel文件(.xlsx, .xls)")
        try:
            content = await file.read()
            stats, message = RequirementService.normal_import_from_excel(db=db, file_content=content)
            return {
                "success": True,
                "message": message,
                "stats": stats
            }
        except Exception as e:
            logger.error(f"普通导入失败: {e}")
            raise HTTPException(status_code=500, detail=f"普通导入失败: {str(e)}")

    
    # ===================== 新增：多Sheet（7列）导入 =====================
    @router.post("/import/multisheet-7cols")
    async def import_multisheet_7cols(
        file: UploadFile = File(...),
        mode: str = Query("full", description="导入模式：full 清空后导入；incremental 仅新增"),
        db: Session = Depends(get_db)
    ):
        """多Sheet（7列）导入：按Sheet名称映射到各自表，支持full/incremental两种模式。"""
        if not file.filename.endswith((".xlsx", ".xls")):
            raise HTTPException(status_code=400, detail="只支持Excel文件(.xlsx, .xls)")
        try:
            content = await file.read()
            result = RequirementService.import_multisheet_7cols(db=db, file_content=content, mode=mode)
            return {
                "success": True,
                "mode": result.get("mode"),
                "sheets": result.get("sheets", {})
            }
        except Exception as e:
            logger.error(f"多Sheet(7列)导入失败: {e}")
            raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")

    
    @router.post("/import/validate")
    async def validate_import(file: UploadFile = File(...)):
        if not file.filename.endswith((".xlsx", ".xls")):
            raise HTTPException(status_code=400, detail="只支持Excel文件(.xlsx, .xls)")
        try:
            content = await file.read()
            result = RequirementService.validate_excel_file(content)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"校验失败: {str(e)}")
    
    # ===================== 七列表：列表 & 导出 =====================
    @router.get("/seven/list", response_model=List[schemas.SevenColRequirementOut])
    def list_seven_cols(
        table: str = Query(..., description="表/Sheet名称：转塔/对抗告警/光雷/吊舱"),
        page: int = Query(1, ge=1),
        page_size: int = Query(50, ge=1, le=200),
        software_category: Optional[str] = Query(None, description="软件类别筛选"),
        test_item_name: Optional[str] = Query(None, description="测试项名称筛选"),
        db: Session = Depends(get_db),
        response: Response = None,
    ):
        """获取七列表数据 - 优化版本，添加超时和错误处理"""
        import time
        start_time = time.time()
        
        try:
            logger.info(f"开始查询七列表: table={table}, page={page}, page_size={page_size}")
            
            # 🚀 优化1: 添加快速验证，避免无效查询
            if table not in ["转塔", "对抗告警", "光雷", "吊舱"]:
                raise HTTPException(status_code=400, detail=f"不支持的表名: {table}")
            
            # 🚀 优化2: 限制页面大小，避免大量数据查询
            if page_size > 100:
                page_size = 100
                logger.warning(f"页面大小超限，调整为100")
            
            # 🚀 优化3: 添加超时检查
            items, total = RequirementService.get_sevencols_with_pagination(
                db=db,
                table=table,
                page=page,
                page_size=page_size,
                software_category=software_category,
                test_item_name=test_item_name,
            )
            
            elapsed = time.time() - start_time
            logger.info(f"查询完成: 耗时{elapsed:.2f}s, 返回{len(items)}条记录, 总计{total}条")
            
            if response is not None:
                response.headers["X-Total-Count"] = str(total)
            return items
            
        except ValueError as ve:
            logger.warning(f"参数错误: {ve}")
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"获取七列表失败 (耗时{elapsed:.2f}s): {e}", exc_info=True)
            # 🚀 优化4: 返回更友好的错误信息
            if "timeout" in str(e).lower():
                raise HTTPException(status_code=504, detail="查询超时，请稍后重试")
            else:
                raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

    @router.get("/seven/export")
    def export_seven_cols(
        table: str = Query(..., description="表/Sheet名称：转塔/对抗告警/光雷/吊舱"),
        software_category: Optional[str] = Query(None, description="软件类别筛选"),
        test_item_name: Optional[str] = Query(None, description="测试项名称筛选"),
        db: Session = Depends(get_db),
    ):
        try:
            content = RequirementService.export_sevencols_by_table(
                db=db, table=table, software_category=software_category, test_item_name=test_item_name
            )
            filename = f"{table}_七列需求.xlsx"
            # 对中文文件名进行URL编码
            from urllib.parse import quote
            encoded_filename = quote(filename, safe='')
            return Response(
                content=content,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
                },
            )
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            logger.error(f"导出七列表失败: {e}")
            raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")

    
    # ===================== 开发工具：清空数据库 =====================
    @router.post("/admin/reset-db")
    def clear_database(confirm: str = Query(..., description="输入 YES 确认执行：将清空数据库中的所有数据")):
        if confirm != "YES":
            raise HTTPException(status_code=400, detail="未确认：请将 confirm 设置为 YES")
        try:
            from ..db.init import clear_db
            ok = clear_db()
            if not ok:
                raise HTTPException(status_code=500, detail="清空数据库失败")
            return {"success": True, "message": "数据库清空成功"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"清空数据库失败: {e}")
            raise HTTPException(status_code=500, detail=f"清空数据库失败: {str(e)}")
    
    
    # ===================== 健康检查 =====================
    @router.get("/health")
    def health_check(db: Session = Depends(get_db)):
        """数据库管理模块健康检查"""
        try:
            # 简单的数据库连接测试
            result = db.execute("SELECT 1").fetchone()
            
            # 检查各个表是否存在
            tables_status = {}
            for table_name, model in getattr(crud, "MODEL_MAP", {}).items():
                if model:
                    try:
                        count = db.query(model).count()
                        tables_status[table_name] = {"status": "ok", "count": count}
                    except Exception as e:
                        tables_status[table_name] = {"status": "error", "error": str(e)}
                else:
                    tables_status[table_name] = {"status": "model_not_found"}
            
            return {
                "status": "healthy",
                "database": "connected",
                "tables": tables_status,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            raise HTTPException(status_code=503, detail=f"数据库连接失败: {str(e)}")
    
    # ===================== 统计 =====================
    @router.get("/stats")
    def stats(db: Session = Depends(get_db)):
        try:
            return RequirementService.get_statistics(db)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
            
except ImportError as e:
    # 如果导入失败，创建空的router避免启动错误
    logger = logging.getLogger(__name__)
    router = APIRouter(prefix="/requirements")
    
    @router.get("/")
    def placeholder():
        return {"message": "模块导入失败，功能不可用"}
    
    print(f"警告: requirements模块导入失败: {e}")
    
    # 设置占位符服务
    RequirementService = PlaceholderService()
    IntelligentImportService = PlaceholderService()
    
    # 创建备用的get_db函数
    def get_db():
        try:
            from ..db.database import SessionLocal
            db = SessionLocal()
            try:
                yield db
            finally:
                db.close()
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise HTTPException(status_code=500, detail="数据库连接失败")
    
    # 重新定义get_db为全局变量
    globals()['get_db'] = get_db