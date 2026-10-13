"""
文件记录仓库
负责文件数据的CRUD操作
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from ..models.file import AnalysisFile
import os

# 导入统一的日志系统
from ...utils.logger import log_debug, log_error

class FileRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_file(self, file_data: Dict[str, Any]) -> AnalysisFile:
        """创建文件记录"""
        file_record = AnalysisFile(**file_data)
        self.db.add(file_record)
        self.db.flush()
        return file_record

    def get_file(self, file_id: int) -> Optional[AnalysisFile]:
        """根据ID获取文件"""
        return self.db.query(AnalysisFile).filter(AnalysisFile.id == file_id).first()

    def get_file_by_name(self, filename: str) -> Optional[AnalysisFile]:
        """根据文件名获取文件"""
        return self.db.query(AnalysisFile).filter(AnalysisFile.filename == filename).first()

    def get_all_files(self) -> List[AnalysisFile]:
        """获取所有文件"""
        return self.db.query(AnalysisFile).all()

    def update_file(self, file_id: int, update_data: Dict[str, Any]) -> Optional[AnalysisFile]:
        """更新文件记录"""
        file_record = self.get_file(file_id)
        if file_record:
            for key, value in update_data.items():
                if hasattr(file_record, key):
                    setattr(file_record, key, value)
            self.db.flush()
        return file_record

    def delete_file(self, file_id: int) -> bool:
        """删除文件记录"""
        try:
            file_record = self.get_file(file_id)
            if file_record:
                # 删除解压文件夹
                if file_record.extract_path and os.path.exists(file_record.extract_path):
                    import shutil
                    shutil.rmtree(file_record.extract_path)
                    
                # 删除上传的文件
                if file_record.file_path and os.path.exists(file_record.file_path):
                    os.remove(file_record.file_path)
                
                # 删除数据库记录
                self.db.delete(file_record)
                self.db.flush()
                return True
            return False
        except Exception as e:
            log_error(f"删除文件时出错", "file_repo", e)
            return False

    def get_files_by_status(self, status: str) -> List[AnalysisFile]:
        """根据状态获取文件"""
        return self.db.query(AnalysisFile).filter(AnalysisFile.status == status).all()
    
    def get_files_by_task(self, task_id: int) -> List[AnalysisFile]:
        """根据任务ID获取文件"""
        return self.db.query(AnalysisFile).filter(AnalysisFile.task_id == task_id).all()
