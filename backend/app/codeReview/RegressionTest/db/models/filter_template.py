"""
全局过滤规则模板模型
不绑定特定任务，可供所有任务使用
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from ..database import Base


class FilterRuleTemplate(Base):
    """全局过滤规则模板模型"""
    __tablename__ = 'code_review_filter_templates'
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 规则名称
    template_name = Column(String(255), nullable=False)
    
    # 关键词（JSON数组）
    keywords = Column(JSON, nullable=False)
    
    # 逻辑类型：'AND' 或 'OR'
    logic_type = Column(String(10), default='AND', nullable=False)
    
    # 规则描述
    description = Column(Text, nullable=True)
    
    # 是否为系统预设规则
    is_system = Column(Boolean, default=False, nullable=False)
    
    # 排序顺序
    sort_order = Column(Integer, default=0, nullable=False)
    
    # 创建和更新时间
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'template_name': self.template_name,
            'keywords': self.keywords,
            'logic_type': self.logic_type,
            'description': self.description,
            'is_system': self.is_system,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
