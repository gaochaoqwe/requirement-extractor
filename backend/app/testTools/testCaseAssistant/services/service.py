"""
测试用例反向推导服务
"""
import asyncio
import time
import uuid
import json
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime

from ..models.models import TestCaseReverseSession, TestItem, GenerationLog
from ..database.database import get_db_session
from .excel_processor import ExcelProcessor
from ..config.config import AI_GENERATION_CONFIG, UPLOAD_DIR
from ..utils.logger import get_session_logger, setup_session_logger

class TestCaseReverseService:
    def __init__(self, session_id: str = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.logger = setup_session_logger(self.session_id)
        self.ai_client = None
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
        处理上传的测试用例Excel文件
        """
        try:
            self.logger.info(f"开始处理上传文件: {original_filename}")
            
            # 初始化进度跟踪
            self.original_filename = original_filename
            self.current_status = "processing"
            
            # 处理Excel文件
            session_id, result = self.excel_processor.process_uploaded_file(file_path, original_filename)
            
            if result["success"]:
                # 更新内存变量
                self.total_items = result.get("total_test_items", 0)
                self.completed_items = 0
                self.error_items = 0
                self.processing_items = 0
                
                self.logger.info(f"文件处理成功，共找到 {self.total_items} 个测试项")
                
                return {
                    "success": True,
                    "session_id": session_id,
                    "message": "文件上传成功，正在进行反向推导",
                    "status": "processing",
                    "total_test_items": self.total_items,
                    "processed_test_items": 0
                }
            else:
                return result
                
        except Exception as e:
            error_msg = f"处理上传文件时出错: {str(e)}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    async def process_session(self, session_id: str, processing_mode: str = "normal") -> Dict[str, Any]:
        """
        处理会话中的所有测试项
        """
        try:
            self.session_id = session_id
            self.logger = get_session_logger(session_id)
            self.ai_client = None
            
            start_time = time.time()
            self.logger.info(f"开始处理会话: {session_id} (模式: {processing_mode})")
            
            # 获取待处理的测试项
            pending_items = self._get_pending_items(session_id)
            
            if not pending_items:
                self.logger.info("没有找到待处理的测试项")
                return {"success": True, "message": "没有待处理的测试项"}
            
            # 更新会话的处理模式
            self._update_session_processing_mode(session_id, processing_mode)
            
            # 更新内存变量
            self.processing_mode = processing_mode
            self.total_items = len(pending_items)
            self.completed_items = 0
            self.error_items = 0
            self.processing_items = 0
            
            self.logger.info(f"找到 {len(pending_items)} 个待处理的测试项")
            
            # 分批处理测试项
            success_count = 0
            error_count = 0
            
            for i in range(0, len(pending_items), self.batch_size):
                batch = pending_items[i:i + self.batch_size]
                self.logger.info(f"处理批次 {i//self.batch_size + 1}，包含 {len(batch)} 个测试项")
                
                # 并发处理当前批次
                tasks = []
                for item in batch:
                    self.processing_items += 1
                    task = self._process_single_item(item, processing_mode)
                    tasks.append(task)
                
                # 等待当前批次完成
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 统计结果
                for result in batch_results:
                    self.processing_items -= 1
                    if isinstance(result, Exception):
                        error_count += 1
                        self.error_items += 1
                        self.logger.error(f"批次处理异常: {str(result)}")
                    elif result and result.get("success"):
                        success_count += 1
                        self.completed_items += 1
                    else:
                        error_count += 1
                        self.error_items += 1

                # 实时更新数据库中的进度信息
                self._update_session_progress(session_id, self.completed_items)
                
                self.logger.info(f"批次处理完成 - 成功: {success_count}, 失败: {error_count}")
                
                # 短暂延迟，让前端有时间获取状态更新
                await asyncio.sleep(0.5)
            
            # 更新会话状态
            self._update_session_status(session_id, "completed")
            
            execution_time = time.time() - start_time
            self.logger.info(f"会话处理完成 - 处理完成 - 成功: {success_count}, 失败: {error_count}, 耗时: {execution_time:.2f}秒")
            
            # 自动生成Excel输出文件
            self.logger.info("开始自动生成Excel输出文件")
            output_result = self.generate_output_file(session_id)
            if output_result["success"]:
                self.output_filename = output_result["filename"]
                self.logger.info(f"Excel文件自动生成成功: {self.output_filename}")
            else:
                self.logger.error(f"Excel文件自动生成失败: {output_result.get('error')}")
            
            return {
                "success": True,
                "message": "会话处理完成",
                "total_items": len(pending_items),
                "success_count": success_count,
                "error_count": error_count,
                "execution_time": execution_time,
                "output_filename": self.output_filename
            }
            
        except Exception as e:
            error_msg = f"处理会话时出错: {str(e)}"
            self.logger.error(error_msg)
            self._update_session_status(session_id, "error", error_msg)
            return {"success": False, "error": error_msg}
    
    async def _process_single_item(self, item: TestItem, processing_mode: str = "normal") -> Dict[str, Any]:
        """
        处理单个测试项
        """
        try:
            self.logger.info(f"开始处理测试项: {item.test_item_name} (模式: {processing_mode})")

            if self.ai_client is None:
                return {"success": False, "error": "反向推导AI功能已移除"}
            
            # 解析测试用例数据
            test_cases_data = json.loads(item.test_cases_data) if item.test_cases_data else []
            
            if not test_cases_data:
                self.logger.warning(f"测试项 {item.test_item_name} 没有测试用例数据")
                return {"success": False, "error": "没有测试用例数据"}
            
            # 更新重试次数
            self._update_item_retry_count(item, 0)
            
            # AI客户端已经内置了重试机制，这里直接调用
            try:
                self.logger.info(f"测试项 {item.test_item_name} 调用AI生成")
                
                # 调用AI生成测试内容和测试方法（AI客户端内部处理重试）
                ai_result = await self.ai_client.generate_test_content_and_method(
                    item.test_item_name, 
                    test_cases_data,
                    processing_mode
                )
                
                if ai_result["success"]:
                    # 更新数据库中的测试项
                    self._update_item_with_ai_result(item, ai_result, processing_mode)
                    
                    self.logger.info(f"测试项 {item.test_item_name} 处理成功")
                    return {"success": True, "item_id": item.id}
                else:
                    error_msg = ai_result.get("error", "AI生成失败")
                    # 更新重试次数（AI客户端内部已经重试了3次）
                    self._update_item_retry_count(item, 3)
                    self._update_item_with_error(item, f"AI生成失败: {error_msg}")
                    self.logger.error(f"测试项 {item.test_item_name} 最终失败: {error_msg}")
                    return {"success": False, "error": error_msg}
                        
            except Exception as e:
                error_msg = f"处理测试项时出错: {str(e)}"
                self.logger.error(f"测试项 {item.test_item_name} 处理异常: {error_msg}")
                self._update_item_with_error(item, error_msg)
                return {"success": False, "error": error_msg}
            
        except Exception as e:
            error_msg = f"处理测试项时出错: {str(e)}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def _update_item_with_ai_result(self, item: TestItem, ai_result: Dict[str, Any], processing_mode: str = "normal"):
        """更新测试项的AI生成结果"""
        try:
            with get_db_session() as db:
                db_item = db.query(TestItem).filter(TestItem.id == item.id).first()
                if db_item:
                    db_item.test_content = ai_result["test_content"]
                    db_item.test_method = ai_result["test_method"]
                    db_item.ai_response_raw = ai_result["raw_response"]
                    db_item.generation_status = "completed"
                    db_item.updated_at = datetime.now()
                    
                    # 如果是模板模式，更新用例模板字段
                    if processing_mode == "template":
                        db_item.case_template_name = ai_result.get("case_template_name", "")
                        db_item.case_template_input = ai_result.get("case_template_input", "")
                        db_item.case_template_expected = ai_result.get("case_template_expected", "")
                    
                    db.commit()
                    
        except Exception as e:
            self.logger.error(f"更新测试项AI结果时出错: {str(e)}")
    
    def _update_item_with_error(self, item: TestItem, error_message: str):
        """更新测试项的错误信息"""
        try:
            with get_db_session() as db:
                db_item = db.query(TestItem).filter(TestItem.id == item.id).first()
                if db_item:
                    db_item.error_message = error_message
                    db_item.generation_status = "error"
                    db_item.updated_at = datetime.now()
                    db.commit()
                    
        except Exception as e:
            self.logger.error(f"更新测试项错误信息时出错: {str(e)}")
    
    def _update_item_retry_count(self, item: TestItem, retry_count: int):
        """更新测试项的重试次数"""
        try:
            with get_db_session() as db:
                db_item = db.query(TestItem).filter(TestItem.id == item.id).first()
                if db_item:
                    db_item.retry_count = retry_count
                    db_item.updated_at = datetime.now()
                    db.commit()
                    
        except Exception as e:
            self.logger.error(f"更新测试项重试次数时出错: {str(e)}")
    
    def _get_pending_items(self, session_id: str) -> List[TestItem]:
        """获取待处理的测试项"""
        try:
            with get_db_session() as db:
                items = db.query(TestItem).filter(
                    TestItem.session_id == session_id,
                    TestItem.generation_status == "pending"
                ).all()
                return items
                
        except Exception as e:
            self.logger.error(f"获取待处理测试项时出错: {str(e)}")
            return []
    
    def _update_session_status(self, session_id: str, status: str, error_message: str = None):
        """更新会话状态"""
        try:
            # 更新内存状态
            self.current_status = status
            if error_message:
                self.error_message = error_message
            
            # 更新数据库状态
            with get_db_session() as db:
                session = db.query(TestCaseReverseSession).filter(
                    TestCaseReverseSession.session_id == session_id
                ).first()
                
                if session:
                    session.status = status
                    if error_message:
                        session.error_message = error_message
                    session.updated_at = datetime.now()
                    db.commit()
                    
        except Exception as e:
            self.logger.error(f"更新会话状态时出错: {str(e)}")
    
    def _update_session_processing_mode(self, session_id: str, processing_mode: str):
        """更新会话的处理模式"""
        try:
            with get_db_session() as db:
                session = db.query(TestCaseReverseSession).filter(
                    TestCaseReverseSession.session_id == session_id
                ).first()
                
                if session:
                    session.processing_mode = processing_mode
                    session.updated_at = datetime.now()
                    db.commit()
                    
        except Exception as e:
            self.logger.error(f"更新会话处理模式时出错: {str(e)}")
    
    def _update_session_progress(self, session_id: str, completed_items: int):
        """实时更新会话的已完成测试项数量"""
        try:
            with get_db_session() as db:
                session = db.query(TestCaseReverseSession).filter(
                    TestCaseReverseSession.session_id == session_id
                ).first()
                
                if session:
                    session.processed_test_items = completed_items
                    session.updated_at = datetime.now()
                    db.commit()
                    
        except Exception as e:
            self.logger.error(f"更新会话进度时出错: {str(e)}")
    
    def get_memory_status(self) -> Dict[str, Any]:
        """获取内存中的状态信息"""
        return {
            "success": True,
            "session_id": self.session_id,
            "status": self.current_status,
            "progress": (self.completed_items / self.total_items * 100) if self.total_items > 0 else 0,
            "original_filename": self.original_filename,
            "total_rows": self.total_items,
            "processed_rows": self.completed_items,
            "total_items": self.total_items,
            "completed_items": self.completed_items,
            "error_items": self.error_items,
            "processing_items": self.processing_items,
            "processing_mode": getattr(self, 'processing_mode', 'normal'),
            "error_message": None,
            "output_filename": self.output_filename
        }
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """获取会话状态"""
        try:
            with get_db_session() as db:
                # 获取会话信息
                session = db.query(TestCaseReverseSession).filter(
                    TestCaseReverseSession.session_id == session_id
                ).first()
                
                if not session:
                    return {"success": False, "error": "会话不存在"}
                
                # 获取测试项统计
                total_items = db.query(TestItem).filter(TestItem.session_id == session_id).count()
                completed_items = db.query(TestItem).filter(
                    TestItem.session_id == session_id,
                    TestItem.generation_status == "completed"
                ).count()
                error_items = db.query(TestItem).filter(
                    TestItem.session_id == session_id,
                    TestItem.generation_status == "error"
                ).count()
                processing_items = db.query(TestItem).filter(
                    TestItem.session_id == session_id,
                    TestItem.generation_status == "processing"
                ).count()
                
                progress = (completed_items / total_items * 100) if total_items > 0 else 0
                
                return {
                    "success": True,
                    "session_id": session_id,
                    "status": session.status,
                    "progress": progress,
                    "original_filename": session.original_filename,
                    "total_rows": session.total_test_items,
                    "processed_rows": session.processed_test_items,
                    "total_items": total_items,
                    "completed_items": completed_items,
                    "error_items": error_items,
                    "processing_items": processing_items,
                    "processing_mode": session.processing_mode or 'normal',
                    "error_message": session.error_message,
                    "output_filename": session.output_filename,
                    "created_at": session.created_at.isoformat() if session.created_at else None,
                    "updated_at": session.updated_at.isoformat() if session.updated_at else None
                }
                
        except Exception as e:
            error_msg = f"获取会话状态时出错: {str(e)}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def generate_output_file(self, session_id: str) -> Dict[str, Any]:
        """生成输出Excel文件"""
        try:
            self.logger.info(f"开始生成会话 {session_id} 的输出文件")
            
            # 调用Excel处理器生成输出文件
            result = self.excel_processor.generate_output_excel(session_id)
            
            if result["success"]:
                # 更新会话的输出文件名
                with get_db_session() as db:
                    session = db.query(TestCaseReverseSession).filter(
                        TestCaseReverseSession.session_id == session_id
                    ).first()
                    
                    if session:
                        session.output_filename = result["filename"]
                        session.updated_at = datetime.now()
                        db.commit()
                        
                        self.logger.info(f"输出文件生成成功: {result['filename']}")
                
                return result
            else:
                self.logger.error(f"生成输出文件失败: {result.get('error')}")
                return result
                
        except Exception as e:
            error_msg = f"生成输出文件时出错: {str(e)}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg} 