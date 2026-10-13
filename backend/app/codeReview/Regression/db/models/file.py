"""
分析文件模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from .task import AnalysisTask
from ..database import Base

class AnalysisFile(Base):
    """分析文件模型"""
    __tablename__ = 'code_review_files'
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('code_review_tasks.id', ondelete='CASCADE'), nullable=True)  # 允许为空，因为上传时还没有任务
    file_path = Column(String(512), nullable=False)  # ZIP文件路径
    extract_path = Column(String(512), nullable=True)  # 解压目录路径
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=True)  # 文件大小(字节)
    file_type = Column(String(50), nullable=True)  # 文件类型(zip)
    upload_time = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default='uploaded')  # uploaded, processing, completed, failed
    functions_count = Column(Integer, default=0)  # 函数数量
    file_count = Column(Integer, default=0)  # 包含的源文件数量
    
    # 关联关系
    task = relationship("AnalysisTask", back_populates="files", foreign_keys=[task_id])
    functions = relationship("AnalysisFunction", back_populates="file", cascade="all, delete-orphan")
    
    # 明确指定 backref 关系
    old_tasks = relationship("AnalysisTask", foreign_keys="AnalysisTask.old_file_id", back_populates="old_file")
    new_tasks = relationship("AnalysisTask", foreign_keys="AnalysisTask.new_file_id", back_populates="new_file")
    report_tasks = relationship("AnalysisTask", foreign_keys="AnalysisTask.report_file_id", back_populates="report_file")
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'file_path': self.file_path,
            'extract_path': self.extract_path,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'status': self.status,
            'functions_count': self.functions_count,
            'file_count': self.file_count,
            'upload_time': self.upload_time.isoformat() if self.upload_time else None
        }
