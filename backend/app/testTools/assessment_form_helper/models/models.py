"""
鉴定测评表单辅助工具数据库模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class AssessmentSession(Base):
    """评估会话表"""
    __tablename__ = "assessment_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), unique=True, index=True, nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    status = Column(String(20), default="uploaded")  # uploaded, processing, completed, error
    total_rows = Column(Integer, default=0)
    processed_rows = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    output_filename = Column(String(255), nullable=True)  # 生成的输出文件名
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class RequirementItem(Base):
    """需求项表"""
    __tablename__ = "requirement_items"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), index=True, nullable=False)
    row_index = Column(Integer, nullable=False)  # Excel中的行号

    # 原始数据列
    original_requirement_description = Column(Text, nullable=True)  # 原始需求描述
    test_item_description = Column(Text, nullable=True)  # 测试项描述
    test_method = Column(Text, nullable=True)  # 测试方法

    # AI生成的列
    generated_requirement_description = Column(Text, nullable=True)  # 生成的需求子项描述
    adequacy_requirement = Column(Text, nullable=True)  # 充分性要求
    pass_criteria = Column(Text, nullable=True)  # 通过准则

    # 状态和元数据
    generation_status = Column(String(20), default="pending")  # pending, processing, completed, error
    ai_response_raw = Column(Text, nullable=True)  # AI原始响应
    error_message = Column(Text, nullable=True)
    processing_time = Column(Float, nullable=True)  # 处理时间(秒)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class GenerationLog(Base):
    """生成日志表"""
    __tablename__ = "generation_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), index=True, nullable=False)
    operation_type = Column(String(50), nullable=False)  # upload, process, generate, download
    status = Column(String(20), nullable=False)  # success, error
    message = Column(Text, nullable=True)
    execution_time = Column(Float, nullable=True)  # 执行时间(秒)
    created_at = Column(DateTime, default=func.now()) 