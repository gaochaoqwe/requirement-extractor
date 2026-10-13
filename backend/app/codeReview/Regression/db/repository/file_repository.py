"""
文件仓库模块
"""
from sqlalchemy.orm import Session
from ..models.file import AnalysisFile
from typing import Dict, Any, Optional, List

class FileRepository:
    """
    文件仓库类
    """
    def __init__(self, db: Session):
        self.db = db
    
    def create_file(self, file_data: Dict[str, Any]) -> AnalysisFile:
        """
        创建新文件记录
        
        Args:
            file_data: 文件数据字典
        
        Returns:
            创建的文件对象
        """
        file = AnalysisFile(**file_data)
        self.db.add(file)
        self.db.commit()
        self.db.refresh(file)
        return file
    
    def get_file_by_id(self, file_id: int) -> Optional[AnalysisFile]:
        """
        根据ID获取文件
        
        Args:
            file_id: 文件ID
        
        Returns:
            文件对象，如果不存在则返回None
        """
        return self.db.query(AnalysisFile).filter(AnalysisFile.id == file_id).first()
    
    def get_files_by_type(self, file_type: str, skip: int = 0, limit: int = 100) -> List[AnalysisFile]:
        """
        根据文件类型获取文件列表
        
        Args:
            file_type: 文件类型 ('old', 'new', 'report')
            skip: 跳过数量
            limit: 限制数量
            
        Returns:
            文件对象列表
        """
        return self.db.query(AnalysisFile).filter(AnalysisFile.file_type == file_type).offset(skip).limit(limit).all()
    
    def update_file(self, file_id: int, update_data: Dict[str, Any]) -> Optional[AnalysisFile]:
        """
        更新文件
        
        Args:
            file_id: 文件ID
            update_data: 更新数据字典
        
        Returns:
            更新后的文件对象，如果文件不存在则返回None
        """
        file = self.get_file_by_id(file_id)
        if not file:
            return None
        
        for key, value in update_data.items():
            setattr(file, key, value)
        
        self.db.commit()
        self.db.refresh(file)
        return file
    
    def delete_file(self, file_id: int) -> bool:
        """
        删除文件
        
        Args:
            file_id: 文件ID
        
        Returns:
            是否成功删除
        """
        file = self.get_file_by_id(file_id)
        if not file:
            return False
        
        self.db.delete(file)
        self.db.commit()
        return True
    
    def list_files(self, skip: int = 0, limit: int = 100) -> List[AnalysisFile]:
        """
        列出文件
        
        Args:
            skip: 跳过数量
            limit: 限制数量
        
        Returns:
            文件列表
        """
        return self.db.query(AnalysisFile).order_by(AnalysisFile.upload_time.desc()).offset(skip).limit(limit).all() 