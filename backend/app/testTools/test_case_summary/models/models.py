"""
测试用例总结工具数据库模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class TestCaseSummarySession(Base):
    """测试用例总结会话表"""
    __tablename__ = "test_case_summary_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), unique=True, index=True, nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    status = Column(String(20), default="uploaded")  # uploaded, processing, completed, error
    total_test_items = Column(Integer, default=0)
    processed_test_items = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    output_filename = Column(String(255), nullable=True)  # 生成的输出文件名
    tester_name = Column(String(100), nullable=True)  # 使用工具的人员名称
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class TestItem(Base):
    """测试项表"""
    __tablename__ = "test_items"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), index=True, nullable=False)
    test_item_name = Column(Text, nullable=False)  # 测试项名称
    
    # 测试用例数据（JSON格式存储）
    test_cases_data = Column(Text, nullable=True)  # 存储所有相关测试用例的JSON数据
    
    # AI生成的总结
    ai_summary = Column(Text, nullable=True)  # AI生成的总结结果
    
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