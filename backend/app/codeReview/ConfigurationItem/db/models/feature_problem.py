"""
功能点审查问题模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from ..database import Base


class Feature(Base):
    """功能点模型 - 存储用户定义的功能点信息"""
    __tablename__ = 'features'
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('code_review_tasks.id', ondelete='CASCADE'), nullable=False)
    
    # 功能点基本信息
    feature_name = Column(String(255), nullable=False)  # 功能点名称
    feature_description = Column(Text, nullable=False)  # 功能点描述（用户输入）
    
    # Agent探索结果
    implementation_description = Column(Text, nullable=True)  # 实现过程描述（AI生成）
    related_files = Column(Text, nullable=True)  # 相关文件列表（JSON格式）
    related_functions = Column(Text, nullable=True)  # 相关函数列表（JSON格式）
    code_locations = Column(Text, nullable=True)  # 代码位置信息（JSON格式）
    call_chain = Column(Text, nullable=True)  # 调用链路顺序（例如："funcA → funcB → funcC"）
    
    # 审查配置信息
    software_type = Column(String(255), nullable=True)  # 软件类型
    domain = Column(String(255), nullable=True)  # 领域
    entry_function = Column(String(255), nullable=True)  # 入口函数
    
    # 审查状态
    status = Column(String(50), default='pending')  # pending/processing/completed/failed
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    problems = relationship("FeatureReviewProblem", back_populates="feature", cascade="all, delete-orphan")
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'feature_name': self.feature_name,
            'feature_description': self.feature_description,
            'implementation_description': self.implementation_description,
            'related_files': self.related_files,
            'related_functions': self.related_functions,
            'code_locations': self.code_locations,
            'call_chain': self.call_chain,
            'software_type': self.software_type,
            'domain': self.domain,
            'entry_function': self.entry_function,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class FeatureReviewProblem(Base):
    """功能点审查问题模型 - 存储功能点审查发现的问题"""
    __tablename__ = 'feature_review_problems'
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('code_review_tasks.id', ondelete='CASCADE'), nullable=False)
    feature_id = Column(Integer, ForeignKey('features.id', ondelete='CASCADE'), nullable=False)
    
    # 功能点信息
    feature_name = Column(String(255), nullable=False)  # 功能点名称
    feature_description = Column(Text, nullable=True)  # 功能点描述
    implementation_path = Column(Text, nullable=True)  # 实现路径（文件和函数列表，JSON格式）
    implementation_description = Column(Text, nullable=True)
    related_files = Column(Text, nullable=True)
    related_functions = Column(Text, nullable=True)
    code_locations = Column(Text, nullable=True)
    
    # 问题核心信息
    issue_name = Column(String(255), nullable=False)  # 问题名称
    issue_level = Column(String(50), nullable=False, default='建议')  # 重要问题/一般问题/建议改进
    issue_location = Column(String(255), nullable=True)  # 问题位置（文件名:函数名）
    
    # 问题详细描述（对齐函数审查）
    file_name = Column(String(255), nullable=True)  # 主要文件名
    function_name = Column(String(255), nullable=True)  # 主要函数名
    line = Column(Integer, nullable=True)  # 问题所在行号（用于代码定位）
    source_code = Column(Text, nullable=True)  # 相关源代码
    problem_reason = Column(Text, nullable=True)  # 问题原因
    description_requirement = Column(Text, nullable=True)  # 功能需求描述
    description_issue = Column(Text, nullable=True)  # 问题描述
    description_location = Column(Text, nullable=True)  # 问题位置描述
    description_impact = Column(Text, nullable=True)  # 影响描述
    business_rule = Column(Text, nullable=True)  # 违反的业务规则
    suggestion = Column(Text, nullable=True)  # 改进建议
    
    # 分类信息
    software_type = Column(String(255), nullable=True)  # 软件类型
    domain = Column(String(255), nullable=True)  # 领域
    
    created_at = Column(DateTime, default=datetime.now)
    
    # 关系
    feature = relationship("Feature", back_populates="problems")
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'feature_id': self.feature_id,
            'feature_name': self.feature_name,
            'feature_description': self.feature_description,
            'implementation_path': self.implementation_path,
            'issue_name': self.issue_name,
            'issue_level': self.issue_level,
            'issue_location': self.issue_location,
            'file_name': self.file_name,
            'function_name': self.function_name,
            'line': self.line,
            'source_code': self.source_code,
            'problem_reason': self.problem_reason,
            'description_requirement': self.description_requirement,
            'description_issue': self.description_issue,
            'description_location': self.description_location,
            'description_impact': self.description_impact,
            'business_rule': self.business_rule,
            'suggestion': self.suggestion,
            'software_type': self.software_type,
            'domain': self.domain,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

