"""
功能审查数据库模型（独立）

包含功能审查需要的所有表模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from .database_feature import Base


class FeatureAnalysisTask(Base):
    """功能审查任务模型（副本）"""
    __tablename__ = 'code_review_tasks'
    
    id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String(255), nullable=False)
    task_description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String(50), default='pending')
    progress = Column(Integer, default=0)
    total_files = Column(Integer, default=0)
    processed_files = Column(Integer, default=0)
    total_problems = Column(Integer, default=0)
    code_file_id = Column(Integer, nullable=True)
    analysis_type = Column(String(50), default='feature_review')
    
    # 关联关系
    files = relationship("FeatureAnalysisFile", back_populates="task", cascade="all, delete-orphan")
    features = relationship("Feature", back_populates="task", cascade="all, delete-orphan")
    
    def to_dict(self):
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
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class FeatureAnalysisFile(Base):
    """功能审查文件模型（副本）"""
    __tablename__ = 'code_review_files'
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('code_review_tasks.id', ondelete='CASCADE'), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=True)
    extract_path = Column(Text, nullable=True)
    file_size = Column(Integer, nullable=True)
    status = Column(String(50), default='pending')
    upload_time = Column(DateTime, default=datetime.utcnow)  # 修改：与主模型保持一致，使用 upload_time
    
    # 关联关系
    task = relationship("FeatureAnalysisTask", back_populates="files")
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'file_name': self.file_name,
            'file_path': self.file_path,
            'extract_path': self.extract_path,
            'file_size': self.file_size,
            'status': self.status,
            'upload_time': self.upload_time.isoformat() if self.upload_time else None
        }


class Feature(Base):
    """功能点模型"""
    __tablename__ = 'features'
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('code_review_tasks.id', ondelete='CASCADE'), nullable=False)
    
    # 功能点基本信息
    feature_name = Column(String(255), nullable=False)
    feature_description = Column(Text, nullable=False)
    
    # Agent探索结果
    implementation_description = Column(Text, nullable=True)
    related_files = Column(Text, nullable=True)
    related_functions = Column(Text, nullable=True)
    code_locations = Column(Text, nullable=True)
    call_chain = Column(Text, nullable=True)
    
    # 审查配置信息
    software_type = Column(String(255), nullable=True)
    domain = Column(String(255), nullable=True)
    entry_function = Column(String(255), nullable=True)
    
    # 审查状态
    status = Column(String(50), default='pending')
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    task = relationship("FeatureAnalysisTask", back_populates="features")
    problems = relationship("FeatureReviewProblem", back_populates="feature", cascade="all, delete-orphan")
    
    def to_dict(self):
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
    """功能点审查问题模型"""
    __tablename__ = 'feature_review_problems'
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('code_review_tasks.id', ondelete='CASCADE'), nullable=False)
    feature_id = Column(Integer, ForeignKey('features.id', ondelete='CASCADE'), nullable=False)
    
    # 功能点信息
    feature_name = Column(String(255), nullable=False)
    feature_description = Column(Text, nullable=True)
    implementation_path = Column(Text, nullable=True)
    implementation_description = Column(Text, nullable=True)
    related_files = Column(Text, nullable=True)
    related_functions = Column(Text, nullable=True)
    code_locations = Column(Text, nullable=True)
    
    # 问题核心信息
    issue_name = Column(String(255), nullable=False)
    issue_level = Column(String(50), nullable=False, default='建议')
    issue_location = Column(String(255), nullable=True)
    
    # 问题详细描述
    file_name = Column(String(255), nullable=True)
    function_name = Column(String(255), nullable=True)
    line = Column(Integer, nullable=True)
    source_code = Column(Text, nullable=True)
    problem_reason = Column(Text, nullable=True)
    description_requirement = Column(Text, nullable=True)
    description_issue = Column(Text, nullable=True)
    description_location = Column(Text, nullable=True)
    description_impact = Column(Text, nullable=True)
    business_rule = Column(Text, nullable=True)
    suggestion = Column(Text, nullable=True)
    
    # 分类信息
    software_type = Column(String(255), nullable=True)
    domain = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    feature = relationship("Feature", back_populates="problems")
    
    def to_dict(self):
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

