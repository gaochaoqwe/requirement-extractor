"""
鉴定测评表单辅助工具业务逻辑服务
支持多并发访问和处理
"""
import asyncio
import time
import uuid
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

from ..models.models import AssessmentSession, RequirementItem, GenerationLog
from ..database.database import get_db_session
from .ai_client import AssessmentAIClient
from .excel_processor import ExcelProcessor
from ..config.config import AI_GENERATION_CONFIG, UPLOAD_DIR
from ..utils.logger import get_session_logger, setup_session_logger

class AssessmentFormService:
    def __init__(self, session_id: str = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.logger = setup_session_logger(self.session_id)
        self.ai_client = AssessmentAIClient(self.session_id)
        self.excel_processor = ExcelProcessor(self.session_id)
        self.batch_size = AI_GENERATION_CONFIG["batch_size"]
        self.max_retries = AI_GENERATION_CONFIG["max_retries"]
        
        # 内存进度跟踪变量
        self.total_items = 0
        self.completed_items = 0
        self.error_items = 0
        self.processing_items = 0
        self.current_status = "pending"
        self.original_filename = ""
        self.output_filename = ""

    def process_uploaded_file(self, file_path: str, original_filename: str) -> Dict[str, Any]:
        """
        处理上传的Excel文件
        """
        try:
            self.logger.info(f"开始处理上传文件: {original_filename}")
            
            # 初始化进度跟踪
            self.original_filename = original_filename
            self.current_status = "processing"
            
            # 处理Excel文件
            session_id, result = self.excel_processor.process_uploaded_file(file_path, original_filename)
            
            if result["success"]:
                # 更新进度信息
                self.total_items = result.get("total_rows", 0)
                self.completed_items = 0
                self.error_items = 0
                self.processing_items = 0
                
                self.logger.info(f"文件处理成功 - 会话ID: {self.session_id}")
                return {"success": True, "total_rows": result.get("total_rows", 0)}
            else:
                self.current_status = "error"
                return result
                
        except Exception as e:
            self.current_status = "error"
            error_msg = f"处理上传文件时出错: {str(e)}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}

    async def process_session(self) -> Dict[str, Any]:
        """
        异步处理会话中的所有需求项
        支持并发处理
        
        Returns:
            Dict[str, Any]: 处理结果
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"开始处理会话: {self.session_id}")
            
            # 更新会话状态为处理中
            self._update_session_status("processing")
            
            # 获取待处理的需求项
            pending_items = self._get_pending_items()
            if not pending_items:
                self.logger.warning("没有找到待处理的需求项")
                return {"success": False, "error": "没有找到待处理的需求项"}
            
            self.logger.info(f"找到{len(pending_items)}个待处理的需求项")
            
            # 分批处理
            total_processed = 0
            total_errors = 0
            
            for i in range(0, len(pending_items), self.batch_size):
                batch = pending_items[i:i + self.batch_size]
                self.logger.info(f"处理批次 {i//self.batch_size + 1}: {len(batch)}个项目")
                
                batch_result = await self._process_batch(batch)
                total_processed += batch_result["processed"]
                total_errors += batch_result["errors"]
                
                # 更新进度
                self._update_session_progress(total_processed)
                
                self.logger.info(f"批次处理完成 - 成功: {batch_result['processed']}, 失败: {batch_result['errors']}")
            
            # 更新最终状态
            if total_errors == 0:
                status = "success"
                message = f"所有{total_processed}个项目处理成功"
            else:
                status = "partial_success"
                message = f"处理完成 - 成功: {total_processed}, 失败: {total_errors}"
            
            execution_time = time.time() - start_time
            self.logger.info(f"会话处理完成 - {message}, 耗时: {execution_time:.2f}秒")
            
            # AI处理完成后，自动生成Excel文件
            try:
                self.logger.info("开始自动生成Excel输出文件")
                generate_result = self.generate_output_file()
                
                if generate_result["success"]:
                    self.logger.info(f"Excel文件自动生成成功: {generate_result['filename']}")
                    # 更新会话状态为已完成，并保存生成的文件名
                    self._update_session_with_output_file("completed", generate_result["filename"])
                    message += f"，输出文件已生成: {generate_result['filename']}"
                else:
                    self.logger.error(f"Excel文件自动生成失败: {generate_result.get('error')}")
                    self._update_session_status("completed", f"AI处理完成但文件生成失败: {generate_result.get('error')}")
                    
            except Exception as e:
                self.logger.error(f"自动生成Excel文件时出错: {str(e)}")
                self._update_session_status("completed", f"AI处理完成但文件生成失败: {str(e)}")
            
            self._log_operation("process", status, message, execution_time)
            
            return {
                "success": True,
                "total_processed": total_processed,
                "total_errors": total_errors,
                "execution_time": execution_time,
                "message": message
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"处理会话时出错: {str(e)}"
            self.logger.error(f"{error_msg}, 耗时: {execution_time:.2f}秒")
            
            self._update_session_status("error", error_msg)
            self._log_operation("process", "error", error_msg, execution_time)
            
            return {"success": False, "error": error_msg}

    async def _process_batch(self, batch: List[RequirementItem]) -> Dict[str, int]:
        """
        并发处理一批需求项
        
        Args:
            batch: 需求项列表
            
        Returns:
            Dict[str, int]: 处理结果统计
        """
        # 创建并发任务
        tasks = []
        for item in batch:
            task = asyncio.create_task(self._process_single_item(item))
            tasks.append(task)
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 统计结果
        processed = 0
        errors = 0
        
        for result in results:
            if isinstance(result, Exception):
                errors += 1
                self.logger.error(f"任务执行异常: {str(result)}")
            elif result and result.get("success"):
                processed += 1
            else:
                errors += 1
        
        return {"processed": processed, "errors": errors}

    async def _process_single_item(self, item: RequirementItem) -> Dict[str, Any]:
        """
        处理单个需求项
        
        Args:
            item: 需求项
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"开始处理需求项 ID: {item.id}, 行: {item.row_index}")
            
            # 更新状态为处理中
            self._update_item_status(item.id, "processing")
            self.processing_items += 1
            
            # 准备输入数据
            original_requirement = item.original_requirement_description or ""
            test_item_description = item.test_item_description or ""
            test_method = item.test_method or ""
            
            # 验证输入数据
            if not test_item_description and not test_method:
                error_msg = "测试项描述和测试方法都为空"
                self.logger.warning(f"需求项 {item.id} 跳过: {error_msg}")
                self._update_item_status(item.id, "error", error_msg)
                return {"success": False, "error": error_msg}
            
            # 重试机制
            last_error = None
            for retry in range(self.max_retries):
                try:
                    self.logger.info(f"需求项 {item.id} 第{retry + 1}次尝试调用AI")
                    
                    # 调用AI生成内容
                    ai_result = await self.ai_client.generate_assessment_content(
                        test_description=test_item_description,
                        test_method=test_method,
                        original_requirement=original_requirement
                    )
                    
                    processing_time = time.time() - start_time
                    
                    # 更新数据库
                    self._update_item_with_ai_result(item.id, ai_result, raw_response="", processing_time=processing_time)
                    
                    # 更新内存进度
                    self.processing_items -= 1
                    self.completed_items += 1
                    
                    self.logger.info(f"需求项 {item.id} 处理成功, 耗时: {processing_time:.2f}秒")
                    return {"success": True, "processing_time": processing_time}
                    
                except Exception as e:
                    last_error = str(e)
                    self.logger.warning(f"需求项 {item.id} AI生成失败，重试 {retry + 1}/{self.max_retries}: {last_error}")
                    
                    if retry < self.max_retries - 1:
                        await asyncio.sleep(1)  # 重试前等待1秒
            
            # 所有重试都失败
            processing_time = time.time() - start_time
            error_msg = f"AI生成失败，已重试{self.max_retries}次: {last_error}"
            self.logger.error(f"需求项 {item.id} 最终失败: {error_msg}")
            
            self._update_item_status(item.id, "error", error_msg, processing_time)
            
            # 更新内存进度
            self.processing_items -= 1
            self.error_items += 1
            
            return {"success": False, "error": error_msg}
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"处理需求项时出错: {str(e)}"
            self.logger.error(f"需求项 {item.id} 异常: {error_msg}")
            
            self._update_item_status(item.id, "error", error_msg, processing_time)
            
            # 更新内存进度
            if self.processing_items > 0:
                self.processing_items -= 1
            self.error_items += 1
            
            return {"success": False, "error": error_msg}

    def get_session_status(self) -> Dict[str, Any]:
        """
        获取会话处理状态 - 非阻塞版本
        
        Returns:
            Dict[str, Any]: 会话状态信息
        """
        import time
        import threading
        start_time = time.time()
        
        # 使用缓存减少数据库查询（缓存1秒）
        current_time = time.time()
        if self._status_cache and (current_time - self._cache_time) < 1.0:
            cached_result = self._status_cache.copy()
            cached_result["query_time"] = "0.000s (cached)"
            cached_result["api_time"] = f"{time.time() - start_time:.3f}s"
            return cached_result
        
        try:
            # 使用独立的数据库连接，避免锁定
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from ..config.config import DATABASE_URL
            
            # 创建独立的数据库引擎，专用于状态查询
            temp_engine = create_engine(
                DATABASE_URL, 
                connect_args={
                    "check_same_thread": False,
                    "timeout": 1  # 1秒超时，快速失败
                },
                pool_pre_ping=True,
                echo=False
            )
            TempSession = sessionmaker(bind=temp_engine)
            db = TempSession()
            
            try:
                # 获取会话信息
                session = db.query(AssessmentSession).filter(
                    AssessmentSession.session_id == self.session_id
                ).first()
                
                if not session:
                    return {"success": False, "error": "会话不存在"}
                
                # 获取需求项统计 - 优化为单个查询
                from sqlalchemy import func, case
                
                stats_query = db.query(
                    func.count(RequirementItem.id).label('total_items'),
                    func.sum(case(
                        (RequirementItem.generation_status == "completed", 1),
                        else_=0
                    )).label('completed_items'),
                    func.sum(case(
                        (RequirementItem.generation_status == "error", 1),
                        else_=0
                    )).label('error_items'),
                    func.sum(case(
                        (RequirementItem.generation_status == "processing", 1),
                        else_=0
                    )).label('processing_items')
                ).filter(
                    RequirementItem.session_id == self.session_id
                ).first()
                
                total_items = stats_query.total_items or 0
                completed_items = stats_query.completed_items or 0
                error_items = stats_query.error_items or 0
                processing_items = stats_query.processing_items or 0
                
                # 记录查询性能
                query_time = time.time() - start_time
                if query_time > 1.0:  # 超过1秒记录警告
                    self.logger.warning(f"状态查询耗时较长: {query_time:.2f}秒")
                
                result = {
                    "success": True,
                    "session_id": self.session_id,
                    "status": session.status,
                    "original_filename": session.original_filename,
                    "total_rows": session.total_rows,
                    "processed_rows": session.processed_rows,
                    "total_items": total_items,
                    "completed_items": completed_items,
                    "error_items": error_items,
                    "processing_items": processing_items,
                    "progress_percentage": (completed_items / total_items * 100) if total_items > 0 else 0,
                    "error_message": session.error_message,
                    "output_filename": session.output_filename,  # 添加输出文件名
                    "created_at": session.created_at.isoformat() if session.created_at else None,
                    "updated_at": session.updated_at.isoformat() if session.updated_at else None,
                    "query_time": f"{query_time:.3f}s"  # 添加查询时间用于调试
                }
                
                # 更新缓存
                self._status_cache = result.copy()
                self._cache_time = time.time()
                
                return result
                
            finally:
                db.close()
                temp_engine.dispose()  # 清理临时引擎
                
        except Exception as e:
            error_msg = f"获取会话状态时出错: {str(e)}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def get_session_status_simple(self) -> Dict[str, Any]:
        """
        获取会话处理状态 - 简化版本，参考ConfigurationItem实现
        
        Returns:
            Dict[str, Any]: 会话状态信息
        """
        try:
            db = get_db_session()
            
            try:
                # 获取会话信息
                session = db.query(AssessmentSession).filter(
                    AssessmentSession.session_id == self.session_id
                ).first()
                
                if not session:
                    return {"success": False, "error": "会话不存在"}
                
                # 获取需求项统计
                total_items = db.query(RequirementItem).filter(
                    RequirementItem.session_id == self.session_id
                ).count()
                
                completed_items = db.query(RequirementItem).filter(
                    RequirementItem.session_id == self.session_id,
                    RequirementItem.generation_status == "completed"
                ).count()
                
                error_items = db.query(RequirementItem).filter(
                    RequirementItem.session_id == self.session_id,
                    RequirementItem.generation_status == "error"
                ).count()
                
                processing_items = db.query(RequirementItem).filter(
                    RequirementItem.session_id == self.session_id,
                    RequirementItem.generation_status == "processing"
                ).count()
                
                return {
                    "success": True,
                    "session_id": self.session_id,
                    "status": session.status,
                    "original_filename": session.original_filename,
                    "total_rows": session.total_rows,
                    "processed_rows": session.processed_rows,
                    "total_items": total_items,
                    "completed_items": completed_items,
                    "error_items": error_items,
                    "processing_items": processing_items,
                    "progress_percentage": (completed_items / total_items * 100) if total_items > 0 else 0,
                    "error_message": session.error_message,
                    "output_filename": session.output_filename,
                    "created_at": session.created_at.isoformat() if session.created_at else None,
                    "updated_at": session.updated_at.isoformat() if session.updated_at else None
                }
                
            finally:
                db.close()
                
        except Exception as e:
            error_msg = f"获取会话状态时出错: {str(e)}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def get_memory_status(self) -> Dict[str, Any]:
        """
        获取基于内存变量的处理状态 - 快速无阻塞
        
        Returns:
            Dict[str, Any]: 会话状态信息
        """
        try:
            # 计算进度百分比
            progress_percentage = 0
            if self.total_items > 0:
                progress_percentage = (self.completed_items / self.total_items) * 100
            
            # 判断整体状态
            if self.completed_items + self.error_items >= self.total_items and self.total_items > 0:
                overall_status = "completed"
                self.current_status = "completed"
            elif self.error_items > 0 and self.completed_items + self.error_items + self.processing_items >= self.total_items:
                overall_status = "completed"  # 即使有错误，只要处理完了就是completed
                self.current_status = "completed"
            else:
                overall_status = self.current_status
            
            return {
                "success": True,
                "session_id": self.session_id,
                "status": overall_status,
                "progress": progress_percentage,
                "original_filename": self.original_filename,
                "total_rows": self.total_items,
                "processed_rows": self.completed_items + self.error_items,
                "total_items": self.total_items,
                "completed_items": self.completed_items,
                "error_items": self.error_items,
                "processing_items": self.processing_items,
                "error_message": None,
                "output_filename": self.output_filename
            }
            
        except Exception as e:
            error_msg = f"获取内存状态时出错: {str(e)}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def generate_output_file(self) -> Dict[str, Any]:
        """
        生成输出Excel文件
        
        Returns:
            Dict[str, Any]: 生成结果
        """
        try:
            self.logger.info("开始生成输出文件")
            
            # 生成输出文件路径
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"assessment_result_{self.session_id}_{timestamp}.xlsx"
            output_path = UPLOAD_DIR / "outputs" / output_filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 使用Excel处理器生成文件
            result = self.excel_processor.generate_output_excel(str(output_path))
            
            if result["success"]:
                result["filename"] = output_filename
                self._log_operation("generate", "success", f"输出文件生成成功: {output_filename}")
                self.logger.info(f"输出文件生成成功: {output_path}")
            else:
                self._log_operation("generate", "error", f"输出文件生成失败: {result.get('error', '未知错误')}")
                self.logger.error(f"输出文件生成失败: {result.get('error', '未知错误')}")
            
            return result
            
        except Exception as e:
            error_msg = f"生成输出文件时出错: {str(e)}"
            self.logger.error(error_msg)
            self._log_operation("generate", "error", error_msg)
            return {"success": False, "error": error_msg}

    def _get_pending_items(self) -> List[RequirementItem]:
        """获取待处理的需求项"""
        try:
            db = get_db_session()
            
            try:
                items = db.query(RequirementItem).filter(
                    RequirementItem.session_id == self.session_id,
                    RequirementItem.generation_status == "pending"
                ).order_by(RequirementItem.row_index).all()
                
                return items
                
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"获取待处理需求项时出错: {str(e)}")
            return []

    def _update_session_status(self, status: str, error_message: str = None):
        """更新会话状态"""
        try:
            db = get_db_session()
            
            try:
                session = db.query(AssessmentSession).filter(
                    AssessmentSession.session_id == self.session_id
                ).first()
                
                if session:
                    session.status = status
                    if error_message:
                        session.error_message = error_message
                    db.commit()
                    
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"更新会话状态时出错: {str(e)}")
    
    def _update_session_with_output_file(self, status: str, output_filename: str, error_message: str = None):
        """更新会话状态并保存输出文件名"""
        try:
            db = get_db_session()
            
            try:
                session = db.query(AssessmentSession).filter(
                    AssessmentSession.session_id == self.session_id
                ).first()
                
                if session:
                    session.status = status
                    session.output_filename = output_filename
                    if error_message:
                        session.error_message = error_message
                    db.commit()
                    
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"更新会话状态和输出文件名时出错: {str(e)}")

    def _update_session_progress(self, processed_count: int):
        """更新会话进度"""
        try:
            db = get_db_session()
            
            try:
                session = db.query(AssessmentSession).filter(
                    AssessmentSession.session_id == self.session_id
                ).first()
                
                if session:
                    session.processed_rows = processed_count
                    db.commit()
                    
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"更新会话进度时出错: {str(e)}")

    def _update_item_status(self, item_id: int, status: str, error_message: str = None, processing_time: float = None):
        """更新需求项状态"""
        try:
            db = get_db_session()
            
            try:
                item = db.query(RequirementItem).filter(RequirementItem.id == item_id).first()
                
                if item:
                    item.generation_status = status
                    if error_message:
                        item.error_message = error_message
                    if processing_time is not None:
                        item.processing_time = processing_time
                    db.commit()
                    
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"更新需求项状态时出错: {str(e)}")

    def _update_item_with_ai_result(self, item_id: int, ai_result: Dict[str, Any], raw_response: str, processing_time: float):
        """更新需求项的AI生成结果"""
        try:
            db = get_db_session()
            
            try:
                item = db.query(RequirementItem).filter(RequirementItem.id == item_id).first()
                
                if item:
                    item.adequacy_requirement = ai_result.get("adequacy_requirement", "")
                    item.pass_criteria = ai_result.get("pass_criteria", "")
                    item.ai_response_raw = raw_response
                    item.generation_status = "completed"
                    item.processing_time = processing_time
                    item.error_message = None
                    db.commit()
                    
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"更新需求项AI结果时出错: {str(e)}")

    def _log_operation(self, operation_type: str, status: str, message: str = None, execution_time: float = None):
        """记录操作日志"""
        try:
            db = get_db_session()
            
            try:
                log = GenerationLog(
                    session_id=self.session_id,
                    operation_type=operation_type,
                    status=status,
                    message=message,
                    execution_time=execution_time
                )
                db.add(log)
                db.commit()
                
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"记录操作日志时出错: {str(e)}")

    @classmethod
    def create_new_session(cls) -> 'AssessmentFormService':
        """创建新的会话服务实例"""
        return cls() 