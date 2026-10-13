"""
普通模式 FPGA PostgreSQL 数据库模型

4张独立表：nm_fpga_analysis_tasks/files/functions/problems
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class AnalysisTask(Base):
    """FPGA分析任务模型"""
    __tablename__ = 'nm_fpga_analysis_tasks'
    
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
    domain = Column(String(50), nullable=False, default='normalModeFpga')
    
    files = relationship("AnalysisFile", back_populates="task", cascade="all, delete-orphan")
    
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
            'domain': self.domain,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class AnalysisFile(Base):
    """FPGA分析文件模型"""
    __tablename__ = 'nm_fpga_analysis_files'
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('nm_fpga_analysis_tasks.id', ondelete='CASCADE'), nullable=True)
    file_path = Column(String(512), nullable=False)
    extract_path = Column(String(512), nullable=True)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=True)
    file_type = Column(String(50), nullable=True)
    upload_time = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default='uploaded')
    functions_count = Column(Integer, default=0)
    file_count = Column(Integer, default=0)
    
    task = relationship("AnalysisTask", back_populates="files")
    functions = relationship("AnalysisFunction", back_populates="file", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'file_path': self.file_path,
            'extract_path': self.extract_path,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'status': self.status,
            'functions_count': self.functions_count,
            'file_count': self.file_count,
            'upload_time': self.upload_time.isoformat() if self.upload_time else None
        }

class AnalysisFunction(Base):
    """FPGA分析函数/文件单元模型（FPGA按文件，占位行）"""
    __tablename__ = 'nm_fpga_analysis_functions'
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey('nm_fpga_analysis_files.id', ondelete='CASCADE'), nullable=False)
    function_name = Column(String(255), nullable=False)
    start_line = Column(Integer, nullable=False)
    end_line = Column(Integer, nullable=False)
    source_code = Column(Text, nullable=False)
    analyzed = Column(Boolean, default=False)
    file_path = Column(String(512), nullable=True)
    function_description = Column(Text, nullable=True)
    commented_code = Column(Text, nullable=True)
    
    file = relationship("AnalysisFile", back_populates="functions")
    problems = relationship("AnalysisProblem", back_populates="function", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'file_id': self.file_id,
            'function_name': self.function_name,
            'start_line': self.start_line,
            'end_line': self.end_line,
            'analyzed': self.analyzed,
            'file_path': self.file_path,
            'function_description': self.function_description,
            'commented_code': self.commented_code,
            'source_code': self.source_code[:200] + '...' if self.source_code and len(self.source_code) > 200 else self.source_code
        }

class AnalysisProblem(Base):
    """FPGA分析问题模型"""
    __tablename__ = 'nm_fpga_analysis_problems'
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('nm_fpga_analysis_tasks.id', ondelete='CASCADE'), nullable=False)
    file_id = Column(Integer, ForeignKey('nm_fpga_analysis_files.id', ondelete='CASCADE'), nullable=False)
    function_id = Column(Integer, ForeignKey('nm_fpga_analysis_functions.id', ondelete='CASCADE'), nullable=False)
    
    file_name = Column(String(255), nullable=False)
    source_code = Column(Text, nullable=False)
    violation_rules = Column(String(255), nullable=True)
    issue_level = Column(String(50), nullable=True)
    issue_name = Column(String(255), nullable=True)
    issue_location = Column(String(255), nullable=True)
    description_requirement = Column(Text, nullable=True)
    description_issue = Column(Text, nullable=True)
    description_location = Column(Text, nullable=True)
    description_impact = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    function = relationship("AnalysisFunction", back_populates="problems")
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'file_id': self.file_id,
            'function_id': self.function_id,
            'file_name': self.file_name,
            'source_code': self.source_code,
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
