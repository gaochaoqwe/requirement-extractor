#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标准化文档管理器
处理标准化文档的等待、检查和回退逻辑
"""

import os
import json
import time
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path

try:
    from .logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    # 简单的日志回退
    def log_info(msg, module="standardization_manager"): print(f"[INFO] {msg}")
    def log_error(msg, module="standardization_manager"): print(f"[ERROR] {msg}")
    def log_warning(msg, module="standardization_manager"): print(f"[WARNING] {msg}")
    def log_debug(msg, module="standardization_manager"): print(f"[DEBUG] {msg}")


class StandardizationManager:
    """标准化文档管理器"""
    
    def __init__(self, max_wait_time: int = 180):
        """
        初始化标准化管理器
        
        Args:
            max_wait_time: 最大等待时间（秒），默认180秒（3分钟）
        """
        self.max_wait_time = max_wait_time
    
    def get_standardized_document_path(self, session_id: str, original_doc_path: str = None) -> Optional[str]:
        """
        获取标准化文档路径（同步版本）
        
        Args:
            session_id: 会话ID
            original_doc_path: 原始文档路径（可选）
            
        Returns:
            标准化文档路径，如果不存在则返回None
        """
        try:
            # 修复路径指向backend目录下的uploads
            backend_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
            session_dir = backend_dir / "uploads" / "dynamic" / "configuration" / session_id
            
            # 查找标准化文档的多种可能路径
            possible_patterns = [
                "standardized_requirement_*.docx",
                "standardized_*.docx",
                "*_standardized.docx"
            ]
            
            for pattern in possible_patterns:
                standardized_files = list(session_dir.glob(pattern))
                if standardized_files:
                    standardized_path = str(standardized_files[0])
                    log_debug(f"找到标准化文档: {standardized_path}", "standardization_manager")
                    return standardized_path
            
            # 如果提供了原始文档路径，尝试构造标准化路径
            if original_doc_path:
                original_path = Path(original_doc_path)
                standardized_path = original_path.parent / f"standardized_{original_path.name}"
                if standardized_path.exists():
                    log_debug(f"找到标准化文档: {standardized_path}", "standardization_manager")
                    return str(standardized_path)
            
            return None
            
        except Exception as e:
            log_error(f"查找标准化文档时出错: {e}", "standardization_manager")
            return None
    
    async def wait_for_standardized_document(self, session_id: str, original_doc_path: str = None) -> Optional[str]:
        """
        等待标准化文档完成（异步版本）
        
        Args:
            session_id: 会话ID  
            original_doc_path: 原始文档路径（可选）
            
        Returns:
            标准化文档路径，如果超时或失败则返回None
        """
        log_info(f"开始等待标准化文档完成，会话ID: {session_id}", "standardization_manager")
        
        start_time = time.time()
        check_interval = 2  # 每2秒检查一次
        
        while time.time() - start_time < self.max_wait_time:
            # 1. 检查是否已有标准化文档
            standardized_path = self.get_standardized_document_path(session_id, original_doc_path)
            if standardized_path:
                log_info(f"标准化文档已完成: {standardized_path}", "standardization_manager")
                return standardized_path
            
            # 2. 检查标准化状态
            status = self._get_standardization_status(session_id)
            if status:
                if status.get('status') == 'completed':
                    # 状态显示完成，再次检查文件
                    standardized_path = status.get('standardized_path')
                    if standardized_path and os.path.exists(standardized_path):
                        log_info(f"标准化文档完成: {standardized_path}", "standardization_manager")
                        return standardized_path
                elif status.get('status') == 'failed':
                    log_warning(f"标准化失败: {status.get('error', 'Unknown error')}", "standardization_manager")
                    return None
            
            # 3. 等待一段时间后重试
            elapsed = time.time() - start_time
            log_debug(f"等待标准化文档... ({elapsed:.1f}s/{self.max_wait_time}s)", "standardization_manager")
            await asyncio.sleep(check_interval)
        
        # 超时
        log_warning(f"等待标准化文档超时 ({self.max_wait_time}s)，会话ID: {session_id}", "standardization_manager")
        return None
    
    def _get_standardization_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取标准化状态"""
        try:
            # 修复路径指向backend目录下的uploads
            backend_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
            session_dir = backend_dir / "uploads" / "dynamic" / "configuration" / session_id
            status_file = session_dir / "standardization_status.json"
            
            if status_file.exists():
                with open(status_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            
            return None
            
        except Exception as e:
            log_error(f"读取标准化状态失败: {e}", "standardization_manager")
            return None
    
    def get_document_for_processing(self, session_id: str, original_doc_path: str, 
                                   wait_for_standardization: bool = True) -> str:
        """
        获取用于处理的文档路径（智能选择标准化或原始文档）
        
        Args:
            session_id: 会话ID
            original_doc_path: 原始文档路径
            wait_for_standardization: 是否等待标准化完成
            
        Returns:
            用于处理的文档路径
        """
        try:
            # 1. 首先检查是否已有标准化文档
            standardized_path = self.get_standardized_document_path(session_id, original_doc_path)
            if standardized_path:
                log_info(f"使用已完成的标准化文档: {standardized_path}", "standardization_manager")
                return standardized_path
            
            # 2. 如果需要等待标准化
            if wait_for_standardization:
                log_info("标准化文档尚未完成，检查是否正在进行中...", "standardization_manager")
                
                status = self._get_standardization_status(session_id)
                if status and status.get('status') == 'processing':
                    log_info("标准化正在进行中，使用原始文档继续处理", "standardization_manager")
                else:
                    log_info("未检测到标准化进程，使用原始文档", "standardization_manager")
            
            # 3. 使用原始文档
            log_info(f"使用原始文档: {original_doc_path}", "standardization_manager")
            return original_doc_path
            
        except Exception as e:
            log_error(f"获取处理文档时出错: {e}", "standardization_manager")
            return original_doc_path
    
    async def get_document_for_processing_async(self, session_id: str, original_doc_path: str, 
                                              wait_timeout: int = 180) -> str:
        """
        异步获取用于处理的文档路径（带智能等待）
        
        Args:
            session_id: 会话ID
            original_doc_path: 原始文档路径
            wait_timeout: 等待超时时间（秒），默认180秒（3分钟）
            
        Returns:
            用于处理的文档路径
        """
        try:
            # 1. 首先检查是否已有标准化文档
            standardized_path = self.get_standardized_document_path(session_id, original_doc_path)
            if standardized_path:
                log_info(f"使用已完成的标准化文档: {standardized_path}", "standardization_manager")
                return standardized_path
            
            # 2. 检查是否正在标准化
            status = self._get_standardization_status(session_id)
            if status and status.get('status') == 'processing':
                log_info(f"标准化正在进行中，等待最多 {wait_timeout} 秒（{wait_timeout//60}分钟）...", "standardization_manager")
                
                # 等待标准化完成（但限制时间）
                original_max_wait = self.max_wait_time
                self.max_wait_time = wait_timeout
                
                try:
                    standardized_path = await self.wait_for_standardized_document(session_id, original_doc_path)
                    if standardized_path:
                        log_info(f"等待成功，使用标准化文档: {standardized_path}", "standardization_manager")
                        return standardized_path
                finally:
                    self.max_wait_time = original_max_wait
            
            # 3. 使用原始文档
            log_info(f"使用原始文档: {original_doc_path}", "standardization_manager")
            return original_doc_path
            
        except Exception as e:
            log_error(f"异步获取处理文档时出错: {e}", "standardization_manager")
            return original_doc_path
    
    def is_standardization_in_progress(self, session_id: str) -> bool:
        """检查标准化是否正在进行中"""
        try:
            status = self._get_standardization_status(session_id)
            return status and status.get('status') == 'processing'
        except Exception:
            return False
    
    def get_standardization_progress_info(self, session_id: str) -> Dict[str, Any]:
        """获取标准化进度信息"""
        try:
            status = self._get_standardization_status(session_id)
            if not status:
                return {
                    "status": "unknown",
                    "message": "未找到标准化状态信息",
                    "has_standardized_doc": self.get_standardized_document_path(session_id) is not None
                }
            
            return {
                "status": status.get('status', 'unknown'),
                "message": self._get_status_message(status),
                "has_standardized_doc": self.get_standardized_document_path(session_id) is not None,
                "completion_time": status.get('completion_time'),
                "error": status.get('error')
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"获取状态失败: {e}",
                "has_standardized_doc": False
            }
    
    def _get_status_message(self, status: Dict[str, Any]) -> str:
        """获取状态描述信息"""
        status_value = status.get('status')
        
        if status_value == 'processing':
            return "标准化正在进行中..."
        elif status_value == 'completed':
            return "标准化已完成"
        elif status_value == 'failed':
            error = status.get('error', 'Unknown error')
            return f"标准化失败: {error}"
        else:
            return "状态未知"


# 全局实例
_standardization_manager = None

def get_standardization_manager() -> StandardizationManager:
    """获取标准化管理器实例（单例模式）"""
    global _standardization_manager
    if _standardization_manager is None:
        _standardization_manager = StandardizationManager()
    return _standardization_manager 