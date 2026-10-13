"""
分析任务模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from ..database import Base


class AnalysisTask(Base):
    """分析任务模型"""
    __tablename__ = 'regression_test_tasks'
    
    id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String(255), nullable=False)
    task_description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    status = Column(String(50), default='pending')  # pending, processing, completed, failed, cancelled, paused
    progress = Column(Integer, default=0)  # 0-100
    total_files = Column(Integer, default=0)
    processed_files = Column(Integer, default=0)
    total_problems = Column(Integer, default=0)
    code_file_id = Column(Integer, nullable=True)  # 关联的代码文件ID
    analysis_type = Column(String(50), default='code_review')  # code_review, feature_review
    tester_name = Column(String(100), nullable=True)  # 测试人员姓名（从登录session获取）

    # 标记问题统计（后续管理员数据面板使用）
    has_marked_problems = Column(Boolean, default=False)      # 是否存在标记问题
    marked_problem_count = Column(Integer, default=0)         # 标记问题数量
    marked_problems_exported = Column(Boolean, default=False) # 是否导出过标记问题
    
    # 任务恢复相关字段
    paused_at = Column(DateTime, nullable=True)  # 暂停时间
    execution_context = Column(Text, nullable=True)  # 执行上下文（JSON格式，用于恢复）
    
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
            'analysis_type': self.analysis_type,
            'tester_name': self.tester_name,
            'has_marked_problems': self.has_marked_problems,
            'marked_problem_count': self.marked_problem_count,
            'marked_problems_exported': self.marked_problems_exported,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'paused_at': self.paused_at.isoformat() if self.paused_at else None,
            'execution_context': self.execution_context
        }
