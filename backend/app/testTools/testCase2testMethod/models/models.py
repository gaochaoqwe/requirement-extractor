"""
测试用例反向推导工具数据库模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class TestCaseReverseSession(Base):
    """测试用例反向推导会话表"""
    __tablename__ = "test_case_reverse_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), unique=True, index=True, nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    status = Column(String(20), default="uploaded")  # uploaded, processing, completed, error
    processing_mode = Column(String(20), default="normal")  # normal, template
    total_test_items = Column(Integer, default=0)
    processed_test_items = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    output_filename = Column(String(255), nullable=True)  # 生成的输出文件名
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class TestItem(Base):
    """测试项表"""
    __tablename__ = "test_items"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), index=True, nullable=False)
    test_item_name = Column(Text, nullable=False)  # 测试项名称
    
    # 原始需求描述（从需求分析表读取）
    requirement_description = Column(Text, nullable=True)  # 需求子项描述，来源于需求分析表S列

    # 测试用例数据（JSON格式存储）
    test_cases_data = Column(Text, nullable=True)  # 存储所有相关测试用例的JSON数据
    
    # AI生成的测试内容和测试方法
    test_content = Column(Text, nullable=True)  # AI生成的测试内容（多条，用编号分隔）
    test_method = Column(Text, nullable=True)   # AI生成的测试方法（多条，用编号分隔）
    
    # 用例模板字段（仅在模板模式下使用）
    case_template_name = Column(Text, nullable=True)      # 用例模板（用例名称）
    case_template_input = Column(Text, nullable=True)     # 用例模板（输入条件）
    case_template_expected = Column(Text, nullable=True)  # 用例模板（预期结果）
    
    # 状态和元数据
    generation_status = Column(String(20), default="pending")  # pending, processing, completed, error
    ai_response_raw = Column(Text, nullable=True)  # AI原始响应
    error_message = Column(Text, nullable=True)
    processing_time = Column(Float, nullable=True)  # 处理时间(秒)
    retry_count = Column(Integer, default=0)  # 重试次数
    
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