"""
用户标记的问题模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from ..database import Base


class MarkedProblem(Base):
    """用户标记的问题模型"""
    __tablename__ = 'code_review_marked_problems'
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('code_review_tasks.id', ondelete='CASCADE'), nullable=False, index=True)
    analysis_type = Column(String(50), nullable=False, index=True)  # function, chain, feature
    
    # 问题唯一标识（根据问题内容生成的key）
    problem_key = Column(String(512), nullable=False)
    
    # 完整的问题数据（JSON格式存储）
    problem_data = Column(JSON, nullable=False)
    
    # 标记信息
    marked_by = Column(String(255), nullable=True)  # 标记人（可选）
    marked_at = Column(DateTime, default=datetime.now, nullable=False)
    
    # 创建联合唯一索引：同一任务下，同一类型的同一问题key只能标记一次
    __table_args__ = (
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'},
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'analysis_type': self.analysis_type,
            'problem_key': self.problem_key,
            'problem_data': self.problem_data,
            'marked_by': self.marked_by,
            'marked_at': self.marked_at.isoformat() if self.marked_at else None
        }

