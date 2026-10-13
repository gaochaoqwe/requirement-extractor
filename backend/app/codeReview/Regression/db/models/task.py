"""
分析任务模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from ..database import Base


class AnalysisTask(Base):
    """回归测试代码审查任务模型"""
    __tablename__ = 'code_review_tasks'
    
    id = Column(String(36), primary_key=True, index=True)  # 使用UUID作为主键
    task_name = Column(String(255), nullable=True)
    task_description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String(50), default='pending')  # pending, processing, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    total_files = Column(Integer, default=0)
    processed_files = Column(Integer, default=0)
    total_problems = Column(Integer, default=0)
    
    # 新增字段，支持回归测试
    old_file_id = Column(Integer, ForeignKey("code_review_files.id"), nullable=True)
    new_file_id = Column(Integer, ForeignKey("code_review_files.id"), nullable=True)
    report_file_id = Column(Integer, ForeignKey("code_review_files.id"), nullable=True)
    result_path = Column(String(255), nullable=True)  # 结果文件路径
    error_message = Column(Text, nullable=True)  # 错误信息
    
    # 兼容旧版本
    code_file_id = Column(Integer, nullable=True)  # 关联的代码文件ID（旧版本使用）
    
    # 关联关系 - 使用显式关系定义避免多外键路径问题
    files = relationship("AnalysisFile", 
                       primaryjoin="AnalysisFile.task_id==AnalysisTask.id",
                       back_populates="task", 
                       cascade="all, delete-orphan")
    
    # 明确指定外键关系
    old_file = relationship("AnalysisFile", 
                          foreign_keys=[old_file_id], 
                          back_populates="old_tasks",
                          post_update=True)
    new_file = relationship("AnalysisFile", 
                          foreign_keys=[new_file_id], 
                          back_populates="new_tasks",
                          post_update=True)
    report_file = relationship("AnalysisFile", 
                             foreign_keys=[report_file_id], 
                             back_populates="report_tasks",
                             post_update=True)
    
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
            'old_file_id': self.old_file_id,
            'new_file_id': self.new_file_id,
            'report_file_id': self.report_file_id,
            'result_path': self.result_path,
            'error_message': self.error_message,
            'code_file_id': self.code_file_id,  # 兼容旧版本
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
