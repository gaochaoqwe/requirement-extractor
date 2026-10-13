"""
审查结果模型
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

# 尝试相对导入，失败则使用绝对导入
try:
    from ..database import Base
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from database import Base


class ReviewResult(Base):
    """审查结果模型"""
    __tablename__ = 'review_results'
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('review_sessions.id', ondelete='CASCADE'), nullable=False)
    doc_type = Column(String(32), nullable=False)  # taskBook, requirementSpec
    doc_name = Column(String(128), nullable=True)
    requirement_content = Column(Text, nullable=True)
    violation_rules = Column(String(256), nullable=True)
    issue_level = Column(String(32), nullable=False, default='一般问题')  # 新增：问题等级字段
    issue_name = Column(String(256), nullable=True)
    issue_location = Column(String(256), nullable=True)
    description_requirement = Column(Text, nullable=True)
    description_issue = Column(Text, nullable=True)
    description_location = Column(Text, nullable=True)
    description_impact = Column(Text, nullable=True)
    
    # 关联关系
    session = relationship("ReviewSession", back_populates="results")
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'doc_type': self.doc_type,
            'doc_name': self.doc_name,
            'requirement_content': self.requirement_content,
            'violation_rules': self.violation_rules,
            'issue_level': self.issue_level,
            'issue_name': self.issue_name,
            'issue_location': self.issue_location,
            'description_requirement': self.description_requirement,
            'description_issue': self.description_issue,
            'description_location': self.description_location,
            'description_impact': self.description_impact
        } 