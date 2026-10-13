#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
软件信息服务
管理软件信息的提取、存储和获取

功能：
1. 从需求规格说明文档提取软件信息
2. 存储和管理提取的软件信息
3. 提供API接口访问软件信息
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import uuid

try:
    from ....utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from .....utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

from .software_info_extractor import extract_software_info_from_document


class SoftwareInfoService:
    """软件信息服务"""
    
    def __init__(self, upload_base_dir: str = None):
        # 修复路径指向backend目录下的uploads
        if upload_base_dir is None:
            backend_dir = Path(__file__).resolve().parent.parent.parent.parent.parent.parent.parent
            upload_base_dir = str(backend_dir / "uploads" / "dynamic" / "configuration")
        self.upload_base_dir = Path(upload_base_dir)
        self.upload_base_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_software_info_from_session(self, session_id: str) -> Dict[str, Any]:
        """
        从指定会话的需求文档中提取软件信息
        
        Args:
            session_id: 会话ID
            
        Returns:
            软件信息提取结果
        """
        try:
            log_info(f"开始从会话 {session_id} 提取软件信息", "software_info_service")
            
            # 检查会话目录是否存在
            session_dir = self.upload_base_dir / session_id
            if not session_dir.exists():
                return self._create_error_result("会话不存在")
            
            # 查找需求文档 - 优先使用标准化文档
            standardized_files = list(session_dir.glob("standardized_requirement_*"))
            requirement_files = list(session_dir.glob("requirement_*"))
            
            if standardized_files:
                requirement_file_path = standardized_files[0]  # 优先使用标准化文档
                log_info(f"找到标准化需求文档: {requirement_file_path}", "software_info_service")
            elif requirement_files:
                requirement_file_path = requirement_files[0]  # 回退到原始文档
                log_info(f"找到原始需求文档: {requirement_file_path}", "software_info_service")
            else:
                return self._create_error_result("未找到需求文档")
            
            log_info(f"使用文档: {requirement_file_path}", "software_info_service")
            
            # 提取软件信息
            print(f"🔍 [SoftwareInfoService] 开始提取软件信息，文档路径: {requirement_file_path}")
            extraction_result = extract_software_info_from_document(str(requirement_file_path), debug_mode=True)
            print(f"🔍 [SoftwareInfoService] 提取结果: {extraction_result}")
            
            # 保存提取结果
            if extraction_result['found']:
                self._save_software_info(session_id, extraction_result['data'])
                log_info(f"软件信息提取成功: {extraction_result['data']}", "software_info_service")
                print(f"✅ [SoftwareInfoService] 最终软件信息: {extraction_result['data']}")
            else:
                log_warning(f"软件信息提取失败: {extraction_result['message']}", "software_info_service")
                print(f"❌ [SoftwareInfoService] 提取失败: {extraction_result['message']}")
            
            return {
                'status': 'success' if extraction_result['found'] else 'warning',
                'message': extraction_result['message'],
                'session_id': session_id,
                'software_info': extraction_result['data'],
                'extraction_details': {
                    'found_table': extraction_result['found'],
                    'table_index': extraction_result.get('table_index'),
                    'document_path': str(requirement_file_path)
                }
            }
            
        except Exception as e:
            log_error(f"提取软件信息时发生错误: {str(e)}", "software_info_service")
            return self._create_error_result(f"提取失败: {str(e)}")
    
    def get_software_info(self, session_id: str) -> Dict[str, Any]:
        """
        获取指定会话的软件信息
        
        Args:
            session_id: 会话ID
            
        Returns:
            软件信息
        """
        try:
            session_dir = self.upload_base_dir / session_id
            software_info_file = session_dir / "software_info.json"
            
            if not software_info_file.exists():
                return self._create_empty_software_info("软件信息未提取")
            
            with open(software_info_file, 'r', encoding='utf-8') as f:
                software_info = json.load(f)
            
            return {
                'status': 'success',
                'message': '获取软件信息成功',
                'session_id': session_id,
                'software_info': software_info
            }
            
        except Exception as e:
            log_error(f"获取软件信息失败: {str(e)}", "software_info_service")
            return self._create_error_result(f"获取失败: {str(e)}")
    
    def update_software_info(self, session_id: str, software_info: Dict[str, str]) -> Dict[str, Any]:
        """
        更新软件信息
        
        Args:
            session_id: 会话ID
            software_info: 软件信息字典
            
        Returns:
            更新结果
        """
        try:
            log_info(f"更新会话 {session_id} 的软件信息", "software_info_service")
            
            # 验证软件信息格式
            required_fields = ['software_name', 'software_version', 'software_id']
            for field in required_fields:
                if field not in software_info:
                    software_info[field] = ''
            
            # 保存更新的信息
            self._save_software_info(session_id, software_info)
            
            return {
                'status': 'success',
                'message': '软件信息更新成功',
                'session_id': session_id,
                'software_info': software_info
            }
            
        except Exception as e:
            log_error(f"更新软件信息失败: {str(e)}", "software_info_service")
            return self._create_error_result(f"更新失败: {str(e)}")
    
    def _save_software_info(self, session_id: str, software_info: Dict[str, str]) -> None:
        """保存软件信息到文件"""
        session_dir = self.upload_base_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        software_info_file = session_dir / "software_info.json"
        
        # 添加元数据
        data_to_save = {
            **software_info,
            'extraction_timestamp': str(Path().stat().st_mtime) if Path().exists() else None,
            'session_id': session_id
        }
        
        with open(software_info_file, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)
        
        log_info(f"软件信息已保存到: {software_info_file}", "software_info_service")
    
    def _create_error_result(self, message: str) -> Dict[str, Any]:
        """创建错误结果"""
        return {
            'status': 'error',
            'message': message,
            'software_info': self._create_empty_software_info()['software_info']
        }
    
    def _create_empty_software_info(self, message: str = "未找到软件信息") -> Dict[str, Any]:
        """创建空的软件信息"""
        return {
            'status': 'empty',
            'message': message,
            'software_info': {
                'software_name': '',
                'software_version': '',
                'software_id': ''
            }
        }
    
    def list_sessions_with_software_info(self) -> Dict[str, Any]:
        """列出所有包含软件信息的会话"""
        try:
            sessions_info = []
            
            for session_dir in self.upload_base_dir.iterdir():
                if session_dir.is_dir():
                    software_info_file = session_dir / "software_info.json"
                    if software_info_file.exists():
                        try:
                            with open(software_info_file, 'r', encoding='utf-8') as f:
                                software_info = json.load(f)
                            sessions_info.append({
                                'session_id': session_dir.name,
                                'software_info': software_info
                            })
                        except Exception as e:
                            log_warning(f"读取会话 {session_dir.name} 的软件信息失败: {str(e)}", "software_info_service")
            
            return {
                'status': 'success',
                'message': f'找到 {len(sessions_info)} 个包含软件信息的会话',
                'sessions': sessions_info,
                'total_count': len(sessions_info)
            }
            
        except Exception as e:
            log_error(f"列出会话信息失败: {str(e)}", "software_info_service")
            return self._create_error_result(f"列出失败: {str(e)}")


# 创建全局服务实例
software_info_service = SoftwareInfoService()


def get_software_info_service() -> SoftwareInfoService:
    """获取软件信息服务实例"""
    return software_info_service 