"""
分析任务模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..base import Base


class AnalysisTask(Base):
    """分析任务模型"""
    __tablename__ = 'nm_analysis_tasks'
    
    id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String(255), nullable=False)
    task_description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String(50), default='pending')  # pending, processing, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    total_files = Column(Integer, default=0)
    processed_files = Column(Integer, default=0)
    total_problems = Column(Integer, default=0)
    code_file_id = Column(Integer, nullable=True)  # 关联的代码文件ID
    domain = Column(String(50), nullable=False, default='normalModeC')  # normalModeC / normalModeFpga
    
    # 关联关系
    files = relationship("AnalysisFile", back_populates="task", cascade="all, delete-orphan")
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'task_name': self.task_name,
            'task_description': self.task_description,
            'status': self.status,
            'progress': self.progress,
            'total_files': self.total_files,
            'processed_files': self.processed_files,
            'total_problems': self.total_problems,
            'code_file_id': self.code_file_id,
            'domain': self.domain,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
