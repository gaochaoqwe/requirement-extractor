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
import os
import sys
import logging
from pathlib import Path
from typing import Tuple, Dict, Any

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 使用相对导入
from ..config.config import UPLOAD_DIR, SUPPORTED_FORMATS
from ..models.models import DocumentAnnotationSession, DocumentAnnotation
from ..database.database import get_db_session
from .document_processor import DocumentProcessor

logger = logging.getLogger(__name__)

class DocumentAnnotationService:
    """文档批注转问题报告单服务"""
    
    def __init__(self):
        self.current_status = {}  # 内存中的状态缓存
        
    async def process_uploaded_file(self, file_path: str, original_filename: str) -> Tuple[bool, str]:
        """处理上传的文档文件（异步入口，仅负责创建会话并启动后台任务）。"""
        try:
            # 验证文件格式
            if not self._validate_file_format(original_filename):
                return False, f"不支持的文件格式，仅支持: {', '.join(SUPPORTED_FORMATS)}"

            # 生成会话ID
            session_id = str(uuid.uuid4())

            # 创建会话记录
            with get_db_session() as db:
                session = DocumentAnnotationSession(
                    session_id=session_id,
                    original_filename=original_filename,
                    file_path=file_path,
                    status="processing",
                )
                db.add(session)

            # 初始化内存状态
            self.current_status[session_id] = {
                "status": "processing",
                "progress": 0,
                "total_annotations": 0,
                "processed_annotations": 0,
            }

            logger.info(f"开始处理文档: {original_filename}, 会话ID: {session_id}")

            # 在当前事件循环中启动后台任务，不阻塞本次请求
            asyncio.create_task(
                self._process_document_annotations_async(session_id, file_path, original_filename)
            )

            # 立即返回，让前端可以拿到 session_id 并开始轮询进度
            return True, session_id

        except Exception as e:
            logger.error(f"处理上传文件时出错: {str(e)}")
            return False, f"处理文件时出错: {str(e)}"
    
    def _validate_file_format(self, filename: str) -> bool:
        """验证文件格式"""
        return any(filename.lower().endswith(fmt) for fmt in SUPPORTED_FORMATS)
    
    async def _process_document_annotations_async(self, session_id: str, file_path: str, filename: str):
        """处理文档批注（异步版本）"""
        try:
            # 创建带session_id的document_processor
            document_processor = DocumentProcessor(session_id)
            
            # 更新状态
            self._update_session_status(session_id, "processing", 10)
            
            # 清理文件名
            clean_filename = document_processor._clean_filename(filename)
            
            # 提取批注
            annotations = document_processor.process_document_annotations(file_path, clean_filename)
            
            # 更新总数
            total_count = len(annotations)
            self._update_session_total_annotations(session_id, total_count)
            self._update_session_status(session_id, "processing", 30)
            
            if total_count == 0:
                self._update_session_status(session_id, "completed", 100)
                logger.warning(f"文档 {filename} 中未找到批注")
                return
            
            # 保存到数据库（包含AI生成）- 使用异步版本
            await document_processor.save_annotations_to_database_async(session_id, annotations)
            self._update_session_status(session_id, "processing", 80)
            
            # 生成输出文件
            output_path = document_processor.generate_excel_output(session_id)
            
            # 更新会话记录
            with get_db_session() as db:
                session = db.query(DocumentAnnotationSession).filter(
                    DocumentAnnotationSession.session_id == session_id
                ).first()
                if session:
                    session.output_file_path = output_path
                    session.processed_annotations = total_count
            
            # 完成处理
            self._update_session_status(session_id, "completed", 100)
            logger.info(f"文档处理完成: {filename}, 共处理 {total_count} 个批注")
            
        except Exception as e:
            logger.error(f"处理文档批注时出错: {str(e)}")
            self._update_session_status(session_id, "error", 0, str(e))
    
    def _update_session_status(self, session_id: str, status: str, progress: int = None, error_message: str = None):
        """更新会话状态"""
        # 更新内存状态
        if session_id not in self.current_status:
            self.current_status[session_id] = {}
        
        self.current_status[session_id]["status"] = status
        if progress is not None:
            self.current_status[session_id]["progress"] = progress
        if error_message:
            self.current_status[session_id]["error_message"] = error_message
        
        # 更新数据库
        try:
            with get_db_session() as db:
                session = db.query(DocumentAnnotationSession).filter(
                    DocumentAnnotationSession.session_id == session_id
                ).first()
                if session:
                    session.status = status
                    if error_message:
                        session.error_message = error_message
        except Exception as e:
            logger.error(f"更新数据库状态时出错: {str(e)}")
    
    def _update_session_total_annotations(self, session_id: str, total: int):
        """更新会话的总批注数"""
        if session_id not in self.current_status:
            self.current_status[session_id] = {}
        
        self.current_status[session_id]["total_annotations"] = total
        
        try:
            with get_db_session() as db:
                session = db.query(DocumentAnnotationSession).filter(
                    DocumentAnnotationSession.session_id == session_id
                ).first()
                if session:
                    session.total_annotations = total
        except Exception as e:
            logger.error(f"更新总批注数时出错: {str(e)}")
    
    def get_memory_status(self, session_id: str) -> Dict[str, Any]:
        """从内存获取状态"""
        return self.current_status.get(session_id, {})
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """获取会话状态"""
        try:
            # 直接从数据库获取状态，保证进度实时
            with get_db_session() as db:
                session = db.query(DocumentAnnotationSession).filter(
                    DocumentAnnotationSession.session_id == session_id
                ).first()

                if not session:
                    return {"success": False, "error": "会话不存在"}

                # 计算进度
                progress = 0
                if session.total_annotations > 0:
                    progress = (session.processed_annotations / session.total_annotations) * 100
                elif session.status == "completed":
                    progress = 100

                return {
                    "success": True,
                    "status": session.status,
                    "progress": progress,
                    "total_annotations": session.total_annotations,
                    "processed_annotations": session.processed_annotations,
                    "error_message": session.error_message,
                }
                
        except Exception as e:
            logger.error(f"获取会话状态时出错: {str(e)}")
            return {"success": False, "error": f"获取状态失败: {str(e)}"}
    
    def generate_output_file(self, session_id: str) -> Tuple[bool, str]:
        """生成输出文件"""
        try:
            with get_db_session() as db:
                session = db.query(DocumentAnnotationSession).filter(
                    DocumentAnnotationSession.session_id == session_id
                ).first()
                
                if not session:
                    return False, "会话不存在"
                
                if session.status != "completed":
                    return False, "处理尚未完成"
                
                if session.output_file_path and os.path.exists(session.output_file_path):
                    return True, session.output_file_path
                
                # 重新生成文件
                document_processor = DocumentProcessor(session_id)
                output_path = document_processor.generate_excel_output(session_id)
                session.output_file_path = output_path
                
                return True, output_path
                
        except Exception as e:
            logger.error(f"生成输出文件时出错: {str(e)}")
            return False, f"生成文件失败: {str(e)}"