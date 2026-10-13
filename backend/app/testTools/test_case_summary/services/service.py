"""
测试用例总结服务
"""
import asyncio
import time
import uuid
import json
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime

from ..models.models import TestCaseSummarySession, TestItem, GenerationLog
from ..database.database import get_db_session
from .ai_client import TestCaseSummaryAIClient
from .excel_processor import ExcelProcessor
from ..config.config import AI_GENERATION_CONFIG, UPLOAD_DIR
from ..utils.logger import get_session_logger, setup_session_logger

class TestCaseSummaryService:
    def __init__(self, session_id: str = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.logger = setup_session_logger(self.session_id)
        self.ai_client = TestCaseSummaryAIClient(self.session_id)
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
        
        # 失败项详情缓存：{ item_id: { test_item_name, error_message, retry_history: [...] } }
        self.failed_items_detail: Dict[int, Dict[str, Any]] = {}
        
    def process_uploaded_file(self, file_path: str, original_filename: str, tester_name: str = '') -> Dict[str, Any]:
        """
        处理上传的测试用例Excel文件
        """
        try:
            self.logger.info(f"开始处理上传文件: {original_filename}")
            
            # 初始化进度跟踪
            self.original_filename = original_filename
            self.current_status = "processing"
            
            # 处理Excel文件
            session_id, result = self.excel_processor.process_uploaded_file(file_path, original_filename, tester_name=tester_name)
            
            if result["success"]:
                # 更新进度信息
                self.total_items = result.get("total_test_items", 0)
                self.completed_items = 0
                self.error_items = 0
                self.processing_items = 0
                
                self.logger.info(f"文件处理成功 - 会话ID: {self.session_id}")
                return {"success": True, "total_test_items": result.get("total_test_items", 0)}
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
        异步处理会话中的所有测试项
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"开始处理会话: {self.session_id}")
            
            # 更新会话状态为处理中
            self._update_session_status("processing")
            
            # 获取待处理的测试项
            pending_items = self._get_pending_items()
            if not pending_items:
                self.logger.warning("没有找到待处理的测试项")
                return {"success": False, "error": "没有找到待处理的测试项"}
            
            self.logger.info(f"找到{len(pending_items)}个待处理的测试项")
            
            # 分批处理
            total_processed = 0
            total_errors = 0
            
            for i in range(0, len(pending_items), self.batch_size):
                batch = pending_items[i:i + self.batch_size]
                self.logger.info(f"处理批次 {i//self.batch_size + 1}: {len(batch)}个测试项")
                
                batch_result = await self._process_batch(batch)
                total_processed += batch_result["processed"]
                total_errors += batch_result["errors"]
                
                # 更新进度
                self._update_session_progress(total_processed + total_errors)
                
                self.logger.info(f"批次处理完成 - 成功: {batch_result['processed']}, 失败: {batch_result['errors']}")
            
            # 更新最终状态
            if total_errors == 0:
                status = "success"
                message = f"所有{total_processed}个测试项处理成功"
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
                    self.output_filename = generate_result["filename"]
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
            self.current_status = "error"
            
            return {"success": False, "error": error_msg}
    
    async def _process_batch(self, batch: List[TestItem]) -> Dict[str, int]:
        """
        并发处理一批测试项
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

    async def _process_single_item(self, item: TestItem) -> Dict[str, Any]:
        """
        处理单个测试项
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"开始处理测试项 ID: {item.id}, 名称: {item.test_item_name}")
            
            # 更新状态为处理中
            self._update_item_status(item.id, "processing")
            self.processing_items += 1
            
            # 解析测试用例数据
            test_cases = json.loads(item.test_cases_data) if item.test_cases_data else []
            
            if not test_cases:
                error_msg = "测试用例数据为空"
                self.logger.warning(f"测试项 {item.id} 跳过: {error_msg}")
                self._update_item_status(item.id, "error", error_msg)
                if self.processing_items > 0:
                    self.processing_items -= 1
                self.error_items += 1
                self.failed_items_detail[item.id] = {
                    "item_id": item.id,
                    "test_item_name": item.test_item_name,
                    "error_message": error_msg,
                    "retry_history": []
                }
                return {"success": False, "error": error_msg}
            
            # 重试机制
            last_error = None
            retry_history = []
            for retry in range(self.max_retries):
                try:
                    attempt_start = time.time()
                    self.logger.info(f"测试项 {item.id} 第{retry + 1}/{self.max_retries}次尝试调用AI")
                    
                    # 调用AI生成总结
                    ai_result = await self.ai_client.generate_test_case_summary(
                        test_item_name=item.test_item_name,
                        test_cases=test_cases
                    )
                    
                    attempt_time = time.time() - attempt_start
                    processing_time = time.time() - start_time
                    
                    if ai_result["success"]:
                        # 更新数据库
                        self._update_item_with_ai_result(item.id, ai_result["summary"], ai_result["raw_response"], processing_time)
                        
                        # 更新内存进度
                        if self.processing_items > 0:
                            self.processing_items -= 1
                        self.completed_items += 1
                        self.failed_items_detail.pop(item.id, None)
                        
                        self.logger.info(f"测试项 {item.id} 处理成功, 尝试次数: {retry + 1}, 耗时: {processing_time:.2f}秒")
                        return {"success": True, "processing_time": processing_time}
                    else:
                        last_error = ai_result.get("error", "AI生成失败")
                        retry_history.append({"attempt": retry + 1, "error": last_error, "time": round(attempt_time, 2)})
                        self.logger.warning(f"测试项 {item.id} AI生成失败，重试 {retry + 1}/{self.max_retries}: {last_error}")
                        
                        if retry < self.max_retries - 1:
                            await asyncio.sleep(1)  # 重试前等待1秒
                    
                except Exception as e:
                    attempt_time = time.time() - attempt_start
                    last_error = str(e)
                    retry_history.append({"attempt": retry + 1, "error": last_error, "time": round(attempt_time, 2)})
                    self.logger.warning(f"测试项 {item.id} AI生成失败，重试 {retry + 1}/{self.max_retries}: {last_error}")
                    
                    if retry < self.max_retries - 1:
                        await asyncio.sleep(1)  # 重试前等待1秒
            
            # 所有重试都失败
            processing_time = time.time() - start_time
            error_msg = f"已自动重试{self.max_retries}次仍失败: {last_error}"
            self.logger.error(f"测试项 {item.id} 最终失败: {error_msg}")
            
            self._update_item_status(item.id, "error", error_msg, processing_time)
            
            # 更新内存进度
            if self.processing_items > 0:
                self.processing_items -= 1
            self.error_items += 1
            self.failed_items_detail[item.id] = {
                "item_id": item.id,
                "test_item_name": item.test_item_name,
                "error_message": error_msg,
                "retry_history": retry_history
            }
            
            return {"success": False, "error": error_msg}
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"处理测试项时出错: {str(e)}"
            self.logger.error(f"测试项 {item.id} 异常: {error_msg}")
            
            self._update_item_status(item.id, "error", error_msg, processing_time)
            
            # 更新内存进度
            if self.processing_items > 0:
                self.processing_items -= 1
            self.error_items += 1
            self.failed_items_detail[item.id] = {
                "item_id": item.id,
                "test_item_name": item.test_item_name,
                "error_message": error_msg,
                "retry_history": []
            }
            
            return {"success": False, "error": error_msg}

    def get_memory_status(self) -> Dict[str, Any]:
        """
        获取基于内存变量的处理状态 - 快速无阻塞
        """
        try:
            # 计算进度百分比
            progress_percentage = 0
            if self.total_items > 0:
                progress_percentage = ((self.completed_items + self.error_items) / self.total_items) * 100
            
            # 判断整体状态
            if self.completed_items + self.error_items >= self.total_items and self.total_items > 0:
                overall_status = "completed"
                self.current_status = "completed"
            else:
                overall_status = self.current_status
            
            return {
                "success": True,
                "session_id": self.session_id,
                "status": overall_status,
                "progress": progress_percentage,
                "original_filename": self.original_filename,
                "total_test_items": self.total_items,
                "processed_test_items": self.completed_items + self.error_items,
                "completed_items": self.completed_items,
                "error_items": self.error_items,
                "processing_items": self.processing_items,
                "error_message": None,
                "output_filename": self.output_filename,
                "failed_items": list(self.failed_items_detail.values())
            }
            
        except Exception as e:
            error_msg = f"获取内存状态时出错: {str(e)}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}

    async def retry_single_item(self, item_id: int) -> Dict[str, Any]:
        """手动重试单个测试项"""
        start_time = time.time()
        try:
            db = get_db_session()
            try:
                item = db.query(TestItem).filter(
                    TestItem.id == item_id,
                    TestItem.session_id == self.session_id
                ).first()
            finally:
                db.close()

            if not item:
                return {"success": False, "error": "测试项不存在"}

            test_cases = json.loads(item.test_cases_data) if item.test_cases_data else []
            if not test_cases:
                error_msg = "测试用例数据为空"
                self._update_item_status(item.id, "error", error_msg)
                return {"success": False, "error": error_msg}

            self._update_item_status(item.id, "processing")
            ai_result = await self.ai_client.generate_test_case_summary(
                test_item_name=item.test_item_name,
                test_cases=test_cases,
                include_debug=True
            )
            processing_time = time.time() - start_time

            if ai_result["success"]:
                self._update_item_with_ai_result(item.id, ai_result["summary"], ai_result["raw_response"], processing_time)
                self.failed_items_detail.pop(item.id, None)
                self._refresh_memory_counts()
                generate_result = self.generate_output_file()
                if generate_result.get("success"):
                    self.output_filename = generate_result["filename"]
                    self._update_session_with_output_file("completed", generate_result["filename"])
                return {
                    "success": True,
                    "item_id": item.id,
                    "test_item_name": item.test_item_name,
                    "summary": ai_result["summary"],
                    "raw_request": ai_result.get("raw_request"),
                    "raw_response": ai_result.get("raw_response"),
                    "output_filename": self.output_filename,
                    "message": "手动重试成功，结果已合并到最终表单"
                }

            error_msg = ai_result.get("error", "AI生成失败")
            self._update_item_status(item.id, "error", error_msg, processing_time)
            self.failed_items_detail[item.id] = {
                "item_id": item.id,
                "test_item_name": item.test_item_name,
                "error_message": error_msg,
                "retry_history": [{"attempt": "manual", "error": error_msg, "time": round(processing_time, 2)}]
            }
            self._refresh_memory_counts()
            return {
                "success": False,
                "item_id": item.id,
                "test_item_name": item.test_item_name,
                "error": error_msg,
                "raw_request": ai_result.get("raw_request"),
                "raw_response": ai_result.get("raw_response")
            }
        except Exception as e:
            error_msg = f"手动重试测试项时出错: {str(e)}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def get_failed_items(self) -> Dict[str, Any]:
        """获取失败测试项列表"""
        try:
            db = get_db_session()
            try:
                items = db.query(TestItem).filter(
                    TestItem.session_id == self.session_id,
                    TestItem.generation_status == "error"
                ).order_by(TestItem.id).all()
            finally:
                db.close()

            failed_items = []
            for item in items:
                detail = self.failed_items_detail.get(item.id, {})
                failed_items.append({
                    "item_id": item.id,
                    "test_item_name": item.test_item_name,
                    "error_message": item.error_message or detail.get("error_message") or "未知错误",
                    "retry_history": detail.get("retry_history", []),
                    "processing_time": item.processing_time
                })
            return {"success": True, "failed_items": failed_items}
        except Exception as e:
            error_msg = f"获取失败项详情时出错: {str(e)}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def _refresh_memory_counts(self):
        """刷新内存计数"""
        try:
            db = get_db_session()
            try:
                items = db.query(TestItem).filter(TestItem.session_id == self.session_id).all()
                self.total_items = len(items)
                self.completed_items = len([item for item in items if item.generation_status == "completed"])
                self.error_items = len([item for item in items if item.generation_status == "error"])
                self.processing_items = len([item for item in items if item.generation_status == "processing"])
            finally:
                db.close()
        except Exception as e:
            self.logger.error(f"刷新内存计数时出错: {str(e)}")

    def generate_output_file(self) -> Dict[str, Any]:
        """
        生成输出Excel文件
        """
        try:
            self.logger.info("开始生成输出文件")
            
            # 生成输出文件路径
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"test_case_summary_{self.session_id}_{timestamp}.xlsx"
            output_path = UPLOAD_DIR / "outputs" / output_filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 使用Excel处理器生成文件
            result = self.excel_processor.generate_output_excel(str(output_path))
            
            if result["success"]:
                result["filename"] = output_filename
                self.output_filename = output_filename
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

    def _get_pending_items(self) -> List[TestItem]:
        """获取待处理的测试项"""
        try:
            db = get_db_session()
            
            try:
                items = db.query(TestItem).filter(
                    TestItem.session_id == self.session_id,
                    TestItem.generation_status == "pending"
                ).order_by(TestItem.id).all()
                
                return items
                
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"获取待处理测试项时出错: {str(e)}")
            return []

    def _update_session_status(self, status: str, error_message: str = None):
        """更新会话状态"""
        try:
            db = get_db_session()
            
            try:
                session = db.query(TestCaseSummarySession).filter(
                    TestCaseSummarySession.session_id == self.session_id
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
                session = db.query(TestCaseSummarySession).filter(
                    TestCaseSummarySession.session_id == self.session_id
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
                session = db.query(TestCaseSummarySession).filter(
                    TestCaseSummarySession.session_id == self.session_id
                ).first()
                
                if session:
                    session.processed_test_items = processed_count
                    db.commit()
                    
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"更新会话进度时出错: {str(e)}")

    def _update_item_status(self, item_id: int, status: str, error_message: str = None, processing_time: float = None):
        """更新测试项状态"""
        try:
            db = get_db_session()
            
            try:
                item = db.query(TestItem).filter(TestItem.id == item_id).first()
                
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
            self.logger.error(f"更新测试项状态时出错: {str(e)}")

    def _update_item_with_ai_result(self, item_id: int, ai_summary: str, raw_response: str, processing_time: float):
        """更新测试项的AI生成结果"""
        try:
            db = get_db_session()
            
            try:
                item = db.query(TestItem).filter(TestItem.id == item_id).first()
                
                if item:
                    item.ai_summary = ai_summary
                    item.ai_response_raw = raw_response
                    item.generation_status = "completed"
                    item.processing_time = processing_time
                    item.error_message = None
                    db.commit()
                    
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"更新测试项AI结果时出错: {str(e)}")

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
    def create_new_session(cls) -> 'TestCaseSummaryService':
        """创建新的会话服务实例"""
        return cls() 