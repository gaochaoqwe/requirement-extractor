"""
问题过滤规则模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from ..database import Base


class ProblemFilterRule(Base):
    """问题过滤规则模型"""
    __tablename__ = 'code_review_problem_filters'
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('code_review_tasks.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # 过滤规则名称
    filter_name = Column(String(255), nullable=True)  # 用户自定义的规则名称（可选）
    
    # 过滤关键词（JSON数组）
    # 例如: ["可能", "数组"] 表示问题原因必须同时包含这两个关键词才会被过滤（AND逻辑）
    # 例如: ["硬编码", "魔法数字"] 表示问题原因包含任一关键词就会被过滤（OR逻辑）
    keywords = Column(JSON, nullable=False)
    
    # 逻辑类型：'AND' 或 'OR'
    logic_type = Column(String(10), default='AND', nullable=False)
    
    # 关联的全局模板ID（可选）
    template_id = Column(Integer, nullable=True)
    
    # 是否启用此规则
    is_enabled = Column(Boolean, default=True, nullable=False)
    
    # 创建和更新时间
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'filter_name': self.filter_name,
            'keywords': self.keywords,
            'logic_type': self.logic_type,
            'template_id': self.template_id,
            'is_enabled': self.is_enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

