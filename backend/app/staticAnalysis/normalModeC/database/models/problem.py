"""
分析问题模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from ..base import Base

class AnalysisProblem(Base):
    """分析问题模型"""
    __tablename__ = 'nm_analysis_problems'
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('nm_analysis_tasks.id', ondelete='CASCADE'), nullable=False)
    file_id = Column(Integer, ForeignKey('nm_analysis_files.id', ondelete='CASCADE'), nullable=False)
    function_id = Column(Integer, ForeignKey('nm_analysis_functions.id', ondelete='CASCADE'), nullable=False)
    
    # 问题详情
    file_name = Column(String(255), nullable=False)
    source_code = Column(Text, nullable=False)
    
    # 保留必要的字段
    violation_rules = Column(String(255), nullable=True)  # 违反的规则
    issue_level = Column(String(50), nullable=True)  # 问题等级：建议改进、一般问题、重要问题
    issue_name = Column(String(255), nullable=True)  # 问题名称
    issue_location = Column(String(255), nullable=True)  # 问题位置
    description_requirement = Column(Text, nullable=True)  # 需求描述
    description_issue = Column(Text, nullable=True)  # 问题描述
    description_location = Column(Text, nullable=True)  # 问题定位
    description_impact = Column(Text, nullable=True)  # 影响分析
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联关系
    function = relationship("AnalysisFunction", back_populates="problems")
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'file_id': self.file_id,
            'function_id': self.function_id,
            'file_name': self.file_name,
            'source_code': self.source_code,
            
            # 保留必要的字段
            'violation_rules': self.violation_rules,
            'issue_level': self.issue_level,
            'issue_name': self.issue_name,
            'issue_location': self.issue_location,
            'description_requirement': self.description_requirement,
            'description_issue': self.description_issue,
            'description_location': self.description_location,
            'description_impact': self.description_impact,
            
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
