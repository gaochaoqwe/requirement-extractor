"""
静态分析问题过滤服务
"""
import uuid
import time
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from ..models.models import StaticAnalysisSession, StaticAnalysisIssue
from ..database.database import get_db_session
from ..config.config import FILTER_CONFIG, OUTPUT_COLUMNS, BATCH_PROCESSING_CONFIG
from ..utils.logger import setup_session_logger
from .excel_processor import ExcelProcessor

class StaticAnalysisFilterService:
    def __init__(self, session_id: str = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.logger = setup_session_logger(self.session_id)
        self.excel_processor = ExcelProcessor(self.session_id)
        
        # 内存进度跟踪变量
        self.total_issues = 0
        self.filtered_issues = 0
        self.processed_issues = 0
        self.current_status = "pending"
        self.original_filename = ""
        self.output_filename = ""
        
    def process_uploaded_file(self, file_path: str, original_filename: str, filter_keywords: List[str] = None) -> Dict[str, Any]:
        """
        处理上传的静态分析Excel文件
        """
        try:
            self.logger.info(f"开始处理上传文件: {original_filename}")
            
            # 初始化进度跟踪
            self.original_filename = original_filename
            self.current_status = "processing"
            
            # 使用用户提供的关键字或默认关键字
            keywords = filter_keywords or FILTER_CONFIG["include_keywords"]
            
            # 处理Excel文件
            session_id, result = self.excel_processor.process_uploaded_file(file_path, original_filename, keywords)
            
            if result["success"]:
                # 更新进度信息
                self.total_issues = result.get("total_issues", 0)
                self.filtered_issues = 0
                self.processed_issues = 0
                
                self.logger.info(f"文件处理成功 - 会话ID: {self.session_id}")
                return {"success": True, "total_issues": result.get("total_issues", 0)}
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
        处理会话中的所有问题项 - 优化批量处理性能
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"开始处理会话: {self.session_id}")
            
            # 更新会话状态为处理中
            self._update_session_status("processing")
            
            # 获取待处理的问题项
            issues = self._get_pending_issues()
            if not issues:
                self.logger.warning("没有找到待处理的问题项")
                return {"success": False, "error": "没有找到待处理的问题项"}
            
            self.logger.info(f"找到{len(issues)}个待处理的问题项")
            
            # 批量处理问题项，提升性能
            PROCESSING_BATCH_SIZE = BATCH_PROCESSING_CONFIG["processing_batch_size"]  # 从配置获取批次大小
            filtered_count = 0
            processed_count = 0
            
            # 分批处理
            for batch_start in range(0, len(issues), PROCESSING_BATCH_SIZE):
                batch_end = min(batch_start + PROCESSING_BATCH_SIZE, len(issues))
                batch_issues = issues[batch_start:batch_end]
                current_batch = (batch_start // PROCESSING_BATCH_SIZE) + 1
                total_batches = (len(issues) + PROCESSING_BATCH_SIZE - 1) // PROCESSING_BATCH_SIZE
                
                self.logger.info(f"处理第{current_batch}/{total_batches}批次，{len(batch_issues)}个问题")
                
                # 批量分析问题
                batch_updates = []
                batch_filtered_count = 0
                
                for issue in batch_issues:
                    try:
                        # 应用过滤规则
                        is_filtered, filter_reason = self._apply_filter_rules(issue)
                        
                        # 收集更新数据
                        update_data = {
                            'id': issue.id,
                            'is_filtered': is_filtered,
                            'filter_reason': filter_reason
                        }
                        
                        # 生成格式化的位置信息
                        if issue.issue_file and issue.issue_line:
                            update_data['issue_location'] = f"{issue.issue_file}文件{issue.issue_line}行"
                        
                        # 生成问题总结
                        update_data['issue_summary'] = issue.issue_name
                        
                        batch_updates.append(update_data)
                        
                        if is_filtered:
                            batch_filtered_count += 1
                        
                    except Exception as e:
                        self.logger.error(f"分析问题项 {issue.id} 时出错: {str(e)}")
                        continue
                
                # 批量更新数据库
                if batch_updates:
                    self._batch_update_issues(batch_updates)
                
                # 更新进度
                batch_processed = len(batch_issues)
                processed_count += batch_processed
                filtered_count += batch_filtered_count
                
                # 更新内存进度
                self.processed_issues = processed_count
                self.filtered_issues = filtered_count
                
                self.logger.info(f"批次{current_batch}处理完成，已处理{processed_count}/{len(issues)}个问题")
            
            # 生成输出文件
            self.logger.info("开始自动生成Excel输出文件")
            output_result = self.generate_output_file()
            
            if output_result["success"]:
                self.output_filename = output_result["filename"]
                self.logger.info(f"Excel文件自动生成成功: {self.output_filename}")
            
            # 更新最终状态
            execution_time = time.time() - start_time
            message = f"处理完成 - 总计: {processed_count}, 过滤: {filtered_count}, 保留: {processed_count - filtered_count}"
            
            self._update_session_status("completed")
            self.current_status = "completed"
            
            self.logger.info(f"会话处理完成 - {message}, 耗时: {execution_time:.2f}秒")
            
            return {
                "success": True,
                "message": message,
                "total_issues": processed_count,
                "filtered_issues": filtered_count,
                "output_filename": self.output_filename
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"处理会话时出错: {str(e)}"
            self.logger.error(f"{error_msg}, 耗时: {execution_time:.2f}秒")
            
            self._update_session_status("error")
            self.current_status = "error"
            
            return {"success": False, "error": error_msg}
    
    def _apply_filter_rules(self, issue: StaticAnalysisIssue) -> Tuple[bool, str]:
        """
        应用过滤规则
        
        Returns:
            tuple: (是否被过滤, 过滤原因)
        """
        issue_name = issue.issue_name or ""
        
        # 1. 检查排除关键字
        for keyword in FILTER_CONFIG["exclude_keywords"]:
            if keyword in issue_name:
                return True, f"包含排除关键字: {keyword}"
        
        # 2. 检查名称长度
        if len(issue_name) < FILTER_CONFIG["min_name_length"]:
            return True, f"问题名称过短: {len(issue_name)}字符"
        
        # 3. 检查是否包含有效关键字
        has_valid_keyword = False
        for keyword in FILTER_CONFIG["include_keywords"]:
            if keyword in issue_name:
                has_valid_keyword = True
                break
        
        if not has_valid_keyword:
            return True, "不包含有效关键字"
        
        return False, ""  # 不过滤
    
    def _get_pending_issues(self) -> List[StaticAnalysisIssue]:
        """获取待处理的问题项"""
        db = get_db_session()
        try:
            return db.query(StaticAnalysisIssue).filter(
                StaticAnalysisIssue.session_id == self.session_id
            ).all()
        finally:
            db.close()
    
    def _update_session_status(self, status: str):
        """更新会话状态"""
        db = get_db_session()
        try:
            session = db.query(StaticAnalysisSession).filter(
                StaticAnalysisSession.session_id == self.session_id
            ).first()
            
            if session:
                session.status = status
                session.filtered_issues = self.filtered_issues
                db.commit()
        finally:
            db.close()
    
    def _batch_update_issues(self, updates: List[Dict]) -> None:
        """批量更新问题项状态 - 提升性能"""
        if not updates:
            return
            
        db = get_db_session()
        try:
            # 使用SQLAlchemy的批量更新功能
            for update_data in updates:
                issue_id = update_data.pop('id')
                db.query(StaticAnalysisIssue).filter(
                    StaticAnalysisIssue.id == issue_id
                ).update(update_data, synchronize_session=False)
            
            db.commit()
            
        except Exception as e:
            self.logger.error(f"批量更新问题状态时出错: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()
    
    def _update_issue_status(self, issue_id: int, is_filtered: bool, filter_reason: str):
        """更新问题项状态 - 保留原方法以便兼容"""
        db = get_db_session()
        try:
            issue = db.query(StaticAnalysisIssue).filter(
                StaticAnalysisIssue.id == issue_id
            ).first()
            
            if issue:
                issue.is_filtered = is_filtered
                issue.filter_reason = filter_reason
                
                # 生成格式化的位置信息
                if issue.issue_file and issue.issue_line:
                    issue.issue_location = f"{issue.issue_file}文件{issue.issue_line}行"
                
                # 生成问题总结（简化版）
                issue.issue_summary = issue.issue_name
                
                db.commit()
        finally:
            db.close()
    
    def generate_output_file(self, rule_type: str = 'all', content_type: str = 'all') -> Dict[str, Any]:
        """
        生成输出Excel文件
        
        Args:
            rule_type: 'all', 'gjb', 'cwe' - 选择生成哪种规则的问题单（普通服务不支持过滤，忽略此参数）
            content_type: 'all', 'accurate', 'uncertain' - 选择包含哪类问题（普通服务不支持过滤，忽略此参数）
        """
        try:
            self.logger.info(f"开始生成输出文件 - 规则类型:{rule_type}, 内容类型:{content_type}")
            
            # 注意：普通服务不支持按规则类型和内容类型过滤，参数仅用于API兼容性
            # 生成输出文件
            result = self.excel_processor.generate_filtered_excel(self.session_id)
            
            if result["success"]:
                self.logger.info(f"输出文件生成成功: {result['output_path']}")
                return {
                    "success": True,
                    "filename": Path(result["output_path"]).name,
                    "output_path": result["output_path"]
                }
            else:
                return result
                
        except Exception as e:
            error_msg = f"生成输出文件时出错: {str(e)}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def get_memory_status(self) -> Dict[str, Any]:
        """
        获取基于内存变量的处理状态 - 快速无阻塞
        """
        try:
            # 计算进度百分比
            progress_percentage = 0
            if self.total_issues > 0:
                progress_percentage = (self.processed_issues / self.total_issues) * 100
            
            # 判断整体状态
            if self.processed_issues >= self.total_issues and self.total_issues > 0:
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
                "total_issues": self.total_issues,
                "processed_issues": self.processed_issues,
                "filtered_issues": self.filtered_issues,
                "retained_issues": self.processed_issues - self.filtered_issues,
                "error_message": None,
                "output_filename": self.output_filename
            }
            
        except Exception as e:
            error_msg = f"获取内存状态时出错: {str(e)}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg} 