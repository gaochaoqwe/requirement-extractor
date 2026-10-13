"""
审查会话模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, String, Text
from sqlalchemy.orm import relationship

# 尝试相对导入，失败则使用绝对导入
try:
    from ..database import Base
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from database import Base


class ReviewSession(Base):
    """审查会话模型"""
    __tablename__ = 'review_sessions'
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    annotated_taskbook_path = Column(Text, nullable=True)  # 研制任务书批注版文件路径
    annotated_requirementspec_path = Column(Text, nullable=True)  # 需求规格说明批注版文件路径
    
    # 关联关系
    results = relationship("ReviewResult", back_populates="session", cascade="all, delete-orphan")
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'annotated_taskbook_path': self.annotated_taskbook_path,
            'annotated_requirementspec_path': self.annotated_requirementspec_path
        } 